"""Exhaustive Fourth-Pass Deep Forensic & Database Invariant Scanner
Auditing all 13,409 faculties, 104 research labs, and 4,184 courses in local PostgreSQL.
"""
import re
import sys
import json
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB, CourseDB

def run_deep_scan():
    db = SessionLocal()
    try:
        print("=" * 70)
        print("COMMENCING UNLIMITED-TOKEN FOURTH-PASS DATABASE FORENSIC SCAN")
        print("=" * 70)

        faculties = db.query(FacultyDB).all()
        labs = db.query(ResearchLabDB).all()
        courses = db.query(CourseDB).all()

        print(f"Total faculty records: {len(faculties)}")
        print(f"Total research labs:   {len(labs)}")
        print(f"Total courses:         {len(courses)}")

        report = {
            "counts": {
                "faculties": len(faculties),
                "labs": len(labs),
                "courses": len(courses)
            },
            "findings": {
                "faculties_names_and_titles": [],
                "faculties_emails_and_pdpa": [],
                "faculties_urls_and_media": [],
                "faculties_metrics_and_openalex": [],
                "faculties_relational_and_embeddings": [],
                "research_labs_integrity": [],
                "courses_integrity": []
            }
        }

        # -------------------------------------------------------------
        # DIMENSION 1: Faculty Names and Titles
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 1] Auditing Faculty Names, Academic Titles, and Characters ---")
        for f in faculties:
            # 1.1 Parentheses in full_name_th
            if f.full_name_th and ("(" in f.full_name_th or ")" in f.full_name_th):
                report["findings"]["faculties_names_and_titles"].append({
                    "id": f.id,
                    "issue": "Parentheses in full_name_th",
                    "value": f.full_name_th
                })

            # 1.2 Glued titles
            if f.full_name_th:
                # Double prefix like 'ดร. อ. ดร.'
                if re.search(r"ดร\.\s*อ\.\s*ดร\.", f.full_name_th):
                    report["findings"]["faculties_names_and_titles"].append({
                        "id": f.id,
                        "issue": "Glued title 'ดร. อ. ดร.'",
                        "value": f.full_name_th
                    })
                # English prefix glued to Thai title like 'รศ.ดร. Dr.', 'ศ.ดร. Prof.'
                if re.search(r"(?:รศ|ผศ|ศ)\.ดร\.\s*(?:Dr\.|Prof\.|Assoc\.|Asst\.)", f.full_name_th):
                    report["findings"]["faculties_names_and_titles"].append({
                        "id": f.id,
                        "issue": "Glued English prefix to Thai title",
                        "value": f.full_name_th
                    })
                # Untrimmed whitespace or double spaces
                if "  " in f.full_name_th or f.full_name_th != f.full_name_th.strip():
                    report["findings"]["faculties_names_and_titles"].append({
                        "id": f.id,
                        "issue": "Whitespace formatting anomaly",
                        "value": repr(f.full_name_th)
                    })

            # 1.3 Null essential fields
            if not f.full_name_th or not f.university_th or not f.faculty_th:
                report["findings"]["faculties_names_and_titles"].append({
                    "id": f.id,
                    "issue": "Missing essential hierarchy field",
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th
                })

        print(f"-> Name & Title issues found: {len(report['findings']['faculties_names_and_titles'])}")

        # -------------------------------------------------------------
        # DIMENSION 2: Emails and PDPA Compliance
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 2] Auditing Emails, PDPA Invariants, and Shared Inboxes ---")
        email_map = defaultdict(list)
        for f in faculties:
            if f.email:
                cleaned = f.email.strip().lower()
                email_map[cleaned].append(f)

                # 2.1 Email regex syntax
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", cleaned):
                    report["findings"]["faculties_emails_and_pdpa"].append({
                        "id": f.id,
                        "issue": "Invalid email syntax",
                        "email": f.email
                    })

                # 2.2 Departmental generic inboxes
                if any(cleaned.startswith(p) for p in ["info@", "admin@", "contact@", "office@", "surgery.med@", "nongyao.jam@"]):
                    report["findings"]["faculties_emails_and_pdpa"].append({
                        "id": f.id,
                        "issue": "Generic departmental/staff email",
                        "email": f.email
                    })

            # 2.3 PDPA Personal phone number leakage in interests, education, or bio
            for field in [f.research_interests, f.education]:
                text_content = " ".join(str(x) for x in (field or []))
                # Check for 10-digit mobile phone starting with 08, 09, 06
                if re.search(r"\b0[689]\d{8}\b", text_content):
                    report["findings"]["faculties_emails_and_pdpa"].append({
                        "id": f.id,
                        "issue": "PDPA violation: Phone number detected in profile field",
                        "match": re.findall(r"\b0[689]\d{8}\b", text_content)
                    })

        # 2.4 Duplicate emails across distinct individuals
        shared_email_groups = 0
        for email, fac_list in email_map.items():
            if len(fac_list) > 1:
                # Check if names are distinct
                distinct_names = set(x.full_name_th for x in fac_list)
                if len(distinct_names) > 1:
                    shared_email_groups += 1
                    report["findings"]["faculties_emails_and_pdpa"].append({
                        "issue": "Shared email across distinct people",
                        "email": email,
                        "members": [{"id": x.id, "name": x.full_name_th, "uni": x.university_th} for x in fac_list]
                    })
        print(f"-> Email & PDPA issues found: {len(report['findings']['faculties_emails_and_pdpa'])} (Shared email groups: {shared_email_groups})")

        # -------------------------------------------------------------
        # DIMENSION 3: URLs and Media Footprint
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 3] Auditing Profile URLs, Image URLs, and Domains ---")
        for f in faculties:
            # 3.1 Invalid URL syntax
            for url_field in ["profile_url", "image_url"]:
                val = getattr(f, url_field)
                if val:
                    val_str = str(val).strip()
                    if not val_str.startswith("http://") and not val_str.startswith("https://"):
                        report["findings"]["faculties_urls_and_media"].append({
                            "id": f.id,
                            "issue": f"Invalid {url_field} protocol",
                            "value": val_str
                        })
                    if " " in val_str:
                        report["findings"]["faculties_urls_and_media"].append({
                            "id": f.id,
                            "issue": f"Space in {url_field}",
                            "value": val_str
                        })

        print(f"-> URL & Media issues found: {len(report['findings']['faculties_urls_and_media'])}")

        # -------------------------------------------------------------
        # DIMENSION 4: Research Metrics and OpenAlex
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 4] Auditing OpenAlex IDs, Citations, and Author Metrics ---")
        openalex_map = defaultdict(list)
        for f in faculties:
            if f.openalex_id and f.openalex_id not in ["not_indexed", "none", "null"]:
                openalex_map[f.openalex_id.strip()].append(f)

            # Negative metrics
            if (f.total_citations is not None and f.total_citations < 0) or \
               (f.h_index is not None and f.h_index < 0) or \
               (f.total_publications_count is not None and f.total_publications_count < 0):
                report["findings"]["faculties_metrics_and_openalex"].append({
                    "id": f.id,
                    "issue": "Negative metric value",
                    "cites": f.total_citations,
                    "h_index": f.h_index,
                    "pubs": f.total_publications_count
                })

        # Duplicate OpenAlex ID across distinct people
        shared_openalex = 0
        for oid, fac_list in openalex_map.items():
            if len(fac_list) > 1:
                distinct_names = set(x.full_name_th for x in fac_list)
                if len(distinct_names) > 1:
                    shared_openalex += 1
                    report["findings"]["faculties_metrics_and_openalex"].append({
                        "issue": "Duplicate OpenAlex ID across distinct people",
                        "openalex_id": oid,
                        "members": [{"id": x.id, "name": x.full_name_th} for x in fac_list]
                    })

        print(f"-> Metrics & OpenAlex issues found: {len(report['findings']['faculties_metrics_and_openalex'])} (Shared OpenAlex groups: {shared_openalex})")

        # -------------------------------------------------------------
        # DIMENSION 5: Relational Integrity & Vector Embeddings
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 5] Auditing Faculty Embedding Vectors & Text Representation ---")
        for f in faculties:
            if f.embedding is None:
                report["findings"]["faculties_relational_and_embeddings"].append({
                    "id": f.id,
                    "issue": "NULL vector embedding"
                })
            elif len(f.embedding) != 768:
                report["findings"]["faculties_relational_and_embeddings"].append({
                    "id": f.id,
                    "issue": f"Invalid vector dimension: {len(f.embedding)} (expected 768)"
                })
            if not f.embedding_text or len(f.embedding_text.strip()) == 0:
                report["findings"]["faculties_relational_and_embeddings"].append({
                    "id": f.id,
                    "issue": "Missing or empty embedding_text"
                })

        print(f"-> Faculty vector & relational issues found: {len(report['findings']['faculties_relational_and_embeddings'])}")

        # -------------------------------------------------------------
        # DIMENSION 6: Research Labs Integrity
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 6] Auditing Research Labs Foreign Keys & Embeddings ---")
        faculty_ids = set(f.id for f in faculties)
        for lab in labs:
            # Check lead advisor FK
            if lab.lead_advisor_id and lab.lead_advisor_id not in faculty_ids:
                report["findings"]["research_labs_integrity"].append({
                    "lab_id": lab.id,
                    "issue": f"Dangling lead_advisor_id '{lab.lead_advisor_id}' (not found in faculties)"
                })
            # Check member faculty FKs
            for mem_id in (lab.member_faculty_ids or []):
                if mem_id not in faculty_ids:
                    report["findings"]["research_labs_integrity"].append({
                        "lab_id": lab.id,
                        "issue": f"Dangling member_faculty_id '{mem_id}' (not found in faculties)"
                    })
            # Check embedding
            if lab.embedding is None:
                report["findings"]["research_labs_integrity"].append({
                    "lab_id": lab.id,
                    "issue": "NULL lab embedding"
                })
            elif len(lab.embedding) != 768:
                report["findings"]["research_labs_integrity"].append({
                    "lab_id": lab.id,
                    "issue": f"Invalid lab vector dimension: {len(lab.embedding)}"
                })

        print(f"-> Research labs issues found: {len(report['findings']['research_labs_integrity'])}")

        # -------------------------------------------------------------
        # DIMENSION 7: Curriculum Courses Integrity
        # -------------------------------------------------------------
        print("\n--- [DIMENSION 7] Auditing Curriculum Courses Integrity ---")
        course_ids = set()
        for c in courses:
            if c.id in course_ids:
                report["findings"]["courses_integrity"].append({
                    "course_id": c.id,
                    "issue": "Duplicate course ID"
                })
            course_ids.add(c.id)

            if not c.title_th or not c.university_th or not c.faculty_th:
                report["findings"]["courses_integrity"].append({
                    "course_id": c.id,
                    "issue": "Missing essential course hierarchy fields"
                })
            if c.embedding is None:
                report["findings"]["courses_integrity"].append({
                    "course_id": c.id,
                    "issue": "NULL course embedding"
                })
            elif len(c.embedding) != 768:
                report["findings"]["courses_integrity"].append({
                    "course_id": c.id,
                    "issue": f"Invalid course vector dimension: {len(c.embedding)}"
                })

        print(f"-> Courses issues found: {len(report['findings']['courses_integrity'])}")

        # -------------------------------------------------------------
        # SUMMARY AND EXPORT
        # -------------------------------------------------------------
        total_findings = sum(len(v) for v in report["findings"].values())
        print("\n" + "=" * 70)
        print("EXHAUSTIVE FOURTH-PASS SCAN SUMMARY")
        print("=" * 70)
        print(f"Total faculties scanned:     {len(faculties)}")
        print(f"Total research labs scanned: {len(labs)}")
        print(f"Total courses scanned:       {len(courses)}")
        print(f"TOTAL FINDINGS IDENTIFIED:   {total_findings}")
        print("=" * 70)

        out_path = BACKEND_DIR / "data" / "agent_states" / "exhaustive_fourth_pass_audit_report.json"
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nForensic report saved to: {out_path}")
        return total_findings

    finally:
        db.close()

if __name__ == "__main__":
    run_deep_scan()
