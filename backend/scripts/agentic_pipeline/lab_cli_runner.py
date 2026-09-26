"""
Research Lab Extraction CLI Runner (SKILL.state Architecture, 2026-09-26).

Crawls a university site with deterministic same-domain link discovery (reusing
course_cli_runner.discover_curriculum_links with a lab keyword set), prunes each page with
ContentPruner, and asks Gemini for a compact LabStatePatch. Labs are deduplicated in Python
(RapidFuzz >= 90 on name_th) and checkpointed to the export file after every page.
Lead advisors are extracted as names only; scripts/ingest_phase5_research_labs.py resolves them
against real faculties rows.

Usage:
    python backend/scripts/agentic_pipeline/lab_cli_runner.py --univ-th "..." --univ-en "..." \
        --url https://www.example.ac.th/ --max-steps 40 --export-file backend/data/agent_states/phase5/x.py
"""
import os
import re
import sys
import json
import time
import argparse
import urllib.request
from urllib.parse import urlparse, quote
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from google import genai
from pydantic import BaseModel, Field, field_validator
from rapidfuzz import fuzz

from app.core.config import settings
from scripts.agentic_pipeline.content_pruner import ContentPruner
from scripts.agentic_pipeline.course_cli_runner import discover_curriculum_links, _base_domain, MIN_TEXT_CHARS

LAB_LINK_RE = re.compile(
    r"(ห้องปฏิบัติการวิจัย|ห้องวิจัย|หน่วยวิจัย|ศูนย์วิจัย|ศูนย์ความเป็นเลิศ|กลุ่มวิจัย|วิจัย|"
    r"research|lab|laboratory|center|centre|excellence|unit)", re.I)

LAB_SYSTEM_PROMPT = """You extract university RESEARCH LABS / RESEARCH CENTERS / RESEARCH UNITS from a web page.
STRICT RULES:
1. Only extract labs that are explicitly named on the page. Never invent labs, people, equipment or domains.
2. lead_advisor_name: the head/director/PI name exactly as written on the page (keep titles), else null.
3. research_domains / flagship_equipment: only items stated on the page; empty list if absent.
4. Skip administrative offices, research-funding offices, journals, news items and events.
5. discovered_urls: leave empty (links are handled deterministically).
Output ONLY JSON matching the LabStatePatch schema."""


class RawLab(BaseModel):
    name_th: Optional[str] = Field(None, description="Lab name in Thai as written")
    name_en: Optional[str] = Field(None, description="Lab name in English as written")
    faculty_th: Optional[str] = Field(None, description="Faculty (คณะ/สำนักวิชา) in Thai, if stated")
    faculty_en: Optional[str] = None
    department_th: Optional[str] = None
    department_en: Optional[str] = None
    lead_advisor_name: Optional[str] = Field(None, description="Head / PI name as written")
    member_names: List[str] = Field(default_factory=list)
    research_domains: List[str] = Field(default_factory=list)
    flagship_equipment: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    website_url: Optional[str] = None

    @field_validator("member_names", "research_domains", "flagship_equipment", mode="before")
    @classmethod
    def _coerce(cls, v):
        return v if v is not None else []


class LabStatePatch(BaseModel):
    new_labs: List[RawLab] = Field(default_factory=list)
    discovered_urls: List[str] = Field(default_factory=list)

    @field_validator("new_labs", "discovered_urls", mode="before")
    @classmethod
    def _coerce(cls, v):
        return v if v is not None else []


class LabExtractionAgent:
    def __init__(self, univ_th: str, univ_en: str, max_steps: int, export_file: str):
        self.univ_th, self.univ_en = univ_th, univ_en
        self.max_steps, self.export_file = max_steps, export_file
        keys = [k.strip() for k in (settings.GEMINI_API_KEYS or os.getenv("GEMINI_API_KEYS", "")).split(",") if k.strip()]
        self.clients = [genai.Client(api_key=k) for k in keys]
        self.key_idx = 0
        self.pending: List[str] = []
        self.visited: List[str] = []
        self.failed: List[str] = []
        self.allowed: set = set()
        self.labs: List[dict] = []

    def seed(self, urls: List[str]):
        for u in urls:
            self.allowed.add(_base_domain(urlparse(u).netloc))
            if u not in self.pending:
                self.pending.append(u)

    def extract(self, html: str, url: str) -> LabStatePatch:
        text = ContentPruner.prune_html(html, max_output_chars=20000)
        prompt = f"University: {self.univ_th} ({self.univ_en})\nCurrent URL: {url}\n\nCONTENT:\n{text}"
        last = None
        for model in ("gemini-3.5-flash-lite", "gemini-3.6-flash"):
            for _ in range(max(1, len(self.clients))):
                try:
                    r = self.clients[self.key_idx % len(self.clients)].models.generate_content(
                        model=model, contents=prompt,
                        config={"system_instruction": LAB_SYSTEM_PROMPT, "response_mime_type": "application/json",
                                "response_schema": LabStatePatch, "temperature": 0.1})
                    return LabStatePatch.model_validate_json(r.text)
                except Exception as e:
                    last = e
                    self.key_idx += 1
                    time.sleep(2.0)
        raise ValueError(f"All models/keys failed: {str(last)[:160]}")

    def merge(self, raw: RawLab, url: str):
        name = re.sub(r"\s+", " ", (raw.name_th or raw.name_en or "").strip())
        if len(name) < 6:
            return
        for lab in self.labs:
            if fuzz.token_sort_ratio(name, lab["_key"]) >= 90:
                for f in ("member_names", "research_domains", "flagship_equipment"):
                    lab[f] += [x for x in getattr(raw, f) if x not in lab[f]]
                for f in ("name_en", "faculty_th", "faculty_en", "department_th", "department_en",
                          "lead_advisor_name", "description", "website_url"):
                    if not lab.get(f) and getattr(raw, f):
                        lab[f] = getattr(raw, f)
                return
        d = raw.model_dump()
        d.update(_key=name, source_url=url, university_th=self.univ_th, university=self.univ_en)
        self.labs.append(d)

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.export_file)), exist_ok=True)
        with open(self.export_file, "w", encoding="utf-8") as f:
            f.write(f"# AI-Extracted Research Labs for {self.univ_th} ({self.univ_en})\n")
            f.write(f"# visited={len(self.visited)} failed={len(self.failed)}\n\n")
            f.write(f"EXTRACTED_LABS = {json.dumps(self.labs, ensure_ascii=False, indent=2)}\n")

    def run(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                 "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                   "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8"}
        step = 0
        while self.pending and step < self.max_steps:
            url = self.pending.pop(0)
            step += 1
            print(f"[{step}/{self.max_steps}] {url}")
            try:
                req = urllib.request.Request(quote(url, safe=":/?#[]@!$&'()*+,;=%~"), headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                links = [u for u in discover_curriculum_links(html, url, self.allowed, LAB_LINK_RE)
                         if u not in self.visited and u not in self.failed and u not in self.pending and u != url]
                self.pending.extend(links)
                self.visited.append(url)
                if len(ContentPruner.prune_html(html, max_output_chars=20000).strip()) < MIN_TEXT_CHARS:
                    print("   -> thin page, LLM skipped")
                    continue
                patch = self.extract(html, url)
                for raw in patch.new_labs:
                    self.merge(raw, url)
                print(f"   -> +{len(patch.new_labs)} labs (total {len(self.labs)}), queued {len(links)}")
            except Exception as e:
                print(f"   -> error: {str(e)[:120]}")
                self.failed.append(url)
            self.save()
            time.sleep(1.0)
        self.save()


def main():
    ap = argparse.ArgumentParser(description="SKILL.state research lab extraction")
    ap.add_argument("--univ-th", required=True)
    ap.add_argument("--univ-en", required=True)
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--export-file", required=True)
    ap.add_argument("--max-steps", type=int, default=40)
    a = ap.parse_args()
    agent = LabExtractionAgent(a.univ_th, a.univ_en, a.max_steps, a.export_file)
    agent.seed(a.url)
    agent.run()
    print(f"Labs exported: {len(agent.labs)} -> {a.export_file}")


if __name__ == "__main__":
    main()
