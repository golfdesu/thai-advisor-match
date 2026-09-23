# -*- coding: utf-8 -*-
"""
Resolve Wave 81 Duplicates & Graduate Harmonization
===================================================
Harmonizes and consolidates graduate faculty profiles across Top 5 Thai universities:
1. Cross-University Graduate Harmonization:
   A. Chulalongkorn University (CU):
      - คณะเกษตรศาสตร์บูรณาการ -> สำนักวิชาทรัพยากรการเกษตร (1 course aligned to 13 CUSAR professors)
      - บัณฑิตวิทยาลัย (สหสาขาวิชา) & วิทยาลัยสหศาสตร์บูรณาการแห่งจุฬาฯ (38 graduate courses aligned to authentic host faculties):
        * สรีรวิทยา / จุลชีววิทยาทางการแพทย์ / เภสัชวิทยา / ชีวเวชศาสตร์ -> คณะแพทยศาสตร์
        * วิทยาศาสตร์สิ่งแวดล้อม / การจัดการสารอันตราย / ชีวสารสนเทศศาสตร์ / นาโนวิทยา -> คณะวิทยาศาสตร์
        * ทันตชีววัสดุศาสตร์ -> คณะทันตแพทยศาสตร์
        * การจัดการโลจิสติกส์ / ธุรกิจเทคโนโลยีและการจัดการนวัตกรรม -> คณะพาณิชยศาสตร์และการบัญชี
        * การจัดการภาษี -> คณะนิติศาสตร์
        * เกาหลีศึกษา / เอเชียตะวันออกเฉียงใต้ / ภาษาอังกฤษสากล -> คณะอักษรศาสตร์
        * สิ่งแวดล้อม การพัฒนา และความยั่งยืน (ESD) / พัฒนามนุษย์และสังคม / กิจการทางทะเล -> คณะรัฐศาสตร์
        * การจัดการทางวัฒนธรรม -> คณะศิลปกรรมศาสตร์
        * เทคโนโลยีและการจัดการพลังงาน / การจัดการความเสี่ยงและภัยพิบัติ -> คณะวิศวกรรมศาสตร์
   B. Thammasat University (TU):
      - TUXSA Online Courses & กองบริหารงานวิชาการ:
        * Data Science / Business Innovation / Distance MBA -> คณะพาณิชยศาสตร์และการบัญชี
        * Applied AI and IoT -> คณะวิศวกรรมศาสตร์
        * Learning Innovation -> คณะวิทยาการเรียนรู้และศึกษาศาสตร์
   C. Mahidol University (MU):
      - สถาบันวิทยาศาสตร์การวิเคราะห์และตรวจสารในการกีฬา -> คณะวิทยาศาสตร์
      - โครงการจัดตั้งวิทยาเขตนครสวรรค์ -> คณะสิ่งแวดล้อมและทรัพยากรศาสตร์
      - โครงการจัดตั้งวิทยาเขตอำนาจเจริญ -> คณะสาธารณสุขศาสตร์
      - โครงการร่วม คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี สถาบันโภชนาการ -> สถาบันโภชนาการ
      - โครงการร่วมคณะแพทยศาสตร์ศิริราชพยาบาล คณะวิศวกรรมศาสตร์ และคณะเทคนิคการแพทย์ -> คณะแพทยศาสตร์ศิริราชพยาบาล
   D. Kasetsart University (KU):
      - บัณฑิตวิทยาลัย (พันธุวิศวกรรมและชีวสารสนเทศ) -> คณะวิทยาศาสตร์
   E. Chiang Mai University (CMU):
      - สถาบันวิจัยวิทยาศาสตร์สุขภาพ (การวิจัยวิทยาศาสตร์สุขภาพ) -> คณะแพทยศาสตร์
2. Synchronizing English university name (university) from TH_TO_EN_CANONICAL.
3. Sanitizing empty strings to None across all URL/email/name fields.
4. Enforcing Bibliometric Monotonicity Invariant (total_publications_count >= h_index).
5. Deduplicating identical OpenAlex IDs within and across universities.
6. Exact & normalized Thai name deduplication within university.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB, CourseDB, ScholarUnassignedDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching, get_email_univ_safe
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL


def merge_faculty_pair(primary: FacultyDB, secondary: FacultyDB, db) -> str:
    """Merges secondary into primary, retaining max metrics and authentic contact info."""
    if secondary.academic_title_th and (not primary.academic_title_th or primary.academic_title_th in ["อาจารย์", "อ."]):
        primary.academic_title_th = secondary.academic_title_th
    if secondary.email and not primary.email:
        primary.email = secondary.email
    if secondary.image_url and not primary.image_url:
        primary.image_url = secondary.image_url
    if secondary.department_th and (not primary.department_th or primary.department_th == "ระบุไม่ได้"):
        primary.department_th = secondary.department_th

    # Bibliometrics: preserve max
    primary.total_citations = max(primary.total_citations or 0, secondary.total_citations or 0)
    primary.h_index = max(primary.h_index or 0, secondary.h_index or 0)
    primary.total_publications_count = max(
        primary.total_publications_count or 0,
        secondary.total_publications_count or 0,
        primary.h_index or 0,
    )

    # Authorship breakdown preservation
    if (secondary.first_author_count or 0) > 0 or (secondary.co_author_count or 0) > 0:
        primary.first_author_count = max(primary.first_author_count or 0, secondary.first_author_count or 0)
        primary.co_author_count = max(primary.co_author_count or 0, secondary.co_author_count or 0)
        primary.total_publications_count = max(
            primary.total_publications_count or 0,
            (primary.first_author_count or 0) + (primary.co_author_count or 0),
        )

    # OpenAlex ID: preserve authentic ID
    if (not primary.openalex_id or primary.openalex_id == "not_indexed") and secondary.openalex_id and secondary.openalex_id != "not_indexed":
        primary.openalex_id = secondary.openalex_id

    # Union publications
    pubs_map = {}
    for p in primary.featured_publications or []:
        t = (p.get("title") or "").strip().lower()
        if t:
            pubs_map[t] = p
    for p in secondary.featured_publications or []:
        t = (p.get("title") or "").strip().lower()
        if t and t not in pubs_map:
            pubs_map[t] = p
    primary.featured_publications = list(pubs_map.values())[:10]

    # Union research interests
    nav_boilerplate = ["วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา", "Office:", "Email:"]
    seen_interests = set()
    cleaned_interests = []
    for item in (primary.research_interests or []) + (secondary.research_interests or []):
        parts = str(item).split(" / ")
        for p in parts:
            k = p.strip().rstrip(",;.:")
            if k.startswith(('"', "'")) and k.endswith(('"', "'")):
                k = k[1:-1].strip()
            if any(b in k for b in nav_boilerplate):
                continue
            if re.match(r"^\d+$", k):
                continue
            if "|" in k:
                k = k.replace("|", "").strip()
            if k and k.lower() not in seen_interests and len(k) > 1:
                seen_interests.add(k.lower())
                cleaned_interests.append(k)
    primary.research_interests = cleaned_interests

    sec_id = secondary.id
    db.commit()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = :sid
                ON CONFLICT (id) DO UPDATE SET
                    total_citations = EXCLUDED.total_citations,
                    h_index = EXCLUDED.h_index,
                    openalex_id = EXCLUDED.openalex_id;
            """),
            {"sid": sec_id},
        )
        conn.execute(text("DELETE FROM public.faculties WHERE id = :sid"), {"sid": sec_id})

    return sec_id


def resolve_wave81_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 81 TOP 5 GRADUATE HARMONIZATION & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 0: Cross-University Graduate Harmonization
        print("\n--- Step 0: Top 5 Graduate Course Harmonization ---", flush=True)

        # 0A: Chulalongkorn University
        cu_agri = db.query(CourseDB).filter(
            CourseDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
            CourseDB.faculty_th == "คณะเกษตรศาสตร์บูรณาการ",
        ).all()
        for c in cu_agri:
            c.faculty_th = "สำนักวิชาทรัพยากรการเกษตร"
            print(f'  [CU Agri Harmonization] "{c.title_th}" -> "สำนักวิชาทรัพยากรการเกษตร"')

        cu_inter_mappings = [
            ("สรีรวิทยา", "คณะแพทยศาสตร์"),
            ("จุลชีววิทยาทางการแพทย์", "คณะแพทยศาสตร์"),
            ("เภสัชวิทยา", "คณะแพทยศาสตร์"),
            ("ชีวเวชศาสตร์", "คณะแพทยศาสตร์"),
            ("วิทยาศาสตร์สิ่งแวดล้อม", "คณะวิทยาศาสตร์"),
            ("สารอันตราย", "คณะวิทยาศาสตร์"),
            ("ชีวสารสนเทศศาสตร์", "คณะวิทยาศาสตร์"),
            ("นาโนวิทยา", "คณะวิทยาศาสตร์"),
            ("สิ่งแวดล้อม", "คณะวิทยาศาสตร์"),
            ("ทันตชีววัสดุ", "คณะทันตแพทยศาสตร์"),
            ("โลจิสติกส์", "คณะพาณิชยศาสตร์และการบัญชี"),
            ("นวัตกรรม", "คณะพาณิชยศาสตร์และการบัญชี"),
            ("ภาษี", "คณะนิติศาสตร์"),
            ("เกาหลีศึกษา", "คณะอักษรศาสตร์"),
            ("เอเชียตะวันออกเฉียงใต้", "คณะอักษรศาสตร์"),
            ("ภาษาอังกฤษ", "คณะอักษรศาสตร์"),
            ("พัฒนามนุษย์", "คณะรัฐศาสตร์"),
            ("ทะเล", "คณะรัฐศาสตร์"),
            ("วัฒนธรรม", "คณะศิลปกรรมศาสตร์"),
            ("พลังงาน", "คณะวิศวกรรมศาสตร์"),
            ("ภัยพิบัติ", "คณะวิศวกรรมศาสตร์"),
        ]

        cu_inter_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
            CourseDB.faculty_th.in_([
                "วิทยาลัยสหศาสตร์บูรณาการแห่งจุฬาฯ",
                "วิทยาลัยสหศาสตร์บูรณาการแห่งจุฬาฯ / บัณฑิตวิทยาลัย",
                "บัณฑิตวิทยาลัย (สหสาขาวิชา)",
            ]),
        ).all()
        for c in cu_inter_courses:
            matched = False
            for kw, target_fac in cu_inter_mappings:
                if kw in c.title_th:
                    c.faculty_th = target_fac
                    print(f'  [CU Interdisciplinary Harmonization] "{c.title_th}" -> "{target_fac}"')
                    matched = True
                    break
            if not matched:
                c.faculty_th = "คณะวิทยาศาสตร์"

        # 0B: Thammasat University
        tu_online_mappings = [
            ("Data Science", "คณะพาณิชยศาสตร์และการบัญชี"),
            ("Business Innovation", "คณะพาณิชยศาสตร์และการบัญชี"),
            ("นวัตกรรมทางธุรกิจ", "คณะพาณิชยศาสตร์และการบัญชี"),
            ("Artificial Intelligence", "คณะวิศวกรรมศาสตร์"),
            ("Learning Innovation", "คณะวิทยาการเรียนรู้และศึกษาศาสตร์"),
        ]
        tu_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยธรรมศาสตร์",
            CourseDB.faculty_th.in_(["หลักสูตรออนไลน์", "กองบริหารงานวิชาการ"]),
        ).all()
        for c in tu_courses:
            for kw, target_fac in tu_online_mappings:
                if kw in c.title_th:
                    c.faculty_th = target_fac
                    print(f'  [TU Online Harmonization] "{c.title_th}" -> "{target_fac}"')
                    break

        # 0C: Mahidol University
        mu_mappings = [
            ("สถาบันวิทยาศาสตร์การวิเคราะห์และตรวจสารในการกีฬา", "คณะวิทยาศาสตร์"),
            ("โครงการจัดตั้งวิทยาเขตนครสวรรค์", "คณะสิ่งแวดล้อมและทรัพยากรศาสตร์"),
            ("โครงการจัดตั้งวิทยาเขตอำนาจเจริญ", "คณะสาธารณสุขศาสตร์"),
            ("โครงการร่วม คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี สถาบันโภชนาการ", "สถาบันโภชนาการ"),
            ("โครงการร่วมคณะแพทยศาสตร์ศิริราชพยาบาล คณะวิศวกรรมศาสตร์ และคณะเทคนิคการแพทย์", "คณะแพทยศาสตร์ศิริราชพยาบาล"),
        ]
        for old_f, new_f in mu_mappings:
            courses = db.query(CourseDB).filter(CourseDB.university_th == "มหาวิทยาลัยมหิดล", CourseDB.faculty_th == old_f).all()
            for c in courses:
                c.faculty_th = new_f
                print(f'  [Mahidol Harmonization] "{c.title_th}" -> "{new_f}"')

        # 0D: Kasetsart University
        ku_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยเกษตรศาสตร์",
            CourseDB.faculty_th == "บัณฑิตวิทยาลัย",
        ).all()
        for c in ku_courses:
            c.faculty_th = "คณะวิทยาศาสตร์"
            print(f'  [KU Harmonization] "{c.title_th}" -> "คณะวิทยาศาสตร์"')

        # 0E: Chiang Mai University
        cmu_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยเชียงใหม่",
            CourseDB.faculty_th == "สถาบันวิจัยวิทยาศาสตร์สุขภาพ",
        ).all()
        for c in cmu_courses:
            c.faculty_th = "คณะแพทยศาสตร์"
            print(f'  [CMU Harmonization] "{c.title_th}" -> "คณะแพทยศาสตร์"')

        db.commit()
        print("✅ Top 5 Graduate Course Harmonization completed.")

        # Step 1: English university name synchronization & empty string sanitization
        all_faculties = db.query(FacultyDB).all()
        for f in all_faculties:
            if f.university_th in TH_TO_EN_CANONICAL:
                expected_en = TH_TO_EN_CANONICAL[f.university_th]
                if f.university != expected_en:
                    f.university = expected_en

            # Sanitize empty strings to None
            if f.image_url == "":
                f.image_url = None
            if f.profile_url == "":
                f.profile_url = None
            if f.email == "":
                f.email = None
            if f.scholar_url == "":
                f.scholar_url = None
            if f.role == "":
                f.role = None
            if f.department == "":
                f.department = None
            if f.department_th == "":
                f.department_th = None

            # Bibliometric monotonicity
            if f.h_index is not None and (f.total_publications_count or 0) < f.h_index:
                f.total_publications_count = f.h_index

        db.commit()

        # Step 2: Deduplicate identical OpenAlex IDs
        dup_oa = (
            db.query(FacultyDB.openalex_id, text("count(*) as cnt"))
            .filter(FacultyDB.openalex_id.isnot(None), FacultyDB.openalex_id != "", FacultyDB.openalex_id != "not_indexed")
            .group_by(FacultyDB.openalex_id)
            .having(text("count(*) > 1"))
            .all()
        )
        print(f"\n--- Resolving {len(dup_oa)} Duplicate OpenAlex ID Clusters ---", flush=True)
        for oaid, cnt in dup_oa:
            records = db.query(FacultyDB).filter(FacultyDB.openalex_id == oaid).all()
            records.sort(
                key=lambda r: (
                    1 if r.email and "@" in r.email else 0,
                    1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                    1 if r.image_url else 0,
                    r.total_citations or 0,
                    r.h_index or 0,
                    1 if not r.id.startswith("univ_") else 0,
                ),
                reverse=True,
            )
            primary = records[0]
            p_cname = clean_thai_name_for_matching(primary.full_name_th)
            for secondary in records[1:]:
                s_cname = clean_thai_name_for_matching(secondary.full_name_th)
                same_person = (
                    (p_cname and s_cname and (p_cname in s_cname or s_cname in p_cname))
                    or (primary.first_name and secondary.first_name and primary.first_name.lower() == secondary.first_name.lower())
                )
                if same_person:
                    print(f"  - Merging OA {oaid}: ({secondary.id}) {secondary.full_name_th} -> ({primary.id}) {primary.full_name_th}")
                    merge_faculty_pair(primary, secondary, db)
                else:
                    print(f"  - Disambiguating OA collision for {oaid}: Disconnecting secondary ({secondary.id}) {secondary.full_name_th} from ({primary.id}) {primary.full_name_th}")
                    secondary.openalex_id = None
                    db.commit()

        # Step 3: Exact & normalized name duplicates within university
        all_facs = db.query(FacultyDB).all()
        norm_map = defaultdict(list)
        for f in all_facs:
            cname = clean_thai_name_for_matching(f.full_name_th)
            if cname and len(cname) > 3:
                norm_map[(f.university_th, cname)].append(f)

        print(f"\n--- Checking Normalized Name Clusters ---", flush=True)
        merged_count = 0
        for (u, cname), records in norm_map.items():
            if len(records) > 1:
                records.sort(
                    key=lambda r: (
                        1 if r.email and "@" in r.email else 0,
                        1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                        r.total_citations or 0,
                        r.h_index or 0,
                        1 if r.image_url else 0,
                    ),
                    reverse=True,
                )
                primary = records[0]
                for secondary in records[1:]:
                    print(f"  - Merging [{u}] {secondary.full_name_th} ({secondary.id}) into ({primary.id})")
                    merge_faculty_pair(primary, secondary, db)
                    merged_count += 1

        print(f"✅ Merged {merged_count} intra-university duplicate records.")
        db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 81 duplicate resolution and Top 5 graduate harmonization completed successfully!")


if __name__ == "__main__":
    resolve_wave81_duplicates()
