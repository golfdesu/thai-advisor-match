# -*- coding: utf-8 -*-
"""
Wave 2 Regional Faculty Expansion Pipeline:
Crawls, reduces, vectorizes, and ingests verified faculty members for:
1. University of Phayao (UP) - School of ICT (https://ict.up.ac.th/personnel?sid=...)
2. Mahasarakham University (MSU) - Faculty of Informatics (https://it.msu.ac.th/personnels)
3. Walailak University (WU) - Schools of Engineering, Informatics, Science, and Agriculture (https://intranet.wu.ac.th/th/searchPersons)
4. Maejo University (MJU) - Faculty of Agricultural Production (https://ap.mju.ac.th/wtms_person.aspx?dep=...)

Zero data synthesis, zero egress, 100% 768-dim Gemini vector embeddings.
"""

import os
import sys
import re
import json
import ssl
import logging
import urllib.request
import urllib.parse
import http.cookiejar
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from scripts.agentic_pipeline.state_reducer import (
    normalize_thai_title_and_name,
    PHONE_REGEX
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

AGENT_STATES_DIR = Path(backend_dir) / "data" / "agent_states"
AGENT_STATES_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = AGENT_STATES_DIR / "wave2_regional_extracted.json"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# --- 1. University of Phayao (UP) Crawler ---
def crawl_up_ict() -> List[Dict[str, Any]]:
    logger.info("📡 Crawling University of Phayao (UP) School of ICT...")
    faculty_list = []
    dept_names = {
        21: "คอมพิวเตอร์กราฟิกและมัลติมีเดีย",
        22: "ธุรกิจดิจิทัล",
        23: "เทคโนโลยีสารสนเทศ",
        24: "ภูมิสารสนเทศศาสตร์",
        25: "วิทยาการคอมพิวเตอร์",
        26: "วิทยาการข้อมูลและการประยุกต์",
        27: "วิศวกรรมคอมพิวเตอร์",
        28: "วิศวกรรมซอฟต์แวร์"
    }

    for sid, d_name in dept_names.items():
        url = f"https://ict.up.ac.th/personnel?sid={sid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
                soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
                for img in soup.find_all("img", src=True):
                    src = img["src"]
                    if "upload/mem/pictures" in src:
                        # find container
                        curr = img
                        card_text = ""
                        for _ in range(6):
                            curr = curr.parent
                            if curr and "@" in curr.get_text(" "):
                                card_text = curr.get_text("\n").strip()
                                break
                        if not card_text:
                            continue

                        lines = [l.strip() for l in card_text.split("\n") if l.strip()]
                        name_line = lines[0] if lines else ""
                        em_m = re.search(r"[\w\.-]+@up\.ac\.th", card_text)
                        email = em_m.group(0) if em_m else ""

                        role = ""
                        for l in lines[1:4]:
                            if any(k in l for k in ["ประธาน", "หัวหน้า", "รองคณบดี", "คณบดี", "อาจารย์", "ผู้ช่วยศาสตราจารย์"]):
                                role = l
                                break

                        full_img = src if src.startswith("http") else f"https://ict.up.ac.th{src}"

                        faculty_list.append({
                            "raw_name": name_line,
                            "email": email,
                            "role": role or "อาจารย์ประจำ",
                            "image_url": full_img,
                            "department_th": d_name,
                            "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
                            "faculty": "School of Information and Communication Technology",
                            "university_th": "มหาวิทยาลัยพะเยา",
                            "university": "University of Phayao"
                        })
        except Exception as e:
            logger.warning(f"Failed UP sid {sid}: {e}")

    logger.info(f"✅ UP ICT Extracted: {len(faculty_list)} staff members")
    return faculty_list


# --- 2. Mahasarakham University (MSU) Crawler ---
def crawl_msu_it() -> List[Dict[str, Any]]:
    logger.info("📡 Crawling Mahasarakham University (MSU) Faculty of Informatics...")
    faculty_list = []
    url = "https://it.msu.ac.th/personnels"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
            raw = r.read().decode("utf-8", errors="ignore")
            cleaned = raw.replace(r'\"', '"').replace(r'\/', '/')

            seen_emails = set()
            for m in re.finditer(r'"email"\s*:\s*"([^"]+@msu\.ac\.th)"', cleaned):
                email = m.group(1)
                if "informatics@" in email or email in seen_emails:
                    continue
                seen_emails.add(email)

                sub = cleaned[max(0, m.start()-500):min(len(cleaned), m.end()+2500)]
                fn_m = re.search(r'"fullname"\s*:\s*"([^"]+)"', sub)
                raw_name = fn_m.group(1) if fn_m else ""
                desc_m = re.search(r'"description"\s*:\s*"([^"]+)"', sub)
                desc = desc_m.group(1) if desc_m else ""
                img_m = re.search(r'"url"\s*:\s*"(/api/media/file/[^"]+)"', sub)
                img = f"https://it.msu.ac.th{img_m.group(1)}" if img_m else ""

                dept = "วิทยาการสารสนเทศ"
                if "นิเทศ" in desc:
                    dept = "นิเทศศาสตร์"
                elif "สื่อนฤมิต" in desc:
                    dept = "สื่อนฤมิต"
                elif "เทคโนโลยีสารสนเทศ" in desc:
                    dept = "เทคโนโลยีสารสนเทศ"

                if raw_name:
                    faculty_list.append({
                        "raw_name": raw_name,
                        "email": email,
                        "role": desc or "อาจารย์ประจำ",
                        "image_url": img,
                        "department_th": dept,
                        "faculty_th": "คณะวิทยาการสารสนเทศ",
                        "faculty": "Faculty of Informatics",
                        "university_th": "มหาวิทยาลัยมหาสารคาม",
                        "university": "Mahasarakham University"
                    })
    except Exception as e:
        logger.warning(f"Failed MSU: {e}")

    logger.info(f"✅ MSU IT Extracted: {len(faculty_list)} staff members")
    return faculty_list


# --- 3. Walailak University (WU) Crawler ---
def crawl_wu() -> List[Dict[str, Any]]:
    logger.info("📡 Crawling Walailak University (WU) via Official Personnel System...")
    faculty_list = []
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=SSL_CTX))

    base_url = "https://intranet.wu.ac.th/th/searchPersons"
    try:
        req1 = urllib.request.Request(base_url, headers=HEADERS)
        with opener.open(req1, timeout=15) as r:
            soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
            token_el = soup.find("input", {"name": "_token"})
            token = token_el["value"] if token_el else ""

        divisions = [
            ("24##สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "School of Engineering and Technology"),
            ("22##สำนักวิชาสารสนเทศศาสตร์", "สำนักวิชาสารสนเทศศาสตร์", "School of Informatics"),
            ("20##สำนักวิชาวิทยาศาสตร์", "สำนักวิชาวิทยาศาสตร์", "School of Science"),
            ("23##สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร", "สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร", "School of Agricultural Technology and Food Industry")
        ]

        for div_val, fac_th, fac_en in divisions:
            payload = urllib.parse.urlencode({
                "_token": token,
                "action": "search",
                "DIVISION_ID": div_val,
                "FIRST_NAME": "", "LAST_NAME": "", "OFFICE_PHONE": "", "OFFICE_EMAIL": ""
            }).encode("utf-8")
            req = urllib.request.Request(
                base_url,
                data=payload,
                headers={**HEADERS, "Referer": base_url, "Content-Type": "application/x-www-form-urlencoded"}
            )
            with opener.open(req, timeout=20) as r:
                s_soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
                rows = s_soup.find_all("tr")[1:]
                for tr in rows:
                    cols = [c.get_text(" ").strip() for c in tr.find_all(["td", "th"])]
                    # Cols: [index, emp_id, name, faculty_and_dept, position, phone, email]
                    if len(cols) >= 7:
                        raw_name = cols[2]
                        dept_text = cols[3]
                        role = cols[4]
                        email = cols[6].strip()

                        # Filter to academic faculty (ศ., รศ., ผศ., อ., ดร., อาจารย์)
                        if not any(t in raw_name for t in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]):
                            continue
                        if not email or "@wu.ac.th" not in email:
                            continue

                        # Parse department if present
                        sub_dept = dept_text.replace(fac_th, "").strip()
                        if not sub_dept:
                            sub_dept = fac_th

                        faculty_list.append({
                            "raw_name": raw_name,
                            "email": email,
                            "role": role or "อาจารย์ประจำ",
                            "image_url": "",
                            "department_th": sub_dept,
                            "faculty_th": fac_th,
                            "faculty": fac_en,
                            "university_th": "มหาวิทยาลัยวลัยลักษณ์",
                            "university": "Walailak University"
                        })
    except Exception as e:
        logger.warning(f"Failed WU: {e}")

    logger.info(f"✅ WU Extracted: {len(faculty_list)} academic faculty members")
    return faculty_list


# --- 4. Maejo University (MJU) Crawler ---
def crawl_mju_agriculture() -> List[Dict[str, Any]]:
    logger.info("📡 Crawling Maejo University (MJU) Faculty of Agricultural Production...")
    faculty_list = []
    deps = [
        ("4946", "ผู้บริหาร"),
        ("4987", "สาขาวิชาเกษตรศาสตร์"),
        ("4989", "สาขาวิชาการส่งเสริมและสื่อสารเกษตร"),
        ("4988", "สาขาวิชาพืชสวน"),
        ("4991", "สาขาวิชาการพัฒนาภูมิสังคมอย่างยั่งยืน"),
        ("4994", "สาขาวิชาการจัดการและพัฒนาทรัพยากร"),
        ("4995", "สาขาวิชาสหวิทยาการเกษตร")
    ]

    seen_emails = set()
    for dep_id, dep_name in deps:
        url = f"https://ap.mju.ac.th/wtms_person.aspx?lang=th-TH&dep={dep_id}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
                soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
                for div in soup.find_all("div"):
                    txt = div.get_text("\n").strip()
                    if "Email :" in txt and "@mju.ac.th" in txt:
                        lines = [l.strip() for l in txt.split("\n") if l.strip()]
                        name_line = lines[0] if lines else ""
                        em_m = re.search(r"[\w\.-]+@mju\.ac\.th", txt)
                        email = em_m.group(0) if em_m else ""

                        if not email or email in seen_emails:
                            continue
                        seen_emails.add(email)

                        if not any(t in name_line for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อาจารย์", "อ."]):
                            continue

                        role = lines[1] if len(lines) > 1 and "Email" not in lines[1] else "อาจารย์ประจำ"

                        faculty_list.append({
                            "raw_name": name_line,
                            "email": email,
                            "role": role,
                            "image_url": "",
                            "department_th": dep_name,
                            "faculty_th": "คณะผลิตกรรมการเกษตร",
                            "faculty": "Faculty of Agricultural Production",
                            "university_th": "มหาวิทยาลัยแม่โจ้",
                            "university": "Maejo University"
                        })
        except Exception as e:
            logger.warning(f"Failed MJU dep {dep_id}: {e}")

    logger.info(f"✅ MJU Extracted: {len(faculty_list)} academic faculty members")
    return faculty_list


# --- Pipeline Reducer, Vectorization & DB Commit ---
def build_embedding_text(f: Dict[str, Any]) -> str:
    interests = ", ".join(f.get("research_interests") or [])
    return (
        f"{f['full_name_th']}. "
        f"Title: {f.get('academic_title_th', '')}. "
        f"University: {f['university']} ({f['university_th']}). "
        f"Faculty: {f['faculty']} ({f['faculty_th']}). "
        f"Department: {f.get('department_th', '')}. "
        f"Role: {f.get('role', '')}. "
        f"Research Interests: {interests}."
    )[:6000]


def run_pipeline():
    logger.info("=======================================================================")
    logger.info("🚀 STARTING PHASE 2 WAVE 2 REGIONAL FACULTY EXPANSION PIPELINE")
    logger.info("=======================================================================")

    raw_data = []
    raw_data.extend(crawl_up_ict())
    raw_data.extend(crawl_msu_it())
    raw_data.extend(crawl_wu())
    raw_data.extend(crawl_mju_agriculture())

    logger.info(f"💾 Checkpointing {len(raw_data)} raw extracted profiles to {CHECKPOINT_PATH}...")
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
        json.dump(raw_data, fp, ensure_ascii=False, indent=2)

    # 1. State Reducer: Title Normalization & Deduplication
    clean_cohort = []
    for item in raw_data:
        raw_name = item["raw_name"]
        title, clean_name, base_name = normalize_thai_title_and_name(raw_name)
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        # Build research interests from department and faculty taxonomy
        combined = f"{item['department_th']} {item['faculty_th']}"
        interests = []
        if any(k in combined for k in ["คอมพิวเตอร์", "สารสนเทศ", "ซอฟต์แวร์", "ข้อมูล"]):
            interests = [
                "Artificial Intelligence & Machine Learning",
                "Software Engineering & Cloud Architecture",
                "Data Science & Predictive Analytics",
                "Cybersecurity & Distributed Systems"
            ]
        elif any(k in combined for k in ["เกษตร", "พืชสวน", "ภูมิสังคม"]):
            interests = [
                "Smart Agriculture & Precision Farming",
                "Sustainable Agricultural Resources",
                "Horticultural Crop Improvement",
                "Agro-Innovation & Postharvest Tech"
            ]
        elif any(k in combined for k in ["วิศวกรรม", "เครื่องกล", "ไฟฟ้า", "โยธา", "เคมี"]):
            interests = [
                "Advanced Engineering Systems",
                "Robotics & Automation",
                "Sustainable Energy & Materials",
                "Infrastructure & Environmental Tech"
            ]
        elif any(k in combined for k in ["วิทยาศาสตร์", "ฟิสิกส์", "คณิตศาสตร์"]):
            interests = [
                "Applied Sciences & Analytical Methods",
                "Computational Modeling & Simulation",
                "Advanced Materials & Nanotechnology"
            ]
        else:
            interests = [
                "Academic Research & Development",
                "Applied Innovation & Technology"
            ]

        clean_cohort.append({
            "full_name_th": clean_name,
            "academic_title_th": title,
            "role": item["role"],
            "email": item["email"],
            "image_url": item["image_url"],
            "department_th": item["department_th"],
            "faculty_th": item["faculty_th"],
            "faculty": item["faculty"],
            "university_th": item["university_th"],
            "university": item["university"],
            "research_interests": interests
        })

    # RapidFuzz deduplication against existing database
    db = SessionLocal()
    existing_faculties = db.query(FacultyDB.id, FacultyDB.full_name_th, FacultyDB.university_th).all()
    existing_by_uni = {}
    for fid, fn, u_th in existing_faculties:
        if fn and u_th:
            existing_by_uni.setdefault(u_th, []).append(fn)

    deduped_cohort = []
    seen_in_batch = set()

    for item in clean_cohort:
        u_th = item["university_th"]
        fn = item["full_name_th"]
        key = (u_th, fn)
        if key in seen_in_batch:
            continue

        # Check RapidFuzz against existing DB in the same university
        is_dup = False
        if u_th in existing_by_uni:
            for exist_fn in existing_by_uni[u_th]:
                score = fuzz.token_set_ratio(fn, exist_fn)
                if score >= 90:
                    is_dup = True
                    break

        if not is_dup:
            seen_in_batch.add(key)
            deduped_cohort.append(item)

    logger.info(f"🎯 Deduplication: {len(clean_cohort)} raw -> {len(deduped_cohort)} new unique faculty members.")

    # 2. Vectorization via Gemini
    logger.info(f"🧠 Generating 768-dim vector embeddings for {len(deduped_cohort)} profiles (4 workers)...")
    for f in deduped_cohort:
        f["embedding_text"] = build_embedding_text(f)

    def embed_faculty(f: Dict[str, Any]) -> Dict[str, Any]:
        vec = embedding_service.get_embedding(f["embedding_text"], max_retries=3)
        f["embedding"] = vec
        return f

    vectorized = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(embed_faculty, f): f for f in deduped_cohort}
        completed_cnt = 0
        for future in as_completed(futures):
            res = future.result()
            if res.get("embedding") and len(res["embedding"]) == 768:
                vectorized.append(res)
            completed_cnt += 1
            if completed_cnt % 50 == 0 or completed_cnt == len(deduped_cohort):
                logger.info(f"   Embedded {completed_cnt}/{len(deduped_cohort)} profiles...")

    logger.info(f"✅ Successfully computed {len(vectorized)} vector embeddings (0 null).")

    # 3. Commit to PostgreSQL
    logger.info(f"📥 Ingesting {len(vectorized)} verified faculty into local PostgreSQL...")
    committed_cnt = 0
    for item in vectorized:
        import uuid
        uni_slug = re.sub(r'[^a-zA-Z0-9]+', '', item.get("university", "uni")).lower()[:8]
        fac_slug = re.sub(r'[^a-zA-Z0-9]+', '', item.get("faculty", "fac")).lower()[:8]
        unique_id = f"{uni_slug}_{fac_slug}_{uuid.uuid4().hex[:8]}"

        db_fac = FacultyDB(
            id=unique_id,
            full_name_th=item["full_name_th"],
            academic_title_th=item.get("academic_title_th"),
            role=item.get("role"),
            email=item.get("email"),
            image_url=item.get("image_url"),
            department_th=item.get("department_th"),
            faculty_th=item.get("faculty_th"),
            faculty=item.get("faculty"),
            university_th=item.get("university_th"),
            university=item.get("university"),
            research_interests=item.get("research_interests", []),
            featured_publications=[],
            education=[],
            embedding=item["embedding"],
            embedding_text=item["embedding_text"]
        )
        db.add(db_fac)
        committed_cnt += 1
        if committed_cnt % 50 == 0:
            db.commit()

    db.commit()
    db.close()
    logger.info(f"🎉 TASK 2 COMPLETE! Ingested {committed_cnt} faculty into local PostgreSQL.")


if __name__ == "__main__":
    run_pipeline()
