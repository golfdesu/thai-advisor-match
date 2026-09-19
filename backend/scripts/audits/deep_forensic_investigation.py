"""Deep forensic investigation of shared emails, duplicates, name formatting, and cross-batch anomalies."""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from rapidfuzz import fuzz

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB, CourseDB

TITLE_PREFIXES = [
    "ศ.ดร.นพ.", "ศ.ดร.พญ.", "ศ.ดร.ทพ.", "ศ.ดร.ทพญ.", "ศ.ดร.สพ.ญ.", "ศ.ดร.สพ.", "ศ.ดร.น.สพ.",
    "รศ.ดร.นพ.", "รศ.ดร.พญ.", "รศ.ดร.ทพ.", "รศ.ดร.ทพญ.", "รศ.ดร.สพ.ญ.", "รศ.ดร.สพ.", "รศ.ดร.น.สพ.",
    "ผศ.ดร.นพ.", "ผศ.ดร.พญ.", "ผศ.ดร.ทพ.", "ผศ.ดร.ทพญ.", "ผศ.ดร.สพ.ญ.", "ผศ.ดร.สพ.", "ผศ.ดร.น.สพ.",
    "อ.ดร.นพ.", "อ.ดร.พญ.", "อ.ดร.ทพ.", "อ.ดร.ทพญ.", "อ.ดร.สพ.ญ.", "อ.ดร.สพ.", "อ.ดร.น.สพ.",
    "ศ. (เชี่ยวชาญพิเศษ)ดร. นพ.", "ศ. (เชี่ยวชาญพิเศษ)ทพญ. ดร.", "ศ. (เชี่ยวชาญพิเศษ)ทพ. ดร.",
    "ศ. (เกียรติคุณ) ดร.", "ศ. (เกียรติคุณ)", "ศ. (คลินิก) ดร. สพ.ญ.", "ผศ. (พิเศษ)พญ.",
    "อ. (ผู้ทรงคุณวุฒิ) รศ. ดร.", "อ. (ผู้ทรงคุณวุฒิ) ศ. ดร.", "อ. (ผู้ทรงคุณวุฒิ) ผศ. ดร.",
    "รศ. สพ.ญ. ดร.", "รศ. ภญ. ดร.", "ผศ. สพ.ญ. ดร.", "ผศ. ภญ. ดร.",
    "รศ. น.สพ. ดร.", "ผศ. น.สพ. ดร.", "อ. น.สพ. ดร.",
    "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ดร.",
    "ศ.เกียรติคุณ", "ศ.คลินิก", "ศ.พิเศษ", "รศ.พิเศษ", "ผศ.พิเศษ",
    "ศ.", "รศ.", "ผศ.", "อ.", "นพ.", "พญ.", "ทพ.", "ทพญ.", "สพ.ญ.", "น.สพ.", "ภก.", "ภญ."
]

def clean_title(name: str) -> str:
    cleaned = name.strip()
    for t in sorted(TITLE_PREFIXES, key=len, reverse=True):
        if cleaned.startswith(t):
            cleaned = cleaned[len(t):].strip()
            break
    # also strip parentheses like (ผู้ทรงคุณวุฒิ) or (เชี่ยวชาญพิเศษ)
    cleaned = re.sub(r"^\([^)]+\)\s*", "", cleaned)
    return cleaned.strip()

def investigate():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).all()
        print(f"Total faculty: {len(faculties)}")

        # 1. Investigate ALL shared emails (including identical names)
        email_map = defaultdict(list)
        for f in faculties:
            if f.email:
                email_map[f.email.lower().strip()].append(f)

        shared_emails_same_person = []
        shared_emails_diff_person = []

        for email, facs in email_map.items():
            if len(facs) > 1:
                names = [clean_title(f.full_name_th or "") for f in facs]
                # Compare similarity
                sim = fuzz.token_sort_ratio(names[0], names[1])
                record_info = {
                    "email": email,
                    "count": len(facs),
                    "faculties": [
                        {
                            "id": f.id,
                            "name": f.full_name_th,
                            "cleaned_name": clean_title(f.full_name_th or ""),
                            "uni": f.university_th,
                            "fac": f.faculty_th,
                            "cites": f.total_citations,
                            "h_idx": f.h_index,
                            "pubs": f.total_publications_count,
                            "openalex": f.openalex_id,
                            "profile_url": f.profile_url
                        }
                        for f in facs
                    ],
                    "sim": sim
                }
                if sim >= 70 or any(fuzz.token_set_ratio(n1, n2) >= 85 for n1 in names for n2 in names if n1 != n2):
                    shared_emails_same_person.append(record_info)
                else:
                    shared_emails_diff_person.append(record_info)

        print(f"\n1. Shared Emails Analysis:")
        print(f"   - Same Person (Duplicates needing Merge): {len(shared_emails_same_person)}")
        print(f"   - Different Persons (Contaminated/Shared inboxes): {len(shared_emails_diff_person)}")

        # 2. Investigate Parentheses & Title formatting
        parentheses_records = []
        for f in faculties:
            if f.full_name_th and ("(" in f.full_name_th or ")" in f.full_name_th):
                parentheses_records.append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "uni": f.university_th,
                    "fac": f.faculty_th,
                    "email": f.email
                })

        print(f"\n2. Parentheses in Name: {len(parentheses_records)}")

        # 3. Investigate exact name duplicates across universities or faculties
        name_map = defaultdict(list)
        for f in faculties:
            cname = clean_title(f.full_name_th or "")
            if cname and len(cname.split()) >= 2:
                name_map[(cname, f.university_th)].append(f)

        intra_uni_duplicate_names = []
        for (cname, uni), facs in name_map.items():
            if len(facs) > 1:
                # Check if this duplicate was already caught by shared_emails
                emails = set(f.email for f in facs if f.email)
                intra_uni_duplicate_names.append({
                    "name": cname,
                    "uni": uni,
                    "count": len(facs),
                    "faculties": [
                        {
                            "id": f.id,
                            "raw_name": f.full_name_th,
                            "fac": f.faculty_th,
                            "email": f.email,
                            "cites": f.total_citations,
                            "openalex": f.openalex_id
                        }
                        for f in facs
                    ]
                })

        print(f"\n3. Intra-University Name Duplicates: {len(intra_uni_duplicate_names)}")

        # Save comprehensive results
        out_data = {
            "shared_emails_same_person": shared_emails_same_person,
            "shared_emails_diff_person": shared_emails_diff_person,
            "parentheses_records": parentheses_records,
            "intra_uni_duplicate_names": intra_uni_duplicate_names
        }
        out_file = BACKEND_DIR / "data" / "agent_states" / "deep_forensic_investigation_report.json"
        out_file.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport written to: {out_file}")

    finally:
        db.close()

if __name__ == "__main__":
    investigate()
