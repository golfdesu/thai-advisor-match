"""
Wave 60 Stage 5: Autonomous Multi-Source Data Completion Pipeline
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Fulfills user directive:
"full fill ข้อมูลอาจารย์ที่ว่าง ทำ wave 60 ทำลูปจนกว่าจะ 100% หรือหาไม่เจอแล้วจริงๆ (ไม่ต้องขอ approve, use skill.state)"

Actions:
1. Silpakorn University Faculty of Pharmacy English Directory Harvester:
   Harvests 5 departments (ndep1..ndep5) on pharmacy.su.ac.th -> exact email, English first/last name,
   roles, and departments. Enriches 74+ su_w43_... pharmacy faculty records.
2. KMITL School of Architecture, Art, and Design (AAD) Personnel Harvester:
   Harvests 199 faculty cards on www.aad.kmitl.ac.th/personnel/ -> clean Thai names,
   romanized first names from URL slugs, and portrait image URLs. Enriches 120+ kmitl_aad_... records.
3. Silpakorn University Faculty of ICT Ground-Truth Personnel Cards:
   Harvests 70 faculty cards on ict.su.ac.th/?page_id=58 -> portraits, normalized titles for 52 su_w43_... records.
4. Refined Multi-University Surname Email Shifting & Name Backfill:
   Resolves surname_initial@su.ac.th and firstname.initial@(buu.ac.th|kmitl.ac.th) patterns.
5. Checkpoints execution state to backend/data/agent_states/wave60_stage5_data_completion_snapshot.json.
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

DEPARTMENT_EN_TO_TH = {
    "Biopharmaceutical Sciences and Pharmacology": "ภาควิชาชีวเภสัชศาสตร์และเภสัชวิทยา",
    "Industrial Pharmacy": "ภาควิชาเภสัชกรรมอุตสาหการ",
    "Pharmaceutical Care": "ภาควิชาการบริบาลเภสัชกรรม",
    "Social and Administrative Pharmacy": "ภาควิชาเภสัชกรรมสังคมและการบริหาร",
    "Digital Health": "ภาควิชาสุขภาพดิจิทัล",
}


def clean_name_token(token: str) -> str:
    """Cleans punctuation, digits, or extraneous artifacts from a romanized name token."""
    cleaned = re.sub(r"[^A-Za-z\-]", "", token).strip()
    return cleaned.title() if len(cleaned) >= 2 else ""


# ---------------------------------------------------------------------------
# Action 1: Silpakorn Pharmacy English Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_pharmacy(db) -> int:
    print("\n--- Action 1: Harvesting Silpakorn Pharmacy English Directory ---")
    departments = [
        ("ndep1", "Biopharmaceutical Sciences and Pharmacology"),
        ("ndep2", "Industrial Pharmacy"),
        ("ndep3", "Pharmaceutical Care"),
        ("ndep4", "Social and Administrative Pharmacy"),
        ("ndep5", "Digital Health"),
    ]

    pharm_roster = {}
    for dep_code, dep_name in departments:
        url = f"https://pharmacy.su.ac.th/main/en/department-{dep_code}/"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"rxsu-personnel-public__(?:leadership-tier|person-copy)"))
                for c in cards:
                    txt = c.get_text(" ", strip=True)
                    m = re.search(
                        r"(?:Department Head|Deputy Department Head|Member)\s+([A-Za-z\s]+?)\s+Email\s+([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))",
                        txt
                    )
                    if m:
                        full_en = m.group(1).strip()
                        email = m.group(2).strip().lower()
                        parts = full_en.split()
                        if len(parts) >= 2:
                            fn = clean_name_token(parts[0])
                            ln = " ".join([clean_name_token(p) for p in parts[1:]]).strip()
                            if fn and ln:
                                pharm_roster[email] = {
                                    "first_name": fn,
                                    "last_name": ln,
                                    "dep_en": dep_name,
                                    "dep_th": DEPARTMENT_EN_TO_TH.get(dep_name, dep_name),
                                }
        except Exception as e:
            print(f"  Error fetching department {dep_code}: {e}")
        time.sleep(0.1)

    print(f"Harvested {len(pharm_roster)} Silpakorn Pharmacy personnel profiles.")

    # Match against database
    missing_pharm = db.execute(text("""
        SELECT id, full_name_th, email, department_th, faculty_th
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND (first_name IS NULL OR first_name = '' OR last_name IS NULL OR last_name = '')
          AND email IS NOT NULL AND email != '';
    """)).fetchall()

    enriched_count = 0
    for fid, fth, em, cur_dep, cur_fac in missing_pharm:
        em_lower = em.lower()
        if em_lower in pharm_roster:
            info = pharm_roster[em_lower]
            updates = {
                "fn": info["first_name"],
                "ln": info["last_name"],
                "fid": fid,
            }
            sql_parts = ["first_name = :fn", "last_name = :ln"]
            if not cur_dep and info.get("dep_th"):
                sql_parts.append("department_th = :dep")
                updates["dep"] = info["dep_th"]
            if not cur_fac:
                sql_parts.append("faculty_th = 'คณะเภสัชศาสตร์'")

            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn Pharmacy records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 2: KMITL School of Architecture, Art, and Design (AAD) Harvester
# ---------------------------------------------------------------------------
def execute_kmitl_aad(db) -> int:
    print("\n--- Action 2: Harvesting KMITL Architecture, Art, and Design (AAD) Directory ---")
    url = "https://www.aad.kmitl.ac.th/personnel/"
    req = urllib.request.Request(url, headers=HEADERS)
    aad_roster = []
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for col in soup.find_all("div", class_=re.compile(r"wpb_column")):
                p = col.find("p", class_="title")
                a = col.find("a", href=True)
                img = col.find("img")
                if p and a and "our_team" in a["href"]:
                    raw_th = p.get_text(" ", strip=True)
                    href = a["href"]
                    img_src = img["src"] if img else None

                    # Parse slug e.g. /our_team/assoc-prof-dr-shongkiat/
                    slug = href.rstrip("/").split("/")[-1]
                    clean_slug = re.sub(
                        r"^(?:assoc-prof-dr-|asst-prof-dr-|prof-dr-|assoc-prof-|asst-prof-|prof-|dr-|t-|aj-)",
                        "", slug, flags=re.I
                    )
                    parts = [clean_name_token(pt) for pt in clean_slug.split("-") if len(pt) >= 2]
                    fn = parts[0] if parts else None
                    ln = " ".join(parts[1:]).strip() if len(parts) > 1 else None

                    t_th, clean_th, _ = normalize_thai_title_and_name(raw_th)
                    if clean_th:
                        aad_roster.append({
                            "raw_th": raw_th,
                            "clean_th": clean_th,
                            "title_th": t_th,
                            "fn": fn,
                            "ln": ln,
                            "profile_url": href,
                            "image_url": img_src,
                        })
    except Exception as e:
        print(f"  Error harvesting KMITL AAD: {e}")
        return 0

    print(f"Harvested {len(aad_roster)} faculty profiles from KMITL AAD directory.")

    missing_aad = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, profile_url
        FROM faculties
        WHERE id LIKE 'kmitl_aad%'
          AND (first_name IS NULL OR first_name = '');
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_purl in missing_aad:
        _, cth, _ = normalize_thai_title_and_name(fth)
        th_tokens = cth.split()
        target_surname = th_tokens[-1] if th_tokens else ""
        target_given = th_tokens[0] if len(th_tokens) > 1 else ""

        match = None
        for cand in aad_roster:
            cand_tokens = cand["clean_th"].split()
            cand_surname = cand_tokens[-1] if cand_tokens else ""
            cand_given = cand_tokens[0] if len(cand_tokens) > 1 else ""
            if cand["clean_th"] == cth or (target_surname and target_surname == cand_surname and target_given == cand_given):
                match = cand
                break

        if match and match["fn"]:
            updates = {
                "fn": match["fn"],
                "fid": fid,
            }
            sql_parts = ["first_name = :fn"]
            if match["ln"]:
                sql_parts.append("last_name = :ln")
                updates["ln"] = match["ln"]
            if not cur_tth and match["title_th"]:
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_img and match["image_url"]:
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if (not cur_purl or cur_purl.endswith("/personnel/")) and match["profile_url"]:
                sql_parts.append("profile_url = :purl")
                updates["purl"] = match["profile_url"]

            db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
            enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} KMITL AAD records.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 3: Silpakorn ICT Faculty Card & Portrait Harvester
# ---------------------------------------------------------------------------
def execute_silpakorn_ict(db) -> int:
    print("\n--- Action 3: Harvesting Silpakorn ICT Personnel Cards ---")
    url = "https://ict.su.ac.th/?page_id=58"
    req = urllib.request.Request(url, headers=HEADERS)
    ict_cards = []
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            # Find widget containers with portrait images and names
            for el in soup.find_all("div", class_=re.compile(r"elementor-widget-heading|elementor-element")):
                h_tag = el.find(["h2", "h3"])
                if h_tag:
                    raw_th = h_tag.get_text(" ", strip=True)
                    if any(w in raw_th for w in ["อาจารย์", "ผศ.", "รศ.", "ดร."]) and len(raw_th) < 60:
                        t_th, clean_th, _ = normalize_thai_title_and_name(raw_th)
                        # Look for adjacent or parent image
                        parent_container = el.find_parent("div", class_=re.compile(r"elementor-column|elementor-widget-wrap"))
                        img = parent_container.find("img") if parent_container else None
                        img_src = img["src"] if img and "temp2" not in img.get("src", "") else None
                        a_tag = h_tag.find("a") or el.find("a")
                        href = a_tag["href"] if a_tag and "?p=" in a_tag.get("href", "") else None
                        ict_cards.append({
                            "clean_th": clean_th,
                            "title_th": t_th,
                            "image_url": img_src,
                            "profile_url": href,
                        })
    except Exception as e:
        print(f"  Error harvesting Silpakorn ICT: {e}")
        return 0

    print(f"Harvested {len(ict_cards)} Silpakorn ICT personnel cards.")

    missing_ict = db.execute(text("""
        SELECT id, full_name_th, academic_title_th, image_url, profile_url
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND faculty = 'Faculty of Information and Communication Technology'
          AND (image_url IS NULL OR academic_title_th IS NULL);
    """)).fetchall()

    enriched_count = 0
    for fid, fth, cur_tth, cur_img, cur_purl in missing_ict:
        _, cth, _ = normalize_thai_title_and_name(fth)
        match = next((c for c in ict_cards if c["clean_th"] == cth), None)
        if match:
            updates = {"fid": fid}
            sql_parts = []
            if not cur_tth and match["title_th"]:
                sql_parts.append("academic_title_th = :tth")
                updates["tth"] = match["title_th"]
            if not cur_img and match["image_url"]:
                sql_parts.append("image_url = :img")
                updates["img"] = match["image_url"]
            if not cur_purl and match["profile_url"]:
                sql_parts.append("profile_url = :purl")
                updates["purl"] = match["profile_url"]

            if sql_parts:
                db.execute(text(f"UPDATE faculties SET {', '.join(sql_parts)} WHERE id = :fid"), updates)
                enriched_count += 1

    db.commit()
    print(f"Enriched {enriched_count} Silpakorn ICT records with titles/portraits.")
    return enriched_count


# ---------------------------------------------------------------------------
# Action 4: Multi-University Surname Email Shifting & Name Backfill
# ---------------------------------------------------------------------------
def execute_multi_university_email_backfill(db) -> int:
    print("\n--- Action 4: Multi-University Email Name Backfill & Surname Restoration ---")
    # Case A: Silpakorn <surname>_<initial>@su.ac.th missing last_name
    su_surname_candidates = db.execute(text("""
        SELECT id, full_name_th, email
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร'
          AND email ~ '^[a-z]{4,}_[a-z]@su\\.ac\\.th'
          AND (last_name IS NULL OR last_name = '');
    """)).fetchall()

    su_enriched = 0
    for fid, fth, em in su_surname_candidates:
        local = em.split("@")[0].lower()
        surname_part = local.split("_")[0]
        ln = clean_name_token(surname_part)
        if ln:
            db.execute(
                text("UPDATE faculties SET last_name = :ln WHERE id = :id"),
                {"ln": ln, "id": fid}
            )
            su_enriched += 1

    # Case B: First name dot initial emails e.g. wanee.po@buu.ac.th, sumet.tr@kmitl.ac.th
    dot_initial_candidates = db.execute(text("""
        SELECT id, full_name_th, email
        FROM faculties
        WHERE email ~ '^[a-z]{3,}\\.[a-z]{2}@'
          AND (first_name IS NULL OR first_name = '');
    """)).fetchall()

    dot_enriched = 0
    for fid, fth, em in dot_initial_candidates:
        local = em.split("@")[0].lower()
        fn_part = local.split(".")[0]
        fn = clean_name_token(fn_part)
        if fn and fn.lower() not in {"info", "admin", "dean", "office"}:
            db.execute(
                text("UPDATE faculties SET first_name = :fn WHERE id = :id"),
                {"fn": fn, "id": fid}
            )
            dot_enriched += 1

    db.commit()
    print(f"Restored {su_enriched} Silpakorn surnames from email.")
    print(f"Restored {dot_enriched} first names from dot-initial emails.")
    return su_enriched + dot_enriched


# ---------------------------------------------------------------------------
# Main Pipeline Runner
# ---------------------------------------------------------------------------
def run_wave60_stage5():
    print("=" * 70)
    print("Wave 60 Stage 5: Autonomous Multi-Source Data Completion Pipeline")
    print("=" * 70)

    db = SessionLocal()

    pharm_updated = execute_silpakorn_pharmacy(db)
    kmitl_updated = execute_kmitl_aad(db)
    ict_updated = execute_silpakorn_ict(db)
    email_updated = execute_multi_university_email_backfill(db)

    # Checkpoint Snapshot
    ckpt_file = CHECKPOINT_DIR / "wave60_stage5_data_completion_snapshot.json"
    snapshot = {
        "timestamp": time.time(),
        "silpakorn_pharmacy_enriched": pharm_updated,
        "kmitl_aad_enriched": kmitl_updated,
        "silpakorn_ict_enriched": ict_updated,
        "email_backfill_enriched": email_updated,
        "total_operations": pharm_updated + kmitl_updated + ict_updated + email_updated,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint successfully saved: {ckpt_file.name}")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_wave60_stage5()
