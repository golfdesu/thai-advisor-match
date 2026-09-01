import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

def run_tests():
    test_queries = [
        "Natural Language Processing AI ประมวลผลภาษาไทย ธรรมศาสตร์",
        "หุ่นยนต์และระบบอัตโนมัติ การแพทย์ อุตสาหกรรม FIBO บางมด",
        "มะเร็งท่อน้ำดี พยาธิใบไม้ตับ ขอนแก่น",
        "ปะการัง การฟื้นฟูระบบนิเวศทางทะเล สงขลานครินทร์",
        "พลังงานสะอาด ไฮโดรเจน ตัวเร่งปฏิกิริยา JGSEE บางมด",
        "แสงซินโครตรอน วัสดุควอนตัม แบตเตอรี่ สุรนารี",
        "โบราณคดีก่อนประวัติศาสตร์ วัฒนธรรมโลงไม้ ศิลปากร",
        "การจัดการท่าเรือและโลจิสติกส์พาณิชยนาวี EEC บูรพา"
    ]
    
    print("=========================================================")
    print("🎯 TESTING MULTI-UNIVERSITY FACULTY ADVISOR AI MATCHING")
    print("=========================================================")

    with SessionLocal() as db:
        for q in test_queries:
            q_vec = embedding_service.get_embedding(q)
            res = db.query(FacultyDB).options(defer(FacultyDB.embedding)).filter(FacultyDB.embedding.isnot(None)).order_by(FacultyDB.embedding.cosine_distance(q_vec)).limit(1).first()
            if res:
                print(f"🔍 คำค้นหางานวิจัย: \"{q}\"")
                print(f"   🏆 ที่ปรึกษาอันดับ 1: [{res.id}] {res.full_name_th} ({res.first_name} {res.last_name})")
                print(f"      🏛️ {res.university_th} | {res.faculty_th} ({res.department_th})")
                print(f"      🔬 สาขาความเชี่ยวชาญ: {', '.join(res.research_interests[:3])}\n")

if __name__ == "__main__":
    run_tests()
