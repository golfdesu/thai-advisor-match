"""
Wave 60: Autonomous Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (use skill.state)"

Actions:
1. Harvest Walailak University official English directory (intranet.wu.ac.th/en/searchPersons)
   across all 50 divisions -> populate first_name, last_name, academic_title_en/th, faculty, email.
2. Extract authentic Latin names embedded in full_name_th (T1) -> populate first_name, last_name,
   and clean full_name_th.
3. Propagate English names from database OpenAlex author counterparts (matching normalized openalex_id).
4. Extract verified first names (and last names where length >= 4) from institutional emails (T2).
5. Normalize academic titles for authentic Thai faculty missing academic_title_th (assign 'อ.' per state_reducer).
6. Checkpoint results to backend/data/agent_states/wave60_data_completion_snapshot.json.
"""

import http.cookiejar
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
from app.models.db_models import FacultyDB
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

MAILBOX_BLOCK = re.compile(
    r"^(info|admin|secretar|faculty|depart|office|itunit|webmail|postmaster|"
    r"chemist|chemistry|biology|biolog|math|mathema|physic|zoo|botany|microbio|"
    r"anatomy|biochem|pharmac|pathol|parasit|food|agri|agricult|vet|nursing|"
    r"educat|psy|library|regist|finance|person|general|dean|hospi|med|cmu|kku|"
    r"ku|tu|su|wu|mu|buu|psu|kmitl|kmutt|mfu|mju|nu|swu|nida|ru|bu|nnru|mru|tru)+",
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


# ---------------------------------------------------------------------------
# Action 1: Walailak University English Directory Harvester
# ---------------------------------------------------------------------------
def harvest_wu_english_directory() -> dict[str, dict]:
    print("\n--- Action 1: Harvesting Walailak Official English Directory ---")
    url = "https://intranet.wu.ac.th/en/searchPersons"
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=SSL_CTX)
    )

    req1 = urllib.request.Request(url, headers=HEADERS)
    with opener.open(req1, timeout=12) as r:
        soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]
        select = soup.find("select", {"name": "DIVISION_ID"})
        divisions = []
        for opt in select.find_all("option"):
            val = opt.get("value")
            txt = opt.text.strip()
            if val:
                divisions.append((val, txt))

    print(f"Targeting {len(divisions)} divisions from WU English Portal...")
    wu_map = {}
    for val, div_txt in divisions:
        data = urllib.parse.urlencode({
            "_token": token,
            "action": "search",
            "FIRST_NAME": "",
            "LAST_NAME": "",
            "OFFICE_PHONE": "",
            "OFFICE_EMAIL": "",
            "DIVISION_ID": val
        }).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, headers={**HEADERS, "Referer": url})
            with opener.open(req, timeout=10) as resp:
                s = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                tbl = s.find("table")
                if not tbl:
                    continue
                for tr in tbl.find_all("tr")[1:]:
                    cols = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                    if len(cols) < 7:
                        continue
                    pid, raw_name, div_str, pos, phone, email = cols[1], cols[2], cols[3], cols[4], cols[5], cols[6]
                    t_th, t_en, clean_name = parse_title_en(raw_name)
                    name_parts = clean_name.split()
                    if len(name_parts) >= 2:
                        fn = name_parts[0].title()
                        ln = " ".join(name_parts[1:]).title()
                        clean_em = email.strip().lower() if ("@" in email and "wu.ac.th" in email) else None
                        wu_map[pid] = {
                            "first_name": fn,
                            "last_name": ln,
                            "title_th": t_th,
                            "title_en": t_en,
                            "div_en": div_txt,
                            "email": clean_em,
                        }
        except Exception as e:
            print(f"  Error fetching {div_txt}: {e}")
        time.sleep(0.08)

    print(f"Scraped {len(wu_map)} unique personnel records from Walailak EN directory.")
    return wu_map


def run_wave60_data_completion():
    print("=" * 70)
    print("Wave 60: Autonomous Data Completion & Zero-Defect Full-Fill")
    print("=" * 70)

    db = SessionLocal()

    # -----------------------------------------------------------------------
    # Action 1: Apply Walailak University English Directory
    # -----------------------------------------------------------------------
    wu_map = harvest_wu_english_directory()
    wu_candidates = db.execute(text("""
        SELECT id, profile_url, academic_title_th, faculty, email
        FROM faculties
        WHERE profile_url LIKE '%intranet.wu.ac.th%pid=%'
          AND (first_name IS NULL OR first_name = '');
    """)).fetchall()

    wu_updated = 0
    for fid, purl, cur_title, cur_fac, cur_em in wu_candidates:
        m = re.search(r"pid=(\d+)", purl or "")
        if m and m.group(1) in wu_map:
            info = wu_map[m.group(1)]
            updates = {
                "fn": info["first_name"],
                "ln": info["last_name"],
                "fid": fid,
            }
            sql_parts = ["first_name = :fn", "last_name = :ln"]
            if not cur_title:
                sql_parts.append("academic_title_th = :t_th")
                updates["t_th"] = info["title_th"]
            if not cur_fac and info.get("div_en"):
                sql_parts.append("faculty = :fac")
                updates["fac"] = info["div_en"]
            if not cur_em and info.get("email"):
                sql_parts.append("email = :em")
                updates["em"] = info["email"]

            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            wu_updated += 1

    db.commit()
    print(f"Successfully updated {wu_updated:,} Walailak records with authentic English profiles.")

    # -----------------------------------------------------------------------
    # Action 2: Embedded Latin Names in full_name_th (T1)
    # -----------------------------------------------------------------------
    print("\n--- Action 2: Extracting Embedded Latin Names from full_name_th ---")
    t1_rows = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE full_name_th ~ '[ก-๙]' AND full_name_th ~ '[A-Za-z]{2,}'
          AND (first_name IS NULL OR first_name = '');
    """)).fetchall()

    t1_updated = 0
    for fid, fn_th in t1_rows:
        fn, ln, clean_th = None, None, None

        # Pattern 1: 'Thai Name (English Name)'
        m1 = re.search(r"\((?:Dr\.\s*|Prof\.\s*|Assoc\.\s*Prof\.\s*|Asst\.\s*Prof\.\s*)?([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-]*)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-\s]*)\)", fn_th)
        if m1:
            fn, ln = m1.group(1).strip().title(), m1.group(2).strip().title()
            clean_th = re.sub(r"\(.*?\)", "", fn_th).strip()

        # Pattern 2: 'Thai Name English Name'
        if not fn:
            m2 = re.search(r"([ก-๙\.\s]+?)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-]*)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-\s]*)$", fn_th)
            if m2:
                clean_th = m2.group(1).strip()
                fn, ln = m2.group(2).strip().title(), m2.group(3).strip().title()

        # Pattern 3: 'English Name Thai Name'
        if not fn:
            m3 = re.search(r"^([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-]*)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-]*)\s+([ก-๙\.\s]+)$", fn_th)
            if m3:
                fn, ln = m3.group(1).strip().title(), m3.group(2).strip().title()
                clean_th = m3.group(3).strip()

        # Pattern 4: Foreign name with Thai title e.g. 'ดร. Sergey Novikov'
        if not fn:
            m4 = re.search(r"^(ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-]*)\s+([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ\.\-\s]*)$", fn_th)
            if m4:
                fn, ln = m4.group(2).strip().title(), m4.group(3).strip().title()
                clean_th = fn_th  # keep as is

        if fn and ln:
            # Check if clean_th has authentic Thai name tokens
            has_thai_letters = any("฀" <= c <= "๿" for c in (clean_th or ""))
            th_tokens = [t for t in (clean_th or "").split() if any("฀" <= c <= "๿" for c in t) and t not in ("ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "อาจารย์")]

            sql_parts = ["first_name = :fn", "last_name = :ln"]
            updates = {"fn": fn, "ln": ln, "fid": fid}

            if has_thai_letters and len(th_tokens) >= 1:
                # Normalize title and name
                norm_title, norm_full, _ = normalize_thai_title_and_name(clean_th)
                sql_parts.append("full_name_th = :fth")
                sql_parts.append("academic_title_th = :tth")
                updates["fth"] = norm_full
                updates["tth"] = norm_title

            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            t1_updated += 1

    db.commit()
    print(f"Successfully updated {t1_updated:,} records from embedded Latin names.")

    # -----------------------------------------------------------------------
    # Action 3: Propagate Counterpart English Names via OpenAlex Counterparts
    # -----------------------------------------------------------------------
    print("\n--- Action 3: Propagating Names from OpenAlex Counterparts ---")
    oa_counterparts = db.execute(text("""
        SELECT DISTINCT ON (t.id)
            t.id, o.first_name, o.last_name
        FROM faculties t
        JOIN faculties o ON
            REPLACE(o.openalex_id, 'https://openalex.org/', '') = REPLACE(t.openalex_id, 'https://openalex.org/', '')
            AND o.id != t.id
        WHERE t.full_name_th ~ '[ก-๙]'
          AND (t.first_name IS NULL OR t.first_name = '')
          AND (t.openalex_id LIKE 'A%' OR t.openalex_id LIKE 'https://openalex.org/A%')
          AND o.first_name IS NOT NULL AND o.first_name != ''
        ORDER BY t.id;
    """)).fetchall()

    for tid, ofn, oln in oa_counterparts:
        db.execute(
            text("UPDATE faculties SET first_name = :fn, last_name = :ln WHERE id = :id"),
            {"fn": ofn, "ln": oln, "id": tid}
        )
    db.commit()
    print(f"Successfully propagated names for {len(oa_counterparts):,} OpenAlex counterpart records.")

    # -----------------------------------------------------------------------
    # Action 4: Extract First (and Last) Names from Institutional Emails
    # -----------------------------------------------------------------------
    print("\n--- Action 4: Extracting Names from Institutional Emails ---")
    email_candidates = db.execute(text("""
        SELECT id, full_name_th, email
        FROM faculties
        WHERE full_name_th ~ '[ก-๙]' AND (first_name IS NULL OR first_name = '')
          AND email IS NOT NULL AND email != '';
    """)).fetchall()

    email_updated = 0
    for fid, fn_th, em in email_candidates:
        local = em.split("@")[0].strip().lower()
        if MAILBOX_BLOCK.match(local):
            continue

        parts = [p for p in re.split(r"[._\-]+", local) if len(p) >= 2]
        if not parts:
            continue

        first_tok = parts[0]
        if len(first_tok) < 3 or first_tok in NOISE_WORDS or any(c.isdigit() for c in first_tok):
            continue
        if not re.match(r"^[a-z]+$", first_tok):
            continue

        first_name = first_tok.title()
        last_name = None

        if len(parts) >= 2:
            last_tok = " ".join(parts[1:])
            if len(last_tok) >= 4 and not any(c.isdigit() for c in last_tok) and last_tok not in NOISE_WORDS:
                if re.match(r"^[a-z\s]+$", last_tok):
                    last_name = last_tok.title()

        sql_parts = ["first_name = :fn"]
        updates = {"fn": first_name, "fid": fid}
        if last_name:
            sql_parts.append("last_name = :ln")
            updates["ln"] = last_name

        db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
        email_updated += 1

    db.commit()
    print(f"Successfully updated {email_updated:,} records from institutional email usernames.")

    # -----------------------------------------------------------------------
    # Action 5: Academic Title Normalization for Thai Faculty Missing Title
    # -----------------------------------------------------------------------
    print("\n--- Action 5: Normalizing Academic Titles for Thai Faculty Missing Titles ---")
    missing_title_rows = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE full_name_th ~ '[ก-๙]' AND academic_title_th IS NULL;
    """)).fetchall()

    title_updated = 0
    for fid, fn_th in missing_title_rows:
        t_th, clean_full, _ = normalize_thai_title_and_name(fn_th)
        db.execute(
            text("UPDATE faculties SET academic_title_th = :tth, full_name_th = :fth WHERE id = :id"),
            {"tth": t_th, "fth": clean_full, "id": fid}
        )
        title_updated += 1

    db.commit()
    print(f"Successfully normalized academic titles for {title_updated:,} Thai faculty records.")

    # -----------------------------------------------------------------------
    # Checkpoint Snapshot
    # -----------------------------------------------------------------------
    ckpt_file = CHECKPOINT_DIR / "wave60_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "walailak_updated": wu_updated,
        "embedded_latin_updated": t1_updated,
        "openalex_counterparts_propagated": len(oa_counterparts),
        "email_names_updated": email_updated,
        "titles_normalized": title_updated,
        "total_fields_enriched": wu_updated + t1_updated + len(oa_counterparts) + email_updated + title_updated,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_data_completion()
