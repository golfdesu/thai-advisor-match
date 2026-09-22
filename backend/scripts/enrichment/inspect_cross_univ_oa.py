# -*- coding: utf-8 -*-
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    # Check Khattiya
    k1 = db.query(FacultyDB).filter(FacultyDB.id == 'chiangmaiu_facultyofv_khattiya_046').first()
    k2 = db.query(FacultyDB).filter(FacultyDB.id == 'wave30_0018_744').first()
    print("--- Ratch Khattiya ---")
    print("k1:", k1.id, k1.full_name_th, k1.university_th, k1.faculty_th, k1.email, k1.openalex_id, k1.total_citations)
    print("k2:", k2.id, k2.full_name_th, k2.university_th, k2.faculty_th, k2.email, k2.openalex_id, k2.total_citations)

    # Check Patchanee
    p1 = db.query(FacultyDB).filter(FacultyDB.id == 'chiangmaiu_facultyofv_patchanee_025').first()
    p2 = db.query(FacultyDB).filter(FacultyDB.id == 'mfu_w52_0477_525').first()
    print("\n--- Prapas Patchanee ---")
    print("p1:", p1.id, p1.full_name_th, p1.university_th, p1.faculty_th, p1.email, p1.openalex_id, p1.total_citations)
    print("p2:", p2.id, p2.full_name_th, p2.university_th, p2.faculty_th, p2.email, p2.openalex_id, p2.total_citations)

    # Check Tadee
    t1 = db.query(FacultyDB).filter(FacultyDB.id == 'chiangmaiu_facultyofv_tadee_032').first()
    t2 = db.query(FacultyDB).filter(FacultyDB.id == 'mfu_w52_0989_963').first()
    t3 = db.query(FacultyDB).filter(FacultyDB.id == 'wave30_0058_345').first()
    print("\n--- Pakpoom Tadee ---")
    print("t1:", t1.id, t1.full_name_th, t1.university_th, t1.faculty_th, t1.email, t1.openalex_id, t1.total_citations)
    print("t2:", t2.id, t2.full_name_th, t2.university_th, t2.faculty_th, t2.email, t2.openalex_id, t2.total_citations)
    print("t3:", t3.id, t3.full_name_th, t3.university_th, t3.faculty_th, t3.email, t3.openalex_id, t3.total_citations)

    db.close()

if __name__ == "__main__":
    main()
