"""
Deterministic State Reducer for Faculty Extraction Agent
Based on the SKILL.state Architecture & Evaluation: https://arxiv.org/html/2608.26263v2#S5
"""
import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz, process

from app.core.security import sanitize_for_prompt
from scripts.agentic_pipeline.models import (
    ExtractionAgentState,
    FacultyStatePatch,
    RawFacultyProfile
)

# Canonical Thai Academic Title Normalization Table
THAI_TITLES_NORMALIZATION = [
    (re.compile(r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.|ศ\.ดร\.)\s*", re.IGNORECASE), "ศ.ดร."),
    (re.compile(r"^(รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.|รศ\.ดร\.)\s*", re.IGNORECASE), "รศ.ดร."),
    (re.compile(r"^(ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.|ผศ\.ดร\.)\s*", re.IGNORECASE), "ผศ.ดร."),
    (re.compile(r"^(ศาสตราจารย์|ศ\.)\s*", re.IGNORECASE), "ศ."),
    (re.compile(r"^(รองศาสตราจารย์|รศ\.)\s*", re.IGNORECASE), "รศ."),
    (re.compile(r"^(ผู้ช่วยศาสตราจารย์|ผศ\.)\s*", re.IGNORECASE), "ผศ."),
    (re.compile(r"^(อาจารย์\s*ดร\.|อ\.\s*ดร\.|อ\.ดร\.)\s*", re.IGNORECASE), "อ.ดร."),
    (re.compile(r"^(อาจารย์|อ\.)\s*", re.IGNORECASE), "อ."),
    (re.compile(r"^(ดร\.)\s*", re.IGNORECASE), "ดร."),
]

# Strips common academic titles from Thai names for clean fuzzy deduplication
TITLE_STRIP_REGEX = re.compile(
    r"^(ศาสตราจารย์\s*เกียรติคุณ|ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์\s*ดร\.|อาจารย์|ดร\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.|ทพ\.|ภก\.|ภญ\.|สพ\.ญ\.|สพ\.ญ\.|นาย|นาง|นางสาว)\s*",
    re.IGNORECASE
)

# Detect and redact Thai phone numbers (PDPA compliance)
PHONE_REGEX = re.compile(r"(0\d{1,2}[-\s]?\d{3}[-\s]?\d{3,4}|\+66[-\s]?\d{1,2}[-\s]?\d{3}[-\s]?\d{3,4})")


def normalize_thai_title_and_name(raw_name_th: str, raw_title_th: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Normalizes Thai name and extracts standard title.
    Returns: (cleaned_title_th, cleaned_full_name_th, base_name_without_title)

    Fixes double-title bugs e.g. "ศ.ดร. ศ.ดร. มานะ" -> "ศ.ดร. มานะ"
    """
    text = re.sub(r"\s+", " ", raw_name_th.strip())

    matched_title = raw_title_th.strip() if raw_title_th else None

    # Loop to normalize and remove duplicated leading titles
    detected_title = None
    changed = True
    while changed:
        changed = False
        for pattern, canon_title in THAI_TITLES_NORMALIZATION:
            m = pattern.match(text)
            if m:
                if not detected_title:
                    detected_title = canon_title
                text = text[m.end():].strip()
                changed = True
                break

    final_title = detected_title or matched_title or "อ."
    base_name = text.strip()

    # Re-assemble clean full Thai name
    full_name_th = f"{final_title} {base_name}".strip()

    return final_title, full_name_th, base_name


def redact_pdpa_and_sanitize(text: Optional[str]) -> Optional[str]:
    """Strips phone numbers and invalid control characters (PDPA & Prompt Hygiene)."""
    if not text:
        return None
    cleaned = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    cleaned = cleaned.replace("\x00", "").strip()
    return cleaned


def generate_canonical_id(univ_prefix: str, faculty_prefix: str, base_name: str, index: int) -> str:
    """Generates clean slug ID like kmitl_eng_mana_001."""
    slug_name = re.sub(r"[^a-zA-Z0-9]", "", base_name.lower())[:15] or f"fac_{index:03d}"
    univ_slug = re.sub(r"[^a-zA-Z0-9]", "", univ_prefix.lower())[:10]
    fac_slug = re.sub(r"[^a-zA-Z0-9]", "", faculty_prefix.lower())[:10]
    return f"{univ_slug}_{fac_slug}_{slug_name}_{index:03d}"


class FacultyStateReducer:
    """
    Deterministic State Reducer (Pure Python + RapidFuzz).
    Applies incoming FacultyStatePatch to update ExtractionAgentState without LLM hallucination.
    """

    def __init__(self, fuzzy_threshold: float = 90.0, db_session=None):
        self.fuzzy_threshold = fuzzy_threshold
        self.db_session = db_session

    def apply_patch(
        self,
        state: ExtractionAgentState,
        patch: FacultyStatePatch,
        step_tokens: int = 0
    ) -> ExtractionAgentState:
        """Applies atomic patch to state deterministically."""
        state.step_count += 1
        state.total_tokens_used += step_tokens

        # 1. Update Discovered URLs (FIFO Queue & deduplication)
        for url in patch.discovered_urls:
            url_clean = url.strip()
            if (
                url_clean
                and url_clean not in state.visited_urls
                and url_clean not in state.pending_urls
                and url_clean not in state.failed_urls
            ):
                state.pending_urls.append(url_clean)

        # 2. Mark Failed/Empty Pages
        for failed_url in patch.unreachable_or_empty_pages:
            failed_clean = failed_url.strip()
            if failed_clean in state.pending_urls:
                state.pending_urls.remove(failed_clean)
            if failed_clean not in state.failed_urls:
                state.failed_urls.append(failed_clean)

        # 3. Process Newly Extracted Profiles
        for raw in patch.new_profiles:
            self._process_single_profile(state, raw)

        # 4. Process Direct Field Updates
        if isinstance(patch.updated_profile_fields, dict):
            for fid, updates in patch.updated_profile_fields.items():
                if fid in state.faculties and isinstance(updates, dict):
                    for k, v in updates.items():
                        if k in state.faculties[fid]:
                            if isinstance(state.faculties[fid][k], list) and isinstance(v, list):
                                existing_list = state.faculties[fid][k]
                                for item in v:
                                    if item not in existing_list:
                                        existing_list.append(item)
                            else:
                                state.faculties[fid][k] = v

        return state

    def _process_single_profile(self, state: ExtractionAgentState, raw: RawFacultyProfile):
        """Validates, normalizes, deduplicates, and adds or merges a single profile."""
        title_th, full_name_th, base_name_th = normalize_thai_title_and_name(
            raw.full_name_th, raw.academic_title_th
        )

        email_clean = (raw.email.strip().lower() if raw.email else None)
        if email_clean:
            email_clean = redact_pdpa_and_sanitize(email_clean)

        # --- Deduplication Check ---
        existing_id = self._find_existing_faculty_id(state, base_name_th, email_clean)

        if existing_id:
            # Merge enriched fields into existing record
            self._merge_into_existing(state.faculties[existing_id], raw)
            return

        # --- Create New Verified Profile ---
        univ_prefix = state.target_university_en or "univ"
        fac_prefix = state.target_faculty_en or "dept"
        new_id = generate_canonical_id(
            univ_prefix,
            fac_prefix,
            raw.last_name or base_name_th,
            len(state.faculties) + 1
        )

        # Clean publications and sanitize
        clean_pubs = []
        for p in raw.featured_publications:
            sanitized_p = redact_pdpa_and_sanitize(p)
            if sanitized_p and sanitized_p not in clean_pubs:
                clean_pubs.append(sanitized_p)

        clean_interests = []
        for item in raw.research_interests:
            sanitized_i = redact_pdpa_and_sanitize(item)
            if sanitized_i and sanitized_i not in clean_interests:
                clean_interests.append(sanitized_i)

        clean_education = []
        for edu in raw.education:
            sanitized_e = redact_pdpa_and_sanitize(edu)
            if sanitized_e and sanitized_e not in clean_education:
                clean_education.append(sanitized_e)

        en_full_name = f"{raw.first_name or ''} {raw.last_name or ''}".strip()

        faculty_dict = {
            "id": new_id,
            "university": state.target_university_en,
            "university_th": state.target_university_th,
            "faculty": state.target_faculty_en or "",
            "faculty_th": state.target_faculty_th or "",
            "department": raw.department_th or "",
            "department_th": raw.department_th or "",
            "academic_title": title_th,
            "academic_title_th": title_th,
            "first_name": raw.first_name or "",
            "last_name": raw.last_name or "",
            "full_name": en_full_name,
            "full_name_th": full_name_th,
            "role": "อาจารย์ประจำ",
            "email": email_clean or "",
            "image_url": raw.image_url or "",
            "profile_url": raw.profile_url or "",
            "education": clean_education,
            "research_interests": clean_interests,
            "featured_publications": clean_pubs,
            "scholar_url": raw.scholar_url or "",
            "confidence_score": 0.95
        }

        # Store in state
        state.faculties[new_id] = faculty_dict
        state.dedup_thai_names[base_name_th] = new_id
        if email_clean:
            state.dedup_emails[email_clean] = new_id

    def _find_existing_faculty_id(
        self,
        state: ExtractionAgentState,
        base_name_th: str,
        email: Optional[str]
    ) -> Optional[str]:
        """Finds existing record using exact email/name match or RapidFuzz fuzzy match."""
        # 1. Exact Email Check
        if email and email in state.dedup_emails:
            return state.dedup_emails[email]

        # 2. Exact Thai Base Name Check
        if base_name_th in state.dedup_thai_names:
            return state.dedup_thai_names[base_name_th]

        # 3. Fuzzy Thai Base Name Check across In-Memory State
        if state.dedup_thai_names:
            existing_names = list(state.dedup_thai_names.keys())
            match = process.extractOne(
                base_name_th,
                existing_names,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=self.fuzzy_threshold
            )
            if match:
                matched_name, score, _ = match
                return state.dedup_thai_names[matched_name]

        # 4. Optional: Database pre-check if session is attached
        if self.db_session:
            try:
                from app.models.db_models import FacultyDB
                # Search by exact email in DB
                if email:
                    db_fac = self.db_session.query(FacultyDB).filter(FacultyDB.email == email).first()
                    if db_fac:
                        return db_fac.id
            except Exception:
                pass

        return None

    def _merge_into_existing(self, target: Dict[str, Any], new_raw: RawFacultyProfile):
        """Deep merges new data fields into existing faculty dict."""
        if not target.get("email") and new_raw.email:
            target["email"] = redact_pdpa_and_sanitize(new_raw.email)
        if not target.get("image_url") and new_raw.image_url:
            target["image_url"] = new_raw.image_url
        if not target.get("scholar_url") and new_raw.scholar_url:
            target["scholar_url"] = new_raw.scholar_url
        if not target.get("profile_url") and new_raw.profile_url:
            target["profile_url"] = new_raw.profile_url

        # Merge Lists
        for pub in new_raw.featured_publications:
            clean_p = redact_pdpa_and_sanitize(pub)
            if clean_p and clean_p not in target.setdefault("featured_publications", []):
                target["featured_publications"].append(clean_p)

        for interest in new_raw.research_interests:
            clean_i = redact_pdpa_and_sanitize(interest)
            if clean_i and clean_i not in target.setdefault("research_interests", []):
                target["research_interests"].append(clean_i)

        for edu in new_raw.education:
            clean_e = redact_pdpa_and_sanitize(edu)
            if clean_e and clean_e not in target.setdefault("education", []):
                target["education"].append(clean_e)


def save_state_checkpoint(state: ExtractionAgentState, output_dir: str = "data/agent_states") -> str:
    """Saves agent state to a JSON checkpoint file."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{state.session_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)
    return file_path


def load_state_checkpoint(file_path: str) -> ExtractionAgentState:
    """Restores an agent state from a JSON checkpoint file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ExtractionAgentState.model_validate(data)
