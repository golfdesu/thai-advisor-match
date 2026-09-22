"""
Wave 60 Stage 2: Autonomous Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (use skill.state)"

Actions:
1. Refined Institutional Email Name Extraction (T2) - fix greedy prefix blocklist.
2. Silpakorn Inverted Name Correction - shift surname from first_name to last_name.
3. SWU Medical Staff Harvester (med.swu.ac.th/../staff/).
4. PSU Surat Thani SCIT Harvester (scit.surat.psu.ac.th/p_person_dt).
5. TSU Researcher Directory Harvester (research.tsu.ac.th/researcher-detail.php).
6. BUU HUSO & Science & Medicine Harvester (huso.buu.ac.th, science.buu.ac.th, med.buu.ac.th).
7. Silpakorn CP Harvester (cp.su.ac.th/teacher).
8. Naresuan University Faculty_th Backfill.
9. Noise Name Sanitization & Final Checkpoint.
"""

import http.cookiejar
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
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

TITLE_EN_STRIP = re.compile(
    r"^(?:Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|Lecturer\s*Dr\.|"
    r"Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*",
    re.I
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

# Genuine organizational/service mailbox blocklist (delimited to prevent matching Thai names)
MAILBOX_BLOCK = re.compile(
    r"^(?:info|admin|administrator|contact|secretary|secretar|office|itunit|webmail|postmaster|"
    r"dean|pr|hr|academic|helpdesk|registrar|finance|general|library|hospital|clinic|"
    r"admission|admissions|service|support|student|alumni)(?:[._\-]|$)",
    re.I
)

NOISE_WORDS = {
    "publications", "publication", "email", "tel", "fax", "position", "department",
    "faculty", "university", "research", "interest", "interests", "profile",
    "homepage", "google", "scholar", "scopus", "detail", "uri", "index",
    "personnel", "teacher", "members", "member", "directory", "academic", "staff",
    "people", "personal", "search", "head", "office", "administration", "view",
    "more", "page", "curriculum", "vitae", "cv", "th", "en", "and", "the", "of",
    "division", "center", "programme", "program", "course", "home",
    "md", "mr", "ms", "drs", "prof", "assoc", "asst", "dr",
}


def parse_title_en(raw_name: str) -> tuple[str, str, str]:
    """Returns (title_th, title_en, clean_name)."""
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


def fetch_url(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return ""


# ---------------------------------------------------------------------------
# Action 1: Refined Institutional Email Name Extraction
# ---------------------------------------------------------------------------
def execute_refined_email_name_resolution(db) -> int:
    print("\n--- Action 1: Refined Institutional Email Name Extraction ---")
    rows = db.execute(text("""
        SELECT id, full_name_th, email
        FROM faculties
        WHERE first_name IS NULL
          AND email IS NOT NULL;
    """)).fetchall()

    updated = 0
    for fid, fn_th, em in rows:
        local = em.split("@")[0].strip().lower()
        domain = em.split("@")[1].strip().lower() if "@" in em else ""
        if MAILBOX_BLOCK.match(local):
            continue

        # Check Silpakorn pattern: lastname_initial@su.ac.th
        if "su.ac.th" in domain and re.match(r"^[a-z]{4,}_[a-z]$", local):
            ln = local.split("_")[0].title()
            db.execute(text("UPDATE faculties SET last_name = :ln WHERE id = :fid"), {"ln": ln, "fid": fid})
            updated += 1
            continue

        parts = [p for p in re.split(r"[._\-]+", local) if len(p) >= 2]
        if not parts:
            continue
        first_tok = parts[0]
        if len(first_tok) >= 3 and first_tok not in NOISE_WORDS and not any(c.isdigit() for c in first_tok) and re.match(r"^[a-z]+$", first_tok):
            fn = first_tok.title()
            ln = None
            if len(parts) >= 2:
                last_tok = " ".join(parts[1:])
                if len(last_tok) >= 4 and not any(c.isdigit() for c in last_tok) and last_tok not in NOISE_WORDS and re.match(r"^[a-z\s]+$", last_tok):
                    ln = last_tok.title()

            sql = "UPDATE faculties SET first_name = :fn"
            params = {"fn": fn, "fid": fid}
            if ln:
                sql += ", last_name = :ln"
                params["ln"] = ln
            sql += " WHERE id = :fid"
            db.execute(text(sql), params)
            updated += 1

    db.commit()
    print(f"Refined email extraction enriched {updated:,} records.")
    return updated


# ---------------------------------------------------------------------------
# Action 2: Silpakorn Inverted Name Correction
# ---------------------------------------------------------------------------
def execute_silpakorn_name_shift(db) -> int:
    print("\n--- Action 2: Silpakorn Inverted Name Correction ---")
    rows = db.execute(text("""
        SELECT id, full_name_th, first_name, email
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND email ~ '^[a-z]+_[a-z]@su\.ac\.th'
          AND last_name IS NULL
          AND first_name IS NOT NULL;
    """)).fetchall()

    shifted = 0
    for fid, fn_th, fn, em in rows:
        # In Silpakorn email 'klomjit_p', 'klomjit' is the surname
        local_prefix = em.split("@")[0].split("_")[0].title()
        db.execute(text("""
            UPDATE faculties
            SET last_name = :ln, first_name = NULL
            WHERE id = :fid
        """), {"ln": local_prefix, "fid": fid})
        shifted += 1

    db.commit()
    print(f"Shifted {shifted:,} Silpakorn surnames from first_name to last_name.")
    return shifted


# ---------------------------------------------------------------------------
# Action 3: SWU Medical Staff Harvester
# ---------------------------------------------------------------------------
def execute_swu_med_harvester(db) -> int:
    print("\n--- Action 3: Harvesting SWU Medical Staff Pages ---")
    depts = [
        ("anatomy", "ภาควิชากายวิภาคศาสตร์"),
        ("biochemistry", "ภาควิชาชีวเคมี"),
        ("eye", "ภาควิชาจักษุวิทยา"),
        ("forensic", "ภาควิชานิติเวชศาสตร์"),
        ("medicine", "ภาควิชาอายุรศาสตร์"),
        ("microbiology", "ภาควิชาจุลชีววิทยา"),
        ("ortho", "ภาควิชาออร์โธปิดิกส์"),
        ("physiology", "ภาควิชาสรีรวิทยา"),
        ("radiology", "ภาควิชารังสีวิทยา"),
        ("surgery", "ภาควิชาศัลยศาสตร์"),
        ("pediatrics", "ภาควิชากุมารเวชศาสตร์"),
        ("obgyn", "ภาควิชาสูติศาสตร์-นรีเวชวิทยา"),
        ("ent", "ภาควิชาโสต ศอ นาสิกวิทยา"),
        ("psychiatry", "ภาควิชาจิตเวชศาสตร์"),
        ("pathology", "ภาควิชาพยาธิวิทยา"),
        ("pharmacology", "ภาควิชาเภสัชวิทยา"),
        ("anesth", "ภาควิชาวิสัญญีวิทยา"),
        ("rehab", "ภาควิชาเวชศาสตร์ฟื้นฟู"),
    ]

    swu_map = {}
    for slug, dept_th in depts:
        url = f"https://med.swu.ac.th/{slug}/staff/"
        html = fetch_url(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all(["div", "p", "span"]):
            text_val = el.get_text(" ", strip=True)
            # Look for English Title + Name
            m = re.search(r"([ก-๙\.\s]+?)\s+(Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.)\s*([A-Za-z\.\s]+),\s*(?:M\.D\.|Ph\.D\.)?", text_val)
            if m:
                raw_th, t_en, raw_en = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                clean_en = TITLE_EN_STRIP.sub("", raw_en).strip()
                en_parts = clean_en.split()
                if len(en_parts) >= 2:
                    fn, ln = en_parts[0].title(), " ".join(en_parts[1:]).title()
                    # Clean Thai name
                    _, norm_full, _ = normalize_thai_title_and_name(raw_th)
                    key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*", "", norm_full).strip()
                    # Find image if available
                    img_src = None
                    parent_container = el.find_parent("div")
                    if parent_container:
                        for img in parent_container.find_all("img"):
                            src = img.get("src", "")
                            if "uploads" in src and ("200x" in src or "300x" in src or "staff" in src):
                                img_src = src
                                break
                    swu_map[key] = {
                        "fn": fn, "ln": ln, "t_en": t_en,
                        "dept_th": dept_th, "img": img_src, "norm_full": norm_full
                    }

    print(f"Scraped {len(swu_map)} personnel profiles from SWU Medicine departments.")

    updated = 0
    swu_records = db.execute(text("""
        SELECT id, full_name_th, first_name, image_url, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ'
          AND (faculty_th = 'คณะแพทยศาสตร์' OR profile_url LIKE '%med.swu.ac.th%');
    """)).fetchall()

    for fid, fth, cur_fn, cur_img, cur_dept in swu_records:
        clean_key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*", "", fth or "").strip()
        if clean_key in swu_map:
            info = swu_map[clean_key]
            sql_parts = []
            updates = {"fid": fid}
            if not cur_fn:
                sql_parts.extend(["first_name = :fn", "last_name = :ln"])
                updates["fn"] = info["fn"]
                updates["ln"] = info["ln"]
            if not cur_img and info.get("img"):
                sql_parts.append("image_url = :img")
                updates["img"] = info["img"]
            if not cur_dept and info.get("dept_th"):
                sql_parts.append("department_th = :dept")
                updates["dept"] = info["dept_th"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                updated += 1

    db.commit()
    print(f"Enriched {updated:,} SWU medical faculty records.")
    return updated


# ---------------------------------------------------------------------------
# Action 4: PSU Surat Thani SCIT Harvester
# ---------------------------------------------------------------------------
def execute_psu_scit_harvester(db) -> int:
    print("\n--- Action 4: Harvesting PSU Surat Thani (SCIT) Directory ---")
    rows = db.execute(text("""
        SELECT id, full_name_th, profile_url, email
        FROM faculties
        WHERE profile_url LIKE '%scit.surat.psu.ac.th%rec_id=%'
          AND first_name IS NULL;
    """)).fetchall()

    print(f"Found {len(rows)} PSU SCIT candidates to enrich...")
    updated = 0
    for fid, fth, purl, cur_em in rows:
        m = re.search(r"rec_id=(\d+)", purl or "")
        if not m:
            continue
        rid = m.group(1)
        url = f"https://scit.surat.psu.ac.th/p_person_dt?type=6&rec_id={rid}"
        html = fetch_url(url, timeout=6)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")

        # Extract title and English name
        fn, ln, em, t_th = None, None, None, None
        for div in soup.find_all(["div", "p"]):
            text_val = div.get_text(" ", strip=True)
            # Pattern: 'Asst. Prof. Dr. Nongyao Mueangdee'
            m_en = re.search(r"(?:Asst\.\s*Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Dr\.|Lecturer|Asst\.\s*Prof\.|Assoc\.\s*Prof\.)\s+([A-Za-z]+)\s+([A-Za-z\s]+?)(?=\s+(?:E-mail|Tel|Phone|โทร|ประวัติ|$))", text_val, re.I)
            if m_en:
                fn = m_en.group(1).title()
                ln = m_en.group(2).title().strip()

            # Pattern: Email
            m_em = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text_val)
            if m_em and not em:
                candidate_em = m_em.group(1).strip().lower()
                if "psu.ac.th" in candidate_em:
                    em = candidate_em

        if fn and ln:
            sql_parts = ["first_name = :fn", "last_name = :ln"]
            updates = {"fn": fn, "ln": ln, "fid": fid}
            if em and not cur_em:
                sql_parts.append("email = :em")
                updates["em"] = em
            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            updated += 1
        time.sleep(0.04)

    db.commit()
    print(f"Enriched {updated:,} PSU Surat Thani records.")
    return updated


# ---------------------------------------------------------------------------
# Action 5: TSU Researcher Directory Harvester
# ---------------------------------------------------------------------------
def execute_tsu_researcher_harvester(db) -> int:
    print("\n--- Action 5: Harvesting TSU Researcher Portal Directory ---")
    rows = db.execute(text("""
        SELECT id, full_name_th, profile_url, faculty_th, department_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยทักษิณ'
          AND profile_url LIKE '%research.tsu.ac.th/researcher-detail.php?id=%'
          AND first_name IS NULL;
    """)).fetchall()

    print(f"Found {len(rows)} TSU researcher candidates to enrich...")
    updated = 0
    for fid, fth, purl, cur_fac, cur_dept in rows:
        m = re.search(r"id=(\d+)", purl or "")
        if not m:
            continue
        rid = m.group(1)
        url = f"https://research.tsu.ac.th/researcher-detail.php?id={rid}"
        html = fetch_url(url, timeout=6)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        h2 = soup.find("h2")
        if not h2:
            continue

        p_name = h2.find_next_sibling("p")
        raw_en = p_name.get_text(" ", strip=True) if p_name else ""
        clean_en = TITLE_EN_STRIP.sub("", raw_en).strip()
        parts = clean_en.split()

        fn, ln = None, None
        if len(parts) >= 2 and all(re.match(r"^[A-Za-z\-]+$", p) for p in parts):
            fn = parts[0].title()
            ln = " ".join(parts[1:]).title()

        # Faculty and department
        fac_th, dept_th = None, None
        p_fac = p_name.find_next_sibling("p") if p_name else None
        if p_fac:
            fac_line = p_fac.get_text(" ", strip=True)
            if "|" in fac_line:
                fac_th = fac_line.split("|")[1].strip()
            p_dept = p_fac.find_next_sibling("p")
            if p_dept:
                dept_cand = p_dept.get_text(" ", strip=True)
                if dept_cand and len(dept_cand) < 40 and not dept_cand.isdigit():
                    dept_th = dept_cand

        if fn and ln:
            sql_parts = ["first_name = :fn", "last_name = :ln"]
            updates = {"fn": fn, "ln": ln, "fid": fid}
            if fac_th and not cur_fac:
                sql_parts.append("faculty_th = :fac")
                updates["fac"] = fac_th
            if dept_th and not cur_dept:
                sql_parts.append("department_th = :dept")
                updates["dept"] = dept_th

            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            updated += 1
        time.sleep(0.04)

    db.commit()
    print(f"Enriched {updated:,} TSU researcher records.")
    return updated


# ---------------------------------------------------------------------------
# Action 6: BUU HUSO & Science & Medicine Harvester
# ---------------------------------------------------------------------------
def execute_buu_harvester(db) -> int:
    print("\n--- Action 6: Harvesting Burapha University Directories ---")
    buu_updated = 0

    # 1. HUSO: huso.buu.ac.th/dpt/
    huso_html = fetch_url("https://huso.buu.ac.th/dpt/")
    if huso_html:
        soup = BeautifulSoup(huso_html, "html.parser")
        current_dept = None
        for line in soup.get_text("\n").split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("ภาควิชา") and len(line) < 35:
                current_dept = line
            elif re.match(r"^\d+\.\s+", line) and current_dept:
                clean_person = re.sub(r"^\d+\.\s+", "", line)
                clean_person = re.sub(r"\s*\(.*?\)", "", clean_person).strip()
                t_th, norm_full, _ = normalize_thai_title_and_name(clean_person)
                clean_key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*", "", norm_full).strip()

                # Update department in DB
                res = db.execute(text("""
                    UPDATE faculties
                    SET faculty_th = 'คณะมนุษยศาสตร์และสังคมศาสตร์',
                        department_th = :dept
                    WHERE university_th = 'มหาวิทยาลัยบูรพา'
                      AND (full_name_th LIKE :k OR full_name_th LIKE :nk)
                      AND department_th IS NULL
                """), {"dept": current_dept, "k": f"%{clean_key}%", "nk": f"%{norm_full}%"})
                buu_updated += res.rowcount

    # 2. Science: science.buu.ac.th/newweb/dept_detail.php?dept=1..9
    for d in range(1, 10):
        url = f"https://science.buu.ac.th/newweb/dept_detail.php?dept={d}"
        s_html = fetch_url(url)
        if not s_html:
            continue
        s_soup = BeautifulSoup(s_html, "html.parser")
        title_tag = s_soup.title.string if s_soup.title else ""
        dept_name = title_tag.split("|")[0].strip() if "|" in title_tag else "คณะวิทยาศาสตร์"

        for em_tag in s_soup.find_all(string=re.compile(r"@buu\.ac\.th")):
            parent = em_tag.parent
            for _ in range(4):
                if any(t in parent.get_text() for t in ["รศ.", "ผศ.", "อ.", "ดร."]):
                    break
                parent = parent.parent
            block_text = parent.get_text(" ", strip=True)

            m_em = re.search(r"([a-zA-Z0-9._%+-]+@buu\.ac\.th)", block_text)
            if not m_em:
                continue
            email_val = m_em.group(1).strip().lower()

            # Name part before phone extension / email
            name_part = block_text.split(email_val)[0].strip()
            name_part = re.sub(r"\d{3,5}.*$", "", name_part).strip()
            t_th, norm_full, _ = normalize_thai_title_and_name(name_part)
            clean_key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*", "", norm_full).strip()

            local_user = email_val.split("@")[0].split(".")[0].split("_")[0]
            fn_cand = local_user.title() if len(local_user) >= 3 and not any(c.isdigit() for c in local_user) else None

            updates = {"dept": dept_name, "em": email_val, "k": f"%{clean_key}%"}
            sql_parts = ["department_th = :dept", "email = :em"]
            if fn_cand:
                sql_parts.append("first_name = COALESCE(first_name, :fn)")
                updates["fn"] = fn_cand

            res = db.execute(text(f"""
                UPDATE faculties
                SET {', '.join(sql_parts)}
                WHERE university_th = 'มหาวิทยาลัยบูรพา'
                  AND full_name_th LIKE :k
                  AND (email IS NULL OR department_th IS NULL);
            """), updates)
            buu_updated += res.rowcount

    # 3. Medicine: med.buu.ac.th/med/teacher-med.php
    med_html = fetch_url("https://med.buu.ac.th/med/teacher-med.php")
    if med_html:
        m_soup = BeautifulSoup(med_html, "html.parser")
        for div in m_soup.find_all("div"):
            t_val = div.get_text(" ", strip=True)
            if "อีเมล :" in t_val and "@" in t_val:
                m_em = re.search(r"([a-zA-Z0-9._%+-]+@go\.buu\.ac\.th|[a-zA-Z0-9._%+-]+@buu\.ac\.th)", t_val)
                m_name = re.search(r"ชื่อ\s*:\s*([ก-๙\.\s]+?)(?=\s+ตำแหน่ง|\s+อีเมล|$)", t_val)
                if m_em and m_name:
                    em_val = m_em.group(1).strip().lower()
                    raw_th = m_name.group(1).strip()
                    _, norm_full, _ = normalize_thai_title_and_name(raw_th)
                    clean_key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.)\s*", "", norm_full).strip()

                    local_user = em_val.split("@")[0].split(".")[0].split("_")[0]
                    fn_cand = local_user.title() if len(local_user) >= 3 and not any(c.isdigit() for c in local_user) else None

                    updates = {"em": em_val, "k": f"%{clean_key}%"}
                    sql_parts = ["email = :em", "faculty_th = 'คณะแพทยศาสตร์'"]
                    if fn_cand:
                        sql_parts.append("first_name = COALESCE(first_name, :fn)")
                        updates["fn"] = fn_cand

                    res = db.execute(text(f"""
                        UPDATE faculties
                        SET {', '.join(sql_parts)}
                        WHERE university_th = 'มหาวิทยาลัยบูรพา'
                          AND full_name_th LIKE :k
                          AND email IS NULL;
                    """), updates)
                    buu_updated += res.rowcount

    db.commit()
    print(f"Enriched {buu_updated:,} Burapha University records.")
    return buu_updated


# ---------------------------------------------------------------------------
# Action 7: Silpakorn Computer Engineering Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_cp_harvester(db) -> int:
    print("\n--- Action 7: Harvesting Silpakorn CP Directory ---")
    updated = 0
    for tid in range(1, 30):
        url = f"https://cp.su.ac.th/teacher/{tid}"
        html = fetch_url(url, timeout=5)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        h3s = [h.get_text(" ", strip=True) for h in soup.find_all("h3")]
        if len(h3s) < 2:
            continue
        raw_th, raw_en = h3s[0], h3s[1]
        t_th, norm_full, _ = normalize_thai_title_and_name(raw_th)
        clean_en = TITLE_EN_STRIP.sub("", raw_en).strip()
        parts = clean_en.split()
        if len(parts) >= 2:
            fn, ln = parts[0].title(), " ".join(parts[1:]).title()
            clean_key = re.sub(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*", "", norm_full).strip()
            res = db.execute(text("""
                UPDATE faculties
                SET first_name = :fn, last_name = :ln,
                    department_th = 'ภาควิชาวิศวกรรมคอมพิวเตอร์',
                    faculty_th = 'คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม'
                WHERE university_th = 'มหาวิทยาลัยศิลปากร'
                  AND full_name_th LIKE :k
                  AND (first_name IS NULL OR last_name IS NULL);
            """), {"fn": fn, "ln": ln, "k": f"%{clean_key}%"})
            updated += res.rowcount

    db.commit()
    print(f"Enriched {updated:,} Silpakorn CP records.")
    return updated


# ---------------------------------------------------------------------------
# Action 8: Naresuan University Faculty_th Backfill
# ---------------------------------------------------------------------------
def execute_naresuan_backfill(db) -> int:
    print("\n--- Action 8: Backfilling Naresuan University Faculty_th ---")
    res = db.execute(text("""
        UPDATE faculties
        SET faculty_th = 'มหาวิทยาลัยนเรศวร',
            faculty = 'Naresuan University'
        WHERE faculty_th IS NULL
          AND faculty = 'มหาวิทยาลัยนเรศวร';
    """))
    db.commit()
    print(f"Backfilled faculty_th for {res.rowcount:,} Naresuan University records.")
    return res.rowcount


# ---------------------------------------------------------------------------
# Action 9: Noise Name Sanitization
# ---------------------------------------------------------------------------
def execute_noise_sanitization(db) -> int:
    print("\n--- Action 9: Sanitizing Noise Names & Clearing Shared Mailboxes ---")
    # Clean up non-person noise names
    res1 = db.execute(text("""
        UPDATE faculties
        SET first_name = NULL
        WHERE first_name IN ('Ighrd') AND email = 'ighrd@buu.ac.th';
    """))
    res2 = db.execute(text("""
        UPDATE faculties
        SET first_name = NULL, email = NULL
        WHERE id = 'tsu_w50_1469_926' AND email = 'eng@tsu.ac.th';
    """))
    res3 = db.execute(text("""
        UPDATE faculties
        SET email = NULL
        WHERE id = 'nu_w45_0067_273' AND email = 'wathanyoop@nu.ac.th';
    """))
    res4 = db.execute(text("""
        UPDATE faculties
        SET email = NULL
        WHERE id = 'buu_w42_0569_384' AND email = 'vichien@go.buu.ac.th';
    """))
    db.commit()
    cleaned = res1.rowcount + res2.rowcount + res3.rowcount + res4.rowcount
    print(f"Sanitized {cleaned} anomalous records.")
    return cleaned


def run_stage2_pipeline():
    print("=" * 70)
    print("Wave 60 Stage 2: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    a1 = execute_refined_email_name_resolution(db)
    a2 = execute_silpakorn_name_shift(db)
    a3 = execute_swu_med_harvester(db)
    a4 = execute_psu_scit_harvester(db)
    a5 = execute_tsu_researcher_harvester(db)
    a6 = execute_buu_harvester(db)
    a7 = execute_silpakorn_cp_harvester(db)
    a8 = execute_naresuan_backfill(db)
    a9 = execute_noise_sanitization(db)

    # Save Checkpoint
    ckpt_file = CHECKPOINT_DIR / "wave60_stage2_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "action1_email_names": a1,
        "action2_silpakorn_shifted": a2,
        "action3_swu_med_enriched": a3,
        "action4_psu_scit_enriched": a4,
        "action5_tsu_researcher_enriched": a5,
        "action6_buu_enriched": a6,
        "action7_silpakorn_cp_enriched": a7,
        "action8_naresuan_backfilled": a8,
        "action9_noise_sanitized": a9,
        "total_operations": a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_stage2_pipeline()
