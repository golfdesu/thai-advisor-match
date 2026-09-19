# -*- coding: utf-8 -*-
"""
Wave-37 Graduate Program Ingestion (โท/เอก) for 4 EXISTS faculties from
orphan_program_check2 verification (MSU Engineering, NU MedSci, PSU Computing,
SU Archaeology). SWU COSCI + MFU IT were UNCLEAR -> skipped (no ingest).

Source: SKILL.state course pipeline exports:
  backend/data/agent_states/wave37_course_msu_eng.py (runner)
  backend/data/agent_states/wave37_course_nu_medsci.py (runner, fallback seed)
  backend/data/agent_states/wave37_course_psu_comp.py (runner, homepage: ตรี only -> 0 kept)
  backend/data/agent_states/wave37_course_psu_comp_grad.py (same-pipeline driver on official
      /th/masterdegree/ hub HTML; 1 grounded โท hub row)
  backend/data/agent_states/wave37_course_su_archaeo.py (same-pipeline driver on official
      archae.su.ac.th HTML: incomplete TLS chain workaround, content official)

Rules (mirrors ingest_wave36_graduate_courses.py):
- Degree levels exactly ปริญญาโท / ปริญญาเอก (drop ตรี + ประกาศนียบัตร + combined โท/เอก rows).
- Dedup: exact (title_th, university_th, degree_level) + RapidFuzz >= 88 within same uni+degree+faculty.
- Duration: map LLM "4 ปี" default -> โท "2 ปี" / เอก "3 ปี".
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
logger = logging.getLogger("wave37")

AGENT_STATES = os.path.join(BACKEND_DIR, "data", "agent_states")
EXPORT_FILES = {
    "msu_eng": ["wave37_course_msu_eng.py"],
    "nu_medsci": ["wave37_course_nu_medsci.py"],
    "psu_comp": ["wave37_course_psu_comp.py", "wave37_course_psu_comp_grad.py"],
    "su_archaeo": ["wave37_course_su_archaeo.py"],
}
UNI_CODES = {"msu_eng": "msu", "nu_medsci": "nu", "psu_comp": "psu", "su_archaeo": "su"}


def load_export(fname):
    path = os.path.join(AGENT_STATES, fname)
    spec = importlib.util.spec_from_file_location(fname.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.EXTRACTED_COURSES)


def norm_title(t):
    return re.sub(r"\s+", " ", (t or "").strip())


def is_combined_level_row(c):
    title = c.get("title_th", "")
    dname = c.get("degree_name", "")
    return ("/" in dname) and ("มหาบัณฑิต" in title) and ("ดุษฎี" in title)


def select_candidates(courses):
    out = []
    for c in courses:
        if c.get("degree_level") not in ("ปริญญาโท", "ปริญญาเอก"):
            continue
        title = norm_title(c.get("title_th", ""))
        if not title or "ประกาศนียบัตร" in title:
            continue
        if is_combined_level_row(c):
            continue
        out.append(c)
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
        if any(k["university_th"] == c["university_th"]
               and k["degree_level"] == c["degree_level"]
               and fuzz.token_sort_ratio(t, norm_title(k["title_th"])) >= 88
               for k in kept):
            continue
        kept.append(c)
    return kept


def main():
    session = SessionLocal()
    try:
        existing_ids = {r[0] for r in session.query(CourseDB.id).all()}
        seen_exact = {(norm_title(t), u, d) for (t, u, d) in session.query(
            CourseDB.title_th, CourseDB.university_th, CourseDB.degree_level).all()}
        seen_fuzzy = [(t or "", u or "", d or "", f or "") for (t, u, d, f) in session.query(
            CourseDB.title_th, CourseDB.university_th, CourseDB.degree_level, CourseDB.faculty_th).all()]

        per_faculty = {}
        to_insert = []
        for key, fnames in EXPORT_FILES.items():
            raw = []
            for fn in fnames:
                raw.extend(load_export(fn))
            cands = dedup_in_batch(select_candidates(raw))
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
                base = f"wave37_{UNI_CODES[key]}_{deg}"
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

        null_emb = 0
        for c in to_insert:
            txt, vec = emb_map[c["id"]]
            if vec is None:
                null_emb += 1
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
        logger.info(f"WAVE37 inserted total={total} null_emb={null_emb}")
        for key, titles in per_faculty.items():
            logger.info(f"{key}: +{len(titles)}")
            for t in titles:
                logger.info(f"  + {t}")
        print(f"WAVE37_DONE total={total} null_emb={null_emb} " +
              " ".join(f"{k}={len(v)}" for k, v in per_faculty.items()))
    finally:
        session.close()


if __name__ == "__main__":
    main()
