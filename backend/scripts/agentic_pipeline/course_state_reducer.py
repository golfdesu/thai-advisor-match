"""
Deterministic State Reducer for Curriculum & Course Extraction
Applies RapidFuzz deduplication, tuition normalization, and state checkpointing.
Based on SKILL.state (arXiv:2608.26263v2).
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz

from scripts.agentic_pipeline.course_models import (
    CourseAgentState,
    CourseStatePatch,
    RawCourseProfile
)


DEGREE_LEVEL_MAP = {
    "ตรี": "ปริญญาตรี",
    "bachelor": "ปริญญาตรี",
    "b.sc": "ปริญญาตรี",
    "b.eng": "ปริญญาตรี",
    "โท": "ปริญญาโท",
    "master": "ปริญญาโท",
    "m.sc": "ปริญญาโท",
    "m.eng": "ปริญญาโท",
    "เอก": "ปริญญาเอก",
    "ph.d": "ปริญญาเอก",
    "doctor": "ปริญญาเอก",
    "doctoral": "ปริญญาเอก",
}


def normalize_degree_level(raw_level: str) -> str:
    """Normalizes degree level to standard Thai taxonomy."""
    lvl = (raw_level or "").lower().strip()
    for k, v in DEGREE_LEVEL_MAP.items():
        if k in lvl:
            return v
    return "ปริญญาตรี"


def calculate_tuition_total(per_semester_str: Optional[str], degree_level: str, duration_years_str: Optional[str]) -> Optional[str]:
    """Calculates standardized total tuition according to Tier-2 discovery guidelines."""
    if not per_semester_str:
        return None

    # Extract numeric amount from string like "21,000 บาท"
    nums = re.findall(r"\d+", per_semester_str.replace(",", ""))
    if not nums:
        return None
    fee = int(nums[0])

    years = 4
    if duration_years_str:
        y_nums = re.findall(r"\d+", duration_years_str)
        if y_nums:
            years = int(y_nums[0])

    if degree_level == "ปริญญาตรี":
        semesters = years * 2
    elif degree_level == "ปริญญาโท":
        semesters = years * 2
    elif degree_level == "ปริญญาเอก":
        semesters = years * 2
    else:
        semesters = years * 2

    total_fee = fee * semesters
    return f"{total_fee:,} บาท"


def generate_course_canonical_id(univ_prefix: str, faculty_prefix: str, title_slug: str, index: int) -> str:
    """Generates clean slug ID like cmu_eng_cpe_001."""
    u_slug = re.sub(r"[^a-zA-Z0-9]", "", (univ_prefix or "univ").lower())[:8]
    f_slug = re.sub(r"[^a-zA-Z0-9]", "", (faculty_prefix or "fac").lower())[:8]
    t_slug = re.sub(r"[^a-zA-Z0-9]", "", (title_slug or "prog").lower())[:15]
    return f"{u_slug}_{f_slug}_{t_slug}_{index:03d}"


class CourseStateReducer:
    """
    Deterministic Reducer for Curriculum Extraction.
    Maintains clean state and deduplicates against existing records via RapidFuzz.
    """

    def __init__(self, fuzzy_threshold: float = 85.0):
        self.fuzzy_threshold = fuzzy_threshold

    def apply_patch(self, state: CourseAgentState, patch: CourseStatePatch, step_tokens: int = 0) -> CourseAgentState:
        state.step_count += 1
        state.total_tokens_used += step_tokens

        # 1. URLs
        for url in patch.discovered_urls:
            url_clean = url.strip()
            if url_clean and url_clean not in state.visited_urls and url_clean not in state.pending_urls:
                state.pending_urls.append(url_clean)

        for failed in patch.unreachable_or_empty_pages:
            f_clean = failed.strip()
            if f_clean in state.pending_urls:
                state.pending_urls.remove(f_clean)
            if f_clean not in state.failed_urls:
                state.failed_urls.append(f_clean)

        # 2. Process courses
        for raw in patch.new_courses:
            self._process_single_course(state, raw)

        return state

    def _process_single_course(self, state: CourseAgentState, raw: RawCourseProfile):
        clean_title_th = re.sub(r"\s+", " ", raw.title_th.strip())
        if not clean_title_th:
            return

        norm_degree = normalize_degree_level(raw.degree_level)
        tuition_sem = raw.tuition_per_semester.strip() if raw.tuition_per_semester else None
        tuition_tot = raw.tuition_total.strip() if raw.tuition_total else calculate_tuition_total(tuition_sem, norm_degree, raw.duration_years)

        # RapidFuzz deduplication check against in-state courses
        match_id = None
        for existing_id, existing_c in state.courses.items():
            if existing_c.get("degree_level") == norm_degree:
                score = fuzz.token_sort_ratio(clean_title_th, existing_c.get("title_th", ""))
                if score >= self.fuzzy_threshold:
                    match_id = existing_id
                    break

        if match_id:
            # Deep merge updates
            existing = state.courses[match_id]
            if not existing.get("tuition_per_semester") and tuition_sem:
                existing["tuition_per_semester"] = tuition_sem
            if not existing.get("tuition_total") and tuition_tot:
                existing["tuition_total"] = tuition_tot
            if not existing.get("description") and raw.description:
                existing["description"] = raw.description
            existing.setdefault("career_paths", [])
            for cp in (raw.career_paths or []):
                if cp not in existing["career_paths"]:
                    existing["career_paths"].append(cp)
            existing.setdefault("curriculum_highlights", [])
            for ch in (raw.curriculum_highlights or []):
                if ch not in existing["curriculum_highlights"]:
                    existing["curriculum_highlights"].append(ch)
            existing.setdefault("tags", [])
            for t in (raw.tags or []):
                if t not in existing["tags"]:
                    existing["tags"].append(t)
        else:
            # Create new canonical course
            idx = len(state.courses) + 1
            cid = generate_course_canonical_id(
                state.target_university_en,
                state.target_faculty_en or "acad",
                raw.title_en or clean_title_th,
                idx
            )
            state.courses[cid] = {
                "id": cid,
                "title_th": clean_title_th,
                "title_en": raw.title_en.strip() if raw.title_en else clean_title_th,
                "degree_level": norm_degree,
                "degree_name": raw.degree_name.strip() if raw.degree_name else "",
                "university": state.target_university_en,
                "university_th": state.target_university_th,
                "faculty": state.target_faculty_en or "",
                "faculty_th": state.target_faculty_th or "",
                "department": raw.department_en or "",
                "department_th": raw.department_th or "",
                "program_type": raw.program_type or "ภาคปกติ",
                "duration_years": raw.duration_years or "4 ปี",
                "total_credits": raw.total_credits or "",
                "tuition_per_semester": tuition_sem or "",
                "tuition_total": tuition_tot or "",
                "description": raw.description or "",
                "curriculum_highlights": list(raw.curriculum_highlights or []),
                "career_paths": list(raw.career_paths or []),
                "tags": list(raw.tags or []),
                "website_url": raw.website_url or ""
            }


DEFAULT_CHECKPOINT_DIR = str(Path(__file__).resolve().parents[2] / "data" / "agent_states")


def save_course_state_checkpoint(state: CourseAgentState, output_dir: str = DEFAULT_CHECKPOINT_DIR) -> str:
    """Saves serialized course state to checkpoint disk file."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"course_{state.session_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))
    return filepath


def load_course_state_checkpoint(filepath: str) -> CourseAgentState:
    """Loads course state from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CourseAgentState.model_validate(data)
