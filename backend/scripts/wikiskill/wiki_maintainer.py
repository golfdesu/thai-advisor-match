"""
WikiSkill Maintainer (Layer 2: Wiki Knowledge Compiler)
Based on WikiSkill Architecture: https://arxiv.org/html/2608.27454v1
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from scripts.wikiskill.trace_logger import ExecutionTraceEntry, TraceLogger


class WikiMaintainer:
    """
    Analyzes raw execution traces and compiles structured knowledge
    into Teacher/.agents/wiki/ without losing history.
    """

    def __init__(
        self,
        wiki_dir: str = "Teacher/.agents/wiki",
        trace_logger: Optional[TraceLogger] = None
    ):
        self.wiki_dir = wiki_dir
        self.trace_logger = trace_logger or TraceLogger()
        self.universities_dir = os.path.join(self.wiki_dir, "universities")
        self.patterns_dir = os.path.join(self.wiki_dir, "patterns")
        os.makedirs(self.universities_dir, exist_ok=True)
        os.makedirs(self.patterns_dir, exist_ok=True)

    def compile_from_traces(self, traces: List[ExecutionTraceEntry]) -> Dict[str, Any]:
        """
        Processes a list of traces, clusters successes vs failures,
        and updates the corresponding university and pattern wiki files.
        """
        summary = {
            "processed_traces": len(traces),
            "updated_universities": set(),
            "new_dead_links_recorded": 0,
            "new_verified_endpoints": 0,
        }

        # Group by university
        grouped_by_univ: Dict[str, List[ExecutionTraceEntry]] = {}
        for t in traces:
            key = t.university_en.lower().replace(" ", "_")
            grouped_by_univ.setdefault(key, []).append(t)

        for univ_slug, univ_traces in grouped_by_univ.items():
            self._update_university_wiki(univ_slug, univ_traces, summary)

        # Log compilation to evolution log
        self._append_evolution_log(summary)

        return summary

    def _update_university_wiki(
        self,
        univ_slug: str,
        traces: List[ExecutionTraceEntry],
        summary: Dict[str, Any]
    ):
        """Updates or creates a university wiki markdown file."""
        file_path = os.path.join(self.universities_dir, f"{univ_slug}.md")
        univ_name_th = traces[0].university_th
        univ_name_en = traces[0].university_en

        verified_urls = {}
        dead_urls = set()

        # Read existing file if present to preserve compounding knowledge
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = f"# {univ_name_en} ({univ_name_th}) — Verified Directory Knowledge\n<!-- Reference: WikiSkill (arXiv:2608.27454v1) -->\n\n"

        for t in traces:
            if t.success and t.extracted_profiles_count > 0:
                verified_urls[t.target_url] = {
                    "faculty_th": t.faculty_th or "General",
                    "profiles_count": t.extracted_profiles_count,
                    "last_verified": time.strftime("%Y-%m-%d")
                }
                summary["new_verified_endpoints"] += 1
            elif not t.success or (t.http_status and t.http_status in [404, 500]):
                dead_urls.add(t.target_url)
                summary["new_dead_links_recorded"] += 1

        # Synthesize updated markdown section
        new_entries = []
        if verified_urls:
            new_entries.append("\n### 🟢 Verified Active Directory URLs\n")
            for url, meta in verified_urls.items():
                new_entries.append(f"- `{url}` ({meta['faculty_th']} - {meta['profiles_count']} profiles verified {meta['last_verified']})")

        if dead_urls:
            new_entries.append("\n### 🔴 Dead / Inaccessible URLs to Avoid\n")
            for url in dead_urls:
                new_entries.append(f"- `{url}` (Failed / 404)")

        updated_content = content.strip() + "\n" + "\n".join(new_entries) + "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        summary["updated_universities"].add(univ_slug)

    def _append_evolution_log(self, summary: Dict[str, Any]):
        """Appends compilation summary to evolution_log.md."""
        log_path = os.path.join(self.wiki_dir, "evolution_log.md")
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        entry = f"""
### [{now_str}] Wiki Knowledge Compilation
- **Traces Processed:** {summary['processed_traces']}
- **Universities Updated:** {', '.join(summary['updated_universities']) if summary['updated_universities'] else 'None'}
- **New Verified Endpoints:** {summary['new_verified_endpoints']}
- **Dead Links Flagged:** {summary['new_dead_links_recorded']}
"""
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def lookup_university_endpoints(self, university_en: str) -> List[str]:
        """Fast lookup of verified endpoints from wiki for a given university."""
        univ_slug = university_en.lower().replace(" ", "_")
        file_path = os.path.join(self.universities_dir, f"{univ_slug}.md")
        endpoints = []

        if not os.path.exists(file_path):
            return endpoints

        with open(file_path, "r", encoding="utf-8") as f:
            in_verified_section = False
            for line in f:
                if "Verified Active Directory URLs" in line:
                    in_verified_section = True
                    continue
                if in_verified_section:
                    if line.startswith("### "):
                        break
                    if line.strip().startswith("- `http"):
                        url = line.split("`")[1]
                        endpoints.append(url)

        return endpoints
