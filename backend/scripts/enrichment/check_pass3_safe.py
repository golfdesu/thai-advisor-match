# -*- coding: utf-8 -*-
"""
Verify Pass 3 clusters with name-matching guard to prevent merging distinct individuals.
"""
import os
import sys
import re
from collections import defaultdict
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

GENERIC_USERS = {
    "info", "admin", "contact", "office", "dean", "sci", "dent", "med", "eng",
    "academic", "graduate", "service", "pr", "help", "hr", "reg", "library",
    "support", "webmaster", "postmaster", "director", "rector", "secretary"
}

RE_TITLE = re.compile(
    r"^(ศ\.เชี่ยวชาญพิเศษ\s+ดร\.\s+นพ\.|ศ\.คลินิก\s+ดร\.\s+สพ\.ญ\.|ศ\.คลินิก\s+ทพญ\.|"
    r"ศ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|ศ\.ดร\.ภก\.|ศ\.ดร\.ภญ\.|ศ\.ดร\.น\.สพ\.|ศ\.ดร\.สพ\.ญ\.|"
    r"รศ\.ดร\.นพ\.|รศ\.ดร\.พญ\.|รศ\.ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.น\.สพ\.|รศ\.ดร\.สพ\.ญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|"
    r"ผศ\.ดร\.นพ\.|ผศ\.ดร\.พญ\.|ผศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.น\.สพ\.|ผศ\.ดร\.สพ\.ญ\.|ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|"
    r"ศ\.นพ\.|ศ\.พญ\.|ศ\.ภก\.|ศ\.ภญ\.|ศ\.น\.สพ\.|ศ\.สพ\.ญ\.|ศ\.ทพ\.|ศ\.ทพญ\.|"
    r"รศ\.นพ\.|รศ\.พญ\.|รศ\.ภก\.|รศ\.ภญ\.|รศ\.น\.สพ\.|รศ\.สพ\.ญ\.|รศ\.ทพ\.|รศ\.ทพญ\.|"
    r"ผศ\.นพ\.|ผศ\.พญ\.|ผศ\.ภก\.|ผศ\.ภญ\.|ผศ\.น\.สพ\.|ผศ\.สพ\.ญ\.|ผศ\.ทพ\.|ผศ\.ทพญ\.|"
    r"อ\.นพ\.|อ\.พญ\.|อ\.ภก\.|อ\.ภญ\.|อ\.น\.สพ\.|อ\.สพ\.ญ\.|อ\.ทพ\.|อ\.ทพญ\.|"
    r"ศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+นพ\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\)|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*"
)

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

email_groups = defaultdict(list)
for f in faculties:
    if f.email and "@" in f.email:
        em = f.email.strip().lower()
        u = em.split("@")[0]
        if u not in GENERIC_USERS and len(u) >= 3:
            email_groups[em].append(f)

dup_emails = {k: v for k, v in email_groups.items() if len(v) > 1}

def get_bare_thai(name):
    if not name: return ""
    m = RE_TITLE.match(name)
    b = name[m.end():].strip() if m else name.strip()
    return re.sub(r"\s+", " ", b)

def get_clean_en(f):
    first = RE_EN_PREFIX.sub("", (f.first_name or "").strip()).strip()
    last = (f.last_name or "").strip()
    if first and last:
        return f"{first} {last}".lower()
    return ""

safe_merges = []
unsafe_diff_people = []

for em, cluster in dup_emails.items():
    # Test pairwise compatibility
    f1 = cluster[0]
    is_safe_cluster = True
    for f2 in cluster[1:]:
        t1 = get_bare_thai(f1.full_name_th)
        t2 = get_bare_thai(f2.full_name_th)
        e1 = get_clean_en(f1)
        e2 = get_clean_en(f2)

        has_thai_1 = bool(re.search(r"[฀-๿]", t1))
        has_thai_2 = bool(re.search(r"[฀-๿]", t2))

        match = False
        if has_thai_1 and has_thai_2:
            # Both have Thai names: check similarity
            ratio = fuzz.token_sort_ratio(t1, t2)
            if ratio >= 80:
                match = True
        elif e1 and e2:
            ratio_en = fuzz.token_sort_ratio(e1, e2)
            if ratio_en >= 80:
                match = True
        elif (not has_thai_1 and has_thai_2) or (has_thai_1 and not has_thai_2):
            # One is English, one is Thai: check if English name in f1/f2 matches
            # e.g. f1.first_name matches f2.first_name or transliteration
            if e1 and e2 and fuzz.token_sort_ratio(e1, e2) >= 70:
                match = True
            else:
                # Check if the English string in Thai field matches English name
                non_th = t1 if not has_thai_1 else t2
                en_target = e2 if not has_thai_1 else e1
                if non_th and en_target and fuzz.partial_ratio(non_th.lower(), en_target) >= 75:
                    match = True

        if not match:
            is_safe_cluster = False
            break

    if is_safe_cluster:
        safe_merges.append((em, cluster))
    else:
        unsafe_diff_people.append((em, cluster))

print(f"Total duplicate email clusters: {len(dup_emails)}")
print(f"Safe verified merges (same person): {len(safe_merges)}")
print(f"Unsafe (different persons sharing email): {len(unsafe_diff_people)}")

print("\n--- Unsafe examples (DO NOT MERGE - need investigation/email clearing) ---")
for em, cluster in unsafe_diff_people[:10]:
    print(f"\nEmail: {em}")
    for f in cluster:
        print(f"  {f.id} | {f.university_th} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | OA: {f.openalex_id}")

db.close()
