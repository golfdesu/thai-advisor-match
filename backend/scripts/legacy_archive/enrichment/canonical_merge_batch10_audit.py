import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

def deduplicate_list(lst):
    seen=set(); out=[]
    for item in lst or []:
        key=json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, dict) else str(item)
        if key not in seen:
            seen.add(key); out.append(item)
    return out

def stringify_pubs(pubs):
    out=[]
    for p in pubs or []:
        if isinstance(p, dict):
            out.append(" ".join(str(v) for v in p.values()))
        else:
            out.append(str(p))
    return out

def build_embedding_text(f):
    parts=[
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.full_name_th or "", f.academic_title_th or "",
        f.faculty_th or "", f.department_th or "",
        f.faculty or "", f.department or "",
        f.university_th or "", f.university or "", f.role or "",
        " ".join(f.research_interests) if f.research_interests else "",
        " ".join(stringify_pubs(f.featured_publications)) if f.featured_publications else "",
        " ".join(f.education) if f.education else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

# (keeper_id, obsolete_id, note)
MERGES=[
    ("tu_law_surapol_001","tu_law_001","Surapol Nitikraipot - same TU Law, keep elite enriched record"),
    ("kmutt_jgsee_navadol_001","kmutt_jgsee_001","Navadol Laosiripojana - same JGSEE, keep correctly spelled Thai name (เหล่าศิริพจน์)"),
    ("ubu_eng_chatchai_001","nu_sgtech_002","Chatchai Sirisamphanwong - UBU primary, NU record has corrupted EN name Sukruedee"),
    ("md-chula-004_8979b8","swu_med_001","Vorasak/Vorasuk Shotelersuk - Chula Medicine is primary genetics center, SWU obsolete"),
    ("eg-cpe-002_1bffad","ku-eng-cpe-003_067815","Suppawong Tuarob - Mahidol EGCO current, KU obsolete (transferred)"),
]

# Homonym pairs that must NOT be merged (same romanization, different persons)
SKIP_MERGES=[
    ("cbs-014_e49a82","mu-sci-001_41f1bd","Kanya Srisuk - homonym: Accounting (Chula) vs Organic Synthesis (Mahidol)"),
    ("chula-edu-004_646066","mu-sh-019_5cf8f3","Anuchat Poungsomlee - homonym: Adult Education (Chula) vs Environmental Ethics (Mahidol)"),
]

db=SessionLocal()
print("=== Canonical Merge Batch 10 Audit (5 pairs) ===")
for keeper_id, obsolete_id, note in MERGES:
    keeper=db.query(FacultyDB).filter(FacultyDB.id==keeper_id).first()
    obsolete=db.query(FacultyDB).filter(FacultyDB.id==obsolete_id).first()
    if not keeper:
        print(f"⚠️ Keeper not found: {keeper_id} ({note})"); continue
    if not obsolete:
        print(f"⚠️ Obsolete already gone: {obsolete_id} ({note})"); continue
    print(f"\n🔀 Merging {obsolete_id} -> {keeper_id} | {note}")
    print(f"   Keeper: {keeper.full_name_th} ({keeper.university_th}) EN:{keeper.first_name} {keeper.last_name} Email:{keeper.email}")
    print(f"   Obsolete: {obsolete.full_name_th} ({obsolete.university_th}) EN:{obsolete.first_name} {obsolete.last_name} Email:{obsolete.email}")

    # Fix corrupted EN name for Chatchai case before merge
    if keeper_id=="ubu_eng_chatchai_001" and obsolete_id=="nu_sgtech_002":
        # Ensure keeper EN is correct
        keeper.first_name="Chatchai"; keeper.last_name="Sirisamphanwong"

    # Merge lists
    keeper.research_interests=deduplicate_list((keeper.research_interests or []) + (obsolete.research_interests or []))
    keeper.featured_publications=deduplicate_list((keeper.featured_publications or []) + (obsolete.featured_publications or []))
    keeper.education=deduplicate_list((keeper.education or []) + (obsolete.education or []))
    keeper.taught_courses=deduplicate_list((keeper.taught_courses or []) + (obsolete.taught_courses or []))

    # Fill missing single fields from obsolete if keeper lacks
    for field in ["image_url","scholar_url","profile_url","role","email"]:
        if not getattr(keeper, field) and getattr(obsolete, field):
            setattr(keeper, field, getattr(obsolete, field))
            print(f"   -> carrying {field}: {getattr(obsolete, field)}")
    # Special for Navadol: carry scholar/profile if keeper missing
    if keeper_id=="kmutt_jgsee_navadol_001":
        if obsolete.scholar_url and not keeper.scholar_url:
            keeper.scholar_url=obsolete.scholar_url
            print(f"   -> carrying scholar_url from obsolete")
        if obsolete.profile_url and not keeper.profile_url:
            keeper.profile_url=obsolete.profile_url
            print(f"   -> carrying profile_url from obsolete")

    # Re-vectorize
    keeper.embedding_text=build_embedding_text(keeper)
    try:
        vec=embedding_service.get_embedding(keeper.embedding_text)
        keeper.embedding=vec
        print(f"   ✅ re-vectorized (dim={len(vec) if vec else 0})")
    except Exception as e:
        print(f"   ⚠️ embedding failed: {e}")

    db.delete(obsolete)
    db.commit()
    print(f"   ✅ Deleted {obsolete_id}, keeper {keeper_id} now has {len(keeper.research_interests)} interests, {len(keeper.featured_publications)} pubs")

print("\n--- Homonym pairs skipped (not merged) ---")
for a,b,note in SKIP_MERGES:
    print(f"⏭️ SKIP {a} <-> {b} : {note}")

# Final stats
total=db.query(FacultyDB).count()
vec_count=db.query(FacultyDB).filter(FacultyDB.embedding.isnot(None)).count()
print(f"\n📊 Post-merge total: {total} | vectorized: {vec_count}")
db.close()
print("✅ Canonical merge batch 10 complete")
