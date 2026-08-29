import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

# Import datasets
from scripts.data_sources.psu_courses import PSU_COURSES
from scripts.data_sources.kmitl_kmutt_courses import KMITL_KMUTT_COURSES
from scripts.data_sources.swu_su_courses import SWU_SU_COURSES
from scripts.data_sources.buu_msu_nida_courses import BUU_MSU_NIDA_COURSES
from scripts.data_sources.top_unis_expansion import TOP_UNIS_EXPANSION_COURSES
from scripts.data_sources.batch2_curricula import BATCH2_COURSES
from scripts.data_sources.batch3_curricula import BATCH3_COURSES
from scripts.data_sources.chula_full_completion import CHULA_COMPLETION_COURSES
from scripts.data_sources.chula_exhaustive_mastery import CHULA_EXHAUSTIVE_COURSES

ALL_DATASETS = [
    ("มหาวิทยาลัยสงขลานครินทร์ (PSU)", PSU_COURSES),
    ("สจล. และ มจธ. (KMITL & KMUTT)", KMITL_KMUTT_COURSES),
    ("มศว และ ม.ศิลปากร (SWU & SU)", SWU_SU_COURSES),
    ("ม.บูรพา, มมส และ นิด้า (BUU, MSU, NIDA)", BUU_MSU_NIDA_COURSES),
    ("จุฬาฯ, ธรรมศาสตร์, มก., มข., มพ., มวล., แม่โจ้ (Top Unis & Regional)", TOP_UNIS_EXPANSION_COURSES),
    ("ชุดที่ 2: ไอที, ศิลปกรรม, ดนตรี, กฎหมาย และสาธารณสุข (Batch 2)", BATCH2_COURSES),
    ("ชุดที่ 3: แพทย์/ทันตะ/การบิน รังสิต, ภาพยนตร์/BUSEM ม.กรุงเทพ, ระบบราง มจพ., EV มทร.ธัญบุรี, วนศาสตร์/ประมง มก. (Batch 3)", BATCH3_COURSES),
    ("ชุดที่ 4: จุฬาลงกรณ์มหาวิทยาลัย ครบ 100% ทุกคณะ (ทันตะ, สหเวช, พยาบาล, สัตวแพทย์, ศิลปกรรม, ครุศาสตร์, อักษรศาสตร์, ทรัพยากรเกษตร, สหสาขาวิชา)", CHULA_COMPLETION_COURSES),
    ("ชุดที่ 5: จุฬาฯ ศศินทร์ (Sasin), วิทย์กีฬา, JIPP จิตวิทยา, ปิโตรเลียม PPC, ประชากรศาสตร์ CPS, สาธารณสุข CPHS, PGS รัฐศาสตร์, BCM นิเทศ", CHULA_EXHAUSTIVE_COURSES),
]

def build_course_embedding_text(c: CourseDB) -> str:
    parts = [
        c.title_th or "",
        c.title_en or "",
        c.degree_level or "",
        c.degree_name or "",
        c.faculty_th or "",
        c.department_th or "",
        c.university_th or "",
        c.university or "",
        c.description or "",
        " ".join(c.curriculum_highlights) if c.curriculum_highlights else "",
        " ".join(c.career_paths) if c.career_paths else "",
        " ".join(c.tags) if c.tags else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

def run_massive_ingestion():
    print("=================================================================")
    print("🚀 MASSIVE MULTI-UNIVERSITY CURRICULUM INGESTION & AI EMBEDDING")
    print("=================================================================")

    db = SessionLocal()
    total_added = 0
    total_updated = 0
    ids_to_embed = set()

    for dataset_name, dataset in ALL_DATASETS:
        print(f"\n📦 กำลังประมวลผลชุดข้อมูล: {dataset_name} ({len(dataset)} รายการ)...")
        added_in_set = 0
        updated_in_set = 0

        for item in dataset:
            cid = item["id"]
            existing = db.query(CourseDB).filter(CourseDB.id == cid).first()

            if not existing:
                new_c = CourseDB(
                    id=item["id"],
                    title_th=item["title_th"],
                    title_en=item["title_en"],
                    degree_level=item["degree_level"],
                    degree_name=item["degree_name"],
                    university=item["university"],
                    university_th=item["university_th"],
                    faculty=item["faculty"],
                    faculty_th=item["faculty_th"],
                    department=item["department"],
                    department_th=item["department_th"],
                    program_type=item["program_type"],
                    duration_years=item["duration_years"],
                    total_credits=item["total_credits"],
                    tuition_per_semester=item["tuition_per_semester"],
                    tuition_total=item["tuition_total"],
                    description=item["description"],
                    curriculum_highlights=item["curriculum_highlights"],
                    career_paths=item["career_paths"],
                    tags=item["tags"],
                    website_url=item["website_url"],
                    embedding_text=""
                )
                new_c.embedding_text = build_course_embedding_text(new_c)
                db.add(new_c)
                ids_to_embed.add(new_c.id)
                added_in_set += 1
                total_added += 1
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
                existing.embedding_text = build_course_embedding_text(existing)
                ids_to_embed.add(existing.id)
                updated_in_set += 1
                total_updated += 1

        db.commit()
        print(f"   -> เพิ่มใหม่: {added_in_set} | ปรับปรุง: {updated_in_set}")

    db.close()
    print(f"\n=================================================================")
    print(f"📊 สรุปการประมวลผลเบื้องต้น: เพิ่มใหม่ {total_added} รายการ | ปรับปรุง {total_updated} รายการ")
    print(f"=================================================================")

    # STEP 2: MULTI-THREADED AI VECTOR EMBEDDING (768-DIM) IN CHUNKS
    print(f"\n🧠 กำลังคำนวณและบันทึก AI Vector Embeddings สำหรับ {len(ids_to_embed)} หลักสูตร...")
    id_list = list(ids_to_embed)

    def fetch_vec(cid):
        with SessionLocal() as s:
            obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
            if obj and obj.embedding_text:
                vec = embedding_service.get_embedding(obj.embedding_text)
                return cid, vec
        return cid, None

    CHUNK = 20
    for i in range(0, len(id_list), CHUNK):
        batch = id_list[i:i+CHUNK]
        v_map = {}
        with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
            futs = {executor.submit(fetch_vec, cid): cid for cid in batch}
            for fut in as_completed(futs):
                cid, vec = fut.result()
                if vec:
                    v_map[cid] = vec
        if v_map:
            with SessionLocal() as s:
                for cid, vec in v_map.items():
                    c_obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
                    if c_obj:
                        c_obj.embedding = vec
                s.commit()
        print(f"   -> บันทึกเวกเตอร์สำเร็จ: {min(i+CHUNK, len(id_list))}/{len(id_list)}")

    print("\n=================================================================")
    print("✅ MASSIVE CURRICULUM INGESTION COMPLETED 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_massive_ingestion()
