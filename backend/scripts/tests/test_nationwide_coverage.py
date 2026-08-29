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
        "ทันตแพทยศาสตร์ มหาวิทยาลัยสงขลานครินทร์ หาดใหญ่",
        "สถาปัตยกรรมเขตร้อน มหาวิทยาลัยสงขลานครินทร์ วิทยาเขตตรัง",
        "เทคโนโลยียางและพอลิเมอร์ชีวภาพ สุราษฎร์ธานี",
        "การบริการและการท่องเที่ยวพรีเมียม ภูเก็ต",
        "แพทยศาสตร์ มหาวิทยาลัยนเรศวร พิษณุโลก",
        "วิศวกรรมชีวการแพทย์ ลาดกระบัง",
        "วิศวกรรมการผลิต แม่พิมพ์อุตสาหกรรม มจธ บางมด",
        "เวชศาสตร์ทางทะเลและใต้น้ำ แพทย์ มหาวิทยาลัยบูรพา",
        "กายภาพบำบัด วารีบำบัด มศว",
        "การออกแบบนิเทศศิลป์ มัณฑนศิลป์ วังท่าพระ ศิลปากร"
    ]
    
    print("=========================================================")
    print("🎯 TESTING NATIONWIDE REGIONAL CURRICULA SEMANTIC SEARCH")
    print("=========================================================")

    with SessionLocal() as db:
        for q in test_queries:
            q_vec = embedding_service.get_embedding(q)
            res = db.query(CourseDB).options(defer(CourseDB.embedding)).filter(CourseDB.embedding.isnot(None)).order_by(CourseDB.embedding.cosine_distance(q_vec)).limit(1).first()
            if res:
                print(f"🔍 คำค้นหา: \"{q}\"")
                print(f"   🏆 อันดับ 1: [{res.id}] {res.title_th}")
                print(f"      🏛️ {res.university_th} | {res.faculty_th} ({res.degree_level})\n")

if __name__ == "__main__":
    run_tests()
