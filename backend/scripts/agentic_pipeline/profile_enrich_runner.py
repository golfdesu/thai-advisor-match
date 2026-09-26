"""
Faculty Profile Field Enrichment Runner (SKILL.state Architecture, Phase 6, 2026-09-26).

Fetches each faculty member's own profile page headlessly (ThreadPoolExecutor), prunes it with
ContentPruner and asks Gemini for education / taught_courses and which of the page's <img>
candidates is the person's photo. The LLM may only pick an image from the candidate list found
in the raw HTML; it never writes a URL. Results are checkpointed to --out after every page, so
a rerun skips ids already done. DB writes happen in scripts/ingest_phase6_profile_fields.py.

Input (--targets): JSON list of {"id", "name_th", "name_en", "profile_url"}
    produced by: python scripts/ingest_phase6_profile_fields.py --export-targets ...

Usage:
    python backend/scripts/agentic_pipeline/profile_enrich_runner.py \
        --targets backend/data/agent_states/phase6/targets_pilot.json \
        --out backend/data/agent_states/phase6/results_pilot.json --workers 6
"""
import os
import re
import sys
import json
import time
import argparse
import threading
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from google import genai
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from scripts.agentic_pipeline.content_pruner import ContentPruner

MAX_IMG_CANDIDATES = 40
IMG_SKIP_RE = re.compile(r"(logo|icon|banner|favicon|sprite|loading|spinner|\.svg($|\?)|\.gif($|\?)|data:)", re.I)

PROFILE_SYSTEM_PROMPT = """You read ONE university faculty profile page and extract fields for the named person.
STRICT RULES:
1. is_person_profile: true only if the page is clearly the profile of the named person.
2. education: degrees exactly as stated on the page (e.g. "Ph.D. (Chemistry), University of X"); [] if absent.
3. taught_courses: course names the person teaches, exactly as stated; [] if absent.
4. image_index: the index of the candidate image that is the person's portrait photo, else null.
   Only choose an index when its src/alt clearly belongs to this person's photo; never a logo or group photo.
5. Never invent anything. Never include phone numbers.
Output ONLY JSON matching the ProfilePatch schema."""


class ProfilePatch(BaseModel):
    is_person_profile: bool = False
    education: List[str] = Field(default_factory=list)
    taught_courses: List[str] = Field(default_factory=list)
    image_index: Optional[int] = None

    @field_validator("education", "taught_courses", mode="before")
    @classmethod
    def _coerce(cls, v):
        return v if v is not None else []


class _ImgCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs: List[tuple] = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            a = dict(attrs)
            src = a.get("src") or a.get("data-src")
            if src:
                self.imgs.append((src.strip(), (a.get("alt") or "").strip()[:80]))


def image_candidates(html: str, page_url: str) -> List[tuple]:
    c = _ImgCollector()
    try:
        c.feed(html)
    except Exception:
        return []
    out, seen = [], set()
    for src, alt in c.imgs:
        url = urljoin(page_url, src)
        if not url.startswith(("http://", "https://")) or IMG_SKIP_RE.search(url) or url in seen:
            continue
        seen.add(url)
        out.append((url, alt))
    return out[:MAX_IMG_CANDIDATES]


class ProfileEnricher:
    def __init__(self, out_path: str):
        keys = [k.strip() for k in (settings.GEMINI_API_KEYS or os.getenv("GEMINI_API_KEYS", "")).split(",") if k.strip()]
        self.clients = [genai.Client(api_key=k) for k in keys]
        self.key_idx = 0
        self.lock = threading.Lock()
        self.out_path = out_path
        self.results = {}
        if os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                self.results = json.load(f)

    def _next_client(self):
        with self.lock:
            self.key_idx += 1
            return self.clients[self.key_idx % len(self.clients)]

    def extract(self, prompt: str) -> ProfilePatch:
        last = None
        for model in ("gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"):
            for _ in range(max(1, len(self.clients))):
                try:
                    r = self._next_client().models.generate_content(
                        model=model, contents=prompt,
                        config={"system_instruction": PROFILE_SYSTEM_PROMPT, "response_mime_type": "application/json",
                                "response_schema": ProfilePatch, "temperature": 0.0})
                    return ProfilePatch.model_validate_json(r.text)
                except Exception as e:
                    last = e
                    time.sleep(2.0)
        raise ValueError(f"All models/keys failed: {str(last)[:160]}")

    def process(self, t: dict) -> dict:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                 "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                   "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8"}
        url = t["profile_url"]
        try:
            req = urllib.request.Request(quote(url, safe=":/?#[]@!$&'()*+,;=%~"), headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return {"status": "fetch_error", "error": str(e)[:120]}
        text = ContentPruner.prune_html(html, max_output_chars=12000).strip()
        imgs = image_candidates(html, url)
        if len(text) < 80 and not imgs:
            return {"status": "thin_page"}
        img_list = "\n".join(f"[{i}] {u} alt=\"{a}\"" for i, (u, a) in enumerate(imgs)) or "(none)"
        prompt = (f"Person: {t.get('name_th') or ''} / {t.get('name_en') or ''}\nURL: {url}\n\n"
                  f"CANDIDATE IMAGES:\n{img_list}\n\nPAGE TEXT:\n{text}")
        try:
            p = self.extract(prompt)
        except Exception as e:
            return {"status": "llm_error", "error": str(e)[:120]}
        img = imgs[p.image_index][0] if p.image_index is not None and 0 <= p.image_index < len(imgs) else None
        return {"status": "ok", "is_person_profile": p.is_person_profile, "education": p.education,
                "taught_courses": p.taught_courses, "image_url": img}

    def save(self):
        with self.lock:
            tmp = self.out_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.out_path)

    def run(self, targets: List[dict], workers: int):
        todo = [t for t in targets if t["id"] not in self.results]
        print(f"targets={len(targets)} already_done={len(targets) - len(todo)} todo={len(todo)}", flush=True)
        done = 0

        def work(t):
            nonlocal done
            res = self.process(t)
            with self.lock:
                self.results[t["id"]] = res
                done += 1
                n = done
            if n % 25 == 0 or n == len(todo):
                self.save()
                print(f"progress {n}/{len(todo)}", flush=True)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, todo))
        self.save()
        stats = {}
        for r in self.results.values():
            stats[r["status"]] = stats.get(r["status"], 0) + 1
        print(f"done: {json.dumps(stats)}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="SKILL.state faculty profile field enrichment")
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="process only the first N targets")
    a = ap.parse_args()
    with open(a.targets, encoding="utf-8") as f:
        targets = json.load(f)
    if a.limit:
        targets = targets[:a.limit]
    ProfileEnricher(a.out).run(targets, a.workers)


if __name__ == "__main__":
    main()
