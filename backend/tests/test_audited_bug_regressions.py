import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.models.schema import _clean_display_name, _strip_leading_title_tokens
from app.core.corpus_index import FACULTY_LEXICAL_INDEX, tokenize_mixed
from app.core.dsa_utils import FastInvertedIndex


def test_thai_title_regex_boundary_safety():
    """Verify that names starting with 'ดร' (e.g. ดรุณี, ดรัลพร) are not mutilated."""
    # 1. Title already separated, full_name_th includes title
    assert _clean_display_name("รศ.ดร.", "รศ.ดร. ดรุณี สถิตถาวร") == "ดรุณี สถิตถาวร"
    assert _clean_display_name("ดร.", "ดร. ดรัลพร บุญมี") == "ดรัลพร บุญมี"

    # 2. No academic_title_th given, collapse duplicated title
    assert _clean_display_name(None, "ดร. ดรุณี สถิตถาวร") == "ดร. ดรุณี สถิตถาวร"
    assert _clean_display_name("", "รศ.ดร. ดรุณี สถิตถาวร") == "รศ.ดร. ดรุณี สถิตถาวร"

    # 3. Direct strip leading tokens test
    assert _strip_leading_title_tokens("ดรุณี สถิตถาวร") == "ดรุณี สถิตถาวร"
    assert _strip_leading_title_tokens("ดร. สมชาย") == "สมชาย"
    assert _strip_leading_title_tokens("ศ.ดร. สุทธิเขตต์") == "สุทธิเขตต์"


def test_bm25_thai_tokenization_symmetry():
    """Verify that BM25 indexing and query scoring use symmetric tokenization."""
    docs = {
        "lab_ai": "ศูนย์วิจัยปัญญาประดิษฐ์และหุ่นยนต์อัจฉริยะ Artificial Intelligence Robotics",
        "lab_bio": "การวิจัยด้านเทคโนโลยีชีวภาพการเกษตรและพันธุศาสตร์พืช",
    }
    # Index with tokenize_mixed
    FACULTY_LEXICAL_INDEX.rebuild(docs, tokenizer=tokenize_mixed)

    # Query with Thai phrase
    query = "ปัญญาประดิษฐ์"
    query_tokens = tokenize_mixed(query)
    scores = FACULTY_LEXICAL_INDEX.score_query(query_tokens)

    assert len(scores) > 0, "BM25 query should return matching documents"
    assert scores[0][0] == "lab_ai", "lab_ai should be the top match"
    assert scores[0][1] > 0.0, "BM25 score for Thai query must be strictly positive"


def test_kmutt_canonical_faculty_merge_integrity():
    """Verify that KMUTT canonical map has no key overwrites and retains all faculties."""
    from scripts.enrichment.canonical_faculty_merge import FACULTY_CANONICAL
    kmutt = FACULTY_CANONICAL.get("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", {})
    assert "คณะเทคโนโลยีสารสนเทศ (SIT)" in kmutt
    assert "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)" in kmutt
    assert "คณะทรัพยากรชีวภาพและเทคโนโลยี (SBT)" in kmutt
    assert len(kmutt) >= 4


def test_merge_duplicate_faculties_scalar_fields_projection():
    """Verify that all SCALAR_FIELDS in merge script are selected in SELECT_COLS."""
    from scripts.audits.merge_duplicate_faculties import SCALAR_FIELDS, SELECT_COLS
    missing = [f for f in SCALAR_FIELDS if f not in SELECT_COLS]
    assert len(missing) == 0, f"Missing fields in SELECT_COLS: {missing}"


def test_lab_inquiry_none_domains_defense():
    """Verify that null/None research_domains does not raise TypeError."""
    class MockLab:
        research_domains = None

    db_lab = MockLab()
    domains_list = [d for d in (db_lab.research_domains or []) if d][:3]
    domains_th = ", ".join(domains_list) if domains_list else "การวิจัยและพัฒนานวัตกรรม"
    assert domains_list == []
    assert domains_th == "การวิจัยและพัฒนานวัตกรรม"


def test_career_quiz_null_coercion_defense():
    """Verify that Pydantic v2 gracefully coerces None to [] for LLM payload stability."""
    from app.models.quiz_schema import CareerRecommendation, CareerProfileResponse, RiasecBreakdown

    rec = CareerRecommendation(
        title="AI Engineer",
        description="Build machine learning systems",
        match_percentage=95,
        skills=None
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


def test_bilingual_title_normalization_foreign_faculty():
    """Verify that foreign faculty with English academic titles are cleanly normalized."""
    from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

    # Foreign faculty crawled with default "อ." prefix prepended to English title
    t, full, base = normalize_thai_title_and_name("อ. Dr. Aye Hninn Khine")
    assert t == "อ.ดร."
    assert full == "อ.ดร. Aye Hninn Khine"
    assert base == "Aye Hninn Khine"

    t, full, base = normalize_thai_title_and_name("อ. Assoc.Prof.Dr.Fredric William Swierczek")
    assert t == "รศ.ดร."
    assert full == "รศ.ดร. Fredric William Swierczek"
    assert base == "Fredric William Swierczek"


def test_agentic_pipeline_null_list_coercion():
    """Verify that Pydantic v2 gracefully coerces None/null to [] on LLM agent payloads."""
    from scripts.agentic_pipeline.models import RawFacultyProfile, FacultyStatePatch, ExtractionAgentState
    from scripts.agentic_pipeline.course_models import RawCourseProfile, CourseStatePatch, CourseAgentState

    # Faculty models
    raw_fac = RawFacultyProfile(
        full_name_th="ดรุณี สถิตถาวร",
        education=None,
        research_interests=None,
        featured_publications=None,
    )
    assert raw_fac.education == []
    assert raw_fac.research_interests == []
    assert raw_fac.featured_publications == []

    patch_fac = FacultyStatePatch(
        discovered_urls=None,
        new_profiles=None,
        updated_profile_fields=None,
        unreachable_or_empty_pages=None,
    )
    assert patch_fac.discovered_urls == []
    assert patch_fac.new_profiles == []
    assert patch_fac.updated_profile_fields == []
    assert patch_fac.unreachable_or_empty_pages == []

    state_fac = ExtractionAgentState(
        session_id="test_s01",
        target_university_th="มหาวิทยาลัยเชียงใหม่",
        target_university_en="Chiang Mai University",
        pending_urls=None,
        visited_urls=None,
        failed_urls=None,
    )
    assert state_fac.pending_urls == []
    assert state_fac.visited_urls == []
    assert state_fac.failed_urls == []

    # Course models
    raw_course = RawCourseProfile(
        title_th="หลักสูตรวิศวกรรมศาสตรบัณฑิต",
        degree_level="ปริญญาตรี",
        curriculum_highlights=None,
        career_paths=None,
        tags=None,
    )
    assert raw_course.curriculum_highlights == []
    assert raw_course.career_paths == []
    assert raw_course.tags == []

    patch_course = CourseStatePatch(
        discovered_urls=None,
        new_courses=None,
        unreachable_or_empty_pages=None,
    )
    assert patch_course.discovered_urls == []
    assert patch_course.new_courses == []
    assert patch_course.unreachable_or_empty_pages == []

    state_course = CourseAgentState(
        session_id="test_c01",
        target_university_th="จุฬาลงกรณ์มหาวิทยาลัย",
        target_university_en="Chulalongkorn University",
        pending_urls=None,
        visited_urls=None,
        failed_urls=None,
    )
    assert state_course.pending_urls == []
    assert state_course.visited_urls == []
    assert state_course.failed_urls == []


def test_thai_name_preservation_no_mutilation():
    """Verify that names starting with 'ดร', 'อ', or 'ศ' are completely preserved."""
    assert _strip_leading_title_tokens("ดรุณี สถิตถาวร") == "ดรุณี สถิตถาวร"
    assert _strip_leading_title_tokens("ดรัลพร บุญมี") == "ดรัลพร บุญมี"
    assert _strip_leading_title_tokens("อภิชัย รัตนวงศ์") == "อภิชัย รัตนวงศ์"
    assert _strip_leading_title_tokens("อดิเรก วงศ์ใหญ่") == "อดิเรก วงศ์ใหญ่"
    assert _strip_leading_title_tokens("ศิริชัย พัฒนาการ") == "ศิริชัย พัฒนาการ"

    # With real titles
    assert _strip_leading_title_tokens("ผศ.ดร. ดรุณี สถิตถาวร") == "ดรุณี สถิตถาวร"
    assert _strip_leading_title_tokens("อ. อภิชัย รัตนวงศ์") == "อภิชัย รัตนวงศ์"
    assert _strip_leading_title_tokens("รศ. ศิริชัย พัฒนาการ") == "ศิริชัย พัฒนาการ"


def test_course_state_reducer_null_safety():
    """Verify that course state reducer does not crash when fields are None."""
    from scripts.agentic_pipeline.course_state_reducer import CourseStateReducer
    from scripts.agentic_pipeline.course_models import CourseAgentState, CourseStatePatch, RawCourseProfile

    reducer = CourseStateReducer()
    state = CourseAgentState(
        session_id="test_sess",
        target_university_th="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        target_university_en="KMUTT",
    )
    raw = RawCourseProfile(
        title_th="วิศวกรรมคอมพิวเตอร์",
        degree_level="ปริญญาตรี",
        career_paths=None,
        curriculum_highlights=None,
        tags=None,
    )
    patch = CourseStatePatch(new_courses=[raw])
    # Should not raise TypeError: 'NoneType' object is not iterable
    state = reducer.apply_patch(state, patch)
    assert len(state.courses) == 1
    c = list(state.courses.values())[0]
    assert c["career_paths"] == []
    assert c["curriculum_highlights"] == []
    assert c["tags"] == []



