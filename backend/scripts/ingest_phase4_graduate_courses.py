# -*- coding: utf-8 -*-
"""
Phase 4 graduate program ingestion (โท/เอก) from university-wide course crawls (2026-09-26).

Source: SKILL.state course pipeline exports (course_cli_runner.py --follow-links):
  backend/data/agent_states/phase4/<key>.py

Rules (mirrors ingest_wave37_graduate_courses.py):
- Degree levels exactly ปริญญาโท / ปริญญาเอก (drop ตรี, ประกาศนียบัตร, combined โท/เอก rows).
- Dedup: exact (title_th, university_th, degree_level) + RapidFuzz >= 88 within same uni + degree.
  A match only fills empty total_credits / title_en / career_paths / curriculum_highlights;
  existing values are never overwritten.
- faculty_th is never guessed: taken from department_th when it names a คณะ/วิทยาลัย/สำนักวิชา,
  else from an existing course of the same university + department. Unresolved rows are
  quarantined to phase4/quarantine_unresolved_faculty.json.
- Duration: map LLM "4 ปี" default -> โท "2 ปี" / เอก "3 ปี".
- Local Docker DB ONLY.

Usage:
    python scripts/ingest_phase4_graduate_courses.py            # dry-run
    python scripts/ingest_phase4_graduate_courses.py --apply
"""
import os
import re
import sys
import json
import argparse
import logging
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from rapidfuzz import fuzz

from app.core.database import SessionLocal
from app.models.db_models import CourseDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase4")

PHASE4_DIR = Path(os.getenv("AGENT_STATE_DIR", BACKEND_DIR / "data" / "agent_states")) / "phase4"
KEYS = ["tsu", "wu", "buu", "msu", "ubu", "sut", "swu", "up"]
FACULTY_RE = re.compile(r"^(คณะ|วิทยาลัย|สำนักวิชา|สถาบัน)")
FILL_FIELDS = ("total_credits", "title_en", "career_paths", "curriculum_highlights")


def load_export(path: Path) -> list[dict]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(getattr(mod, "EXTRACTED_COURSES", []))


def norm_title(t):
    return re.sub(r"\s+", " ", (t or "").strip())


# field-of-study core: strips program / degree / สาขาวิชา wording so "หลักสูตรเคมี" and
# "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเคมี" compare equal
_CORE_STRIP_RE = re.compile(
    r"(หลักสูตร|ระดับ|ปริญญาโท|ปริญญาเอก|แผน\s*[กข]\S*|สาขาวิชา|สาขา|"
    r"[ก-๙]*(มหาบัณฑิต|ดุษฎีบัณฑิต)|\(.*?\)|\s+)")
_DEGREE_MARK_RE = re.compile(r"(มหาบัณฑิต|ดุษฎีบัณฑิต|ปริญญาโท|ปริญญาเอก)")


def core_key(title):
    return _CORE_STRIP_RE.sub("", title or "")


def select_candidates(courses):
    out = []
    for c in courses:
        if c.get("degree_level") not in ("ปริญญาโท", "ปริญญาเอก"):
            continue
        title = norm_title(c.get("title_th"))
        if not title or "ประกาศนียบัตร" in title:
            continue
        if "/" in (c.get("degree_name") or "") and "มหาบัณฑิต" in title and "ดุษฎี" in title:
            continue
        c["title_th"] = title
        out.append(c)
    return out


def normalize_duration(c):
    dur = (c.get("duration_years") or "").strip()
    if dur in ("4 ปี", "", "-"):
        return "2 ปี" if c["degree_level"] == "ปริญญาโท" else "3 ปี"
    return dur


def has_credits(v):
    return bool(v) and bool(re.search(r"\d", str(v))) and str(v).strip() != "0"


def build_embedding_text(c):
    return (
        f"{c['title_th']} {c.get('title_en') or ''}. "
        f"University: {c.get('university', '')} {c.get('university_th', '')}. "
        f"Faculty: {c.get('faculty') or ''} {c.get('faculty_th', '')}. "
        f"Department: {c.get('department') or ''} {c.get('department_th') or ''}. "
        f"Degree: {c['degree_level']} {c.get('degree_name') or ''}. "
        f"Description: {c.get('description') or ''}. "
        f"Highlights: {', '.join(c.get('curriculum_highlights') or [])}. "
        f"Careers: {', '.join(c.get('career_paths') or [])}. Tags: {', '.join(c.get('tags') or [])}."
    )


def main(apply: bool) -> None:
    session = SessionLocal()
    try:
        rows = session.query(CourseDB.id, CourseDB.title_th, CourseDB.title_en, CourseDB.university_th,
                             CourseDB.degree_level, CourseDB.faculty_th, CourseDB.faculty,
                             CourseDB.department_th, CourseDB.total_credits,
                             CourseDB.career_paths, CourseDB.curriculum_highlights).all()
        existing_ids = {r.id for r in rows}
        dept_faculty = {}
        for r in rows:
            if r.department_th and r.faculty_th:
                dept_faculty.setdefault((r.university_th, norm_title(r.department_th)), set()).add(
                    (r.faculty_th, r.faculty or ""))

        to_insert, fills, quarantine, stats = [], {}, [], {}
        for key in KEYS:
            path = PHASE4_DIR / f"{key}.py"
            if not path.exists():
                continue
            kept = []
            for c in select_candidates(load_export(path)):
                if any(k["degree_level"] == c["degree_level"] and
                       fuzz.token_sort_ratio(c["title_th"], k["title_th"]) >= 88 for k in kept):
                    continue
                kept.append(c)
            n_new = n_fill = n_q = 0
            for c in kept:
                u, d, t = c["university_th"], c["degree_level"], c["title_th"]
                ck = core_key(t)
                match = next((r for r in rows if r.university_th == u and r.degree_level == d and
                              (norm_title(r.title_th) == t or fuzz.token_sort_ratio(t, norm_title(r.title_th)) >= 88
                               or (ck and core_key(r.title_th) == ck))),
                             None)
                if not match and ck and any(r.university_th == u and core_key(r.title_th) == ck for r in rows):
                    # same field exists at another level; LLM-assigned level is not trustworthy enough
                    quarantine.append({**c, "reason": "field exists at other degree level"})
                    n_q += 1
                    continue
                if match:
                    patch = {}
                    if not has_credits(match.total_credits) and has_credits(c.get("total_credits")):
                        patch["total_credits"] = c["total_credits"]
                    if not (match.title_en or "").strip() and (c.get("title_en") or "").strip() \
                            and c["title_en"].strip() != t:
                        patch["title_en"] = c["title_en"].strip()
                    if not match.career_paths and c.get("career_paths"):
                        patch["career_paths"] = c["career_paths"]
                    if not match.curriculum_highlights and c.get("curriculum_highlights"):
                        patch["curriculum_highlights"] = c["curriculum_highlights"]
                    if patch:
                        fills[match.id] = patch
                        n_fill += 1
                    continue
                if not _DEGREE_MARK_RE.search(t) and not re.search(r"(Master|Doctor)", c.get("title_en") or ""):
                    # title names no degree; its level was inferred by the LLM
                    quarantine.append({**c, "reason": "title has no degree marker"})
                    n_q += 1
                    continue
                dept = norm_title(c.get("department_th"))
                if FACULTY_RE.match(dept):
                    c["faculty_th"], c["faculty"] = dept, c.get("department") or ""
                else:
                    opts = dept_faculty.get((u, dept), set()) if dept else set()
                    if len(opts) != 1:
                        quarantine.append({**c, "reason": "faculty_th unresolved"})
                        n_q += 1
                        continue
                    c["faculty_th"], c["faculty"] = next(iter(opts))
                deg = "msc" if d == "ปริญญาโท" else "phd"
                n = 1
                while f"phase4_{key}_{deg}_{n:02d}" in existing_ids:
                    n += 1
                c["id"] = f"phase4_{key}_{deg}_{n:02d}"
                existing_ids.add(c["id"])
                c["duration_years"] = normalize_duration(c)
                if (c.get("title_en") or "").strip() == t:
                    c["title_en"] = None  # reducer copies title_th when no English title exists
                to_insert.append(c)
                n_new += 1
            stats[key] = {"grad_candidates": len(kept), "new": n_new, "fill_existing": n_fill, "quarantined": n_q}

        print(json.dumps(stats, ensure_ascii=False))
        (PHASE4_DIR / "ingest_plan.json").write_text(json.dumps(
            {"insert": to_insert, "fill": fills}, ensure_ascii=False, indent=1), encoding="utf-8")
        (PHASE4_DIR / "quarantine_unresolved_faculty.json").write_text(
            json.dumps(quarantine, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"insert={len(to_insert)} fill={len(fills)} quarantine={len(quarantine)}")
        if not apply:
            print("DRY-RUN only — re-run with --apply to execute.")
            return

        from app.core.embedding_service import embedding_service

        def embed(c):
            try:
                vec = embedding_service.get_embedding(build_embedding_text(c))
                return vec if isinstance(vec, list) and len(vec) == 768 else None
            except Exception as e:
                logger.warning(f"embed fail {c['id']}: {str(e)[:120]}")
                return None

        with ThreadPoolExecutor(max_workers=6) as ex:
            vecs = list(ex.map(embed, to_insert))
        for c, vec in zip(to_insert, vecs):
            session.add(CourseDB(
                id=c["id"], title_th=c["title_th"], title_en=c.get("title_en"),
                degree_level=c["degree_level"], degree_name=c.get("degree_name"),
                university=c.get("university"), university_th=c.get("university_th"),
                faculty=c.get("faculty"), faculty_th=c.get("faculty_th"),
                department=c.get("department"), department_th=c.get("department_th"),
                program_type=c.get("program_type") or "ภาคปกติ",
                duration_years=c.get("duration_years"),
                total_credits=c.get("total_credits") if has_credits(c.get("total_credits")) else None,
                tuition_per_semester=c.get("tuition_per_semester") or None,
                tuition_total=c.get("tuition_total") or None,
                description=c.get("description"),
                curriculum_highlights=c.get("curriculum_highlights") or [],
                career_paths=c.get("career_paths") or [],
                tags=c.get("tags") or [],
                website_url=c.get("website_url"),
                embedding_text=build_embedding_text(c), embedding=vec,
            ))
        for cid, patch in fills.items():
            session.query(CourseDB).filter(CourseDB.id == cid).update(patch)
        session.commit()
        null_emb = sum(v is None for v in vecs)
        print(f"APPLIED insert={len(to_insert)} (null_emb={null_emb}) fill={len(fills)}")
    finally:
        session.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase 4 graduate course ingestion")
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
