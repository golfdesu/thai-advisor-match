# -*- coding: utf-8 -*-
"""
Simulation of 3-Pass Academic Deduplication per Section 9 Invariant 10:
Pass 1: Normalized Thai Name within same university
Pass 2: Clean English Name within same university
Pass 3: Verified Non-Shared Personal Academic Email
"""
import os
import sys
import re
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

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

# Pass 1: Normalized Thai Name + Univ
pass1_groups = defaultdict(list)
# Pass 2: Clean English Name + Univ
pass2_groups = defaultdict(list)
# Pass 3: Unique Email
pass3_groups = defaultdict(list)

for f in faculties:
    name_th = (f.full_name_th or "").strip()
    if re.search(r"[฀-๿]", name_th):
        m = RE_TITLE.match(name_th)
        bare_th = name_th[m.end():].strip() if m else name_th
        bare_th = re.sub(r"\s+", " ", bare_th)
        words = bare_th.split()
        if len(words) >= 2 and len(bare_th) >= 6:
            pass1_groups[(f.university_th, bare_th)].append(f.id)

    # English name
    first_en = RE_EN_PREFIX.sub("", (f.first_name or "").strip()).strip()
    last_en = (f.last_name or "").strip()
    if first_en and last_en and len(first_en) > 1 and len(last_en) > 1:
        clean_en = f"{first_en} {last_en}".lower()
        pass2_groups[(f.university_th, clean_en)].append(f.id)

    # Email
    if f.email and "@" in f.email:
        clean_email = f.email.strip().lower()
        # Exclude common departmental inboxes
        user = clean_email.split("@")[0]
        if user not in {"info", "admin", "contact", "office", "dean", "sci", "dent", "med", "eng"}:
            pass3_groups[clean_email].append(f.id)

p1_dups = {k: v for k, v in pass1_groups.items() if len(v) > 1}
p2_dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}
p3_dups = {k: v for k, v in pass3_groups.items() if len(v) > 1}

print(f"Pass 1 (Thai Name + Univ) duplicate clusters: {len(p1_dups)} (records: {sum(len(v) for v in p1_dups.values())})")
print(f"Pass 2 (English Name + Univ) duplicate clusters: {len(p2_dups)} (records: {sum(len(v) for v in p2_dups.values())})")
print(f"Pass 3 (Verified Email) duplicate clusters: {len(p3_dups)} (records: {sum(len(v) for v in p3_dups.values())})")

db.close()
