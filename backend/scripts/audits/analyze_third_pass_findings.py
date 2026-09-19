import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def analyze():
    report_path = BACKEND_DIR / "data" / "agent_states" / "exhaustive_third_pass_audit_report.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))

    db = SessionLocal()
    try:
        print("=== DETAILED BREAKDOWN OF TITLES & NAMES ===")
        for item in data.get("titles_and_names", []):
            fac = db.query(FacultyDB).filter(FacultyDB.id == item["id"]).first()
            if fac:
                print(f"ID: {fac.id} | Name: {fac.full_name_th} | Uni: {fac.university_th} | Fac: {fac.faculty_th} | Title: {fac.academic_title_th}")

        print("\n=== DETAILED BREAKDOWN OF CONTACT & PDPA (SHARED EMAILS) ===")
        for item in data.get("contact_and_pdpa", []):
            if item.get("type") == "shared_email_across_persons":
                email = item["email"]
                facs = db.query(FacultyDB).filter(FacultyDB.email == email).all()
                print(f"\nEmail: {email} (Count: {len(facs)})")
                for f in facs:
                    print(f"   -> ID: {f.id} | Name: {f.full_name_th} | Uni: {f.university_th} | Fac: {f.faculty_th} | Cites: {f.total_citations} | OpenAlex: {f.openalex_id}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze()
