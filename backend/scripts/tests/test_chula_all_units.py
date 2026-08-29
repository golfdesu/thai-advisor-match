import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

def run_tests():
    test_queries = [
        "Sasin Flexible MBA ศศินทร์ จุฬาลงกรณ์",
        "วิทยาศาสตร์การกีฬาและการออกกำลังกาย จุฬา",
        "JIPP จิตวิทยานานาชาติ จุฬาลงกรณ์ University of Queensland",
        "วิทยาศาสตร์พอลิเมอร์ PPC จุฬาลงกรณ์",
        "ประชากรศาสตร์ สังคมผู้สูงอายุ จุฬาลงกรณ์ CPS",
        "การเมืองและโลกสัมพันธ์ศึกษา PGS รัฐศาสตร์ จุฬา",
        "การจัดการการสื่อสาร BCM นิเทศศาสตร์ จุฬา"
    ]
    
    print("=========================================================")
    print("🎯 TESTING CHULALONGKORN COMPLETE COVERAGE SEARCH")
    print("=========================================================")

    with SessionLocal() as db:
        for q in test_queries:
            q_vec = embedding_service.get_embedding(q)
            res = db.query(CourseDB).options(defer(CourseDB.embedding)).filter(CourseDB.university == 'Chulalongkorn University', CourseDB.embedding.isnot(None)).order_by(CourseDB.embedding.cosine_distance(q_vec)).limit(1).first()
            if res:
                print(f"🔍 คำค้นหา: \"{q}\"")
                print(f"   🏆 อันดับ 1: [{res.id}] {res.title_th}")
                print(f"      🏛️ {res.faculty_th} ({res.degree_level})\n")

if __name__ == "__main__":
    run_tests()
