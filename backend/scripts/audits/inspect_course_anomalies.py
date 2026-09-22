# -*- coding: utf-8 -*-
"""
Inspect all course anomalies across 7 categories in PostgreSQL.
"""
import sys, os, json, re
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import dotenv
dotenv.load_dotenv(ROOT / ".env")

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from sqlalchemy.orm import defer

def inspect_all():
    db = SessionLocal()
    try:
        courses = db.query(CourseDB).options(defer(CourseDB.embedding)).all()
        print(f"Total courses loaded: {len(courses)}")

        # 1. Degree Level Inconsistencies
        deg_levels = defaultdict(list)
        for c in courses:
            deg_levels[c.degree_level].append(c.id)
        print("\n=== 1. Degree Levels ===")
        for deg, ids in deg_levels.items():
            print(f"  {deg}: {len(ids)} courses")

        # 2. Empty degree_name
        empty_deg_name = [c for c in courses if not (c.degree_name or "").strip()]
        print(f"\n=== 2. Empty degree_name: {len(empty_deg_name)} ===")
        for c in empty_deg_name:
            print(f"  id: {c.id} | uni: {c.university_th} | title: {c.title_th} | deg_level: {c.degree_level}")

        # 3. Faculty Name Inconsistencies (faculty_th)
        mfu_en_fac = [c for c in courses if (c.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง" or "mfu" in c.id) and re.search(r"[a-zA-Z]", c.faculty_th or "")]
        print(f"\n=== 3a. MFU English faculties: {len(mfu_en_fac)} ===")
        mfu_facs = set(c.faculty_th for c in mfu_en_fac)
        for f in sorted(mfu_facs):
            print(f"  '{f}'")

        unspecified_fac = [c for c in courses if (c.faculty_th or "").strip() in ["ไม่ระบุ", "None", ""] or not c.faculty_th]
        print(f"\n=== 3b. Unspecified faculties: {len(unspecified_fac)} ===")
        for c in unspecified_fac:
            print(f"  id: {c.id} | uni: {c.university_th} | title: {c.title_th}")

        typo_fac = [c for c in courses if "สาขาวิชมนุษยนิเวศศาสตร์" in (c.faculty_th or "")]
        print(f"\n=== 3c. Typo faculties: {len(typo_fac)} ===")
        for c in typo_fac:
            print(f"  id: {c.id} | fac: {c.faculty_th}")

        # 4. Course Title Anomalies (title_th)
        double_prefix = [c for c in courses if "หลักสูตรหลักสูตร" in (c.title_th or "")]
        print(f"\n=== 4a. Double prefix: {len(double_prefix)} ===")
        for c in double_prefix:
            print(f"  id: {c.id} | title: {c.title_th}")

        nbsp_titles = [c for c in courses if " " in (c.title_th or "")]
        print(f"\n=== 4b. Non-breaking space in title: {len(nbsp_titles)} ===")
        for c in nbsp_titles:
            print(f"  id: {c.id} | title: {repr(c.title_th)}")

        zero_thai = [c for c in courses if not re.search(r"[฀-๿]", c.title_th or "")]
        print(f"\n=== 4c. Zero Thai chars in title_th: {len(zero_thai)} ===")
        for c in zero_thai:
            print(f"  id: {c.id} | title_th: {c.title_th} | title_en: {c.title_en} | uni: {c.university_th}")

        raw_en_in_title = [c for c in courses if re.search(r"[a-zA-Z]{3,}", c.title_th or "")]
        print(f"\n=== 4d. Raw English words in title_th: {len(raw_en_in_title)} ===")
        for c in raw_en_in_title[:20]:
            print(f"  id: {c.id} | title: {c.title_th}")

        # 5. Tuition Anomalies
        cmu_null_total = [c for c in courses if c.university_th == "มหาวิทยาลัยเชียงใหม่" and c.tuition_total is None and c.tuition_per_semester]
        print(f"\n=== 5a. CMU tuition_total IS NULL with semester: {len(cmu_null_total)} ===")
        for c in cmu_null_total[:5]:
            print(f"  id: {c.id} | sem: {c.tuition_per_semester} | total: {c.tuition_total} | dur: {c.duration_years}")

        thb_tuition = [c for c in courses if ("THB" in str(c.tuition_per_semester or "")) or ("THB" in str(c.tuition_total or ""))]
        print(f"\n=== 5b. 'THB' in tuition: {len(thb_tuition)} ===")
        for c in thb_tuition:
            print(f"  id: {c.id} | sem: {c.tuition_per_semester} | total: {c.tuition_total}")

        # 6. Duration & Credits format
        bare_dur = [c for c in courses if re.match(r"^\d+(\.\d+)?$", str(c.duration_years or "").strip())]
        print(f"\n=== 6a. Bare number duration_years: {len(bare_dur)} ===")
        for c in bare_dur[:5]:
            print(f"  id: {c.id} | dur: {c.duration_years}")

        bare_credits = [c for c in courses if re.match(r"^\d+$", str(c.total_credits or "").strip())]
        print(f"\n=== 6b. Bare number total_credits: {len(bare_credits)} ===")
        for c in bare_credits[:5]:
            print(f"  id: {c.id} | cred: {c.total_credits}")

        # 7. Semantic Tag & Career Path Contamination
        it_careers = ["Software Engineer", "Data Scientist / AI Engineer", "System Analyst & Architect", "Cybersecurity Specialist", "นักวิชาการ/นักวิจัยคอมพิวเตอร์"]
        mismatched_it = []
        for c in courses:
            c_careers = c.career_paths or []
            if c_careers == it_careers:
                comb = ((c.faculty_th or "") + " " + (c.title_th or "")).lower()
                # If definitely not IT
                if any(k in comb for k in ["พยาบาล", "แพทย์", "ทันตแพทย์", "สาธารณสุข", "เภสัช", "สถาปัตย", "มนุษย", "อักษร", "นิติ", "ศิลปกรรม"]):
                    mismatched_it.append(c)
        print(f"\n=== 7. Mismatched IT fallback career paths: {len(mismatched_it)} ===")
        for c in mismatched_it[:10]:
            print(f"  id: {c.id} | fac: {c.faculty_th} | title: {c.title_th}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_all()
