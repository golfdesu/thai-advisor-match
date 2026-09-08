# -*- coding: utf-8 -*-
"""
Fast Disambiguation of merged university strings in faculties table
"""
import os, sys, re
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def disambiguate_fast():
    session = SessionLocal()
    records = session.query(FacultyDB).filter(FacultyDB.university_th.like('%และ%')).all()
    print(f"Found {len(records)} records with merged university strings.")

    fixed = 0
    for f in records:
        email = (f.email or "").lower()
        dep = f.department_th or ""
        fac = f.faculty_th or ""
        fid = f.id.lower()
        name = f.full_name_th or ""

        # Determine university
        uni_th = None
        uni_en = None

        if "chula.ac.th" in email:
            uni_th, uni_en = "จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"
        elif "mahidol.ac.th" in email or "mahidol.edu" in email:
            uni_th, uni_en = "มหาวิทยาลัยมหิดล", "Mahidol University"
        elif "cmu.ac.th" in email:
            uni_th, uni_en = "มหาวิทยาลัยเชียงใหม่", "Chiang Mai University"
        elif "ku.ac.th" in email or "ku.th" in email:
            uni_th, uni_en = "มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University"
        elif "tu.ac.th" in email:
            uni_th, uni_en = "มหาวิทยาลัยธรรมศาสตร์", "Thammasat University"
        elif "chulalongk" in fid:
            # Check if this profile came from Chula or Mahidol based on department or known names
            if "ศิริราช" in dep or "รามาธิบดี" in dep or "เวชศาสตร์เขตร้อน" in dep:
                uni_th, uni_en = "มหาวิทยาลัยมหิดล", "Mahidol University"
            else:
                uni_th, uni_en = "จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"
        elif "mahidol" in fid:
            if "เชียงใหม่" in dep:
                uni_th, uni_en = "มหาวิทยาลัยเชียงใหม่", "Chiang Mai University"
            else:
                uni_th, uni_en = "มหาวิทยาลัยมหิดล", "Mahidol University"
        else:
            uni_th, uni_en = "จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"

        f.university_th = uni_th
        f.university = uni_en
        fixed += 1

    session.commit()
    print(f"Successfully disambiguated {fixed} records!")

    remaining = session.query(FacultyDB).filter(FacultyDB.university_th.like('%และ%')).count()
    print(f"Remaining ambiguous records: {remaining}")
    session.close()

if __name__ == "__main__":
    disambiguate_fast()
