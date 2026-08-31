import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

# Import datasets
from scripts.data_sources.tu_kku_faculties import TU_KKU_FACULTIES
from scripts.data_sources.psu_kmitl_kmutt_faculties import PSU_KMITL_KMUTT_FACULTIES
from scripts.data_sources.sut_swu_su_buu_faculties import SUT_SWU_SU_BUU_FACULTIES
from scripts.data_sources.batch2_faculties_expansion import BATCH2_FACULTIES
from scripts.data_sources.regional_universities_faculties import REGIONAL_UNIVERSITIES_FACULTIES
from scripts.data_sources.mfu_expanded_faculties import MFU_EXPANDED_FACULTIES
from scripts.data_sources.elite_breakthrough_faculties import ELITE_BREAKTHROUGH_FACULTIES
from scripts.data_sources.multi_disciplinary_outstanding_faculties import MULTI_DISCIPLINARY_OUTSTANDING_FACULTIES
from scripts.data_sources.new_elite_faculties_batch7 import NEW_ELITE_FACULTIES_BATCH_7

ALL_FACULTY_DATASETS = [
    ("มหาวิทยาลัยธรรมศาสตร์ และ มหาวิทยาลัยขอนแก่น (TU & KKU)", TU_KKU_FACULTIES),
    ("ม.สงขลานครินทร์, สจล. และ มจธ. (PSU, KMITL, KMUTT - FIBO/SIT)", PSU_KMITL_KMUTT_FACULTIES),
    ("มทส., มศว, ม.ศิลปากร และ ม.บูรพา (SUT, SWU, SU, BUU)", SUT_SWU_SU_BUU_FACULTIES),
    ("ชุดที่ 2: อาจารย์ดีเด่นแห่งชาติ ธรรมศาสตร์, ขอนแก่น, ม.อ., สจล. และ มจธ. (Batch 2 Expansion)", BATCH2_FACULTIES),
    ("ชุดที่ 3: อาจารย์และนักวิจัยมหาวิทยาลัยภูมิภาค (PSU, NU, BUU, MFU, UBU, MSU, WU, UP, TSU, MJU, SU, SWU)", REGIONAL_UNIVERSITIES_FACULTIES),
    ("ชุดที่ 4: คณาจารย์และนักวิจัยชั้นนำ มหาวิทยาลัยแม่ฟ้าหลวง (MFU Comprehensive Expansion)", MFU_EXPANDED_FACULTIES),
    ("ชุดที่ 5: นักวิทยาศาสตร์ดีเด่นแห่งชาติและระดับโลก (CU, CMU, SUT, KKU Breakthrough Leaders)", ELITE_BREAKTHROUGH_FACULTIES),
    ("ชุดที่ 6: อาจารย์ดีเด่นแห่งชาติและผู้ทรงคุณวุฒิหลากหลายสาขา (KU, TU, KKU, CU, MU Multi-Disciplinary)", MULTI_DISCIPLINARY_OUTSTANDING_FACULTIES),
    ("ชุดที่ 7: นักวิจัยดีเด่นแห่งชาติและนักวิทยาศาสตร์รางวัลสากล (Batch 7: Elite Scholars)", NEW_ELITE_FACULTIES_BATCH_7),
]

def build_faculty_embedding_text(f: FacultyDB) -> str:
    parts = [
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.full_name_th or "",
        f.academic_title_th or "",
        f.faculty_th or "",
        f.department_th or "",
        f.faculty or "",
        f.department or "",
        f.university_th or "",
        f.university or "",
        f.role or "",
        " ".join(f.research_interests) if f.research_interests else "",
        " ".join(f.featured_publications) if f.featured_publications else "",
        " ".join(f.education) if f.education else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

def run_faculty_ingestion():
    print("=================================================================")
    print("🚀 MASSIVE FACULTY ADVISOR INGESTION & AI EMBEDDING PIPELINE")
    print("=================================================================")

    db = SessionLocal()
    total_added = 0
    total_updated = 0
    ids_to_embed = set()

    for dataset_name, dataset in ALL_FACULTY_DATASETS:
        print(f"\n👨‍🏫 กำลังประมวลผลชุดข้อมูลอาจารย์: {dataset_name} ({len(dataset)} ท่าน)...")
        added_in_set = 0
        updated_in_set = 0

        for item in dataset:
            fid = item["id"]
            existing = db.query(FacultyDB).filter(FacultyDB.id == fid).first()

            filtered_data = {
                "id": item["id"],
                "university": item.get("university"),
                "university_th": item.get("university_th"),
                "faculty": item.get("faculty"),
                "faculty_th": item.get("faculty_th"),
                "department": item.get("department"),
                "department_th": item.get("department_th"),
                "academic_title_th": item.get("academic_title_th"),
                "first_name": item.get("first_name"),
                "last_name": item.get("last_name"),
                "full_name_th": item.get("full_name_th"),
                "role": item.get("role"),
                "email": item.get("email"),
                "image_url": item.get("image_url"),
                "profile_url": item.get("profile_url"),
                "education": item.get("education", []),
                "research_interests": item.get("research_interests", []),
                "taught_courses": item.get("taught_courses", []),
                "featured_publications": item.get("featured_publications", []),
                "scholar_url": item.get("scholar_url"),
                "embedding_text": ""
            }

            if not existing:
                new_f = FacultyDB(**filtered_data)
                new_f.embedding_text = build_faculty_embedding_text(new_f)
                db.add(new_f)
                ids_to_embed.add(new_f.id)
                added_in_set += 1
                total_added += 1
            else:
                for k, v in filtered_data.items():
                    if k != "id":
                        setattr(existing, k, v)
                existing.embedding_text = build_faculty_embedding_text(existing)
                ids_to_embed.add(existing.id)
                updated_in_set += 1
                total_updated += 1

        db.commit()
        print(f"   -> เพิ่มอาจารย์ใหม่: {added_in_set} | ปรับปรุงข้อมูล: {updated_in_set}")

    db.close()
    print(f"\n=================================================================")
    print(f"📊 สรุปการประมวลผลเบื้องต้น: เพิ่มใหม่อาจารย์ {total_added} ท่าน | ปรับปรุง {total_updated} ท่าน")
    print(f"=================================================================")

    # STEP 2: MULTI-THREADED AI VECTOR EMBEDDING (768-DIM)
    print(f"\n🧠 กำลังคำนวณและบันทึก AI Vector Embeddings สำหรับอาจารย์ {len(ids_to_embed)} ท่าน...")
    id_list = list(ids_to_embed)

    def fetch_vec(fid):
        with SessionLocal() as s:
            obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if obj and obj.embedding_text:
                vec = embedding_service.get_embedding(obj.embedding_text)
                return fid, vec
        return fid, None

    CHUNK = 20
    for i in range(0, len(id_list), CHUNK):
        batch = id_list[i:i+CHUNK]
        v_map = {}
        with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
            futs = {executor.submit(fetch_vec, fid): fid for fid in batch}
            for fut in as_completed(futs):
                fid, vec = fut.result()
                if vec:
                    v_map[fid] = vec
        if v_map:
            with SessionLocal() as s:
                for fid, vec in v_map.items():
                    f_obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                    if f_obj:
                        f_obj.embedding = vec
                s.commit()
        print(f"   -> บันทึกเวกเตอร์สำเร็จ: {min(i+CHUNK, len(id_list))}/{len(id_list)}")

    print("\n=================================================================")
    print("✅ FACULTY ADVISOR INGESTION & AI EMBEDDING COMPLETED 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_faculty_ingestion()
