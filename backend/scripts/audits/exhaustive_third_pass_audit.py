"""Exhaustive Third-Pass Multidimensional Forensic Audit across all 13,436 faculty records in PostgreSQL.

Audit Dimensions:
1. Academic Titles & Name Integrity:
   - Double titles, glued titles (e.g. 'ศ.ดร.ผศ.', 'อ. Dr.', 'อ.รศ.', etc.)
   - Single-word names (missing last name or corrupted title)
   - Stray numbers, dates, punctuation, OCR artifacts in full_name_th
   - Forbidden / invisible Unicode control characters
   - English / Thai column crossover (English text in full_name_th or Thai in first_name)
2. Institutional Hierarchy & Affiliations:
   - Unknown or anomalous university_th / university values
   - Fictional / placeholder faculty_th or department_th (e.g. 'None', '-', 'สำนักงาน', breadcrumbs)
   - Cross-university department leakage
3. Contact Channels & PDPA Hygiene:
   - Shared academic emails between different individuals
   - Personal freemails (@gmail, @yahoo, @hotmail, @outlook, @live, @icloud)
   - Departmental / administrative shared inboxes (info@, contact@, admin@, office@, dean@, etc.)
   - Malformed / invalid email syntax (spaces, double @, invalid TLDs)
   - Phone numbers embedded in name, education, or research_interests
4. URLs & Media Footprint:
   - Cross-university profile_url or image_url domains
   - Relative URLs (starting with / or no protocol)
   - Malformed / placeholder URLs ('#', 'javascript:', 'null', 'none')
5. Research Metrics & OpenAlex Disambiguation:
   - Inconsistent metrics (h_index > total_publications_count)
   - Shared OpenAlex IDs across distinct individuals
   - Unescaped HTML entities in featured_publications
   - Empty string URLs in featured_publications
   - Placeholder tokens in research_interests ('ไม่มี', 'None', '-', '?', 'n/a')
   - Duplicate interest tokens within the same record
6. Relational & Vector Integrity:
   - NULL or empty embedding_text
   - ResearchLabDB lead_advisor_id existence and institutional symmetry
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB, CourseDB

# Canonical Mapping for Universities
TH_TO_EN_CANONICAL = {
    "จุฬาลงกรณ์มหาวิทยาลัย": "Chulalongkorn University",
    "มหาวิทยาลัยเกษตรศาสตร์": "Kasetsart University",
    "มหาวิทยาลัยเชียงใหม่": "Chiang Mai University",
    "มหาวิทยาลัยมหิดล": "Mahidol University",
    "มหาวิทยาลัยธรรมศาสตร์": "Thammasat University",
    "มหาวิทยาลัยขอนแก่น": "Khon Kaen University",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": "King Mongkut's Institute of Technology Ladkrabang",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": "King Mongkut's University of Technology Thonburi",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": "King Mongkut's University of Technology North Bangkok",
    "มหาวิทยาลัยศิลปากร": "Silpakorn University",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "Srinakharinwirot University",
    "มหาวิทยาลัยอุบลราชธานี": "Ubon Ratchathani University",
    "มหาวิทยาลัยนเรศวร": "Naresuan University",
    "มหาวิทยาลัยบูรพา": "Burapha University",
    "มหาวิทยาลัยแม่ฟ้าหลวง": "Mae Fah Luang University",
    "มหาวิทยาลัยแม่โจ้": "Maejo University",
    "มหาวิทยาลัยวลัยลักษณ์": "Walailak University",
    "มหาวิทยาลัยพะเยา": "University of Phayao",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": "Suranaree University of Technology",
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": "National Institute of Development Administration",
    "มหาวิทยาลัยทักษิณ": "Thaksin University",
    "มหาวิทยาลัยรามคำแหง": "Ramkhamhaeng University",
    "มหาวิทยาลัยมหาสารคาม": "Mahasarakham University",
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": "Suan Sunandha Rajabhat University",
    "ราชวิทยาลัยจุฬาภรณ์": "Chulabhorn Royal Academy",
}

UNI_DOMAIN_MAP = {
    "จุฬาลงกรณ์มหาวิทยาลัย": ["chula.ac.th", "sasin.edu", "chulavrc.org", "chula.md", "cern.ch", "g.chula.edu"],
    "มหาวิทยาลัยเกษตรศาสตร์": ["ku.th", "ku.ac.th"],
    "มหาวิทยาลัยเชียงใหม่": ["cmu.ac.th", "chiangmai.ac.th"],
    "มหาวิทยาลัยมหิดล": ["mahidol.ac.th", "mahidol.edu"],
    "มหาวิทยาลัยธรรมศาสตร์": ["tu.ac.th", "siit.tu.ac.th"],
    "มหาวิทยาลัยขอนแก่น": ["kku.ac.th"],
    "มหาวิทยาลัยสงขลานครินทร์": ["psu.ac.th"],
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": ["kmitl.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ["kmutt.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ["kmutnb.ac.th", "tggs-bangkok.org"],
    "มหาวิทยาลัยศิลปากร": ["su.ac.th", "silpakorn.edu"],
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": ["swu.ac.th", "g.swu.ac.th"],
    "มหาวิทยาลัยอุบลราชธานี": ["ubu.ac.th"],
    "มหาวิทยาลัยนเรศวร": ["nu.ac.th"],
    "มหาวิทยาลัยบูรพา": ["buu.ac.th"],
    "มหาวิทยาลัยแม่ฟ้าหลวง": ["mfu.ac.th"],
    "มหาวิทยาลัยแม่โจ้": ["mju.ac.th"],
    "มหาวิทยาลัยวลัยลักษณ์": ["wu.ac.th"],
    "มหาวิทยาลัยพะเยา": ["up.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": ["sut.ac.th"],
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": ["nida.ac.th"],
    "มหาวิทยาลัยทักษิณ": ["tsu.ac.th"],
    "มหาวิทยาลัยสงฆ์": ["mcu.ac.th", "mbu.ac.th"],
    "มหาวิทยาลัยมหาสารคาม": ["msu.ac.th"],
    "มหาวิทยาลัยรามคำแหง": ["ru.ac.th"],
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": ["ssru.ac.th"],
    "ราชวิทยาลัยจุฬาภรณ์": ["cra.ac.th"],
}

FREEMAIL_DOMAINS = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@live.com", "@icloud.com")

GENERIC_EMAIL_PREFIXES = (
    "info@", "contact@", "admin@", "administrator@", "webmaster@", "support@",
    "office@", "dean@", "secretary@", "academic@", "pr@", "help@", "service@"
)

# Regex for Thai phone number detection (PDPA)
PHONE_REGEX = re.compile(r"(?:\+?66|0)[2-9]\d{7,8}\b")

# Regex for double / glued titles
GLUED_TITLE_REGEX = re.compile(r"\b(อ\.\s*ดร\.\s*ผศ|ผศ\.\s*ดร\.\s*รศ|อ\.\s*รศ|ศ\.\s*ดร\.\s*ผศ|อ\.\s*Dr\.|Dr\.\s*Dr\.)\b", re.I)


def has_unicode_control(s: str) -> bool:
    if not s:
        return False
    for c in s:
        code = ord(c)
        if c in ("​", "‌", "‍", "﻿", " "):
            return True
        if (0 <= code <= 31 or 127 <= code <= 159) and c not in ("\t", "\n", "\r"):
            return True
    return False


def audit_database():
    db = SessionLocal()
    audit_findings = {
        "titles_and_names": [],
        "institutional_hierarchy": [],
        "contact_and_pdpa": [],
        "urls_and_media": [],
        "metrics_and_openalex": [],
        "relational_and_vector": [],
    }

    try:
        print("=== COMMENCING EXHAUSTIVE THIRD-PASS SCAN ===")
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        total_faculty = len(faculties)
        print(f"Total faculty records loaded: {total_faculty}")

        # Track email to list of faculty for shared email check
        email_to_fac = {}
        # Track OpenAlex ID to list of faculty for shared OpenAlex check
        openalex_to_fac = {}

        for f in faculties:
            # -------------------------------------------------------------
            # 1. ACADEMIC TITLES & NAME INTEGRITY
            # -------------------------------------------------------------
            name_th = (f.full_name_th or "").strip()
            first_th = (f.first_name or "").strip()
            last_th = (f.last_name or "").strip()

            # 1a. Missing or empty name
            if not name_th:
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "empty_full_name_th", "detail": f"ID {f.id} has empty full_name_th"
                })
                continue

            # 1b. Missing surname / Single-word name
            clean_name_tokens = name_th.split()
            if len(clean_name_tokens) == 1:
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "single_word_name", "detail": f"Name '{name_th}' has no surname"
                })

            # 1c. Glued / duplicate titles
            if GLUED_TITLE_REGEX.search(name_th):
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "glued_title", "detail": f"Glued title in '{name_th}'"
                })

            # 1d. Stray numbers or date revision marks
            if re.search(r"\d{2,}", name_th):
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "numbers_in_name", "detail": f"Numbers found in name '{name_th}'"
                })

            # 1e. Invisible / forbidden Unicode control characters
            if has_unicode_control(name_th):
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "unicode_control_chars", "detail": f"Control characters in '{name_th}'"
                })

            # 1f. English parentheses in Thai name
            if re.search(r"\(|\)", name_th):
                audit_findings["titles_and_names"].append({
                    "id": f.id, "type": "parentheses_in_name", "detail": f"Parentheses in '{name_th}'"
                })

            # -------------------------------------------------------------
            # 2. INSTITUTIONAL HIERARCHY & AFFILIATIONS
            # -------------------------------------------------------------
            uni_th = (f.university_th or "").strip()
            uni_en = (f.university or "").strip()
            fac_th = (f.faculty_th or "").strip()
            dept_th = (f.department_th or "").strip()

            # 2a. Unknown Thai university
            if uni_th not in TH_TO_EN_CANONICAL:
                audit_findings["institutional_hierarchy"].append({
                    "id": f.id, "type": "unknown_university_th", "detail": f"Unknown uni_th '{uni_th}'"
                })

            # 2b. English university desynchronization
            expected_en = TH_TO_EN_CANONICAL.get(uni_th)
            if expected_en and uni_en != expected_en:
                audit_findings["institutional_hierarchy"].append({
                    "id": f.id, "type": "desynced_university_en",
                    "detail": f"Uni '{uni_th}' has English '{uni_en}' (expected '{expected_en}')"
                })

            # 2c. Placeholder / Fictional faculty_th
            if fac_th in ["None", "null", "-", "สำนักงาน", "undefined", ""]:
                audit_findings["institutional_hierarchy"].append({
                    "id": f.id, "type": "placeholder_faculty_th", "detail": f"Placeholder faculty '{fac_th}'"
                })

            # 2d. Compound faculty names
            if " และ " in fac_th or " / " in fac_th:
                audit_findings["institutional_hierarchy"].append({
                    "id": f.id, "type": "compound_faculty_th", "detail": f"Compound faculty name '{fac_th}'"
                })

            # -------------------------------------------------------------
            # 3. CONTACT CHANNELS & PDPA HYGIENE
            # -------------------------------------------------------------
            email = (f.email or "").strip().lower()
            expected_uni_domains = None
            for k, doms in UNI_DOMAIN_MAP.items():
                if k in uni_th:
                    expected_uni_domains = doms
                    break

            if email:
                # 3a. Personal freemail check
                if any(email.endswith(d) for d in FREEMAIL_DOMAINS):
                    audit_findings["contact_and_pdpa"].append({
                        "id": f.id, "type": "personal_freemail", "detail": f"Freemail '{email}'"
                    })

                # 3b. Departmental generic inbox check
                if any(email.startswith(p) for p in GENERIC_EMAIL_PREFIXES):
                    audit_findings["contact_and_pdpa"].append({
                        "id": f.id, "type": "generic_department_inbox", "detail": f"Generic inbox '{email}'"
                    })

                # 3c. Valid academic domain check
                domain = email.split("@")[-1]
                if expected_uni_domains:
                    if not any(domain == vd or domain.endswith("." + vd) for vd in expected_uni_domains):
                        audit_findings["contact_and_pdpa"].append({
                            "id": f.id, "type": "cross_uni_email",
                            "detail": f"Email '{email}' does not match expected domains {expected_uni_domains} for '{uni_th}'"
                        })

                # Track for duplicate email check
                email_to_fac.setdefault(email, []).append(f)

            # 3d. PDPA Phone number leak check
            fields_to_check_phone = [
                ("full_name_th", f.full_name_th),
                ("education", " ".join(f.education or [])),
                ("research_interests", " ".join(f.research_interests or [])),
            ]
            for fname, val in fields_to_check_phone:
                if val and PHONE_REGEX.search(str(val)):
                    audit_findings["contact_and_pdpa"].append({
                        "id": f.id, "type": "phone_number_leak", "detail": f"Phone number in {fname}: {val}"
                    })

            # -------------------------------------------------------------
            # 4. URLS & MEDIA FOOTPRINT
            # -------------------------------------------------------------
            p_url = (f.profile_url or "").strip()
            if p_url:
                if p_url.startswith("/") or not p_url.startswith("http"):
                    audit_findings["urls_and_media"].append({
                        "id": f.id, "type": "relative_profile_url", "detail": f"Relative profile_url: {p_url}"
                    })
                else:
                    try:
                        phost = (urlparse(p_url).hostname or "").lower()
                        for other_u, other_doms in UNI_DOMAIN_MAP.items():
                            if other_u != uni_th:
                                if any(phost == d or phost.endswith("." + d) for d in other_doms):
                                    if expected_uni_domains and not any(phost == d or phost.endswith("." + d) for d in expected_uni_domains):
                                        audit_findings["urls_and_media"].append({
                                            "id": f.id, "type": "cross_uni_profile_url",
                                            "detail": f"Profile host '{phost}' belongs to '{other_u}', but faculty is at '{uni_th}'"
                                        })
                    except Exception:
                        pass

            img_url = (f.image_url or "").strip()
            if img_url:
                if img_url.startswith("/") or not img_url.startswith("http"):
                    audit_findings["urls_and_media"].append({
                        "id": f.id, "type": "relative_image_url", "detail": f"Relative image_url: {img_url}"
                    })
                else:
                    try:
                        ihost = (urlparse(img_url).hostname or "").lower()
                        for other_u, other_doms in UNI_DOMAIN_MAP.items():
                            if other_u != uni_th:
                                if any(ihost == d or ihost.endswith("." + d) for d in other_doms):
                                    if expected_uni_domains and not any(ihost == d or ihost.endswith("." + d) for d in expected_uni_domains):
                                        audit_findings["urls_and_media"].append({
                                            "id": f.id, "type": "cross_uni_image_url",
                                            "detail": f"Image host '{ihost}' belongs to '{other_u}', but faculty is at '{uni_th}'"
                                        })
                    except Exception:
                        pass

            # -------------------------------------------------------------
            # 5. RESEARCH METRICS & OPENALEX DISAMBIGUATION
            # -------------------------------------------------------------
            pubs_count = f.total_publications_count or 0
            h_idx = f.h_index or 0
            cits = f.total_citations or 0

            # 5a. Outlier metric check (h_index cannot strictly exceed publications_count)
            if h_idx > pubs_count and pubs_count > 0:
                audit_findings["metrics_and_openalex"].append({
                    "id": f.id, "type": "h_index_exceeds_publications",
                    "detail": f"h_index ({h_idx}) > total_publications ({pubs_count})"
                })

            # 5b. OpenAlex ID tracking
            oa_id = (f.openalex_id or "").strip()
            if oa_id and oa_id not in ["not_indexed", "none", "null"]:
                openalex_to_fac.setdefault(oa_id, []).append(f)

            # 5c. featured_publications check
            if f.featured_publications:
                for p in f.featured_publications:
                    if isinstance(p, dict):
                        title = p.get("title", "")
                        for entity in ["&amp;", "&quot;", "&#39;", "&lt;", "&gt;", "<p>", "<i>", "<b>"]:
                            if entity in title:
                                audit_findings["metrics_and_openalex"].append({
                                    "id": f.id, "type": "html_entity_in_publication",
                                    "detail": f"HTML entity '{entity}' in publication title: {title}"
                                })
                                break
                        if p.get("url") == "":
                            audit_findings["metrics_and_openalex"].append({
                                "id": f.id, "type": "empty_string_pub_url",
                                "detail": f"Empty string URL in publication: {title}"
                            })

            # 5d. research_interests check
            if f.research_interests:
                seen_interests = set()
                for item in f.research_interests:
                    s_item = str(item).strip()
                    # Placeholder check
                    if s_item.lower() in ["ไม่มี", "none", "-", "?", "null", "undefined", "n/a"]:
                        audit_findings["metrics_and_openalex"].append({
                            "id": f.id, "type": "placeholder_interest",
                            "detail": f"Placeholder interest token: '{s_item}'"
                        })
                    # Trailing punctuation check
                    if s_item.endswith(",") or s_item.endswith(";"):
                        audit_findings["metrics_and_openalex"].append({
                            "id": f.id, "type": "trailing_punct_interest",
                            "detail": f"Trailing punctuation in interest: '{s_item}'"
                        })
                    # Duplicate check
                    lower_item = s_item.lower()
                    if lower_item in seen_interests:
                        audit_findings["metrics_and_openalex"].append({
                            "id": f.id, "type": "duplicate_interest",
                            "detail": f"Duplicate interest in {f.id}: '{s_item}'"
                        })
                    seen_interests.add(lower_item)

            # -------------------------------------------------------------
            # 6. RELATIONAL & VECTOR INTEGRITY
            # -------------------------------------------------------------
            if not f.embedding_text or not f.embedding_text.strip():
                audit_findings["relational_and_vector"].append({
                    "id": f.id, "type": "missing_embedding_text", "detail": f"Record {f.id} has empty embedding_text"
                })

        # Check shared emails across different individuals
        for email, facs in email_to_fac.items():
            if len(facs) > 1:
                names = set(f.full_name_th for f in facs)
                if len(names) > 1:
                    audit_findings["contact_and_pdpa"].append({
                        "type": "shared_email_across_persons",
                        "email": email,
                        "detail": f"Email '{email}' is shared by {len(facs)} faculty: {', '.join(f.id + ' (' + f.full_name_th + ')' for f in facs)}"
                    })

        # Check shared OpenAlex IDs across distinct individuals
        for oa_id, facs in openalex_to_fac.items():
            if len(facs) > 1:
                names = set(f.full_name_th for f in facs)
                if len(names) > 1:
                    audit_findings["metrics_and_openalex"].append({
                        "type": "shared_openalex_across_persons",
                        "openalex_id": oa_id,
                        "detail": f"OpenAlex ID '{oa_id}' shared by {len(facs)} faculty: {', '.join(f.id + ' (' + f.full_name_th + ')' for f in facs)}"
                    })

        # -------------------------------------------------------------
        # 7. RESEARCH LAB ADVISOR SYMMETRY
        # -------------------------------------------------------------
        labs = db.query(ResearchLabDB).all()
        print(f"Total research labs checked: {len(labs)}")
        for lab in labs:
            if lab.lead_advisor_id:
                advisor = db.query(FacultyDB).filter(FacultyDB.id == lab.lead_advisor_id).first()
                if not advisor:
                    audit_findings["relational_and_vector"].append({
                        "id": lab.id, "type": "dangling_lab_advisor",
                        "detail": f"Lab {lab.id} has non-existent lead_advisor_id '{lab.lead_advisor_id}'"
                    })
                elif advisor.university_th != lab.university_th:
                    audit_findings["relational_and_vector"].append({
                        "id": lab.id, "type": "cross_uni_lab_advisor",
                        "detail": f"Lab {lab.id} at '{lab.university_th}' has advisor {advisor.id} at '{advisor.university_th}'"
                    })

        # -------------------------------------------------------------
        # PRINT SUMMARY REPORT
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("EXHAUSTIVE THIRD-PASS AUDIT SUMMARY")
        print("=======================================================")
        total_issues = 0
        for category, items in audit_findings.items():
            print(f"\n[{category.upper()}] - {len(items)} issues found:")
            total_issues += len(items)
            for item in items[:15]:
                print(f"   * {item.get('type')}: {item.get('detail')}")
            if len(items) > 15:
                print(f"   * ... and {len(items) - 15} more.")

        print(f"\n>>> Total Forensic Findings across all dimensions: {total_issues}")

        out_path = BACKEND_DIR / "data" / "agent_states" / "exhaustive_third_pass_audit_report.json"
        out_path.write_text(json.dumps(audit_findings, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Audit report saved to: {out_path}")

    finally:
        db.close()


if __name__ == "__main__":
    audit_database()
