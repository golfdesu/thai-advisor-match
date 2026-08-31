import sys
import os
import re
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict
from sqlalchemy.orm import defer

def clean_title(name):
    if not name:
        return ''
    titles = [
        'ศาสตราจารย์ ดร.', 'รองศาสตราจารย์ ดร.', 'ผู้ช่วยศาสตราจารย์ ดร.',
        'ศาสตราจารย์', 'รองศาสตราจารย์', 'ผู้ช่วยศาสตราจารย์', 'อาจารย์ ดร.', 'อาจารย์',
        'ศ.ดร.', 'รศ.ดร.', 'ผศ.ดร.', 'อ.ดร.', 'ดร.', 'ศ.', 'รศ.', 'ผศ.', 'อ.',
        'Prof. Dr.', 'Assoc. Prof. Dr.', 'Asst. Prof. Dr.', 'Prof.', 'Assoc. Prof.', 'Asst. Prof.', 'Dr.'
    ]
    res = name
    for t in titles:
        res = res.replace(t, '')
    return re.sub(r'\s+', ' ', res).strip()

def run_audit():
    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
    print(f"Total faculty records in DB: {len(faculties)}")

    # 1. Thai Name Duplicates
    th_name_groups = defaultdict(list)
    for f in faculties:
        c_name = clean_title(f.full_name_th)
        if c_name:
            th_name_groups[c_name].append(f)

    # 2. English Name Duplicates
    en_name_groups = defaultdict(list)
    for f in faculties:
        if f.first_name and f.last_name:
            en_key = f"{f.first_name.strip().lower()} {f.last_name.strip().lower()}"
            en_name_groups[en_key].append(f)

    # 3. Email Duplicates
    email_groups = defaultdict(list)
    for f in faculties:
        if f.email and '@' in f.email:
            email_groups[f.email.strip().lower()].append(f)

    dup_th = {k: v for k, v in th_name_groups.items() if len(v) > 1}
    dup_en = {k: v for k, v in en_name_groups.items() if len(v) > 1}
    dup_email = {k: v for k, v in email_groups.items() if len(v) > 1}

    print("\n=================================================================")
    print("📋 ผลการตรวจสอบความซ้ำซ้อนของข้อมูลอาจารย์ในฐานข้อมูล")
    print("=================================================================")

    print(f"\n1. 📧 อีเมลซ้ำกัน (Duplicate Emails): {len(dup_email)} กลุ่ม")
    if dup_email:
        for em, grp in dup_email.items():
            print(f"   [Email: {em}]")
            for f in grp:
                print(f"     - ID: {f.id} | {f.academic_title_th} {f.full_name_th} ({f.first_name} {f.last_name}) | {f.university_th} - {f.faculty_th}")
    else:
        print("   ✅ ไม่พบอีเมลซ้ำกันเลย (0 records)")

    print(f"\n2. 🇹🇭 ชื่อภาษาไทยซ้ำกัน (หลัง Normalize ตัดคำนำหน้า/ตำแหน่ง): {len(dup_th)} กลุ่ม")
    if dup_th:
        for name, grp in dup_th.items():
            print(f"   [ชื่อไทย: \"{name}\"] ({len(grp)} รายการ)")
            for f in grp:
                print(f"     - ID: {f.id} | {f.academic_title_th} {f.full_name_th} | EN: {f.first_name} {f.last_name} | {f.university_th} | คณะ: {f.faculty_th} | Email: {f.email}")
    else:
        print("   ✅ ไม่พบชื่อภาษาไทยซ้ำกันเลย (0 records)")

    print(f"\n3. 🇬🇧 ชื่อภาษาอังกฤษซ้ำกัน (First + Last Name): {len(dup_en)} กลุ่ม")
    if dup_en:
        for name, grp in dup_en.items():
            print(f"   [ชื่ออังกฤษ: \"{name}\"] ({len(grp)} รายการ)")
            for f in grp:
                print(f"     - ID: {f.id} | {f.academic_title_th} {f.full_name_th} | {f.university_th} - {f.faculty_th} | Email: {f.email}")
    else:
        print("   ✅ ไม่พบชื่อภาษาอังกฤษซ้ำกันเลย (0 records)")

    db.close()

if __name__ == "__main__":
    run_audit()
