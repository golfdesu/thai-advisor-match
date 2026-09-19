# -*- coding: utf-8 -*-
"""
Apply Microscopic Hygiene Repairs.

Applies:
1. Fix corrupted publication title for Asst. Prof. Dr. Monthana Phiphatphen (Thaksin University).
2. Merge Prince of Songkla duplicate into active Walailak University profile for Prof. Dr. Manat Chaijan
   with authoritative OpenAlex metrics (h-index=37, citations, works).
3. Backfill embedding_text for 5,216 faculties where text column was null (vector embedding intact).
4. Standardize program_type values in courses (International -> นานาชาติ, Thai/Regular -> ภาคปกติ).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def build_standard_embedding_text(f: FacultyDB) -> str:
    parts = [
        f.full_name_th or "",
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.academic_title_th or "",
        f.university_th or f.university or "",
        f.faculty_th or f.faculty or "",
        f.department_th or f.department or "",
    ]
    if f.research_interests:
        parts.append(" ".join(f.research_interests))
    if f.featured_publications:
        pub_titles = [
            p.get("title", "") if isinstance(p, dict) else str(p)
            for p in f.featured_publications
        ]
        parts.append(" ".join([t for t in pub_titles if t]))
    return " ".join([p for p in parts if p]).strip()


def apply_microscopic_repairs():
    db = SessionLocal()
    print("=" * 65)
    print("🚀 APPLYING MICROSCOPIC DATABASE REPAIRS")
    print("=" * 65)

    try:
        # 1. Fix corrupted publication title
        monthana = db.query(FacultyDB).filter(FacultyDB.id == "thaksinuni_facultyofe_phiphatphen_045").first()
        if monthana and monthana.featured_publications:
            print(f"📄 Restoring publication title for Monthana Phiphatphen: {monthana.id}")
            new_pubs = []
            for p in monthana.featured_publications:
                if isinstance(p, dict) and (p.get("title") or "").strip() == "-":
                    p["title"] = "การพัฒนาชุดกิจกรรมการอ่านภาษาอังกฤษเพื่อความเข้าใจโดยใช้การจัดการเรียนรู้แบบร่วมมือเทคนิค CIRC สำหรับนักเรียนชั้นมัธยมศึกษาปีที่ 1"
                    p["venue"] = "วารสารศึกษาศาสตร์ มหาวิทยาลัยทักษิณ (eduthu)"
                new_pubs.append(p)
            monthana.featured_publications = new_pubs

        # 2. Merge Manat Chaijan PSU record into active Walailak University record
        psu_manat = db.query(FacultyDB).filter(FacultyDB.id == "psu_agro_manat_001").first()
        wu_manat = db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_6e9f9e9a").first()
        if psu_manat and wu_manat:
            print(f"🔗 Merging PSU legacy record {psu_manat.id} into active Walailak profile {wu_manat.id}")
            wu_manat.openalex_id = psu_manat.openalex_id
            wu_manat.h_index = psu_manat.h_index
            wu_manat.total_citations = psu_manat.total_citations
            wu_manat.total_publications_count = psu_manat.total_publications_count
            if not wu_manat.featured_publications:
                wu_manat.featured_publications = psu_manat.featured_publications

            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == psu_manat.id).update(
                {ResearchLabDB.lead_advisor_id: wu_manat.id}
            )
            db.delete(psu_manat)

        # 3. Backfill embedding_text for faculties where column is None
        empty_emb_facs = db.query(FacultyDB).filter(FacultyDB.embedding_text.is_(None)).all()
        print(f"📝 Backfilling embedding_text for {len(empty_emb_facs)} faculty records...")
        for f in empty_emb_facs:
            f.embedding_text = build_standard_embedding_text(f)

        # 4. Standardize course program_type
        prog_type_map = {
            "International": "นานาชาติ",
            "International Program": "นานาชาติ",
            "International (Double Degree)": "นานาชาติ",
            "Special Program, International Program": "นานาชาติ",
            "หลักสูตรนานาชาติ": "นานาชาติ",
            "หลักสูตรนานาชาติ (International Program)": "นานาชาติ",
            "โครงการนานาชาติ (International Program)": "นานาชาติ",
            "Thai": "ภาคปกติ",
            "Thai Program": "ภาคปกติ",
            "ภาษาไทย": "ภาคปกติ",
            "ภาคภาษาไทย": "ภาคปกติ",
            "ไทย": "ภาคปกติ",
            "หลักสูตรไทย": "ภาคปกติ",
            "หลักสูตรปกติ": "ภาคปกติ",
            "ปกติ": "ภาคปกติ",
            "Regular": "ภาคปกติ",
            "โครงการปกติ": "ภาคปกติ",
            "National Program": "ภาคปกติ",
            "Taught in Thai": "ภาคปกติ",
            "English Program": "ภาคภาษาอังกฤษ",
            "English": "ภาคภาษาอังกฤษ",
            "ภาษาอังกฤษ": "ภาคภาษาอังกฤษ",
        }
        courses = db.query(CourseDB).filter(CourseDB.program_type.isnot(None)).all()
        course_fix_count = 0
        for c in courses:
            pt = (c.program_type or "").strip()
            if pt in prog_type_map:
                c.program_type = prog_type_map[pt]
                course_fix_count += 1
        print(f"🎓 Standardized program_type for {course_fix_count} courses")

        db.commit()
        print("\n" + "=" * 65)
        print("✅ ALL MICROSCOPIC REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during microscopic repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_microscopic_repairs()
