import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

def dedup_list(items):
    if not items: return []
    seen=set(); res=[]
    for x in items:
        key=json.dumps(x,sort_keys=True,ensure_ascii=False) if isinstance(x,dict) else str(x).strip()
        if key and key not in seen:
            seen.add(key); res.append(x)
    return res

def stringify(items):
    if not items: return ""
    return " ".join(" ".join(str(v) for v in x.values() if v) if isinstance(x,dict) else str(x) for x in items)

def build_text(f):
    parts=[f"{f.first_name or ''} {f.last_name or ''}".strip(), f.full_name_th or "", f.academic_title_th or "", f.faculty_th or "", f.department_th or "", f.faculty or "", f.department or "", f.university_th or "", f.university or "", f.role or "", stringify(f.research_interests), stringify(f.featured_publications), stringify(f.education)]
    return " ".join(p.strip() for p in parts if p.strip())[:6000]

# Definite intra-university or same-person duplicates that re-appeared via batch re-ingestion
PAIRS=[("tu_law_surapol_001","tu_law_001"),("md-chula-004_8979b8","swu_med_001"),("nu_sgtech_002","ubu_eng_chatchai_001"),("kmutt_jgsee_navadol_001","kmutt_jgsee_001")]

db=SessionLocal()
merged=0
for keeper_id, obsolete_id in PAIRS:
    keeper=db.query(FacultyDB).filter(FacultyDB.id==keeper_id).first()
    obsolete=db.query(FacultyDB).filter(FacultyDB.id==obsolete_id).first()
    if not keeper or not obsolete:
        print(f"Skip {keeper_id} <- {obsolete_id}: not found (keeper={bool(keeper)}, obsolete={bool(obsolete)})")
        continue
    print(f"Merging {keeper_id} <- {obsolete_id}  [{keeper.full_name_th} @ {keeper.university_th}]")
    keeper.research_interests=dedup_list((keeper.research_interests or [])+(obsolete.research_interests or []))
    keeper.featured_publications=dedup_list((keeper.featured_publications or [])+(obsolete.featured_publications or []))
    keeper.education=dedup_list((keeper.education or [])+(obsolete.education or []))
    keeper.taught_courses=dedup_list((keeper.taught_courses or [])+(obsolete.taught_courses or []))
    if not keeper.image_url and obsolete.image_url: keeper.image_url=obsolete.image_url
    if not keeper.scholar_url and obsolete.scholar_url: keeper.scholar_url=obsolete.scholar_url
    keeper.embedding_text=build_text(keeper)
    keeper.embedding=embedding_service.get_embedding(keeper.embedding_text)
    db.delete(obsolete)
    merged+=1
db.commit()
print(f"Merged {merged} records")
print(f"Total left: {db.query(FacultyDB).count()}")
db.close()
