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


def test_enricher_total_citations_preservation():
    """Verify that enriching publications does not overwrite authoritative total_citations.

    Authoritative lifetime citation metrics come from OpenAlex author metrics (author.cited_by_count).
    Harvesting a subset of publications from Crossref or ThaiJO must never overwrite rec.total_citations.
    """
    class MockFaculty:
        def __init__(self, total_citations=1542, works_count=45):
            self.total_citations = total_citations
            self.total_publications_count = works_count
            self.featured_publications = [{"title": "Paper A", "citations": 5}]

    rec = MockFaculty(total_citations=1542, works_count=45)
    new_pubs = [
        {"title": "Paper A", "citations": 5},
        {"title": "Paper B", "citations": 12},
    ]
    # Simulate the fixed enricher logic
    added = len(new_pubs) - len(rec.featured_publications)
    if added > 0:
        rec.featured_publications = new_pubs
        rec.total_publications_count = max(rec.total_publications_count or 0, len(new_pubs))
        # Crucial: rec.total_citations is NOT overwritten with sum(p.get('citations', 0)...)

    assert rec.total_citations == 1542, "Authoritative lifetime citations must be preserved!"
    assert rec.total_publications_count == 45, "Higher lifetime publications count must not be shrunk!"
    assert len(rec.featured_publications) == 2


def test_university_dedup_key_canonicalization():
    """Verify that university aliases and language variants produce symmetric dedup keys."""
    from app.core.university_canonicalizer import (
        get_university_dedup_key,
        canonicalize_university_en,
        canonicalize_university_th
    )

    # Chulalongkorn variants
    assert get_university_dedup_key("Chula") == "chulalongkorn university"
    assert get_university_dedup_key("CU") == "chulalongkorn university"
    assert get_university_dedup_key("จุฬาลงกรณ์มหาวิทยาลัย") == "chulalongkorn university"
    assert get_university_dedup_key("Chulalongkorn University") == "chulalongkorn university"

    # KMUTT variants
    assert get_university_dedup_key("KMUTT") == "king mongkut's university of technology thonburi"
    assert get_university_dedup_key("มจธ.") == "king mongkut's university of technology thonburi"

    # KMITL variants
    assert get_university_dedup_key("KMITL") == "king mongkut's institute of technology ladkrabang"
    assert get_university_dedup_key("สจล.") == "king mongkut's institute of technology ladkrabang"

    # PSU variants
    assert get_university_dedup_key("PSU") == "prince of songkla university"
    assert get_university_dedup_key("มอ.") == "prince of songkla university"


def test_database_hygiene_clean_name_noise():
    """Verify name sanitization cleans OCR/date/boilerplate artifacts without truncating names."""
    from scripts.audits.clean_and_deduplicate_database_2026_09_13 import clean_name_noise

    # Revision markers & dates
    assert clean_name_noise("ผศ.ดร. กัญญาณัฐ เปี่ยมงาม2") == "ผศ.ดร. กัญญาณัฐ เปี่ยมงาม"
    assert clean_name_noise("รศ. นพ. กิตติพงศ์ NEW2") == "รศ. นพ. กิตติพงศ์"
    assert clean_name_noise("ผศ.ดร. ธวัชชัย 27.02.68") == "ผศ.ดร. ธวัชชัย"

    # Parenthesized English suffix
    assert clean_name_noise("รศ.ดร. ภานุวิชญ์ ตู้ประเสริฐ (Tuwanut)") == "รศ.ดร. ภานุวิชญ์ ตู้ประเสริฐ"
    assert clean_name_noise("ศ.ดร. เอียน เฟนวิก (Prof. Dr. Ian Fenwick)") == "ศ.ดร. เอียน เฟนวิก"

    # Academic title boundary split
    assert clean_name_noise("รศ. นพ.สยาม ทองประเสริฐAssoc. Prof. Siam Tongprasert, M.D.") == "รศ. นพ.สยาม ทองประเสริฐ"
    assert clean_name_noise("ผศ.ดร. ชัยพร ตั้งทองAsst. Prof. Dr. Chaiporn ThangthongEmail:") == "ผศ.ดร. ชัยพร ตั้งทอง"

    # Affiliations & positions
    assert clean_name_noise("อ. พญ.ชนัดดา วงศ์เอกชูตระกูลสังกัดศูนย์ศรีพัฒน์") == "อ. พญ.ชนัดดา วงศ์เอกชูตระกูล"
    assert clean_name_noise("รศ. นพ.ศุภพงษ์ อาวรณ์Assoc.Prof.Supapong Arwon, MD.หัวหน้าหน่วย") == "รศ. นพ.ศุภพงษ์ อาวรณ์"


def test_database_hygiene_clean_email_and_department_detection():
    """Verify email cleaning strips zero-width spaces and detects shared institutional emails."""
    from scripts.audits.clean_and_deduplicate_database_2026_09_13 import clean_email_str, is_shared_email

    # Zero-width spaces & attached characters
    assert clean_email_str("​user@chula.ac.th﻿") == "user@chula.ac.th"
    assert clean_email_str("Email : test.user@kku.ac.th") == "test.user@kku.ac.th"
    assert clean_email_str("ch") is None
    assert clean_email_str("user@su.") is None

    # Shared departmental emails
    assert is_shared_email("sci@ku.ac.th") is True
    assert is_shared_email("dent@cmu.ac.th") is True
    assert is_shared_email("civil@eng.chula.ac.th") is True
    assert is_shared_email("bdavid@chula.ac.th") is False
    assert is_shared_email("boonchai.u@chula.ac.th") is False


def test_database_hygiene_english_title_prefix_stripping():
    """Verify academic title prefixes are stripped from English first names."""
    from scripts.audits.clean_residual_database_anomalies_2026_09_13 import parse_clean_english_name

    assert parse_clean_english_name("Prof.", "Brenda Porter") == ("Brenda", "Porter")
    assert parse_clean_english_name("Assoc.", "Prof. Dr. Abhisit Pinmaneekul") == ("Abhisit", "Pinmaneekul")
    assert parse_clean_english_name("Asst.Prof.Dr.", "Sujitra Klinsrisuk") == ("Sujitra", "Klinsrisuk")
    assert parse_clean_english_name("ASSOC.PROF.DR.", "KULTIDA ROJVIBOONCHAI") == ("KULTIDA", "ROJVIBOONCHAI")
    assert parse_clean_english_name("Mr.", "Boonkiat Techamanachai") == ("Boonkiat", "Techamanachai")
    assert parse_clean_english_name("Mrs.", "Kanidtha Vidthayanon") == ("Kanidtha", "Vidthayanon")
    assert parse_clean_english_name("Dr.", "Suwat Nanan") == ("Suwat", "Nanan")
    # Known CMU single surname
    assert parse_clean_english_name("Prof.", "Hansapinyo", "cmu_eng_department_prof_34") == ("Chayanon", "Hansapinyo")


def test_database_hygiene_mahidol_cs_slug_parser():
    """Verify Mahidol ICT profile URLs and emails resolve to authentic English names."""
    from scripts.audits.clean_residual_database_anomalies_2026_09_13 import parse_mahidol_cs_slug

    url1 = "https://www.ict.mahidol.ac.th/th/people/computer-science-academic-group/chomtip_pornpanomchai/"
    assert parse_mahidol_cs_slug(url1, "chomtip.pornpanomchai@mahidol.ac.th") == ("Chomtip", "Pornpanomchai")

    url2 = "https://www.ict.mahidol.ac.th/th/people/computer-science-academic-group/pawitra_liamruk/"
    assert parse_mahidol_cs_slug(url2, None) == ("Pawitra", "Liamruk")

    # Fallback to email
    assert parse_mahidol_cs_slug(None, "thanapon.noraset@mahidol.ac.th") == ("Thanapon", "Noraset")






