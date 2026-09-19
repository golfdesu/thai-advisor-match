"""Scan local PostgreSQL for deeper anomalies:
1. Duplicate faculty records (same person in same university)
2. Departmental shared inboxes in personal email field
3. Empty string values in featured_publications ('url': '')
4. Broken/unusual department or university fields
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def clean_thai_name(name: str | None) -> str:
    if not name:
        return ""
    # Strip common titles
    n = re.sub(
        r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.|สพ\.ญ\.|ทนพ\.|ทนพญ\.|นายแพทย์|แพทย์หญิง|ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s*",
        "",
        name.strip(),
    )
    n = re.sub(r"^(เกียรติคุณ|ดร\.)\s*", "", n.strip())
    n = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)\s*", "", n.strip())
    return re.sub(r"\s+", " ", n).strip()


def run_scan():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("DEEP LOCAL POSTGRESQL ANOMALY SCAN")
        print("=" * 80)

        # 1. DUPLICATE FACULTY MEMBERS (SAME PERSON IN SAME UNIVERSITY)
        name_uni_map: dict[tuple[str, str], list[FacultyDB]] = {}
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            cn = clean_thai_name(f.full_name_th)
            parts = cn.split()
            if len(parts) >= 2 and len(parts[0]) > 1 and len(parts[1]) > 1:
                key = (cn, f.university_th or "")
                name_uni_map.setdefault(key, []).append(f)

        same_uni_dups = {k: v for k, v in name_uni_map.items() if len(v) > 1}
        print(f"\n[1] Duplicate faculty records (same Thai name & university): {len(same_uni_dups)}")
        for (name, uni), facs in list(same_uni_dups.items())[:15]:
            print(f"  * '{name}' at {uni} ({len(facs)} records):")
            for f in facs:
                print(f"    - [{f.id}] {f.full_name_th} | {f.faculty_th} | Email: {f.email} | OA: {f.openalex_id}")

        # 2. DEPARTMENTAL SHARED INBOXES
        email_counts = Counter()
        email_map: dict[str, list[FacultyDB]] = {}
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            if f.email:
                em = f.email.lower().strip()
                email_counts[em] += 1
                email_map.setdefault(em, []).append(f)

        dept_inbox_candidates = []
        for em, cnt in email_counts.items():
            if cnt >= 3:
                dept_inbox_candidates.append((em, cnt))

        print(f"\n[2] Highly shared emails (>= 3 faculty records): {len(dept_inbox_candidates)}")
        total_records_with_shared_email = sum(cnt for _, cnt in dept_inbox_candidates)
        print(f"  Total records affected: {total_records_with_shared_email}")
        for em, cnt in sorted(dept_inbox_candidates, key=lambda x: x[1], reverse=True)[:15]:
            print(f"  * {em}: {cnt} records")
            for f in email_map[em][:2]:
                print(f"    - [{f.id}] {f.full_name_th} ({f.university_th})")

        # 3. EMPTY URLS IN FEATURED_PUBLICATIONS
        empty_pub_urls = []
        for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
            if isinstance(f.featured_publications, list):
                has_empty_url = False
                for p in f.featured_publications:
                    if isinstance(p, dict) and p.get("url") == "":
                        has_empty_url = True
                        break
                if has_empty_url:
                    empty_pub_urls.append(f.id)
        print(f"\n[3] Faculty records with empty publication URL ('url': ''): {len(empty_pub_urls)}")

        # 4. UNIVERSITY & FACULTY CANONICALIZATION CHECK
        unis = Counter(f.university_th for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500))
        print(f"\n[4] Total distinct universities in faculties: {len(unis)}")
        for u, cnt in unis.most_common(10):
            print(f"  * {u}: {cnt:,} records")

        # Check for any university with weird character or trailing space
        unusual_unis = [u for u in unis if not u or u.strip() != u or "  " in u]
        print(f"  Unusual university strings: {unusual_unis}")

    finally:
        db.close()


if __name__ == "__main__":
    run_scan()
