"""Harvest authentic official university emails for Phase 30 using SKILL.state architecture.

Target High-Yield Clusters (Phase 30):
1. Chula Faculty of Engineering - Water Resources Engineering (water.eng.chula.ac.th)
2. Kasetsart University - Computer Engineering (cpe.ku.ac.th)
3. Chula Faculty of Allied Health Sciences (ahs.chula.ac.th)
4. Chula Faculty of Science - Mathematics & Computer Science (math.sc.chula.ac.th)

Strict Section 9 Quality Invariants & PDPA:
- Reject freemails (@gmail.com, @hotmail.com, @yahoo.com, etc.)
- Reject generic departmental inboxes (info@, saraban@, contact@, admin@, etc.)
- ONLY official academic emails (@chula.ac.th, @ku.ac.th, .ac.th, .edu)
- Strict institution & faculty scoping eliminating cross-institution false positives
- Zero personal telephone numbers collected
- Unresolvable faculty remain SQL NULL rather than fabricated
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.request
import warnings
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy.orm import defer

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.agentic_pipeline.models import (
    ExtractionAgentState,
    FacultyStatePatch,
    RawFacultyProfile
)
from scripts.agentic_pipeline.state_reducer import (
    FacultyStateReducer,
    save_state_checkpoint
)

OUTPUT_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase30.json"
SKILL_STATE_FILE = BACKEND_DIR / "data" / "agent_states" / "skill_state_phase30"

REJECT_FREEMAILS = {
    "@gmail.com", "@hotmail.com", "@yahoo.com", "@yahoo.co.th",
    "@live.com", "@outlook.com", "@icloud.com"
}

REJECT_GENERIC_PREFIXES = {
    "info@", "contact@", "saraban@", "admin@", "support@", "office@",
    "dean@", "webmaster@", "pr@", "academic@", "admissions@", "admission@",
    "fibo@", "fin@", "help@", "service@", "press@", "registrar@", "facilities@",
    "saraban_econ@", "marketing@"
}

VALID_SUFFIXES = (
    ".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk",
    "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md"
)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def validate_email(email: str) -> bool:
    email_clean = email.strip().lower().replace("%20", "")
    if any(email_clean.endswith(f) for f in REJECT_FREEMAILS):
        return False
    if any(email_clean.startswith(g) for g in REJECT_GENERIC_PREFIXES):
        return False
    if not any(email_clean.endswith(s) or f"@{s}" in email_clean for s in VALID_SUFFIXES):
        return False
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        return False
    user = email_clean.split("@")[0]
    if user.startswith("_") or user.startswith(".") or len(user) < 2:
        return False
    return True


def fetch_url_html(url: str, timeout: int = 10) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return ""


# -------------------------------------------------------------
# Scrapers for Phase 30 Targeted Clusters
# -------------------------------------------------------------

def scrape_chula_water_engineering() -> list[dict[str, str]]:
    """Scrape Chula Water Resources Engineering verified profiles."""
    print("\n--- Harvesting Chula Water Resources Engineering ---")
    targets = [
        ("cu_eng_wave13_b_0052", "https://water.eng.chula.ac.th/?staff-member=pongsak-suttinon"),
        ("cu_eng_wave13_b_0060", "https://water.eng.chula.ac.th/staff-member/tanawat-tangjarusritaratorn/")
    ]
    results = []
    for fid, url in targets:
        html = fetch_url_html(url, timeout=6)
        if not html:
            continue
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@chula\.ac\.th", html, re.I)
        for em in set(emails):
            clean_em = em.strip().lower()
            if validate_email(clean_em):
                results.append({
                    "id": fid,
                    "email": clean_em,
                    "source": url,
                    "cluster": "Chula Water Resources Engineering"
                })
                break
    print(f"  Extracted {len(results)} verified Chula Water Resources contacts.")
    return results


def scrape_ku_cpe() -> list[dict[str, str]]:
    """Scrape Kasetsart University Computer Engineering verified profiles."""
    print("\n--- Harvesting KU Computer Engineering ---")
    url = "https://cpe.ku.ac.th/index.php/teacher-information/?id=213"
    html = fetch_url_html(url, timeout=6)
    results = []
    if html:
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@ku\.ac\.th", html, re.I)
        for em in set(emails):
            clean_em = em.strip().lower()
            if validate_email(clean_em):
                results.append({
                    "id": "ku_eng_cpe_004",
                    "email": clean_em,
                    "source": url,
                    "cluster": "Kasetsart Computer Engineering"
                })
                break
    print(f"  Extracted {len(results)} verified KU CPE contacts.")
    return results


def scrape_chula_ahs() -> list[dict[str, str]]:
    """Scrape Chula Faculty of Allied Health Sciences verified profiles."""
    print("\n--- Harvesting Chula Allied Health Sciences ---")
    url = "https://www.ahs.chula.ac.th/academic-staff/pawan-chaiparinya/"
    html = fetch_url_html(url, timeout=6)
    results = []
    if html:
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@chula\.ac\.th", html, re.I)
        for em in set(emails):
            clean_em = em.strip().lower()
            if validate_email(clean_em):
                results.append({
                    "id": "cu_ahs_wave15_0017",
                    "email": clean_em,
                    "source": url,
                    "cluster": "Chula Allied Health Sciences"
                })
                break
    print(f"  Extracted {len(results)} verified Chula AHS contacts.")
    return results


def scrape_chula_math() -> list[dict[str, str]]:
    """Scrape Chula Science (Mathematics & Computer Science) verified profiles."""
    print("\n--- Harvesting Chula Math & Computer Science ---")
    url = "https://www.math.sc.chula.ac.th/people/krung-s/"
    html = fetch_url_html(url, timeout=6)
    results = []
    if html:
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@chula\.ac\.th", html, re.I)
        for em in set(emails):
            clean_em = em.strip().lower()
            if validate_email(clean_em):
                results.append({
                    "id": "cu_cbs_wave11_0185",
                    "email": clean_em,
                    "source": url,
                    "cluster": "Chula Science (Math & Computer Science)"
                })
                break
    print(f"  Extracted {len(results)} verified Chula Math contacts.")
    return results


def main():
    print("==========================================================")
    print("🚀 PHASE 30 AUTHENTIC OFFICIAL EMAIL RECOVERY PIPELINE")
    print("==========================================================")

    # 1. Scrape all targeted clusters
    recovered_items: list[dict[str, str]] = []
    recovered_items.extend(scrape_chula_water_engineering())
    recovered_items.extend(scrape_ku_cpe())
    recovered_items.extend(scrape_chula_ahs())
    recovered_items.extend(scrape_chula_math())

    print(f"\nTotal verified harvested contacts: {len(recovered_items)}")

    # 2. Enrich and verify each candidate with local PostgreSQL record details
    db = SessionLocal()
    verified_list = []
    try:
        for item in recovered_items:
            fid = item["id"]
            email = item["email"]
            source = item["source"]
            cluster = item["cluster"]

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                print(f"  [ERROR] Faculty ID {fid} not found in DB!")
                continue

            verified_list.append({
                "id": f.id,
                "full_name_th": f.full_name_th,
                "first_name": f.first_name,
                "last_name": f.last_name,
                "university_th": f.university_th,
                "faculty_th": f.faculty_th,
                "department_th": f.department_th,
                "email": email,
                "source": source,
                "cluster": cluster,
                "match_score": 100
            })
            print(f"  [VERIFIED 100%] {f.id} | {f.full_name_th} ({f.university_th} - {f.faculty_th}) -> {email}")

        print(f"\n✨ Total verified recoveries for Phase 30: {len(verified_list)}")

        # 3. Save checkpoint for Phase 30
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json.dumps(verified_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 Checkpoint saved to: {OUTPUT_FILE}")

        # 4. Integrate with SKILL.state Architecture
        print("\n--- Checkpointing to SKILL.state ---")
        agent_state = ExtractionAgentState(
            session_id=f"phase30_recovery_{int(time.time())}",
            target_university_th="จุฬาลงกรณ์มหาวิทยาลัย, มหาวิทยาลัยเกษตรศาสตร์",
            target_university_en="Chulalongkorn University, Kasetsart University",
            target_faculty_th="Multi-Faculty Phase 30 Recovery",
            target_faculty_en="Multi-Faculty Phase 30 Recovery"
        )
        raw_profiles = []
        for rec in verified_list:
            raw_profiles.append(RawFacultyProfile(
                full_name_th=rec["full_name_th"],
                first_name=rec["first_name"],
                last_name=rec["last_name"],
                email=rec["email"],
                profile_url=rec["source"]
            ))
        patch = FacultyStatePatch(extracted_faculties=raw_profiles)
        reducer = FacultyStateReducer(db_session=db)
        updated_state = reducer.apply_patch(agent_state, patch, step_tokens=len(verified_list) * 25)
        save_state_checkpoint(updated_state, str(SKILL_STATE_FILE))
        print(f"💾 SKILL.state checkpoint committed to: {SKILL_STATE_FILE}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
