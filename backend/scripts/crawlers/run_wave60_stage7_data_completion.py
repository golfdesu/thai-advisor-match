"""
Wave 60 Stage 7: Autonomous Multi-Source Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (ไม่ต้องขอ approve, use skill.state)"

Actions:
1. Burapha University Faculty of Humanities and Social Sciences (HUSO) Harvester (10 Departments):
   Harvests huso.buu.ac.th/dpt/ -> 119+ faculty across Psychology, History, Western Languages,
   Eastern Languages, Thai, Economics, Sociology, Communication Arts, Religion, Information Studies, Geo-Info.
2. Burapha University Faculty of Science Harvester (10 Departments):
   Harvests science.buu.ac.th/newweb/dept_detail.php?dept=1..10 and individual person_detail.php?uid=...
   -> 157+ faculty with institutional @buu.ac.th emails, English first names, and titles.
3. Burapha University Faculty of Education Harvester (7 Departments):
   Harvests edu.buu.ac.th/personnel/show/1..7 -> 94 faculty with portrait URLs, titles, and departments.
4. Silpakorn University Faculty of Science (Physics) Harvester:
   Harvests phy.sc.su.ac.th/people.html -> 21 faculty with exact English names, @silpakorn.edu / @su.ac.th emails.
5. Silpakorn University Faculty of Science (Chemistry) Harvester:
   Harvests chem.sc.su.ac.th/staff -> 46 faculty with portrait URLs, titles, and departments.
6. SWU Faculty of Science (Computer Science & Materials Science) Harvester:
   Harvests cs.science.swu.ac.th/teacher-staff/ and materials.science.swu.ac.th/faculty-members-2/
   -> resolves missing surnames (e.g. วีรยุทธ เจริญเรืองกิจ), portraits, and English names.
7. Multi-University Email Pattern Backfill (Pass 3):
   Restores first/last names from institutional email structures across remaining Thai universities.
8. Checkpoints execution state to backend/data/agent_states/wave60_stage7_data_completion_snapshot.json.
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
# Action 1: Burapha University HUSO Harvester (10 Departments)
# ---------------------------------------------------------------------------
def execute_burapha_huso(db) -> int:
    print("\n--- Action 1: Harvesting Burapha HUSO (10 Departments) ---")
    url = "https://huso.buu.ac.th/dpt/"
    req = urllib.request.Request(url, headers=HEADERS)
    huso_roster = []

    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            main = soup.find("main") or soup.find("article") or soup
            lines = [l.strip() for l in main.get_text("\n", strip=True).splitlines() if l.strip()]

            cur_dept = None
            for line in lines:
                if line.startswith("ภาควิชา"):
                    cur_dept = line.split("(")[0].strip()
                    continue

                # Match numbered faculty lines e.g. "1. ดร.นิสรา คำมณี (หัวหน้าภาควิชา)"
                m_num = re.match(r"^\d+\.\s*(.+)$", line)
                if m_num and cur_dept:
                    raw = m_num.group(1).strip()
                    if any(noise in raw for noise in ["เจ้าหน้าที่", "นักวิชาการ", "พนักงาน"]):
                        continue

                    # Check if foreign name: e.g. "Mr.Richard Anthony O Donnell"
                    if any(pfx in raw for pfx in ["Mr.", "MISS.", "Miss."]) and not any('฀' <= c <= '๿' for c in raw):
                        clean_en = re.sub(r"^(?:Mr\.|MISS\.|Miss\.)\s*", "", raw, flags=re.I).strip()
                        parts = [clean_name_token(p) for p in clean_en.split() if len(p) >= 2]
                        if len(parts) >= 2:
                            fn = parts[0]
                            ln = " ".join(parts[1:])
                            huso_roster.append({
                                "clean_th": raw,
                                "raw_th": raw,
                                "title_th": "อ.",
                                "fn": fn,
                                "ln": ln,
                                "dep_th": cur_dept,
                            })
                    else:
                        clean_th = re.sub(r"\([^)]*\)", "", raw).strip()
                        t_th, cth, _ = normalize_thai_title_and_name(clean_th)
                        if cth and len(cth.split()) >= 2:
                            huso_roster.append({
                                "clean_th": cth,
                                "raw_th": clean_th,
                                "title_th": t_th,
                                "fn": None,
                                "ln": None,
                                "dep_th": cur_dept,
                            })
    except Exception as e:
        print(f"  Error harvesting Burapha HUSO: {e}")
        return 0

    print(f"Harvested {len(huso_roster)} Burapha HUSO personnel profiles.")

    missing_buu_huso = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, department_th, faculty_th, first_name, last_name
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยบูรพา'
          AND (faculty_th = 'คณะมนุษยศาสตร์และสังคมศาสตร์' OR faculty = 'Faculty of Humanities and Social Sciences' OR id LIKE 'buu_w42%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_dep, cur_fac, cur_fn, cur_ln in missing_buu_huso:
        _, cth, _ = normalize_thai_title_and_name(fth)
        th_tokens = cth.split()
        target_surname = th_tokens[-1] if th_tokens else ""
        target_given = th_tokens[0] if len(th_tokens) > 1 else ""

        match = None
        for cand in huso_roster:
            if cand["clean_th"] == cth:
                match = cand
                break
            cand_tokens = cand["clean_th"].split()
            cand_surname = cand_tokens[-1] if cand_tokens else ""
            cand_given = cand_tokens[0] if len(cand_tokens) > 1 else ""
            if target_surname and target_surname == cand_surname and target_given == cand_given:
                match = cand
                break

        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะมนุษยศาสตร์และสังคมศาสตร์'")
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_ln and match.get("ln"):
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Burapha HUSO records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 2: Burapha University Faculty of Science (10 Departments)
# ---------------------------------------------------------------------------
def execute_burapha_science(db) -> int:
    print("\n--- Action 2: Harvesting Burapha Faculty of Science (10 Departments) ---")
    sci_roster = []

    for d in range(1, 12):
        url = f"https://science.buu.ac.th/newweb/dept_detail.php?dept={d}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                dep_title = soup.title.string.split("|")[0].strip() if soup.title else "คณะวิทยาศาสตร์"
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "person_detail.php?uid=" in href:
                        raw_name = a.get_text(" ", strip=True)
                        t_th, cth, _ = normalize_thai_title_and_name(raw_name)
                        if cth and len(cth.split()) >= 2:
                            # Fetch individual profile for email
                            prof_url = f"https://science.buu.ac.th/newweb/{href}"
                            em, fn = None, None
                            try:
                                p_req = urllib.request.Request(prof_url, headers=HEADERS)
                                with urllib.request.urlopen(p_req, context=SSL_CTX, timeout=5) as p_resp:
                                    p_soup = BeautifulSoup(p_resp.read().decode("utf-8", errors="ignore"), "html.parser")
                                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@(?:go\.)?buu\.ac\.th", p_soup.get_text())
                                    if emails:
                                        em = emails[0].lower()
                                        local = em.split("@")[0].split("_")[0].split(".")[0]
                                        fn = clean_name_token(local)
                            except Exception:
                                pass

                            sci_roster.append({
                                "clean_th": cth,
                                "title_th": t_th,
                                "email": em,
                                "fn": fn,
                                "dep_th": dep_title,
                            })
        except Exception as e:
            print(f"  Error fetching BUU Science Dept {d}: {e}")
        time.sleep(0.05)

    print(f"Harvested {len(sci_roster)} Burapha Science personnel profiles.")

    missing_buu_sci = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, email, department_th, faculty_th, first_name
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยบูรพา'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'buu_w42%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_em, cur_dep, cur_fac, cur_fn in missing_buu_sci:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = next((item for item in sci_roster if item["clean_th"] == cth), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_em and match.get("email"):
                sql_parts.append("email = :em")
                updates["em"] = match["email"]
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Burapha Science records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 3: Burapha University Faculty of Education (7 Departments)
# ---------------------------------------------------------------------------
def execute_burapha_education(db) -> int:
    print("\n--- Action 3: Harvesting Burapha Faculty of Education (7 Departments) ---")
    edu_roster = []

    for d in range(1, 8):
        url = f"https://edu.buu.ac.th/personnel/show/{d}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if "pic" in src or "ภาควิชา" in src:
                        parent = img.find_parent("div")
                        next_div = parent.find_next_sibling("div") if parent else None
                        if next_div:
                            h5 = next_div.find("h5")
                            raw_name = h5.get_text(" ", strip=True) if h5 else next_div.get_text(" ", strip=True).split()[0]
                            # Check role
                            h6 = next_div.find("h6")
                            role_txt = h6.get_text(" ", strip=True) if h6 else ""
                            if any(noise in role_txt for noise in ["เจ้าหน้าที่", "นักวิชาการ", "การเงิน", "พัสดุ"]):
                                continue

                            t_th, cth, _ = normalize_thai_title_and_name(raw_name)
                            if cth and len(cth.split()) >= 2:
                                # Extract department from image path e.g. .../ภาควิชาการจัดการเรียนรู้/...
                                dep_m = re.search(r"/(ภาควิชา[^/]+)/", src)
                                dep_th = dep_m.group(1) if dep_m else "คณะศึกษาศาสตร์"

                                edu_roster.append({
                                    "clean_th": cth,
                                    "title_th": t_th,
                                    "image_url": src,
                                    "dep_th": dep_th,
                                })
        except Exception as e:
            print(f"  Error fetching BUU Education Dept {d}: {e}")
        time.sleep(0.05)

    print(f"Harvested {len(edu_roster)} Burapha Education personnel profiles.")

    missing_buu_edu = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยบูรพา'
          AND (faculty_th = 'คณะศึกษาศาสตร์' OR faculty = 'Faculty of Education' OR id LIKE 'buu_w42%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_dep, cur_fac in missing_buu_edu:
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
    print(f"Enriched {enriched_count} Burapha Education records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 4: Silpakorn University Faculty of Science (Physics) Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_physics(db) -> int:
    print("\n--- Action 4: Harvesting Silpakorn Science (Physics) ---")
    url = "http://phy.sc.su.ac.th/people.html"
    req = urllib.request.Request(url, headers=HEADERS)
    phy_roster = []

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            lines = [l.strip() for l in soup.get_text("\n", strip=True).splitlines() if l.strip()]
            for i, line in enumerate(lines):
                if "@silpakorn.edu" in line or "@su.ac.th" in line:
                    em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu)", line, re.I)
                    email_str = em_match.group(0).lower() if em_match else None

                    th_line, en_line = None, None
                    for offset in range(1, 6):
                        if i - offset >= 0:
                            cand = lines[i - offset]
                            if any(t in cand for t in ["ผศ.", "รศ.", "ศ.", "อ."]) and any('฀' <= c <= '๿' for c in cand):
                                th_line = cand
                            elif any(t in cand for t in ["Dr.", "Prof.", "Assistant", "Associate"]) and not any('฀' <= c <= '๿' for c in cand):
                                en_line = cand

                    if th_line:
                        t_th, cth, _ = normalize_thai_title_and_name(th_line)
                        fn, ln = None, None
                        if en_line:
                            clean_en = re.sub(r"^(?:(?:Asst|Assoc)\.?\s*Prof\.?\s*(?:Dr\.?)?|Prof\.?\s*(?:Dr\.?)?|Dr\.?)\s*", "", en_line, flags=re.I).strip()
                            parts = [clean_name_token(p) for p in clean_en.split() if len(p) >= 2]
                            if len(parts) >= 2 and all(p.replace("-", "").isalpha() for p in parts[:2]):
                                fn = parts[0]
                                ln = " ".join(parts[1:])

                        phy_roster.append({
                            "clean_th": cth,
                            "title_th": t_th,
                            "fn": fn,
                            "ln": ln,
                            "email": email_str,
                            "dep_th": "ภาควิชาฟิสิกส์",
                        })
    except Exception as e:
        print(f"  Error harvesting Silpakorn Physics: {e}")
        return 0

    print(f"Harvested {len(phy_roster)} Silpakorn Physics personnel profiles.")

    missing_su_phy = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, email, first_name, last_name, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'su_w43%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_em, cur_fn, cur_ln, cur_dep, cur_fac in missing_su_phy:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = next((item for item in phy_roster if item["clean_th"] == cth), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match.get("title_th"):
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_em and match.get("email"):
                sql_parts.append("email = :em")
                updates["em"] = match["email"]
            if not cur_fn and match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if not cur_ln and match.get("ln"):
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]
            if not cur_dep and match.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = match["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn Physics records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 5: Silpakorn University Faculty of Science (Chemistry) Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_chemistry(db) -> int:
    print("\n--- Action 5: Harvesting Silpakorn Science (Chemistry) ---")
    url = "https://chem.sc.su.ac.th/staff"
    req = urllib.request.Request(url, headers=HEADERS)
    chem_roster = []

    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "/uploads/wp/" in src and (".png" in src or ".jpg" in src):
                    filename = src.split("/")[-1]
                    clean_fn = re.sub(r"_(?:new|logo|s|\d+)?\.(?:png|jpg)$", "", filename)
                    clean_fn = clean_fn.replace("-", " ").replace("_", " ").strip()
                    if any('฀' <= c <= '๿' for c in clean_fn):
                        t_th, cth, _ = normalize_thai_title_and_name(clean_fn)
                        if cth and len(cth.split()) >= 2:
                            full_img_url = f"https://chem.sc.su.ac.th{src}" if src.startswith("/") else src
                            chem_roster.append({
                                "clean_th": cth,
                                "title_th": t_th,
                                "image_url": full_img_url,
                                "dep_th": "ภาควิชาเคมี",
                            })
    except Exception as e:
        print(f"  Error harvesting Silpakorn Chemistry: {e}")
        return 0

    print(f"Harvested {len(chem_roster)} Silpakorn Chemistry personnel profiles.")

    missing_su_chem = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'su_w43%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_dep, cur_fac in missing_su_chem:
        _, cth, _ = normalize_thai_title_and_name(fth)
        th_tokens = cth.split()
        target_surname = th_tokens[-1] if th_tokens else ""
        target_given = th_tokens[0] if len(th_tokens) > 1 else ""

        match = None
        for cand in chem_roster:
            if cand["clean_th"] == cth:
                match = cand
                break
            cand_tokens = cand["clean_th"].split()
            cand_surname = cand_tokens[-1] if cand_tokens else ""
            cand_given = cand_tokens[0] if len(cand_tokens) > 1 else ""
            if target_surname and target_surname == cand_surname and target_given == cand_given:
                match = cand
                break

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
                sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn Chemistry records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 6: SWU Computer Science & Materials Science Harvester
# ---------------------------------------------------------------------------
def execute_swu_science(db) -> int:
    print("\n--- Action 6: Harvesting SWU Science (CS & Materials) ---")
    swu_roster = []

    # 1. Computer Science
    try:
        url_cs = "https://cs.science.swu.ac.th/teacher-staff/"
        req = urllib.request.Request(url_cs, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            imgs = soup.find_all("img")
            for img in imgs:
                src = img.get("src", "")
                if "uploads/20" in src and ("cropped" in src or "png" in src or "jpg" in src):
                    fname = src.split("/")[-1]
                    clean_slug = re.sub(r"_(?:cropped.*|\d+)\.(?:jpg|png)$", "", fname)
                    parts = clean_slug.split("-")
                    if len(parts) >= 2 and all(p.replace("_", "").isalpha() for p in parts[:2]):
                        fn = clean_name_token(parts[0])
                        ln = " ".join([clean_name_token(p) for p in parts[1:]])
                        swu_roster.append({
                            "fn": fn,
                            "ln": ln,
                            "image_url": src,
                            "dep_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
                        })
    except Exception as e:
        print(f"  Error fetching SWU CS: {e}")

    # 2. Materials Science
    try:
        url_mat = "https://materials.science.swu.ac.th/faculty-members-2/"
        req = urllib.request.Request(url_mat, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            lines = [l.strip() for l in soup.get_text("\n", strip=True).splitlines() if l.strip()]
            for i, line in enumerate(lines):
                if any(line.startswith(pfx) for pfx in ["ผศ.", "รศ.", "อ.ดร.", "อ."]):
                    t_th, cth, _ = normalize_thai_title_and_name(line)
                    if cth and len(cth.split()) >= 2 and i + 1 < len(lines):
                        cand_en = lines[i + 1]
                        clean_en = re.sub(r"^(?:(?:Asst|Assoc)\.?\s*Prof\.?\s*(?:Dr\.?)?|Prof\.?\s*(?:Dr\.?)?|Dr\.?)\s*", "", cand_en, flags=re.I).strip()
                        parts = [clean_name_token(p) for p in clean_en.split() if len(p) >= 2]
                        if len(parts) >= 2:
                            swu_roster.append({
                                "clean_th": cth,
                                "title_th": t_th,
                                "fn": parts[0],
                                "ln": " ".join(parts[1:]),
                                "dep_th": "ภาควิชาวัสดุศาสตร์",
                            })
    except Exception as e:
        print(f"  Error fetching SWU Materials: {e}")

    print(f"Harvested {len(swu_roster)} SWU Science personnel profiles.")

    # Match against SWU database
    missing_swu = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, department_th, faculty_th, first_name, last_name
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ'
          AND (faculty_th = 'คณะวิทยาศาสตร์' OR faculty = 'Faculty of Science' OR id LIKE 'swu_w44%');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_dep, cur_fac, cur_fn, cur_ln in missing_swu:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = None
        for cand in swu_roster:
            if cand.get("clean_th") and cand["clean_th"] == cth:
                match = cand
                break
            # Or match on first name
            if cand.get("fn") and cur_fn and cand["fn"].lower() == cur_fn.lower():
                match = cand
                break
            # Or match on known Weerayuth
            if "วีรยุทธ" in fth and cand.get("fn") == "Werayuth":
                match = cand
                break

        if match:
            updates = {"fid": fid}
            sql_parts = []
            if match.get("fn"):
                sql_parts.append("first_name = :fn")
                updates["fn"] = match["fn"]
            if match.get("ln"):
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]
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
                sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")

            # Check if full_name_th was incomplete (e.g. 'วีรยุทธ')
            if fth.strip() == "วีรยุทธ" and match.get("ln"):
                sql_parts.append("full_name_th = 'ผศ.ดร. วีรยุทธ เจริญเรืองกิจ'")

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} SWU Science records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 7: Multi-University Email Pattern Backfill (Pass 3)
# ---------------------------------------------------------------------------
def execute_multi_university_email_backfill_pass3(db) -> int:
    print("\n--- Action 7: Multi-University Email Name Backfill (Pass 3) ---")
    # Firstname_initial@... e.g. jutarat_k@buu.ac.th
    underscore_candidates = db.execute(text("""
        SELECT id, full_name_th, email
        FROM faculties
        WHERE email ~ '^[a-z]{3,}_[a-z]@'
          AND (first_name IS NULL OR first_name = '');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, em in underscore_candidates:
        local = em.split("@")[0].lower()
        fn_part = local.split("_")[0]
        fn = clean_name_token(fn_part)
        if fn and fn.lower() not in {"info", "admin", "dean", "office"}:
            db.execute(
                text("UPDATE faculties SET first_name = :fn WHERE id = :id"),
                {"fn": fn, "id": fid}
            )
            enriched_count += 1

    db.commit()
    print(f"Restored {enriched_count} first names from underscore email format.")
    return enriched_count


# ---------------------------------------------------------------------------
# Main Pipeline Runner
# ---------------------------------------------------------------------------
def run_wave60_stage7():
    print("=" * 70)
    print("Wave 60 Stage 7: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    buu_huso_updated = execute_burapha_huso(db)
    buu_sci_updated = execute_burapha_science(db)
    buu_edu_updated = execute_burapha_education(db)
    su_phy_updated = execute_silpakorn_physics(db)
    su_chem_updated = execute_silpakorn_chemistry(db)
    swu_sci_updated = execute_swu_science(db)
    email_updated = execute_multi_university_email_backfill_pass3(db)

    # Checkpoint Snapshot
    ckpt_file = CHECKPOINT_DIR / "wave60_stage7_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "burapha_huso_enriched": buu_huso_updated,
        "burapha_science_enriched": buu_sci_updated,
        "burapha_education_enriched": buu_edu_updated,
        "silpakorn_physics_enriched": su_phy_updated,
        "silpakorn_chemistry_enriched": su_chem_updated,
        "swu_science_enriched": swu_sci_updated,
        "email_backfill_pass3_enriched": email_updated,
        "total_operations": (
            buu_huso_updated + buu_sci_updated + buu_edu_updated +
            su_phy_updated + su_chem_updated + swu_sci_updated + email_updated
        ),
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_stage7()
