"""
Wave 60 Stage 3: Autonomous Multi-Source Faculty Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (use skill.state)"

Actions:
1. Harvest Silpakorn Engineering English Portals (eng2.su.ac.th) across 7 departments
   -> populates first_name, last_name, academic_title_en/th, department, image_url.
2. Harvest PSU Medicine (Internal Medicine) Directory (internal-medicine.psu.ac.th/doctor/?doctor_page=1..7)
   -> populates first_name, last_name, academic_title_en, image_url, education for 78 doctors.
3. Harvest Thammasat Medicine (ATTM) Official Directory (www.med.tu.ac.th/department/attm/?page_id=124)
   -> populates paired first_name, last_name, academic_title_en, and email for 31 faculty.
4. Extract Authentic Romanized Names from Thammasat Allied Health Sciences Slugs (allied.tu.ac.th/cv/?professor=...)
   -> populates first_name, last_name.
5. Harvest SWU Dentistry Department Rosters (dent.swu.ac.th/Default.aspx?tabid=17201, 17202, 17198, 17200, 17199)
   -> populates first_name, image_url, department_th, department across 85 faculty.
6. Harvest Silpakorn Pharmacy Department Portals (pharmacy.su.ac.th/main/department-ndep1..5/)
   -> populates authentic image_url, email, department_th, scholar_url (Scopus).
7. Execute Safe Precision Trailing Surname Initial Stripping on Email-derived First Names.
8. Checkpoint results to backend/data/agent_states/wave60_stage3_data_completion_snapshot.json.
"""

import json
import re
import ssl
import sys
import time
import urllib.parse
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

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TITLE_EN_STRIP = re.compile(
    r"^(?:Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|Lecturer\s*Dr\.|"
    r"Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*",
    re.I,
)

TITLE_EN_TO_TH = [
    (re.compile(r"^Prof\.\s*Dr\.", re.I), "ศ.ดร.", "Prof. Dr."),
    (re.compile(r"^Assoc\.\s*Prof\.\s*Dr\.", re.I), "รศ.ดร.", "Assoc. Prof. Dr."),
    (re.compile(r"^Asst\.\s*Prof\.\s*Dr\.", re.I), "ผศ.ดร.", "Asst. Prof. Dr."),
    (re.compile(r"^Lecturer\s*Dr\.", re.I), "อ.ดร.", "Lecturer Dr."),
    (re.compile(r"^Prof\.", re.I), "ศ.", "Prof."),
    (re.compile(r"^Assoc\.\s*Prof\.", re.I), "รศ.", "Assoc. Prof."),
    (re.compile(r"^Asst\.\s*Prof\.", re.I), "ผศ.", "Asst. Prof."),
    (re.compile(r"^Dr\.", re.I), "ดร.", "Dr."),
    (re.compile(r"^Lecturer", re.I), "อ.", "Lecturer"),
]

TITLE_TH_STRIP = re.compile(
    r"^(?:ศ\.ดร\.นพ\.|รศ\.ดร\.นพ\.|ผศ\.ดร\.นพ\.|อ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|รศ\.ดร\.พญ\.|ผศ\.ดร\.พญ\.|อ\.ดร\.พญ\.|"
    r"ศ\.นพ\.|รศ\.นพ\.|ผศ\.นพ\.|อ\.นพ\.|ศ\.พญ\.|รศ\.พญ\.|ผศ\.พญ\.|อ\.พญ\.|"
    r"ศ\.ดร\.ภญ\.|รศ\.ดร\.ภญ\.|ผศ\.ดร\.ภญ\.|อ\.ดร\.ภญ\.|ศ\.ดร\.ภก\.|รศ\.ดร\.ภก\.|ผศ\.ดร\.ภก\.|อ\.ดร\.ภก\.|"
    r"ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|อ\.ดร\.ทพ\.|อ\.ดร\.ทพญ\.|"
    r"ทพ\.|ทพญ\.|พท\.ป\.|พท\.|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ภญ\.|ภก\.)\s*"
)

TH_TO_EN_INITIAL = {
    "ก": "k", "ข": "k", "ค": "k", "ฆ": "k",
    "จ": "c", "ฉ": "c", "ช": "c", "ฌ": "c",
    "ซ": "s", "ศ": "s", "ษ": "s", "ส": "s",
    "ด": "d", "ฎ": "d",
    "ต": "t", "ฏ": "t", "ถ": "t", "ท": "t", "ธ": "t",
    "บ": "b",
    "ป": "p", "ผ": "p", "ฝ": "f", "พ": "p", "ฟ": "f", "ภ": "p",
    "ม": "m",
    "ย": "y", "ญ": "y",
    "ร": "r", "ฤ": "r",
    "ล": "l", "ฬ": "l",
    "ว": "w",
    "ห": "h", "ฮ": "h",
    "น": "n", "ณ": "n",
    "ง": "n",
}

TH_FINAL_CONSONANT_SOUNDS = {
    "s": set("สศษซชฌ"),
    "p": set("บปพภฟผฝ"),
    "t": set("ดตถทธจชซศษสฏฐฑฒ"),
    "k": set("กขคฆ"),
    "m": set("ม"),
    "n": set("นณญรลฬ"),
    "y": set("ย"),
    "w": set("ว"),
}


def parse_title_en(raw_name: str) -> tuple[str, str, str]:
    t_th = "อ."
    t_en = ""
    for pat, th, en in TITLE_EN_TO_TH:
        m = pat.match(raw_name)
        if m:
            t_th = th
            t_en = en
            break
    clean_name = TITLE_EN_STRIP.sub("", raw_name).strip()
    return t_th, t_en, clean_name


# ---------------------------------------------------------------------------
# Action 1: Silpakorn Engineering English Portals
# ---------------------------------------------------------------------------
def execute_silpakorn_engineering_en(db) -> int:
    print("\n--- Action 1: Harvesting Silpakorn Engineering English Portals ---")
    depts = [
        ("department_materials_science.php?lang=en", "ภาควิชาวิทยาการและวิศวกรรมวัสดุ", "Department of Materials Science and Engineering"),
        ("department_food_technology.php?lang=en", "ภาควิชาเทคโนโลยีอาหาร", "Department of Food Technology"),
        ("department_biotechnology_technology.php?lang=en", "ภาควิชาเทคโนโลยีชีวภาพ", "Department of Biotechnology"),
        ("department_industrial_technology.php?lang=en", "ภาควิชาวิศวกรรมอุตสาหการ", "Department of Industrial Engineering and Management"),
        ("department_mechanical_engineering.php?lang=en", "ภาควิชาวิศวกรรมเครื่องกล", "Department of Mechanical Engineering"),
        ("department_chemical_engineering.php?lang=en", "ภาควิชาวิศวกรรมเคมี", "Department of Chemical Engineering"),
        ("department_electrical_engineering.php?lang=en", "ภาควิชาวิศวกรรมไฟฟ้า", "Department of Electrical Engineering"),
    ]

    eng_map = {}
    for page, dth, den in depts:
        url = f"https://eng2.su.ac.th/{page}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                cards = soup.find_all("div", class_=lambda c: c and "col-" in c and "text-center" in c)
                for c in cards:
                    p = c.find("p", class_="font-dean-head")
                    a = c.find("a", href=lambda h: h and "id=" in h)
                    img = c.find("img")
                    if p and a:
                        pid = a["href"].split("id=")[-1].strip()
                        raw_en = p.get_text(" ", strip=True)
                        tth, ten, clean_en = parse_title_en(raw_en)
                        parts = clean_en.split()
                        if len(parts) >= 2:
                            fn = parts[0].title()
                            ln = " ".join(parts[1:]).title()
                            img_src = img["src"].strip() if img else None
                            eng_map[pid] = {
                                "first_name": fn,
                                "last_name": ln,
                                "academic_title_th": tth,
                                "academic_title_en": ten,
                                "department_th": dth,
                                "department": den,
                                "image_url": img_src,
                            }
        except Exception as e:
            print(f"  Error fetching {page}: {e}")

    print(f"Scraped {len(eng_map)} faculty profiles from Silpakorn Engineering portals.")

    # Match in database by profile_url LIKE '%department_teacher_portfolio.php?id={pid}%'
    candidates = db.execute(text("""
        SELECT id, profile_url, first_name, last_name, academic_title_th, department_th, image_url
        FROM faculties
        WHERE profile_url LIKE '%eng.su.ac.th/department_teacher_portfolio.php?id=%';
    """)).fetchall()

    updated = 0
    for fid, purl, cur_fn, cur_ln, cur_tth, cur_dth, cur_img in candidates:
        m = re.search(r"id=(\d+)", purl or "")
        if m and m.group(1) in eng_map:
            info = eng_map[m.group(1)]
            sql_parts = []
            params = {"fid": fid}

            if not cur_fn or not cur_ln:
                sql_parts.extend(["first_name = :fn", "last_name = :ln"])
                params["fn"] = info["first_name"]
                params["ln"] = info["last_name"]
            if not cur_tth:
                sql_parts.append("academic_title_th = :tth")
                params["tth"] = info["academic_title_th"]
            if not cur_dth:
                sql_parts.extend(["department_th = :dth", "department = :den"])
                params["dth"] = info["department_th"]
                params["den"] = info["department"]
            if not cur_img and info.get("image_url"):
                sql_parts.append("image_url = :img")
                params["img"] = info["image_url"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                updated += 1

    db.commit()
    print(f"Enriched {updated} Silpakorn Engineering faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 2: PSU Medicine (Internal Medicine) Harvester
# ---------------------------------------------------------------------------
def execute_psu_internal_medicine(db) -> int:
    print("\n--- Action 2: Harvesting PSU Medicine (Internal Medicine) Directory ---")
    scraped_doctors = []
    for p in range(1, 8):
        url = f"https://internal-medicine.psu.ac.th/doctor/?doctor_page={p}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                cards = soup.find_all("article") or soup.find_all("div", class_="diis-listcard")
                for card in cards:
                    nth = card.find("h3", class_="diis-listcard-name")
                    nen = card.find("div", class_="diis-listcard-name-en")
                    img = card.find("img")
                    edu_div = card.find("div", class_="diis-listcard-info-item")
                    if nth and nen:
                        raw_th = nth.get_text(strip=True)
                        raw_en = nen.get_text(strip=True)
                        img_url = img["src"].strip() if img else None
                        edu_items = []
                        if edu_div:
                            for li in edu_div.find_all(["li", "p"]):
                                t = li.get_text(strip=True)
                                if t and len(t) > 5 and t not in ("การศึกษา", "Education"):
                                    edu_items.append(t)
                        scraped_doctors.append({
                            "name_th": raw_th,
                            "name_en": raw_en,
                            "image_url": img_url,
                            "education": edu_items,
                        })
        except Exception as e:
            print(f"  Error on page {p}: {e}")

    print(f"Scraped {len(scraped_doctors)} doctor profiles from PSU Internal Medicine.")

    db_doctors = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url
        FROM faculties
        WHERE id LIKE 'psu_med_wave15_%'
          AND department_th LIKE '%อายุรศาสตร์%';
    """)).fetchall()

    db_map = {}
    for db_id, fn_th, cur_tth, cur_img in db_doctors:
        clean = TITLE_TH_STRIP.sub("", fn_th).strip()
        parts = clean.split()
        if len(parts) >= 2:
            db_map[(parts[0], parts[1])] = (db_id, cur_img)

    updated = 0
    for doc in scraped_doctors:
        clean_th = TITLE_TH_STRIP.sub("", doc["name_th"]).strip()
        th_parts = clean_th.split()
        if len(th_parts) >= 2 and (th_parts[0], th_parts[1]) in db_map:
            db_id, cur_img = db_map[(th_parts[0], th_parts[1])]
            raw_en = doc["name_en"]
            raw_en_clean = re.sub(r"\s+M\.D\.", "", raw_en, flags=re.I).strip()
            tth, ten, clean_name = parse_title_en(raw_en_clean)
            en_parts = clean_name.split()
            if len(en_parts) >= 2:
                fn = en_parts[0].title()
                ln = " ".join(en_parts[1:]).title()
                sql = "UPDATE faculties SET first_name = :fn, last_name = :ln"
                params = {"fn": fn, "ln": ln, "fid": db_id}
                if not cur_img and doc["image_url"]:
                    sql += ", image_url = :img"
                    params["img"] = doc["image_url"]
                if doc["education"]:
                    sql += ", education = :edu"
                    params["edu"] = json.dumps(doc["education"], ensure_ascii=False)
                sql += " WHERE id = :fid"
                db.execute(text(sql), params)
                updated += 1

    db.commit()
    print(f"Enriched {updated} PSU Internal Medicine doctors with exact English profiles and images.")
    return updated


# ---------------------------------------------------------------------------
# Action 3: Thammasat Medicine ATTM Harvester
# ---------------------------------------------------------------------------
def execute_thammasat_attm(db) -> int:
    print("\n--- Action 3: Harvesting Thammasat Medicine (ATTM) Official Directory ---")
    url = "https://www.med.tu.ac.th/department/attm/?page_id=124"
    attm_pairs = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for h3 in soup.find_all("h3"):
                th_name = h3.get_text(" ", strip=True)
                if not th_name or len(th_name) < 5:
                    continue
                h4 = h3.find_next_sibling("h4")
                en_name = h4.get_text(" ", strip=True) if h4 else None
                div = h3.find_next_sibling("div")
                email = None
                if div:
                    m = re.search(r"[\w\.-]+@tu\.ac\.th", div.get_text(" ", strip=True))
                    if m:
                        email = m.group(0).lower().strip()
                if th_name and en_name:
                    attm_pairs.append({
                        "name_th": th_name,
                        "name_en": en_name,
                        "email": email,
                    })
    except Exception as e:
        print(f"  Error fetching TU ATTM directory: {e}")

    print(f"Parsed {len(attm_pairs)} paired faculty profiles from TU ATTM portal.")

    tu_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยธรรมศาสตร์'
          AND (department_th LIKE '%การแพทย์แผนไทย%' OR faculty_th LIKE '%แพทย์%');
    """)).fetchall()

    updated = 0
    matched_fids = set()
    for item in attm_pairs:
        tokens = item["name_th"].split()
        surname = tokens[-1]
        for fid, fn_th, cur_fn, cur_ln, cur_em in tu_db_rows:
            if fid in matched_fids:
                continue
            if surname in fn_th:
                matched_fids.add(fid)
                raw_en = item["name_en"]
                raw_en_clean = re.sub(r",\s*(?:Ph\.?\s*D\.?|M\.?\s*Sc\.?|B\.?\s*ATM\.?|M\.?\s*D\.?).*$", "", raw_en, flags=re.I).strip()
                tth, ten, clean_name = parse_title_en(raw_en_clean)
                en_parts = clean_name.split()
                if len(en_parts) >= 2:
                    fn = en_parts[0].title()
                    ln = " ".join(en_parts[1:]).title()
                    sql_parts = ["first_name = :fn", "last_name = :ln"]
                    params = {"fn": fn, "ln": ln, "fid": fid}
                    if not cur_em and item.get("email"):
                        em = item["email"]
                        local = em.split("@")[0].lower()
                        if any(tok in local or local in tok for tok in [fn.lower(), ln.lower()]):
                            sql_parts.append("email = :em")
                            params["em"] = em
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Thammasat ATTM faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 4: Thammasat Allied Health Sciences Professor Slug Extraction
# ---------------------------------------------------------------------------
def execute_thammasat_allied_slugs(db) -> int:
    print("\n--- Action 4: Extracting Names from Thammasat Allied Health Sciences Slugs ---")
    rows = db.execute(text("""
        SELECT id, profile_url, first_name, last_name
        FROM faculties
        WHERE profile_url LIKE '%allied.tu.ac.th/cv/?professor=%'
          AND (first_name IS NULL OR last_name IS NULL OR first_name = '' OR last_name = '');
    """)).fetchall()

    updated = 0
    for fid, purl, cur_fn, cur_ln in rows:
        m = re.search(r"professor=([^&]+)", purl or "")
        if m:
            slug = urllib.parse.unquote(m.group(1)).strip()
            parts = slug.split("-")
            if len(parts) >= 2 and not any(c.isdigit() for c in slug) and not any("฀" <= c <= "๿" for c in slug):
                fn = parts[0].title()
                ln = " ".join(parts[1:]).title()
                if len(fn) >= 3 and len(ln) >= 3:
                    db.execute(
                        text("UPDATE faculties SET first_name = :fn, last_name = :ln WHERE id = :fid"),
                        {"fn": fn, "ln": ln, "fid": fid}
                    )
                    updated += 1

    db.commit()
    print(f"Enriched {updated} Thammasat Allied Health Sciences records from authentic slugs.")
    return updated


# ---------------------------------------------------------------------------
# Action 5: SWU Dentistry Department & Image Harvester
# ---------------------------------------------------------------------------
def execute_swu_dentistry(db) -> int:
    print("\n--- Action 5: Harvesting SWU Dentistry Department Rosters & Images ---")
    depts = [
        (17201, "ภาควิชาทันตกรรมทั่วไป", "Department of General Dentistry"),
        (17202, "ภาควิชาทันตกรรมสำหรับเด็กและทันตกรรมป้องกัน", "Department of Pediatric and Preventive Dentistry"),
        (17198, "ภาควิชาทันตกรรมอนุรักษ์และทันกรรมประดิษฐ์", "Department of Restorative and Prosthetic Dentistry"),
        (17200, "ภาควิชาศัลยศาสตร์และเวชศาสตร์ช่องปาก", "Department of Oral and Maxillofacial Surgery"),
        (17199, "ภาควิชาโอษฐวิทยา", "Department of Stomatology"),
    ]

    dent_roster = []
    for tabid, dth, den in depts:
        url = f"https://dent.swu.ac.th/Default.aspx?tabid={tabid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                for thumb in soup.find_all("div", class_="thumbnail"):
                    img = thumb.find("img")
                    h6 = thumb.find("h6")
                    if img and h6:
                        src = img.get("src", "")
                        raw_name = h6.get_text(" ", strip=True)
                        if any(k in raw_name for k in ["ทพ.", "ทพญ.", "อ.", "ผศ.", "รศ.", "ศ.", "ดร."]):
                            dent_roster.append({
                                "name_th": raw_name,
                                "image_src": src,
                                "department_th": dth,
                                "department": den,
                            })
        except Exception as e:
            print(f"  Error on tabid {tabid}: {e}")

    print(f"Harvested {len(dent_roster)} faculty profiles from SWU Dentistry.")

    db_swu = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, department_th, image_url
        FROM faculties
        WHERE university_th LIKE '%ศรีนครินทรวิโรฒ%'
          AND (faculty_th LIKE '%ทันต%' OR department_th LIKE '%ทันต%');
    """)).fetchall()

    db_map = {}
    for fid, fn_th, cur_fn, cur_ln, cur_dth, cur_img in db_swu:
        clean = TITLE_TH_STRIP.sub("", fn_th).strip()
        parts = clean.split()
        if len(parts) >= 2:
            db_map[(parts[0], parts[1])] = (fid, cur_fn, cur_ln, cur_dth, cur_img)

    updated = 0
    for doc in dent_roster:
        clean_th = TITLE_TH_STRIP.sub("", doc["name_th"]).strip()
        th_parts = clean_th.split()
        if len(th_parts) >= 2 and (th_parts[0], th_parts[1]) in db_map:
            fid, cur_fn, cur_ln, cur_dth, cur_img = db_map[(th_parts[0], th_parts[1])]
            sql_parts = []
            params = {"fid": fid}

            # Extract first_name from image filename (e.g. /portals/42/Images/Person/DCD/teerachate.jpg)
            img_file = Path(doc["image_src"].split("?")[0]).stem.lower()
            if not cur_fn and len(img_file) >= 4 and img_file.isalpha():
                # Check trailing initial consonant
                th_surname = th_parts[-1]
                surname_init = th_surname[0]
                expected_c = TH_TO_EN_INITIAL.get(surname_init)
                if expected_c and img_file.endswith(expected_c):
                    fn_candidate = img_file[:-1].title()
                else:
                    fn_candidate = img_file.title()
                if len(fn_candidate) >= 3:
                    sql_parts.append("first_name = :fn")
                    params["fn"] = fn_candidate

            if not cur_dth:
                sql_parts.extend(["department_th = :dth", "department = :den"])
                params["dth"] = doc["department_th"]
                params["den"] = doc["department"]

            if not cur_img and doc["image_src"]:
                full_img_url = urllib.parse.urljoin("https://dent.swu.ac.th", doc["image_src"])
                sql_parts.append("image_url = :img")
                params["img"] = full_img_url

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                updated += 1

    db.commit()
    print(f"Enriched {updated} SWU Dentistry faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 6: Silpakorn Pharmacy Scopus and Department Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_pharmacy(db) -> int:
    print("\n--- Action 6: Harvesting Silpakorn Pharmacy Portals & Scopus Details ---")
    pharm_depts = [
        ("http://pharmacy.su.ac.th/main/department-ndep1/", "สาขาวิชาเภสัชศาสตร์ชีวภาพและเภสัชวิทยา", "Department of Biopharmaceutical Sciences and Pharmacology"),
        ("http://pharmacy.su.ac.th/main/department-ndep2/", "สาขาวิชาเภสัชกรรมอุตสาหกรรม", "Department of Industrial Pharmacy"),
        ("http://pharmacy.su.ac.th/main/department-ndep3/", "สาขาวิชาบริบาลทางเภสัชกรรม", "Department of Pharmaceutical Care"),
        ("http://pharmacy.su.ac.th/main/department-ndep4/", "สาขาวิชาเภสัชศาสตร์สังคมและการบริหาร", "Department of Social and Administrative Pharmacy"),
        ("http://pharmacy.su.ac.th/main/department-ndep5/", "สาขาวิชาสุขภาพดิจิทัล", "Department of Digital Health"),
    ]

    pharm_roster = []
    for url, dth, den in pharm_depts:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                for h3 in soup.find_all("h3"):
                    raw_th = h3.get_text(" ", strip=True)
                    if any(k in raw_th for k in ["อ.", "ผศ.", "รศ.", "ศ.", "ดร."]):
                        card = h3.find_parent("div")
                        grand = card.find_parent("div") if card else None
                        img = grand.find("img") if grand else None
                        email, scopus_url = None, None
                        if grand:
                            for a in grand.find_all("a", href=True):
                                href = a["href"]
                                if "mailto:" in href:
                                    email = href.replace("mailto:", "").split("?")[0].strip().lower()
                                elif "scopus.com" in href:
                                    scopus_url = href.strip()
                        pharm_roster.append({
                            "name_th": raw_th,
                            "email": email,
                            "image_url": img["src"].strip() if img else None,
                            "scholar_url": scopus_url,
                            "department_th": dth,
                            "department": den,
                        })
        except Exception as e:
            print(f"  Error fetching {url}: {e}")

    print(f"Scraped {len(pharm_roster)} faculty records from Silpakorn Pharmacy portals.")

    db_pharm = db.execute(text("""
        SELECT id, full_name_th, email, image_url, scholar_url, department_th
        FROM faculties
        WHERE university_th LIKE '%ศิลปากร%'
          AND faculty_th LIKE '%เภสัช%';
    """)).fetchall()

    updated = 0
    matched_fids = set()
    for item in pharm_roster:
        tokens = item["name_th"].split()
        surname = tokens[-1]
        for fid, fn_th, cur_em, cur_img, cur_sch, cur_dth in db_pharm:
            if fid in matched_fids:
                continue
            if surname in fn_th:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if not cur_em and item.get("email") and "su.ac.th" in item["email"]:
                    sql_parts.append("email = :em")
                    params["em"] = item["email"]
                if not cur_img and item.get("image_url"):
                    sql_parts.append("image_url = :img")
                    params["img"] = item["image_url"]
                if not cur_sch and item.get("scholar_url"):
                    sql_parts.append("scholar_url = :sch")
                    params["sch"] = item["scholar_url"]
                if not cur_dth:
                    sql_parts.extend(["department_th = :dth", "department = :den"])
                    params["dth"] = item["department_th"]
                    params["den"] = item["department"]

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Pharmacy faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 7: Safe Precision Trailing Surname Initial Consonant Stripping
# ---------------------------------------------------------------------------
def execute_safe_trailing_consonant_stripping(db) -> int:
    print("\n--- Action 7: Safe Trailing Surname Initial Consonant Stripping ---")
    rows = db.execute(text("""
        SELECT id, full_name_th, first_name, email
        FROM faculties
        WHERE full_name_th ~ '[ก-๙]'
          AND first_name IS NOT NULL AND length(first_name) >= 5
          AND (last_name IS NULL OR last_name = '')
          AND email ~ '^[a-z]+[a-z]@[a-z0-9\.-]+';
    """)).fetchall()

    stripped_count = 0
    for fid, fn_th, fn_en, em in rows:
        th_parts = [p for p in fn_th.split() if p not in ["ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "อาจารย์", "พท.ป.", "ทพ.", "ทพญ.", "นพ.", "พญ.", "ภญ.", "ภก."]]
        if len(th_parts) >= 2:
            th_firstname = th_parts[0]
            th_surname = th_parts[-1]
            surname_init = th_surname[0]
            expected_consonant = TH_TO_EN_INITIAL.get(surname_init)

            if expected_consonant and fn_en.lower().endswith(expected_consonant):
                # Clean Thai firstname vowels to inspect the actual final consonant
                fn_clean_thai = re.sub(r"[เแโใไ่้๊๋์็ิีึืุูะัาำๅๆฯ]", "", th_firstname)
                last_thai_char = fn_clean_thai[-1] if fn_clean_thai else ""

                # If Thai firstname naturally ends with this consonant sound, do NOT strip!
                if expected_consonant in TH_FINAL_CONSONANT_SOUNDS and last_thai_char in TH_FINAL_CONSONANT_SOUNDS[expected_consonant]:
                    continue

                cleaned_fn = fn_en[:-1]
                if len(cleaned_fn) >= 4:
                    db.execute(
                        text("UPDATE faculties SET first_name = :fn WHERE id = :fid"),
                        {"fn": cleaned_fn, "fid": fid}
                    )
                    stripped_count += 1

    db.commit()
    print(f"Safely stripped trailing surname initials from {stripped_count} email-derived first names.")
    return stripped_count


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def run_wave60_stage3():
    print("=" * 70)
    print("Wave 60 Stage 3: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    a1 = execute_silpakorn_engineering_en(db)
    a2 = execute_psu_internal_medicine(db)
    a3 = execute_thammasat_attm(db)
    a4 = execute_thammasat_allied_slugs(db)
    a5 = execute_swu_dentistry(db)
    a6 = execute_silpakorn_pharmacy(db)
    a7 = execute_safe_trailing_consonant_stripping(db)

    total_ops = a1 + a2 + a3 + a4 + a5 + a6 + a7

    ckpt_file = CHECKPOINT_DIR / "wave60_stage3_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "silpakorn_engineering_en_updated": a1,
        "psu_internal_medicine_updated": a2,
        "thammasat_attm_updated": a3,
        "thammasat_allied_slugs_updated": a4,
        "swu_dentistry_updated": a5,
        "silpakorn_pharmacy_updated": a6,
        "trailing_consonants_stripped": a7,
        "total_operations": total_ops,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_stage3()
