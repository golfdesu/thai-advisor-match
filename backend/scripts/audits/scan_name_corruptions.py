# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()

print("--- SCANNING FOR ENGLISH LETTERS OR ADMINISTRATIVE WORDS IN full_name_th ---")

en_in_th = []
admin_words = ["ได้รับเงิน", "ประจำตำแหน่ง", "รักษาการ", "ปฏิบัติการแทน", "คณะกรรมการ", "นอกคณะ", "คำสั่ง", "ประกาศ"]
admin_in_th = []

for f in db.query(FacultyDB).all():
    name = f.full_name_th or ""
    # Strip known title prefixes like อ., ดร., ศ., รศ., ผศ.
    clean_name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.|สพญ\.)\s*", "", name).strip()
    clean_name = re.sub(r"^(ดร\.|พญ\.|นพ\.|ทญ\.|ทพ\.)\s*", "", clean_name).strip()

    # Check if clean_name contains english characters
    if re.search(r"[a-zA-Z]", clean_name):
        en_in_th.append((f.id, f.university_th, f.faculty_th, name, f.first_name, f.last_name, f.email))

    for w in admin_words:
        if w in name:
            admin_in_th.append((f.id, f.university_th, f.faculty_th, name, w))

print(f"Total faculty with English in full_name_th: {len(en_in_th)}")
# Group by ID prefix
prefix_counts = {}
for item in en_in_th:
    pref = item[0].split("_")[0] + "_" + (item[0].split("_")[1] if len(item[0].split("_")) > 1 else "")
    prefix_counts[pref] = prefix_counts.get(pref, 0) + 1

print("Prefix distribution:", prefix_counts)
print("\nSample records:")
for item in en_in_th[:25]:
    print(f"  {item[0]} | {item[1]} | {item[2]} | th: {repr(item[3])} | en: {item[4]} {item[5]}")

print(f"\nTotal faculty with admin words in full_name_th: {len(admin_in_th)}")
for item in admin_in_th:
    print(f"  {item[0]} | {item[1]} | {item[2]} | name: {repr(item[3])} | matched: {item[4]}")

db.close()
