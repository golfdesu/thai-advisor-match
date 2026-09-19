# -*- coding: utf-8 -*-
"""
Phase 3 Deep Forensic Diagnostic Script.
Audits:
1. Embeddings completeness across Faculty, Course, and Lab.
2. PDPA phone numbers / personal contact leaks in education, research_interests, department.
3. Boilerplate / placeholder noise in research_interests, career_paths, curriculum_highlights.
4. Tuition fee outliers / corruption in courses.
5. Title mismatch between academic_title_th and full_name_th.
6. Research lab lead_advisor_id university mismatch.
7. Courses duplicate check within same university + degree + title.
8. Cross-university duplicate faculty (same person at 2 universities).
"""
import sys
import re
from pathlib import Path
from collections import defaultdict, Counter

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

def run_inspection():
    db = SessionLocal()
    print("=" * 70)
    print("🔬 PHASE 3 DEEP COMPREHENSIVE FORENSIC SCAN")
    print("=" * 70)

    faculties = db.query(FacultyDB).all()
    courses = db.query(CourseDB).all()
    labs = db.query(ResearchLabDB).all()

    print(f"Total: {len(faculties)} faculties, {len(courses)} courses, {len(labs)} labs\n")

    # 1. Embeddings & Embedding Text Completeness
    print("--- 1. EMBEDDINGS & EMBEDDING TEXT COMPLETENESS ---")
    fac_null_emb = sum(1 for f in faculties if f.embedding is None)
    fac_null_txt = sum(1 for f in faculties if not f.embedding_text or not f.embedding_text.strip())
    course_null_emb = sum(1 for c in courses if c.embedding is None)
    lab_null_emb = sum(1 for l in labs if l.embedding is None)
    print(f"Faculties missing embedding: {fac_null_emb}")
    print(f"Faculties missing embedding_text: {fac_null_txt}")
    print(f"Courses missing embedding: {course_null_emb}")
    print(f"Labs missing embedding: {lab_null_emb}")

    # 2. PDPA Compliance: Phone Numbers in Free-Text Fields
    print("\n--- 2. PDPA COMPLIANCE: PHONE NUMBERS IN FREE-TEXT FIELDS ---")
    # Strict Thai phone regex: 02-xxx-xxxx, 0xx-xxx-xxxx, +66...
    phone_pattern = re.compile(r"(?:(?:\+66|0)[2-9]\d{1}[- ]?\d{3}[- ]?\d{3,4}|(?:\+66|0)[689]\d{1}[- ]?\d{3}[- ]?\d{4})")
    phone_hits = []
    for f in faculties:
        for field_name, val_list in [("education", f.education or []), ("research_interests", f.research_interests or [])]:
            for item in val_list:
                m = phone_pattern.findall(item)
                if m:
                    phone_hits.append((f.id, f.full_name_th, field_name, m, item))
    print(f"PDPA phone number occurrences found: {len(phone_hits)}")
    for ph in phone_hits[:15]:
        print(f"   ⚠️ {ph[0]} ({ph[1]}): {ph[2]} contains phone {ph[3]} -> '{ph[4][:80]}'")

    # 3. Boilerplate / Junk in Faculty Fields
    print("\n--- 3. BOILERPLATE / JUNK IN FACULTY FIELDS ---")
    junk_patterns = [
        re.compile(r"^(ไม่มี|none|-|n/a|\.|null|undefined|\?)$", re.I),
        re.compile(r"^https?://", re.I),
        re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"), # email as interest
        re.compile(r"^(เบอร์โทร|โทรศัพท์|โทรสาร|\bfax\b|\btel\b|\broom\b|ห้องทำงาน)", re.I),
        re.compile(r"(คลิกที่นี่|ดาวน์โหลด|download)", re.I)
    ]
    junk_interests = []
    for f in faculties:
        if f.research_interests:
            for item in f.research_interests:
                clean_item = item.strip()
                for jp in junk_patterns:
                    if jp.search(clean_item):
                        junk_interests.append((f.id, f.full_name_th, clean_item))
                        break
    print(f"Junk items in research_interests: {len(junk_interests)}")
    for ji in junk_interests[:15]:
        print(f"   ⚠️ {ji[0]} ({ji[1]}): '{ji[2]}'")

    # Education boilerplate
    junk_edu = []
    for f in faculties:
        if f.education:
            for item in f.education:
                clean_item = item.strip()
                if len(clean_item) <= 2 or any(jp.search(clean_item) for jp in junk_patterns):
                    junk_edu.append((f.id, f.full_name_th, clean_item))
    print(f"Junk items in education: {len(junk_edu)}")
    for je in junk_edu[:15]:
        print(f"   ⚠️ {je[0]} ({je[1]}): '{je[2]}'")

    # 4. Academic Title vs Full Name Title Discrepancies
    print("\n--- 4. ACADEMIC TITLE VS FULL NAME TITLE DISCREPANCIES ---")
    title_mismatches = []
    for f in faculties:
        full = (f.full_name_th or "").strip()
        act = (f.academic_title_th or "").strip()
        if act and full:
            # Check if full_name_th starts with academic_title_th
            # normalize spaces
            act_n = re.sub(r"\s+", "", act)
            full_n = re.sub(r"\s+", "", full)
            if not full_n.startswith(act_n):
                # check if there is an obvious title mismatch
                # e.g. act says "ศ.ดร." but full starts with "รศ.ดร."
                title_mismatches.append((f.id, act, full))
    print(f"Title mismatches (academic_title_th not prefix of full_name_th): {len(title_mismatches)}")
    for tm in title_mismatches[:15]:
        print(f"   ⚠️ {tm[0]}: academic_title_th='{tm[1]}' vs full_name_th='{tm[2]}'")

    # 5. Faculty Image URL Anomalies
    print("\n--- 5. FACULTY IMAGE URL ANOMALIES ---")
    bad_img_urls = []
    for f in faculties:
        if f.image_url:
            url = f.image_url.strip()
            if not url.startswith("http") or any(x in url for x in ["localhost", "127.0.0.1", "spacer.gif", "blank.png", "default-avatar"]):
                bad_img_urls.append((f.id, f.full_name_th, url, f.university_th))
    print(f"Bad or placeholder image URLs: {len(bad_img_urls)}")
    for bi in bad_img_urls[:10]:
        print(f"   ⚠️ {bi[0]} ({bi[1]}, {bi[3]}): '{bi[2]}'")

    # 6. Courses: Tuition Fee Outliers & Formatting
    print("\n--- 6. COURSES: TUITION FEE OUTLIERS & FORMATTING ---")
    tuition_anomalies = []
    for c in courses:
        if c.tuition_per_semester is not None:
            raw_t = str(c.tuition_per_semester).strip()
            # extract numeric value
            nums = re.findall(r"[\d,]+", raw_t)
            if nums:
                val = float(nums[0].replace(",", ""))
                if val < 0 or val > 2_000_000:
                    tuition_anomalies.append((c.id, c.title_th, raw_t, val))
            elif raw_t not in ["-", "ไม่ระบุ", "ตามประกาศมหาวิทยาลัย", "ฟรี", "ไม่มีค่าใช้จ่าย"]:
                tuition_anomalies.append((c.id, c.title_th, raw_t, "non-numeric"))
    print(f"Tuition anomalies: {len(tuition_anomalies)}")
    for ta in tuition_anomalies[:10]:
        print(f"   ⚠️ {ta[0]} ('{ta[1]}'): tuition = {ta[2]} ({ta[3]})")

    # Courses career_paths and curriculum_highlights junk
    junk_course_fields = []
    for c in courses:
        for fname, flist in [("career_paths", c.career_paths or []), ("curriculum_highlights", c.curriculum_highlights or [])]:
            for item in flist:
                clean_item = str(item).strip()
                if len(clean_item) <= 2 or any(jp.search(clean_item) for jp in junk_patterns[:3]):
                    junk_course_fields.append((c.id, c.title_th, fname, clean_item))
    print(f"Junk items in course career_paths / highlights: {len(junk_course_fields)}")
    for jc in junk_course_fields[:10]:
        print(f"   ⚠️ {jc[0]} ('{jc[1]}'): {jc[2]} = '{jc[3]}'")

    # Courses title_th and title_en anomalies
    course_title_anomalies = []
    for c in courses:
        tth = (c.title_th or "").strip()
        ten = (c.title_en or "").strip()
        if not tth:
            course_title_anomalies.append((c.id, "missing title_th", tth, ten))
        elif re.search(r"^[a-zA-Z0-9\s.,()&/-]+$", tth) and len(tth) > 5:
            # title_th is pure English!
            course_title_anomalies.append((c.id, "title_th is pure English", tth, ten))
    print(f"Course title language anomalies: {len(course_title_anomalies)}")
    for cta in course_title_anomalies[:10]:
        print(f"   ⚠️ {cta[0]}: {cta[1]} -> th='{cta[2]}' | en='{cta[3]}'")

    # Duplicate courses
    course_dup_map = defaultdict(list)
    for c in courses:
        key = ((c.title_th or "").strip(), (c.university_th or "").strip(), (c.degree_level or "").strip(), (c.program_type or "").strip())
        course_dup_map[key].append(c)
    dup_courses = {k: v for k, v in course_dup_map.items() if len(v) > 1 and k[0]}
    print(f"Potential duplicate courses (same title, uni, degree, program_type): {len(dup_courses)}")
    for (tth, uni, deg, pt), clist in list(dup_courses.items())[:5]:
        print(f"   ⚠️ [{uni}] '{tth}' ({deg}, {pt}): {len(clist)} records ({', '.join(c.id for c in clist)})")

    # 7. Research Lab: Lead Advisor University Mismatch
    print("\n--- 7. RESEARCH LAB: LEAD ADVISOR UNIVERSITY MISMATCH ---")
    fac_uni_map = {f.id: f.university_th for f in faculties}
    lab_mismatches = []
    for l in labs:
        if l.lead_advisor_id and l.lead_advisor_id in fac_uni_map:
            adv_uni = fac_uni_map[l.lead_advisor_id]
            if adv_uni != l.university_th:
                lab_mismatches.append((l.id, l.name_th, l.university_th, l.lead_advisor_id, adv_uni))
    print(f"Labs with advisor at different university: {len(lab_mismatches)}")
    for lm in lab_mismatches:
        print(f"   ⚠️ Lab {lm[0]} ('{lm[1]}') at '{lm[2]}' has advisor {lm[3]} from '{lm[4]}'")

    # 8. Cross-University Duplicate Faculty (Same Person Scraped at Two Universities)
    print("\n--- 8. CROSS-UNIVERSITY DUPLICATE FACULTY ---")
    th_name_all = defaultdict(list)
    for f in faculties:
        th = f.full_name_th or ""
        th_clean = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|นพ|พญ|ทพ|ทพญ|สพ|ภก|ภญ|\.|\s)+", "", th).strip()
        th_clean = re.sub(r"\s+", "", th_clean)
        if len(th_clean) >= 6:
            th_name_all[th_clean].append(f)

    cross_uni_dups = []
    for name_clean, flist in th_name_all.items():
        unis = set(f.university_th for f in flist)
        if len(unis) > 1:
            # verify they have same English name or OpenAlex ID
            cross_uni_dups.append((name_clean, flist))

    print(f"Cross-university identical Thai names: {len(cross_uni_dups)}")
    for nc, flist in cross_uni_dups[:10]:
        print(f"   ⚠️ '{nc}':")
        for f in flist:
            print(f"      - {f.id} | {f.full_name_th} | {f.university_th} | {f.faculty_th} | OpenAlex: {f.openalex_id}")

    db.close()
    print("\n" + "=" * 70)
    print("🏁 PHASE 3 SCAN COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_inspection()
