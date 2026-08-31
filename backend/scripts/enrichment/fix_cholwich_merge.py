import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

def dedup_list(lst):
    seen=set(); out=[]
    for x in lst or []:
        key=json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, dict) else str(x).strip()
        if key not in seen and key:
            seen.add(key); out.append(x)
    return out

def build_text(f):
    parts=[
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.full_name_th or "", f.academic_title_th or "",
        f.faculty_th or "", f.department_th or "",
        f.faculty or "", f.department or "",
        f.university_th or "", f.university or "", f.role or "",
        " ".join(f.research_interests) if f.research_interests else "",
        " ".join([json.dumps(p, ensure_ascii=False) if isinstance(p, dict) else str(p) for p in (f.featured_publications or [])]),
        " ".join(f.education) if f.education else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

db = SessionLocal()
keeper_id = "tu_siit_cholwich_001"
obsolete_id = "tu_siit_003"
keeper = db.query(FacultyDB).filter(FacultyDB.id==keeper_id).first()
obsolete = db.query(FacultyDB).filter(FacultyDB.id==obsolete_id).first()
if not keeper or not obsolete:
    print(f"Skip: keeper {keeper_id} exists={bool(keeper)}, obsolete {obsolete_id} exists={bool(obsolete)}")
    sys.exit(0)

print(f"Merging {obsolete_id} -> {keeper_id}")
print(f" Keeper: {keeper.full_name_th} EN:{keeper.first_name} {keeper.last_name} | {keeper.email}")
print(f" Obsolete: {obsolete.full_name_th} EN:{obsolete.first_name} {obsolete.last_name} | {obsolete.email}")

# Deep merge
keeper.research_interests = dedup_list((keeper.research_interests or []) + (obsolete.research_interests or []))
keeper.featured_publications = dedup_list((keeper.featured_publications or []) + (obsolete.featured_publications or []))
keeper.education = dedup_list((keeper.education or []) + (obsolete.education or []))
keeper.taught_courses = dedup_list((keeper.taught_courses or []) + (obsolete.taught_courses or []))
for field in ["image_url","scholar_url","profile_url","role"]:
    if not getattr(keeper, field) and getattr(obsolete, field):
        setattr(keeper, field, getattr(obsolete, field))
        print(f"  carried {field}")

# Normalize Thai name to keeper (elite form is more accurate with full title dedup), keep EN as Nattee (Google Scholar confirms Nattee)
keeper.embedding_text = build_text(keeper)
try:
    keeper.embedding = embedding_service.get_embedding(keeper.embedding_text)
    print(f"  re-vectorized dim={len(keeper.embedding) if keeper.embedding else 0}")
except Exception as e:
    print(f"  embedding failed: {e}")

db.delete(obsolete)
db.commit()
print(f"  Deleted {obsolete_id}")
print(f"  Keeper now: {len(keeper.research_interests)} interests, {len(keeper.featured_publications)} pubs")

total=db.query(FacultyDB).count()
vec=db.query(FacultyDB).filter(FacultyDB.embedding.isnot(None)).count()
print(f"Post-merge total: {total} | vectorized: {vec}")
db.close()
