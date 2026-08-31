import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

def deduplicate_list(items):
    if not items:
        return []
    seen = set()
    res = []
    for x in items:
        if isinstance(x, dict):
            key = json.dumps(x, sort_keys=True, ensure_ascii=False)
        else:
            key = str(x).strip()
        if key not in seen and key:
            seen.add(key)
            res.append(x)
    return res

def stringify_list(items):
    if not items:
        return ""
    res = []
    for x in items:
        if isinstance(x, dict):
            res.append(" ".join(str(v) for v in x.values() if v))
        else:
            res.append(str(x))
    return " ".join(res)

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
        stringify_list(f.research_interests),
        stringify_list(f.featured_publications),
        stringify_list(f.education)
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

NEW_BATCH_DUPLICATES = [
    # (keeper_id, obsolete_id)
    ("cu_eng_suttichai_001", "cu_eng_chem_001"),        # ศ.ดร. สุทธิชัย อัสสะบำรุงรัตน์
    ("kmutt_fibo_001", "kmutt_fibo_djitt_laowattana"),  # รศ. ดร.ชิต เหล่าวัฒนา
    ("sut_eng_001", "sut_eng_jiraphon_001"),            # รศ.ดร. จิระพล ศรีเสริฐผล
    ("tu_tbs_nopadol_001", "tu_tbs_002"),               # ศ.ดร. นภดล ร่มโพธิ์
    ("tu_eng_phadungsak_001", "tu_tse_phadungsak_001"), # ศ.ดร. ผดุงศักดิ์ รัตนเดโช
    ("kku_tech_alissara_001", "kku_sci_alissara_001"),  # ศ.ดร. อลิศรา เรืองแสง
    ("md-chula-004_8979b8", "swu_med_001"),             # ศ.ดร.พญ. วรศักดิ์ โชติเลอศักดิ์ (already done but verifying)
    ("tu_law_surapol_001", "tu_law_001"),               # ศ.ดร. สุรพล นิติไกรพจน์
    ("nu_sgtech_002", "ubu_eng_chatchai_001"),          # รศ.ดร. ชัชชัย ศิริสัมพันธ์วงศ์ (already done but verifying)
    ("cu_sci_tirayut_001", "cu_sci_pna_001"),           # ศ.ดร. ธีรยุทธ วิไลวัลย์
    ("kmutt_jgsee_navadol_001", "kmutt_jgsee_001"),     # ศ.ดร. นวดล เหล่าศิริพจน์ (Fuzzy Match: เหล่าศิริพจนา)
    ("mu_si_ptye_001", "mu_si_pathai_001"),             # ศ.ดร. เพทาย เย็นจิตโสมนัส (Fuzzy Match: ปัทมาพันธุ์)
    ("psu_agro_soottawat_001", "psu_marine_biotech_001"), # ศ.ดร. สุทธวัฒน์ เบญจกุล (Fuzzy Match: สุทธิวัฒน์)
]

def execute_new_batch_merges():
    print("=================================================================")
    print("🧹 EXECUTING FINAL MERGE FOR RECENT ELITE BATCH")
    print("=================================================================")

    db = SessionLocal()
    merged_count = 0

    for keeper_id, obsolete_id in NEW_BATCH_DUPLICATES:
        keeper = db.query(FacultyDB).filter(FacultyDB.id == keeper_id).first()
        obsolete = db.query(FacultyDB).filter(FacultyDB.id == obsolete_id).first()

        if not keeper or not obsolete:
            continue

        print(f"\n🔗 Merging: {keeper.id} [{keeper.university_th}] <- {obsolete.id} [{obsolete.university_th}]")

        keeper.research_interests = deduplicate_list((keeper.research_interests or []) + (obsolete.research_interests or []))
        keeper.featured_publications = deduplicate_list((keeper.featured_publications or []) + (obsolete.featured_publications or []))
        keeper.education = deduplicate_list((keeper.education or []) + (obsolete.education or []))
        keeper.taught_courses = deduplicate_list((keeper.taught_courses or []) + (obsolete.taught_courses or []))

        if not keeper.image_url and obsolete.image_url:
            keeper.image_url = obsolete.image_url
        if not keeper.scholar_url and obsolete.scholar_url:
            keeper.scholar_url = obsolete.scholar_url
        if not keeper.role and obsolete.role:
            keeper.role = obsolete.role
        if not keeper.email and obsolete.email:
            keeper.email = obsolete.email
        if not keeper.profile_url and obsolete.profile_url:
            keeper.profile_url = obsolete.profile_url

        keeper.embedding_text = build_faculty_embedding_text(keeper)
        keeper.embedding = embedding_service.get_embedding(keeper.embedding_text)

        db.delete(obsolete)
        merged_count += 1

    db.commit()
    print(f"\n✅ Merged {merged_count} duplicate records.")

    total_left = db.query(FacultyDB).count()
    print(f"\n📊 Total Unique Faculty Records Now: {total_left} ท่าน")
    print("=================================================================")
    db.close()

if __name__ == "__main__":
    execute_new_batch_merges()
