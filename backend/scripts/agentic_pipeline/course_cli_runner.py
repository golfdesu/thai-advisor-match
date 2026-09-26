"""
Universal Course Extraction Agent & CLI Runner (SKILL.state Architecture)
Applies deterministic content pruning, minimal state patches, and RapidFuzz deduplication.
Based on arXiv:2608.26263v2 and .agents/skills/data-curriculum-tuition-discovery/
"""
import os
import sys
import time
import uuid
import json
import re
import argparse
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote, quote
from typing import List, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Setup backend paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from google import genai
from app.core.config import settings
from scripts.agentic_pipeline.course_models import CourseAgentState, CourseStatePatch
from scripts.agentic_pipeline.course_state_reducer import (
    CourseStateReducer,
    save_course_state_checkpoint,
    load_course_state_checkpoint
)
from scripts.agentic_pipeline.content_pruner import ContentPruner


COURSE_SYSTEM_PROMPT = """You are an expert Academic Curriculum & Tuition Discovery Extraction Agent.
Your task is to analyze university program web pages, extract standardized degree programs, and emit an atomic JSON State Patch.

STRICT EXTRACTION RULES:
1. Extract all academic programs/curricula mentioned in the provided text chunk.
2. Degree level MUST be one of: ปริญญาตรี, ปริญญาโท, ปริญญาเอก.
3. Extract official degree abbreviations (e.g. วศ.บ., วท.บ., วศ.ม., ปร.ด., B.Eng., M.Sc.).
4. Extract tuition fees per semester and total program fees if mentioned.
5. Extract duration (e.g. 4 ปี, 2 ปี) and total credits.
6. Output ONLY a valid JSON adhering to the `CourseStatePatch` schema.
"""

# --follow-links: deterministic curriculum link discovery from raw HTML (no LLM involved)
_LINK_KEYWORD_RE = re.compile(
    r"(หลักสูตร|บัณฑิตศึกษา|ปริญญาโท|ปริญญาเอก|มหาบัณฑิต|ดุษฎีบัณฑิต|ปร\.ด\.|"
    r"curricul|program|graduate|grad|master|doctor|degree|course)", re.I)
_LINK_SKIP_RE = re.compile(
    r"(\.(pdf|jpe?g|png|gif|docx?|xlsx?|pptx?|zip|rar|mp4)$|/news|/event|/activity|/gallery|"
    r"ข่าว|กิจกรรม|login|facebook\.com|youtube\.com|line\.me|mailto:|tel:|javascript:)", re.I)
MAX_LINKS_PER_PAGE = 15
MIN_TEXT_CHARS = 200


class _AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors: List[Tuple[str, str]] = []
        self._href: Optional[str] = None
        self._text: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.anchors.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def _base_domain(host: str) -> str:
    """'grad.swu.ac.th' -> 'swu.ac.th'; 'www.sut.ac.th' -> 'sut.ac.th'."""
    parts = host.lower().split(".")
    n = 3 if len(parts) >= 3 and parts[-2] in ("ac", "co", "or", "go") else 2
    return ".".join(parts[-n:])


def discover_curriculum_links(html_content: str, page_url: str, allowed_domains: set,
                              keyword_re: Optional[re.Pattern] = None) -> List[str]:
    """Same-university links whose URL or anchor text mentions a keyword (curriculum by default), best first."""
    keyword_re = keyword_re or _LINK_KEYWORD_RE
    collector = _AnchorCollector()
    try:
        collector.feed(html_content)
    except Exception:
        return []
    scored = {}
    for href, text in collector.anchors:
        if not href or href.startswith("#"):
            continue
        url = urljoin(page_url, href.strip()).split("#")[0]
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or _base_domain(parsed.netloc) not in allowed_domains:
            continue
        haystack = f"{unquote(url)} {text}"
        if _LINK_SKIP_RE.search(haystack):
            continue
        hits = len(keyword_re.findall(haystack))
        if hits:
            scored[url] = max(scored.get(url, 0), hits)
    return [u for u, _ in sorted(scored.items(), key=lambda kv: -kv[1])][:MAX_LINKS_PER_PAGE]


class CourseExtractionAgent:
    """Autonomous State-Driven Curriculum Discovery Agent."""

    def __init__(
        self,
        target_university_th: str,
        target_university_en: str,
        target_faculty_th: Optional[str] = None,
        target_faculty_en: Optional[str] = None,
        session_id: Optional[str] = None,
        max_steps: int = 30,
        checkpoint_dir: str = "data/agent_states",
        follow_links: bool = False
    ):
        self.follow_links = follow_links
        self.allowed_domains: set = set()
        self.session_id = session_id or f"course_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.state = CourseAgentState(
            session_id=self.session_id,
            target_university_th=target_university_th,
            target_university_en=target_university_en,
            target_faculty_th=target_faculty_th,
            target_faculty_en=target_faculty_en
        )
        self.reducer = CourseStateReducer()
        self.max_steps = max_steps
        self.checkpoint_dir = checkpoint_dir

        raw_keys = settings.GEMINI_API_KEYS.split(",") if settings.GEMINI_API_KEYS else []
        self.api_keys = [k.strip() for k in raw_keys if k.strip()]
        if not self.api_keys and (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")):
            self.api_keys = [settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")]
        self.clients = [genai.Client(api_key=k) for k in self.api_keys if k]
        self.client = self.clients[0] if self.clients else None
        self.current_key_idx = 0

    def _get_active_client(self):
        if not self.clients:
            raise ValueError("No valid Gemini API key configured.")
        return self.clients[self.current_key_idx % len(self.clients)]

    def _rotate_key(self):
        if len(self.clients) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.clients)

    def add_seed_urls(self, urls: List[str]):
        for u in urls:
            self.allowed_domains.add(_base_domain(urlparse(u).netloc))
            if u not in self.state.pending_urls and u not in self.state.visited_urls:
                self.state.pending_urls.append(u)

    def extract_patch_from_html(self, html_content: str, current_url: str = "") -> CourseStatePatch:
        if not self.clients:
            raise ValueError("No valid Gemini API key configured.")

        # Prune boilerplate nav/footer
        cleaned_text = ContentPruner.prune_html(html_content, max_output_chars=20000)

        prompt = f"""Target University: {self.state.target_university_th} ({self.state.target_university_en})
Faculty: {self.state.target_faculty_th or 'All'}
Current URL: {current_url}

CONTENT:
{cleaned_text}
"""
        last_err: Optional[Exception] = None
        for model_name in ('gemini-3.5-flash-lite', 'gemini-3.8-flash', 'gemini-3.6-flash'):
            for _ in range(max(1, len(self.clients))):
                try:
                    response = self._get_active_client().models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            'system_instruction': COURSE_SYSTEM_PROMPT,
                            'response_mime_type': 'application/json',
                            'response_schema': CourseStatePatch,
                            'temperature': 0.1
                        }
                    )
                    patch = CourseStatePatch.model_validate_json(response.text)
                    return patch
                except Exception as e:
                    last_err = e
                    print(f"   -> LLM {model_name} key#{self.current_key_idx} failed ({str(e)[:160]}); rotating...")
                    self._rotate_key()
                    time.sleep(2.0)
        raise ValueError(f"All extraction models/keys failed. Last error: {last_err}")

    def run_crawl_loop(self):
        self.state.status = "in_progress"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        while self.state.pending_urls and self.state.step_count < self.max_steps:
            current_url = self.state.pending_urls.pop(0)
            print(f"[{self.state.step_count+1}/{self.max_steps}] Crawling: {current_url}")

            try:
                # percent-encode Thai path segments; urllib rejects non-ASCII URLs
                req = urllib.request.Request(quote(current_url, safe=":/?#[]@!$&'()*+,;=%~"), headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html_content = resp.read().decode("utf-8", errors="replace")

                if self.follow_links:
                    links = [u for u in discover_curriculum_links(html_content, current_url, self.allowed_domains)
                             if u not in self.state.visited_urls and u not in self.state.failed_urls
                             and u not in self.state.pending_urls and u != current_url]
                    self.state.pending_urls.extend(links)
                    if links:
                        print(f"   -> Queued {len(links)} curriculum links")
                    # skip the LLM on link-only hub pages (saves Gemini quota)
                    if len(ContentPruner.prune_html(html_content, max_output_chars=20000).strip()) < MIN_TEXT_CHARS:
                        self.state.visited_urls.append(current_url)
                        self.state.step_count += 1
                        print("   -> Thin page, LLM skipped")
                        save_course_state_checkpoint(self.state, output_dir=self.checkpoint_dir)
                        continue

                patch = self.extract_patch_from_html(html_content, current_url=current_url)
                self.state = self.reducer.apply_patch(self.state, patch)
                self.state.visited_urls.append(current_url)
                print(f"   -> Extracted {len(patch.new_courses)} courses (Total: {len(self.state.courses)})")

            except Exception as e:
                print(f"   -> Error on {current_url}: {e}")
                self.state.failed_urls.append(current_url)

            save_course_state_checkpoint(self.state, output_dir=self.checkpoint_dir)
            time.sleep(1.0)

        self.state.status = "completed"
        save_course_state_checkpoint(self.state, output_dir=self.checkpoint_dir)

    def export_as_python_dataset(self) -> str:
        courses_list = list(self.state.courses.values())
        header = f"# AI-Extracted Courses for {self.state.target_university_th} ({self.state.target_university_en})\n"
        header += f"# Extracted using SKILL.state Architecture\n\n"
        header += f"EXTRACTED_COURSES = {json.dumps(courses_list, ensure_ascii=False, indent=4)}\n"
        return header


def main():
    parser = argparse.ArgumentParser(description="SKILL.state Universal Course Discovery & Extraction")
    parser.add_argument("--univ-th", type=str, required=True, help="University Thai Name")
    parser.add_argument("--univ-en", type=str, required=True, help="University English Name")
    parser.add_argument("--faculty-th", type=str, default="", help="Faculty Thai Name")
    parser.add_argument("--faculty-en", type=str, default="", help="Faculty English Name")
    parser.add_argument("--url", action="append", help="Seed URL to crawl", default=[])
    parser.add_argument("--export-file", type=str, help="Python export path", default=None)
    parser.add_argument("--max-steps", type=int, default=15)
    parser.add_argument("--follow-links", action="store_true",
                        help="Queue same-university curriculum links found in page HTML")

    args = parser.parse_args()

    agent = CourseExtractionAgent(
        target_university_th=args.univ_th,
        target_university_en=args.univ_en,
        target_faculty_th=args.faculty_th,
        target_faculty_en=args.faculty_en,
        max_steps=args.max_steps,
        follow_links=args.follow_links
    )

    if args.url:
        agent.add_seed_urls(args.url)

    if agent.state.pending_urls:
        agent.run_crawl_loop()
    else:
        print("No URLs provided. Use --url <URL> to specify seed endpoints.")

    if args.export_file:
        code = agent.export_as_python_dataset()
        os.makedirs(os.path.dirname(os.path.abspath(args.export_file)), exist_ok=True)
        with open(args.export_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Dataset exported to: {args.export_file}")


if __name__ == "__main__":
    main()
