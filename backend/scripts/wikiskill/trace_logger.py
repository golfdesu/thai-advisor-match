"""
WikiSkill Trace Logger (Layer 1: Raw Execution Traces)
Based on WikiSkill Architecture: https://arxiv.org/html/2608.27454v1
"""
import os
import json
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExecutionTraceEntry(BaseModel):
    """Immutable single step execution trace."""
    trace_id: str
    timestamp: float = Field(default_factory=time.time)
    session_id: str
    university_th: str
    university_en: str
    faculty_th: Optional[str] = None
    target_url: str
    http_status: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    extracted_profiles_count: int = 0
    discovered_urls_count: int = 0
    tokens_used: int = 0
    duration_ms: float = 0.0
    strategy_used: str = "direct_http"


class TraceLogger:
    """Appends atomic execution traces to the raw_traces storage."""

    def __init__(self, trace_dir: str = "Teacher/.agents/raw_traces"):
        self.trace_dir = trace_dir
        os.makedirs(self.trace_dir, exist_ok=True)

    def log_trace(self, trace: ExecutionTraceEntry) -> str:
        """Appends trace entry to daily jsonl file."""
        date_str = time.strftime("%Y-%m-%d", time.localtime(trace.timestamp))
        file_path = os.path.join(self.trace_dir, f"{date_str}_traces.jsonl")

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(trace.model_dump_json() + "\n")

        return file_path

    def read_session_traces(self, session_id: str) -> List[ExecutionTraceEntry]:
        """Reads all traces matching a given session_id."""
        traces = []
        if not os.path.exists(self.trace_dir):
            return traces

        for fname in os.listdir(self.trace_dir):
            if fname.endswith(".jsonl"):
                fpath = os.path.join(self.trace_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            if data.get("session_id") == session_id:
                                traces.append(ExecutionTraceEntry.model_validate(data))
        return traces
