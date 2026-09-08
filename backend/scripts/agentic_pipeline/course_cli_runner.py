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
import argparse
import urllib.request
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
        checkpoint_dir: str = "data/agent_states"
    ):
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
        self.client = genai.Client(api_key=self.api_keys[0]) if self.api_keys else None

    def add_seed_urls(self, urls: List[str]):
        for u in urls:
            if u not in self.state.pending_urls and u not in self.state.visited_urls:
                self.state.pending_urls.append(u)

    def extract_patch_from_html(self, html_content: str, current_url: str = "") -> CourseStatePatch:
        if not self.client:
            raise ValueError("No valid Gemini API key configured.")

        # Prune boilerplate nav/footer
        cleaned_text = ContentPruner.prune_html(html_content, max_output_chars=20000)

        prompt = f"""Target University: {self.state.target_university_th} ({self.state.target_university_en})
Faculty: {self.state.target_faculty_th or 'All'}
Current URL: {current_url}

CONTENT:
{cleaned_text}
"""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
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
                req = urllib.request.Request(current_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html_content = resp.read().decode("utf-8", errors="replace")

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

    args = parser.parse_args()

    agent = CourseExtractionAgent(
        target_university_th=args.univ_th,
        target_university_en=args.univ_en,
        target_faculty_th=args.faculty_th,
        target_faculty_en=args.faculty_en,
        max_steps=args.max_steps
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
