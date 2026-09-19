# -*- coding: utf-8 -*-
"""
Wave-36 Graduate Program Ingestion (โท/เอก) for 6 faculties.

Source: SKILL.state course pipeline exports in backend/data/agent_states/wave36_course_*.py
(extraction) + 2 MJU rows grounded in the official admissions table
(admissions.mju.ac.th Graduate ProjectProgram grid: faculty-attributed rows).

Rules:
- Degree levels exactly ปริญญาโท / ปริญญาเอก (drop ตรี + ประกาศนียบัตร + combined โท/เอก rows).
- MJU: only Science-faculty rows (extractor defaulted target faculty onto all rows).
- Dedup: exact (title_th, university_th, degree_level) + RapidFuzz >= 88 within same uni+degree.
- Duration: keep genuine values; map LLM "4 ปี" default -> โท "2 ปี" / เอก "3 ปี".
- Local Docker DB ONLY (SessionLocal -> localhost:5432).
"""
import os
import re
import sys
import logging
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from rapidfuzz import fuzz

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wave36")

AGENT_STATES = os.path.join(BACKEND_DIR, "data", "agent_states")
EXPORT_KEYS = ["mju_sci", "msu_techno", "swu_pt", "nu_agi", "psu_agro", "kku_rx"]
UNI_CODES = {
    "mju_sci": "mju", "msu_techno": "msu", "swu_pt": "swu",
    "nu_agi": "nu", "psu_agro": "psu", "kku_rx": "kku",
}
MJU_SCIENCE_MATCH = ("เคมีประยุกต์", "เทคโนโลยีชีวภาพ", "พันธุศาสตร์", "นาโน")
MJU_ADMISSIONS_URL = ("https://admissions.mju.ac.th/graduate/"
                      "ProjectProgram.aspx?LevelID=3&ProjectID=Nw%3D%3D&r=1")

# Two MJU Science programs present as faculty-attributed rows in the official
# admissions grid but missed by the LLM patch (verified via raw-HTML probe).
MJU_TABLE_GROUNDED = [
    {
        "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาพันธุศาสตร์",
        "title_en": "Master of Science Program in Genetics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (พันธุศาสตร์)",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "",
        "department_th": "สาขาวิชาพันธุศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "",
        "tuition_per_semester": "",
        "tuition_total": "",
        "description": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพันธุศาสตร์ (บัณฑิตวิทยาลัย มหาวิทยาลัยแม่โจ้)",
        "curriculum_highlights": [],
        "career_paths": [],
        "tags": ["Genetics", "พันธุศาสตร์"],
        "website_url": MJU_ADMISSIONS_URL,
    },
    {
        "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีนาโน",
        "title_en": "Master of Science Program in Nanoscience and Nanotechnology",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาศาสตร์และเทคโนโลยีนาโน)",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "",
        "department_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีนาโน",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "",
        "tuition_per_semester": "",
        "tuition_total": "",
        "description": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีนาโน (บัณฑิตวิทยาลัย มหาวิทยาลัยแม่โจ้)",
        "curriculum_highlights": [],
        "career_paths": [],
        "tags": ["Nanoscience", "Nanotechnology", "นาโน"],
        "website_url": MJU_ADMISSIONS_URL,
    },
]


def load_export(key):
    path = os.path.join(AGENT_STATES, f"wave36_course_{key}.py")
    spec = importlib.util.spec_from_file_location(f"wave36_{key}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.EXTRACTED_COURSES)


def norm_title(t):
    return re.sub(r"\s+", " ", (t or "").strip())


def is_combined_level_row(c):
    title = c.get("title_th", "")
    dname = c.get("degree_name", "")
    return ("/" in dname) and ("มหาบัณฑิต" in title) and ("ดุษฎี" in title)


def select_candidates(key, courses):
    out = []
    for c in courses:
        if c.get("degree_level") not in ("ปริญญาโท", "ปริญญาเอก"):
            continue
        title = norm_title(c.get("title_th", ""))
        if not title or "ประกาศนียบัตร" in title:
            continue
        if is_combined_level_row(c):
            continue
        if key == "mju_sci" and not any(k in title for k in MJU_SCIENCE_MATCH):
            continue
        out.append(c)
    if key == "mju_sci":
        out.extend(MJU_TABLE_GROUNDED)
    return out


def normalize_duration(c):
    dur = (c.get("duration_years") or "").strip()
    if dur in ("4 ปี", "", "-"):
        return "2 ปี" if c["degree_level"] == "ปริญญาโท" else "3 ปี"
    return dur


def build_embedding_text(c):
    hl = ", ".join(c.get("curriculum_highlights") or [])
    cp = ", ".join(c.get("career_paths") or [])
    tg = ", ".join(c.get("tags") or [])
    return (
        f"{c['title_th']} {c.get('title_en', '')}. "
        f"University: {c.get('university', '')} {c.get('university_th', '')}. "
        f"Faculty: {c.get('faculty', '')} {c.get('faculty_th', '')}. "
        f"Department: {c.get('department', '')} {c.get('department_th', '')}. "
        f"Degree: {c['degree_level']} {c.get('degree_name', '')}. "
        f"Description: {c.get('description', '')}. "
        f"Highlights: {hl}. Careers: {cp}. Tags: {tg}."
    )


def dedup_in_batch(cands):
    kept = []
    for c in cands:
        t = norm_title(c["title_th"])
        dup = False
        for k in kept:
            if (k["university_th"] == c["university_th"]
                    and k["degree_level"] == c["degree_level"]
                    and fuzz.token_sort_ratio(t, norm_title(k["title_th"])) >= 88):
                dup = True
                break
        if not dup:
            kept.append(c)
    return kept


def main():
    session = SessionLocal()
    try:
        existing_ids = {r[0] for r in session.query(CourseDB.id).all()}
        existing_rows = session.query(
            CourseDB.title_th, CourseDB.university_th, CourseDB.degree_level).all()
        seen_exact = {(norm_title(t), u, d) for (t, u, d) in existing_rows}
        seen_fuzzy = [(t or "", u or "", d or "", f or "")
                      for (t, u, d, f) in
                      session.query(CourseDB.title_th, CourseDB.university_th,
                                    CourseDB.degree_level, CourseDB.faculty_th).all()]

        per_faculty = {}
        to_insert = []
        for key in EXPORT_KEYS:
            cands = dedup_in_batch(select_candidates(key, load_export(key)))
            added = []
            for c in cands:
                t = norm_title(c["title_th"])
                u = c["university_th"]
                d = c["degree_level"]
                if (t, u, d) in seen_exact:
                    logger.info(f"SKIP exact-dup: {t[:60]}")
                    continue
                if any(uu == u and dd == d and ff == c["faculty_th"]
                       and fuzz.token_sort_ratio(t, (tt or "")) >= 88
                       for (tt, uu, dd, ff) in seen_fuzzy):
                    logger.info(f"SKIP fuzzy-dup: {t[:60]}")
                    continue
                deg = "msc" if d == "ปริญญาโท" else "phd"
                base = f"wave36_{UNI_CODES[key]}_{deg}"
                n = 1
                cid = f"{base}_{n:02d}"
                while cid in existing_ids:
                    n += 1
                    cid = f"{base}_{n:02d}"
                existing_ids.add(cid)
                c["id"] = cid
                c["title_th"] = t
                c["duration_years"] = normalize_duration(c)
                seen_exact.add((t, u, d))
                seen_fuzzy.append((t, u, d, c["faculty_th"]))
                added.append(c)
                to_insert.append(c)
            per_faculty[key] = [c["title_th"] for c in added]

        # Embeddings (threaded) + single-batch commit
        def embed(c):
            try:
                txt = build_embedding_text(c)
                vec = embedding_service.get_embedding(txt)
                ok = isinstance(vec, list) and len(vec) == 768
                return (c["id"], txt, vec if ok else None)
            except Exception as e:
                logger.warning(f"embed fail {c['id']}: {str(e)[:120]}")
                return (c["id"], build_embedding_text(c), None)

        emb_map = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(embed, c): c["id"] for c in to_insert}
            for f in as_completed(futs):
                cid, txt, vec = f.result()
                emb_map[cid] = (txt, vec)

        for c in to_insert:
            txt, vec = emb_map[c["id"]]
            session.add(CourseDB(
                id=c["id"], title_th=c["title_th"], title_en=c.get("title_en"),
                degree_level=c["degree_level"], degree_name=c.get("degree_name"),
                university=c.get("university"), university_th=c.get("university_th"),
                faculty=c.get("faculty"), faculty_th=c.get("faculty_th"),
                department=c.get("department"), department_th=c.get("department_th"),
                program_type=c.get("program_type") or "ภาคปกติ",
                duration_years=c.get("duration_years"),
                total_credits=c.get("total_credits") or None,
                tuition_per_semester=c.get("tuition_per_semester") or None,
                tuition_total=c.get("tuition_total") or None,
                description=c.get("description"),
                curriculum_highlights=c.get("curriculum_highlights") or [],
                career_paths=c.get("career_paths") or [],
                tags=c.get("tags") or [],
                website_url=c.get("website_url"),
                embedding_text=txt, embedding=vec,
            ))
        session.commit()
        total = sum(len(v) for v in per_faculty.values())
        logger.info(f"WAVE36 inserted total={total}")
        for key, titles in per_faculty.items():
            logger.info(f"{key}: +{len(titles)}")
            for t in titles:
                logger.info(f"  + {t}")
        print(f"WAVE36_DONE total={total} " +
              " ".join(f"{k}={len(v)}" for k, v in per_faculty.items()))
    finally:
        session.close()


if __name__ == "__main__":
    main()
