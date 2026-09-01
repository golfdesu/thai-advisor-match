"""
Autonomous State-Driven Faculty Extraction Agent Controller
Based on the SKILL.state Architecture & Evaluation: https://arxiv.org/html/2608.26263v2#S5
"""
import os
import time
import uuid
import json
import httpx
from typing import List, Optional, Dict, Any

from scripts.agentic_pipeline.models import ExtractionAgentState, FacultyStatePatch
from scripts.agentic_pipeline.state_reducer import (
    FacultyStateReducer,
    save_state_checkpoint,
    load_state_checkpoint
)
from scripts.agentic_pipeline.llm_client import LLMStatePatchGenerator
from scripts.wikiskill.trace_logger import TraceLogger, ExecutionTraceEntry
from scripts.wikiskill.wiki_maintainer import WikiMaintainer


class FacultyExtractionAgent:
    """
    Autonomous State-Driven Faculty Extraction Agent.
    Implements the SKILL.state runtime loop (arXiv:2608.26263v2) and logs to WikiSkill (arXiv:2608.27454v1).
    """

    def __init__(
        self,
        target_university_th: str,
        target_university_en: str,
        target_faculty_th: Optional[str] = None,
        target_faculty_en: Optional[str] = None,
        session_id: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        db_session=None,
        max_steps: int = 50,
        checkpoint_dir: str = "data/agent_states",
        auto_lookup_wiki: bool = True
    ):
        self.session_id = session_id or f"extract_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.state = ExtractionAgentState(
            session_id=self.session_id,
            target_university_th=target_university_th,
            target_university_en=target_university_en,
            target_faculty_th=target_faculty_th,
            target_faculty_en=target_faculty_en,
        )
        self.reducer = FacultyStateReducer(db_session=db_session)
        self.patch_generator = LLMStatePatchGenerator(api_key=gemini_api_key)
        self.max_steps = max_steps
        self.checkpoint_dir = checkpoint_dir
        self.trace_logger = TraceLogger()
        self.wiki_maintainer = WikiMaintainer()

        # WikiSkill Layer 2: Fast Seed Lookup from Persistent Knowledge
        if auto_lookup_wiki:
            known_endpoints = self.wiki_maintainer.lookup_university_endpoints(target_university_en)
            if known_endpoints:
                self.add_seed_urls(known_endpoints)

    def add_seed_urls(self, urls: List[str]):
        """Adds initial directory URLs to crawl."""
        for u in urls:
            if u not in self.state.pending_urls and u not in self.state.visited_urls:
                self.state.pending_urls.append(u)

    def step_with_html(self, html_content: str, current_url: str = "") -> FacultyStatePatch:
        """Runs a single extraction turn given an explicit HTML string."""
        self.state.status = "in_progress"
        patch, tokens = self.patch_generator.generate_patch(
            state=self.state,
            html_chunk=html_content,
            current_url=current_url
        )
        self.state = self.reducer.apply_patch(self.state, patch, step_tokens=tokens)
        if current_url and current_url not in self.state.visited_urls:
            self.state.visited_urls.append(current_url)
            if current_url in self.state.pending_urls:
                self.state.pending_urls.remove(current_url)

        save_state_checkpoint(self.state, output_dir=self.checkpoint_dir)
        return patch

    def run_crawl_loop(self, timeout_sec: int = 15) -> ExtractionAgentState:
        """Executes autonomous multi-step crawl across pending URLs."""
        self.state.status = "in_progress"

        import urllib.request
        import ssl

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        while self.state.pending_urls and self.state.step_count < self.max_steps:
            current_url = self.state.pending_urls.pop(0)
            print(f"\n[Step {self.state.step_count + 1}] 🌐 Fetching: {current_url}")

            try:
                req = urllib.request.Request(
                    current_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout_sec) as resp:
                    html_text = resp.read().decode("utf-8", errors="ignore")
                    status_code = resp.getcode()

                patch = self.step_with_html(html_text, current_url=current_url)
                print(f"  ✅ Extracted {len(patch.new_profiles)} profiles. Total so far: {len(self.state.faculties)}")
                print(f"  📊 Summary: {patch.summary_of_changes}")

                # Log successful trace
                self.trace_logger.log_trace(ExecutionTraceEntry(
                    trace_id=f"trace_{int(time.time()*1000)}",
                    session_id=self.session_id,
                    university_th=self.state.target_university_th,
                    university_en=self.state.target_university_en,
                    faculty_th=self.state.target_faculty_th,
                    target_url=current_url,
                    http_status=status_code,
                    success=True,
                    extracted_profiles_count=len(patch.new_profiles),
                    discovered_urls_count=len(patch.discovered_urls)
                ))

            except Exception as e:
                print(f"  ❌ Failed to fetch {current_url}: {e}")
                self.state.failed_urls.append(current_url)
                # Log failed trace
                self.trace_logger.log_trace(ExecutionTraceEntry(
                    trace_id=f"trace_{int(time.time()*1000)}",
                    session_id=self.session_id,
                    university_th=self.state.target_university_th,
                    university_en=self.state.target_university_en,
                    faculty_th=self.state.target_faculty_th,
                    target_url=current_url,
                    success=False,
                    error_message=str(e)
                ))

            time.sleep(1.0)  # Courtesy delay between university server requests

        self.state.status = "completed"
        save_state_checkpoint(self.state, output_dir=self.checkpoint_dir)
        return self.state

    def export_as_dataset_python(self, variable_name: str = "EXTRACTED_FACULTIES") -> str:
        """Exports the verified in-memory state as a ready-to-import Python dataset file."""
        faculty_list = list(self.state.faculties.values())
        header = f"# Auto-generated by SKILL.state FacultyExtractionAgent (Session: {self.state.session_id})\n"
        code = f"{header}{variable_name} = " + json.dumps(faculty_list, ensure_ascii=False, indent=4) + "\n"
        return code
