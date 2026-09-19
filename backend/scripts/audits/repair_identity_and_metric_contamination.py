"""Repair identity and metric contamination in local PostgreSQL.

Default mode is a read-only dry-run. ``--apply`` commits only these bounded repairs:

1. Purge 20 synthetic mock records (mu-sci-001 to mu-sci-020) and 2 non-person / duplicate stubs:
   - 'khonkaenun_facultyofm_fac_011_011' (header scraper artifact 'รศ. พญ.')
   - 'chulalongk_facultyofs_fac_009_009' (duplicate stub of 'chulalongk_facultyofs_fac_017_017')
2. Disambiguate and reset single-name contaminated OpenAlex metrics:
   - Disassociate CERN Peter Jenni metrics (A5107869992, h-index 102) from Chula Pharmacy lecturer
   - Disassociate UC Davis Eliot Atekwana metrics (A5017130028) from Chula Allied Health
   - Disassociate Louisville Noppadon metrics (A5025835750) from Chula Pharmacy
   - Disassociate Parinya Chamnan metrics (A5016951527) from KKU Parinya Khongphrom
   - Disassociate Daris Swindler metrics (A5109813649) and assign authentic Daris Samart (A5025322553)
   - Disassociate CMU Wachiraporn Maisang metrics (A5046364570) from Walailak Law instructor
   - Disassociate other mismatched single-name records
3. Correct regional faculty identities from authoritative live web sources:
   - Thaksin University (MuSE) 5 faculty members (Rungrawee, Sunsanee, Thianthip, Vanpra, Wanwisa)
   - Ubon Ratchathani University (Liberal Arts) Mitt Supphud
4. Normalize double prefixes ('นพ. นพ.') and leading/multiple whitespaces in names and courses.
5. Normalize empty strings ("") to SQL NULL across faculties (first_name, last_name, email, profile_url, image_url, scholar_url).
6. Rebuild embedding_text for every updated faculty record.

Zero external API calls, zero egress to Supabase.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import CourseDB, FacultyDB, ResearchLabDB


SYNTHETIC_MOCK_IDS_TO_DELETE = {
    f"mu-sci-{i:03d}_{h}"
    for i, h in [
        (1, "41f1bd"), (2, "296615"), (3, "6d8bcd"), (4, "575311"), (5, "f6b64c"),
        (6, "43e0d6"), (7, "83af46"), (8, "107e9b"), (9, "169543"), (10, "4f78b1"),
        (11, "a2d648"), (12, "973f30"), (13, "7a1fa2"), (14, "950b3f"), (15, "c22e94"),
        (16, "ecc60e"), (17, "81e4f9"), (18, "f76373"), (19, "cee9fd"), (20, "75da4b"),
    ]
}

STUB_IDS_TO_DELETE = {
    "khonkaenun_facultyofm_fac_011_011",  # Header scraper artifact 'รศ. พญ.'
    "chulalongk_facultyofs_fac_009_009",  # Duplicate stub of 'chulalongk_facultyofs_fac_017_017'
}

ALL_IDS_TO_DELETE = SYNTHETIC_MOCK_IDS_TO_DELETE | STUB_IDS_TO_DELETE

# Specific verified updates for single-name records with contaminated OpenAlex metrics
OPENALEX_CONTAMINATION_RESETS = {
    "chulalongk_facultyofp_fac_036_036": {
        "full_name_th": "ผศ. ภญ. เจนนิษฐ์ มั่นคงปรีดากุล",
        "first_name": "Jennis",
        "last_name": "Meancongpheedakul",
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "khonkaenun_facultyofm_fac_035_035": {
        "last_name": "Khongphrom",
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chulalongk_facultyofp_fac_010_010": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chulalongk_facultyofa_fac_008_008": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "khonkaenun_facultyofm_fac_031_031": {
        # Verified authentic KKU Physics profile A5025322553
        "last_name": "Samart",
        "openalex_id": "https://openalex.org/A5025322553",
        "total_publications_count": 80,
        "total_citations": 511,
        "h_index": 12,
        "featured_publications": [],
    },
    "regionalun_facultymem_fac_050_050": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "khonkaenun_facultyofm_fac_036_036": {
        "last_name": "Chaiwiriyawong",
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chulalongk_facultyofd_fac_028_028": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chulalongk_facultyofd_fac_020_020": {
        "full_name_th": "รศ.ดร. ทพญ. สุนทรา พรรณเชษฐ์",
        "last_name": "Panchetr",
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chulalongk_facultyofa_fac_001_001": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "mahidoluni_facultyofm_fac_015_015": {
        "openalex_id": "not_indexed",
        "total_publications_count": 0,
        "total_citations": 0,
        "h_index": 0,
        "featured_publications": [],
    },
    "chula_eng_cp_020": {
        # Valid profile, but last_name was empty string
        "last_name": "Lursinsap",
    },
}

# Regional faculty identity fixes from authoritative live websites
REGIONAL_FACULTY_FIXES = {
    "regionalun_facultymem_fac_088_088": {
        "full_name_th": "รศ.ดร. รุ่งรวี จิตภักดี",
        "first_name": "Rungrawee",
        "last_name": "Jitpakdee",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Multidisciplinary and Entrepreneurship",
        "faculty_th": "คณะสหวิทยาการและการประกอบการ",
        "department": "Multidisciplinary and Entrepreneurship",
        "department_th": "สหวิทยาการและการประกอบการ",
    },
    "regionalun_facultymem_fac_089_089": {
        "full_name_th": "อ.ดร. ศันสนีย์ วงศ์สวัสดิ์",
        "first_name": "Sunsanee",
        "last_name": "Wongsawat",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Multidisciplinary and Entrepreneurship",
        "faculty_th": "คณะสหวิทยาการและการประกอบการ",
        "department": "Multidisciplinary and Entrepreneurship",
        "department_th": "สหวิทยาการและการประกอบการ",
    },
    "regionalun_facultymem_fac_090_090": {
        "full_name_th": "อ. เทียนทิพย์ เดียวกี่",
        "first_name": "Thianthip",
        "last_name": "Diawkee",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Multidisciplinary and Entrepreneurship",
        "faculty_th": "คณะสหวิทยาการและการประกอบการ",
        "department": "Multidisciplinary and Entrepreneurship",
        "department_th": "สหวิทยาการและการประกอบการ",
    },
    "regionalun_facultymem_fac_091_091": {
        "full_name_th": "อ. วันพระ สืบสกุลจินดา",
        "first_name": "Vanpra",
        "last_name": "Seubsakulajinda",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Multidisciplinary and Entrepreneurship",
        "faculty_th": "คณะสหวิทยาการและการประกอบการ",
        "department": "Multidisciplinary and Entrepreneurship",
        "department_th": "สหวิทยาการและการประกอบการ",
    },
    "regionalun_facultymem_fac_092_092": {
        "full_name_th": "อ. วันวิสา วัชรากร",
        "first_name": "Wanwisa",
        "last_name": "Watcharakorn",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Multidisciplinary and Entrepreneurship",
        "faculty_th": "คณะสหวิทยาการและการประกอบการ",
        "department": "Multidisciplinary and Entrepreneurship",
        "department_th": "สหวิทยาการและการประกอบการ",
    },
    "regionalun_facultymem_fac_096_096": {
        "full_name_th": "อ. มิตต ทรัพย์ผุด",
        "first_name": "Mitt",
        "last_name": "Supphud",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Music Education",
        "department_th": "หลักสูตรศึกษาศาสตรบัณฑิต วิชาเอกดนตรีศึกษา",
    },
}

DOUBLE_TITLE_FIXES = {
    "khonkaenun_facultyofm_fac_004_004": "นพ. ยุทธพงศ์ วงศ์สวัสดิวัฒน์",
    "khonkaenun_facultyofm_fac_005_005": "นพ. รัฐพล อุปลา",
    "khonkaenun_facultyofm_fac_006_006": "นพ. สิรภูมิ เนียมสนิท",
}

WHITESPACE_NAME_FIXES = {
    "mahidoluni_facultyofm_akaraviputh_007": {"last_name": "Akaraviputh"},
    "cmu_eng_ee_015": {"full_name_th": "รศ.ดร. สมบูรณ์ นุชประยูร"},
}


def normalize_whitespace(text: str | None) -> str | None:
    if not text:
        return text
    return re.sub(r" {2,}", " ", text).strip()


def main(*, apply: bool) -> None:
    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "deleted_records": [],
        "openalex_resets": [],
        "regional_faculty_fixes": [],
        "double_title_fixes": [],
        "whitespace_name_fixes": [],
        "courses_collapsed_whitespace": 0,
        "empty_strings_normalized": {
            "first_name": 0,
            "last_name": 0,
            "email": 0,
            "profile_url": 0,
            "image_url": 0,
            "scholar_url": 0,
        },
        "embedding_texts_rebuilt": 0,
    }

    try:
        # 1. DELETE MOCK AND NON-PERSON RECORDS
        for fac_id in sorted(ALL_IDS_TO_DELETE):
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f:
                # Double check no research lab references this faculty
                lab = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == fac_id).first()
                if lab:
                    print(f"Skipping deletion of {fac_id}: referenced by lab {lab.id}")
                    continue
                report["deleted_records"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "reason": "synthetic mock" if f.id.startswith("mu-sci-") else "scraper stub",
                })
                if apply:
                    db.delete(f)

        # 2. OPENALEX CONTAMINATION RESETS
        for fac_id, updates in OPENALEX_CONTAMINATION_RESETS.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f:
                old_metrics = {
                    "openalex_id": f.openalex_id,
                    "total_publications_count": f.total_publications_count,
                    "total_citations": f.total_citations,
                    "h_index": f.h_index,
                }
                for k, v in updates.items():
                    setattr(f, k, v)
                f.embedding_text = build_faculty_embedding_text(f)
                report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1
                report["openalex_resets"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "before": old_metrics,
                    "after": {
                        "openalex_id": f.openalex_id,
                        "total_publications_count": f.total_publications_count,
                        "total_citations": f.total_citations,
                        "h_index": f.h_index,
                    },
                })

        # 3. REGIONAL FACULTY IDENTITY FIXES
        for fac_id, updates in REGIONAL_FACULTY_FIXES.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f:
                old_state = {
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th,
                    "department_th": f.department_th,
                }
                for k, v in updates.items():
                    setattr(f, k, v)
                f.embedding_text = build_faculty_embedding_text(f)
                report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1
                report["regional_faculty_fixes"].append({
                    "id": f.id,
                    "before": old_state,
                    "after": {
                        "full_name_th": f.full_name_th,
                        "university_th": f.university_th,
                        "faculty_th": f.faculty_th,
                        "department_th": f.department_th,
                    },
                })

        # 4. DOUBLE TITLE FIXES
        for fac_id, new_name in DOUBLE_TITLE_FIXES.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f and f.full_name_th != new_name:
                report["double_title_fixes"].append({
                    "id": f.id,
                    "before": f.full_name_th,
                    "after": new_name,
                })
                f.full_name_th = new_name
                f.embedding_text = build_faculty_embedding_text(f)
                report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        # 5. WHITESPACE NAME FIXES
        for fac_id, fields in WHITESPACE_NAME_FIXES.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f:
                for k, v in fields.items():
                    setattr(f, k, v)
                f.embedding_text = build_faculty_embedding_text(f)
                report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1
                report["whitespace_name_fixes"].append({"id": f.id, "fields": fields})

        # 6. COLLAPSE MULTIPLE SPACES IN COURSES
        courses = db.query(CourseDB).options(defer(CourseDB.embedding)).yield_per(500)
        for c in courses:
            changed = False
            if c.title_th and "  " in c.title_th:
                c.title_th = normalize_whitespace(c.title_th)
                changed = True
            if c.title_en and "  " in c.title_en:
                c.title_en = normalize_whitespace(c.title_en)
                changed = True
            if changed:
                report["courses_collapsed_whitespace"] = int(report["courses_collapsed_whitespace"]) + 1

        # 7. EMPTY STRINGS TO NULL ACROSS ALL REMAINING FACULTIES
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for f in faculties:
            if f.id in ALL_IDS_TO_DELETE:
                continue

            changed = False
            if f.first_name is not None and f.first_name.strip() == "":
                f.first_name = None
                report["empty_strings_normalized"]["first_name"] += 1
                changed = True

            if f.last_name is not None and f.last_name.strip() == "":
                f.last_name = None
                report["empty_strings_normalized"]["last_name"] += 1
                changed = True

            if f.email is not None and f.email.strip() == "":
                f.email = None
                report["empty_strings_normalized"]["email"] += 1
                changed = True

            if f.profile_url is not None and f.profile_url.strip() == "":
                f.profile_url = None
                report["empty_strings_normalized"]["profile_url"] += 1
                changed = True

            if f.image_url is not None and f.image_url.strip() == "":
                f.image_url = None
                report["empty_strings_normalized"]["image_url"] += 1
                changed = True

            if f.scholar_url is not None and f.scholar_url.strip() == "":
                f.scholar_url = None
                report["empty_strings_normalized"]["scholar_url"] += 1
                changed = True

            if changed:
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        out_filename = (
            "identity_and_metric_contamination_apply.json"
            if apply
            else "identity_and_metric_contamination_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Deleted records (mock/stubs): {len(report['deleted_records'])}")
        print(f"OpenAlex contamination resets: {len(report['openalex_resets'])}")
        print(f"Regional faculty identity fixes: {len(report['regional_faculty_fixes'])}")
        print(f"Double title fixes ('นพ. นพ.'): {len(report['double_title_fixes'])}")
        print(f"Whitespace name fixes: {len(report['whitespace_name_fixes'])}")
        print(f"Courses collapsed whitespace: {report['courses_collapsed_whitespace']}")
        print(f"Empty strings normalized to NULL:")
        for k, v in report["empty_strings_normalized"].items():
            print(f"  - {k}: {v}")
        print(f"Faculty embedding texts rebuilt: {report['embedding_texts_rebuilt']}")
        print(f"Report: {out_path}")

        if apply:
            db.commit()
            print("Committed all changes to local PostgreSQL.")
        else:
            db.rollback()
            print("Dry-run complete. No changes were committed.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit changes to local PostgreSQL")
    args = parser.parse_args()
    main(apply=args.apply)
