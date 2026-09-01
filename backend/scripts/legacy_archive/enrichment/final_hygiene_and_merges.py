import sys
import os
import json
import re
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

def clean_repeated_title(name_th):
    if not name_th:
        return name_th
    # Clean patterns like "ศ.ดร. ศ.ดร. ...", "รศ.ดร. รศ.ดร. ...", "ผศ.ดร. ผศ.ดร. ...", "อ. อ. ..."
    patterns = [
        (r'^(ศ\.ดร\.\s+)+ศ\.ดร\.\s*', 'ศ.ดร. '),
        (r'^(รศ\.ดร\.\s+)+รศ\.ดร\.\s*', 'รศ.ดร. '),
        (r'^(ผศ\.ดร\.\s+)+ผศ\.ดร\.\s*', 'ผศ.ดร. '),
        (r'^(ศ\.นพ\.ดร\.\s+)+ศ\.นพ\.ดร\.\s*', 'ศ.นพ.ดร. '),
        (r'^(ศ\.นพ\.\s+)+ศ\.นพ\.\s*', 'ศ.นพ. '),
        (r'^(รศ\.นพ\.\s+)+รศ\.นพ\.\s*', 'รศ.นพ. '),
        (r'^(ผศ\.นพ\.\s+)+ผศ\.นพ\.\s*', 'ผศ.นพ. '),
        (r'^(ศ\.ภญ\.ดร\.\s+)+ศ\.ภญ\.ดร\.\s*', 'ศ.ภญ.ดร. '),
        (r'^(รศ\.ดร\.ภญ\.\s+)+รศ\.ดร\.ภญ\.\s*', 'รศ.ดร.ภญ. '),
        (r'^(ศ\.ทพญ\.ดร\.\s+)+ศ\.ทพญ\.ดร\.\s*', 'ศ.ทพญ.ดร. '),
        (r'^(รศ\.ทญ\.ดร\.\s+)+รศ\.ทญ\.ดร\.\s*', 'รศ.ทญ.ดร. '),
        (r'^(ผศ\.\s*ดร\.\s+)+ผศ\.\s*ดร\.\s*', 'ผศ.ดร. '),
        (r'^(รศ\.\s*ดร\.\s+)+รศ\.\s*ดร\.\s*', 'รศ.ดร. '),
        (r'^(ศ\.\s*ดร\.\s+)+ศ\.\s*ดร\.\s*', 'ศ.ดร. '),
        (r'^(ดร\.\s+)+ดร\.\s*', 'ดร. '),
        (r'^(อ\.\s+)+อ\.\s*', 'อ. '),
        (r'^(นาย\s+)+นาย\s*', 'นาย '),
        (r'^(นางสาว\s+)+นางสาว\s*', 'นางสาว '),
        (r'^(ศาสตราจารย์ ดร\.\s+)+ศาสตราจารย์ ดร\.\s*', 'ศ.ดร. '),
        (r'^(รองศาสตราจารย์ ดร\.\s+)+รองศาสตราจารย์ ดร\.\s*', 'รศ.ดร. '),
        (r'^(ผู้ช่วยศาสตราจารย์ ดร\.\s+)+ผู้ช่วยศาสตราจารย์ ดร\.\s*', 'ผศ.ดร. '),
    ]
    res = name_th
    for pat, repl in patterns:
        res = re.sub(pat, repl, res)
    return res.strip()

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

# Specific deep-audit merge pairs
DEEP_MERGE_PAIRS = [
    # 1. ผศ.ดร. ชัยวุฒิ ตั้งสมชัย (CMU Business School)
    ("cmu_bus_024", "cmu-ba-008_c2c907"),

    # 2. ศ.ดร.นพ. วรศักดิ์ โชติเลอศักดิ์ (CU Medicine Center of Excellence in Medical Genetics - not SWU)
    ("md-chula-004_8979b8", "swu_med_001"),

    # 3. ศ.ดร.นพ. สุรพล อิสรไกรศีล (Siriraj Mahidol)
    ("mu_siriraj_stemcell_001", "fac_siriraj_009_fb9f37"),

    # 4. ศ.ดร.ภญ. มยุรี กัลยาวัฒนกุล (MFU Cosmetic Science)
    ("mfu_cosmetic_mayuree_001", "mfu_cossci_001"),

    # 5. รศ.ดร. ณรงค์ฤทธิ์ วราภรณ์ (KMUTT SIT)
    ("kmutt_sit_narongrit_waraporn", "kmutt_sit_narongrit_w"),

    # 6. ศ.ดร. ลดาวัลย์ พวงจิตร (KU Forestry)
    ("ku_forest_carbon_001", "ku_for_001_70ee0f"),

    # 7. ศ.ภญ.ดร. ดวงดาว ฉันทศาสตร์ (MU Pharmacy)
    ("mu_pharm_biopharm_001", "mu_pharm_doungdaw_001"),
]

def execute_final_hygiene_and_merges():
    print("=================================================================")
    print("🧹 EXECUTING FINAL MERGES & TITLE HYGIENE NORMALIZATION")
    print("=================================================================")

    db = SessionLocal()
    merged_count = 0

    # 1. Execute deep duplicate merges
    for keeper_id, obsolete_id in DEEP_MERGE_PAIRS:
        keeper = db.query(FacultyDB).filter(FacultyDB.id == keeper_id).first()
        obsolete = db.query(FacultyDB).filter(FacultyDB.id == obsolete_id).first()

        if not keeper or not obsolete:
            print(f"⚠️ Skip: keeper ({keeper_id}) or obsolete ({obsolete_id}) not found.")
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

        keeper.full_name_th = clean_repeated_title(keeper.full_name_th)
        keeper.embedding_text = build_faculty_embedding_text(keeper)
        keeper.embedding = embedding_service.get_embedding(keeper.embedding_text)

        db.delete(obsolete)
        merged_count += 1

    # 2. Normalize full_name_th across ALL remaining faculty records
    print("\n📝 Normalizing repeated titles across all faculty records...")
    all_faculties = db.query(FacultyDB).all()
    title_fixed = 0

    for f in all_faculties:
        cleaned_th = clean_repeated_title(f.full_name_th)
        if cleaned_th != f.full_name_th:
            f.full_name_th = cleaned_th
            title_fixed += 1

    db.commit()
    print(f"✅ Merged {merged_count} duplicate records.")
    print(f"✅ Cleaned and normalized titles for {title_fixed} records.")

    total_left = db.query(FacultyDB).count()
    print(f"\n📊 Total Unique Faculty Records Now: {total_left} ท่าน")
    print("=================================================================")
    db.close()

if __name__ == "__main__":
    execute_final_hygiene_and_merges()
