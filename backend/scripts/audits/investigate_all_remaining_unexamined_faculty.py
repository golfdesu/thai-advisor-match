"""Headless forensic investigation of all remaining unexamined missing faculty using SKILL.state.

Directly investigates all 937 unexamined faculty records (the remaining pool outside
clinical hospital doctors and audited policy omissions).

Evaluates every record:
1. Profile URL probing and email discovery (HTTP fetching with timeout and SSL verification bypass).
2. Strict Section 9 validation (zero freemails, zero generic inboxes, institutional domain verification).
3. Anti-alignment guard: ensures emails scraped from multi-faculty directory pages are NOT
   misaligned to adjacent faculty (requires individual name-to-email token verification).
4. Systematic audit classification for every single faculty member.
5. Checkpointing entire agent state via SKILL.state architecture (ExtractionAgentState, FacultyStatePatch, FacultyStateReducer).
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
import warnings
from collections import Counter
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
    RawFacultyProfile,
)
from scripts.agentic_pipeline.state_reducer import (
    FacultyStateReducer,
    save_state_checkpoint,
)

OUTPUT_REPORT = BACKEND_DIR / "data" / "agent_states" / "comprehensive_investigation_937_faculty.json"
SKILL_STATE_FILE = BACKEND_DIR / "data" / "agent_states" / "skill_state_comprehensive_investigation_937.json"

REJECT_FREEMAILS = {
    "@gmail.com", "@hotmail.com", "@yahoo.com", "@yahoo.co.th",
    "@live.com", "@outlook.com", "@icloud.com"
}

REJECT_GENERIC_PREFIXES = {
    "info@", "contact@", "saraban@", "admin@", "support@", "office@",
    "dean@", "webmaster@", "pr@", "academic@", "admissions@", "admission@",
    "fibo@", "fin@", "help@", "service@", "press@", "registrar@", "facilities@",
    "marketing@", "agriubu@", "la@", "phar@", "phar_it@", "chemistry@", "sci@",
    "sciest@", "ma.sci@", "zoo.sci@", "cheminfo@", "djitt@", "tls@", "ed.swu@",
    "eng@", "ieadmin@"
}

VALID_SUFFIXES = (
    ".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk",
    "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md"
)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def validate_email(email: str) -> tuple[bool, str]:
    email_clean = email.strip().lower().replace("%20", "")
    if any(email_clean.endswith(f) for f in REJECT_FREEMAILS):
        return False, "FREEMAIL_REJECTED_SECTION_9"
    if any(email_clean.startswith(g) for g in REJECT_GENERIC_PREFIXES):
        return False, "GENERIC_INBOX_REJECTED_SECTION_9"
    if not any(email_clean.endswith(s) or f"@{s}" in email_clean for s in VALID_SUFFIXES):
        return False, "INVALID_DOMAIN_NOT_ACADEMIC"
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        return False, "CORRUPT_EMAIL_SYNTAX"
    user = email_clean.split("@")[0]
    if user.startswith("_") or user.startswith(".") or len(user) < 2:
        return False, "INVALID_LOCAL_PART"
    return True, "VALID_AUTHENTIC_ACADEMIC"


def is_known_policy_omission(f: FacultyDB) -> tuple[bool, str]:
    fac = f.faculty_th or ""
    u = f.university_th or ""
    if "แพทยศาสตร์" in fac:
        return True, "CLINICAL_MEDICINE_HOSPITAL_POLICY"
    if "ทันตแพทยศาสตร์" in fac:
        return True, "CLINICAL_DENTISTRY_HOSPITAL_POLICY"
    if "พาณิชยศาสตร์และการบัญชี" in fac and "จุฬา" in u:
        return True, "CHULA_CBS_INACTIVE_EMERITUS"
    if "สถาปัตยกรรม" in fac and "ลาดกระบัง" in u:
        return True, "KMITL_ARCH_FREEMAIL_CLUSTER"
    if "วิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม" in fac and "ศิลปากร" in u:
        return True, "SILPAKORN_ENG_LEGACY_FREEMAILS"
    if "เภสัชศาสตร์" in fac and "จุฬา" in u:
        return True, "CHULA_PHARM_EMPTY_OR_FREEMAIL"
    if "วิศวกรรมศาสตร์" in fac and "เชียงใหม่" in u:
        return True, "CMU_ENG_FREEMAIL_CLUSTER"
    return False, ""


def probe_url_for_emails(url: str) -> tuple[set[str], str]:
    if not url or not url.startswith("http"):
        return set(), "NO_VALID_HTTP_URL"
    parsed = urllib.parse.urlsplit(url)
    encoded_path = urllib.parse.quote(parsed.path)
    encoded_query = urllib.parse.quote(parsed.query, safe="=&?/")
    clean_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, encoded_path, encoded_query, parsed.fragment))

    req = urllib.request.Request(clean_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=4) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application" not in content_type:
                return set(), "NON_HTML_RESPONSE"
            html = resp.read().decode("utf-8", errors="ignore")
            emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html))
            return emails, "SUCCESS"
    except urllib.error.HTTPError as e:
        return set(), f"HTTP_ERROR_{e.code}"
    except Exception as e:
        err_msg = str(e)
        if "timed out" in err_msg.lower():
            return set(), "TIMEOUT"
        if "getaddrinfo" in err_msg.lower():
            return set(), "DNS_LOOKUP_FAILED"
        return set(), "CONNECTION_FAILED"


def check_name_to_email_token_match(f: FacultyDB, email: str) -> bool:
    user_part = email.lower().split("@")[0]
    first = (f.first_name or "").lower().strip()
    last = (f.last_name or "").lower().strip()

    if first and len(first) >= 3 and first in user_part:
        return True
    if last and len(last) >= 3 and last in user_part:
        return True
    if first and last:
        # Check first initial + last name (e.g. jdoe, doe.j)
        if first[0] + last[:4] in user_part or last + "." + first[0] in user_part:
            return True
        if first[:4] + "." + last[:3] in user_part:
            return True
    return False


def main():
    print("======================================================================")
    print("🔍 COMPREHENSIVE FORENSIC INVESTIGATION OF ALL REMAINING UNEXAMINED FACULTY")
    print("   Powered by SKILL.state Architecture & Section 9 Quality Invariants")
    print("======================================================================")

    db = SessionLocal()
    try:
        # 1. Fetch all missing faculty
        all_missing = db.query(FacultyDB).filter(
            (FacultyDB.email.is_(None) | (FacultyDB.email == ""))
        ).options(defer(FacultyDB.embedding)).all()

        print(f"Total missing faculty in database: {len(all_missing)}")

        # 2. Separate into known policy clusters vs unexamined pool
        policy_clusters: list[dict] = []
        unexamined: list[FacultyDB] = []

        for f in all_missing:
            is_pol, pol_reason = is_known_policy_omission(f)
            if is_pol:
                policy_clusters.append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th,
                    "reason": pol_reason
                })
            else:
                unexamined.append(f)

        print(f"Known policy/clinical omission clusters: {len(policy_clusters)}")
        print(f"Target unexamined faculty pool: {len(unexamined)} records")

        # 3. Cache probed domains to avoid repeated timeouts on dead hosts
        dead_domains: set[str] = set()
        domain_probe_cache: dict[str, tuple[set[str], str]] = {}

        investigated_results = []
        recovered_emails = []
        status_counter = Counter()

        print("\n--- Initiating Systematic Investigation Across Unexamined Pool ---")
        start_time = time.time()

        for idx, f in enumerate(unexamined, 1):
            fid = f.id
            name = f.full_name_th or f"{f.first_name} {f.last_name}"
            uni = f.university_th or ""
            fac = f.faculty_th or ""
            url = f.profile_url or ""

            # Check if International Visiting / Emeritus
            if "ดุริยางคศิลป์" in fac and "มหิดล" in uni:
                audit_verdict = "VISITING_INTERNATIONAL_ARTIST"
                final_email = None
            elif "ศศินทร์" in fac and "จุฬา" in uni:
                audit_verdict = "VISITING_ADJUNCT_PROFESSOR"
                final_email = None
            elif not url or not url.startswith("http"):
                audit_verdict = "NO_PROFILE_URL_PUBLISHED"
                final_email = None
            else:
                domain = urllib.parse.urlsplit(url).netloc
                if domain in dead_domains:
                    audit_verdict = "DEAD_DOMAIN_UNREACHABLE"
                    final_email = None
                else:
                    if url in domain_probe_cache:
                        emails, fetch_status = domain_probe_cache[url]
                    else:
                        emails, fetch_status = probe_url_for_emails(url)
                        domain_probe_cache[url] = (emails, fetch_status)
                        if fetch_status in {"DNS_LOOKUP_FAILED", "CONNECTION_FAILED"}:
                            dead_domains.add(domain)

                    if fetch_status != "SUCCESS":
                        audit_verdict = f"PROFILE_PROBE_{fetch_status}"
                        final_email = None
                    elif not emails:
                        audit_verdict = "EMPTY_PROFILE_NO_EMAIL"
                        final_email = None
                    else:
                        valid_candidates = []
                        rejection_reasons = []
                        for em in emails:
                            is_val, reason = validate_email(em)
                            if is_val:
                                valid_candidates.append(em)
                            else:
                                rejection_reasons.append(reason)

                        if valid_candidates:
                            # Verify name-to-email token match to prevent false positive adjacent email alignment
                            matched_email = None
                            for cand in valid_candidates:
                                if check_name_to_email_token_match(f, cand):
                                    matched_email = cand
                                    break

                            if matched_email:
                                audit_verdict = "AUTHENTIC_ACADEMIC_EMAIL_FOUND"
                                final_email = matched_email
                            else:
                                audit_verdict = "DIRECTORY_PAGE_MULTI_FACULTY_NO_INDIVIDUAL_MATCH"
                                final_email = None
                        else:
                            if any("FREEMAIL" in r for r in rejection_reasons):
                                audit_verdict = "FREEMAIL_EXCLUSION_SECTION_9"
                            elif any("GENERIC" in r for r in rejection_reasons):
                                audit_verdict = "GENERIC_INBOX_EXCLUSION_SECTION_9"
                            else:
                                audit_verdict = "UNVERIFIED_EMAIL_REJECTED"
                            final_email = None

            status_counter[audit_verdict] += 1
            rec_entry = {
                "id": fid,
                "full_name_th": name,
                "first_name": f.first_name,
                "last_name": f.last_name,
                "university_th": uni,
                "faculty_th": fac,
                "department_th": f.department_th,
                "profile_url": url,
                "verdict": audit_verdict,
                "recovered_email": final_email
            }
            investigated_results.append(rec_entry)

            if final_email:
                recovered_emails.append(rec_entry)

            if idx % 100 == 0 or idx == len(unexamined):
                print(f"  Processed {idx:4d} / {len(unexamined)} faculty... (Elapsed: {time.time()-start_time:.1f}s)")

        print("\n======================================================================")
        print("📊 FINAL AUDITED VERDICT BREAKDOWN OF 937 UNEXAMINED FACULTY")
        print("======================================================================")
        for verdict, count in status_counter.most_common():
            print(f"  {count:4d} : {verdict}")

        print(f"\n✨ Total Authentically Recovered Emails: {len(recovered_emails)}")
        for r in recovered_emails:
            print(f"  - {r['id']} | {r['full_name_th']} ({r['university_th']}) -> {r['recovered_email']}")

        # 4. Checkpoint to SKILL.state Architecture
        print("\n--- Checkpointing to SKILL.state Architecture ---")
        agent_state = ExtractionAgentState(
            session_id=f"unexamined_937_investigation_{int(time.time())}",
            target_university_th="All Universities (937 Remaining Pool)",
            target_university_en="All Universities (937 Remaining Pool)",
            target_faculty_th="Exhaustive Forensic Investigation",
            target_faculty_en="Exhaustive Forensic Investigation"
        )
        raw_profiles = []
        for rec in investigated_results:
            raw_profiles.append(RawFacultyProfile(
                full_name_th=rec["full_name_th"],
                first_name=rec.get("first_name"),
                last_name=rec.get("last_name"),
                email=rec["recovered_email"],
                profile_url=rec["profile_url"]
            ))

        patch = FacultyStatePatch(extracted_faculties=raw_profiles)
        reducer = FacultyStateReducer(db_session=db)
        updated_state = reducer.apply_patch(agent_state, patch, step_tokens=len(unexamined) * 20)
        save_state_checkpoint(updated_state, str(SKILL_STATE_FILE))
        print(f"💾 Committed SKILL.state checkpoint to: {SKILL_STATE_FILE}")

        # Save structured report
        report_data = {
            "total_unexamined_investigated": len(unexamined),
            "verdict_breakdown": dict(status_counter),
            "recovered_emails_count": len(recovered_emails),
            "recovered_emails": recovered_emails,
            "investigated_records": investigated_results
        }
        OUTPUT_REPORT.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 Comprehensive audit report saved to: {OUTPUT_REPORT}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
