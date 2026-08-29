import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

def run_verification():
    with SessionLocal() as db:
        courses = db.query(CourseDB).options(defer(CourseDB.embedding)).all()
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

        print("======================================================")
        print("       FINAL EXHAUSTIVE QUALITY & FACT AUDIT          ")
        print("======================================================")
        print(f"1. Total Courses in DB:   {len(courses)}")
        print(f"2. Total Faculties in DB: {len(faculties)}")

        # --- FACULTY CHECKS ---
        fac_no_vec = db.query(FacultyDB).filter(FacultyDB.embedding == None).count()
        fac_no_interests = sum(1 for f in faculties if not f.research_interests or len(f.research_interests) == 0)
        fac_no_uni_th = sum(1 for f in faculties if not f.university_th or f.university_th == 'ไม่ระบุ')
        print(f"\n[FACULTIES INTEGRITY]")
        print(f"  - Missing Embeddings:         {fac_no_vec} (0 expected)")
        print(f"  - Missing Research Interests: {fac_no_interests} (0 expected)")
        print(f"  - Missing University TH:      {fac_no_uni_th} (0 expected)")

        # --- COURSES CHECKS ---
        c_no_vec = db.query(CourseDB).filter(CourseDB.embedding == None).count()
        c_no_desc = sum(1 for c in courses if not c.description or c.description in ['ไม่ระบุ', 'None', ''] or len(c.description) < 15)
        c_no_uni_th = sum(1 for c in courses if not c.university_th or c.university_th == 'ไม่ระบุ')
        invalid_ids = sum(1 for c in courses if not c.id or c.id in ['ไม่ระบุ', 'None', 'course-1'])
        print(f"\n[COURSES INTEGRITY]")
        print(f"  - Missing Embeddings:         {c_no_vec} (0 expected)")
        print(f"  - Missing Descriptions:       {c_no_desc} (0 expected)")
        print(f"  - Missing University TH:      {c_no_uni_th} (0 expected)")
        print(f"  - Invalid / Placeholder IDs:  {invalid_ids} (0 expected)")

        # Degree Levels
        deg_dist = defaultdict(int)
        for c in courses:
            deg_dist[c.degree_level] += 1
        print(f"\n[DEGREE LEVELS DISTRIBUTION]")
        for deg, cnt in sorted(deg_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {deg:30}: {cnt}")

        # --- SEMANTIC SEARCH TESTS ---
        print(f"\n======================================================")
        print("       AI SEMANTIC SEARCH TESTS (5 DOMAINS)           ")
        print("======================================================")
        
        test_queries = [
            ("วิศวกรรมหุ่นยนต์และระบบอัตโนมัติ AI", "Course"),
            ("แพทย์ เวชศาสตร์ป้องกัน ระบาดวิทยา", "Course"),
            ("Data Science การวิเคราะห์ข้อมูลและการเงิน", "Course"),
            ("Natural Language Processing ปัญญาประดิษฐ์", "Faculty"),
            ("นิติศาสตร์ กฎหมายธุรกิจและทรัพย์สินทางปัญญา", "Course"),
        ]

        for q, target in test_queries:
            q_vec = embedding_service.get_embedding(q)
            if target == "Course":
                res = db.query(CourseDB).options(defer(CourseDB.embedding)).filter(CourseDB.embedding.isnot(None)).order_by(CourseDB.embedding.cosine_distance(q_vec)).limit(2).all()
                print(f"\n🔍 Search Course: \"{q}\"")
                for r in res:
                    print(f"   -> [{r.id}] {r.title_th} | {r.university_th} ({r.faculty_th})")
            else:
                res = db.query(FacultyDB).options(defer(FacultyDB.embedding)).filter(FacultyDB.embedding.isnot(None)).order_by(FacultyDB.embedding.cosine_distance(q_vec)).limit(2).all()
                print(f"\n🔍 Search Faculty: \"{q}\"")
                for r in res:
                    t = r.academic_title_th or ""
                    n = r.full_name_th or r.full_name or ""
                    print(f"   -> [{r.id}] {n} | {r.university_th} ({r.department_th})")

if __name__ == "__main__":
    run_verification()
