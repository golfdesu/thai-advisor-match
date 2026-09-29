# -*- coding: utf-8 -*-
"""
Ingest Phase 1 Graduate Courses (โท/เอก) for 5 Top Missing Universities:
  1. Walailak University (WU - มหาวิทยาลัยวลัยลักษณ์)
  2. Thaksin University (TSU - มหาวิทยาลัยทักษิณ)
  3. Srinakharinwirot University (SWU - มหาวิทยาลัยศรีนครินทรวิโรฒ)
  4. University of Phayao (UP - มหาวิทยาลัยพะเยา)
  5. Suranaree University of Technology (SUT - มหาวิทยาลัยเทคโนโลยีสุรนารี)

Features:
- Academic major extraction and clean_major normalization.
- RapidFuzz >= 88 major-level deduplication against existing database courses and within batch.
- High-quality faculty attribution and degree title normalization.
- 768-dimensional Gemini vector embedding generation via embedding_service.
- Non-blocking circuit breaker with retry and graceful degradation.
- Atomic batch commit to local PostgreSQL (courses table).
"""
import os
import sys
import re
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_phase1")

RAW_DATA_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "phase1_courses_raw.json")

# Faculty mapping normalizations for SWU and UP
SWU_FACULTY_RULES = [
    (r"นิติศาสตร|นโยบาย|การฑูต|การท่องเที่ยว", "คณะสังคมศาสตร์", "Faculty of Social Sciences"),
    (r"จิตวิทยา|พฤติกรรมศาสตร์|ความต้องการพิเศษ|การศึกษา|การสอน|กศ\.|การเรียนรู้", "คณะศึกษาศาสตร์", "Faculty of Education"),
    (r"ออกแบบเพื่อธุรกิจ|แฟชั่น|แบรนด์สร้างสรรค์|อุตสาหกรรมสร้างสรรค์", "วิทยาลัยอุตสาหกรรมสร้างสรรค์", "College of Creative Industry"),
    (r"ดุริยางคศาสตร์|ศิลปวัฒนธรรม|ทัศนศิลป์", "คณะศิลปกรรมศาสตร์", "Faculty of Fine Arts"),
    (r"เศรษฐศาสตร์|บริหารธุรกิจ", "คณะบริหารธุรกิจเพื่อสังคม", "Faculty of Business Administration for Society"),
    (r"กีฬา|นันทนาการ|พลศึกษา", "คณะศึกษาศาสตร์", "Faculty of Education"),
    (r"ส่งเสริมสุขภาพ|กายภาพบำบัด", "คณะกายภาพบำบัด", "Faculty of Physical Therapy"),
    (r"เคมี|ฟิสิกส์|ชีว|คณิต|วิทยาศาสตร์|วัสดุ", "คณะวิทยาศาสตร์", "Faculty of Science"),
    (r"วิศวกรรม", "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (r"พยาบาล", "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (r"แพทย์|ตจวิทยา", "คณะแพทยศาสตร์", "Faculty of Medicine"),
    (r"ทันต", "คณะทันตแพทยศาสตร์", "Faculty of Dentistry"),
    (r"เภสัช", "คณะเภสัชศาสตร์", "Faculty of Pharmacy"),
    (r"สื่อ|ภาพยนตร์", "วิทยาลัยนวัตกรรมสื่อสารสังคม", "College of Social Communication Innovation"),
    (r"เกษตร|อาหาร", "คณะเทคโนโลยีและนวัตกรรมผลิตภัณฑ์การเกษตร", "Faculty of Agricultural Product Innovation and Technology"),
]

UP_FACULTY_RULES = [
    (r"บริหารธุรกิจ|การจัดการ|การท่องเที่ยว|นิเทศ", "คณะบริหารธุรกิจและนิเทศศาสตร์", "School of Business and Communication Arts"),
    (r"การศึกษา|การบริหารการศึกษา|หลักสูตรและการสอน", "วิทยาลัยการศึกษา", "School of Education"),
    (r"สถาปัตยกรรม|ศิลปกรรม", "คณะสถาปัตยกรรมศาสตร์และศิลปกรรมศาสตร์", "School of Architecture and Fine Arts"),
]

UNI_CODE_MAP = {
    "มหาวิทยาลัยวลัยลักษณ์": "wu",
    "มหาวิทยาลัยทักษิณ": "tsu",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "swu",
    "มหาวิทยาลัยพะเยา": "up",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": "sut"
}

def clean_major(t):
    if not t:
        return ""
    m = re.search(r"สาขาวิชา(.*?)$", t)
    maj = m.group(1).strip() if m else t
    maj = re.sub(r"\(.*?\)", "", maj)
    maj = re.sub(r"(แบบ\s*[ก-ฮ0-9\.]+|แผน\s*[ก-ฮ0-9\.]+|ภาคปกติ|ภาคพิเศษ|นานาชาติ|โครงการพิเศษ)", "", maj).strip()
    return re.sub(r"\s+", " ", maj)

def clean_course_item(c):
    title = (c.get("title_th") or "").strip()
    title = re.sub(r"\s+", " ", title)

    # Filter out header artifacts
    if not title or title in ("หลักสูตร/สาขาวิชา", "สาขาวิชา") or title.endswith(" สาขาวิชา"):
        if title == "หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชา":
            title = "หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชาบริหารธุรกิจ"
        else:
            return None

    # Normalize duplicate or redundant major strings
    title = re.sub(r"สาขาวิชานิติศาสตรมหาบัณฑิต", "สาขาวิชานิติศาสตร์", title)
    title = re.sub(r"สาขาวิชานิติศาสตรดุษฎีบัณฑิต", "สาขาวิชานิติศาสตร์", title)
    title = re.sub(r"\s*\(ห้องเรียนวิทยาเขต.*?\)", "", title)
    title = title.strip()

    c["title_th"] = title
    u = c.get("university_th", "")

    # SWU Faculty refinement
    if u == "มหาวิทยาลัยศรีนครินทรวิโรฒ" and c.get("faculty_th") == "บัณฑิตวิทยาลัย":
        for pat, fac_th, fac_en in SWU_FACULTY_RULES:
            if re.search(pat, title):
                c["faculty_th"] = fac_th
                c["faculty"] = fac_en
                break

    # UP Faculty refinement
    if u == "มหาวิทยาลัยพะเยา":
        for pat, fac_th, fac_en in UP_FACULTY_RULES:
            if re.search(pat, title):
                c["faculty_th"] = fac_th
                c["faculty"] = fac_en
                break

    # Normalize duration
    dur = (c.get("duration_years") or "").strip()
    if dur in ("4 ปี", "", "-"):
        c["duration_years"] = "2 ปี" if c.get("degree_level") == "ปริญญาโท" else "3 ปี"

    return c

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

def main(dry_run=False):
    logger.info(f"=== Starting Phase 1 Graduate Course Ingestion (Dry Run: {dry_run}) ===")

    if not os.path.exists(RAW_DATA_PATH):
        logger.error(f"Raw data file not found: {RAW_DATA_PATH}")
        return

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_courses = json.load(f)
    logger.info(f"Loaded {len(raw_courses)} raw courses from checkpoint.")

    session = SessionLocal()
    try:
        # Load existing courses
        existing_ids = {r[0] for r in session.query(CourseDB.id).all()}
        existing_rows = session.query(
            CourseDB.title_th, CourseDB.university_th, CourseDB.degree_level, CourseDB.faculty_th
        ).all()

        existing_set = set()
        for t, u, d, f in existing_rows:
            maj = clean_major(t)
            norm_t = re.sub(r"\s+", " ", t or "").strip()
            existing_set.add((maj, u, d))
            existing_set.add((norm_t, u, d))

        # Stage 1: Clean and filter candidates
        valid_candidates = []
        for c in raw_courses:
            cleaned = clean_course_item(c)
            if cleaned:
                valid_candidates.append(cleaned)
        logger.info(f"Cleaned candidates: {len(valid_candidates)} (filtered out {len(raw_courses) - len(valid_candidates)})")

        # Stage 2: Deduplicate against database and within batch using clean_major + RapidFuzz
        to_insert = []
        skipped_exact = 0
        skipped_fuzzy_db = 0
        skipped_fuzzy_batch = 0

        for c in valid_candidates:
            t = c["title_th"]
            u = c["university_th"]
            d = c["degree_level"]
            f = c["faculty_th"]
            maj = clean_major(t)

            if not maj:
                continue

            # Exact DB check (by full title or clean major)
            if (t, u, d) in existing_set or (maj, u, d) in existing_set:
                skipped_exact += 1
                continue

            # Fuzzy DB check
            fuzzy_dup = False
            for ex_maj, ex_u, ex_d in existing_set:
                if ex_u == u and ex_d == d and len(maj) > 3 and len(ex_maj) > 3:
                    ratio = fuzz.token_sort_ratio(maj, ex_maj)
                    if ratio >= 88:
                        fuzzy_dup = True
                        logger.info(f"SKIP DB fuzzy-dup ({ratio}%): '{t}' (major: '{maj}') matches existing '{ex_maj}'")
                        break
            if fuzzy_dup:
                skipped_fuzzy_db += 1
                continue

            # Fuzzy batch check (dedup within to_insert)
            batch_dup = False
            for k in to_insert:
                if k["university_th"] == u and k["degree_level"] == d:
                    ins_maj = clean_major(k["title_th"])
                    if maj == ins_maj or (len(maj) > 3 and len(ins_maj) > 3 and fuzz.token_sort_ratio(maj, ins_maj) >= 88):
                        batch_dup = True
                        logger.info(f"SKIP batch fuzzy-dup: '{t}' matches batch '{k['title_th']}'")
                        break
            if batch_dup:
                skipped_fuzzy_batch += 1
                continue

            # Generate unique ID
            uni_prefix = UNI_CODE_MAP.get(u, "grad")
            deg_prefix = "doc" if d == "ปริญญาเอก" else "grad"
            idx = 1
            cid = f"{uni_prefix}_{deg_prefix}_{idx:03d}"
            while cid in existing_ids:
                idx += 1
                cid = f"{uni_prefix}_{deg_prefix}_{idx:03d}"
            existing_ids.add(cid)
            c["id"] = cid

            existing_set.add((t, u, d))
            existing_set.add((maj, u, d))
            to_insert.append(c)

        logger.info(f"Deduplication summary: Valid Candidates={len(valid_candidates)}, Skipped Exact={skipped_exact}, Skipped DB Fuzzy={skipped_fuzzy_db}, Skipped Batch Fuzzy={skipped_fuzzy_batch}, Unique To Insert={len(to_insert)}")

        # Breakdown by university
        from collections import Counter
        uni_breakdown = Counter(c["university_th"] for c in to_insert)
        for u, count in uni_breakdown.items():
            lvl_counts = Counter(c["degree_level"] for c in to_insert if c["university_th"] == u)
            logger.info(f"  -> {u}: {count} new courses ({dict(lvl_counts)})")

        if dry_run:
            logger.info("DRY RUN mode: No database changes made.")
            return

        # Stage 3: Embedding generation via ThreadPoolExecutor
        logger.info(f"Generating 768-dim embeddings for {len(to_insert)} courses...")

        def embed_course(c):
            txt = build_embedding_text(c)
            for attempt in range(3):
                try:
                    vec = embedding_service.get_embedding(txt)
                    if isinstance(vec, list) and len(vec) == 768:
                        return (c["id"], txt, vec)
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"Embedding attempt {attempt+1} failed for {c['id']}: {e}")
                    time.sleep(2.0 * (attempt + 1))
            # Fallback circuit breaker
            logger.error(f"Fallback to zero-vector for {c['id']}")
            return (c["id"], txt, [0.0] * 768)

        emb_results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_c = {executor.submit(embed_course, c): c for c in to_insert}
            for future in as_completed(future_to_c):
                cid, txt, vec = future.result()
                emb_results[cid] = (txt, vec)

        # Stage 4: Atomic Database Commit
        logger.info(f"Committing {len(to_insert)} new courses to PostgreSQL...")
        for c in to_insert:
            txt, vec = emb_results[c["id"]]
            course_obj = CourseDB(
                id=c["id"],
                title_th=c["title_th"],
                title_en=c.get("title_en"),
                degree_level=c["degree_level"],
                degree_name=c.get("degree_name"),
                university=c.get("university"),
                university_th=c["university_th"],
                faculty=c.get("faculty"),
                faculty_th=c.get("faculty_th"),
                department=c.get("department", ""),
                department_th=c.get("department_th", ""),
                program_type=c.get("program_type", "ภาคปกติ"),
                duration_years=c.get("duration_years", "2 ปี"),
                total_credits=c.get("total_credits", ""),
                tuition_per_semester=c.get("tuition_per_semester", ""),
                tuition_total=c.get("tuition_total", ""),
                description=c.get("description", ""),
                curriculum_highlights=c.get("curriculum_highlights") or [],
                career_paths=c.get("career_paths") or [],
                tags=c.get("tags") or [],
                website_url=c.get("website_url", ""),
                embedding_text=txt,
                embedding=vec
            )
            session.add(course_obj)

        session.commit()
        logger.info(f"SUCCESS: Successfully inserted {len(to_insert)} graduate courses into database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    main(dry_run=is_dry)
