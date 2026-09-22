"""
Wave 60 Stage 4: Autonomous Multi-Source Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (use skill.state)"

Actions:
1. Silpakorn Chemistry Next.js Harvester (chem.sc.su.ac.th/staff)
2. Silpakorn Biology Bilingual Harvester (bio.sc.su.ac.th/personnel-in-english & /personnel)
3. Silpakorn Physics Bilingual & Email Harvester (phy.sc.su.ac.th/people.html)
4. Silpakorn Mathematics Rich Profile Harvester (math.sc.su.ac.th/?page_id=57)
5. Silpakorn Statistics Harvester (stat.sc.su.ac.th/บุคลากร/)
6. Silpakorn Microbiology Harvester (micro.sc.su.ac.th/instructors/)
7. SWU Dentistry Multi-Tab Harvester (dent.swu.ac.th/Default.aspx?tabid=...)
8. Burapha University Informatics Multi-Threaded Harvester (informatics.buu.ac.th/?page_id=349)
9. Comprehensive Academic Title Normalization for Thai Faculty (academic_title_th IS NULL OR '')
10. State Checkpoint in backend/data/agent_states/wave60_stage4_data_completion_snapshot.json
"""

import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
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

TITLE_TH_STRIP = re.compile(
    r"^(?:ศาสตราจารย์\s*เกียรติคุณ\s*ดร\.|ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"อาจารย์\s*ดร\.|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศาสตราจารย์\s*เกียรติคุณ|ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพ\.|ทพญ\.|นพ\.|พญ\.|ภก\.|ภญ\.|"
    r"นายแพทย์|แพทย์หญิง|ทันตแพทย์|ทันตแพทย์หญิง|เภสัชกร|เภสัชกรหญิง|"
    r"นาย|นางสาว|นาง|ว่าที่\s*ร\.ต\.|ม\.ล\.)\s*",
    re.I
)

TITLE_EN_STRIP = re.compile(
    r"^(?:Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|Assist\.\s*Prof\.\s*Dr\.|Lecturer\s*Dr\.|Lect\.\s*Dr\.|"
    r"Emeritus\s*Prof\.\s*Dr\.|"
    r"Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Assist\.\s*Prof\.|Dr\.|Lecturer|Lect\.|Mr\.|Mrs\.|Ms\.|Miss)\s*",
    re.I
)

TITLE_EN_TO_TH = [
    (re.compile(r"^Prof\.\s*Dr\.", re.I), "ศ.ดร.", "Prof. Dr."),
    (re.compile(r"^Assoc\.\s*Prof\.\s*Dr\.", re.I), "รศ.ดร.", "Assoc. Prof. Dr."),
    (re.compile(r"^(?:Asst\.|Assist\.)\s*Prof\.\s*Dr\.", re.I), "ผศ.ดร.", "Asst. Prof. Dr."),
    (re.compile(r"^(?:Lecturer|Lect\.)\s*Dr\.", re.I), "อ.ดร.", "Lecturer Dr."),
    (re.compile(r"^Prof\.", re.I), "ศ.", "Prof."),
    (re.compile(r"^Assoc\.\s*Prof\.", re.I), "รศ.", "Assoc. Prof."),
    (re.compile(r"^(?:Asst\.|Assist\.)\s*Prof\.", re.I), "ผศ.", "Asst. Prof."),
    (re.compile(r"^Dr\.", re.I), "ดร.", "Dr."),
    (re.compile(r"^(?:Lecturer|Lect\.)", re.I), "อ.", "Lecturer"),
]

MAILBOX_BLOCK = re.compile(
    r"^(info|admin|secretar|faculty|depart|office|itunit|webmail|postmaster|"
    r"chemist|chemistry|biology|biolog|math|mathema|physic|zoo|botany|microbio|"
    r"anatomy|biochem|pharmac|pathol|parasit|food|agri|agricult|vet|nursing|"
    r"educat|psy|library|regist|finance|person|general|dean|hospi|med|pr)+",
    re.I
)

TH_TO_EN_INITIAL = {
    "ก": "k", "ข": "k", "ค": "k", "ง": "n", "จ": "c", "ฉ": "c", "ช": "c", "ซ": "s",
    "ญ": "y", "ด": "d", "ต": "t", "ถ": "t", "ท": "t", "ธ": "t", "น": "n", "บ": "b",
    "ป": "p", "ผ": "p", "ฝ": "f", "พ": "p", "ฟ": "f", "ภ": "p", "ม": "m", "ย": "y",
    "ร": "r", "ล": "l", "ว": "w", "ศ": "s", "ษ": "s", "ส": "s", "ห": "h", "อ": "a",
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
# Action 1: Silpakorn Chemistry Next.js Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_chem(db) -> int:
    print("\n--- Action 1: Harvesting Silpakorn Chemistry (chem.sc.su.ac.th) ---")
    url = "https://chem.sc.su.ac.th/staff"
    chem_staff = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            for m in re.finditer(r'\{\\"id\\":\\"(?P<id>[^"\\]+)\\",\\"name\\":\\"(?P<name>[^"\\]+)\\",\\"nameEn\\":\\"(?P<nameEn>[^"\\]+)\\"', html):
                d = m.groupdict()
                chem_staff.append((d["name"], d["nameEn"]))
    except Exception as e:
        print(f"  Error fetching Silpakorn Chem: {e}")

    print(f"Parsed {len(chem_staff)} staff profiles from Silpakorn Chemistry.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for raw_th, raw_en in chem_staff:
        clean_th = TITLE_TH_STRIP.sub("", raw_th).strip()
        th_tokens = clean_th.split()
        th_surname = th_tokens[-1] if th_tokens else ""

        tth, ten, clean_en = parse_title_en(raw_en)
        en_parts = clean_en.split()
        en_last = en_parts[-1].lower() if len(en_parts) >= 2 else ""

        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept in su_db_rows:
            if fid in matched_fids:
                continue
            is_match = False
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                is_match = True
            elif cur_ln and cur_ln.lower() == en_last:
                is_match = True

            if is_match:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if len(en_parts) >= 2:
                    fn = en_parts[0].title()
                    ln = " ".join(en_parts[1:]).title()
                    if not cur_fn:
                        sql_parts.append("first_name = :fn")
                        params["fn"] = fn
                    if not cur_ln:
                        sql_parts.append("last_name = :ln")
                        params["ln"] = ln

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาเคมี'")
                    sql_parts.append("department = 'Department of Chemistry'")

                if not cur_tth:
                    if tth:
                        sql_parts.append("academic_title_th = :tth")
                        params["tth"] = tth
                    elif clean_th:
                        norm_tth, _, _ = normalize_thai_title_and_name(clean_th)
                        sql_parts.append("academic_title_th = :tth")
                        params["tth"] = norm_tth

                # Update full_name_th if it was English display name from OpenAlex
                if not re.search(r"[ก-๙]", cur_fth or "") and clean_th:
                    _, norm_fth, _ = normalize_thai_title_and_name(clean_th)
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Chemistry records.")
    return updated


# ---------------------------------------------------------------------------
# Action 2: Silpakorn Biology Bilingual Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_biology(db) -> int:
    print("\n--- Action 2: Harvesting Silpakorn Biology (bio.sc.su.ac.th) ---")
    url_th = "https://bio.sc.su.ac.th/personnel"
    url_en = "https://bio.sc.su.ac.th/personnel-in-english"
    bio_pairs = []

    try:
        req_th = urllib.request.Request(url_th, headers=HEADERS)
        with urllib.request.urlopen(req_th, context=SSL_CTX, timeout=10) as resp:
            soup_th = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            th_items = []
            for a in soup_th.find_all("a", href=True):
                if "profile/" in a["href"]:
                    txt = a.get_text(" ", strip=True)
                    txt_clean = re.sub(r"(หัวหน้าภาควิชา|รองหัวหน้าภาค|ประธานหลักสูตร|อาจารย์ประจำภาค|อาจารย์).*$", "", txt).strip()
                    if any(k in txt_clean for k in ["ศ.", "รศ.", "ผศ.", "ดร.", "อาจารย์", "นาง", "นาย"]):
                        th_items.append(txt_clean)

        req_en = urllib.request.Request(url_en, headers=HEADERS)
        with urllib.request.urlopen(req_en, context=SSL_CTX, timeout=10) as resp:
            soup_en = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            en_items = []
            for p in soup_en.find_all(["p", "h3", "h4", "div"]):
                t = p.get_text(" ", strip=True)
                if re.match(r"^(?:Prof\.|Assoc\.\s*Prof\.|Assist\.\s*Prof\.|Dr\.|Lect\.)", t, re.I):
                    if len(t) < 80 and t not in en_items:
                        en_items.append(t)

        for i in range(min(len(th_items), len(en_items))):
            bio_pairs.append((th_items[i], en_items[i]))
    except Exception as e:
        print(f"  Error fetching Silpakorn Biology: {e}")

    print(f"Parsed {len(bio_pairs)} paired profiles from Silpakorn Biology.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, academic_title_th, faculty_th, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for raw_th, raw_en in bio_pairs:
        clean_th = TITLE_TH_STRIP.sub("", raw_th).strip()
        th_tokens = clean_th.split()
        th_surname = th_tokens[-1] if th_tokens else ""

        tth, ten, clean_en = parse_title_en(raw_en)
        en_parts = clean_en.split()
        en_last = en_parts[-1].lower() if len(en_parts) >= 2 else ""

        for fid, cur_fth, cur_fn, cur_ln, cur_tth, cur_fac, cur_dept in su_db_rows:
            if fid in matched_fids:
                continue
            is_match = False
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                is_match = True
            elif cur_ln and cur_ln.lower() == en_last:
                is_match = True

            if is_match:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if len(en_parts) >= 2:
                    fn = en_parts[0].title()
                    ln = " ".join(en_parts[1:]).title()
                    if not cur_fn:
                        sql_parts.append("first_name = :fn")
                        params["fn"] = fn
                    if not cur_ln:
                        sql_parts.append("last_name = :ln")
                        params["ln"] = ln

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาชีววิทยา'")
                    sql_parts.append("department = 'Department of Biology'")

                if not cur_tth and tth:
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = tth

                if not re.search(r"[ก-๙]", cur_fth or "") and clean_th:
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(clean_th)
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Biology records.")
    return updated


# ---------------------------------------------------------------------------
# Action 3: Silpakorn Physics Bilingual & Email Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_physics(db) -> int:
    print("\n--- Action 3: Harvesting Silpakorn Physics (phy.sc.su.ac.th) ---")
    url = "https://phy.sc.su.ac.th/people.html"
    phy_staff = []

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for c in soup.find_all("div", class_=re.compile(r"team|person|card|member|staff", re.I)):
                txt = c.get_text(" ", strip=True)
                m_en = re.search(r"(?:Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.)\s+([A-Za-z]+)\s+([A-Za-z]+)", txt)
                m_th = re.search(r"(ศ\.|รศ\.|ผศ\.|อ\.)?\s*ดร\.\s*([ก-๙]+)\s+([ก-๙]+)", txt)
                m_em = re.search(r"[\w\.-]+@su\.ac\.th", txt, re.I)
                img = c.find("img")
                img_src = img.get("src") if img else None
                if m_en and m_th:
                    full_img = urllib.parse.urljoin("https://phy.sc.su.ac.th/", img_src) if img_src else None
                    phy_staff.append({
                        "th_title": (m_th.group(1) or "อ.") + "ดร.",
                        "th_fn": m_th.group(2),
                        "th_ln": m_th.group(3),
                        "en_fn": m_en.group(1).title(),
                        "en_ln": m_en.group(2).title(),
                        "email": m_em.group(0).lower() if m_em else None,
                        "image_url": full_img,
                    })
    except Exception as e:
        print(f"  Error fetching Silpakorn Physics: {e}")

    print(f"Parsed {len(phy_staff)} faculty profiles from Silpakorn Physics.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th, image_url
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for doc in phy_staff:
        th_surname = doc["th_ln"]
        en_last = doc["en_ln"].lower()

        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept, cur_img in su_db_rows:
            if fid in matched_fids:
                continue
            is_match = False
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                is_match = True
            elif cur_ln and cur_ln.lower() == en_last:
                is_match = True

            if is_match:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if not cur_fn:
                    sql_parts.append("first_name = :fn")
                    params["fn"] = doc["en_fn"]
                if not cur_ln:
                    sql_parts.append("last_name = :ln")
                    params["ln"] = doc["en_ln"]

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาฟิสิกส์'")
                    sql_parts.append("department = 'Department of Physics'")

                if not cur_tth and doc.get("th_title"):
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = doc["th_title"]

                if not cur_em and doc.get("email"):
                    sql_parts.append("email = :em")
                    params["em"] = doc["email"]

                if not cur_img and doc.get("image_url"):
                    sql_parts.append("image_url = :img")
                    params["img"] = doc["image_url"]

                if not re.search(r"[ก-๙]", cur_fth or ""):
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(f"{doc['th_fn']} {doc['th_ln']}")
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Physics records.")
    return updated


# ---------------------------------------------------------------------------
# Action 4: Silpakorn Mathematics Rich Profile Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_math(db) -> int:
    print("\n--- Action 4: Harvesting Silpakorn Mathematics (math.sc.su.ac.th) ---")
    url = "http://math.sc.su.ac.th/?page_id=57"
    math_staff = []

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for p in soup.find_all(["p", "div", "td"]):
                txt = p.get_text(" ", strip=True)
                if any(k in txt for k in ["Professor", "Dr."]) and any(k in txt for k in ["ศ.", "รศ.", "ผศ.", "อ."]):
                    if len(txt) > 400:
                        continue
                    m_en = re.search(r"(?:Professor|Associate\s*Professor|Assistant\s*Professor|Dr\.|Miss|Mr\.|Mrs\.)\s*(?:Dr\.)?\s*([A-Za-z]+)\s+([A-Za-z]+)", txt)
                    m_th = re.search(r"(ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([ก-๙]+)\s+([ก-๙]+)", txt)
                    m_em = re.search(r"[\w\.-]+@su\.ac\.th", txt, re.I)
                    img = p.find("img")
                    img_src = img.get("src") if img else None
                    if m_en and m_th:
                        math_staff.append({
                            "th": m_th.group(0),
                            "th_fn": m_th.group(2),
                            "th_ln": m_th.group(3),
                            "en_fn": m_en.group(1).title(),
                            "en_ln": m_en.group(2).title(),
                            "email": m_em.group(0).lower() if m_em else None,
                            "image": img_src,
                        })
    except Exception as e:
        print(f"  Error fetching Silpakorn Math: {e}")

    # Deduplicate
    seen = set()
    unique_math = []
    for f in math_staff:
        if f["th"] not in seen:
            seen.add(f["th"])
            unique_math.append(f)

    print(f"Parsed {len(unique_math)} unique profiles from Silpakorn Mathematics.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th, image_url
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for doc in unique_math:
        th_surname = doc["th_ln"]
        en_last = doc["en_ln"].lower()

        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept, cur_img in su_db_rows:
            if fid in matched_fids:
                continue
            is_match = False
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                is_match = True
            elif cur_ln and cur_ln.lower() == en_last:
                is_match = True

            if is_match:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if not cur_fn:
                    sql_parts.append("first_name = :fn")
                    params["fn"] = doc["en_fn"]
                if not cur_ln:
                    sql_parts.append("last_name = :ln")
                    params["ln"] = doc["en_ln"]

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาคณิตศาสตร์'")
                    sql_parts.append("department = 'Department of Mathematics'")

                if not cur_tth:
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(doc["th"])
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = norm_tth

                if not cur_em and doc.get("email"):
                    sql_parts.append("email = :em")
                    params["em"] = doc["email"]

                if not cur_img and doc.get("image"):
                    sql_parts.append("image_url = :img")
                    params["img"] = doc["image"]

                if not re.search(r"[ก-๙]", cur_fth or ""):
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(f"{doc['th_fn']} {doc['th_ln']}")
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Mathematics records.")
    return updated


# ---------------------------------------------------------------------------
# Action 5: Silpakorn Statistics Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_stat(db) -> int:
    print("\n--- Action 5: Harvesting Silpakorn Statistics (stat.sc.su.ac.th) ---")
    url = "https://stat.sc.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/"
    stat_staff = []

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for div in soup.find_all(class_=re.compile(r"elementor-widget-container|team|member|box")):
                t = div.get_text(" ", strip=True)
                if any(k in t for k in ["อ.ดร.", "ผศ.ดร.", "รศ.ดร."]) and len(t) < 350:
                    m_th = re.search(r"(อ\.ดร\.|ผศ\.ดร\.|รศ\.ดร\.)\s*([ก-๙]+)\s+([ก-๙]+)", t)
                    m_em = re.search(r"[\w\.-]+@su\.ac\.th", t)
                    img = div.find("img")
                    img_src = img.get("src") if img else None

                    # Extract degrees if present
                    edu = []
                    for deg in re.findall(r"(?:Ph\.D\.|ปร\.ด\.|วท\.ม\.|สต\.ม\.|วท\.บ\.|วทบ\.)\s*\([^\)]+\)\s*[ก-๙A-Za-z\s]+", t):
                        deg_clean = deg.strip()
                        if len(deg_clean) > 5 and deg_clean not in edu:
                            edu.append(deg_clean)

                    if m_th:
                        stat_staff.append({
                            "title_th": m_th.group(1),
                            "first_th": m_th.group(2),
                            "last_th": m_th.group(3),
                            "email": m_em.group(0).lower() if m_em else None,
                            "image": img_src,
                            "education": edu,
                        })
    except Exception as e:
        print(f"  Error fetching Silpakorn Statistics: {e}")

    # Deduplicate by first_th + last_th
    seen = set()
    unique_stat = []
    for doc in stat_staff:
        k = (doc["first_th"], doc["last_th"])
        if k not in seen:
            seen.add(k)
            unique_stat.append(doc)

    print(f"Parsed {len(unique_stat)} faculty profiles from Silpakorn Statistics.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th, image_url, education
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for doc in unique_stat:
        th_surname = doc["last_th"]
        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept, cur_img, cur_edu in su_db_rows:
            if fid in matched_fids:
                continue
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาสถิติ'")
                    sql_parts.append("department = 'Department of Statistics'")

                if not cur_tth:
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = doc["title_th"]

                if not cur_em and doc.get("email"):
                    sql_parts.append("email = :em")
                    params["em"] = doc["email"]

                if not cur_img and doc.get("image"):
                    sql_parts.append("image_url = :img")
                    params["img"] = doc["image"]

                if (not cur_edu or cur_edu == []) and doc.get("education"):
                    sql_parts.append("education = :edu")
                    params["edu"] = json.dumps(doc["education"], ensure_ascii=False)

                # Extract last_name from email username if missing
                if not cur_ln and doc.get("email"):
                    local = doc["email"].split("@")[0]
                    parts = local.split("_")
                    if len(parts) >= 1 and len(parts[0]) >= 4:
                        sql_parts.append("last_name = :ln")
                        params["ln"] = parts[0].title()

                if not re.search(r"[ก-๙]", cur_fth or ""):
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(f"{doc['first_th']} {doc['last_th']}")
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Statistics records.")
    return updated


# ---------------------------------------------------------------------------
# Action 6: Silpakorn Microbiology Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_micro(db) -> int:
    print("\n--- Action 6: Harvesting Silpakorn Microbiology (micro.sc.su.ac.th) ---")
    url = "https://micro.sc.su.ac.th/instructors/"
    micro_staff = []

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for h in soup.find_all(["h2", "h3", "h4", "div", "p"]):
                txt = h.get_text(" ", strip=True)
                m_th = re.search(r"(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.)\s*([ก-๙]+)\s+([ก-๙]+)", txt)
                if m_th and len(txt) < 150:
                    parent = h.find_parent(["div", "section"])
                    em = None
                    scopus = None
                    if parent:
                        m_em = re.search(r"mailto:([\w\.-]+@(?:su\.ac\.th|silpakorn\.edu))", str(parent))
                        if m_em:
                            em = m_em.group(1).lower()
                        m_sc = re.search(r"https://www\.scopus\.com/authid/detail\.uri\?authorId=\d+", str(parent))
                        if m_sc:
                            scopus = m_sc.group(0)

                    micro_staff.append({
                        "title_th": m_th.group(1),
                        "first_th": m_th.group(2),
                        "last_th": m_th.group(3),
                        "email": em,
                        "scholar_url": scopus,
                    })
    except Exception as e:
        print(f"  Error fetching Silpakorn Micro: {e}")

    # Deduplicate
    seen = set()
    unique_micro = []
    for doc in micro_staff:
        k = (doc["first_th"], doc["last_th"])
        if k not in seen:
            seen.add(k)
            unique_micro.append(doc)

    print(f"Parsed {len(unique_micro)} faculty profiles from Silpakorn Microbiology.")

    su_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th, scholar_url
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for doc in unique_micro:
        th_surname = doc["last_th"]
        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept, cur_sch in su_db_rows:
            if fid in matched_fids:
                continue
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาศาสตร์'")
                    sql_parts.append("faculty = 'Faculty of Science'")
                if not cur_dept:
                    sql_parts.append("department_th = 'ภาควิชาจุลชีววิทยา'")
                    sql_parts.append("department = 'Department of Microbiology'")

                if not cur_tth:
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = doc["title_th"]

                if not cur_em and doc.get("email"):
                    sql_parts.append("email = :em")
                    params["em"] = doc["email"]

                if not cur_sch and doc.get("scholar_url"):
                    sql_parts.append("scholar_url = :sch")
                    params["sch"] = doc["scholar_url"]

                if not cur_ln and doc.get("email"):
                    local = doc["email"].split("@")[0]
                    parts = local.split("_")
                    if len(parts) >= 1 and len(parts[0]) >= 4:
                        sql_parts.append("last_name = :ln")
                        params["ln"] = parts[0].title()

                if not re.search(r"[ก-๙]", cur_fth or ""):
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(f"{doc['first_th']} {doc['last_th']}")
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Silpakorn Microbiology records.")
    return updated


# ---------------------------------------------------------------------------
# Action 7: SWU Dentistry Multi-Tab Harvester (Fixed Position Stripping)
# ---------------------------------------------------------------------------
def execute_swu_dentistry(db) -> int:
    print("\n--- Action 7: Harvesting SWU Dentistry (dent.swu.ac.th) ---")
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
                    if img:
                        src = img.get("src", "")
                        txt = thumb.get_text(" ", strip=True)
                        txt_clean = re.sub(r"(หัวหน้าภาควิชา|รองหัวหน้าภาค|ประธานหลักสูตร|อาจารย์ประจำภาค|อาจารย์).*$", "", txt).strip()
                        if any(k in txt_clean for k in ["ทพ.", "ทพญ.", "อ.", "ผศ.", "รศ.", "ศ.", "ดร."]):
                            dent_roster.append({
                                "name_th": txt_clean,
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

    updated = 0
    matched_fids = set()

    for doc in dent_roster:
        tokens = doc["name_th"].split()
        th_surname = tokens[-1] if tokens else ""

        for fid, cur_fth, cur_fn, cur_ln, cur_dth, cur_img in db_swu:
            if fid in matched_fids:
                continue
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                # Extract first_name from image filename (e.g. /portals/42/Images/Person/DGD/bhornsawan.JPG)
                img_stem = Path(doc["image_src"].split("?")[0]).stem.lower()
                if not cur_fn and len(img_stem) >= 4 and img_stem.isalpha() and img_stem not in ("person", "thumb", "noimage"):
                    surname_init = th_surname[0]
                    expected_c = TH_TO_EN_INITIAL.get(surname_init)
                    if expected_c and img_stem.endswith(expected_c):
                        fn_candidate = img_stem[:-1].title()
                    else:
                        fn_candidate = img_stem.title()
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
                break

    db.commit()
    print(f"Enriched {updated} SWU Dentistry faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 8: Burapha University Informatics Multi-Threaded Harvester
# ---------------------------------------------------------------------------
def execute_burapha_informatics(db) -> int:
    print("\n--- Action 8: Harvesting Burapha Informatics (informatics.buu.ac.th) ---")
    url = "https://informatics.buu.ac.th/?page_id=349"
    links = []

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "?instructors=" in href:
                    m = re.search(r"\?instructors=([a-z\-]+)", href)
                    if m:
                        links.append((m.group(1), href))
    except Exception as e:
        print(f"  Error fetching BUU Informatics: {e}")

    seen = set()
    unique_links = []
    for slug, href in links:
        if slug not in seen:
            seen.add(slug)
            unique_links.append((slug, href))

    def fetch_inst(item):
        slug, href = item
        try:
            r = urllib.request.Request(href, headers=HEADERS)
            with urllib.request.urlopen(r, context=SSL_CTX, timeout=8) as res:
                html = res.read().decode("utf-8", errors="ignore")
                s = BeautifulSoup(html, "html.parser")
                title_txt = s.title.string if s.title else ""
                clean_title = title_txt.split("–")[0].split("-")[0].strip()
                clean_title = re.sub(r"\(.*?\)", "", clean_title).strip()
                emails = re.findall(r"[\w\.-]+@go\.buu\.ac\.th", html)
                em = emails[0].lower() if emails else None
                return {"slug": slug, "raw_th": clean_title, "email": em}
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(filter(None, ex.map(fetch_inst, unique_links)))

    print(f"Parsed {len(results)} instructor profiles from BUU Informatics.")

    buu_db_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, academic_title_th, faculty_th, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยบูรพา';
    """)).fetchall()

    updated = 0
    matched_fids = set()

    for doc in results:
        raw_th = doc["raw_th"]
        clean_th = TITLE_TH_STRIP.sub("", raw_th).strip()
        th_tokens = clean_th.split()
        th_surname = th_tokens[-1] if th_tokens else ""

        slug_clean = re.sub(r"-\d*$", "", doc["slug"]).strip("-")
        slug_parts = slug_clean.split("-")
        en_first = slug_parts[0].title() if len(slug_parts) >= 1 else None
        en_last = " ".join(slug_parts[1:]).title() if len(slug_parts) >= 2 else None

        for fid, cur_fth, cur_fn, cur_ln, cur_em, cur_tth, cur_fac, cur_dept in buu_db_rows:
            if fid in matched_fids:
                continue
            is_match = False
            if th_surname and len(th_surname) >= 3 and th_surname in cur_fth:
                is_match = True
            elif en_last and cur_ln and cur_ln.lower() == en_last.lower():
                is_match = True

            if is_match:
                matched_fids.add(fid)
                sql_parts = []
                params = {"fid": fid}

                if en_first and not cur_fn:
                    sql_parts.append("first_name = :fn")
                    params["fn"] = en_first
                if en_last and not cur_ln:
                    sql_parts.append("last_name = :ln")
                    params["ln"] = en_last

                if not cur_fac:
                    sql_parts.append("faculty_th = 'คณะวิทยาการสารสนเทศ'")
                    sql_parts.append("faculty = 'Faculty of Informatics'")
                if not cur_dept:
                    sql_parts.append("department_th = 'สาขาวิชาวิทยาการคอมพิวเตอร์และสารสนเทศ'")

                if not cur_tth and raw_th:
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(raw_th)
                    sql_parts.append("academic_title_th = :tth")
                    params["tth"] = norm_tth

                if not cur_em and doc.get("email"):
                    sql_parts.append("email = :em")
                    params["em"] = doc["email"]

                if not re.search(r"[ก-๙]", cur_fth or "") and clean_th:
                    norm_tth, norm_fth, _ = normalize_thai_title_and_name(clean_th)
                    sql_parts.append("full_name_th = :fth")
                    params["fth"] = norm_fth

                if sql_parts:
                    db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), params)
                    updated += 1
                break

    db.commit()
    print(f"Enriched {updated} Burapha University Informatics records.")
    return updated


# ---------------------------------------------------------------------------
# Action 9: Comprehensive Academic Title Normalization for Thai Faculty
# ---------------------------------------------------------------------------
def execute_normalize_thai_titles(db) -> int:
    print("\n--- Action 9: Normalizing Academic Titles for Thai Faculty ---")
    missing_title_rows = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE full_name_th ~ '[ก-๙]'
          AND (academic_title_th IS NULL OR academic_title_th = '');
    """)).fetchall()

    print(f"Found {len(missing_title_rows):,} Thai faculty records missing academic_title_th.")
    updated = 0
    for fid, fn_th in missing_title_rows:
        t_th, clean_full, _ = normalize_thai_title_and_name(fn_th)
        db.execute(
            text("UPDATE faculties SET academic_title_th = :tth, full_name_th = :fth WHERE id = :id"),
            {"tth": t_th, "fth": clean_full, "id": fid}
        )
        updated += 1

    db.commit()
    print(f"Successfully normalized academic titles for {updated:,} Thai faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Master Execution Flow
# ---------------------------------------------------------------------------
def run_wave60_stage4_data_completion():
    print("=" * 70)
    print("Wave 60 Stage 4: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    c1 = execute_silpakorn_chem(db)
    c2 = execute_silpakorn_biology(db)
    c3 = execute_silpakorn_physics(db)
    c4 = execute_silpakorn_math(db)
    c5 = execute_silpakorn_stat(db)
    c6 = execute_silpakorn_micro(db)
    c7 = execute_swu_dentistry(db)
    c8 = execute_burapha_informatics(db)
    c9 = execute_normalize_thai_titles(db)

    # Checkpoint snapshot
    ckpt_file = CHECKPOINT_DIR / "wave60_stage4_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "silpakorn_chem_updated": c1,
        "silpakorn_bio_updated": c2,
        "silpakorn_phy_updated": c3,
        "silpakorn_math_updated": c4,
        "silpakorn_stat_updated": c5,
        "silpakorn_micro_updated": c6,
        "swu_dentistry_updated": c7,
        "burapha_informatics_updated": c8,
        "academic_titles_normalized": c9,
        "total_operations": c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print(f"Total Stage 4 Operations: {snapshot['total_operations']:,}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_stage4_data_completion()
