import pytest
import os
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

    assert len(state.faculties) == 1
    assert "cmu_eng_ee_001" in state.faculties
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
    stored = state.faculties["cmu_eng_ee_001"]
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
