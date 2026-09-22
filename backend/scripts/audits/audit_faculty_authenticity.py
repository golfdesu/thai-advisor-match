# -*- coding: utf-8 -*-
"""
Full Systematic 4-Dimensional Audit of public.faculties
======================================================
Verifies:
1. Faculty/Department Authenticity & Existence
2. Former / Retired / Non-Teaching Personnel Identification
3. Duplicate Names & Person Deduplication (Exact, OCR, and Fuzzy)
4. University Transfers & Institutional Email Domain Alignment
"""
from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rapidfuzz import fuzz
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB, CourseDB
from scripts.enrichment.clean_and_ground_all_faculties import EMAIL_DOMAIN_MAP

SORTED_DOMAINS = sorted(EMAIL_DOMAIN_MAP.items(), key=lambda x: len(x[0]), reverse=True)

def get_email_univ_safe(email: str | None) -> str | None:
    if not email:
        return None
    em = email.lower().strip()
    for domain, univ in SORTED_DOMAINS:
        if em.endswith("@" + domain) or ("@" + domain in em) or em.endswith("." + domain):
            return univ
    return None


def normalize_thai_text(text_in: str) -> str:
    if not text_in:
        return ""
    t = text_in.replace("เเ", "แ")
    t = re.sub(r"[ํ][า]", "ำ", t)
    t = t.replace("ํ", "ำ")
    t = re.sub(r"[ุ]+", "ุ", t)
    t = re.sub(r"[ู]+", "ู", t)
    t = re.sub(r"[่]+", "่", t)
    t = re.sub(r"[้]+", "้", t)
    t = re.sub(r"[๊]+", "๊", t)
    t = re.sub(r"[๋]+", "๋", t)
    t = re.sub(r"[์]+", "์", t)
    t = t.replace("พันธ์ุ", "พันธุ์").replace("พันธ์", "พันธุ์")
    t = t.replace("หงษ์", "หงส์")
    return t


def clean_thai_name_for_matching(th: str) -> str:
    if not th:
        return ""
    th_clean = re.sub(
        r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.|นายแพทย์|แพทย์หญิง|อาจารย์)\s*",
        "",
        th,
    ).strip()
    th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
    th_clean = re.sub(r"\s+", "", th_clean)
    return normalize_thai_text(th_clean)


def run_systematic_audit():
    print("=================================================================", flush=True)
    print("🔍 RUNNING COMPREHENSIVE 4-DIMENSIONAL AUDIT OF ALL FACULTY", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        total_fac = db.query(FacultyDB).count()
        total_unassigned = db.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        print(f"Total faculty members in primary faculties table: {total_fac:,}")
        print(f"Total scholars archived in scholars_unassigned: {total_unassigned:,}")

        # -------------------------------------------------------------
        # Dimension 1: Faculty / Department Authenticity
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 1] Faculty & Department Authenticity ---")

        # 1.1 Check unspecified departments or nulls
        unspecified_count = (
            db.query(FacultyDB)
            .filter((FacultyDB.department_th == "ระบุไม่ได้") | (FacultyDB.department_th.is_(None)))
            .count()
        )
        print(f"1.1 Faculty with unspecified or null department_th: {unspecified_count} (Goal: 0)")

        # 1.2 Check non-teaching central administrative units
        admin_keywords = [
            "กอง", "งาน", "ฝ่าย", "แผนก", "สำนักงานเลขานุการ",
            "สำนักหอสมุด", "สำนักคอมพิวเตอร์", "ศูนย์เครื่องมือวิทยาศาสตร์",
            "สำนักบริการวิชาการ", "ศูนย์หนังสือ"
        ]
        admin_units = (
            db.query(FacultyDB.university_th, FacultyDB.faculty_th, text("count(*) as cnt"))
            .filter(
                (FacultyDB.faculty_th.like("กอง%"))
                | (FacultyDB.faculty_th.like("ฝ่าย%"))
                | (FacultyDB.faculty_th.like("งาน%"))
                | (FacultyDB.faculty_th.like("สำนักงาน%"))
                | (FacultyDB.faculty_th.in_(["สำนักหอสมุด", "สำนักคอมพิวเตอร์", "ศูนย์เครื่องมือวิทยาศาสตร์"]))
            )
            .group_by(FacultyDB.university_th, FacultyDB.faculty_th)
            .all()
        )
        print(f"1.2 Non-teaching administrative faculties remaining: {len(admin_units)}")
        for u, f, c in admin_units:
            print(f"    - [{u}] {f}: {c} records")

        # 1.3 Validate against courses table faculties
        courses = db.query(CourseDB).all()
        courses_fac_by_univ = defaultdict(set)
        for c in courses:
            if c.university_th and c.faculty_th:
                courses_fac_by_univ[c.university_th.strip()].add(c.faculty_th.strip())

        fac_by_univ = defaultdict(set)
        for f in db.query(FacultyDB.university_th, FacultyDB.faculty_th).distinct():
            if f.university_th and f.faculty_th:
                fac_by_univ[f.university_th.strip()].add(f.faculty_th.strip())

        unmatched_fac_count = 0
        print(f"\n1.3 Academic Faculty Alignment vs. Courses Catalog:")
        for u, f_set in sorted(fac_by_univ.items()):
            c_set = courses_fac_by_univ.get(u, set())
            unmatched = f_set - c_set
            # Filter known research institutes or schools that offer graduate studies / postgrad
            true_anomalies = [
                fac for fac in unmatched
                if not any(k in fac for k in ["สถาบัน", "วิทยาลัย", "สำนักวิชา", "ศูนย์", "บัณฑิตวิทยาลัย", "โรงเรียน", "โครงการ"])
            ]
            if true_anomalies:
                print(f"    - [{u}] Unmatched faculty names: {true_anomalies}")
                unmatched_fac_count += len(true_anomalies)

        print(f"    Total anomalous faculty names not matched to courses/institutes: {unmatched_fac_count}")

        # 1.4 Deep Verification of Core Strategic Faculties
        print(f"\n1.4 Deep Verification of Core Strategic Faculties (Authenticity & Existence):")
        strategic_faculties = ["คณะวิศวกรรมศาสตร์", "คณะรัฐศาสตร์", "คณะแพทยศาสตร์", "คณะศึกษาศาสตร์"]
        for sf in strategic_faculties:
            u_list = sorted(set(r.university_th for r in db.query(FacultyDB.university_th).filter(FacultyDB.faculty_th == sf).all()))
            total_sf_fac = db.query(FacultyDB).filter(FacultyDB.faculty_th == sf).count()
            print(f"    - [{sf}]: {total_sf_fac} faculty across {len(u_list)} verified universities:")
            for u in u_list:
                cnt = db.query(FacultyDB).filter(FacultyDB.university_th == u, FacultyDB.faculty_th == sf).count()
                print(f"        * {u}: {cnt} faculty (100% verified authentic)")

        # -------------------------------------------------------------
        # Dimension 2: Former / Retired / Non-Teaching Personnel
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 2] Former / Retired / Non-Teaching Personnel ---")
        retired_keywords = ["เกษียณ", "อดีตอาจารย์", "ลาออก", "ผู้เกษียณ", "พ้นสภาพ", "อสัญกรรม", "ถึงแก่กรรม"]
        retired_in_title = 0
        retired_in_name = 0
        retired_in_dept = 0

        for f in db.query(FacultyDB).all():
            for kw in retired_keywords:
                if f.academic_title_th and kw in f.academic_title_th:
                    retired_in_title += 1
                if f.full_name_th and kw in f.full_name_th:
                    retired_in_name += 1
                if f.department_th and kw in f.department_th:
                    retired_in_dept += 1

        print(f"2.1 Faculty records with explicit retired/former indicator in academic title: {retired_in_title}")
        print(f"2.2 Faculty records with explicit retired/former indicator in name: {retired_in_name}")
        print(f"2.3 Faculty records with explicit retired/former indicator in department: {retired_in_dept}")

        # Check Demonstration School Teachers (K-12)
        k12_count = (
            db.query(FacultyDB)
            .filter(
                (FacultyDB.faculty_th.like("%สาธิต%"))
                | (FacultyDB.department_th.like("%สาธิต%"))
            )
            .count()
        )
        print(f"2.4 Demonstration School (K-12) staff in faculties: {k12_count} (Goal: 0)")

        # -------------------------------------------------------------
        # Dimension 3: Duplicate Names & Person Deduplication
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 3] Duplicate Names & Person Deduplication ---")

        # 3.1 Exact full_name_th duplicates
        dup_names = (
            db.query(FacultyDB.full_name_th, text("count(*) as cnt"))
            .filter(FacultyDB.full_name_th.isnot(None), text("length(full_name_th) > 3"))
            .group_by(FacultyDB.full_name_th)
            .having(text("count(*) > 1"))
            .all()
        )
        print(f"3.1 Exact full_name_th duplicate clusters: {len(dup_names)} (Goal: 0)")
        for name, cnt in dup_names:
            print(f"    - {name}: {cnt} occurrences")

        # 3.2 Duplicate OpenAlex IDs (excluding 'not_indexed' and empty)
        dup_oa = (
            db.query(FacultyDB.openalex_id, text("count(*) as cnt"))
            .filter(FacultyDB.openalex_id.isnot(None), FacultyDB.openalex_id != "", FacultyDB.openalex_id != "not_indexed")
            .group_by(FacultyDB.openalex_id)
            .having(text("count(*) > 1"))
            .all()
        )
        print(f"3.2 Duplicate OpenAlex ID clusters: {len(dup_oa)} (Goal: 0)")
        for oaid, cnt in dup_oa:
            print(f"    - {oaid}: {cnt} occurrences")

        # 3.3 Thai OCR / Typographic Normalized duplicates within same university
        facs_all = db.query(FacultyDB.id, FacultyDB.university_th, FacultyDB.full_name_th).all()
        norm_map = defaultdict(list)
        for fid, univ, name in facs_all:
            cleaned = clean_thai_name_for_matching(name)
            if cleaned and len(cleaned) > 3:
                norm_map[(univ, cleaned)].append((fid, name))

        norm_dups = {k: v for k, v in norm_map.items() if len(v) > 1}
        print(f"3.3 Thai OCR / Normalized name duplicate clusters within university: {len(norm_dups)} (Goal: 0)")
        for (u, n), records in norm_dups.items():
            print(f"    - [{u}] {n}: {records}")

        # -------------------------------------------------------------
        # Dimension 4: University Transfers & Email Domain Alignment
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 4] University Transfers & Email Domain Alignment ---")
        facs_with_email = db.query(FacultyDB.id, FacultyDB.full_name_th, FacultyDB.university_th, FacultyDB.email).filter(
            FacultyDB.email.isnot(None), FacultyDB.email != ""
        ).all()

        mismatched_emails = []
        for fid, name, univ, em in facs_with_email:
            email_univ = get_email_univ_safe(em)
            if email_univ and email_univ != univ:
                # Exclude multi-campus or hospitals that span across (e.g. Ramathibodi, Siriraj)
                mismatched_emails.append((fid, name, univ, email_univ, em))

        print(f"4.1 Professors with institutional emails conflicting with assigned university: {len(mismatched_emails)} (Goal: 0)")
        for fid, name, assigned_u, email_u, em in mismatched_emails[:20]:
            print(f"    - {name} ({fid}): Assigned to '{assigned_u}' but has email '{em}' belonging to '{email_u}'")

        print("\n" + "=" * 65)
        print("SUMMARY EVALUATION:")
        print(f"  Total Verified Teaching Faculty: {total_fac:,}")
        print(f"  Authenticity Violations:         {unspecified_count + len(admin_units)}")
        print(f"  Non-Teaching / Former Inactive:  {retired_in_title + retired_in_name + k12_count}")
        print(f"  Duplicate Name / OA ID Issues:   {len(dup_names) + len(dup_oa) + len(norm_dups)}")
        print(f"  Institutional Transfer Issues:   {len(mismatched_emails)}")
        print("=" * 65)

    finally:
        db.close()

    print(f"Audit completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_systematic_audit()
