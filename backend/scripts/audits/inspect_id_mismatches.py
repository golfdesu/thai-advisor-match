"""Scan for ID prefix vs university_th mismatches."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB


def main():
    db = SessionLocal()
    prefix_uni_rules = [
        ("chulalongk_", "จุฬาลงกรณ์มหาวิทยาลัย"),
        ("cu_", "จุฬาลงกรณ์มหาวิทยาลัย"),
        ("chula_", "จุฬาลงกรณ์มหาวิทยาลัย"),
        ("mahidoluni_", "มหาวิทยาลัยมหิดล"),
        ("mu_", "มหาวิทยาลัยมหิดล"),
        ("chiangmaiu_", "มหาวิทยาลัยเชียงใหม่"),
        ("cmu_", "มหาวิทยาลัยเชียงใหม่"),
        ("kasetsartu_", "มหาวิทยาลัยเกษตรศาสตร์"),
        ("ku_", "มหาวิทยาลัยเกษตรศาสตร์"),
        ("khonkaenun_", "มหาวิทยาลัยขอนแก่น"),
        ("kku_", "มหาวิทยาลัยขอนแก่น"),
        ("thammasatu_", "มหาวิทยาลัยธรรมศาสตร์"),
        ("tu_", "มหาวิทยาลัยธรรมศาสตร์"),
        ("silpakornu_", "มหาวิทยาลัยศิลปากร"),
        ("su_", "มหาวิทยาลัยศิลปากร"),
        ("thaksinuni_", "มหาวิทยาลัยทักษิณ"),
        ("tsu_", "มหาวิทยาลัยทักษิณ"),
    ]

    mismatches = []
    for f in db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500):
        for prefix, expected_uni in prefix_uni_rules:
            if f.id.startswith(prefix) and f.university_th != expected_uni:
                mismatches.append((f.id, f.full_name_th, f.university_th, expected_uni))

    print(f"ID vs University mismatches: {len(mismatches)}")
    for m in mismatches:
        print(f"  [{m[0]}] '{m[1]}': current='{m[2]}' vs expected='{m[3]}'")

    db.close()


if __name__ == "__main__":
    main()
