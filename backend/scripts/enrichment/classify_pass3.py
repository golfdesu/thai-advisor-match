# -*- coding: utf-8 -*-
"""
Classify all 118 remaining duplicate email clusters into:
1. Confirmed Same Person (safe to merge)
2. Different Persons sharing an email (e.g. Supawan Ponpitakchai vs Supawan Pongpattanawut)
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
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b|อ\.|ผศ\.|รศ\.|ศ\.)\s*",
    re.IGNORECASE
)

def get_bare_thai(name):
    if not name: return ""
    m = RE_TITLE.match(name)
    b = name[m.end():].strip() if m else name.strip()
    return re.sub(r"\s+", " ", b)

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

def are_same_person(f1, f2, email):
    # 1. Check if OpenAlex ID is identical
    oa1 = (f1.openalex_id or "").replace("https://openalex.org/", "").strip()
    oa2 = (f2.openalex_id or "").replace("https://openalex.org/", "").strip()
    if oa1 and oa2 and oa1 != "not_indexed" and oa2 != "not_indexed" and oa1 == oa2:
        return True

    t1 = get_bare_thai(f1.full_name_th)
    t2 = get_bare_thai(f2.full_name_th)
    has_th1 = bool(re.search(r"[฀-๿]", t1))
    has_th2 = bool(re.search(r"[฀-๿]", t2))

    # Both have Thai:
    if has_th1 and has_th2:
        # Check token sort ratio
        ratio = fuzz.token_sort_ratio(t1, t2)
        if ratio >= 60:
            return True
        # Check if first names match in Thai
        w1 = t1.split()
        w2 = t2.split()
        if w1 and w2:
            fn_sim = fuzz.ratio(w1[0], w2[0])
            if fn_sim >= 80:
                # If first names match, check last names
                if len(w1) > 1 and len(w2) > 1:
                    ln_sim = fuzz.ratio(w1[1], w2[1])
                    if ln_sim >= 60:
                        return True
                    else:
                        return False # Different last names!
        return False

    # One is Thai, one is English
    # Extract email username parts e.g. "kanjana.l" -> "kanjana", "l"
    u = email.split("@")[0].lower()
    clean_en_tokens = re.sub(r"[^a-zA-Z\s]", " ", f"{f1.first_name} {f1.last_name} {f2.first_name} {f2.last_name}").lower().split()

    # If the English name token matches the non-Thai record
    non_th = t1 if not has_th1 else t2
    non_th_clean = RE_EN_PREFIX.sub("", non_th).strip().lower()

    # Check if non_th_clean is in clean_en_tokens or matches username
    if any(fuzz.partial_ratio(tok, non_th_clean) >= 80 for tok in clean_en_tokens):
        return True
    if any(tok in non_th_clean for tok in u.split(".")):
        return True

    return False

safe_clusters = []
unsafe_clusters = []

for em, cluster in dup_emails.items():
    all_same = True
    f_lead = cluster[0]
    for f_other in cluster[1:]:
        if not are_same_person(f_lead, f_other, em):
            all_same = False
            break

    if all_same:
        safe_clusters.append((em, cluster))
    else:
        unsafe_clusters.append((em, cluster))

print(f"Total duplicate email clusters: {len(dup_emails)}")
print(f"Safe verified merges (same person): {len(safe_clusters)}")
print(f"Unsafe (different persons sharing email): {len(unsafe_clusters)}")

print("\n--- Unsafe Clusters Sample ---")
for em, cluster in unsafe_clusters[:15]:
    print(f"\nEmail: {em}")
    for f in cluster:
        print(f"  {f.id} | {f.university_th} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | OA: {f.openalex_id}")

db.close()
