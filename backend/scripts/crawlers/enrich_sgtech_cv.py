"""Enrich NU SGtech DB rows from CV checkpoint (email-exact match, fill empties only)."""
import sys, json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

st = json.load(open(ROOT / "backend/data/agent_states/extract_1789733119_14fee8.json", encoding="utf-8"))
facs = st.get("faculties", {})
db = SessionLocal()
try:
    rows = db.query(FacultyDB).filter(
        FacultyDB.university_th == "มหาวิทยาลัยนเรศวร",
        FacultyDB.faculty_th == "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี (SGtech)").all()
    by_email = { (r.email or "").strip().lower(): r for r in rows if r.email }
    enr = {"edu": 0, "res": 0, "pub": 0, "email": 0}
    for sid, p in facs.items():
        em = (p.get("email") or "").strip().lower()
        if not em or em not in by_email: continue
        r = by_email[em]
        if p.get("education") and not (r.education or []):
            r.education = p["education"][:8]; enr["edu"] += 1
        if p.get("research_interests") and not (r.research_interests or []):
            r.research_interests = p["research_interests"][:10]; enr["res"] += 1
        if p.get("featured_publications") and not (r.featured_publications or []):
            pubs = []
            for x in p["featured_publications"][:8]:
                pubs.append({"title": x[:500]} if isinstance(x, str) else x)
            r.featured_publications = pubs; enr["pub"] += 1
        if p.get("email") and not (r.email or ""):
            r.email = p["email"].strip().lower(); enr["email"] += 1
    db.commit()
    _log(f"matched-rows {len(by_email)} enriched {enr}")
finally:
    db.close()
