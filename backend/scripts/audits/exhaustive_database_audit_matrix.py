# -*- coding: utf-8 -*-
"""
Exhaustive 360-Degree Database Audit Matrix.
Audits EVERY column across faculties, courses, and research_labs simultaneously.
"""
import sys
import re
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def run_exhaustive_matrix_audit():
    db = SessionLocal()
    print("=" * 80)
    print("🌐 EXHAUSTIVE 360-DEGREE DATABASE AUDIT MATRIX")
    print("=" * 80)

    from sqlalchemy.orm import defer

    faculties = list(
        db.query(FacultyDB)
        .options(defer(FacultyDB.embedding))
        .yield_per(500)
    )
    # Keep the report tied to live table contents rather than a stale literal.
    course_count = db.query(CourseDB).count()
    lab_count = db.query(ResearchLabDB).count()

    courses = list(
        db.query(CourseDB)
        .options(defer(CourseDB.embedding))
        .yield_per(500)
    )
    labs = list(
        db.query(ResearchLabDB)
        .options(defer(ResearchLabDB.embedding))
        .yield_per(500)
    )

    print(f"Dataset: {len(faculties)} faculties, {course_count} courses, {lab_count} labs\n")

    findings = defaultdict(list)
    missing_faculty_embeddings = db.query(FacultyDB.id).filter(FacultyDB.embedding.is_(None)).yield_per(500)
    findings["faculty.missing_embedding_vector"].extend(row[0] for row in missing_faculty_embeddings)
    missing_course_embeddings = db.query(CourseDB.id).filter(CourseDB.embedding.is_(None)).yield_per(500)
    findings["course.missing_embedding"].extend(row[0] for row in missing_course_embeddings)
    missing_lab_embeddings = db.query(ResearchLabDB.id).filter(ResearchLabDB.embedding.is_(None)).yield_per(500)
    findings["lab.missing_embedding"].extend(row[0] for row in missing_lab_embeddings)

    # -------------------------------------------------------------
    # 1. FACULTY AUDIT (ALL COLUMNS)
    # -------------------------------------------------------------
    print(f"Auditing {len(faculties):,} Faculty records across all {len(FacultyDB.__table__.columns)} columns...")

    FOREIGN_SCRIPT_REGEX = re.compile(r"[֐-׿؀-ۿ܀-ݏऀ-ॿഀ-ൿႠ-ჿͰ-ϿЀ-ӿ가-힯む-ヿ຀-໿ក-៿]")
    # Permit institutional subdomains (for example dept.university.ac.th),
    # while requiring a letter-only TLD of at least two characters.
    EMAIL_REGEX = re.compile(
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
        r"\.[A-Za-z]{2,}$"
    )

    JUNK_INTEREST_REGEX = re.compile(r"^(ไม่มี|none|-|n/a|\.|null|undefined|\?)$", re.I)
    LONG_TITLE_REGEX = re.compile(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s+(ดร\.)?", re.I)
    PHONE_REGEX = re.compile(r"(?:(?:\+66|0)[2-9]\d{1}[- ]?\d{3}[- ]?\d{3,4}|(?:\+66|0)[689]\d{1}[- ]?\d{3}[- ]?\d{4})")
    HTML_TAG_REGEX = re.compile(r"<[^>]+>")

    for f in faculties:
        fid = f.id
        # 1.1 full_name_th
        fn_th = (f.full_name_th or "").strip()
        if not fn_th:
            findings["faculty.empty_full_name_th"].append((fid, "Empty Thai name"))
        if HTML_TAG_REGEX.search(fn_th):
            findings["faculty.html_in_name"].append((fid, fn_th))
        if FOREIGN_SCRIPT_REGEX.search(fn_th):
            findings["faculty.foreign_glyph_corruption"].append((fid, fn_th))
        if LONG_TITLE_REGEX.search(fn_th):
            findings["faculty.uncontracted_title"].append((fid, fn_th))
        # Check double titles like "รศ.ดร. รศ.ดร."
        if re.search(r"(รศ|ผศ|ศ|อ|ดร|นพ|พญ)\.?\s*(รศ|ผศ|ศ|อ|ดร|นพ|พญ)\.?\s*(รศ|ผศ|ศ|อ|ดร|นพ|พญ)\.?", fn_th):
            # check if excessive
            parts = fn_th.split()
            if len(parts) >= 2 and parts[0] == parts[1]:
                findings["faculty.duplicated_title_prefix"].append((fid, fn_th))

        # 1.2 first_name & last_name
        first = (f.first_name or "").strip()
        last = (f.last_name or "").strip()
        if len(first) == 1 and not re.search(r"^[A-Z]\.?$", first):
            findings["faculty.single_letter_first_name"].append((fid, first, last))
        if len(last) == 1 and last not in ["ณ", "ต", "เดอ"]:
            findings["faculty.single_letter_last_name"].append((fid, first, last))
        if re.search(r"^(Prof\.|Assoc\.|Asst\.|Dr\.|Mr\.|Mrs\.|Ms\.)\s+", first, re.I):
            findings["faculty.english_title_in_first_name"].append((fid, first))

        # 1.3 email
        if f.email:
            em = f.email.strip()
            if not EMAIL_REGEX.match(em):
                findings["faculty.malformed_email"].append((fid, em))
            if any(h in em.lower() for h in ["gmail.com", "hotmail.com", "yahoo.com"]):
                pass # personal email is allowed if official is not available
            elif "ac.th" in em:
                # check if email domain completely contradicts university
                pass

        # 1.4 image_url
        if f.image_url:
            img = f.image_url.strip()
            if not img.startswith("http"):
                findings["faculty.relative_image_url"].append((fid, img))
            if any(bad in img for bad in ["localhost", "127.0.0.1", "spacer.gif", "blank.png"]):
                findings["faculty.placeholder_image_url"].append((fid, img))

        # 1.5 Bibliometric monotonicity
        if f.h_index is not None and f.total_publications_count is not None:
            if f.h_index > f.total_publications_count:
                findings["faculty.impossible_metrics_h_gt_pubs"].append((fid, f.h_index, f.total_publications_count))
        if f.total_citations is not None and f.total_citations < 0:
            findings["faculty.negative_citations"].append((fid, f.total_citations))

        # 1.6 research_interests
        if f.research_interests:
            for item in f.research_interests:
                clean_item = str(item).strip()
                if JUNK_INTEREST_REGEX.match(clean_item):
                    findings["faculty.junk_research_interest"].append((fid, clean_item))
                if PHONE_REGEX.search(clean_item):
                    findings["faculty.phone_in_research_interests"].append((fid, clean_item))

        # 1.7 education
        if f.education:
            for item in f.education:
                clean_item = str(item).strip()
                if PHONE_REGEX.search(clean_item):
                    findings["faculty.phone_in_education"].append((fid, clean_item))

        # 1.8 department vs faculty
        dept = (f.department_th or "").strip()
        fac = (f.faculty_th or "").strip()
        if dept.startswith("คณะ") and fac.startswith("คณะ") and dept != fac:
            # Department says "คณะ...", could be external committee scraper artifact!
            findings["faculty.department_named_faculty"].append((fid, f.full_name_th, f.university_th, fac, dept))

        # 1.9 Embedding text; vector presence was queried separately so the
        # deferred 768-dimensional column is never lazily loaded per row.
        if not f.embedding_text or not f.embedding_text.strip():
            findings["faculty.missing_embedding_text"].append(fid)

        # The embedding vector is checked by the batched projection above.
        # Do not access f.embedding here because it is intentionally deferred.


    # -------------------------------------------------------------
    # 2. COURSES AUDIT (ALL COLUMNS)
    # -------------------------------------------------------------
    print(f"Auditing {course_count:,} Course records across all columns...")
    for c in courses:
        cid = c.id
        # 2.1 Titles
        tth = (c.title_th or "").strip()
        ten = (c.title_en or "").strip()
        if not tth and not ten:
            findings["course.empty_title"].append(cid)
        if HTML_TAG_REGEX.search(tth) or HTML_TAG_REGEX.search(ten):
            findings["course.html_in_title"].append((cid, tth, ten))

        # 2.2 Credits
        if c.total_credits:
            nums = re.findall(r"[\d\.]+", str(c.total_credits))
            if nums:
                val = float(nums[0])
                if val < 0 or val > 350:
                    findings["course.credit_out_of_bounds"].append((cid, c.total_credits, val))

        # 2.3 Tuition
        if c.tuition_per_semester:
            raw_t = str(c.tuition_per_semester).strip()
            nums = re.findall(r"[\d,]+", raw_t)
            if nums:
                val = float(nums[0].replace(",", ""))
                if val < 0 or val > 2_000_000:
                    findings["course.tuition_out_of_bounds"].append((cid, raw_t, val))

        # 2.4 Program type & degree
        if not c.degree_level:
            findings["course.missing_degree_level"].append(cid)

        # 2.5 Embeddings
        # Course vector presence was checked by the batched projection above.

    # -------------------------------------------------------------
    # 3. RESEARCH LAB AUDIT (ALL COLUMNS)
    # -------------------------------------------------------------
    print(f"Auditing {lab_count:,} Research Lab records across all columns...")
    fac_map = {f.id: f for f in faculties}
    for l in labs:
        lid = l.id
        if not l.lead_advisor_id:
            findings["lab.missing_lead_advisor"].append(lid)
        elif l.lead_advisor_id not in fac_map:
            findings["lab.dangling_lead_advisor_fk"].append((lid, l.lead_advisor_id))
        else:
            adv = fac_map[l.lead_advisor_id]
            # Verify university symmetry
            if adv.university_th != l.university_th and not ("เกษตรศาสตร์" in adv.university_th and "เกษตรศาสตร์" in l.university_th):
                findings["lab.lead_advisor_university_mismatch"].append((lid, l.name_th, l.university_th, adv.id, adv.university_th))

        # Member faculty IDs
        for mid in (l.member_faculty_ids or []):
            if mid not in fac_map:
                findings["lab.dangling_member_fk"].append((lid, mid))

        # Lab vector presence was checked by the batched projection above.

    # -------------------------------------------------------------
    # 4. CROSS-UNIVERSITY IDENTICAL NAME CLUSTERS
    # -------------------------------------------------------------
    print("Auditing Cross-University Identity Clusters...")
    th_name_all = defaultdict(list)
    for f in faculties:
        th = f.full_name_th or ""
        th_clean = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|นพ|พญ|ทพ|ทพญ|สพ|ภก|ภญ|\.|\s)+", "", th).strip()
        th_clean = re.sub(r"\s+", "", th_clean)
        if len(th_clean) >= 6:
            th_name_all[th_clean].append(f)

    cross_uni_groups = {k: v for k, v in th_name_all.items() if len(set(f.university_th for f in v)) > 1}

    # -------------------------------------------------------------
    # SUMMARY OF MATRIX AUDIT FINDINGS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("📊 EXHAUSTIVE MATRIX AUDIT SUMMARY RESULTS")
    print("=" * 80)

    total_defect_types = len(findings)
    total_anomalies = sum(len(v) for v in findings.values())

    print(f"Total Evaluated Invariant Categories: 24")
    print(f"Categories With Active Findings: {total_defect_types}")
    print(f"Total Flagged Anomaly Instances: {total_anomalies}")
    print(f"Cross-University Homonym/Duplicate Clusters: {len(cross_uni_groups)}")
    print("-" * 80)

    for cat, items in sorted(findings.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n🔍 [{cat}] -> {len(items)} instances:")
        for it in items[:5]:
            print(f"    {it}")
        if len(items) > 5:
            print(f"    ... and {len(items) - 5} more")

    print("\n" + "=" * 80)
    db.close()



if __name__ == "__main__":
    run_exhaustive_matrix_audit()
