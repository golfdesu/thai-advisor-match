import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

def validate_search():
    db = SessionLocal()
    queries = [
        "การปรับปรุงพันธุ์ข้าวหอมมะลิและการตัดต่อยีน Riceberry",
        "การให้ความร้อนด้วยคลื่นไมโครเวฟและการอบแห้งเชิงอุตสาหกรรม Microwave Thermal",
        "การผลิตก๊าซไฮโดรเจนชีวภาพ Bio-hydrogen จากของเสียโรงงานแป้งมันสำปะหลัง",
        "การวัดผลองค์กรเชิงกลยุทธ์ด้วย OKRs และ Balanced Scorecard",
        "คดีปกครอง กฎหมายรัฐธรรมนูญ และสัญญาทางปกครอง",
        "เซนเซอร์ตรวจจับดีเอ็นเอด้วย PNA (Peptide Nucleic Acid) และเคมีชีวภาพ",
        "การสกัดเส้นใยใบสับปะรด PALF เสริมแรงในยางธรรมชาติและพอลิเมอร์คอมโพสิต"
    ]

    print("=== 🎯 MULTI-DISCIPLINARY SEMANTIC SEARCH VALIDATION ===\n")

    for q in queries:
        q_vec = embedding_service.get_embedding(q)
        results = db.query(FacultyDB).order_by(FacultyDB.embedding.cosine_distance(q_vec)).limit(2).all()
        print(f"🔍 คำค้นหา: \"{q}\"")
        for idx, r in enumerate(results, 1):
            interests = ", ".join(r.research_interests[:2]) if r.research_interests else "N/A"
            print(f"   {idx}. {r.academic_title_th or ''} {r.first_name or ''} {r.last_name or ''} ({r.university_th or ''})")
            print(f"      คณะ/สำนัก: {r.faculty_th or ''} - {r.department_th or ''}")
            print(f"      ความเชี่ยวชาญ: {interests}")
        print()

    db.close()

if __name__ == "__main__":
    validate_search()
