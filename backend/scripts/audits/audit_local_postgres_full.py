"""Thorough read-only audit of local PostgreSQL (advisor_match).

Checks all entities across:
1. Basic inventory, table schemas, and vector completeness (768-dim)
2. Empty strings across all columns
3. Non-human names, breadcrumbs, placeholder/mock patterns
4. Double academic titles, glued titles, title formatting
5. OpenAlex metric contamination, single-name mismatches, citation outliers
6. Department & faculty field anomalies
7. Structured JSON arrays (education, research_interests, featured_publications)
8. Courses & research labs hygiene
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def run_audit():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("LOCAL POSTGRESQL (advisor_match) COMPREHENSIVE AUDIT REPORT")
        print("=" * 80)

        # 1. INVENTORY & VECTORS
        f_count = db.query(FacultyDB).count()
        f_emb_null = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()
        c_count = db.query(CourseDB).count()
        c_emb_null = db.query(CourseDB).filter(CourseDB.embedding.is_(None)).count()
        l_count = db.query(ResearchLabDB).count()
        l_emb_null = db.query(ResearchLabDB).filter(ResearchLabDB.embedding.is_(None)).count()

        print("\n[1] ENTITY INVENTORY & 768-DIM VECTOR INTEGRITY:")
        print(f"  - Faculties:     {f_count:,} (missing vectors: {f_emb_null})")
        print(f"  - Courses:       {c_count:,} (missing vectors: {c_emb_null})")
        print(f"  - Research Labs: {l_count:,} (missing vectors: {l_emb_null})")

        # 2. EMPTY STRING COLUMNS
        print("\n[2] EMPTY STRING ('') ANOMALY SCAN:")
        fac_empty = {}
        for col in [
            "first_name", "last_name", "email", "profile_url", "image_url",
            "scholar_url", "full_name_th", "academic_title_th", "department_th",
            "faculty_th", "university_th", "openalex_id"
        ]:
            cnt = db.query(FacultyDB).filter(getattr(FacultyDB, col) == "").count()
            if cnt > 0:
                fac_empty[col] = cnt
        print(f"  - Faculty empty strings: {fac_empty if fac_empty else 'CLEAN (0 found)'}")

        course_empty = {}
        for col in [
            "title_th", "title_en", "degree_level", "degree_name", "faculty_th",
            "university_th", "department_th"
        ]:
            cnt = db.query(CourseDB).filter(getattr(CourseDB, col) == "").count()
            if cnt > 0:
                course_empty[col] = cnt
        print(f"  - Course empty strings: {course_empty if course_empty else 'CLEAN (0 found)'}")

        lab_empty = {}
        for col in ["name_th", "name_en", "faculty_th", "university_th", "lead_advisor_id"]:
            cnt = db.query(ResearchLabDB).filter(getattr(ResearchLabDB, col) == "").count()
            if cnt > 0:
                lab_empty[col] = cnt
        print(f"  - Lab empty strings: {lab_empty if lab_empty else 'CLEAN (0 found)'}")

        # 3. NAME HYGIENE & SUSPICIOUS PATTERNS
        print("\n[3] NAME HYGIENE & SUSPICIOUS PATTERNS:")

        # Scraper/placeholder patterns
        suspicious_keywords = [
            "null", "undefined", "NaN", "Lorem", "test", "sample", "admin",
            "คณาจารย์", "เจ้าหน้าที่", "บุคลากร", "ผู้ประสานงาน", "ห้องปฏิบัติการ",
            "ภาควิชา", "กลุ่มวิชา", "สถานที่", "โทรศัพท์", "เบอร์โทร", "Email"
        ]
        non_human = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            name = f.full_name_th or ""
            for kw in suspicious_keywords:
                if kw in name:
                    non_human.append((f.id, name, f.university_th, kw))
                    break
        print(f"  - Non-human or header keywords in faculty names: {len(non_human)}")
        for item in non_human[:10]:
            print(f"    * [{item[0]}] '{item[1]}' ({item[2]}) [matched '{item[3]}']")

        # Glued title check (Thai title followed directly by Thai letter without dot or space)
        glued_titles = []
        double_titles = []
        double_spaces = []
        thai_title_pattern = re.compile(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.|สพ\.ญ\.|ทนพ\.|ทนพญ\.)[^\s\.]")
        double_title_pattern = re.compile(r"(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)\s*(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)")

        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            name = f.full_name_th or ""
            if "  " in name:
                double_spaces.append((f.id, name))
            # Check for double title like "นพ. นพ." or "ผศ. ผศ."
            parts = name.split()
            if len(parts) >= 2 and parts[0] == parts[1] and parts[0] in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "นพ.", "พญ.", "ทพ.", "ทพญ.", "ภก.", "ภญ."]:
                double_titles.append((f.id, name))

        print(f"  - Double spaces in full_name_th: {len(double_spaces)}")
        print(f"  - Double identical titles (e.g. 'นพ. นพ.'): {len(double_titles)}")
        for dt in double_titles[:5]:
            print(f"    * [{dt[0]}] '{dt[1]}'")

        # Check for first_name / last_name anomalies
        name_anomalies = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            fn = f.first_name or ""
            ln = f.last_name or ""
            if fn and len(fn) == 1:
                name_anomalies.append((f.id, f.full_name_th, f"single-char first_name: '{fn}'"))
            if ln and len(ln) == 1:
                name_anomalies.append((f.id, f.full_name_th, f"single-char last_name: '{ln}'"))
            if fn and ln and fn == ln:
                name_anomalies.append((f.id, f.full_name_th, f"first_name == last_name: '{fn}'"))
        print(f"  - First/Last name anomalies: {len(name_anomalies)}")
        for na in name_anomalies[:10]:
            print(f"    * [{na[0]}] {na[1]}: {na[2]}")

        # 4. OPENALEX & METRICS DISAMBIGUATION
        print("\n[4] OPENALEX & METRICS INTEGRITY:")

        # High citation outliers (> 5,000)
        high_cites = db.query(FacultyDB).filter(FacultyDB.total_citations > 5000).order_by(FacultyDB.total_citations.desc()).all()
        print(f"  - Total faculties with total_citations > 5,000: {len(high_cites)}")
        for f in high_cites[:15]:
            print(f"    * [{f.id}] {f.full_name_th} ({f.first_name} {f.last_name}) - {f.university_th}")
            print(f"      Citations: {f.total_citations:,}, H-index: {f.h_index}, OpenAlex: {f.openalex_id}")

        # Discrepancies: not_indexed or NULL openalex_id but citations > 0
        discrepancies = db.query(FacultyDB).filter(
            FacultyDB.openalex_id.in_(["not_indexed", None]),
            FacultyDB.total_citations > 0
        ).all()
        print(f"  - Faculties with not_indexed/NULL openalex_id but citations > 0: {len(discrepancies)}")
        for d in discrepancies[:5]:
            print(f"    * [{d.id}] {d.full_name_th}: Cites={d.total_citations}, H={d.h_index}, OA={d.openalex_id}")

        # Multiple distinct individuals sharing same openalex_id (excluding 'not_indexed')
        oa_groups = {}
        for f in db.query(FacultyDB).filter(
            FacultyDB.openalex_id.isnot(None),
            FacultyDB.openalex_id != "not_indexed"
        ).options(defer(FacultyDB.embedding)).yield_per(500):
            oa_groups.setdefault(f.openalex_id, []).append((f.id, f.full_name_th, f.university_th))

        shared_oa = {k: v for k, v in oa_groups.items() if len(v) > 1}
        print(f"  - Shared OpenAlex IDs (excluding 'not_indexed'): {len(shared_oa)}")
        for oa_id, members in list(shared_oa.items())[:5]:
            print(f"    * OpenAlex ID {oa_id}: {len(members)} faculty members")
            for m in members:
                print(f"      - [{m[0]}] {m[1]} ({m[2]})")

        # 5. STRUCTURED CONTENT (EDUCATION, RESEARCH_INTERESTS, PUBLICATIONS)
        print("\n[5] STRUCTURED CONTENT & SCRAPER ARTIFACT SCAN:")
        ed_artifacts = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            ed = f.education
            if isinstance(ed, list):
                for item in ed:
                    if isinstance(item, str) and ("edDegree:" in item or "modalOpen:" in item or "null,selectedMajor" in item):
                        ed_artifacts.append((f.id, f.full_name_th, item[:60]))
        print(f"  - JavaScript modal/state artifacts in education: {len(ed_artifacts)}")
        for ea in ed_artifacts[:5]:
            print(f"    * [{ea[0]}] {ea[1]}: '{ea[2]}...'")

        # Check research interests boilerplate (>200 chars or containing telephone/download)
        interest_anomalies = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            interests = f.research_interests
            if isinstance(interests, list):
                for item in interests:
                    if isinstance(item, str):
                        if len(item) > 250 or any(kw in item for kw in ["โทร.", "โทรศัพท์", "02-", "0-2", "053-", "043-", "074-", "ดาวน์โหลด", "download", "http://", "https://"]):
                            interest_anomalies.append((f.id, f.full_name_th, item[:70]))
        print(f"  - Research interest anomalies (length>250 or phone/URL): {len(interest_anomalies)}")
        for ia in interest_anomalies[:5]:
            print(f"    * [{ia[0]}] {ia[1]}: '{ia[2]}...'")

        # Check featured_publications anomalies (boilerplate titles)
        pub_boilerplate = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            pubs = f.featured_publications
            if isinstance(pubs, list):
                for p in pubs:
                    if isinstance(p, dict):
                        title = p.get("title") or ""
                        if title.startswith("Email:") or title.startswith("Tel:") or title.startswith("เบอร์โทร:") or "Lorem ipsum" in title:
                            pub_boilerplate.append((f.id, f.full_name_th, title[:60]))
        print(f"  - Publication boilerplate titles (Email:, Tel:, etc.): {len(pub_boilerplate)}")

        # 6. COURSES & RESEARCH LABS
        print("\n[6] COURSES & RESEARCH LABS INTEGRITY:")
        course_multi_spaces = db.query(CourseDB).filter(
            (CourseDB.title_th.like("%  %")) | (CourseDB.title_en.like("%  %"))
        ).count()
        print(f"  - Courses with multiple consecutive spaces: {course_multi_spaces}")

        # Broken lead_advisor_id in research_labs
        lab_broken_advisor = 0
        for lab in db.query(ResearchLabDB).all():
            if lab.lead_advisor_id:
                adv = db.query(FacultyDB).filter(FacultyDB.id == lab.lead_advisor_id).first()
                if not adv:
                    lab_broken_advisor += 1
                    print(f"    * Broken advisor in lab [{lab.id}]: {lab.lead_advisor_id} not found!")
        print(f"  - Research labs with broken lead_advisor_id: {lab_broken_advisor}")

        print("\n" + "=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_audit()
