# -*- coding: utf-8 -*-
"""
Dry-run comprehensive database hygiene repairs.
"""
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

db = SessionLocal()

print("=" * 70)
print("🧪 DRY-RUN COMPREHENSIVE DATABASE HYGIENE REPAIRS")
print("=" * 70)

# 1. CMU Duplicates
pasiri_donor = db.query(FacultyDB).filter(FacultyDB.id == "cmu_21646dd5_9077").first()
pasiri_target = db.query(FacultyDB).filter(FacultyDB.id == "cmu_398c4c40_5859").first()
print(f"[1.1] Pasiri Singhasiri: donor={pasiri_donor is not None}, target={pasiri_target is not None}")

siam_donor = db.query(FacultyDB).filter(FacultyDB.id == "cmu_6add0253_6499").first()
siam_target = db.query(FacultyDB).filter(FacultyDB.id == "cmu-med-021_9d90dd").first()
print(f"[1.2] Siam Tongprasert: donor={siam_donor is not None}, target={siam_target is not None}")

# 2. Administrative decree names
leena = db.query(FacultyDB).filter(FacultyDB.id == "mu_pharm_wave12_0064").first()
nuttanan = db.query(FacultyDB).filter(FacultyDB.id == "mu_pharm_wave12_0096").first()
print(f"[2] Administrative decree names: Leena={leena is not None}, Nuttanan={nuttanan is not None}")

# 3. KKU glued titles
kku_glued = [
    ("kku_agri_wave14_b_0079", "รศ.ดร. ประกายจันทร์ นิ่มกิ่งรัตน์"),
    ("kku_agri_wave14_b_0080", "รศ.ดร. อุบล ตังควานิช"),
    ("kku_agri_wave14_b_0081", "ผศ.ดร. ดวงรัตน์ ธงภักดิ์"),
    ("kku_agri_wave14_b_0082", "ผศ.ดร. ยุวธิดา ศรีพลแท่น"),
    ("kku_agri_wave14_b_0083", "ผศ.ดร. นรินทร์ ชมภูพวง"),
    ("kku_agri_wave14_b_0084", "อ.ดร. ปพิชญา เตียวกุล"),
    ("kku_agri_wave14_b_0086", "ผศ.ดร. สุวิตา แสไพศาล"),
    ("kku_agri_wave14_b_0087", "รศ.ดร. เพชรรัตน์ ธรรมเบญจพล"),
    ("kku_agri_wave14_b_0088", "ผศ.ดร. กานต์สิรี จินดาปัณณาพัฒน์"),
    ("kku_agri_wave14_b_0089", "อ.ดร. ชเนรินทร์ ฟ้าแลบ"),
]
found_kku = 0
for fid, clean in kku_glued:
    rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
    if rec:
        found_kku += 1
print(f"[3] KKU Agriculture glued titles: {found_kku}/10 found")

# 4. Hidden characters
thanasak = db.query(FacultyDB).filter(FacultyDB.id == "sut_thanasak_phittayakorn_8728").first()
print(f"[4] SUT Thanasak Phittayakorn: {thanasak is not None}")

# 5. English title parsing in mu_pharm_wave12
mu_pharm_assist = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.id.like("mu_pharm_wave12%"),
        FacultyDB.first_name == "Assist."
    )
    .all()
)
print(f"[5.1] mu_pharm_wave12 with first_name='Assist.': {len(mu_pharm_assist)}")

# KKU Ph.D. in last_name
kku_phd = db.query(FacultyDB).filter(FacultyDB.last_name.like("%Ph.D%")).all()
print(f"[5.2] Faculties with Ph.D in last_name: {len(kku_phd)}")

# 6. Impossible metrics
zero_work_h = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.h_index > 0,
        FacultyDB.total_citations == 0,
        FacultyDB.total_publications_count == 0,
    )
    .all()
)
print(f"[6] Faculty with h_index > 0 and 0 cits & 0 pubs: {len(zero_work_h)}")

# 7. Course duration & program_type
c_dur = [
    c for c in db.query(CourseDB).all()
    if (c.duration_years or "").strip() in ["1-2", "3-4", "3 - 4", "0.5", "1.5"]
]
print(f"[7.1] Courses with raw numeric duration range: {len(c_dur)}")

pt_map = {
    "นานาชาติ (International Program)": "นานาชาติ",
    "หลักสูตรนานาชาติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
    "หลักสูตรนานาชาติ / หลักสูตรสหสาขาวิชา / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
    "หลักสูตรนานาชาติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ ) / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ",
    "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันเสาร์-อาทิตย์ )": "ภาคปกติ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคปกติ (วันเสาร์-อาทิตย์)": "ภาคปกติ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ ) / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ / ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
    "หลักสูตรสองภาษา / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "สองภาษา / ภาคพิเศษ",
    "หลักสูตรสองภาษา / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "สองภาษา",
    "หลักสูตรไทย (ภาคพิเศษ)": "ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันจันทร์-ศุกร์ (ช่วงเย็น)) และ ภาคพิเศษ (วันเสาร์-อาทิตย์)": "ภาคพิเศษ",
    "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
    "โครงการพิเศษ (เสาร์-อาทิตย์)": "ภาคพิเศษ",
    "ภาคปกติ / โครงการพิเศษ": "ภาคปกติ / ภาคพิเศษ",
    "ภาคปกติ (23,000 บาท/เทอม) | โครงการพิเศษ/นานาชาติ (50,000 บาท/เทอม)": "ภาคปกติ / โครงการพิเศษ",
    "วิจัยเต็มเวลา (Full Research)": "วิจัยเต็มเวลา",
}
c_pt = [c for c in db.query(CourseDB).all() if (c.program_type or "").strip() in pt_map]
print(f"[7.2] Courses with unstandardized program_type: {len(c_pt)}")

db.close()
