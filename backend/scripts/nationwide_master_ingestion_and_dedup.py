import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB, FacultyDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer
from sqlalchemy import func

# Import new nationwide curricula datasets
from scripts.data_sources.psu_full_campuses import PSU_FULL_CAMPUSES_COURSES
from scripts.data_sources.kmitl_kmutt_full import KMITL_KMUTT_FULL_COURSES
from scripts.data_sources.swu_su_buu_full import SWU_SU_BUU_FULL_COURSES
from scripts.data_sources.nu_ku_grad_full import NU_KU_GRAD_FULL_COURSES

ALL_EXPANSION_DATASETS = [
    ("มหาวิทยาลัยสงขลานครินทร์ 5 วิทยาเขต (PSU Full Campuses)", PSU_FULL_CAMPUSES_COURSES),
    ("สจล. และ มจธ. ครบทุกภาควิชา (KMITL & KMUTT Full)", KMITL_KMUTT_FULL_COURSES),
    ("มศว, ม.ศิลปากร และ ม.บูรพา ครบทุกกลุ่มสาขา (SWU, SU, BUU Full)", SWU_SU_BUU_FULL_COURSES),
    ("ม.นเรศวร และ ม.เกษตรศาสตร์ บัณฑิตศึกษา ป.โท-เอก (NU & KU Grad)", NU_KU_GRAD_FULL_COURSES),
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

def execute_nationwide_expansion_and_dedup():
    print("==========================================================================")
    print("🚀 NATIONWIDE CURRICULA EXPANSION & COMPREHENSIVE DEDUPLICATION ENGINE")
    print("==========================================================================")

    # -------------------------------------------------------------------------
    # STEP 1: INGESTION OF NEW NATIONWIDE DATASETS
    # -------------------------------------------------------------------------
    db = SessionLocal()
    total_added = 0
    total_updated = 0
    ids_to_embed = set()

    for dataset_name, dataset in ALL_EXPANSION_DATASETS:
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
    print(f"\n✅ บันทึกชุดข้อมูลใหม่สำเร็จ: เพิ่มใหม่ {total_added} รายการ | ปรับปรุง {total_updated} รายการ")

    # -------------------------------------------------------------------------
    # STEP 2: RIGOROUS REDUNDANCY DETECTION & INTELLIGENT MERGING
    # -------------------------------------------------------------------------
    print("\n🔍 เริ่มกระบวนการตรวจสอบและกำจัดข้อมูลซ้ำซ้อน (Redundancy Deduplication)...")
    db = SessionLocal()
    all_courses = db.query(CourseDB).all()
    
    # Group by (university, normalized title, degree_level)
    groups = defaultdict(list)
    for c in all_courses:
        norm_title = (c.title_th or "").strip().lower().replace(" ", "")
        norm_uni = (c.university or "").strip().lower()
        norm_deg = (c.degree_level or "").strip()
        key = (norm_uni, norm_title, norm_deg)
        groups[key].append(c)

    deleted_count = 0
    merged_count = 0

    for key, items in groups.items():
        if len(items) > 1:
            # Score each item based on completeness
            def completeness_score(course: CourseDB) -> int:
                score = 0
                if course.tuition_per_semester: score += 5
                if course.tuition_total: score += 5
                if course.website_url: score += 5
                if course.description and len(course.description) > 50: score += 5
                if course.curriculum_highlights and len(course.curriculum_highlights) > 0: score += 3
                if course.career_paths and len(course.career_paths) > 0: score += 3
                if course.tags and len(course.tags) > 0: score += 2
                if course.embedding is not None: score += 2
                return score

            sorted_items = sorted(items, key=completeness_score, reverse=True)
            canonical = sorted_items[0]
            redundant_duplicates = sorted_items[1:]

            # Merge missing fields from duplicates into canonical
            for dup in redundant_duplicates:
                if not canonical.tuition_per_semester and dup.tuition_per_semester:
                    canonical.tuition_per_semester = dup.tuition_per_semester
                if not canonical.tuition_total and dup.tuition_total:
                    canonical.tuition_total = dup.tuition_total
                if not canonical.website_url and dup.website_url:
                    canonical.website_url = dup.website_url
                if not canonical.description and dup.description:
                    canonical.description = dup.description
                if not canonical.curriculum_highlights and dup.curriculum_highlights:
                    canonical.curriculum_highlights = dup.curriculum_highlights
                if not canonical.career_paths and dup.career_paths:
                    canonical.career_paths = dup.career_paths

                # Delete duplicate
                db.delete(dup)
                deleted_count += 1
                merged_count += 1

            canonical.embedding_text = build_course_embedding_text(canonical)
            ids_to_embed.add(canonical.id)

    db.commit()
    db.close()
    print(f"🧹 รวมและกำจัดหลักสูตรที่ซ้ำซ้อนสำเร็จ: ลบส่วนซ้ำ {deleted_count} รายการ (รวมข้อมูลครบถ้วน)")

    # -------------------------------------------------------------------------
    # STEP 3: RE-COMPUTE VECTOR EMBEDDINGS (768-DIM) SAFELY IN CHUNKS
    # -------------------------------------------------------------------------
    # Also check if any courses are currently missing embeddings
    db = SessionLocal()
    missing_vecs = db.query(CourseDB.id).filter(CourseDB.embedding == None).all()
    for row in missing_vecs:
        ids_to_embed.add(row[0])
    db.close()

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

    print("\n==========================================================================")
    print("✅ NATIONWIDE CURRICULA EXPANSION & DEDUPLICATION COMPLETED 100%!")
    print("==========================================================================")

if __name__ == "__main__":
    execute_nationwide_expansion_and_dedup()
