# -*- coding: utf-8 -*-
"""
Normalize empty strings ("") to SQL NULL (None) across all string columns in FacultyDB:
first_name, last_name, email, profile_url, image_url, academic_title_th,
faculty, faculty_th, department, department_th, scholar_url.
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def main():
    db = SessionLocal()
    cols = [
        'first_name', 'last_name', 'email', 'profile_url', 'image_url',
        'academic_title_th', 'faculty', 'faculty_th', 'department', 'department_th', 'scholar_url'
    ]

    for col in cols:
        attr = getattr(FacultyDB, col)
        updated = db.query(FacultyDB).filter(attr == '').update({attr: None}, synchronize_session=False)
        print(f"Updated {updated} records where {col} == ''.")

    db.commit()
    db.close()
    print("Empty strings normalized to NULL successfully.")

if __name__ == "__main__":
    main()
