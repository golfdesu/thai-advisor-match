# -*- coding: utf-8 -*-
"""
Resolve Wave 80 Duplicates & Grounding Merge
============================================
Merges duplicates and consolidates profiles following Wave 80 acquisition:
1. Harmonizing Course-to-Faculty Naming:
   A. Sripatum University (SPU):
      - วิทยาลัยนานาชาติศรีปทุม -> วิทยาลัยบัณฑิตศึกษาด้านการจัดการ
      - มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น: บัณฑิตวิทยาลัย -> วิทยาลัยบัณฑิตศึกษาด้านการจัดการ
   B. Mae Fah Luang University (MFU):
      - Aligning 19 graduate courses from 'บัณฑิตวิทยาลัย' to their authentic host schools:
        * Cosmetic Science -> สำนักวิชาวิทยาศาสตร์เครื่องสำอาง
        * Anti-Aging & Regenerative Medicine / Science / Dermatology -> สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ
        * Public Health / Border Health / Sports Science -> สำนักวิชาวิทยาศาสตร์สุขภาพ
        * Applied Chemistry / Biological Science / Materials / Sustainable Environment -> สำนักวิชาวิทยาศาสตร์
        * Computer Engineering / Digital Transformation -> สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์
        * English for Professional Development -> สำนักวิชาศิลปศาสตร์
        * Health & Biomedical Analytics -> สำนักวิชาการแพทย์บูรณาการ
        * Innovative Food Science / Postharvest Technology -> สำนักวิชาอุตสาหกรรมเกษตร
        * International Development -> สำนักวิชานวัตกรรมสังคม
        * International Logistics -> สำนักวิชาการจัดการ
   C. Mahidol University (MU):
      - Aligning 23 graduate courses from 'บัณฑิตวิทยาลัย' to their authentic host faculties/institutes:
        * Orthopaedic Surgery -> คณะแพทยศาสตร์ศิริราชพยาบาล
        * Human Rights / Peace Studies -> สถาบันสิทธิมนุษยชนและสันติศึกษา
        * Population Research / Reproductive Health -> สถาบันวิจัยประชากรและสังคม
        * Social Innovation / Society Design / Ethics / Criminology -> คณะสังคมศาสตร์และมนุษยศาสตร์
        * Learning Innovation -> สถาบันนวัตกรรมการเรียนรู้
        * Child & Disability Quality of Life / Special Needs -> สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว
        * Food & Nutrition -> สถาบันโภชนาการ
        * Multicultural Studies / Linguistics / Museum Studies / Cultural Studies / ASEAN Studies -> สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย
   D. Chiang Mai University (CMU):
      - Aligning 11 graduate courses from 'วิทยาลัยพหุวิทยาการและสหวิทยาการ' and 'บัณฑิตวิทยาลัย':
        * Forensic Science / Mental Health -> คณะแพทยศาสตร์
        * Biotechnology -> คณะอุตสาหกรรมเกษตร
        * Sports Science -> คณะศึกษาศาสตร์
        * Contemporary Chinese -> คณะมนุษยศาสตร์
        * Integrated Science -> วิทยาลัยศิลปะ สื่อ และเทคโนโลยี
        * Marine Studies -> คณะวิทยาศาสตร์
        * บัณฑิตวิทยาลัย general -> คณะวิทยาศาสตร์
2. Synchronizing English university name (university) from TH_TO_EN_CANONICAL ("Sripatum University").
3. Sanitizing empty strings to None across all URL/email/name fields.
4. Sanitizing research interests: stripping nav boilerplate, slashes, trailing punctuation.
5. Standardizing publication shape to {"title", "year", "venue", "url", "citation_count"}.
6. PDPA freemail purge (only official institutional emails retained).
7. Cross-university email domain alignment using get_email_univ_safe.
8. Enforcing Bibliometric Monotonicity Invariant (total_publications_count >= h_index).
9. Deduplicating identical OpenAlex IDs within and across universities.
10. Exact & normalized Thai name deduplication within university.
11. Archiving merged secondary records to public.scholars_unassigned.
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


def resolve_wave80_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 80 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 0: Harmonize Course-to-Faculty Naming
        print("\n--- Step 0: Course-to-Faculty Harmonization ---", flush=True)

        # 0A: SPU Harmonization
        spu_courses = [
            ("มหาวิทยาลัยศรีปทุม", "วิทยาลัยนานาชาติศรีปทุม", "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ"),
            ("มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น", "บัณฑิตวิทยาลัย", "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ"),
        ]
        for u, old_f, new_f in spu_courses:
            courses = db.query(CourseDB).filter(CourseDB.university_th == u, CourseDB.faculty_th == old_f).all()
            for c in courses:
                c.faculty_th = new_f
            if courses:
                print(f'  [SPU Course Harmonization] [{u}] "{old_f}" -> "{new_f}" ({len(courses)} courses)')

        # 0B: MFU Harmonization (19 Graduate Courses)
        mfu_mappings = [
            ("เครื่องสำอาง", "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง"),
            ("สาธารณสุข", "สำนักวิชาวิทยาศาสตร์สุขภาพ"),
            ("การจัดการสุขภาพชายแดน", "สำนักวิชาวิทยาศาสตร์สุขภาพ"),
            ("กีฬาประยุกต์", "สำนักวิชาวิทยาศาสตร์สุขภาพ"),
            ("เวชศาสตร์ชะลอวัย", "สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ"),
            ("วิทยาศาสตร์ชะลอวัย", "สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ"),
            ("ตจวิทยา", "สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ"),
            ("เคมีประยุกต์", "สำนักวิชาวิทยาศาสตร์"),
            ("วิทยาศาสตร์ชีวภาพ", "สำนักวิชาวิทยาศาสตร์"),
            ("นวัตกรรมวัสดุ", "สำนักวิชาวิทยาศาสตร์"),
            ("สิ่งแวดล้อมอย่างยั่งยืน", "สำนักวิชาวิทยาศาสตร์"),
            ("วิศวกรรมคอมพิวเตอร์", "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์"),
            ("ดิจิทัล", "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์"),
            ("ภาษาอังกฤษ", "สำนักวิชาศิลปศาสตร์"),
            ("ชีวการแพทย์", "สำนักวิชาการแพทย์บูรณาการ"),
            ("อาหาร", "สำนักวิชาอุตสาหกรรมเกษตร"),
            ("หลังการเก็บเกี่ยว", "สำนักวิชาอุตสาหกรรมเกษตร"),
            ("การพัฒนาระหว่างประเทศ", "สำนักวิชานวัตกรรมสังคม"),
            ("โลจิสติกส์", "สำนักวิชาการจัดการ"),
        ]
        mfu_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง",
            CourseDB.faculty_th == "บัณฑิตวิทยาลัย",
        ).all()
        for c in mfu_courses:
            for kw, target_fac in mfu_mappings:
                if kw in c.title_th:
                    c.faculty_th = target_fac
                    print(f'  [MFU Course Harmonization] "{c.title_th}" -> "{target_fac}"')
                    break

        # 0C: Mahidol Harmonization (23 Graduate Courses)
        mu_mappings = [
            ("ออร์โธปิดิกส์", "คณะแพทยศาสตร์ศิริราชพยาบาล"),
            ("สิทธิมนุษยชน", "สถาบันสิทธิมนุษยชนและสันติศึกษา"),
            ("ประชากร", "สถาบันวิจัยประชากรและสังคม"),
            ("นวัตกรรมสังคม", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("การออกแบบและพัฒนาสังคม", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("สุขภาพและการพัฒนาที่ยั่งยืน", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("การประเมินโครงการทางสังคม", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("ศาสนาและจริยศาสตร์", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("อาชญาวิทยา", "คณะสังคมศาสตร์และมนุษยศาสตร์"),
            ("พหุวัฒนธรรม", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("พิพิธภัณฑศึกษา", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("อาเซียนศึกษา", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("ภาษาและการสื่อสาร", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("วัฒนธรรมศึกษา", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("ภาษาศาสตร์", "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย"),
            ("นวัตกรรมการเรียนรู้", "สถาบันนวัตกรรมการเรียนรู้"),
            ("คนพิการ", "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว"),
            ("ความต้องการพิเศษ", "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว"),
            ("อาหารและโภชนาการ", "สถาบันโภชนาการ"),
        ]
        mu_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยมหิดล",
            CourseDB.faculty_th == "บัณฑิตวิทยาลัย",
        ).all()
        for c in mu_courses:
            for kw, target_fac in mu_mappings:
                if kw in c.title_th:
                    c.faculty_th = target_fac
                    print(f'  [Mahidol Course Harmonization] "{c.title_th}" -> "{target_fac}"')
                    break

        # 0D: CMU Harmonization (14 Courses)
        cmu_mappings = [
            ("เทคโนโลยีชีวภาพ", "คณะอุตสาหกรรมเกษตร"),
            ("สุขภาพจิต", "คณะแพทยศาสตร์"),
            ("นิติวิทยาศาสตร์", "คณะแพทยศาสตร์"),
            ("วิทยาศาสตร์การกีฬา", "คณะศึกษาศาสตร์"),
            ("ภาษาจีนร่วมสมัย", "คณะมนุษยศาสตร์"),
            ("บูรณาการศาสตร์", "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี"),
            ("ทางทะเล", "คณะวิทยาศาสตร์"),
            ("บัณฑิตวิทยาลัย", "คณะวิทยาศาสตร์"),
        ]
        cmu_courses = db.query(CourseDB).filter(
            CourseDB.university_th == "มหาวิทยาลัยเชียงใหม่",
            CourseDB.faculty_th.in_(["วิทยาลัยพหุวิทยาการและสหวิทยาการ", "บัณฑิตวิทยาลัย", "วิทยาลัยการศึกษาและการจัดการทางทะเล"]),
        ).all()
        for c in cmu_courses:
            matched = False
            for kw, target_fac in cmu_mappings:
                if kw in c.title_th or kw in c.faculty_th:
                    c.faculty_th = target_fac
                    print(f'  [CMU Course Harmonization] "{c.title_th}" -> "{target_fac}"')
                    matched = True
                    break
            if not matched:
                c.faculty_th = "คณะวิทยาศาสตร์"

        db.commit()
        print("✅ Course harmonization completed.")

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

        db.commit()

        # Step 2: Clean anomalous entries, fix slashes in interests, and publication shape for Wave 80
        all_spu_records = db.query(FacultyDB).filter(FacultyDB.id.like("spu_%")).all()

        nav_boilerplate = ["วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา", "ค่าเทอม", "Office:", "Email:"]

        for f in all_spu_records:
            # Fix double title prefixes
            for prefix in ["ศ.เกียรติคุณ นพ.", "ศ.เกียรติคุณ", "ศ.ดร.นพ.", "ศ.ดร.พญ.", "ศ.ดร.", "รศ.ดร.นพ.", "รศ.ดร.พญ.", "รศ.ดร.", "ผศ.ดร.นพ.", "ผศ.ดร.พญ.", "ผศ.ดร.", "อ.ดร.นพ.", "อ.ดร.พญ.", "อ.ดร.", "ศ.นพ.", "ศ.พญ.", "รศ.นพ.", "รศ.พญ.", "ผศ.นพ.", "ผศ.พญ.", "อ.นพ.", "อ.พญ.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "พญ.", "นพ.", "อาจารย์"]:
                dbl = f"{prefix} {prefix}"
                if f.full_name_th and dbl in f.full_name_th:
                    f.full_name_th = f.full_name_th.replace(dbl, prefix)

            # Ensure last_name is clean and non-empty
            if f.first_name and not f.last_name:
                f.last_name = f.first_name

            # URL encode spaces in profile_url and image_url
            if f.image_url and " " in f.image_url:
                f.image_url = urllib.parse.quote(f.image_url, safe=":/%?=")
            if f.profile_url and " " in f.profile_url:
                f.profile_url = urllib.parse.quote(f.profile_url, safe=":/%?=")

            # Deduplicate research interests, split " / ", and strip punctuation & nav boilerplate
            if f.research_interests:
                seen_int = set()
                c_int = []
                for item in f.research_interests:
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
                        if k and k.lower() not in seen_int and len(k) > 1:
                            seen_int.add(k.lower())
                            c_int.append(k)
                f.research_interests = c_int

            # Standardize featured publications shape
            if f.featured_publications:
                clean_pubs = []
                for pub in f.featured_publications:
                    if isinstance(pub, dict) and pub.get("title"):
                        clean_pubs.append({
                            "title": pub["title"],
                            "year": pub.get("year"),
                            "venue": pub.get("venue"),
                            "url": pub.get("url") or pub.get("doi"),
                            "citation_count": pub.get("citation_count") or pub.get("citations") or 0,
                        })
                f.featured_publications = clean_pubs

        # PDPA freemail purge (only institutional emails retained)
        for dom in ["@yahoo.", "@gmail.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            for f in db.query(FacultyDB).filter(FacultyDB.email.like(f"%{dom}%")).all():
                f.email = None

        # Cross-university email domain alignment:
        facs_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        for f in facs_with_email:
            email_univ = get_email_univ_safe(f.email)
            if email_univ and email_univ != f.university_th:
                print(f"  [Email Realignment] Clearing conflicting foreign email '{f.email}' ({email_univ}) for '{f.full_name_th}' at '{f.university_th}'")
                f.email = None

        # Bibliometric Monotonicity Invariant: total_publications_count >= h_index
        monotonicity_violations = db.query(FacultyDB).filter(
            FacultyDB.h_index.isnot(None),
            FacultyDB.total_publications_count < FacultyDB.h_index,
        ).all()
        if monotonicity_violations:
            print(f"\n--- Enforcing Bibliometric Monotonicity ({len(monotonicity_violations)} records) ---", flush=True)
            for f in monotonicity_violations:
                f.total_publications_count = max(f.total_publications_count or 0, f.h_index or 0)

        db.commit()

        # Step 3: Deduplicate identical OpenAlex IDs
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

        # Step 4: Exact & normalized name duplicates within university
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

        # Step 5: Cross-university transfer realignment
        print(f"\n--- Checking Cross-University Transfer Realignment ---", flush=True)
        spu_thanyanan = db.query(FacultyDB).filter(FacultyDB.id == "spu_bus_0023").first()
        wu_thanyanan = db.query(FacultyDB).filter(FacultyDB.id == "wu_w51_0113_919").first()
        if spu_thanyanan and wu_thanyanan:
            print("  [Transfer Realignment] Thanyanan Sarachon transferred from Walailak to SPU Business.")
            # Merge metrics and archive WU ghost
            if wu_thanyanan.total_citations and wu_thanyanan.total_citations > (spu_thanyanan.total_citations or 0):
                spu_thanyanan.total_citations = wu_thanyanan.total_citations
            if wu_thanyanan.h_index and wu_thanyanan.h_index > (spu_thanyanan.h_index or 0):
                spu_thanyanan.h_index = wu_thanyanan.h_index
            if wu_thanyanan.openalex_id and wu_thanyanan.openalex_id != "not_indexed":
                spu_thanyanan.openalex_id = wu_thanyanan.openalex_id
            db.commit()

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'wu_w51_0113_919'
                        ON CONFLICT (id) DO UPDATE SET
                            total_citations = EXCLUDED.total_citations,
                            h_index = EXCLUDED.h_index;
                    """)
                )
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'wu_w51_0113_919'"))
            print("  ✅ Archived inactive Walailak ghost wu_w51_0113_919 to scholars_unassigned.")
            db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 80 duplicate resolution and course harmonization completed successfully!")


if __name__ == "__main__":
    resolve_wave80_duplicates()
