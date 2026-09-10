import pytest
import os
import sys
from pathlib import Path

BACKEND_DIR = str(Path(__file__).resolve().parents[1])
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import json
from scripts.agentic_pipeline.models import (
    ExtractionAgentState,
    FacultyStatePatch,
    RawFacultyProfile
)
from scripts.agentic_pipeline.state_reducer import (
    FacultyStateReducer,
    normalize_thai_title_and_name,
    redact_pdpa_and_sanitize,
    save_state_checkpoint,
    load_state_checkpoint
)
from app.models.quiz_schema import (
    CareerRecommendation,
    CareerProfileResponse,
    RiasecBreakdown
)


def test_thai_title_normalization():
    """Verify Thai title cleanup and deduplication of repeated titles."""
    # Test case 1: Double title issue (ศ.ดร. ศ.ดร.)
    title, full_name, base_name = normalize_thai_title_and_name("ศ.ดร. ศ.ดร. มานะ ใจดี")
    assert title == "ศ.ดร."
    assert full_name == "ศ.ดร. มานะ ใจดี"
    assert base_name == "มานะ ใจดี"

    # Test case 2: Long Thai title without abbreviation
    title, full_name, base_name = normalize_thai_title_and_name("รองศาสตราจารย์ ดร. สมชาย มุ่งมั่น")
    assert title == "รศ.ดร."
    assert full_name == "รศ.ดร. สมชาย มุ่งมั่น"
    assert base_name == "สมชาย มุ่งมั่น"

    # Test case 3: Plain Dr.
    title, full_name, base_name = normalize_thai_title_and_name("ดร. วิภา รักษ์ชาติ")
    assert title == "ดร."
    assert full_name == "ดร. วิภา รักษ์ชาติ"


def test_pdpa_phone_redaction():
    """Verify Thai phone numbers are redacted to comply with PDPA."""
    text_with_phone = "ติดต่อเบอร์ 081-234-5678 หรือ 02-1234567 อีเมล test@chula.ac.th"
    redacted = redact_pdpa_and_sanitize(text_with_phone)
    assert "081-234-5678" not in redacted
    assert "02-1234567" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "test@chula.ac.th" in redacted


def test_state_reducer_dedup_and_enrichment():
    """Verify deterministic state reduction, deduplication, and deep merging."""
    state = ExtractionAgentState(
        session_id="test_session_001",
        target_university_th="มหาวิทยาลัยเชียงใหม่",
        target_university_en="Chiang Mai University",
        target_faculty_th="คณะวิศวกรรมศาสตร์",
        target_faculty_en="Faculty of Engineering"
    )

    reducer = FacultyStateReducer(fuzzy_threshold=85.0)

    # Patch 1: Insert first raw profile
    raw_prof_1 = RawFacultyProfile(
        id="cmu_eng_ee_001",
        full_name_th="ผศ.ดร. กิตติศักดิ์ เจริญสุข",
        academic_title_th="ผศ.ดร.",
        first_name="Kittisak",
        last_name="Charoensuk",
        email="kittisak@cmu.ac.th",
        education=["Ph.D. in Electrical Engineering, CMU"],
        research_interests=["Smart Grid", "Renewable Energy"],
        featured_publications=["Smart Inverter Optimization 2024"]
    )

    patch_1 = FacultyStatePatch(
        discovered_urls=["https://eng.cmu.ac.th/staff/cpe"],
        new_profiles=[raw_prof_1],
        summary_of_changes="Extracted 1 professor from EE"
    )

    state = reducer.apply_patch(state, patch_1, step_tokens=450)

    # The reducer derives a CANONICAL id from target_university_en +
    # target_faculty_en + last_name and IGNORES the caller-supplied raw.id
    # (see generate_canonical_id / apply_patch, state_reducer.py:173-180).
    # So we assert the real contract instead of pinning a literal slug that
    # legitimately changes if the truncation scheme is ever tuned.
    assert len(state.faculties) == 1
    fac_id = next(iter(state.faculties))
    assert fac_id.startswith("chiangmai")   # university prefix
    assert "charoensuk" in fac_id            # last_name slug
    assert state.faculties[fac_id]["id"] == fac_id
    assert state.step_count == 1
    assert state.total_tokens_used == 450
    assert "https://eng.cmu.ac.th/staff/cpe" in state.pending_urls

    # Patch 2: Discovered duplicate with slightly different name formatting and richer publication data
    raw_prof_2_dup = RawFacultyProfile(
        full_name_th="ผู้ช่วยศาสตราจารย์ ดร. กิตติศักดิ์ เจริญสุข",  # Slightly different title representation
        email="kittisak@cmu.ac.th",
        scholar_url="https://scholar.google.com/citations?user=xyz",
        featured_publications=["Advanced Microgrid Control 2025"]
    )

    patch_2 = FacultyStatePatch(
        new_profiles=[raw_prof_2_dup],
        summary_of_changes="Extracted another page containing Dr. Kittisak"
    )

    state = reducer.apply_patch(state, patch_2, step_tokens=350)

    # Should NOT increase count, but should merge scholar_url and new publication
    assert len(state.faculties) == 1
    stored = state.faculties[fac_id]
    assert stored["scholar_url"] == "https://scholar.google.com/citations?user=xyz"
    assert "Advanced Microgrid Control 2025" in stored["featured_publications"]
    assert "Smart Inverter Optimization 2024" in stored["featured_publications"]


def test_checkpointing_roundtrip(tmp_path):
    """Verify that agent state can be serialized and perfectly restored."""
    state = ExtractionAgentState(
        session_id="test_checkpoint_session",
        target_university_th="จุฬาลงกรณ์มหาวิทยาลัย",
        target_university_en="Chulalongkorn University",
        step_count=5,
        total_tokens_used=2400
    )
    state.faculties["cu_001"] = {
        "id": "cu_001",
        "full_name_th": "ศ.ดร. สุรศักดิ์ วิทยา",
        "research_interests": ["Bioinformatics", "Genomics"]
    }

    checkpoint_file = save_state_checkpoint(state, output_dir=str(tmp_path))
    assert os.path.exists(checkpoint_file)

    restored = load_state_checkpoint(checkpoint_file)
    assert restored.session_id == state.session_id
    assert restored.total_tokens_used == 2400
    assert "cu_001" in restored.faculties
    assert restored.faculties["cu_001"]["full_name_th"] == "ศ.ดร. สุรศักดิ์ วิทยา"


def test_english_academic_title_normalization():
    """Verify bilingual title normalization handles English prefixes and preserves Thai names."""
    # 1. English Prof. Dr.
    t, full, base = normalize_thai_title_and_name("Prof. Dr. David Smith")
    assert t == "ศ.ดร."
    assert full == "ศ.ดร. David Smith"
    assert base == "David Smith"

    # 2. English Assoc. Prof. Dr.
    t, full, base = normalize_thai_title_and_name("Assoc. Prof. Dr.LEE KIAN CHENG")
    assert t == "รศ.ดร."
    assert full == "รศ.ดร. LEE KIAN CHENG"
    assert base == "LEE KIAN CHENG"

    # 3. Stacked Thai default + English Dr. (e.g. crawler output before fix)
    t, full, base = normalize_thai_title_and_name("อ. Dr. Aye Hninn Khine")
    assert t == "อ.ดร."
    assert full == "อ.ดร. Aye Hninn Khine"
    assert base == "Aye Hninn Khine"

    # 4. Stacked Thai default + English Assoc.Prof.Dr.
    t, full, base = normalize_thai_title_and_name("อ. Assoc.Prof.Dr.Fredric William Swierczek")
    assert t == "รศ.ดร."
    assert full == "รศ.ดร. Fredric William Swierczek"
    assert base == "Fredric William Swierczek"

    # 5. Standalone Dr.
    t, full, base = normalize_thai_title_and_name("Dr. Alexander Horstmann")
    assert t == "ดร."
    assert full == "ดร. Alexander Horstmann"
    assert base == "Alexander Horstmann"

    # 6. Safety invariant: Thai names starting with 'ดร' must NOT have their names mutilated
    t, full, base = normalize_thai_title_and_name("ดรุณี ใจกล้า")
    assert base == "ดรุณี ใจกล้า"
    assert "ดรุณี" in full

    # 7. Academic rank precedence: official stored title 'รศ.ดร.' overrides partial 'Dr.' token
    t, full, base = normalize_thai_title_and_name("Dr. Somchart Fugkeaw", raw_title_th="รศ.ดร.")
    assert t == "รศ.ดร."
    assert full == "รศ.ดร. Somchart Fugkeaw"


def test_quiz_schema_null_coercion():
    """Verify Pydantic v2 gracefully coerces None to [] for LLM payload stability."""
    rec = CareerRecommendation(
        title="AI Engineer",
        description="Build machine learning systems",
        match_percentage=95,
        skills=None  # Coerced from None to []
    )
    assert rec.skills == []

    resp = CareerProfileResponse(
        tier="standard",
        archetype_title="The Analytical Builder",
        archetype_code="IR (Investigative-Realistic)",
        archetype_description="Enjoys deep technical exploration",
        riasec_scores=RiasecBreakdown(),
        personality_summary="Focused problem-solver",
        strengths=None,
        ideal_work_environment="Tech Lab",
        lifestyle_highlights=None,
        growth_advice="Keep learning",
        share_quote="Dream big",
        top_careers=None,
        recommended_courses=None
    )
    assert resp.strengths == []
    assert resp.lifestyle_highlights == []
    assert resp.top_careers == []
    assert resp.recommended_courses == []

