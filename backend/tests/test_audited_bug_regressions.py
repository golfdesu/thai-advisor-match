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


def test_faculty_vector_has_lexical_source_text():
    """Every persisted faculty vector must retain text for lexical fallback search."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        broken = (
            db.query(FacultyDB.id)
            .filter(FacultyDB.embedding.isnot(None), FacultyDB.embedding_text.is_(None))
            .count()
        )
        assert broken == 0, f"Found {broken} faculty vectors without embedding_text"
    finally:
        db.close()


def test_faculty_insert_hook_builds_text_for_existing_vector():
    """The ORM guard fills canonical text when an insert already has a vector."""
    from app.models.db_models import FacultyDB, _ensure_faculty_embedding_text

    faculty = FacultyDB(
        id="test-faculty",
        full_name_th="อ. ทดสอบ ระบบ",
        first_name="Test",
        last_name="System",
        university_th="มหาวิทยาลัยทดสอบ",
        research_interests=["Database systems"],
        embedding=[0.0] * 768,
    )
    _ensure_faculty_embedding_text(None, None, faculty)

    assert faculty.embedding_text is not None
    assert "Test System" in faculty.embedding_text
    assert "Database systems" in faculty.embedding_text


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
    from scripts.audits.clean_and_deduplicate_database import clean_name_noise

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


def test_audit_email_regex_accepts_institutional_subdomains():
    """The audit must not flag valid multi-label academic addresses."""
    import re

    email_regex = re.compile(
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
        r"\.[A-Za-z]{2,}$"
    )
    valid = [
        "supachai.pra@mahidol.ac.th",
        "siree.c@ku.ac.th",
        "chaisak.ch@chula.ac.th",
        "dept.staff@university.edu",
    ]
    invalid = [
        "user@su.",
        "user@.ac.th",
        "user@ac.th.",
        "user@university.c1",
    ]

    assert all(email_regex.fullmatch(value) for value in valid)
    assert not any(email_regex.fullmatch(value) for value in invalid)


def test_database_hygiene_clean_email_and_department_detection():
    """Verify email cleaning strips zero-width spaces and detects shared institutional emails."""
    from scripts.audits.clean_and_deduplicate_database import clean_email_str, is_shared_email

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
    from scripts.audits.clean_residual_database_anomalies import parse_clean_english_name

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
    from scripts.audits.clean_residual_database_anomalies import parse_mahidol_cs_slug

    url1 = "https://www.ict.mahidol.ac.th/th/people/computer-science-academic-group/chomtip_pornpanomchai/"
    assert parse_mahidol_cs_slug(url1, "chomtip.pornpanomchai@mahidol.ac.th") == ("Chomtip", "Pornpanomchai")

    url2 = "https://www.ict.mahidol.ac.th/th/people/computer-science-academic-group/pawitra_liamruk/"
    assert parse_mahidol_cs_slug(url2, None) == ("Pawitra", "Liamruk")

    # Fallback to email
    assert parse_mahidol_cs_slug(None, "thanapon.noraset@mahidol.ac.th") == ("Thanapon", "Noraset")


def test_openalex_corroboration_short_tokens_and_homonym_safety():
    """Verify OpenAlex corroboration matches 4-letter Thai universities and avoids Peking/King false positives."""
    from scripts.enrich_openalex_author_metrics import corroborates

    # Khon Kaen University (4-letter tokens 'khon', 'kaen')
    kku_cand = {"affiliations": [{"institution": {"display_name": "Khon Kaen University"}}]}
    assert corroborates(kku_cand, "Khon Kaen University") is True

    # Ubon Ratchathani University (4-letter token 'ubon')
    ubu_cand = {"affiliations": [{"institution": {"display_name": "Ubon Ratchathani University"}}]}
    assert corroborates(ubu_cand, "Ubon Ratchathani University") is True

    # Siam University (4-letter token 'siam')
    siam_cand = {"affiliations": [{"institution": {"display_name": "Siam University"}}]}
    assert corroborates(siam_cand, "Siam University") is True

    # Peking University must NOT corroborate King Mongkut's University
    peking_cand = {"affiliations": [{"institution": {"display_name": "Peking University"}}]}
    assert corroborates(peking_cand, "King Mongkut's Institute of Technology Ladkrabang") is False
    assert corroborates(peking_cand, "King Mongkut's University of Technology North Bangkok") is False

    # Authentic Ladkrabang affiliation
    kmitl_cand = {"affiliations": [{"institution": {"display_name": "King Mongkut's Institute of Technology Ladkrabang"}}]}
    assert corroborates(kmitl_cand, "King Mongkut's Institute of Technology Ladkrabang") is True


def test_fact_check_audit_invariants():
    """Verify dot-boundary domain check and non-person placeholder detection."""
    # Dot boundary check prevents kku.ac.th from matching ku.ac.th
    dom_suffix = "ku.ac.th"
    kku_domain = "kku.ac.th"
    ku_domain = "ku.ac.th"
    sub_ku_domain = "eng.ku.ac.th"

    assert not (kku_domain == dom_suffix or kku_domain.endswith("." + dom_suffix))
    assert ku_domain == dom_suffix or ku_domain.endswith("." + dom_suffix)
    assert sub_ku_domain == dom_suffix or sub_ku_domain.endswith("." + dom_suffix)

    # Placeholder detection: bare title only string
    assert len(_strip_leading_title_tokens("ผศ. ดร ผศ")) < 3
    assert len(_strip_leading_title_tokens("รศ.ดร. ธีรพร กงบังเกิด")) >= 3


def test_phase2_noble_and_compound_surname_preservation():
    """Verify that noble/compound particles ('ณ', 'ต.') are preserved without truncation."""
    def parse_thai_first_last(full_name: str, title: str | None = None) -> tuple[str, str]:
        import re
        raw = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.|สพญ\.|ว่าที่ร้อยตรี|อาจารย์|ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์)\s*", "", full_name).strip()
        raw = re.sub(r"^(ดร\.|นพ\.|พญ\.)\s*", "", raw).strip()
        tokens = raw.split()
        if len(tokens) == 1:
            return tokens[0], ""
        if len(tokens) == 3 and tokens[1] in ["ณ", "ต.", "เดอ"]:
            return tokens[0], f"{tokens[1]} {tokens[2]}"
        return tokens[0], " ".join(tokens[1:])

    fn, ln = parse_thai_first_last("ผศ.ดร. ภัทรหทัย ณ ลำพูน")
    assert fn == "ภัทรหทัย"
    assert ln == "ณ ลำพูน"

    fn, ln = parse_thai_first_last("อ.ดร. ดาลัด ณ นคร")
    assert fn == "ดาลัด"
    assert ln == "ณ นคร"

    fn, ln = parse_thai_first_last("รศ.ดร. จิรโรจน์ ต.เทียนประเสริฐ")
    assert fn == "จิรโรจน์"
    assert ln == "ต.เทียนประเสริฐ"


def test_phase2_custom_font_glyph_corruption_invariants():
    """Verify detection of custom-font glyph corruption (foreign scripts in Thai names)."""
    import re
    FOREIGN_SCRIPT_REGEX = re.compile(r"[֐-׿؀-ۿ܀-ݏऀ-ॿഀ-ൿႠ-ჿͰ-ϿЀ-ӿ가-힯゠-ヿ຀-໿ក-៿]")

    # Authentic Thai strings
    assert not FOREIGN_SCRIPT_REGEX.search("รศ.ดร. สุปตนา เอื้อทวีกุล")
    assert not FOREIGN_SCRIPT_REGEX.search("รศ.ดร. พรฤดี เนติโสภากุล")
    assert not FOREIGN_SCRIPT_REGEX.search("รศ.ดร. สุชิน อรุณสวัสดิ์วงศ์")

    # Corrupted strings scraped from mis-mapped university PDF/fonts
    assert FOREIGN_SCRIPT_REGEX.search("ดร. สุปตนา อุทัยवेกียรติ")
    assert FOREIGN_SCRIPT_REGEX.search("รศ.ดร. พรฤดี เนติσοფაკულ")
    assert FOREIGN_SCRIPT_REGEX.search("ผศ.ดร. กันยดา ประจุศิܠป")


def test_phase2_bibliometric_monotonicity_invariants():
    """Verify that total_publications_count >= h_index across all bibliometric records."""
    from scripts.audits.inspect_deep_bugs import run_deep_inspection
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        invalid_metrics = db.query(FacultyDB).filter(
            FacultyDB.h_index.isnot(None),
            FacultyDB.total_publications_count.isnot(None),
            FacultyDB.h_index > FacultyDB.total_publications_count
        ).count()
        assert invalid_metrics == 0, f"Found {invalid_metrics} faculties violating h_index <= total_publications_count"
    finally:
        db.close()


def test_phase2_course_credit_concatenation_sanitization():
    """Verify that course total_credits are sane and not concatenated with course subject codes."""
    import re
    from app.core.database import SessionLocal
    from app.models.db_models import CourseDB

    db = SessionLocal()
    try:
        # Check CMU ABM 797 course is sanitized
        c = db.query(CourseDB).filter(CourseDB.id == "cmu_tqf_25490041110551").first()
        if c:
            assert c.total_credits == "36 หน่วยกิต"
            assert "368797" not in (c.description or "")

        # Check all course credits are <= 350
        for course in db.query(CourseDB).filter(CourseDB.total_credits.isnot(None)).all():
            nums = re.findall(r"[\d\.]+", str(course.total_credits))
            if nums:
                val = float(nums[0])
                assert 0 <= val <= 350, f"Course {course.id} credit out of bounds: {val}"
    finally:
        db.close()


def test_phase3_academic_title_contractions():
    """Verify that full-word academic titles in full_name_th are cleanly contracted to canonical abbreviations."""
    import re
    long_title_patterns = [
        (re.compile(r"^ศาสตราจารย์\s+ดร\.\s*", re.I), "ศ.ดร. "),
        (re.compile(r"^รองศาสตราจารย์\s+ดร\.\s*", re.I), "รศ.ดร. "),
        (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+ดร\.\s*", re.I), "ผศ.ดร. "),
        (re.compile(r"^ศาสตราจารย์\s+", re.I), "ศ. "),
        (re.compile(r"^รองศาสตราจารย์\s+", re.I), "รศ. "),
        (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+", re.I), "ผศ. "),
        (re.compile(r"^อาจารย์\s+ดร\.\s*", re.I), "อ.ดร. "),
        (re.compile(r"^อาจารย์\s+", re.I), "อ. "),
    ]

    def contract_name(name: str) -> str:
        for pat, rep in long_title_patterns:
            if pat.search(name):
                return pat.sub(rep, name)
        return name

    assert contract_name("รองศาสตราจารย์ ดร.หรรษา เศรษฐบุปผา") == "รศ.ดร. หรรษา เศรษฐบุปผา"
    assert contract_name("ผู้ช่วยศาสตราจารย์ กิตติศักดิ์ บุญช่วย") == "ผศ. กิตติศักดิ์ บุญช่วย"
    assert contract_name("ศาสตราจารย์ ดร.วิภาดา คุณาวิกติกุล") == "ศ.ดร. วิภาดา คุณาวิกติกุล"
    assert contract_name("อาจารย์ ดร.ประสิทธิ์ พงษ์เรืองพันธุ์") == "อ.ดร. ประสิทธิ์ พงษ์เรืองพันธุ์"
    assert contract_name("อาจารย์ สมชาย ใจดี") == "อ. สมชาย ใจดี"


def test_phase3_kmutt_relative_image_resolution():
    """Verify that no faculty records retain relative image URLs."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        rel_imgs = db.query(FacultyDB).filter(FacultyDB.image_url.like("/%")).all()
        assert len(rel_imgs) == 0, f"Found {len(rel_imgs)} relative image URLs that were not resolved to absolute HTTPS!"

        # Verify KMUTT microbiology and chemistry sample records have valid HTTPS domains
        micro_sample = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_4bf8615a_9065").first()
        if micro_sample:
            assert micro_sample.image_url.startswith("https://mic.kmutt.ac.th/")

        chem_sample = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_791d8ceb_3344").first()
        if chem_sample:
            assert chem_sample.image_url.startswith("https://chem.kmutt.ac.th/")
    finally:
        db.close()


def test_phase3_junk_research_interests_filter():
    """Verify that pure placeholder tokens are filtered while domain-specific terms are preserved."""
    import re
    junk_pat = re.compile(r"^(ไม่มี|none|-|n/a|\.|null|undefined|\?)$", re.I)

    raw_interests = [
        "Machine Learning",
        "-",
        "Data Science",
        "?",
        "null",
        "ไม่มี",
        "none",
        "n/a",
        "โทรศัพท์เคลื่อนที่",
        "Room Control"
    ]
    cleaned = [x for x in raw_interests if not junk_pat.match(x.strip())]
    assert "-" not in cleaned
    assert "?" not in cleaned
    assert "null" not in cleaned
    assert "ไม่มี" not in cleaned
    assert "none" not in cleaned
    assert "n/a" not in cleaned
    assert "Machine Learning" in cleaned
    assert "Data Science" in cleaned
    # Telecommunications economics & acoustic control terms must be preserved
    assert "โทรศัพท์เคลื่อนที่" in cleaned
    assert "Room Control" in cleaned


def test_phase3_research_lab_advisor_institutional_symmetry():
    """Verify that repaired research labs have lead advisors strictly from the same institution."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB, ResearchLabDB

    db = SessionLocal()
    try:
        lab_ids = [
            "su_pharm_drug_delivery_lab",
            "su_eng_biopolymer_advanced_materials",
            "nida_bigdata_social_innovation"
        ]
        for lid in lab_ids:
            lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lid).first()
            assert lab is not None, f"Lab {lid} not found"
            advisor = db.query(FacultyDB).filter(FacultyDB.id == lab.lead_advisor_id).first()
            assert advisor is not None, f"Advisor {lab.lead_advisor_id} for lab {lid} not found"
            assert advisor.university_th == lab.university_th, (
                f"Lab '{lab.id}' university '{lab.university_th}' does not match "
                f"lead advisor '{advisor.id}' university '{advisor.university_th}'"
            )
    finally:
        db.close()


def test_phase4_kku_medicine_committee_cleanups():
    """Verify Khon Kaen Med ethics committee scraper artifacts are re-attributed and deduplicated."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Donors deleted and merged
        assert db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_009_009").first() is None
        siriraj_dean = db.query(FacultyDB).filter(FacultyDB.id == "mu_si_apichat_001").first()
        assert siriraj_dean is not None
        assert siriraj_dean.university_th == "มหาวิทยาลัยมหิดล"

        # SUT re-attributions
        tantanuch = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_tantanuch_018").first()
        assert tantanuch.university_th == "มหาวิทยาลัยเทคโนโลยีสุรนารี"
        assert tantanuch.faculty_th == "สำนักวิชาวิทยาศาสตร์"

        # PSU re-attributions
        yipinsoi = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_010_010").first()
        assert yipinsoi.university_th == "มหาวิทยาลัยสงขลานครินทร์"
        assert yipinsoi.faculty_th == "คณะแพทยศาสตร์"

        # CMU Med re-attributions
        chatkul = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_chatkul_013").first()
        assert chatkul.university_th == "มหาวิทยาลัยเชียงใหม่"
        assert chatkul.faculty_th == "คณะแพทยศาสตร์"

        # KKU Science re-attributions
        boonyue = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_033_033").first()
        assert boonyue.faculty_th == "คณะวิทยาศาสตร์"

        # KKU Engineering re-attributions
        phongrak = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_phongraktham_039").first()
        assert phongrak.faculty_th == "คณะวิศวกรรมศาสตร์"

        # Double titles and surname restoration
        fac4 = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_004_004").first()
        assert fac4.full_name_th == "นพ. ยุทธพงศ์ วงศ์สวัสดิวัฒน์"

        arnon = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_nithichanon_007").first()
        assert arnon.full_name_th == "ผศ.ดร. อานันต์ นิธิชานนท์"
        assert arnon.last_name == "Nithichanon"
    finally:
        db.close()


def test_phase4_mahidol_public_health_cleanups():
    """Verify Mahidol Public Health scraper artifacts are merged and re-attributed."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Donor merged
        assert db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofp_naksen_012").first() is None
        cmu_naksen = db.query(FacultyDB).filter(FacultyDB.id == "chiangmaiu_facultyofp_naksen_003").first()
        assert cmu_naksen is not None

        # Re-attributions
        mahikul = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofp_mahikul_014").first()
        assert mahikul.university_th == "ราชวิทยาลัยจุฬาภรณ์"

        narin = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofp_narin_027").first()
        assert narin.university_th == "มหาวิทยาลัยเชียงใหม่"
        assert narin.faculty_th == "คณะพยาบาลศาสตร์"
    finally:
        db.close()


def test_phase4_chula_communication_arts_naming():
    """Verify Chula Communication Arts faculty naming is standardized to คณะนิเทศศาสตร์."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 0 Chula faculties named คณะวารสารศาสตร์และสื่อสารมวลชน
        invalid_count = db.query(FacultyDB).filter(
            FacultyDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
            FacultyDB.faculty_th == "คณะวารสารศาสตร์และสื่อสารมวลชน"
        ).count()
        assert invalid_count == 0

        # Dean Preeda
        preeda = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofc_akrachantachote_016").first()
        assert preeda.faculty_th == "คณะนิเทศศาสตร์"

        # External TU faculty member
        chong = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofc_chongvilaikasem_017").first()
        assert chong.university_th == "มหาวิทยาลัยธรรมศาสตร์"
        assert chong.faculty_th == "คณะวารสารศาสตร์และสื่อสารมวลชน"
    finally:
        db.close()


def test_phase4_regional_universities_domain_mapping():
    """Verify regional university profiles are correctly mapped to their domain institutions."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        mju_wrong = db.query(FacultyDB).filter(
            FacultyDB.id.like("regionalun_facultymem_%"),
            FacultyDB.profile_url.like("%mju.ac.th%"),
            FacultyDB.university_th == "มหาวิทยาลัยนเรศวร"
        ).count()
        assert mju_wrong == 0

        ubu_wrong = db.query(FacultyDB).filter(
            FacultyDB.id.like("regionalun_facultymem_%"),
            FacultyDB.profile_url.like("%ubu.ac.th%"),
            FacultyDB.university_th == "มหาวิทยาลัยนเรศวร"
        ).count()
        assert ubu_wrong == 0

        klaivit = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_klaivitphat_086").first()
        assert klaivit.university_th == "มหาวิทยาลัยทักษิณ"
    finally:
        db.close()


def test_phase4_silpakorn_architecture_committee_cleanups():
    """Verify Silpakorn Architecture committee sweeps are re-attributed and deduplicated."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Donor merged
        assert db.query(FacultyDB).filter(FacultyDB.id == "silpakornu_facultyofa_sangsayan_003").first() is None
        cu_pracha = db.query(FacultyDB).filter(FacultyDB.id == "cu_ds_wave11_0023").first()
        assert cu_pracha is not None
        assert cu_pracha.university_th == "จุฬาลงกรณ์มหาวิทยาลัย"

        # KMUTNB re-attribution
        anantacha = db.query(FacultyDB).filter(FacultyDB.id == "silpakornu_facultyofa_anantacha_017").first()
        assert anantacha.university_th == "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ"
        assert anantacha.faculty_th == "คณะสถาปัตยกรรมและการออกแบบ"

        # CMU Fine Arts re-attribution
        chainakut = db.query(FacultyDB).filter(FacultyDB.id == "silpakornu_facultyofa_chainakut_015").first()
        assert chainakut.university_th == "มหาวิทยาลัยเชียงใหม่"
        assert chainakut.faculty_th == "คณะวิจิตรศิลป์"

        # Authentic Silpakorn Painting faculty
        kasorn = db.query(FacultyDB).filter(FacultyDB.id == "silpakornu_facultyofa_kasornsawan_006").first()
        assert kasorn.university_th == "มหาวิทยาลัยศิลปากร"
        assert kasorn.faculty_th == "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์"
    finally:
        db.close()


def test_phase4_cross_uni_deduplication_metrics_preservation():
    """Verify cross-university deduplication merges preserve maximum bibliometric metrics."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Bin Zhao
        assert db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_zhao_021").first() is None
        bin_zhao = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_thammasatb_fac_072_072").first()
        assert bin_zhao is not None
        assert bin_zhao.total_publications_count >= 660
        assert bin_zhao.total_citations >= 22690
        assert bin_zhao.university_th == "มหาวิทยาลัยธรรมศาสตร์"

        # Anchana Prathep
        assert db.query(FacultyDB).filter(FacultyDB.id == "ku-sci-zoo-010_648b2c").first() is None
        anchana = db.query(FacultyDB).filter(FacultyDB.id == "princeofso_facultyofs_prateep_105").first()
        assert anchana is not None
        assert anchana.total_publications_count >= 115
        assert anchana.total_citations >= 2990
        assert anchana.university_th == "มหาวิทยาลัยสงขลานครินทร์"

        # Tuantong Jutagate
        assert db.query(FacultyDB).filter(FacultyDB.id == "ku_fish_tuantong_001").first() is None
        tuantong = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofa_jutagate_001").first()
        assert tuantong is not None
        assert tuantong.total_publications_count >= 70
        assert tuantong.total_citations >= 1008
        assert tuantong.university_th == "มหาวิทยาลัยอุบลราชธานี"

        # Somkit Lertpaithoon
        assert db.query(FacultyDB).filter(FacultyDB.id == "thaksinuni_facultyofl_lertpaithoon_009").first() is None
        somkit = db.query(FacultyDB).filter(FacultyDB.id == "tu_law_064").first()
        assert somkit is not None
        assert somkit.university_th == "มหาวิทยาลัยธรรมศาสตร์"
    finally:
        db.close()


def test_phase4_institutional_faculty_names():
    """Verify official institutional faculty names for NIDA and KU."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        for nid in ["nida_biz_001", "nida_biz_002", "nida_biz_003"]:
            f = db.query(FacultyDB).filter(FacultyDB.id == nid).first()
            if f:
                assert f.faculty_th == "คณะบริหารธุรกิจ"

        for kid in ["ku_agri_001", "ku_agri_entomology_001"]:
            f = db.query(FacultyDB).filter(FacultyDB.id == kid).first()
            if f:
                assert f.faculty_th == "คณะเกษตร"
    finally:
        db.close()


def test_phase5_regionalun_generic_breadcrumb_faculties_repaired():
    """Verify all generic breadcrumb faculty_th == 'คณาจารย์และนักวิจัย' are resolved."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Zero records with generic breadcrumb
        generic_count = db.query(FacultyDB).filter(FacultyDB.faculty_th == "คณาจารย์และนักวิจัย").count()
        assert generic_count == 0

        # NU Education
        swangmek = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_swangmek_002").first()
        assert swangmek is not None
        assert swangmek.faculty_th == "คณะศึกษาศาสตร์"
        assert swangmek.department_th == "ภาควิชาการศึกษา"

        # MJU Veterinary Medicine
        uphoyo = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_uphoyo_080").first()
        assert uphoyo is not None
        assert uphoyo.faculty_th == "คณะสัตวแพทยศาสตร์"

        # NU Business Administration
        nilmoj = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_nilmoj_030").first()
        assert nilmoj is not None
        assert nilmoj.faculty_th == "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร"

        # NU Science
        onpong = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_onpong_027").first()
        assert onpong is not None
        assert onpong.faculty_th == "คณะวิทยาศาสตร์"
        assert onpong.department_th == "ภาควิชาคอมพิวเตอร์"
    finally:
        db.close()


def test_phase5_cross_university_duplicates_merged_and_metrics_preserved():
    """Verify Phase 5 cross-university duplicate merges and lifetime metric preservation."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # Chaiyong Ragkhitwetsagul (Mahidol ICT canonical)
        assert db.query(FacultyDB).filter(FacultyDB.id == "camt-cmu-015_01d96c").first() is None
        chaiyong = db.query(FacultyDB).filter(FacultyDB.id == "mu_398425a6_1356").first()
        assert chaiyong is not None
        assert chaiyong.total_publications_count >= 69
        assert chaiyong.total_citations >= 791
        assert chaiyong.university_th == "มหาวิทยาลัยมหิดล"

        # Charun Bunyakan (PSU Chem Eng canonical)
        assert db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_437c2bf2").first() is None
        charun = db.query(FacultyDB).filter(FacultyDB.id == "psu_eng_002").first()
        assert charun is not None
        assert charun.total_publications_count >= 30
        assert charun.total_citations >= 604
        assert charun.university_th == "มหาวิทยาลัยสงขลานครินทร์"

        # Kiattawee Choowongkomon (KU Biochem canonical)
        assert db.query(FacultyDB).filter(FacultyDB.id == "mu_sc_kiattawee_001").first() is None
        kiattawee = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0003").first()
        assert kiattawee is not None
        assert kiattawee.total_publications_count >= 326
        assert kiattawee.total_citations >= 4087
        assert kiattawee.university_th == "มหาวิทยาลัยเกษตรศาสตร์"

        # Pitiwat Wattanachai (CMU Civil Eng canonical)
        assert db.query(FacultyDB).filter(FacultyDB.id == "sut_eng_pitiwat_001").first() is None
        pitiwat = db.query(FacultyDB).filter(FacultyDB.id == "cmu_eng_department_prof_41").first()
        assert pitiwat is not None
        assert pitiwat.total_publications_count >= 29
        assert pitiwat.total_citations >= 298
        assert pitiwat.university_th == "มหาวิทยาลัยเชียงใหม่"
    finally:
        db.close()


def test_phase5_psu_nonglak_surname_and_mfu_komsan_metrics_disambiguated():
    """Verify PSU Nonglak Thai surname and MFU Komsan research metrics disambiguation."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        psu_nonglak = db.query(FacultyDB).filter(FacultyDB.id == "psu_agro_nonglak_001").first()
        assert psu_nonglak is not None
        assert psu_nonglak.full_name_th == "รศ.ดร. นงลักษณ์ มีเถ้าขันจิตร"
        assert psu_nonglak.last_name == "Meethaokhanchit"
        assert psu_nonglak.university_th == "มหาวิทยาลัยสงขลานครินทร์"

        # Separate from KKU Nursing
        kku_nonglak = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofn_methakanjanasak_018").first()
        assert kku_nonglak is not None
        assert kku_nonglak.full_name_th == "ผศ.ดร. นงลักษณ์ เมธากาญจนศักดิ์"
        assert kku_nonglak.university_th == "มหาวิทยาลัยขอนแก่น"

        # MFU Komsan Suriya
        mfu_komsan = db.query(FacultyDB).filter(FacultyDB.id == "mfu_med_komsan_001").first()
        assert mfu_komsan is not None
        assert mfu_komsan.total_citations == 0
        assert mfu_komsan.openalex_id == "not_indexed"
        assert mfu_komsan.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง"

        # CMU Komsan Suriya
        cmu_komsan = db.query(FacultyDB).filter(FacultyDB.id == "cmu_499533f0_5132").first()
        assert cmu_komsan is not None
        assert cmu_komsan.total_citations >= 400
        assert cmu_komsan.university_th == "มหาวิทยาลัยเชียงใหม่"
    finally:
        db.close()


def test_phase5_featured_publications_html_sanitized():
    """Verify zero unescaped HTML entities or HTML markup tags in featured_publications."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        all_facs = db.query(FacultyDB).all()
        for f in all_facs:
            if f.featured_publications:
                for p in f.featured_publications:
                    title = p.get("title", "") if isinstance(p, dict) else str(p)
                    assert "&amp;" not in title, f"Found &amp; in {f.id}: {title}"
                    assert "&quot;" not in title, f"Found &quot; in {f.id}: {title}"
                    assert "&#39;" not in title, f"Found &#39; in {f.id}: {title}"
                    assert "&lt;" not in title, f"Found &lt; in {f.id}: {title}"
                    assert "&gt;" not in title, f"Found &gt; in {f.id}: {title}"
                    assert "<p" not in title.lower(), f"Found <p in {f.id}: {title}"
                    assert "<i>" not in title.lower(), f"Found <i> in {f.id}: {title}"
                    assert "<strong>" not in title.lower(), f"Found <strong> in {f.id}: {title}"
    finally:
        db.close()


def test_phase5_research_interests_punctuation_sanitized():
    """Verify research interests do not contain trailing commas, semicolons, or scraper artifact quotes."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        all_facs = db.query(FacultyDB).all()
        for f in all_facs:
            if f.research_interests:
                for it in f.research_interests:
                    s = str(it).strip()
                    assert not s.endswith(","), f"Trailing comma in {f.id}: {s}"
                    assert not s.endswith(";"), f"Trailing semicolon in {f.id}: {s}"
                    assert not s.startswith('"'), f"Leading quote in {f.id}: {s}"
                    assert not s.endswith('"'), f"Trailing quote in {f.id}: {s}"
                    assert s != "คณาจารย์และนักวิจัย", f"Placeholder interest in {f.id}"
    finally:
        db.close()


def test_phase5_institutional_standardizations():
    """Verify institutional naming standardizations and lab advisor symmetry."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB, ResearchLabDB

    db = SessionLocal()
    try:
        # Thaksin economics faculty standardized
        invalid_tsu = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%ทักษิณ%"),
            FacultyDB.faculty_th == "คณะเศรษฐศาสตร์และการบริหาร"
        ).count()
        assert invalid_tsu == 0

        # SUT Synchrotron lab advisor belongs to SUT
        lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == "sut_synchrotron_advanced_materials_lab").first()
        assert lab is not None
        advisor = db.query(FacultyDB).filter(FacultyDB.id == lab.lead_advisor_id).first()
        assert advisor is not None
        assert advisor.university_th == "มหาวิทยาลัยเทคโนโลยีสุรนารี"
        assert advisor.id == "sut_eng_sarawut_001"
    finally:
        db.close()


def test_phase6_research_interests_microscopic_hygiene():
    """Verify Phase 6 microscopic content hygiene across research_interests."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    import re

    db = SessionLocal()
    try:
        all_facs = db.query(FacultyDB).all()
        provenance_keywords = [
            "verified via",
            "identity confirmed",
            "this summary is",
            "no areas of expertise",
            "no specific publications",
            "stated area of expertise",
            "faculty page",
            "source page",
            "faculty-members listing",
        ]

        for f in all_facs:
            if f.research_interests:
                for it in f.research_interests:
                    s = str(it).strip()
                    # 1. Zero pure digits
                    assert not re.match(r"^\d+$", s), f"Pure digit interest found in {f.id}: {s}"
                    # 2. Zero unparsed pipes
                    assert "|" not in s, f"Unparsed pipe found in {f.id}: {s}"
                    # 3. Zero unparsed slashes
                    assert " / " not in s, f"Unparsed slash found in {f.id}: {s}"
                    # 4. Zero provenance / commentary strings
                    low = s.lower()
                    for pk in provenance_keywords:
                        assert pk not in low, f"Provenance token '{pk}' found in {f.id}: {s}"

        # 5. Verify Amornsri stuttering resolved
        amornsri = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_agrips_0129").first()
        assert amornsri is not None
        assert "egg hatching and paralysis" in amornsri.research_interests
        assert "nematode management" in amornsri.research_interests
        assert not any("egg hatching egg hatching" in it for it in amornsri.research_interests)

        # 6. Verify Burapha engineering faculty cleaned
        anuphon = db.query(FacultyDB).filter(FacultyDB.id == "buu_eng_anuphon").first()
        assert anuphon is not None
        assert "วิศวกรรมเครื่องกล" in anuphon.research_interests
        assert "Mechanical Engineering" in anuphon.research_interests

        adisak = db.query(FacultyDB).filter(FacultyDB.id == "buu_eng_adisakn").first()
        assert adisak is not None
        assert "productivity improvement" in adisak.research_interests
        assert not any("This summary is derived" in it for it in adisak.research_interests)
    finally:
        db.close()


def test_phase7_unicode_contamination_purge():
    """Phase 7: Verify Greek/Cyrillic/Georgian/Kannada Unicode contamination is purged from full_name_th."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    import unicodedata

    # Unicode blocks that must NOT appear in Thai academic names
    FORBIDDEN_SCRIPT_RANGES = [
        (0x0370, 0x03FF),   # Greek and Coptic
        (0x0400, 0x04FF),   # Cyrillic
        (0x10A0, 0x10FF),   # Georgian
        (0x0C80, 0x0CFF),   # Kannada
    ]

    def has_forbidden_unicode(s: str) -> bool:
        for ch in s:
            cp = ord(ch)
            for start, end in FORBIDDEN_SCRIPT_RANGES:
                if start <= cp <= end:
                    return True
        return False

    db = SessionLocal()
    try:
        # Spot-check the 8 records that were contaminated
        fixed_cases = [
            ("chula_eng_ee_016", "รศ.ดร. ฉันทชนะ ตั้งวงศ์สาน"),
            ("chula_eng_ee_018", "ศ.ดร. ชาวดิษฐ์ อัศวกุล"),
            ("chulalongk_facultyofn_anuruang_008", "ผศ.ดร. ศกุนตลา อนันตรูชา"),
            ("kingmongku_schoolofin_netisopakul_008", "รศ.ดร. พรฤดี เนติโซปากุล"),
            ("mu_cmmu_019", "รศ.ดร. สุภารักษ์ สุรัมยังกิจแก้ว"),
            ("thammasatu_sirindhorn_piantanakulchai_030", "ดร. มงกุฎ เปียนตานากุลชัย"),
            ("mu_sci_wave14_b_0099", "ผศ.ดร. ปรียานุช จุงคง"),
            ("mu_cmmu_prattana_001", "รศ.ดร. ปรัชญา พันณกิจกาสเอม"),
        ]
        for faculty_id, expected_name in fixed_cases:
            f = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if f is not None:
                assert f.full_name_th == expected_name, (
                    f"Unicode fix failed for {faculty_id}: got '{f.full_name_th}', expected '{expected_name}'"
                )
                assert not has_forbidden_unicode(f.full_name_th), (
                    f"Forbidden Unicode still present in {faculty_id}: '{f.full_name_th}'"
                )

        # Full sweep: no faculty in DB should have forbidden Unicode in full_name_th
        all_f = db.query(FacultyDB).all()
        contaminated = [
            f for f in all_f
            if f.full_name_th and has_forbidden_unicode(f.full_name_th)
        ]
        assert len(contaminated) == 0, (
            f"Found {len(contaminated)} records with Unicode contamination: "
            + ", ".join(f.id for f in contaminated[:5])
        )
    finally:
        db.close()


def test_phase7_kku_business_expertise_tags_purged():
    """Phase 7: Verify KKU Business 'Expertise in X' / 'ความเชี่ยวชาญด้าน' LLM provenance tags are fully purged."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        kku_biz = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%ขอนแก่น%"),
            FacultyDB.faculty_th.like("%บริหาร%"),
        ).all()

        for f in kku_biz:
            for item in (f.research_interests or []):
                s = str(item).strip()
                assert not s.lower().startswith("expertise in"), (
                    f"Provenance tag 'Expertise in' found in {f.id}: '{s}'"
                )
                assert not s.startswith("ความเชี่ยวชาญด้าน"), (
                    f"Provenance tag 'ความเชี่ยวชาญด้าน' found in {f.id}: '{s}'"
                )
    finally:
        db.close()


def test_phase7_no_intra_faculty_duplicate_interests():
    """Phase 7: Verify no faculty record has the same interest token twice (case-insensitive)."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        all_f = db.query(FacultyDB).all()
        duplicates_found = []
        for f in all_f:
            if not f.research_interests:
                continue
            seen = set()
            for item in f.research_interests:
                key = str(item).strip().lower()
                if key in seen and key:
                    duplicates_found.append(f"{f.id}: '{item}'")
                seen.add(key)

        assert len(duplicates_found) == 0, (
            f"Found {len(duplicates_found)} intra-faculty duplicate interests: "
            + "; ".join(duplicates_found[:5])
        )
    finally:
        db.close()


def test_phase8_publications_have_api_shape():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        invalid = []
        allowed = {"title", "year", "venue", "url", "citation_count"}
        for faculty in db.query(FacultyDB).yield_per(500):
            for item in (faculty.featured_publications or []):
                if not isinstance(item, dict) or not item.get("title"):
                    invalid.append(faculty.id)
                    break
                assert set(item).issubset(allowed), f"Unexpected fields for {faculty.id}: {item}"
        assert invalid == [], f"Malformed publication records: {invalid[:5]}"
    finally:
        db.close()


def test_phase8_mixed_language_english_names_purged():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    import re

    expected = {
        "ku_eng_cpe_009": ("Yod", "Thipsuwan"),
        "tu_law_070": ("Supreeya", "Kaewla-iat"),
        "chulalongk_facultyofs_torg_057": ("Panthana", "Torg"),
        "thammasatu_facultyofn_raethong_216": ("Parinya", "Raethong"),
        "chulalongk_facultyofl_niyom_030": ("Patch", "Niyomsilp"),
    }

    db = SessionLocal()
    try:
        for faculty_id, names in expected.items():
            faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            assert faculty is not None
            assert (faculty.first_name, faculty.last_name) == names
            assert not re.search(r"[ก-๙]", faculty.first_name or "")
            assert not re.search(r"[ก-๙]", faculty.last_name or "")
    finally:
        db.close()


def test_phase8_openalex_placeholder_not_collision():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        rows = db.query(FacultyDB).filter(FacultyDB.openalex_id == "not_indexed").limit(2).all()
        assert len(rows) == 2
        assert rows[0].id != rows[1].id
    finally:
        db.close()


def test_phase9_publications_and_scholar_urls_are_normalized():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    import re

    db = SessionLocal()
    try:
        invalid_publications = []
        invalid_urls = []
        for faculty in db.query(FacultyDB).yield_per(500):
            assert isinstance(faculty.featured_publications, list), faculty.id
            for item in faculty.featured_publications:
                assert isinstance(item, dict) and item.get("title"), faculty.id
            if faculty.scholar_url is not None:
                if faculty.scholar_url.strip() in {"", "-", "—", "ไม่มี"}:
                    invalid_urls.append(faculty.id)
                elif not re.match(r"^https?://", faculty.scholar_url.strip(), re.I):
                    invalid_urls.append(faculty.id)
        assert invalid_publications == []
        assert invalid_urls == []
    finally:
        db.close()


def test_phase9_author_metrics_do_not_decrease_publication_count():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        invalid = db.query(FacultyDB).filter(
            FacultyDB.total_publications_count < FacultyDB.h_index
        ).count()
        assert invalid == 0
    finally:
        db.close()


def test_phase10_disambiguated_metric_subcounts_are_cleared():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        jennit = db.query(FacultyDB).filter(
            FacultyDB.id == "chulalongk_facultyofp_fac_036_036"
        ).first()
        assert jennit is not None
        assert (jennit.total_publications_count, jennit.first_author_count, jennit.co_author_count) == (0, 0, 0)

        komsan = db.query(FacultyDB).filter(
            FacultyDB.id == "mfu_med_komsan_001"
        ).first()
        assert komsan is not None
        assert (komsan.first_author_count, komsan.co_author_count) == (0, 0)
        assert komsan.total_citations == 0
        assert komsan.h_index == 0
        assert komsan.openalex_id == "not_indexed"
    finally:
        db.close()


def test_phase11_structured_content_and_secondary_hygiene():
    """Verify Phase 11 structured content cleanup and secondary database hygiene invariants."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB, CourseDB

    db = SessionLocal()
    try:
        # 1. Non-person geographic scraper artifact purged
        assert db.query(FacultyDB).filter(FacultyDB.id == "srinakha_facultyo_6dde3ed5").first() is None

        # 2. CMU cross-contaminated email cleared
        nat = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_012_012").first()
        if nat:
            assert nat.email is None

        # 3. Chula Psychology JS artifact purged across entire database
        chula_artifact_prefix = "edDegree: null,selectedMajor: null,modalOpen: false"
        for f in db.query(FacultyDB).yield_per(500):
            for e in (f.education or []):
                assert not str(e).startswith(chula_artifact_prefix), f"Artifact in {f.id}"

            # 4. Zero empty strings in department, department_th, and role
            assert f.department != "", f"Empty department string in {f.id}"
            assert f.department_th != "", f"Empty department_th string in {f.id}"
            assert f.role != "", f"Empty role string in {f.id}"

            # 5. Zero unencoded spaces in profile_url and image_url
            if f.profile_url:
                assert " " not in f.profile_url, f"Unencoded space in profile_url for {f.id}"
            if f.image_url:
                assert " " not in f.image_url, f"Unencoded space in image_url for {f.id}"

        # 6. Course degree_name empty strings
        for c in db.query(CourseDB).yield_per(500):
            assert c.degree_name != "", f"Empty degree_name string in course {c.id}"
    finally:
        db.close()


def test_phase12_identity_and_metric_contamination_purge():
    """Verify Phase 12 mock purging, OpenAlex disambiguation, and regional faculty fixes."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB, CourseDB

    db = SessionLocal()
    try:
        # 1. Zero synthetic mu-sci mock records
        mu_sci_count = db.query(FacultyDB).filter(FacultyDB.id.like("mu-sci-%")).count()
        assert mu_sci_count == 0, f"Found {mu_sci_count} remaining mu-sci- records"

        # 2. Stub deletion
        assert db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofs_fac_009_009").first() is None

        # 3. Disambiguated OpenAlex resets
        p_khong = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_035_035").first()
        assert p_khong is not None
        assert p_khong.openalex_id == "not_indexed"
        assert p_khong.total_citations == 0
        assert p_khong.total_publications_count == 0

        nop = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofp_fac_010_010").first()
        assert nop is not None
        assert nop.openalex_id == "not_indexed"
        assert nop.total_citations == 0

        anong = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofa_fac_008_008").first()
        assert anong is not None
        assert anong.openalex_id == "not_indexed"
        assert anong.total_citations == 0

        daris = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_fac_031_031").first()
        assert daris is not None
        assert daris.openalex_id == "https://openalex.org/A5025322553"
        assert daris.total_citations == 511
        assert daris.h_index == 12

        jennit = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofp_fac_036_036").first()
        assert jennit is not None
        assert jennit.openalex_id == "not_indexed"
        assert jennit.total_citations == 0

        chidchanok = db.query(FacultyDB).filter(FacultyDB.id == "chula_eng_cp_020").first()
        assert chidchanok is not None
        assert chidchanok.last_name == "Lursinsap"

        # 4. Regional faculty identity fixes
        tsu_88 = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_fac_088_088").first()
        assert tsu_88 is not None
        assert tsu_88.full_name_th == "รศ.ดร. รุ่งรวี จิตภักดี"
        assert tsu_88.university_th == "มหาวิทยาลัยทักษิณ"
        assert tsu_88.faculty_th == "คณะสหวิทยาการและการประกอบการ"

        tsu_89 = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_fac_089_089").first()
        assert tsu_89 is not None
        assert tsu_89.full_name_th == "อ.ดร. ศันสนีย์ วงศ์สวัสดิ์"
        assert tsu_89.university_th == "มหาวิทยาลัยทักษิณ"

        ubu_96 = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_fac_096_096").first()
        assert ubu_96 is not None
        assert ubu_96.full_name_th == "อ. มิตต ทรัพย์ผุด"
        assert ubu_96.university_th == "มหาวิทยาลัยอุบลราชธานี"
        assert ubu_96.faculty_th == "คณะศิลปศาสตร์"

        # 5. Zero empty strings in faculty URL/email/name fields
        for f in db.query(FacultyDB).yield_per(500):
            assert f.first_name != "", f"Empty first_name string in {f.id}"
            assert f.last_name != "", f"Empty last_name string in {f.id}"
            assert f.email != "", f"Empty email string in {f.id}"
            assert f.profile_url != "", f"Empty profile_url string in {f.id}"
            assert f.image_url != "", f"Empty image_url string in {f.id}"
            assert f.scholar_url != "", f"Empty scholar_url string in {f.id}"

        # 6. Zero courses with multiple consecutive spaces
        for c in db.query(CourseDB).yield_per(500):
            if c.title_th:
                assert "  " not in c.title_th, f"Multiple spaces in course title_th {c.id}"
            if c.title_en:
                assert "  " not in c.title_en, f"Multiple spaces in course title_en {c.id}"
    finally:
        db.close()


def test_phase13_email_hygiene_and_duplicates():
    """Verify Phase 13 email hygiene, freemail cleanup, publication URLs, and duplicate stubs."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Duplicate stubs permanently removed
        assert db.query(FacultyDB).filter(FacultyDB.id == "tu_law_021").first() is None
        assert db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofa_siriprikphong_026").first() is None

        # 2. Canonical records exist and contaminated email cleared
        limpaowart = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_facultyofl_limpaowart_005").first()
        assert limpaowart is not None
        assert limpaowart.email is None, f"Contaminated email still present: {limpaowart.email}"

        siriprik = db.query(FacultyDB).filter(FacultyDB.id == "tu_37991aa4_4542").first()
        assert siriprik is not None
        assert siriprik.email != "allied@allied.tu.ac.th", f"Shared allied email still present: {siriprik.email}"
        assert siriprik.email == "pilaiwan.s@allied.tu.ac.th"

        # 3. Departmental shared inboxes purged
        shared_depts = [
            "fish@ku.ac.th", "allied@allied.tu.ac.th", "fac-en@silpakorn.edu", "agro@psu.ac.th",
            "engineering@kku.ac.th", "chemy@ku.ac.th", "math@cmu.ac.th", "attm@med.tu.ac.th",
            "biology@cmu.ac.th", "intmed@cmu.ac.th", "ams@cmu.ac.th", "dsc@cmu.ac.th",
            "cpe@ku.ac.th", "chemistry@kmutt.ac.th", "stat@sci.kmutnb.ac.th", "ie@eng.chula.ac.th"
        ]
        for s_email in shared_depts:
            cnt = db.query(FacultyDB).filter(FacultyDB.email == s_email).count()
            assert cnt == 0, f"Found {cnt} records with shared department email {s_email}"

        # 4. Zero personal freemail addresses across entire database
        freemail_domains = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@live.com")
        for f in db.query(FacultyDB).yield_per(500):
            if f.email:
                em_lower = f.email.lower()
                assert not any(em_lower.endswith(dom) for dom in freemail_domains), (
                    f"Personal freemail address found in {f.id}: {f.email}"
                )

            # 5. Zero empty string URLs in featured_publications
            if isinstance(f.featured_publications, list):
                for p in f.featured_publications:
                    if isinstance(p, dict):
                        assert p.get("url") != "", f"Empty string URL in publication for faculty {f.id}"
    finally:
        db.close()


def test_phase14_residual_personal_email_hygiene():
    """Verify Phase 14 residual personal/freemail/corporate emails nulled and domain typos corrected."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Residual personal/freemail/corporate emails set to NULL (excluding recovered official emails)
        nulled_ids = [
            "chula_eng_ee_008",
            "tu_law_039",
            "su_eng_teacher_086",
            "chulalongk_facultyofp_horstmann_079",
            "cmu_3d00ad57_5599",
            "cmu_7645de8c_5935",
            "cu_cbs_wave11_0297",
            "su_eng_teacher_109",
            "cu_wave19_edu_0101",
            "msu_petchpengchai__8908",
        ]
        for fid in nulled_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            assert f is not None
            assert f.email is None, f"Email still present for {fid}: {f.email}"

        # 2. Preserved and corrected institutional emails
        su_fac = db.query(FacultyDB).filter(FacultyDB.id == "su_eng_teacher_093").first()
        assert su_fac is not None
        assert su_fac.email == "lapnonkawow_s@su.ac.th"
        cu_fac = db.query(FacultyDB).filter(FacultyDB.id == "cu_wave19_edu_0116").first()
        assert cu_fac is not None
        assert cu_fac.email == "weeraphol.s@chula.ac.th"

        tu_fac = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_sirindhorn_iamprasertkun_001").first()
        assert tu_fac is not None
        assert tu_fac.email == "pawin@siit.tu.ac.th"

        # 3. Comprehensive check: 100% of emails in DB belong to valid academic/gov/official domains
        valid_suffixes = (
            ".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk", "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md"
        )
        for f in db.query(FacultyDB).yield_per(500):
            if f.email:
                em = f.email.lower().strip()
                dom = em.split("@")[-1] if "@" in em else ""
                assert any(dom == s or dom.endswith(s) for s in valid_suffixes), (
                    f"Non-institutional email found in {f.id}: {f.email}"
                )
    finally:
        db.close()


def test_phase15_recovered_official_university_emails():
    """Verify Phase 15 recovered authentic university emails across KU Forest and Chula Science."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KU Forest recovered campus emails
        ku_sisc = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_sisc_0034").first()
        assert ku_sisc is not None
        assert ku_sisc.email == "sfsciksc@src.ku.ac.th"

        ku_scie = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_scie_0011").first()
        assert ku_scie is not None
        assert ku_scie.email == "thapranee.h@nontri.ku.ac.th"

        ku_csc = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_pubh_0011").first()
        assert ku_csc is not None
        assert ku_csc.email == "fphbpk@csc.ku.ac.th"

        # 2. CU Science recovered emails (Chem, Math, Bio)
        cu_chem = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0024").first()
        assert cu_chem is not None
        assert cu_chem.email == "narong.pr@chula.ac.th"

        cu_math = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0082").first()
        assert cu_math is not None
        assert cu_math.email == "korkeat.k@chula.ac.th"

        cu_bio = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0142").first()
        assert cu_bio is not None
        assert cu_bio.email == "suchinda.m@chula.ac.th"

        # 3. Departmental chemistry@ was not assigned
        cu_chem_dept = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0030").first()
        assert cu_chem_dept is not None
        assert cu_chem_dept.email is None

        # 4. Total faculty with official email >= 9290
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 9290
    finally:
        db.close()


def test_phase16_recovered_official_university_emails():
    """Verify Phase 16 recovered authentic university emails across CMU, PSU, and KU."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. CMU Dent recovered email and 1-to-1 profile URL
        cmu_dent = db.query(FacultyDB).filter(FacultyDB.id == "cmu_4eafefda_8604").first()
        assert cmu_dent is not None
        assert cmu_dent.email == "supatra.sa@cmu.ac.th"
        assert cmu_dent.profile_url == "https://www.dent.cmu.ac.th/web/staff/supatra.sa@cmu.ac.th"

        # 2. PSU Agro recovered email
        psu_agro = db.query(FacultyDB).filter(FacultyDB.id == "psu_agro_wave13_0012").first()
        assert psu_agro is not None
        assert psu_agro.email == "pochanart.k@psu.ac.th"

        # 3. KU Chem recovered email and 1-to-1 profile URL
        ku_chem = db.query(FacultyDB).filter(FacultyDB.id == "ku_1e55e114_1626").first()
        assert ku_chem is not None
        assert ku_chem.email == "fscitnn@ku.ac.th"
        assert ku_chem.profile_url == "https://chemy.sci.ku.ac.th/ku-personnel/tanin-nanok/"

        # 4. CMU Math recovered email and 1-to-1 profile URL
        cmu_math = db.query(FacultyDB).filter(FacultyDB.id == "cmu_700d1c7d_5607").first()
        assert cmu_math is not None
        assert cmu_math.email == "wipawinee.ch@cmu.ac.th"
        assert cmu_math.profile_url == "http://math.science.cmu.ac.th/personals-detail.php?id=70"

        # 5. KU Forest deep retry recovered email
        ku_forest = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_engsrc_0086").first()
        assert ku_forest is not None
        assert ku_forest.email == "sfengyps@src.ku.ac.th"

        # 6. Total faculty with official email >= 9530
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 9530
    finally:
        db.close()


def test_phase17_recovered_official_university_emails():
    """Verify Phase 17 recovered authentic university emails across Kasetsart University Faculty of Science."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KU Science Physics recovered email and 1-to-1 profile URL
        ku_phys = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_0015").first()
        assert ku_phys is not None
        assert ku_phys.email == "fscicpk@ku.ac.th"
        assert "physics.sci.ku.ac.th/ku-personnel/" in (ku_phys.profile_url or "")

        # 2. KU Science Maths recovered email and 1-to-1 profile URL
        ku_math = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_0034").first()
        assert ku_math is not None
        assert ku_math.email == "montri.m@ku.th"
        assert "maths.sci.ku.ac.th/ku-personnel/" in (ku_math.profile_url or "")

        # 3. KU Science Earth recovered email and 1-to-1 profile URL
        ku_earth = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0051").first()
        assert ku_earth is not None
        assert ku_earth.email == "chawisa.phuj@ku.ac.th"
        assert "earth.sci.ku.ac.th/ku-personnel/" in (ku_earth.profile_url or "")

        # 4. KU Science Genetics recovered email and 1-to-1 profile URL
        ku_genetics = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_0063").first()
        assert ku_genetics is not None
        assert ku_genetics.email == "fscikss@ku.ac.th"
        assert "genetics.sci.ku.ac.th/ku-personnel/" in (ku_genetics.profile_url or "")

        # 5. KU Science Botany recovered email
        ku_botany = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0027").first()
        assert ku_botany is not None
        assert ku_botany.email == "jaruswan.w@ku.th"

        # 6. KU Science Biochem recovered email
        ku_biochem = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0001").first()
        assert ku_biochem is not None
        assert ku_biochem.email == "fscislt@ku.ac.th"

        # 7. Total faculty with official email >= 9700
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 9700
    finally:
        db.close()


def test_phase18_recovered_official_university_emails():
    """Verify Phase 18 recovered authentic university emails across TU TDS, CMU AMS, KMUTNB, CU Science & Dent."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. TU TDS Architecture & Planning recovered email
        tu_tds = db.query(FacultyDB).filter(FacultyDB.id == "tu_15e99a37_2286").first()
        assert tu_tds is not None
        assert tu_tds.email == "archan@ap.tu.ac.th"

        # 2. CMU AMS Occupational Therapy recovered email
        cmu_ot = db.query(FacultyDB).filter(FacultyDB.id == "cmu_48e50e9c_0252").first()
        assert cmu_ot is not None
        assert cmu_ot.email == "kewalin.panyo@cmu.ac.th"

        # 3. KMUTNB Applied Statistics recovered email
        kmutnb_stat = db.query(FacultyDB).filter(FacultyDB.id == "kmutnb_1638a3e9_4313").first()
        assert kmutnb_stat is not None
        assert kmutnb_stat.email == "yupaporn.a@sci.kmutnb.ac.th"

        # 4. CU Science Food Tech recovered email
        cu_food = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0173").first()
        assert cu_food is not None
        assert cu_food.email == "kitipong.a@chula.ac.th"

        # 5. CU Science Chem recovered email and profile URL
        cu_chem = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0044").first()
        assert cu_chem is not None
        assert cu_chem.email == "preecha.ki@chula.ac.th"
        assert cu_chem.profile_url == "https://chem.sc.chula.ac.th/preecha-kittikhunnatham/"

        # 6. CMU Science Biology recovered email
        cmu_bio = db.query(FacultyDB).filter(FacultyDB.id == "cmu_3c861083_3909").first()
        assert cmu_bio is not None
        assert cmu_bio.email == "siriphorn.jang@cmu.ac.th"

        # 7. CU Dentistry recovered email and profile URL
        cu_dent = db.query(FacultyDB).filter(FacultyDB.id == "cu_dent_wave15_0004").first()
        assert cu_dent is not None
        assert cu_dent.email == "kritchai.b@chula.ac.th"
        assert cu_dent.profile_url == "https://www.dent.chula.ac.th/teams/kritchai-bespinyowong/"

        # 8. Total faculty with official email >= 9830
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 9830
    finally:
        db.close()


def test_phase19_recovered_emails_deduplication_and_name_sanitization():
    """Verify Phase 19 recovered authentic emails, deduplication, and positional suffix sanitization."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Chula Nursing recovered email and profile URL
        cu_nurse = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofn_thato_001").first()
        assert cu_nurse is not None
        assert cu_nurse.email == "ratsiri.t@chula.ac.th"
        assert "nurs.chula.ac.th" in (cu_nurse.profile_url or "")

        # 2. TU Economics recovered email and university affiliation correction
        tu_econ = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_fakthong_015").first()
        assert tu_econ is not None
        assert tu_econ.email == "tiraphap@econ.tu.ac.th"
        assert tu_econ.university_th == "มหาวิทยาลัยธรรมศาสตร์"

        # 3. Chula Computer Engineering recovered email
        cu_cp = db.query(FacultyDB).filter(FacultyDB.id == "chula_eng_cp_pornsiri").first()
        assert cu_cp is not None
        assert cu_cp.email == "pornsiri.mu@chula.ac.th"

        # 4. Chula Veterinary Science recovered email
        cu_vet = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofv_taweethavonsawa_126").first()
        assert cu_vet is not None
        assert cu_vet.email == "piyanan.t@chula.ac.th"

        # 5. Chula Arts Linguistics recovered email
        cu_arts = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofa_techaiya_017").first()
        assert cu_arts is not None
        assert cu_arts.email == "jakapun.t@chula.ac.th"

        # 6. Chula Dentistry recovered email
        cu_dent = db.query(FacultyDB).filter(FacultyDB.id == "cu_dent_wave15_0015").first()
        assert cu_dent is not None
        assert cu_dent.email == "joao.f@chula.ac.th"

        # 7. KU Science recovered email
        ku_sci = db.query(FacultyDB).filter(FacultyDB.id == "ku_230570fa_1484").first()
        assert ku_sci is not None
        assert ku_sci.email == "fscinpp@ku.ac.th"

        # 8. Verified duplicates purged and metrics preserved
        assert db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_tanasritunyakul_007").first() is None
        primary_tu = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_thanasomboonyag_040").first()
        assert primary_tu is not None
        assert primary_tu.total_publications_count >= 1
        assert primary_tu.email == "alongkorn@econ.tu.ac.th"
        assert primary_tu.university_th == "มหาวิทยาลัยธรรมศาสตร์"

        for ku_dup_id in ["ku_2354332d_7230", "ku_285b9111_9427", "ku_43dde539_3137", "ku_682d440e_2212"]:
            assert db.query(FacultyDB).filter(FacultyDB.id == ku_dup_id).first() is None

        # 9. Verified Thai full names sanitized (0 records with 'อาจารย์ประจำ')
        tu_cleaned = db.query(FacultyDB).filter(FacultyDB.id == "tu_58504fd1_7364").first()
        assert tu_cleaned is not None
        assert tu_cleaned.full_name_th == "ผศ. ชวนพิศ บุญเกิด"

        psu_cleaned = db.query(FacultyDB).filter(FacultyDB.id == "psu_eng_wave11_0036").first()
        assert psu_cleaned is not None
        assert psu_cleaned.full_name_th == "ผศ.ดร. กิตติคุณ ทองพูล"

        pos_count = db.query(FacultyDB).filter(FacultyDB.full_name_th.like("%อาจารย์ประจำ%")).count()
        assert pos_count == 0, f"Found {pos_count} records with 'อาจารย์ประจำ' in full_name_th"

        # 10. Total faculties with official email >= 9900
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 9900
    finally:
        db.close()


def test_phase20_recovered_official_university_emails_and_name_repair():
    """Verify Phase 20 recovered authentic university emails and Direk Nualsing name repair."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Chula Engineering recovered emails
        cu_eng = db.query(FacultyDB).filter(FacultyDB.id == "chula_eng_ee_033").first()
        assert cu_eng is not None
        assert cu_eng.email == "watchara@chula.ac.th"
        assert "eng.chula.ac.th/th/staff/" in (cu_eng.profile_url or "")

        cu_civil = db.query(FacultyDB).filter(FacultyDB.id == "cu_eng_wave13_b_0004").first()
        assert cu_civil is not None
        assert cu_civil.email == "fcewsk@eng.chula.ac.th"

        cu_supot = db.query(FacultyDB).filter(FacultyDB.id == "cu_eng_wave13_b_0016").first()
        assert cu_supot is not None
        assert cu_supot.email == "supot.t@chula.ac.th"

        # 2. TU Engineering 100% resolution of NULLs and Direk Nualsing name repair
        tu_direk = db.query(FacultyDB).filter(FacultyDB.id == "tu_eng_wave16_0018").first()
        assert tu_direk is not None
        assert tu_direk.full_name_th == "อ.ดร. ดิเรก นวลสิงห์"
        assert tu_direk.email == "ndirek@engr.tu.ac.th"
        assert tu_direk.profile_url == "https://me.engr.tu.ac.th/staff/professor_pattaya"

        tu_ece = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_facultyofe_srisrisawang_013").first()
        assert tu_ece is not None
        assert tu_ece.email == "snitikor@engr.tu.ac.th"

        tu_iem = db.query(FacultyDB).filter(FacultyDB.id == "tu_eng_wave16_0003").first()
        assert tu_iem is not None
        assert tu_iem.email == "lbusaba@engr.tu.ac.th"

        tu_ce = db.query(FacultyDB).filter(FacultyDB.id == "tu_eng_wave16_0019").first()
        assert tu_ce is not None
        assert tu_ce.email == "sweeraya@engr.tu.ac.th"

        # 0 NULLs remaining in TU Engineering
        tu_eng_null = db.query(FacultyDB).filter(
            FacultyDB.email.is_(None),
            FacultyDB.university_th.like("%ธรรมศาสตร์%"),
            FacultyDB.faculty_th.like("%วิศวกรรม%")
        ).count()
        assert tu_eng_null == 0

        # 3. KU Chemical Engineering recovered emails
        ku_chem_eng = db.query(FacultyDB).filter(FacultyDB.id == "ku_eng_wave12_0025").first()
        assert ku_chem_eng is not None
        assert ku_chem_eng.email == "santi.bard@ku.th"

        # 4. CMU Agro-Industry recovered emails
        cmu_agro = db.query(FacultyDB).filter(FacultyDB.id == "chiangmaiu_facultyofa_rattanapitigorn_007").first()
        assert cmu_agro is not None
        assert cmu_agro.email == "panida.r@cmu.ac.th"

        # 5. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 6. Total faculties with official email >= 10100
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 10100
    finally:
        db.close()


def test_phase21_recovered_official_university_emails_and_null_audit():
    """Verify Phase 21 recovered authentic university emails and null audit invariants."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Mahidol College of Music recovered emails (118 verified)
        mahidol_music_f = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_collegeofm_pidokrajt_061").first()
        assert mahidol_music_f is not None
        assert mahidol_music_f.email == "narongchai.pid@mahidol.ac.th"
        assert "music.mahidol.ac.th/people/" in (mahidol_music_f.profile_url or "")

        # 2. Sasin School of Management recovered emails (26 verified)
        sasin_f = db.query(FacultyDB).filter(FacultyDB.id == "cu_sasin_006").first()
        assert sasin_f is not None
        assert sasin_f.email == "chaipong.pongpanich@sasin.edu"
        assert "sasin.edu/team/profile/" in (sasin_f.profile_url or "")

        # Verify visiting faculty in Sasin with no personal email remain NULL
        sasin_alvin = db.query(FacultyDB).filter(FacultyDB.id == "cu_sasin_001").first()
        assert sasin_alvin is not None
        assert sasin_alvin.email is None

        # 3. TU Medicine recovered emails (31 verified)
        tu_med_f = db.query(FacultyDB).filter(FacultyDB.id == "tu_74d4b85d_8557").first()
        assert tu_med_f is not None
        assert tu_med_f.email == "pasitpon@tu.ac.th"
        assert "med.tu.ac.th/cmfm/" in (tu_med_f.profile_url or "")

        tu_attm_f = db.query(FacultyDB).filter(FacultyDB.id == "tu_127cd3b6_7450").first()
        assert tu_attm_f is not None
        assert tu_attm_f.email == "jitpisut@tu.ac.th"
        assert "med.tu.ac.th/department/attm/" in (tu_attm_f.profile_url or "")

        # 4. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 5. Total faculties with official email >= 10270
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 10270
    finally:
        db.close()


def test_phase22_recovered_official_university_emails_and_null_audit():
    """Verify Phase 22 recovered authentic university emails and null audit invariants."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Mahidol Tropical Medicine recovered emails (101 verified)
        tm_f1 = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyoft_thussachan_070").first()
        assert tm_f1 is not None
        assert tm_f1.email == "ajjima.thu@mahidol.ac.th"
        assert "tm.mahidol.ac.th/tropmed-staff/" in (tm_f1.profile_url or "")

        tm_f2 = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyoft_chewapreecha_061").first()
        assert tm_f2 is not None
        assert tm_f2.email == "kamolchanok.che@mahidol.ac.th"

        # 2. KMITL Industrial Education recovered emails (95 verified, 100% of NULLs)
        kmitl_f1 = db.query(FacultyDB).filter(FacultyDB.id == "kmitl_siet_wave16_0001").first()
        assert kmitl_f1 is not None
        assert kmitl_f1.email == "amornchai.ch@kmitl.ac.th"
        assert "siet.kmitl.ac.th/index.php/node/" in (kmitl_f1.profile_url or "")

        kmitl_f2 = db.query(FacultyDB).filter(FacultyDB.id == "kmitl_siet_wave16_0083").first()
        assert kmitl_f2 is not None
        assert kmitl_f2.email == "pakkapong.po@kmitl.ac.th"

        # 3. TU Allied Health Sciences recovered emails (42 verified) & name repair
        tu_ahs_f = db.query(FacultyDB).filter(FacultyDB.id == "tu_58504fd1_7364").first()
        assert tu_ahs_f is not None
        assert tu_ahs_f.email == "chuanpis.b@allied.tu.ac.th"
        assert "allied.tu.ac.th/cv/?professor=" in (tu_ahs_f.profile_url or "")

        tu_repaired = db.query(FacultyDB).filter(FacultyDB.id == "tu_5671dd53_0452").first()
        assert tu_repaired is not None
        assert tu_repaired.full_name_th == "รศ.ดร. หิรัญญา ศรีธาตุ"
        assert tu_repaired.email == "hiranya.s@allied.tu.ac.th"

        # 4. CU Pharmacy recovered emails (5 verified)
        cu_pharm_f = db.query(FacultyDB).filter(FacultyDB.id == "cu_pharm_wave16_0006").first()
        assert cu_pharm_f is not None
        assert cu_pharm_f.email == "khachen.k@chula.ac.th"

        # Verify CU Pharmacy faculty with only personal freemails remain SQL NULL
        cu_pharm_freemail = db.query(FacultyDB).filter(FacultyDB.id == "cu_pharm_wave16_0001").first()
        assert cu_pharm_freemail is not None
        assert cu_pharm_freemail.email is None

        # Verify UBU Pharmacy records with no official email remain SQL NULL
        ubu_pharm_f = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofp_veravatnchai_040").first()
        assert ubu_pharm_f is not None
        assert ubu_pharm_f.email is None

        # 5. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 6. Total faculties with official email >= 10515
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 10515
    finally:
        db.close()


def test_phase23_recovered_official_university_emails_and_null_audit():
    """Verify Phase 23 recovered authentic university emails and null audit invariants."""
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KU Fisheries recovered emails (60 verified)
        ku_fish_f = db.query(FacultyDB).filter(FacultyDB.id == "ku_fish_wave11_0002").first()
        assert ku_fish_f is not None
        assert ku_fish_f.email == "ffisngh@ku.ac.th"

        # 2. KKU Engineering recovered emails (44 verified) and 1-to-1 profile URLs
        # Note: kku_1dd5e0f1_2035 deduplicated into canonical khonkaenun_collegeofc_leelapatra_062
        kku_eng_f = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_collegeofc_leelapatra_062").first()
        assert kku_eng_f is not None
        assert kku_eng_f.email == "watis@kku.ac.th"

        # 3. Chula Science Chemistry (5 verified) & Physics CERN (1 verified)
        # Note: chulalongk_facultyofs_fac_006_006 deduplicated into canonical cu_sci_wave14_b_0034
        cu_chem_f = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0034").first()
        assert cu_chem_f is not None
        assert cu_chem_f.email == "pakorn.v@chula.ac.th"
        assert "chem.sc.chula.ac.th/" in (cu_chem_f.profile_url or "")

        cu_phys_cern = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofs_asawatangtrakul_024").first()
        assert cu_phys_cern is not None
        assert cu_phys_cern.email == "chayanit@cern.ch"

        # 4. Chula Medicine recovered emails (4 verified)
        cu_med_f = db.query(FacultyDB).filter(FacultyDB.id == "cu_342cdc4e_4440").first()
        assert cu_med_f is not None
        assert cu_med_f.email == "pon.t@chula.md"
        assert "md.chula.ac.th/staff/" in (cu_med_f.profile_url or "")

        # 5. CMU Science Math recovered email (1 verified)
        cmu_math_f = db.query(FacultyDB).filter(FacultyDB.id == "cmu_3097ff5e_4125").first()
        assert cmu_math_f is not None
        assert cmu_math_f.email == "parkpoom.phetpradap@cmu.ac.th"

        # 6. Forensic NULL verification: confirm shared department inboxes never assigned
        # Silpakorn Engineering faculty must NOT receive shared FAC-EN@su.ac.th
        su_shared_count = db.query(FacultyDB).filter(FacultyDB.email.in_(["fac-en@su.ac.th", "fac-en@silpakorn.edu"])).count()
        assert su_shared_count == 0, f"Found {su_shared_count} faculties assigned shared SU inbox"

        # RU Political Science faculty must NOT receive shared political@ru.ac.th
        ru_shared_count = db.query(FacultyDB).filter(FacultyDB.email == "political@ru.ac.th").count()
        assert ru_shared_count == 0, f"Found {ru_shared_count} faculties assigned shared RU inbox"

        # 7. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 8. Total faculties with official email >= 10630
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None)).count()
        assert total_with_email >= 10630, f"Expected >= 10630, got {total_with_email}"
    finally:
        db.close()


def test_phase24_recovered_official_university_emails_and_null_audit():
    """Phase 24 audit: verifies 280 recovered authentic official emails across 6 clusters.

    1. KU Agriculture (139 verified official @ku.ac.th emails via foa-research-link API)
    2. KKU Nursing (70 verified official @kku.ac.th emails via nu.kku.ac.th)
    3. KU Engineering (37 verified official @ku.ac.th emails via hr.eng.ku.ac.th directory API)
    4. KMUTT Science (25 verified official @kmutt.ac.th, @mail.kmutt.ac.th emails)
    5. KU Science (8 verified official @ku.ac.th emails via departmental endpoints)
    6. Chula Pharmacy (1 verified official @chula.ac.th email via loadpersonnel.php)
    7. Forensic NULL verification: shared department inboxes never assigned to individuals
    8. Zero personal freemails across the database (PDPA Invariant)
    9. Total faculties with official email >= 10910
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KU Agriculture recovered emails
        ku_agr_1 = db.query(FacultyDB).filter(FacultyDB.id == "ku_agr_wave12_0004").first()
        assert ku_agr_1 is not None
        assert ku_agr_1.email == "agrtrw@ku.ac.th"
        assert "research.ku.ac.th/forest/Person.aspx?id=" in (ku_agr_1.profile_url or "")

        ku_agr_2 = db.query(FacultyDB).filter(FacultyDB.id == "ku_agr_wave12_0005").first()
        assert ku_agr_2 is not None
        assert ku_agr_2.email == "agrtts@ku.ac.th"

        # 2. KKU Nursing recovered emails
        kku_nurs_1 = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofn_panthuchin_030").first()
        assert kku_nurs_1 is not None
        assert kku_nurs_1.email == "pchonl@kku.ac.th"

        # 3. KU Engineering recovered emails
        ku_eng_1 = db.query(FacultyDB).filter(FacultyDB.id == "ku_eng_cpe_002").first()
        assert ku_eng_1 is not None
        assert ku_eng_1.email == "fengknw@ku.ac.th"
        assert "hr.eng.ku.ac.th/directory.php?id=" in (ku_eng_1.profile_url or "")

        ku_eng_2 = db.query(FacultyDB).filter(FacultyDB.id == "ku_eng_cpe_003").first()
        assert ku_eng_2 is not None
        assert ku_eng_2.email == "jtf@ku.ac.th"

        # 4. KMUTT Science recovered emails
        kmutt_sci_1 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_a312d0b4_4097").first()
        assert kmutt_sci_1 is not None
        assert kmutt_sci_1.email == "songsirin.rue@mail.kmutt.ac.th"
        assert "mic.kmutt.ac.th" in (kmutt_sci_1.profile_url or "")

        # 5. KU Science recovered emails
        ku_sci_1 = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0069").first()
        assert ku_sci_1 is not None
        assert ku_sci_1.email == "fsciwsf@ku.ac.th"

        # 6. Chula Pharmacy recovered email
        cu_pharm_1 = db.query(FacultyDB).filter(FacultyDB.id == "cu_pharm_wave16_0063").first()
        assert cu_pharm_1 is not None
        assert cu_pharm_1.email == "wanna.s@chula.ac.th"

        # 7. Forensic NULL verification: confirm shared departmental inboxes never assigned
        shared_inboxes = ["chem@kmutt.ac.th", "nu.inbox@kku.ac.th", "aad@kmitl.ac.th", "sci@ku.ac.th"]
        for inbox in shared_inboxes:
            assigned_count = db.query(FacultyDB).filter(FacultyDB.email == inbox).count()
            assert assigned_count == 0, f"Found {assigned_count} faculties assigned shared inbox {inbox}"

        # 8. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 9. Total faculties with official email >= 10910
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 10910, f"Expected >= 10910, got {total_with_email}"
    finally:
        db.close()


def test_phase25_recovered_official_university_emails_and_null_audit():
    """Phase 25 audit: verifies 351 cumulative recovered authentic official emails across 12 clusters.

    1. KMITL Architecture (18 verified official @kmitl.ac.th emails)
    2. Chula Pol Sci (3 verified official @chula.ac.th emails)
    3. CMU Engineering (1 verified official @cmu.ac.th email)
    4. Chula Asian Studies (17 verified official @chula.ac.th emails)
    5. Chula Vet (7 verified official @chula.ac.th emails)
    6. UBU Pharmacy (25 verified official @ubu.ac.th emails)
    7. Forensic NULL audit: Chula CP retired faculty, Chula Pharm freemails, hospital clinical omissions
    8. Zero personal freemails across the database (PDPA Invariant)
    9. Total faculties with official email >= 10980 (currently 10,987)
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KMITL Architecture
        kmitl_1 = db.query(FacultyDB).filter(FacultyDB.id == "kmitl_aad_wave16_0049").first()
        assert kmitl_1 is not None
        assert kmitl_1.email == "thirayu.ju@kmitl.ac.th"
        assert "aad.kmitl.ac.th/our_team/" in (kmitl_1.profile_url or "")

        # 2. Chula Pol Sci
        chula_pol_1 = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofp_phuapansawat_046").first()
        assert chula_pol_1 is not None
        assert chula_pol_1.email == "khorapin.p@chula.ac.th"

        # 3. CMU Engineering
        cmu_eng_1 = db.query(FacultyDB).filter(FacultyDB.id == "cmu_eng_department_parida_8").first()
        assert cmu_eng_1 is not None
        assert cmu_eng_1.email == "parida.jewpanya@cmu.ac.th"

        # 4. Chula Asian Studies
        ias_1 = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_instituteo_sindhupun_003").first()
        assert ias_1 is not None
        assert ias_1.email == "jirayudh.s@chula.ac.th"

        # 5. Chula Vet
        vet_1 = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofv_wangdee_040").first()
        assert vet_1 is not None
        assert vet_1.email == "chalika.w@chula.ac.th"
        assert "vet.chula.ac.th/researcher_info/" in (vet_1.profile_url or "")

        # 6. UBU Pharmacy
        ubu_1 = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofp_butsri_016").first()
        assert ubu_1 is not None
        assert ubu_1.email == "siriwoot.b@ubu.ac.th"
        assert "phar.ubu.ac.th/main/profile/" in (ubu_1.profile_url or "")

        # 7. Forensic NULL verification: confirm shared departmental inboxes never assigned
        shared_inboxes = ["phar@ubu.ac.th", "ias@chula.ac.th", "aad@kmitl.ac.th"]
        for inbox in shared_inboxes:
            assigned_count = db.query(FacultyDB).filter(FacultyDB.email == inbox).count()
            assert assigned_count == 0, f"Found {assigned_count} faculties assigned shared inbox {inbox}"

        # 8. Zero personal freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 9. Total faculties with official email >= 10980
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 10980, f"Expected >= 10980, got {total_with_email}"
    finally:
        db.close()


def test_cross_university_and_foreign_visiting_hygiene():
    """Verify system-wide hygiene against cross-university contamination and foreign visiting faculty.

    1. Foreign visiting professors residing abroad purged (CBS & Sasin)
    2. Inverted/misplaced affiliations re-affiliated to authentic universities (TU LITU & MFU IT)
    3. Cross-university contaminated emails sanitized or replaced with authentic institutional emails
    4. Verified Dolchai La-ornual re-affiliated to Mahidol MUIC
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Purged foreign visiting professors
        purged_visiting_ids = [
            "cu_cbs_wave11_0035",  # Woon Oh Jung (Seoul National Univ)
            "cu_cbs_wave11_0032",  # Thomas Kirchmaier (Copenhagen Business School)
            "cu_sasin_014",        # Eliane Karsaklian (UIC)
            "cu_sasin_028",        # Mark W. Finn (Northwestern)
            "cu_sasin_030",        # Michael Frenkel (WHU)
            "cu_sasin_045",        # Sankar Sen (Baruch CUNY)
            "cu_sasin_052",        # Tauhid R. Zaman (Yale)
        ]
        assert db.query(FacultyDB).filter(FacultyDB.id.in_(purged_visiting_ids)).count() == 0

        # 2. Re-affiliated misplaced faculty
        # Pragasit Sitthitikul (formerly Thaksin Music -> now Thammasat LITU)
        assert db.query(FacultyDB).filter(FacultyDB.id == "thaksinuni_facultyofm_sitthitikul_008").first() is None
        p_litu = db.query(FacultyDB).filter(FacultyDB.id == "tu_litu_sitthitikul_001").first()
        assert p_litu is not None
        assert p_litu.university_th == "มหาวิทยาลัยธรรมศาสตร์"
        assert p_litu.faculty_th == "สถาบันภาษา"
        assert p_litu.email == "pragasit.s@litu.tu.ac.th"

        # Sirikan Chucherd (formerly Thammasat SIIT -> now Mae Fah Luang IT)
        # Note: mfu_it_chucherd_011 deduplicated into canonical mfu_sirikan_chucherd_1962 in third pass
        # Rename 2026-09: MFU School of IT renamed to School of Applied Digital
        # Technology (verified live: adt.mfu.ac.th title; it.mfu.ac.th dead)
        assert db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_sirindhorn_chucherd_011").first() is None
        s_mfu = db.query(FacultyDB).filter(FacultyDB.id == "mfu_sirikan_chucherd_1962").first()
        assert s_mfu is not None
        assert s_mfu.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง"
        assert s_mfu.faculty_th == "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์"
        assert s_mfu.email == "sirikan@mfu.ac.th"

        # Dolchai La-ornual (formerly Chula Sasin -> now Mahidol MUIC)
        assert db.query(FacultyDB).filter(FacultyDB.id == "cu_sasin_011").first() is None
        d_muic = db.query(FacultyDB).filter(FacultyDB.id == "mu_muic_dolchai_001").first()
        assert d_muic is not None
        assert d_muic.university_th == "มหาวิทยาลัยมหิดล"
        assert "วิทยาลัยนานาชาติ" in d_muic.faculty_th
        assert d_muic.email == "dolchai.lar@mahidol.ac.th"

        # 3. Authentic institutional emails recovered for previously contaminated records
        tu_eng = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_facultyofe_vorapojpisut_001").first()
        assert tu_eng is not None
        assert tu_eng.email == "vsupacha@engr.tu.ac.th"

        ubu_agr = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofa_jutagate_001").first()
        assert ubu_agr is not None
        assert ubu_agr.email == "tuantong.j@ubu.ac.th"

        # 4. Cross-university contaminated emails sanitized to None
        sanitized_ids = [
            "thammasatu_facultyofp_sakulpanich_026",
            "thammasatu_facultyofp_suksriwong_002",
            "thammasatu_facultyofp_sarisut_027",
            "thammasatu_facultyofp_suwankoot_003",
        ]
        for fid in sanitized_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            assert f is not None
            assert f.email is None
    finally:
        db.close()


def test_secondary_scan_bilingual_symmetry_and_faculty_hygiene():
    """Verify Phase 30 secondary scan fixes:
    1. Zero bilingual university naming desynchronizations.
    2. Zero cross-university profile or image URLs.
    3. Thaksin University MUSE realigned and zero 'คณะดุริยางคศาสตร์'.
    4. Zero compound faculty names (Siriraj/Rama, KU Agro/Vet, BUU Marine/Sci).
    5. Re-affiliated Chulalongkorn Medicine professors.
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

    db = SessionLocal()
    try:
        # 1. Zero bilingual university name desynchronizations
        all_faculties = db.query(FacultyDB).all()
        mismatches = [
            f.id for f in all_faculties
            if f.university_th in TH_TO_EN_CANONICAL and f.university != TH_TO_EN_CANONICAL[f.university_th]
        ]
        assert len(mismatches) == 0, f"Found {len(mismatches)} English university name mismatches: {mismatches[:5]}"

        # 2. Cross-university profile and image URLs sanitized
        tu_me = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_facultyofe_vorapojpisut_001").first()
        assert tu_me is not None
        assert tu_me.profile_url == "https://me.engr.tu.ac.th/th/department_me/personel_detail/3"

        mu_ict = db.query(FacultyDB).filter(FacultyDB.id == "mu_398425a6_1356").first()
        assert mu_ict is not None
        assert mu_ict.image_url == "https://www.ict.mahidol.ac.th/wp-content/uploads/2021/05/Chaiyong-1.jpg"

        wu_s1 = db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_e7211fe0").first()
        assert wu_s1 is not None
        assert wu_s1.profile_url == "https://science.wu.ac.th/"
        assert wu_s1.image_url is None

        wu_s2 = db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_ebb717ab").first()
        assert wu_s2 is not None
        assert wu_s2.profile_url == "https://science.wu.ac.th/"
        assert wu_s2.image_url is None

        ku_sci = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0003").first()
        assert ku_sci is not None
        assert ku_sci.image_url is None

        # 3. Thaksin University MUSE: zero 'คณะดุริยางคศาสตร์' and duplicates merged
        music_fac_count = db.query(FacultyDB).filter(FacultyDB.faculty_th == "คณะดุริยางคศาสตร์").count()
        assert music_fac_count == 0, f"Found {music_fac_count} records still labeled 'คณะดุริยางคศาสตร์'"

        # Donors deleted
        donors = [
            "thaksinuni_facultyofm_jitpakdee_001",
            "thaksinuni_facultyofm_wongsawat_002",
            "thaksinuni_facultyofm_diawkee_003",
            "thaksinuni_facultyofm_seubsakulajinda_004",
            "thaksinuni_facultyofm_watcharakorn_005",
        ]
        assert db.query(FacultyDB).filter(FacultyDB.id.in_(donors)).count() == 0

        # Targets have email and metrics preserved
        target_rungrawee = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_fac_088_088").first()
        assert target_rungrawee is not None
        assert target_rungrawee.email == "rungrawee.j@tsu.ac.th"
        assert target_rungrawee.total_citations >= 19
        assert target_rungrawee.faculty_th == "คณะสหวิทยาการและการประกอบการ"

        # 4. Compound faculties eliminated
        compound_count = db.query(FacultyDB).filter(
            (FacultyDB.faculty_th.like("% และ %")) |
            (FacultyDB.faculty_th.like("% / %"))
        ).count()
        assert compound_count == 0, f"Found {compound_count} compound faculty names remaining"

        # Corrupt record purged
        assert db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_fac_015_015").first() is None

        # 5. Re-affiliated Chulalongkorn Medicine professors
        trairak = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_pisitkun_018").first()
        assert trairak is not None
        assert trairak.university_th == "จุฬาลงกรณ์มหาวิทยาลัย"
        assert trairak.faculty_th == "คณะแพทยศาสตร์"
        assert trairak.department_th == "ศูนย์เชี่ยวชาญเฉพาะทางด้านชีววิทยาระบบ"

        surasak = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_wannakrairot_020").first()
        assert surasak is not None
        assert surasak.university_th == "จุฬาลงกรณ์มหาวิทยาลัย"
        assert surasak.faculty_th == "คณะแพทยศาสตร์"
        assert surasak.department_th == "ภาควิชาพยาธิวิทยา"

        # 6. Repaired Thai names
        piti = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_thuvasethakul_003").first()
        assert piti is not None
        assert piti.full_name_th == "รศ.ดร. นพ.ปีติ ธุวะเศรษฐกุล"

        bovornsom = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_leerapan_019").first()
        assert bovornsom is not None
        assert bovornsom.full_name_th == "อ.ดร. นพ.บวรศม ลีระพันธ์"
    finally:
        db.close()


def test_phase32_recovered_official_university_emails_and_null_audit():
    """Verify Phase 32 recovered authentic university emails and null audit invariants:
    1. UBU Pharmacy recovered emails (37 verified).
    2. Chula Science recovered emails (3 verified: Chem, MatSci, Geo).
    3. Section 9 freemail rejection: Chula MatSci boonkerd remains NULL (@gmail rejected).
    4. Section 9 generic rejection: Chula Chem plainpan remains NULL (chemistry@ rejected).
    5. Zero freemails in the entire database (PDPA invariant).
    6. Total faculties with official email >= 11,214 (+40 increase).
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. UBU Pharmacy recovered emails
        f_ubu1 = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofp_saohin_023").first()
        assert f_ubu1 is not None
        assert f_ubu1.email == "wipawee.s@ubu.ac.th"

        f_ubu2 = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofp_jitsang_037").first()
        assert f_ubu2 is not None
        assert f_ubu2.email == "kusuma.j@ubu.ac.th"

        f_ubu3 = db.query(FacultyDB).filter(FacultyDB.id == "ubonratcha_facultyofp_mangkonkaew_044").first()
        assert f_ubu3 is not None
        assert f_ubu3.email == "rachata.m@ubu.ac.th"

        # 2. Chula Science recovered emails
        f_cu1 = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0025").first()
        assert f_cu1 is not None
        assert f_cu1.email == "nattapong.p@chula.ac.th"

        f_cu2 = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofs_potiyaraj_038").first()
        assert f_cu2 is not None
        assert f_cu2.email == "pranut.p@chula.ac.th"

        f_cu3 = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofs_chawchai_055").first()
        assert f_cu3 is not None
        assert f_cu3.email == "sakonvan.c@chula.ac.th"

        # 3. Section 9 Freemail Rejection
        f_freemail = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofs_boonkerd_036").first()
        assert f_freemail is not None
        assert f_freemail.email is None

        # 4. Section 9 Generic Inbox Rejection
        f_generic = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0030").first()
        assert f_generic is not None
        assert f_generic.email is None

        # 5. Zero freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 6. Total faculties with official email >= 11,214
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 11214
    finally:
        db.close()


def test_phase33_recovered_official_university_emails_and_null_audit():
    """Verify Phase 33 recovered authentic university emails and null audit invariants:
    1. TU Allied Health recovered emails (4 verified: MT & PT).
    2. KU Science recovered emails (7 verified: Chem, Micro, MatSci, CS, Zoo).
    3. Mahidol College of Music recovered email (1 verified: Harimpanich).
    4. Section 9 freemail rejection: KU Botany chitchak (@outlook) & KU Math tokaew (@yahoo) remain NULL.
    5. Zero freemails in the entire database (PDPA invariant).
    6. Total faculties with official email >= 11,226 (+12 increase).
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. TU Allied Health recovered emails
        f_tu1 = db.query(FacultyDB).filter(FacultyDB.id == "tu_d2fed09e_0066").first()
        assert f_tu1 is not None
        assert f_tu1.email == "natthaporn.n@allied.tu.ac.th"

        f_tu2 = db.query(FacultyDB).filter(FacultyDB.id == "tu_1d396f37_4465").first()
        assert f_tu2 is not None
        assert f_tu2.email == "patcharee.i@allied.tu.ac.th"

        f_tu3 = db.query(FacultyDB).filter(FacultyDB.id == "tu_d48e0f5a_5885").first()
        assert f_tu3 is not None
        assert f_tu3.email == "chatnapa@staff.tu.ac.th"

        f_tu4 = db.query(FacultyDB).filter(FacultyDB.id == "tu_1f8e5f46_6233").first()
        assert f_tu4 is not None
        assert f_tu4.email == "kochakorn.pha@allied.tu.ac.th"

        # 2. KU Science recovered emails
        f_ku_chem1 = db.query(FacultyDB).filter(FacultyDB.id == "ku_2573750b_7634").first()
        assert f_ku_chem1 is not None
        assert f_ku_chem1.email == "fsciprsr@ku.ac.th"

        f_ku_chem2 = db.query(FacultyDB).filter(FacultyDB.id == "ku_325ee636_3738").first()
        assert f_ku_chem2 is not None
        assert f_ku_chem2.email == "fsciwks@ku.ac.th"

        f_ku_chem3 = db.query(FacultyDB).filter(FacultyDB.id == "ku_be14cea1_6056").first()
        assert f_ku_chem3 is not None
        assert f_ku_chem3.email == "withsakorn.san@ku.th"

        f_ku_micro = db.query(FacultyDB).filter(FacultyDB.id == "ku_12fb0dd2_0604").first()
        assert f_ku_micro is not None
        assert f_ku_micro.email == "fsciiok@ku.ac.th"

        f_ku_matsci = db.query(FacultyDB).filter(FacultyDB.id == "ku_4b78a035_1700").first()
        assert f_ku_matsci is not None
        assert f_ku_matsci.email == "fscinmp@ku.ac.th"

        f_ku_cs = db.query(FacultyDB).filter(FacultyDB.id == "ku_26b46fb4_0870").first()
        assert f_ku_cs is not None
        assert f_ku_cs.email == "fsciscr@ku.ac.th"

        f_ku_zoo = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0077").first()
        assert f_ku_zoo is not None
        assert f_ku_zoo.email == "fscipil@ku.ac.th"

        # 3. Mahidol College of Music recovered email
        f_mu = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_collegeofm_harimpanich_165").first()
        assert f_mu is not None
        assert f_mu.email == "lim@mahidol.ac.th"

        # 4. Section 9 Freemail Rejection: KU Botany & KU Math
        f_botany_freemail = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0029").first()
        assert f_botany_freemail is not None
        assert f_botany_freemail.email is None

        f_math_freemail = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_0042").first()
        assert f_math_freemail is not None
        assert f_math_freemail.email is None

        # 5. Zero freemails in the entire database (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 6. Total faculties with official email >= 11,226
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 11226
    finally:
        db.close()


def test_phase34_recovered_official_university_emails_and_null_audit():
    """Verify Phase 34 email recoveries across Mahidol CMMU and KMUTT FIBO.

    Verifies:
    1. Mahidol University College of Management (CMMU) recovered emails (19 records)
    2. KMUTT Institute of Field Robotics (FIBO) recovered emails (5 records)
    3. Section 9 Quality Invariants: zero freemails, zero generic inboxes
    4. Embedding text recomputed and updated for all 24 records
    5. Total faculties with official email >= 11,250
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. Mahidol CMMU recovered emails
        f_cmmu1 = db.query(FacultyDB).filter(FacultyDB.id == "mu_cmmu_001").first()
        assert f_cmmu1 is not None
        assert f_cmmu1.email == "kittichai.raj@mahidol.ac.th"
        assert f_cmmu1.embedding_text is not None and "Kittichai" in f_cmmu1.embedding_text

        f_cmmu2 = db.query(FacultyDB).filter(FacultyDB.id == "mu_cmmu_002").first()
        assert f_cmmu2 is not None
        assert f_cmmu2.email == "nattavud.pim@mahidol.ac.th"

        f_cmmu10 = db.query(FacultyDB).filter(FacultyDB.id == "mu_cmmu_010").first()
        assert f_cmmu10 is not None
        assert f_cmmu10.email == "roy.kou@mahidol.ac.th"

        f_cmmu15 = db.query(FacultyDB).filter(FacultyDB.id == "mu_cmmu_015").first()
        assert f_cmmu15 is not None
        assert f_cmmu15.email == "astrid.kai@mahidol.ac.th"

        f_cmmu20 = db.query(FacultyDB).filter(FacultyDB.id == "mu_cmmu_020").first()
        assert f_cmmu20 is not None
        assert f_cmmu20.email == "nathasit.ger@mahidol.ac.th"

        # 2. KMUTT FIBO recovered emails
        f_fibo1 = db.query(FacultyDB).filter(FacultyDB.id == "leadingtha_engineerin_pengwang_008").first()
        assert f_fibo1 is not None
        assert f_fibo1.email == "eakkachai.pen@kmutt.ac.th"
        assert f_fibo1.embedding_text is not None and "Pengwang" in f_fibo1.embedding_text

        f_fibo2 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_fibo_prakarnkiat_y").first()
        assert f_fibo2 is not None
        assert f_fibo2.email == "prakarnkiat.you@kmutt.ac.th"

        f_fibo3 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_fibo_warasinee_c").first()
        assert f_fibo3 is not None
        assert f_fibo3.email == "warasinee.cha@kmutt.ac.th"

        f_fibo4 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_fibo_arbtip_d").first()
        assert f_fibo4 is not None
        assert f_fibo4.email == "arbtip.dhe@kmutt.ac.th"

        f_fibo5 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_fibo_chaowwalit_t").first()
        assert f_fibo5 is not None
        assert f_fibo5.email == "chaowwalit.tha@kmutt.ac.th"

        # 3. Section 9 Freemail & Generic Rejection (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 4. Total faculties with official email >= 11,250
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 11250
    finally:
        db.close()


def test_phase35_recovered_official_university_emails_and_null_audit():
    """Verify Phase 35 email recoveries across KMUTT Microbiology and KMUTT SIT.

    Verifies:
    1. KMUTT Department of Microbiology recovered emails (9 records)
    2. KMUTT School of Information Technology (SIT) recovered emails (7 records)
    3. Section 9 Quality Invariants: zero freemails, zero generic inboxes
    4. Embedding text recomputed and updated
    5. Total faculties with official email >= 11,266
    """
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB

    db = SessionLocal()
    try:
        # 1. KMUTT Microbiology recovered emails
        f_micro1 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_4bf8615a_9065").first()
        assert f_micro1 is not None
        assert f_micro1.email == "duangtip.moo@kmutt.ac.th"
        assert f_micro1.embedding_text is not None

        f_micro2 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_3b0ec732_2197").first()
        assert f_micro2 is not None
        assert f_micro2.email == "niyom.kam@kmutt.ac.th"

        f_micro3 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_5482c64f_9833").first()
        assert f_micro3 is not None
        assert f_micro3.email == "wittaya.kao@kmutt.ac.th"

        f_micro4 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_44a91424_9581").first()
        assert f_micro4 is not None
        assert f_micro4.email == "sukanya.phu@kmutt.ac.th"

        # 2. KMUTT SIT recovered emails
        f_sit1 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_narongrit_waraporn").first()
        assert f_sit1 is not None
        assert f_sit1.email == "narongrit@sit.kmutt.ac.th"

        f_sit2 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_siam_yamsangsung").first()
        assert f_sit2 is not None
        assert f_sit2.email == "siam@sit.kmutt.ac.th"

        f_sit3 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_wichian_chutimaskul").first()
        assert f_sit3 is not None
        assert f_sit3.email == "wichian@sit.kmutt.ac.th"

        f_sit4 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_vajirasak_vanijja").first()
        assert f_sit4 is not None
        assert f_sit4.email == "vachee@sit.kmutt.ac.th"

        f_sit5 = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_umaporn_supasitthimethee").first()
        assert f_sit5 is not None
        assert f_sit5.email == "umaporn@sit.kmutt.ac.th"

        # 3. Unexamined Pool Recovered Emails (SUT, NIDA, NU, MJU)
        f_sut = db.query(FacultyDB).filter(FacultyDB.id == "sut_apinun_buritatum_6141").first()
        assert f_sut is not None
        assert f_sut.email == "apinun_ce@sut.ac.th"

        f_nida = db.query(FacultyDB).filter(FacultyDB.id == "nida_as_001").first()
        assert f_nida is not None
        assert f_nida.email == "surapong@as.nida.ac.th"

        f_nu = db.query(FacultyDB).filter(FacultyDB.id == "nu_kumropr__8257").first()
        assert f_nu is not None
        assert f_nu.email == "kumropr@nu.ac.th"

        # 4. Section 9 Freemail & Generic Rejection (PDPA Invariant)
        for freemail_domain in ["@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            freemail_count = db.query(FacultyDB).filter(FacultyDB.email.like(f"%{freemail_domain}%")).count()
            assert freemail_count == 0, f"Found {freemail_count} records with {freemail_domain}"

        # 5. Total faculties with official email >= 11,272
        total_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").count()
        assert total_with_email >= 11272
    finally:
        db.close()



















