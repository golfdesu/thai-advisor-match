from app.core.database import SessionLocal
from app.models.db_models import CourseDB
import sys

sys.stdout.reconfigure(encoding="utf-8")
session = SessionLocal()
mu_courses = session.query(CourseDB).filter(CourseDB.university == "Mahidol University").all()

print("Sample of 'ไม่ระบุ' faculties:")
for c in mu_courses:
    f = c.faculty_th or c.faculty
    if f == "ไม่ระบุ":
        print(f" - {c.title_th} | {c.title_en}")

print("\nSample of 'คณะวิทยาศาสตร์':")
count = 0
for c in mu_courses:
    f = c.faculty_th or c.faculty
    if f == "คณะวิทยาศาสตร์":
        print(f" - {c.title_th} | {c.title_en}")
        count += 1
        if count > 10: break
