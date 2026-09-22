"""Wave 60: Autonomous Faculty Data Enrichment Pipeline (SKILL.state 5-Pillars)

Fills missing faculty emails, Thai names, academic titles, faculties, and departments.
Implements a 3-Pass Iterative Loop until convergence:
  - Pass 1: In-Memory Cross-Checkpoint Enrichment (from 39 disk checkpoint files)
  - Pass 2: Headless Crawl of Unique 1-to-1 Profile URLs (ThreadPoolExecutor)
  - Pass 3: Cached Directory Crawl with Card-Level Name Matching for Shared URLs
"""

import sys
import re
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB

from sqlalchemy import text

# ─────────────────────────────────────────────────────────────
# Domain Whitelists & Hygiene Guards
# ─────────────────────────────────────────────────────────────
UNIVERSITY_DOMAINS: dict[str, list[str]] = {
    "Chulalongkorn University":                               ["chula.ac.th"],
    "Mahidol University":                                     ["mahidol.ac.th", "mahidol.edu"],
    "Prince of Songkla University":                           ["psu.ac.th"],
    "Khon Kaen University":                                   ["kku.ac.th"],
    "Thammasat University":                                   ["tu.ac.th"],
    "King Mongkut's Institute of Technology Ladkrabang":      ["kmitl.ac.th"],
    "King Mongkut's University of Technology Thonburi":       ["kmutt.ac.th"],
    "Chiang Mai University":                                  ["cmu.ac.th"],
    "Kasetsart University":                                   ["ku.ac.th", "ku.th"],
    "Silpakorn University":                                   ["su.ac.th", "silpakorn.edu"],
    "Srinakharinwirot University":                            ["swu.ac.th", "g.swu.ac.th"],
    "Burapha University":                                     ["buu.ac.th"],
    "Suranaree University of Technology":                     ["sut.ac.th"],
    "Naresuan University":                                    ["nu.ac.th"],
    "King Mongkut's University of Technology North Bangkok":  ["kmutnb.ac.th"],
    "Ramkhamhaeng University":                                ["ru.ac.th"],
    "Walailak University":                                    ["wu.ac.th"],
    "University of Phayao":                                   ["up.ac.th"],
    "Ubon Ratchathani University":                            ["ubu.ac.th"],
    "Thaksin University":                                     ["tsu.ac.th"],
    "National Institute of Development Administration":       ["nida.ac.th"],
    "Maejo University":                                       ["mju.ac.th"],
    "Mae Fah Luang University":                               ["mfu.ac.th"],
    "Mahasarakham University":                                ["msu.ac.th"],
    "Chulabhorn Research Institute":                          ["cri.or.th", "cgi.ac.th", "cra.ac.th"],
    "Chulabhorn Graduate Institute":                          ["cgi.ac.th", "cri.or.th", "cra.ac.th"],
    "Chulabhorn Royal Academy":                               ["cra.ac.th", "cgi.ac.th"],
}

GENERIC_OR_SHARED_EMAILS = {
    "research.tsu@tsu.ac.th", "admin@tsu.ac.th", "info@tsu.ac.th",
    "webadmin@sit.kmutt.ac.th", "grad@chula.ac.th", "commarts@chula.ac.th",
    "ie@eng.chula.ac.th", "survey@eng.chula.ac.th", "mining@eng.chula.ac.th",
    "water@eng.chula.ac.th", "cpe@eng.cmu.ac.th", "cpe@ku.ac.th", "cpe@kku.ac.th",
    "math@cmu.ac.th", "biology@cmu.ac.th", "intmed@cmu.ac.th", "ams@cmu.ac.th",
    "dsc@cmu.ac.th", "pediatrics@cmu.ac.th", "chemy@ku.ac.th", "fish@ku.ac.th",
    "ase@eng.ku.ac.th", "engineering@kku.ac.th", "chemistry@kmutt.ac.th",
    "microbiology@kmutt.ac.th", "stat@sci.kmutnb.ac.th", "cs@sci.kmutnb.ac.th",
    "ic@sci.kmutnb.ac.th", "agro@psu.ac.th", "allied@allied.tu.ac.th",
    "attm@med.tu.ac.th", "fac-en@silpakorn.edu", "contact@cmu.ac.th",
    "pr@chula.ac.th", "info@cmu.ac.th", "info@kku.ac.th", "admin@kku.ac.th"
}

GENERIC_PREFIXES = {
    "admin", "info", "contact", "office", "dean", "pr", "support", "help",
    "webmaster", "postmaster", "service", "academic", "registrar", "admission",
    "research", "hr", "secretary", "saraban", "center", "division", "faculty",
    "department", "staff", "public", "news", "mail", "general"
}

RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
RE_THAI_NAME = re.compile(r"[฀-๿]{2,}\s+[฀-๿]{2,}")
RE_TITLE = re.compile(r"(ศ\.\s*ดร\.|รศ\.\s*ดร\.|ผศ\.\s*ดร\.|อ\.\s*ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)")

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = 8
REQUEST_DELAY = 0.2
BATCH_SIZE = 100


def is_valid_university_email(email: str, univ_en: str) -> bool:
    """Validate university email domain and filter out generic/shared inboxes."""
    e = email.lower().strip().rstrip(".")
    if not e or "@" not in e:
        return False
    if e in GENERIC_OR_SHARED_EMAILS:
        return False

    local_part, domain_part = e.split("@", 1)
    if local_part in GENERIC_PREFIXES:
        return False

    # Disallow freemails
    if any(domain_part == f or domain_part.endswith("." + f) for f in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
        return False

    domains = UNIVERSITY_DOMAINS.get(univ_en, [])
    if not domains:
        # Generic check for Thai academic domain
        return domain_part.endswith(".ac.th") or domain_part.endswith(".edu")

    return any(domain_part == d or domain_part.endswith("." + d) for d in domains)


def fetch_url(url: str, timeout: int = 12) -> str:
    """Headless HTTP fetcher with User-Agent and length cap."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(250000).decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# PASS 1: Checkpoint-Based In-Memory Cross Enrichment
# ─────────────────────────────────────────────────────────────
def run_pass1_checkpoint_enrichment(db) -> int:
    """Extract missing emails and metadata from historical wave extraction checkpoints."""
    print("\n--- Pass 1: In-Memory Checkpoint State Reducer ---")
    files = glob.glob(str(CHECKPOINT_DIR / "*extraction*.json"))
    print(f"Loading {len(files)} extraction checkpoints...")

    lookup_by_th: dict[tuple[str, str], dict] = {}
    lookup_by_en: dict[tuple[str, str], dict] = {}
    lookup_by_url: dict[str, dict] = {}

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                records = json.load(fp)
                if not isinstance(records, list):
                    continue
                for r in records:
                    email = (r.get("email") or "").strip().lower()
                    u_th = (r.get("university_th") or "").strip()
                    u_en = (r.get("university") or "").strip()
                    name_th = (r.get("full_name_th") or "").strip()
                    name_en = (r.get("full_name_en") or "").strip().lower()
                    if not name_en and r.get("first_name") and r.get("last_name"):
                        name_en = f"{r['first_name']} {r['last_name']}".strip().lower()
                    p_url = (r.get("profile_url") or "").strip()

                    payload = {
                        "email": email,
                        "faculty_th": (r.get("faculty_th") or "").strip(),
                        "department_th": (r.get("department_th") or "").strip(),
                        "academic_title_th": (r.get("academic_title_th") or "").strip(),
                        "full_name_th": name_th,
                        "image_url": (r.get("image_url") or "").strip(),
                    }

                    if p_url and "openalex" not in p_url:
                        lookup_by_url[p_url] = payload
                    if name_th and len(name_th) > 4:
                        if u_th:
                            lookup_by_th[(u_th, name_th)] = payload
                        if u_en:
                            lookup_by_th[(u_en, name_th)] = payload
                    if name_en and len(name_en) > 5:
                        if u_th:
                            lookup_by_en[(u_th, name_en)] = payload
                        if u_en:
                            lookup_by_en[(u_en, name_en)] = payload
        except Exception:
            continue

    print(f"Index built: {len(lookup_by_th):,} Thai keys, {len(lookup_by_en):,} EN keys, {len(lookup_by_url):,} URL keys")

    # Fetch DB records missing email
    rows = db.execute(text(
        "SELECT id, university, university_th, full_name_th, profile_url, email, faculty_th, department_th "
        "FROM faculties "
        "WHERE (email IS NULL OR email = '') OR (faculty_th IS NULL OR faculty_th = '')"
    )).fetchall()

    enriched_count = 0
    updates = []

    for r in rows:
        fac_id, u_en, u_th, db_name, db_url, db_email, db_fac, db_dept = r
        matched_payload = None

        # 1. Match by profile URL
        if db_url and db_url in lookup_by_url:
            matched_payload = lookup_by_url[db_url]

        # 2. Match by Thai Name
        if not matched_payload and db_name:
            if u_th and (u_th, db_name) in lookup_by_th:
                matched_payload = lookup_by_th[(u_th, db_name)]
            elif u_en and (u_en, db_name) in lookup_by_th:
                matched_payload = lookup_by_th[(u_en, db_name)]

        # 3. Match by English Name (if full_name_th in DB contains English)
        if not matched_payload and db_name:
            lower_name = db_name.lower().strip()
            if u_th and (u_th, lower_name) in lookup_by_en:
                matched_payload = lookup_by_en[(u_th, lower_name)]
            elif u_en and (u_en, lower_name) in lookup_by_en:
                matched_payload = lookup_by_en[(u_en, lower_name)]

        if matched_payload:
            new_email = matched_payload.get("email") if not db_email and is_valid_university_email(matched_payload.get("email", ""), u_en or u_th) else db_email
            new_fac = matched_payload.get("faculty_th") if not db_fac else db_fac
            new_dept = matched_payload.get("department_th") if not db_dept else db_dept
            new_name_th = matched_payload.get("full_name_th") if matched_payload.get("full_name_th") and not re.search(r"[฀-๿]", db_name or "") else db_name

            if new_email != db_email or new_fac != db_fac or new_dept != db_dept or new_name_th != db_name:
                updates.append({
                    "id": fac_id,
                    "email": new_email or "",
                    "faculty_th": new_fac or "",
                    "department_th": new_dept or "",
                    "full_name_th": new_name_th or db_name,
                })
                if new_email and new_email != db_email:
                    enriched_count += 1

    if updates:
        for i in range(0, len(updates), BATCH_SIZE):
            chunk = updates[i : i + BATCH_SIZE]
            for item in chunk:
                db.execute(text(
                    "UPDATE faculties SET email = :email, faculty_th = :faculty_th, "
                    "department_th = :department_th, full_name_th = :full_name_th "
                    "WHERE id = :id"
                ), item)
            db.commit()

    print(f"Pass 1 Complete: {len(updates):,} records enriched with metadata ({enriched_count:,} emails)")
    return enriched_count


# ─────────────────────────────────────────────────────────────
# PASS 2: Headless 1-to-1 Profile Crawl
# ─────────────────────────────────────────────────────────────
def crawl_single_profile(row: tuple) -> dict | None:
    fac_id, u_en, u_th, name, profile_url = row
    html = fetch_url(profile_url)
    if not html:
        return None

    emails = RE_EMAIL.findall(html)
    valid_email = None
    for em in emails:
        em_clean = em.lower().strip().rstrip(".")
        if is_valid_university_email(em_clean, u_en):
            valid_email = em_clean
            break

    # Extract Thai name if current DB name is English
    new_thai_name = None
    if not re.search(r"[฀-๿]", name or ""):
        thai_names = RE_THAI_NAME.findall(html)
        if thai_names:
            # Pick first candidate that does not contain generic words
            for tn in thai_names[:5]:
                if not any(w in tn for w in ["มหาวิทยาลัย", "คณะ", "ภาควิชา", "สำนัก", "หน้าหลัก", "ติดต่อ", "รายละเอียด"]):
                    new_thai_name = tn.strip()
                    break

    if valid_email or new_thai_name:
        return {
            "id": fac_id,
            "email": valid_email,
            "full_name_th": new_thai_name,
        }
    return None


def run_pass2_unique_profiles(db) -> int:
    """Crawl unique 1-to-1 faculty profile pages."""
    print("\n--- Pass 2: Unique 1-to-1 Profile URLs Crawl ---")
    rows = db.execute(text(
        "WITH url_counts AS ("
        "    SELECT profile_url, count(*) as cnt FROM faculties "
        "    WHERE (email IS NULL OR email = '') "
        "    AND profile_url != '' AND profile_url NOT LIKE '%openalex%' "
        "    GROUP BY profile_url"
        ") "
        "SELECT f.id, f.university, f.university_th, f.full_name_th, f.profile_url "
        "FROM faculties f "
        "JOIN url_counts u ON f.profile_url = u.profile_url "
        "WHERE u.cnt = 1 "
        "AND (f.email IS NULL OR f.email = '') "
        "ORDER BY f.university, f.id"
    )).fetchall()

    total = len(rows)
    print(f"Targeting {total:,} unique profile URLs...")
    if total == 0:
        return 0

    found_emails = 0
    found_names = 0
    checked = 0
    updates = []

    for batch_start in range(0, total, BATCH_SIZE):
        batch = rows[batch_start : batch_start + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(crawl_single_profile, r) for r in batch]
            for fut in as_completed(futures):
                checked += 1
                res = fut.result()
                if res:
                    updates.append(res)
                    if res.get("email"):
                        found_emails += 1
                    if res.get("full_name_th"):
                        found_names += 1

        if updates:
            for item in updates:
                if item.get("email") and item.get("full_name_th"):
                    db.execute(text(
                        "UPDATE faculties SET email = :email, full_name_th = :full_name_th WHERE id = :id"
                    ), item)
                elif item.get("email"):
                    db.execute(text(
                        "UPDATE faculties SET email = :email WHERE id = :id"
                    ), {"email": item["email"], "id": item["id"]})
                elif item.get("full_name_th"):
                    db.execute(text(
                        "UPDATE faculties SET full_name_th = :full_name_th WHERE id = :id"
                    ), {"full_name_th": item["full_name_th"], "id": item["id"]})
            db.commit()
            updates.clear()

        pct = 100 * checked // max(1, total)
        print(f"    [{pct:3d}%] {checked:,}/{total:,} crawled | {found_emails:,} emails found | {found_names:,} names recovered", end="\r")
        time.sleep(REQUEST_DELAY)

    print()
    print(f"Pass 2 Complete: {found_emails:,} emails, {found_names:,} Thai names recovered from 1-to-1 pages")
    return found_emails


# ─────────────────────────────────────────────────────────────
# PASS 3: Shared Directory Page Matching (Card-Level)
# ─────────────────────────────────────────────────────────────
def run_pass3_shared_directories(db) -> int:
    """Fetch shared directory pages and match emails to faculty within their specific DOM cards."""
    print("\n--- Pass 3: Shared Directory Card-Level Matching ---")
    rows = db.execute(text(
        "WITH url_counts AS ("
        "    SELECT profile_url, count(*) as cnt FROM faculties "
        "    WHERE (email IS NULL OR email = '') "
        "    AND profile_url != '' AND profile_url NOT LIKE '%openalex%' "
        "    GROUP BY profile_url"
        ") "
        "SELECT f.id, f.university, f.university_th, f.full_name_th, f.first_name, f.last_name, f.profile_url "
        "FROM faculties f "
        "JOIN url_counts u ON f.profile_url = u.profile_url "
        "WHERE u.cnt > 1 "
        "AND (f.email IS NULL OR f.email = '') "
        "ORDER BY f.profile_url"
    )).fetchall()

    if not rows:
        print("No shared directory URLs to process.")
        return 0

    # Group by profile_url
    by_url: dict[str, list] = {}
    for r in rows:
        by_url.setdefault(r[6], []).append(r)

    print(f"Targeting {len(rows):,} faculty across {len(by_url):,} shared directory pages...")
    found_emails = 0
    checked_dirs = 0

    for p_url, fac_list in by_url.items():
        checked_dirs += 1
        html = fetch_url(p_url, timeout=15)
        if not html:
            continue

        univ_en = fac_list[0][1]

        # Scan for each faculty member within the page HTML
        for f_item in fac_list:
            fac_id, _, _, full_name_th, first_name, last_name, _ = f_item
            # Search tokens: full Thai name, or first/last names
            search_tokens = []
            if full_name_th and len(full_name_th) > 3:
                search_tokens.append(full_name_th)
                # Split Thai name into words
                parts = full_name_th.split()
                if len(parts) >= 2:
                    search_tokens.append(parts[0])
                    search_tokens.append(parts[1])
            if first_name and len(first_name) > 3:
                search_tokens.append(first_name)
            if last_name and len(last_name) > 3:
                search_tokens.append(last_name)

            best_email = None
            for tok in search_tokens:
                pos = html.find(tok)
                if pos != -1:
                    # Slice card window around name (+- 800 characters)
                    window_start = max(0, pos - 400)
                    window_end = min(len(html), pos + 800)
                    card_chunk = html[window_start:window_end]

                    emails = RE_EMAIL.findall(card_chunk)
                    for em in emails:
                        em_clean = em.lower().strip().rstrip(".")
                        if is_valid_university_email(em_clean, univ_en):
                            best_email = em_clean
                            break
                    if best_email:
                        break

            if best_email:
                db.execute(text(
                    "UPDATE faculties SET email = :email WHERE id = :id"
                ), {"email": best_email, "id": fac_id})
                db.commit()
                found_emails += 1

        pct = 100 * checked_dirs // max(1, len(by_url))
        print(f"    [{pct:3d}%] {checked_dirs:,}/{len(by_url):,} directories parsed | {found_emails:,} emails matched", end="\r")
        time.sleep(REQUEST_DELAY)

    print()
    print(f"Pass 3 Complete: {found_emails:,} emails matched from shared directory pages")
    return found_emails


# ─────────────────────────────────────────────────────────────
# MAIN CONTROL LOOP
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("Wave 60: Autonomous Faculty Enrichment Loop (SKILL.state 5-Pillars)")
    print("=" * 70)

    db = SessionLocal()
    iteration = 1
    total_new_emails = 0

    try:
        # Initial status
        init_total = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()
        init_has_email = db.execute(text("SELECT COUNT(*) FROM faculties WHERE email IS NOT NULL AND email != ''")).scalar()
        print(f"Initial State: {init_has_email:,} / {init_total:,} faculties have email ({100*init_has_email//max(1,init_total)}%)")

        while True:
            print(f"\n{'='*30} ITERATION {iteration} {'='*30}")
            p1_count = run_pass1_checkpoint_enrichment(db)
            p2_count = run_pass2_unique_profiles(db)
            p3_count = run_pass3_shared_directories(db)

            iter_total = p1_count + p2_count + p3_count
            total_new_emails += iter_total

            # Save iteration checkpoint
            ckpt = CHECKPOINT_DIR / "wave60_enrichment_checkpoint.json"
            status = {
                "iteration": iteration,
                "timestamp": time.time(),
                "pass1_checkpoint_emails": p1_count,
                "pass2_unique_profile_emails": p2_count,
                "pass3_shared_dir_emails": p3_count,
                "total_new_emails_this_iter": iter_total,
                "cumulative_new_emails": total_new_emails
            }
            with open(ckpt, "w", encoding="utf-8") as fp:
                json.dump(status, fp, ensure_ascii=False, indent=2)

            print(f"\nIteration {iteration} Yield: {iter_total:,} new emails found.")

            # Convergence condition: If no new emails found or max iterations reached
            if iter_total == 0 or iteration >= 3:
                print("\nPipeline reached convergence (no further records resolvable with current sources).")
                break

            iteration += 1

        # Final Summary
        final_has_email = db.execute(text("SELECT COUNT(*) FROM faculties WHERE email IS NOT NULL AND email != ''")).scalar()
        print("\n" + "=" * 70)
        print("Wave 60 Autonomous Loop Finished")
        print(f"  Initial Emails:     {init_has_email:,}")
        print(f"  Final Emails:       {final_has_email:,} (+{final_has_email - init_has_email:,})")
        print(f"  Total DB Faculties: {init_total:,}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
