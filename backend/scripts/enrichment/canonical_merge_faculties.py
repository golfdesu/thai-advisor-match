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

# Mapping of (canonical_keeper_id, obsolete_duplicate_id)
# Verified real institutional affiliations:
CANONICAL_MERGE_PAIRS = [
    # 1. ศ.นพ. กิตติศักดิ์ สวรรยาวิสุทธิ์ -> มข. (KKU คณะแพทยศาสตร์)
    ("kku_med_kittisak_001", "cmu-med-007_b66197"),

    # 2. รศ.ดร. กานดา รุณาเพ็ง สายแก้ว -> มข. (KKU วิทยาลัยการคอมพิวเตอร์)
    ("kku_comp_kanda_001", "camt-cmu-009_083a06"),

    # 3. ศ.ดร. วรวัฒน์ มีวาสนา -> มทส. (SUT สำนักวิชาวิทยาศาสตร์)
    ("sut_sci_worawat_001", "chula_sci_007_587384"),

    # 4. รศ.ดร. ฉัตรชัย โชติษฐยางกูร -> มข. (KKU คณะวิศวกรรมศาสตร์)
    ("kku_eng_chatchai_j_001", "sut_eng_chatchai_001"),

    # 5. ศ.ดร. สมชาย วงศ์วิเศษ -> มจธ. (KMUTT คณะวิศวกรรมศาสตร์)
    ("kmutt_eng_001", "cu_eng_me_thermal_001"),

    # 6. ศ.ดร. สมประวิณ มันประเสริฐ -> มธ. (TU คณะเศรษฐศาสตร์)
    ("tu_econ_001", "econ-cu-013_be7879"),

    # 7. ศ.ดร.นพ. ชัชชัย เหมือนประสาท -> มหิดล (Mahidol คณะแพทยศาสตร์ รพ.รามาธิบดี)
    ("rama_med_013_8eae76", "cu_ahs_physio_001"),

    # 8. ศ.ดร. สุขสันติ์ หอพิบูลสุข -> มทส. (SUT สำนักวิชาวิศวกรรมศาสตร์)
    ("sut_civil_geo_001", "tu_tse_suksun_001"),

    # 9. รศ.ดร. กิตติศักดิ์ ปรกติ -> มธ. (TU คณะนิติศาสตร์)
    ("tu_law_kittisak_001", "chula-law-007_0b9b18"),

    # 10. รศ.ดร. มงคล เอกปัญญาพงศ์ -> มก. (KU คณะวิศวกรรมศาสตร์)
    ("ku-eng-ee-007_d30e07", "chula_sci_006_a86f06"),

    # 11. ศ.ดร. บุญชัย เตชะอำนาจ -> จุฬาฯ (CU คณะวิศวกรรมศาสตร์)
    ("cu-eng-ee-002_f70a64", "sut_eng_boonchai_001"),

    # 12. ศ.นพ. รุ่งโรจน์ กฤตยพงษ์ -> มหิดล (Mahidol คณะแพทยศาสตร์ศิริราชพยาบาล)
    ("mu_si_rungroj_001", "cu_med_cardio_001"),

    # 13. ศ.ทพญ.ดร. วรานุช ปิติพัฒน์ -> มข. (KKU คณะทันตแพทยศาสตร์)
    ("kku_dent_waranuch_001", "dt-mu-008_7ff31c"),

    # 14. ศ.ทญ.ดร. นวรัตน์ วราอัศวปติ -> มข. (KKU คณะทันตแพทยศาสตร์)
    ("kku_dent_nawarat_001", "dt-mu-017_c54c74"),

    # 15. รศ.ดร. เกียรติอนันต์ ล้วนแก้ว -> มธ. (TU คณะเศรษฐศาสตร์)
    ("tu_econ_kiatanantha_001", "econ-cu-008_f41bb4"),

    # 16. รศ.ดร. ศุภชัย ศรีสุชาติ -> มธ. (TU คณะเศรษฐศาสตร์)
    ("tu_econ_supachai_001", "econ-cu-018_742dd9"),

    # 17. รศ.ดร. ชัชชัย ศิริสัมพันธ์วงศ์ -> ม.นเรศวร (NU วิทยาลัยพลังงานทดแทน SGtech)
    ("nu_sgtech_002", "ubu_eng_chatchai_001"),

    # 18. รศ.ดร. สมยศ เกียรติวนิชวิไล -> สจล. (KMITL คณะวิศวกรรมศาสตร์)
    ("kmitl_rail_001", "kku_eng_somyot_001"),
]

def execute_canonical_merges():
    print("=================================================================")
    print("🚀 EXECUTING CANONICAL DISAMBIGUATION & FACULTY MERGES")
    print("=================================================================")

    db = SessionLocal()
    merged_count = 0

    for keeper_id, obsolete_id in CANONICAL_MERGE_PAIRS:
        keeper = db.query(FacultyDB).filter(FacultyDB.id == keeper_id).first()
        obsolete = db.query(FacultyDB).filter(FacultyDB.id == obsolete_id).first()

        if not keeper or not obsolete:
            print(f"⚠️ Skip: keeper ({keeper_id}) or obsolete ({obsolete_id}) not found.")
            continue

        print(f"\n🔗 Merging duplicate into Canonical: {keeper.academic_title_th} {keeper.first_name} {keeper.last_name}")
        print(f"   Keeper: {keeper.id} [{keeper.university_th}] <- Obsolete: {obsolete.id} [{obsolete.university_th}]")

        # Deep merge properties
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

        # Update embedding text and vector
        keeper.embedding_text = build_faculty_embedding_text(keeper)
        keeper.embedding = embedding_service.get_embedding(keeper.embedding_text)

        db.delete(obsolete)
        merged_count += 1

    db.commit()
    print(f"\n=================================================================")
    print(f"✅ Merged & Purged {merged_count} duplicate records successfully!")

    total_left = db.query(FacultyDB).count()
    print(f"📊 Final Unique Faculty in Database: {total_left} ท่าน")
    print("=================================================================")
    db.close()

if __name__ == "__main__":
    execute_canonical_merges()
