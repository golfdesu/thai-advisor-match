import os
import sys
import json
import re
from dotenv import load_dotenv

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from rapidfuzz import fuzz

def main():
    json_path = os.path.join(backend_dir, "data", "cmu_tcas_scraped.json")
    with open(json_path, "r", encoding="utf-8") as f:
        tcas_data = json.load(f)

    # Aggregate TCAS by faculty, major, curriculum
    majors_map = {}
    for p in tcas_data:
        if p["tuition_per_semester"] == "ไม่ระบุ":
            continue
        key = (p["faculty"], p["major"], p["curriculum_type"])
        if key not in majors_map:
            majors_map[key] = {
                "faculty": p["faculty"],
                "major": p["major"],
                "curriculum_type": p["curriculum_type"],
                "fee": p["tuition_per_semester"],
                "careers": p["career_paths"],
                "source_url": p["source_url"]
            }

    print(f"Total Unique Valid TCAS Fee Records: {len(majors_map)}")

    db = SessionLocal()
    cmu_courses = db.query(CourseDB).filter(
        CourseDB.university.ilike("%Chiang Mai%"),
        CourseDB.degree_level.in_(["ปริญญาตรี", "Bachelor", "Bachelor's Degree"])
    ).all()

    print(f"Total CMU Bachelor Courses in DB: {len(cmu_courses)}")

    updated_count = 0
    for c in cmu_courses:
        best_match = None
        best_score = 0

        # Clean title for matching
        c_title = re.sub(r"^(หลักสูตร|สาขาวิชา|วท\.บ\.|วศ\.บ\.|ศศ\.บ\.|บธ\.บ\.|น\.บ\.|ส\.บ\.|พย\.บ\.|พท\.บ\.|พจ\.บ\.|พ\.บ\.|ท\.บ\.|ค\.บ\.|ศ\.บ\.|บช\.บ\.|ภ\.บ\.|สถ\.บ\.|ศศ\.บ\.)\s*", "", c.title_th)
        c_title = re.sub(r"\(\d{4}\)", "", c_title).strip()

        for (fac, maj, cur), info in majors_map.items():
            score = fuzz.token_set_ratio(c_title, maj)

            # Boost if faculty matches
            if c.faculty_th and fac in c.faculty_th:
                score += 15

            # Inter matching
            if "นานาชาติ" in c.title_th and cur == "นานาชาติ":
                score += 20
            elif "นานาชาติ" not in c.title_th and cur == "นานาชาติ":
                score -= 30

            if score > best_score:
                best_score = score
                best_match = info

        if best_match and best_score >= 70:
            c.tuition_per_semester = best_match["fee"]

            # Calculate total tuition
            fee_num_match = re.search(r"(\d[\d,]*)", best_match["fee"])
            if fee_num_match:
                fee_num = int(fee_num_match.group(1).replace(",", ""))

                # Check semesters
                if any(k in c.title_th for k in ["แพทย", "ทันต", "สัตว", "เภสัช"]):
                    semesters = 12
                elif "5 ปี" in (c.duration_years or "") or "สถาปัตยกรรม" in c.title_th:
                    semesters = 10
                else:
                    semesters = 8

                c.tuition_total = f"{fee_num * semesters:,} บาท"

            if best_match["careers"] and len(best_match["careers"]) > 0:
                c.career_paths = best_match["careers"]

            c.website_url = best_match["source_url"]

            # Re-generate embedding
            tags_str = " ".join(c.tags) if c.tags else ""
            career_str = " ".join(c.career_paths) if c.career_paths else ""
            t_en = c.title_en or ""
            f_th = c.faculty_th or ""
            f_en = c.faculty or ""
            desc = c.description or ""
            emb_text = f"{c.title_th} {t_en} {f_th} {f_en} {desc} {career_str} {tags_str}"
            c.embedding_text = emb_text
            try:
                c.embedding = embedding_service.get_embedding(emb_text)
            except Exception:
                pass

            updated_count += 1
            print(f"Updated: [{c.id}] {c.title_th} -> {c.tuition_per_semester} (Total: {c.tuition_total})")

    db.commit()
    print(f"\nSuccessfully enriched {updated_count} CMU Bachelor courses with TCAS official tuition fees!")
    db.close()

if __name__ == "__main__":
    main()
