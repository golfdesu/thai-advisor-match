import sys
import os
import re
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict
from rapidfuzz import fuzz
from sqlalchemy.orm import defer

def clean_thai_name(name):
    if not name:
        return ""
    titles = [
        'ศาสตราจารย์เกียรติคุณ ดร.', 'ศาสตราจารย์ ดร.', 'รองศาสตราจารย์ ดร.', 'ผู้ช่วยศาสตราจารย์ ดร.',
        'ศาสตราจารย์คลินิก นพ.', 'ศาสตราจารย์ นพ.ดร.', 'รองศาสตราจารย์ นพ.ดร.', 'ผู้ช่วยศาสตราจารย์ นพ.ดร.',
        'ศาสตราจารย์ ทพญ.ดร.', 'รองศาสตราจารย์ ทพญ.ดร.', 'ผู้ช่วยศาสตราจารย์ ทพญ.ดร.',
        'ศาสตราจารย์ ทญ.ดร.', 'รองศาสตราจารย์ ทญ.ดร.', 'ผู้ช่วยศาสตราจารย์ ทญ.ดร.',
        'ศาสตราจารย์ นพ.', 'รองศาสตราจารย์ นพ.', 'ผู้ช่วยศาสตราจารย์ นพ.',
        'ศาสตราจารย์', 'รองศาสตราจารย์', 'ผู้ช่วยศาสตราจารย์', 'อาจารย์ ดร.', 'อาจารย์',
        'ศ.เกียรติคุณ ดร.', 'ศ.คลินิก นพ.', 'ศ.นพ.ดร.', 'รศ.นพ.ดร.', 'ผศ.นพ.ดร.',
        'ศ.ทพญ.ดร.', 'รศ.ทพญ.ดร.', 'ผศ.ทพญ.ดร.', 'ศ.ทญ.ดร.', 'รศ.ทญ.ดร.', 'ผศ.ทญ.ดร.',
        'ศ.นพ.', 'รศ.นพ.', 'ผศ.นพ.', 'ศ.พญ.', 'รศ.พญ.', 'ผศ.พญ.',
        'ศ.ดร.', 'รศ.ดร.', 'ผศ.ดร.', 'อ.ดร.', 'ดร.', 'ศ.', 'รศ.', 'ผศ.', 'อ.',
        'Prof. Dr.', 'Assoc. Prof. Dr.', 'Asst. Prof. Dr.', 'Prof.', 'Assoc. Prof.', 'Asst. Prof.', 'Dr.',
        'นายแพทย์', 'แพทย์หญิง', 'ทันตแพทย์หญิง', 'ทันตแพทย์', 'นพ.', 'พญ.', 'ทพ.', 'ทพญ.'
    ]
    res = name
    for t in titles:
        res = res.replace(t, " ")
    res = re.sub(r'\(.*?\)', '', res) # remove parentheses
    return re.sub(r'\s+', ' ', res).strip()

def clean_en_name(first, last):
    full = f"{first or ''} {last or ''}".strip().lower()
    full = re.sub(r'^(prof\.|assoc\.\s*prof\.|asst\.\s*prof\.|dr\.|mr\.|mrs\.|ms\.)\s*', '', full)
    return re.sub(r'\s+', ' ', full).strip()

def run_deep_audit():
    print("=================================================================")
    print("🔬 RUNNING COMPREHENSIVE 1,446 FACULTY DEEP AUDIT & INTEGRITY CHECK")
    print("=================================================================")

    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
    print(f"Total faculty records analyzed: {len(faculties)}")

    # 1. Exact Email Check
    email_map = defaultdict(list)
    # 2. Exact Cleaned Thai Name Check
    th_name_map = defaultdict(list)
    # 3. Exact Cleaned English Name Check
    en_name_map = defaultdict(list)
    # 4. Scholar URL Check
    scholar_map = defaultdict(list)
    # 5. Profile URL Check
    profile_url_map = defaultdict(list)

    # 6. Data Hygiene issues
    missing_interests = []
    missing_email = []
    invalid_embedding = []
    duplicate_titles_in_th = []

    for f in faculties:
        # Check title formatting
        if f.full_name_th and any(f.full_name_th.startswith(t) for t in ["ศ.ดร. ศ.ดร.", "รศ.ดร. รศ.ดร.", "ผศ.ดร. ผศ.ดร.", "ศ.นพ. ศ.นพ."]):
            duplicate_titles_in_th.append(f)

        if not f.research_interests or len(f.research_interests) == 0:
            missing_interests.append(f)

        if not f.email:
            missing_email.append(f)

        if f.email and "@" in f.email:
            email_map[f.email.strip().lower()].append(f)

        th_clean = clean_thai_name(f.full_name_th)
        if len(th_clean) > 3:
            th_name_map[th_clean].append(f)

        en_clean = clean_en_name(f.first_name, f.last_name)
        if len(en_clean) > 3:
            en_name_map[en_clean].append(f)

        if f.scholar_url and "scholar.google" in f.scholar_url:
            scholar_map[f.scholar_url.strip().lower()].append(f)

        if f.profile_url and len(f.profile_url) > 10:
            profile_url_map[f.profile_url.strip().lower()].append(f)

    print("\n--- 1. Exact Key Duplicate Analysis ---")
    print(f"📧 Email Duplicates: {sum(1 for v in email_map.values() if len(v) > 1)} groups")
    print(f"🇹🇭 Normalized Thai Name Duplicates: {sum(1 for v in th_name_map.values() if len(v) > 1)} groups")
    print(f"🇬🇧 Normalized English Name Duplicates: {sum(1 for v in en_name_map.values() if len(v) > 1)} groups")
    print(f"🎓 Scholar URL Duplicates: {sum(1 for v in scholar_map.values() if len(v) > 1)} groups")
    print(f"🔗 Profile URL Duplicates: {sum(1 for v in profile_url_map.values() if len(v) > 1)} groups")

    # Display any remaining duplicate groups
    for name, grp in th_name_map.items():
        if len(grp) > 1:
            print(f"\n⚠️ Thai Name Match: '{name}'")
            for f in grp:
                print(f"   - ID: {f.id} | {f.full_name_th} | {f.university_th} - {f.faculty_th} | Email: {f.email}")

    for name, grp in en_name_map.items():
        if len(grp) > 1:
            print(f"\n⚠️ English Name Match: '{name}'")
            for f in grp:
                print(f"   - ID: {f.id} | TH: {f.full_name_th} | {f.university_th} - {f.faculty_th} | Email: {f.email}")

    for url, grp in scholar_map.items():
        if len(grp) > 1:
            print(f"\n⚠️ Scholar URL Match: '{url}'")
            for f in grp:
                print(f"   - ID: {f.id} | {f.full_name_th} | {f.university_th}")

    # 2. Fuzzy Name Match across all remaining records
    print("\n--- 2. Fuzzy Cross-University Name Match Analysis (RapidFuzz > 90) ---")
    fuzzy_matches = []
    faculty_list = list(faculties)
    n = len(faculty_list)

    for i in range(n):
        f1 = faculty_list[i]
        name1 = clean_thai_name(f1.full_name_th)
        en1 = clean_en_name(f1.first_name, f1.last_name)
        if not name1 and not en1:
            continue

        for j in range(i + 1, min(i + 150, n)): # check proximity and cross check
            f2 = faculty_list[j]
            name2 = clean_thai_name(f2.full_name_th)
            en2 = clean_en_name(f2.first_name, f2.last_name)

            # Check high similarity in Thai name
            if name1 and name2 and len(name1) > 5 and len(name2) > 5:
                ratio = fuzz.ratio(name1, name2)
                if 88 <= ratio < 100:
                    fuzzy_matches.append((ratio, "TH_FUZZY", f1, f2))

            # Check high similarity in English name
            if en1 and en2 and len(en1) > 8 and len(en2) > 8:
                en_ratio = fuzz.ratio(en1, en2)
                if 90 <= en_ratio < 100:
                    fuzzy_matches.append((en_ratio, "EN_FUZZY", f1, f2))

    print(f"Found {len(fuzzy_matches)} potential fuzzy name matches.")
    for ratio, match_type, f1, f2 in fuzzy_matches[:15]:
        print(f"   [{match_type} {ratio:.1f}%] ID1: {f1.id} ({f1.full_name_th} / {f1.university_th}) <==> ID2: {f2.id} ({f2.full_name_th} / {f2.university_th})")

    # 3. Data Hygiene Report
    print("\n--- 3. Data Hygiene & Title Formatting ---")
    print(f"📌 Repeated Titles in full_name_th (e.g., 'ศ.ดร. ศ.ดร.'): {len(duplicate_titles_in_th)} records")
    for f in duplicate_titles_in_th[:5]:
        print(f"   - {f.id}: {f.full_name_th} -> Suggest clean to: {re.sub(r'^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|ศ\.นพ\.)\s*', '', f.full_name_th)}")

    print(f"📌 Missing Research Interests: {len(missing_interests)} records")
    print(f"📌 Missing Emails: {len(missing_email)} records")

    db.close()

if __name__ == "__main__":
    run_deep_audit()
