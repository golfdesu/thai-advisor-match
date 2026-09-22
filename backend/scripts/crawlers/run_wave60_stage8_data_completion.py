"""
Wave 60 Stage 8: Autonomous Multi-Source Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"ทำ stage 8 เลย / ทำต่อ stage 9 10 11 12 โดยไม่ต้องขอ approve"

Actions:
1. Silpakorn University Faculty of Science (Biology):
   Harvests bio.sc.su.ac.th/personnel & personnel-in-english -> 30+ faculty with
   matched Thai/English names, academic titles, portraits, and department affiliations.
2. Silpakorn University Faculty of Science (Computing):
   Harvests cp.su.ac.th/teacher and individual profiles -> 19+ faculty with
   Thai/English names, exact @su.ac.th emails, portraits, and department affiliations.
3. Silpakorn University Faculty of Science (Physics Fixes):
   Resolves Dr. Jarungsang Laksanaboonsong (ผศ.ดร. จรุงแสง ลักษณบุญส่ง) and
   Dr. Chawarat Siriwong from phy.sc.su.ac.th/people.html.
4. SWU Faculty of Dentistry (5 Departments):
   Harvests dent.swu.ac.th (tabid=17201, 17202, 17198, 17200, 17199) -> 84 faculty
   with normalized Thai titles, portrait image URLs, romanized first names, and departments.
5. SWU Faculty of Education (8 Departments):
   Harvests edu.swu.ac.th/institute/{curriculum-and-instruction, edad, gep, edtech, ...}
   -> portraits, normalized titles, and department affiliations.
6. Burapha University Faculty of Pharmacy (5 Departments):
   Harvests pharm.buu.ac.th/department-teacher.php?id={1, 3, 4, 5, 10} -> 30+ faculty
   with institutional emails, portrait URLs, titles, and departments.
7. Multi-University Email Decoupling & Typo Fixing (Pass 4):
   Decouples trailing initials from first names (e.g. teerapond -> Teerapon),
   fixes corrupted email syntax (e.g. taimpaga@.tu.ac.th -> taimpaga@tu.ac.th).
8. Checkpoints execution state to backend/data/agent_states/wave60_stage8_data_completion_snapshot.json.
"""

import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def clean_name_token(token: str) -> str:
    """Cleans punctuation, digits, or extraneous artifacts from a romanized name token."""
    cleaned = re.sub(r"[^A-Za-z\-]", "", token).strip()
    return cleaned.title() if len(cleaned) >= 2 else ""


# ---------------------------------------------------------------------------
# Action 1: Silpakorn University Faculty of Science (Biology)
# ---------------------------------------------------------------------------
def execute_silpakorn_biology(db) -> int:
    print("\n--- Action 1: Harvesting Silpakorn Science (Biology) ---")
    bio_roster = []

    # 1. Fetch Thai personnel list
    th_map = {}
    try:
        url_th = "http://bio.sc.su.ac.th/personnel"
        req = urllib.request.Request(url_th, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "profile/" in href:
                    slug = href.split("profile/")[-1].split("-")[0]
                    raw_name = a.get_text(" ", strip=True)
                    t_th, _, raw_pure = normalize_thai_title_and_name(raw_name)
                    if raw_pure and len(raw_pure.split()) >= 2:
                        img = a.find("img")
                        img_url = None
                        if img and img.get("src"):
                            src = img["src"]
                            img_url = f"http://bio.sc.su.ac.th/{src}" if not src.startswith("http") else src
                        th_map[slug] = {
                            "clean_name": raw_pure,
                            "title_th": t_th,
                            "image_url": img_url,
                        }
    except Exception as e:
        print(f"  Error fetching Silpakorn Biology (TH): {e}")

    # 2. Fetch English personnel list
    try:
        url_en = "http://bio.sc.su.ac.th/personnel-in-english"
        req = urllib.request.Request(url_en, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "profile-in-english/" in href:
                    slug = href.split("profile-in-english/")[-1].split("-")[0]
                    raw_en = a.get_text(" ", strip=True)
                    clean_en = re.sub(r"^(?:(?:Asst|Assoc|Assist)\.?\s*Prof\.?\s*(?:Dr\.?)?|Prof(?:essor)?\.?\s*(?:Dr\.?)?|Dr\.?|Miss\s*)\s*", "", raw_en, flags=re.I).strip()
                    clean_en = clean_en.split(",")[0].strip()
                    parts = [clean_name_token(p) for p in clean_en.split() if len(p) >= 2]
                    if len(parts) >= 2 and slug in th_map:
                        item = th_map[slug]
                        item["fn"] = parts[0]
                        item["ln"] = " ".join(parts[1:])
                        item["dep_th"] = "ภาควิชาชีววิทยา"
                        bio_roster.append(item)
    except Exception as e:
        print(f"  Error fetching Silpakorn Biology (EN): {e}")

    print(f"Harvested {len(bio_roster)} Silpakorn Biology personnel profiles.")

    missing_su_bio = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, first_name, last_name, image_url, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'su_w43%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_fn, cur_ln, cur_img, cur_dep in missing_su_bio:
        _, _, pure_th = normalize_thai_title_and_name(fth)
        match = next((item for item in bio_roster if item["clean_name"] == pure_th), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if match.get("fn") and (not cur_fn or cur_fn != match["fn"]):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if match.get("ln") and (not cur_ln or cur_ln != match["ln"]):
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]
            if not cur_img and match.get("image_url"):
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn Biology records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 2: Silpakorn University Faculty of Science (Computing)
# ---------------------------------------------------------------------------
def execute_silpakorn_computing(db) -> int:
    print("\n--- Action 2: Harvesting Silpakorn Science (Computing) ---")
    cp_roster = []

    try:
        url_cp = "https://cp.su.ac.th/teacher"
        req = urllib.request.Request(url_cp, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            teacher_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.match(r"^https://cp\.su\.ac\.th/teacher/\d+$", href):
                    teacher_links.append(href)

            # Deduplicate URLs
            teacher_links = list(dict.fromkeys(teacher_links))
            for t_url in teacher_links:
                try:
                    t_req = urllib.request.Request(t_url, headers=HEADERS)
                    with urllib.request.urlopen(t_req, context=SSL_CTX, timeout=6) as t_resp:
                        t_soup = BeautifulSoup(t_resp.read().decode("utf-8", errors="ignore"), "html.parser")
                        t_text = t_soup.get_text("\n", strip=True)
                        lines = [l.strip() for l in t_text.splitlines() if l.strip()]

                        th_name, en_name, em_val, img_val = None, None, None, None
                        # Find image
                        for img in t_soup.find_all("img"):
                            src = img.get("src", "")
                            if "crop" in src:
                                img_val = src
                                break

                        # Find email
                        em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu)", t_text, re.I)
                        if em_match:
                            em_val = em_match.group(0).lower()

                        for l in lines:
                            if any(l.startswith(pfx) for pfx in ["ผศ.", "รศ.", "อ.", "ศ."]) and any('฀' <= c <= '๿' for c in l):
                                if not th_name and " " not in l[:4]:
                                    th_name = l
                            elif any(l.startswith(pfx) for pfx in ["Asst.", "Assoc.", "Prof.", "Dr."]) and not any('฀' <= c <= '๿' for c in l):
                                if not en_name:
                                    en_name = l

                        if th_name:
                            t_th, cth, _ = normalize_thai_title_and_name(th_name)
                            fn, ln = None, None
                            if en_name:
                                clean_en = re.sub(r"^(?:(?:Asst|Assoc)\.?\s*Prof\.?\s*(?:Dr\.?)?|Prof\.?\s*(?:Dr\.?)?|Dr\.?)\s*", "", en_name, flags=re.I).strip()
                                parts = [clean_name_token(p) for p in clean_en.split() if len(p) >= 2]
                                if len(parts) >= 2:
                                    fn = parts[0]
                                    ln = " ".join(parts[1:])

                            if cth and len(cth.split()) >= 2:
                                cp_roster.append({
                                    "clean_th": cth,
                                    "title_th": t_th,
                                    "fn": fn,
                                    "ln": ln,
                                    "email": em_val,
                                    "image_url": img_val,
                                    "dep_th": "ภาควิชาคอมพิวเตอร์",
                                })
                except Exception:
                    pass
                time.sleep(0.05)
    except Exception as e:
        print(f"  Error fetching Silpakorn Computing: {e}")

    print(f"Harvested {len(cp_roster)} Silpakorn Computing personnel profiles.")

    missing_su_cp = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, first_name, last_name, email, image_url, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'su_w43%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_fn, cur_ln, cur_em, cur_img, cur_dep in missing_su_cp:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = next((item for item in cp_roster if item["clean_th"] == cth), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_ln and match.get("ln"):
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]
            if not cur_em and match.get("email"):
                sql_parts.append("email = :em")
                updates["em"] = match["email"]
            if not cur_img and match.get("image_url"):
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn Computing records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 3: Silpakorn University Faculty of Science (Physics Fixes)
# ---------------------------------------------------------------------------
def execute_silpakorn_physics_fixes(db) -> int:
    print("\n--- Action 3: Silpakorn Physics Targeted Fixes ---")
    enriched_count = 0

    # 1. Jaroonsang Laksanaboonsong (su_w43_0113_595)
    db.execute(text("""
        UPDATE faculties
        SET first_name = 'Jarungsang',
            last_name = 'Laksanaboonsong',
            academic_title_th = 'ผศ.ดร.',
            department_th = 'ภาควิชาฟิสิกส์'
        WHERE id = 'su_w43_0113_595';
    """))
    enriched_count += 1

    # 2. Chawarat Siriwong (su_w43_0127_489)
    db.execute(text("""
        UPDATE faculties
        SET first_name = 'Chawarat',
            last_name = 'Siriwong',
            academic_title_th = 'ผศ.ดร.',
            department_th = 'ภาควิชาฟิสิกส์'
        WHERE id = 'su_w43_0127_489';
    """))
    enriched_count += 1

    db.commit()
    print(f"Applied {enriched_count} targeted Silpakorn Physics fixes.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 4: SWU Faculty of Dentistry (5 Departments)
# ---------------------------------------------------------------------------
def execute_swu_dentistry(db) -> int:
    print("\n--- Action 4: Harvesting SWU Faculty of Dentistry (5 Departments) ---")
    dent_roster = []

    dept_map = {
        17201: "ภาควิชาทันตกรรมทั่วไป",
        17202: "ภาควิชาทันตกรรมสำหรับเด็กและทันตกรรมป้องกัน",
        17198: "ภาควิชาทันตกรรมอนุรักษ์และทันกรรมประดิษฐ์",
        17200: "ภาควิชาศัลยศาสตร์และเวชศาสตร์ช่องปาก",
        17199: "ภาควิชาโอษฐวิทยา",
    }

    for tid, dep_name in dept_map.items():
        url = f"https://dent.swu.ac.th/Default.aspx?tabid={tid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if any(w in src.lower() for w in ["images/person", "hospital", "wp-content/uploads"]):
                        parent = img.find_parent("table") or img.find_parent("div")
                        txt = parent.get_text(" ", strip=True) if parent else ""
                        if any(noise in txt for noise in ["นักจัดการ", "พนักงาน", "ช่าง", "เจ้าหน้าที่", "Avatar"]):
                            continue

                        # Extract clean thai name
                        m = re.search(r"((?:รศ|ผศ|อ|ศ)\.?(?:ดร\.?)?(?:ทพ|ทพญ)?\.?\s*[ก-๙]+(?:\s+[ก-๙]+)+)", txt)
                        if m:
                            raw = m.group(1)
                            t_th, _, pure_th = normalize_thai_title_and_name(raw)
                            if pure_th and len(pure_th.split()) >= 2:
                                # Extract romanized first name from filename
                                fname = src.split("/")[-1].split("?")[0]
                                clean_slug = re.sub(r"\.(?:jpg|jpeg|png|gif)$", "", fname, flags=re.I)
                                fn = clean_name_token(clean_slug) if clean_slug.isalpha() else None

                                full_img = f"https://dent.swu.ac.th{src}" if src.startswith("/") else src
                                dent_roster.append({
                                    "clean_name": pure_th,
                                    "title_th": t_th,
                                    "fn": fn,
                                    "image_url": full_img,
                                    "dep_th": dep_name,
                                })
        except Exception as e:
            print(f"  Error fetching SWU Dent tab {tid}: {e}")
        time.sleep(0.05)

    print(f"Harvested {len(dent_roster)} SWU Dentistry personnel profiles.")

    missing_swu_dent = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, first_name, last_name, image_url, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ'
          AND (faculty_th = 'คณะทันตแพทยศาสตร์' OR faculty = 'Faculty of Dentistry' OR id LIKE 'swu_w44%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_fn, cur_ln, cur_img, cur_dep, cur_fac in missing_swu_dent:
        _, _, pure_th = normalize_thai_title_and_name(fth)
        match = next((item for item in dent_roster if item["clean_name"] == pure_th), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_img and match.get("image_url"):
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะทันตแพทยศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} SWU Dentistry records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 5: SWU Faculty of Education (8 Departments)
# ---------------------------------------------------------------------------
def execute_swu_education(db) -> int:
    print("\n--- Action 5: Harvesting SWU Faculty of Education (8 Departments) ---")
    edu_roster = []

    depts = [
        ("curriculum-and-instruction", "ภาควิชาหลักสูตรและการสอน"),
        ("edad", "ภาควิชาการบริหารการศึกษาและการอุดมศึกษา"),
        ("gep", "ภาควิชาการแนะแนวและจิตวิทยาการศึกษา"),
        ("edtech", "ภาควิชาเทคโนโลยีการศึกษา"),
        ("industrial-education", "ภาควิชาอุตสาหกรรมศึกษา"),
        ("human-potentials", "ภาควิชาการวัดผลและวิจัยการศึกษา"),
        ("adult-education-and-live-long-learning", "ภาควิชาการศึกษาผู้ใหญ่และการศึกษาตลอดชีวิต"),
        ("special-education", "ภาควิชาการศึกษาพิเศษ"),
    ]

    for slug, dep_name in depts:
        url = f"https://edu.swu.ac.th/institute/{slug}/"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    fname = src.split("/")[-1]
                    clean_slug = re.sub(r"-\d+x\d+\.(?:jpg|png)$", "", fname)
                    clean_slug = re.sub(r"\.(?:jpg|png)$", "", clean_slug)
                    clean_slug = clean_slug.replace("-", " ").replace("_", " ").strip()

                    if any('฀' <= c <= '๿' for c in clean_slug):
                        t_th, cth, _ = normalize_thai_title_and_name(clean_slug)
                        if cth and len(cth.split()) >= 2:
                            edu_roster.append({
                                "clean_th": cth,
                                "title_th": t_th,
                                "image_url": src,
                                "dep_th": dep_name,
                            })
        except Exception as e:
            print(f"  Error fetching SWU Edu {slug}: {e}")
        time.sleep(0.05)

    print(f"Harvested {len(edu_roster)} SWU Education personnel profiles.")

    missing_swu_edu = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ'
          AND (faculty_th = 'คณะศึกษาศาสตร์' OR faculty = 'Faculty of Education' OR id LIKE 'swu_w44%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_dep, cur_fac in missing_swu_edu:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = next((item for item in edu_roster if item["clean_th"] == cth), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_img and match.get("image_url"):
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะศึกษาศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} SWU Education records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 6: Burapha University Faculty of Pharmacy (5 Departments)
# ---------------------------------------------------------------------------
def execute_burapha_pharmacy(db) -> int:
    print("\n--- Action 6: Harvesting Burapha Faculty of Pharmacy (5 Departments) ---")
    pharm_roster = []

    dept_ids = [1, 3, 4, 5, 10]
    for did in dept_ids:
        url = f"https://pharm.buu.ac.th/department-teacher.php?id={did}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"col-", re.I))
                for card in cards:
                    txt = card.get_text("\n", strip=True)
                    if any(t in txt for t in ["ผศ.", "รศ.", "อ.", "ศ."]) and "อีเมล์" in txt:
                        lines = [l.strip() for l in txt.splitlines() if l.strip()]
                        raw_name, em_val, dep_val = None, None, None
                        for i, line in enumerate(lines):
                            if any(line.startswith(pfx) for pfx in ["ผศ.", "รศ.", "อ.", "ศ."]) and not raw_name:
                                raw_name = line
                            if "สาขาวิชา :" in line and i + 1 < len(lines):
                                dep_val = lines[i + 1]
                            if "@" in line and "." in line:
                                em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:go\.)?buu\.ac\.th", line, re.I)
                                if em_match:
                                    em_val = em_match.group(0).lower()

                        img = card.find("img")
                        img_url = None
                        if img and img.get("src"):
                            src = img["src"]
                            img_url = f"https://pharm.buu.ac.th/{src}" if not src.startswith("http") else src

                        if raw_name:
                            t_th, _, pure_th = normalize_thai_title_and_name(raw_name)
                            fn = clean_name_token(em_val.split("@")[0]) if em_val else None
                            if pure_th and len(pure_th.split()) >= 2:
                                pharm_roster.append({
                                    "clean_name": pure_th,
                                    "title_th": t_th,
                                    "fn": fn,
                                    "email": em_val,
                                    "image_url": img_url,
                                    "dep_th": dep_val or "คณะเภสัชศาสตร์",
                                })
        except Exception as e:
            print(f"  Error fetching BUU Pharm dept {did}: {e}")
        time.sleep(0.05)

    print(f"Harvested {len(pharm_roster)} Burapha Pharmacy personnel profiles.")

    missing_buu_pharm = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, first_name, email, image_url, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยบูรพา'
          AND (faculty_th = 'คณะเภสัชศาสตร์' OR faculty = 'Faculty of Pharmacy' OR id LIKE 'buu_w42%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_fn, cur_em, cur_img, cur_dep, cur_fac in missing_buu_pharm:
        _, _, pure_th = normalize_thai_title_and_name(fth)
        match = next((item for item in pharm_roster if item["clean_name"] == pure_th), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_em and match.get("email"):
                sql_parts.append("email = :em")
                updates["em"] = match["email"]
            if not cur_img and match.get("image_url"):
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะเภสัชศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Burapha Pharmacy records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 7: Multi-University Email Decoupling & Typo Fixing (Pass 4)
# ---------------------------------------------------------------------------
def execute_email_decoupling_and_typo_fixes_pass4(db) -> int:
    print("\n--- Action 7: Email Decoupling & Typo Fixing (Pass 4) ---")
    enriched_count = 0

    # 1. Fix known typo email: taimpaga@.tu.ac.th -> taimpaga@tu.ac.th
    res1 = db.execute(text("""
        UPDATE faculties
        SET email = 'taimpaga@tu.ac.th'
        WHERE email = 'taimpaga@.tu.ac.th';
    """))
    enriched_count += res1.rowcount

    # 2. Fix Naresuan University trailing surname initial attached to first_name
    # e.g. nu_suphannikai__6653: first_name='Suphannikai' -> 'Suphannika'
    nu_candidates = db.execute(text(r"""
        SELECT id, full_name_th, first_name, email
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยนเรศวร'
          AND first_name IS NOT NULL
          AND LENGTH(first_name) >= 5
          AND email ~ '^[a-z]+[a-z]@nu\.ac\.th';
    """)).fetchall()

    for fid, fth, cur_fn, em in nu_candidates:
        local = em.split("@")[0].lower()
        _, cth, _ = normalize_thai_title_and_name(fth)
        th_tokens = cth.split()
        if len(th_tokens) >= 2 and cur_fn.lower() == local:
            # Trailing letter is initial of surname
            clean_fn = clean_name_token(cur_fn[:-1])
            if clean_fn and len(clean_fn) >= 3:
                db.execute(text("UPDATE faculties SET first_name = :fn WHERE id = :id"), {"fn": clean_fn, "id": fid})
                enriched_count += 1

    db.commit()
    print(f"Applied {enriched_count} email decoupling & typo fixes.")
    return enriched_count


# ---------------------------------------------------------------------------
# Main Pipeline Runner
# ---------------------------------------------------------------------------
def run_wave60_stage8():
    print("=" * 70)
    print("Wave 60 Stage 8: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    bio_updated = execute_silpakorn_biology(db)
    cp_updated = execute_silpakorn_computing(db)
    phy_updated = execute_silpakorn_physics_fixes(db)
    swu_dent_updated = execute_swu_dentistry(db)
    swu_edu_updated = execute_swu_education(db)
    buu_pharm_updated = execute_burapha_pharmacy(db)
    email_updated = execute_email_decoupling_and_typo_fixes_pass4(db)

    # Checkpoint Snapshot
    ckpt_file = CHECKPOINT_DIR / "wave60_stage8_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "silpakorn_biology_enriched": bio_updated,
        "silpakorn_computing_enriched": cp_updated,
        "silpakorn_physics_fixes": phy_updated,
        "swu_dentistry_enriched": swu_dent_updated,
        "swu_education_enriched": swu_edu_updated,
        "burapha_pharmacy_enriched": buu_pharm_updated,
        "email_decoupling_pass4_enriched": email_updated,
        "total_operations": (
            bio_updated + cp_updated + phy_updated +
            swu_dent_updated + swu_edu_updated +
            buu_pharm_updated + email_updated
        ),
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_stage8()
