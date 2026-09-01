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
    queries = [
        "นักบินพาณิชย์ การบิน รังสิต",
        "วิศวกรรมระบบรางและรถไฟความเร็วสูง พระนครเหนือ",
        "หุ่นยนต์และระบบอัตโนมัติ FIBO บางมด",
        "นวัตกรรมบูรณาการ สตาร์ทอัพ BAScii จุฬาลงกรณ์",
        "วิทยาศาสตร์ทางทะเลและสิ่งแวดล้อมชายฝั่ง ม.อ. หาดใหญ่",
        "โบราณคดีและการอนุรักษ์มรดกวัฒนธรรม ศิลปากร"
    ]
    
    print("=========================================================")
    print("🎯 TESTING SPECIALIZED CURRICULA SEMANTIC VECTOR SEARCH")
    print("=========================================================")

    with SessionLocal() as db:
        for q in queries:
            q_vec = embedding_service.get_embedding(q)
            res = db.query(CourseDB).options(defer(CourseDB.embedding)).filter(CourseDB.embedding.isnot(None)).order_by(CourseDB.embedding.cosine_distance(q_vec)).limit(1).first()
            if res:
                print(f"🔍 คำค้นหา: \"{q}\"")
                print(f"   🏆 อันดับ 1: [{res.id}] {res.title_th}")
                print(f"      🏛️ {res.university_th} ({res.faculty_th})\n")

if __name__ == "__main__":
    run_tests()
