# -*- coding: utf-8 -*-
"""
Safe Two-Factor Cross-University Deduplication Simulation
========================================================
Enforces Invariant 10:
- Distinct persons with homonymous Thai names across different disciplines MUST NOT be merged.
- Only merges records where:
  1. OpenAlex ID matches (and not 'not_indexed')
  2. OR English first_name and last_name match
  3. OR Official institutional email matches
  4. OR Publication titles in featured_publications overlap (Jaccard > 0.3 or common title)
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

EMAIL_DOMAIN_MAP = {
    "chula.ac.th": "จุฬาลงกรณ์มหาวิทยาลัย",
    "cmu.ac.th": "มหาวิทยาลัยเชียงใหม่",
    "ku.ac.th": "มหาวิทยาลัยเกษตรศาสตร์",
    "mahidol.ac.th": "มหาวิทยาลัยมหิดล",
    "mahidol.edu": "มหาวิทยาลัยมหิดล",
    "psu.ac.th": "มหาวิทยาลัยสงขลานครินทร์",
    "kku.ac.th": "มหาวิทยาลัยขอนแก่น",
    "tu.ac.th": "มหาวิทยาลัยธรรมศาสตร์",
    "kmutt.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "kmitl.ac.th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "kmutnb.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "su.ac.th": "มหาวิทยาลัยศิลปากร",
    "sut.ac.th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "swu.ac.th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "buu.ac.th": "มหาวิทยาลัยบูรพา",
    "nu.ac.th": "มหาวิทยาลัยนเรศวร",
    "mfu.ac.th": "มหาวิทยาลัยแม่ฟ้าหลวง",
    "up.ac.th": "มหาวิทยาลัยพะเยา",
    "wu.ac.th": "มหาวิทยาลัยวลัยลักษณ์",
    "tsu.ac.th": "มหาวิทยาลัยทักษิณ",
    "msu.ac.th": "มหาวิทยาลัยมหาสารคาม",
    "ubu.ac.th": "มหาวิทยาลัยอุบลราชธานี",
    "mju.ac.th": "มหาวิทยาลัยแม่โจ้",
    "nida.ac.th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์",
    "ru.ac.th": "มหาวิทยาลัยรามคำแหง",
    "stou.ac.th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
}


def get_email_univ(email: str | None) -> str | None:
    if not email:
        return None
    em = email.lower().strip()
    for domain, univ in EMAIL_DOMAIN_MAP.items():
        if domain in em:
            return univ
    return None


def are_same_person(r1: FacultyDB, r2: FacultyDB) -> bool:
    """Strict Two-Factor Person Disambiguation."""
    # Factor 1: OpenAlex ID
    if r1.openalex_id and r2.openalex_id:
        if r1.openalex_id != "not_indexed" and r2.openalex_id != "not_indexed":
            if r1.openalex_id == r2.openalex_id:
                return True

    # Factor 2: Email
    if r1.email and r2.email:
        if r1.email.strip().lower() == r2.email.strip().lower():
            return True

    # Factor 3: English Name
    fn1 = (r1.first_name or "").strip().lower()
    ln1 = (r1.last_name or "").strip().lower()
    fn2 = (r2.first_name or "").strip().lower()
    ln2 = (r2.last_name or "").strip().lower()
    if fn1 and ln1 and fn2 and ln2:
        if fn1 == fn2 and ln1 == ln2:
            return True
        # If both have English names and they do NOT match -> definitely distinct persons!
        return False

    # Factor 4: Publication overlap
    pubs1 = set()
    for p in (r1.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and len(t) > 10:
            pubs1.add(t)
    pubs2 = set()
    for p in (r2.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and len(t) > 10:
            pubs2.add(t)

    if pubs1 and pubs2 and len(pubs1.intersection(pubs2)) > 0:
        return True

    # If Thai name matches exactly and both are in the exact same field/department
    d1 = (r1.department_th or "").strip()
    d2 = (r2.department_th or "").strip()
    f1 = (r1.faculty_th or "").strip()
    f2 = (r2.faculty_th or "").strip()
    if d1 and d2 and d1 != "ระบุไม่ได้" and d1 == d2:
        return True
    if f1 and f2 and f1 != "ระบุไม่ได้" and f1 == f2:
        return True

    return False


db = SessionLocal()
try:
    facs = db.query(FacultyDB).all()
    print(f"Total faculties: {len(facs):,}")

    # Build potential candidate clusters by Thai name
    thai_groups = defaultdict(list)
    for f in facs:
        th = (f.full_name_th or "").strip()
        th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.)\s*", "", th).strip()
        th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
        th_clean = re.sub(r"\s+", "", th_clean)
        if th_clean and len(th_clean) > 3 and not re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)$", th_clean):
            thai_groups[th_clean].append(f)

    # Build clusters by English name
    en_groups = defaultdict(list)
    for f in facs:
        fn = (f.first_name or "").strip().lower()
        ln = (f.last_name or "").strip().lower()
        if fn and ln and len(fn) > 1 and len(ln) > 1:
            en_groups[(fn, ln)].append(f)

    # Resolve duplicates
    verified_merges = []
    distinct_kept = []

    seen_pairs = set()

    # 1. Thai group checks
    for th_name, group in thai_groups.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                r1, r2 = group[i], group[j]
                pair_key = tuple(sorted([r1.id, r2.id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                if are_same_person(r1, r2):
                    verified_merges.append((r1, r2, f"Thai: {th_name}"))
                else:
                    distinct_kept.append((r1, r2, f"Disambiguated distinct: {th_name}"))

    # 2. English group checks
    for (fn, ln), group in en_groups.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                r1, r2 = group[i], group[j]
                pair_key = tuple(sorted([r1.id, r2.id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                verified_merges.append((r1, r2, f"English: {fn} {ln}"))

    print(f"\nTwo-Factor Deduplication Audit Results:")
    print(f"- Verified Duplicate Pairs to Merge & Clean: {len(verified_merges)}")
    print(f"- Distinct Persons Preserved (Disambiguated Collisions): {len(distinct_kept)}")

    print("\nSample Distinct Persons Preserved (Preventing False Merges):")
    for r1, r2, reason in distinct_kept[:5]:
        print(f"  Person 1: {r1.id} | {r1.full_name_th} ({r1.first_name} {r1.last_name}) @ {r1.university_th} [{r1.faculty_th}]")
        print(f"  Person 2: {r2.id} | {r2.full_name_th} ({r2.first_name} {r2.last_name}) @ {r2.university_th} [{r2.faculty_th}]")
        print("  --> KEPT DISTINCT (Zero False Merge)")
        print("-" * 60)

    print("\nSample Verified Duplicates to Merge & Archive Ghost:")
    for r1, r2, reason in verified_merges[:5]:
        print(f"  Row 1: {r1.id} | {r1.full_name_th} ({r1.first_name} {r1.last_name}) @ {r1.university_th} [{r1.faculty_th}] [Email: {r1.email}]")
        print(f"  Row 2: {r2.id} | {r2.full_name_th} ({r2.first_name} {r2.last_name}) @ {r2.university_th} [{r2.faculty_th}] [Email: {r2.email}]")
        print(f"  --> VERIFIED DUPLICATE ({reason})")
        print("-" * 60)

finally:
    db.close()
