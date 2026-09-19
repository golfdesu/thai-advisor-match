"""Scan entire PostgreSQL database for:
1. Foreign institutional emails (e.g. .edu, .ac.uk, .ac.jp, foreign domains) on Thai universities.
2. Cross-university email mismatches (e.g. Chula faculty with Mahidol/KU/CMU email, or vice versa).
3. Visiting / Adjunct / External roles in faculties table.
"""
from __future__ import annotations

import json
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

UNI_DOMAIN_MAP = {
    "จุฬาลงกรณ์มหาวิทยาลัย": ["chula.ac.th", "sasin.edu", "chulavrc.org", "chula.md"],
    "มหาวิทยาลัยเกษตรศาสตร์": ["ku.th", "ku.ac.th"],
    "มหาวิทยาลัยเชียงใหม่": ["cmu.ac.th", "chiangmai.ac.th"],
    "มหาวิทยาลัยมหิดล": ["mahidol.ac.th", "mahidol.edu"],
    "มหาวิทยาลัยธรรมศาสตร์": ["tu.ac.th", "siit.tu.ac.th"],
    "มหาวิทยาลัยขอนแก่น": ["kku.ac.th"],
    "มหาวิทยาลัยสงขลานครินทร์": ["psu.ac.th"],
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": ["kmitl.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ["kmutt.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ["kmutnb.ac.th", "tggs-bangkok.org"],
    "มหาวิทยาลัยศิลปากร": ["su.ac.th"],
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": ["swu.ac.th", "g.swu.ac.th"],
    "มหาวิทยาลัยอุบลราชธานี": ["ubu.ac.th"],
    "มหาวิทยาลัยนเรศวร": ["nu.ac.th"],
    "มหาวิทยาลัยบูรพา": ["buu.ac.th"],
    "มหาวิทยาลัยแม่ฟ้าหลวง": ["mfu.ac.th"],
    "มหาวิทยาลัยแม่โจ้": ["mju.ac.th"],
    "มหาวิทยาลัยวลัยลักษณ์": ["wu.ac.th"],
    "มหาวิทยาลัยพะเยา": ["up.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": ["sut.ac.th"],
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์": ["nida.ac.th"],
    "มหาวิทยาลัยทักษิณ": ["tsu.ac.th"],
    "มหาวิทยาลัยสงฆ์": ["mcu.ac.th", "mbu.ac.th"],
}

# Organizations / Hospitals / Research institutes that are affiliated with universities:
# e.g., rihes.cmu.ac.th, med.cmu.ac.th, etc. are under cmu.ac.th


def main():
    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)

    foreign_email_records = []
    cross_uni_records = []
    visiting_role_records = []

    count = 0
    email_count = 0

    for f in faculties:
        count += 1
        role_str = (f.role or "").lower()
        name_str = (f.full_name_th or "").lower()

        # Condition 3: Visiting / Adjunct role
        if any(k in role_str or k in name_str for k in ["visiting", "อาจารย์พิเศษ", "adjunct", "part-time"]):
            visiting_role_records.append({
                "id": f.id,
                "name": f.full_name_th,
                "uni": f.university_th,
                "faculty": f.faculty_th,
                "role": f.role,
                "email": f.email
            })

        if not f.email:
            continue

        email_count += 1
        em = f.email.strip().lower()
        domain = em.split("@")[-1]

        # Condition 1: Foreign institution domain
        is_thai = any(domain.endswith(t) for t in [".th", "chulavrc.org", "tggs-bangkok.org", "sasin.edu", "chula.md"])
        if not is_thai:
            foreign_email_records.append({
                "id": f.id,
                "name": f.full_name_th,
                "uni": f.university_th,
                "faculty": f.faculty_th,
                "email": f.email,
                "domain": domain
            })
            continue

        # Condition 2: Cross-University Domain Mismatch
        uni = f.university_th or ""
        matched_uni_key = None
        for k in UNI_DOMAIN_MAP:
            if k in uni:
                matched_uni_key = k
                break

        if matched_uni_key:
            valid_domains = UNI_DOMAIN_MAP[matched_uni_key]
            # check if domain matches any valid domain or subdomain
            if not any(domain == vd or domain.endswith("." + vd) for vd in valid_domains):
                cross_uni_records.append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "uni": f.university_th,
                    "faculty": f.faculty_th,
                    "email": f.email,
                    "domain": domain,
                    "expected": valid_domains
                })

    print(f"Total faculties scanned: {count}")
    print(f"Total faculties with email: {email_count}")

    print("\n=======================================================")
    print(f"1. FOREIGN INSTITUTIONAL EMAILS (NOT THAI DOMAIN): {len(foreign_email_records)}")
    print("=======================================================")
    for r in foreign_email_records:
        print(f"  {r['id']} | {r['name']} | {r['uni']} | {r['faculty']} | {r['email']}")

    print("\n=======================================================")
    print(f"2. CROSS-UNIVERSITY EMAIL MISMATCHES: {len(cross_uni_records)}")
    print("=======================================================")
    for r in cross_uni_records:
        print(f"  {r['id']} | {r['name']} | {r['uni']} | {r['faculty']} | {r['email']} (Expected: {r['expected']})")

    print("\n=======================================================")
    print(f"3. VISITING / ADJUNCT / SPECIAL ROLES: {len(visiting_role_records)}")
    print("=======================================================")
    for r in visiting_role_records:
        print(f"  {r['id']} | {r['name']} | {r['uni']} | {r['faculty']} | role={r['role']} | email={r['email']}")

    # Save to json report
    out_file = BACKEND_DIR / "data" / "agent_states" / "scan_cross_uni_and_visiting_report.json"
    report = {
        "total_scanned": count,
        "total_with_email": email_count,
        "foreign_emails": foreign_email_records,
        "cross_uni_mismatches": cross_uni_records,
        "visiting_roles": visiting_role_records
    }
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved to: {out_file}")

    db.close()


if __name__ == "__main__":
    main()
