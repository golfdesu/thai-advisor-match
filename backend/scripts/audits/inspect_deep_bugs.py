# -*- coding: utf-8 -*-
"""
Deep bug & anomaly inspection script across database & domain logic.
"""
import sys
import re
from pathlib import Path
from collections import Counter

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
from scripts.audits.clean_and_deduplicate_database import is_shared_email

# Permit institutional subdomains (for example dept.university.ac.th),
# while requiring a letter-only TLD of at least two characters.
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
    r"\.[A-Za-z]{2,}$"
)

def run_deep_inspection():
    db = SessionLocal()
    print("=" * 70)
    print("🔍 RUNNING DEEP COMPREHENSIVE BUG & ANOMALY SCAN")
    print("=" * 70)

    faculties = db.query(FacultyDB).all()
    courses = db.query(CourseDB).all()
    labs = db.query(ResearchLabDB).all()

    print(f"Loaded: {len(faculties)} faculties, {len(courses)} courses, {len(labs)} labs\n")

    # --- 1. FACULTIES AUDIT ---
    print("--- 1. FACULTY AUDIT ---")

    # 1.1 OpenAlex Metrics Invariants
    impossible_metrics = []
    dup_openalex = {}
    for f in faculties:
        # h-index vs citations: h_index papers must each have >= h_index citations, so total_citations >= h^2
        # (unless h_index <= 1, e.g. h=1 requires >=1 citation)
        if f.h_index and f.total_citations is not None:
            if f.h_index > f.total_citations:
                impossible_metrics.append((f.id, f.full_name_th, f"h_index ({f.h_index}) > citations ({f.total_citations})"))
        if f.h_index and f.total_publications_count is not None:
            if f.h_index > f.total_publications_count:
                impossible_metrics.append((f.id, f.full_name_th, f"h_index ({f.h_index}) > publications ({f.total_publications_count})"))
        if (f.h_index or 0) < 0 or (f.total_citations or 0) < 0 or (f.total_publications_count or 0) < 0:
            impossible_metrics.append((f.id, f.full_name_th, "negative metric values"))

        if f.openalex_id and f.openalex_id != "not_indexed":
            dup_openalex.setdefault(f.openalex_id, []).append((f.id, f.full_name_th, f.university_th))

    print(f"[1.1] Impossible OpenAlex metrics: {len(impossible_metrics)}")
    for m in impossible_metrics[:10]:
        print(f"   ⚠️ {m[0]}: {m[1]} -> {m[2]}")

    dup_openalex_coll = {k: v for k, v in dup_openalex.items() if len(v) > 1}
    print(f"[1.2] Duplicate OpenAlex IDs across distinct faculty: {len(dup_openalex_coll)}")
    for oid, fac_list in list(dup_openalex_coll.items())[:10]:
        print(f"   ⚠️ OpenAlex ID {oid} shared by:")
        for fid, fn, uni in fac_list:
            print(f"      - {fid} | {fn} ({uni})")

    # 1.3 Publication title anomalies
    corrupt_pubs = []
    for f in faculties:
        if f.featured_publications:
            for idx, p in enumerate(f.featured_publications):
                t = p.get("title") if isinstance(p, dict) else str(p)
                t_str = str(t).strip() if t else ""
                if not t_str or len(t_str) <= 2 or t_str.lower() in ["-", "n/a", "none", "null", "."]:
                    corrupt_pubs.append((f.id, f.full_name_th, idx, t_str))
    print(f"[1.3] Corrupted publication titles: {len(corrupt_pubs)}")
    for cp in corrupt_pubs[:10]:
        print(f"   ⚠️ {cp[0]} ({cp[1]}): pub[{cp[2]}] = '{cp[3]}'")

    # 1.4 Email anomalies & duplicates
    invalid_emails = []
    email_users = {}
    for f in faculties:
        if f.email:
            em = f.email.strip()
            if not EMAIL_REGEX.match(em):
                invalid_emails.append((f.id, f.full_name_th, em))
            elif not is_shared_email(em):
                email_users.setdefault(em.lower(), []).append((f.id, f.full_name_th, f.university_th))

    print(f"[1.4] Invalid email formats: {len(invalid_emails)}")
    for ie in invalid_emails[:10]:
        print(f"   ⚠️ {ie[0]} ({ie[1]}): '{ie[2]}'")

    dup_emails = {k: v for k, v in email_users.items() if len(v) > 1}
    print(f"[1.5] Non-shared duplicate emails across records: {len(dup_emails)}")
    for em, fl in list(dup_emails.items())[:10]:
        print(f"   ⚠️ Email {em} shared by:")
        for fid, fn, uni in fl:
            print(f"      - {fid} | {fn} ({uni})")

    # 1.6 Names & Academic Titles anomalies
    strange_titles = Counter(f.academic_title_th for f in faculties if f.academic_title_th)
    print(f"[1.6] Academic titles distribution (total distinct: {len(strange_titles)})")
    # Check for strange patterns in titles
    odd_titles = [t for t in strange_titles if any(c in t for c in ["..", "  ", "(", ")", "/", "\\", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])]
    if odd_titles:
        print(f"   ⚠️ Potentially malformed titles: {odd_titles}")
    else:
        print("   ✅ All academic titles clean of numbers and bad punctuation.")

    # Check first_name / last_name containing academic titles
    name_with_title = []
    title_tokens_en = ["dr.", "dr", "prof.", "prof", "assoc.", "asst.", "ph.d.", "md", "m.d."]
    for f in faculties:
        fn_l = (f.first_name or "").lower().split()
        ln_l = (f.last_name or "").lower().split()
        if any(t in fn_l for t in title_tokens_en):
            name_with_title.append((f.id, "first_name", f.first_name, f.last_name))
        elif any(t in ln_l for t in title_tokens_en):
            name_with_title.append((f.id, "last_name", f.first_name, f.last_name))
    print(f"[1.7] English first/last names containing title prefixes: {len(name_with_title)}")
    for nwt in name_with_title[:10]:
        print(f"   ⚠️ {nwt[0]}: field '{nwt[1]}' has value '{nwt[2]} {nwt[3]}'")

    # Single character names
    single_char_names = []
    for f in faculties:
        if f.first_name and len(f.first_name.strip()) == 1:
            single_char_names.append((f.id, "first_name", f.first_name, f.last_name, f.full_name_th))
        if f.last_name and len(f.last_name.strip()) == 1:
            single_char_names.append((f.id, "last_name", f.first_name, f.last_name, f.full_name_th))
    print(f"[1.8] Single character first or last names: {len(single_char_names)}")
    for scn in single_char_names[:10]:
        print(f"   ⚠️ {scn[0]}: {scn[1]}='{scn[2]}' ({scn[3]}) -> {scn[4]}")

    # Check for HTML entities or unescaped tags in full_name_th, first_name, last_name
    html_in_names = []
    for f in faculties:
        for val, col in [(f.full_name_th, "full_name_th"), (f.first_name, "first_name"), (f.last_name, "last_name")]:
            if val and any(x in val for x in ["<", ">", "&nbsp;", "&amp;", "&quot;", "&#", "\t", "\n", "\r"]):
                html_in_names.append((f.id, col, val))
    print(f"[1.9] HTML tags, entities, or control characters in names: {len(html_in_names)}")
    for hin in html_in_names[:10]:
        print(f"   ⚠️ {hin[0]}: {hin[1]} = {repr(hin[2])}")

    # 1.10 Check potential duplicate faculty within same university
    norm_name_uni = {}
    for f in faculties:
        # clean Thai name
        clean_name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.|สพญ\.|ว่าที่ร้อยตรี|พ\.ต\.ท\.|พ\.ต\.อ\.|พ\.ต\.ต\.)\s*", "", (f.full_name_th or "").strip())
        clean_name = re.sub(r"^(ดร\.|พญ\.|นพ\.|ทญ\.|ทพ\.)\s*", "", clean_name).strip()
        if clean_name and len(clean_name) > 5:
            key = (clean_name, f.university_th)
            norm_name_uni.setdefault(key, []).append((f.id, f.full_name_th, f.email))

    intra_uni_dups = {k: v for k, v in norm_name_uni.items() if len(v) > 1}
    print(f"[1.10] Potential duplicate faculty within same university: {len(intra_uni_dups)}")
    for (cn, uni), fl in list(intra_uni_dups.items())[:10]:
        print(f"   ⚠️ '{cn}' at {uni}:")
        for fid, fn, em in fl:
            print(f"      - {fid} | {fn} | {em}")

    # --- 2. COURSES AUDIT ---
    print("\n--- 2. COURSES AUDIT ---")
    deg_levels = Counter(c.degree_level for c in courses)
    print(f"[2.1] Degree levels: {dict(deg_levels)}")

    prog_types = Counter(c.program_type for c in courses if c.program_type)
    print(f"[2.2] Program types: {dict(prog_types)}")

    # Credits anomalies
    credit_anomalies = []
    for c in courses:
        if c.total_credits is not None:
            try:
                # extract digits
                c_num = float(re.findall(r"[\d\.]+", str(c.total_credits))[0]) if re.findall(r"[\d\.]+", str(c.total_credits)) else None
                if c_num is not None and (c_num < 0 or c_num > 350):
                    credit_anomalies.append((c.id, c.title_th, c.total_credits))
            except Exception:
                pass
    print(f"[2.3] Credit anomalies (<0 or >350): {len(credit_anomalies)}")
    for ca in credit_anomalies[:10]:
        print(f"   ⚠️ {ca[0]}: '{ca[1]}' credits = {ca[2]}")

    # Duration anomalies
    duration_anomalies = []
    for c in courses:
        if c.duration_years:
            dur = c.duration_years.strip()
            # Expecting either 'X ปี' or 'ไม่ระบุ'
            if not (dur.endswith("ปี") or dur == "ไม่ระบุ"):
                duration_anomalies.append((c.id, c.title_th, dur))
    print(f"[2.4] Duration anomalies (not ending with 'ปี' or 'ไม่ระบุ'): {len(duration_anomalies)}")
    for da in duration_anomalies[:10]:
        print(f"   ⚠️ {da[0]}: '{da[1]}' duration = '{da[2]}'")

    # HTML in course titles
    html_in_courses = []
    for c in courses:
        for val, col in [(c.title_th, "title_th"), (c.title_en, "title_en")]:
            if val and any(x in val for x in ["<", ">", "&nbsp;", "&amp;", "&quot;", "&#", "\t", "\n", "\r"]):
                html_in_courses.append((c.id, col, val))
    print(f"[2.5] HTML tags or control chars in course titles: {len(html_in_courses)}")
    for hic in html_in_courses[:10]:
        print(f"   ⚠️ {hic[0]}: {hic[1]} = {repr(hic[2])}")

    # --- 3. RESEARCH LABS AUDIT ---
    print("\n--- 3. RESEARCH LABS AUDIT ---")
    dangling_labs = []
    fac_ids = set(f.id for f in faculties)
    for l in labs:
        if l.lead_advisor_id and l.lead_advisor_id not in fac_ids:
            dangling_labs.append((l.id, l.name_th, l.lead_advisor_id))
    print(f"[3.1] Research labs with dangling lead_advisor_id: {len(dangling_labs)}")
    for dl in dangling_labs:
        print(f"   ⚠️ Lab {dl[0]} ('{dl[1]}') points to missing advisor: {dl[2]}")

    # Empty names
    empty_lab_names = [l.id for l in labs if not l.name_th or not l.name_th.strip()]
    print(f"[3.2] Research labs with empty name_th: {len(empty_lab_names)}")

    db.close()
    print("\n" + "=" * 70)
    print("🏁 DEEP SCAN COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_deep_inspection()
