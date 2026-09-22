# -*- coding: utf-8 -*-
"""
Database-Wide Zero-Defect Cleaning & Purge Pipeline (Round 2):
1. Snapshots & Deletes 36 non-person, phantom, curriculum header, phone header,
   and unindexed foreign-language co-author records.
2. Unlinks any foreign key references in research_labs.
3. Fixes and normalizes 34 corrupted records (exotic unicode glyph substitutions,
   textbook citation text leaks, parenthetical website breadcrumbs).
4. Replaces non-standard unicode dashes (‐-—) with standard ASCII '-' and
   strips zero-width characters (​, ﻿) across the entire database.
5. Re-synchronizes embedding_text for all modified records.
"""
import os
import sys
import re
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text
from sqlalchemy.orm import defer

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "clean_round2_deleted_and_normalized.json"
)

DELETE_IDS = [
    # Phone number headers
    "su_w43_0220_705",
    "su_w43_0221_414",
    # SUT date intervals
    "sut_w46_0004_701",
    "sut_w46_0461_162",
    "sut_w46_0468_883",
    "sut_w46_0630_202",
    "sut_w46_0631_549",
    "sut_w46_0666_777",
    "sut_w46_0670_721",
    "sut_w46_0684_403",
    "sut_w46_0700_452",
    "sut_w46_0708_664",
    "sut_w46_0780_262",
    "sut_w46_0842_165",
    # School / Curriculum / Department headers
    "su_w43_0218_832",
    "su_w43_0188_609",
    "su_w43_0208_925",
    "wave21_0015_909",
    # Journal / Conference phantoms
    "wu_w51_1051_594",
    "rmutk_w53b_0085_421",
    "rmutk_w53b_0094_754",
    # Multiple co-authors collapsed into single record
    "wu_w51_2146_599",
    "rmutk_w53b_0596_797",
    # Non-person single token without profile/pubs
    "tsu_w50_1877_597",
    # Unindexed foreign script co-authors with zero publications
    "sut_w46_0477_947",
    "ubu_w49_0224_520",
    "ubu_w49_0756_709",
    "mfu_w52_0893_798",
    "mfu_w52_1819_594",
    "ssru_w56_0381_429",
    "skru_w56_0327_612",
    "reru_w56_0309_646",
    "rmuti_w53b_1060_487",
    "rmutp_w53b_0168_140",
    "nstru_w56_0672_783",
    "ssru_w56_1051_918",
]

SPECIFIC_FIXES = {
    # Foreign glyph corruption fixes
    "kmitl_w39_0072_938": ("ผศ.ดร.", "ผศ.ดร. อริวา สุกันดี เปอร์มานา"),
    "kmitl_w39_0086_189": ("ผศ.ดร.", "ผศ.ดร. เชาวลิต หะมนตรี"),
    "kmitl_w39_0088_963": ("รศ.ดร.", "รศ.ดร. จารุวรรณ ก้อยวานิช"),
    "kmitl_w39_0090_593": ("ผศ.ดร.", "ผศ.ดร. รนน เจียรตระกูล"),
    "kmitl_w39_0136_293": ("รศ.ดร.", "รศ.ดร. สารินพร วิสิทธิ์สัตตพงศ์"),
    "kmitl_w39_0165_104": ("รศ.ดร.", "รศ.ดร. สมยศ เกียรติวานิชวิไล"),
    "kmitl_w39_0175_503": ("ดร.", "ดร. ณัชนนท์ ศุภอดิเรก"),
    "wave22_1321_259": ("รศ.ดร.", "รศ.ดร. มนทิณี ธีรลักษณ์"),
    "wave22_1325_223": ("รศ.ดร.", "รศ.ดร. บุษยา บุนนาค"),
    "wave26_0007_583": ("ศ.ดร.", "ศ.ดร. พลภัทร บุราคม"),
    "wave26_0008_239": ("ศ.ดร.", "ศ.ดร. อุดม ทุมโฆสิต"),
    "wave26_0014_518": ("รศ.ดร.", "รศ.ดร. เกษมศานต์ โชติชาครพันธุ์"),
    "wave26_0018_907": ("รศ.ดร.", "รศ.ดร. ปานนดา จันทรสุขรี"),
    "wave26_0020_553": ("รศ.ดร.", "รศ.ดร. ประพนธ์ สหพัฒนา"),
    "wave26_0034_285": ("รศ.ดร.", "รศ.ดร. ณัฐวุฒิ เจนวิทยาโรจน์"),
    "wave26_0037_394": ("ผศ.ดร.", "ผศ.ดร. ธันยนี โพธิสาร"),
    "wave26_0044_578": ("ผศ.ดร.", "ผศ.ดร. อรรถพล มูมี"),
    "wave27_0039_339": ("ศ.ดร.", "ศ.ดร. ปนัดดา บุญเสริม"),
    "wave27_0045_213": ("ศ.ดร.", "ศ.ดร. ชนาน อังศุธนะสมบัติ"),
    "wave27_0062_229": ("ศ.ดร.", "ศ.ดร. บัณฑิต เจตสว่าง"),
    "wave27_0073_607": ("ศ.ดร.", "ศ.ดร. เฉลิมพร องค์วรรณโสภณ"),
    "wave28_0004_662": ("รศ.ดร.", "รศ.ดร. ชูเกียรติ นิติสาจประเสริฐ"),

    # Trailing book/citation/unmatched punctuation fixes
    "wave21_0036_272": ("รศ.ดร.", "รศ.ดร. คณิศร์ มาตรา"),
    "mfu_w52_0005_860": ("ทพ.", "ทพ. พันฤทธิ์ ทองมาเอง"),
    "mfu_w52_0007_404": ("ทพญ.ดร.", "ทพญ.ดร. วิสสุตา คำพาที"),

    # Parenthetical website link fixes
    "wave21_0215_110": ("ผศ.ดร.", "ผศ.ดร. เสกสรรค์ ทองติ๊บ"),
    "wave21_0216_399": ("ดร.", "ดร. อุรัชชา สัจจาพงศ์"),
    "wave21_0213_992": ("อ.ดร.", "อ.ดร. สุทธิชัย ศิรินวล"),
    "wave21_0214_663": ("อ.ดร.", "อ.ดร. สุรางคนา ไชยรินคำ"),

    # Administrative parenthetical cleanup
    "buu_w42_0217_296": ("อ.", "อ. วิทวัส พันธุมจินดา"),
    "buu_w42_0222_937": ("อ.", "อ. จิรายุส อาบกิ่ง"),

    # Title formatting
    "nu_w45_0068_744": (None, "Kroekkiat Chinda"),
    "mfu_w52_0014_346": ("ศ.(เชี่ยวชาญพิเศษ) ทพ.ดร.", "ศ.(เชี่ยวชาญพิเศษ) ทพ.ดร. สุทธิชัย กฤษณะประกรกิจ"),
    "mfu_w52_0050_822": ("ศ.(พิเศษ) ดร.", "ศ.(พิเศษ) ดร. Kevin Hyde"),
}

def execute_cleaning():
    db = SessionLocal()
    try:
        # 1. Snapshot and Delete
        targets = db.query(FacultyDB).filter(FacultyDB.id.in_(DELETE_IDS)).all()
        print(f"Found {len(targets)} records to delete in Round 2 purge")

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "deleted_records": [],
            "normalized_records_before": []
        }

        for r in targets:
            snapshot["deleted_records"].append({
                "id": r.id,
                "full_name_th": r.full_name_th,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "university_th": r.university_th,
                "faculty_th": r.faculty_th,
                "department_th": r.department_th,
                "role": r.role,
                "email": r.email,
            })

        # Snapshot before values for normalized records
        norm_targets = db.query(FacultyDB).filter(FacultyDB.id.in_(list(SPECIFIC_FIXES.keys()))).all()
        for r in norm_targets:
            snapshot["normalized_records_before"].append({
                "id": r.id,
                "academic_title_th": r.academic_title_th,
                "full_name_th": r.full_name_th,
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        # Unlink foreign keys in research_labs
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(DELETE_IDS)).all()
        if labs:
            for l in labs:
                l.lead_advisor_id = None
            print(f"Unlinked {len(labs)} lab lead advisor references")

        for r in targets:
            db.delete(r)
        print(f"Deleted {len(targets)} records from faculties table")

        # 2. Specific Fixes
        for fid, (new_title, new_name) in SPECIFIC_FIXES.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                if new_title is not None:
                    fac.academic_title_th = new_title
                fac.full_name_th = new_name
                fac.embedding_text = build_faculty_embedding_text(fac)

        print(f"Applied {len(SPECIFIC_FIXES)} specific record normalizations")

        # 3. Database-Wide Unicode Hyphen & Zero-Width Char Normalization
        all_faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        unicode_dash_count = 0

        for f in all_faculties:
            name = f.full_name_th or ""
            changed = False

            # Replace unicode dashes with ASCII hyphen
            new_name = name
            for dash in ("‐", "‑", "‒", "–", "—"):
                if dash in new_name:
                    new_name = new_name.replace(dash, "-")
                    changed = True

            # Strip zero-width spaces
            for zw in ("​", "﻿"):
                if zw in new_name:
                    new_name = new_name.replace(zw, "")
                    changed = True

            new_name = new_name.strip()
            if changed and new_name != name:
                f.full_name_th = new_name
                f.embedding_text = build_faculty_embedding_text(f)
                unicode_dash_count += 1

        print(f"Normalized {unicode_dash_count} records with unicode dashes/zero-width chars")

        db.commit()
        print("Round 2 Database-wide changes successfully committed!")

    except Exception as e:
        db.rollback()
        print(f"Error during execution: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_cleaning()
