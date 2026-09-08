# -*- coding: utf-8 -*-
import sys
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
all_facs = db.query(FacultyDB).all()

bogus_titles = {
    "content",
    "editorial board",
    "the effect of inlet and outlet pattern on a parabolic dome solar collector",
    "assessment of milking hygiene practices and raw goat milk quality: a case study of a dairy goat farm in narathiwat province, thailand",
    "effect of nine-square counting dance on physical and cognitive function in older adults with mild cognitive impairment: a randomized controlled trial",
    "greenhouse gas emissions from a petroleum naphtha storage tank"
}

affected = 0
for f in all_facs:
    if not f.featured_publications:
        continue
    has_bogus = False
    cleaned = []
    for p in f.featured_publications:
        t = (p.get("title", "") or "" if isinstance(p, dict) else str(p)).strip().lower()
        v = ((p.get("venue") or "") if isinstance(p, dict) else "").strip()
        url = ((p.get("url") or "") if isinstance(p, dict) else "").strip()
        if t in bogus_titles or "ahstr/article/view" in url or v == "วารสารวิจัย มหาวิทยาลัยนเรศวร":
            has_bogus = True
        else:
            cleaned.append(p)
    if has_bogus:
        affected += 1

print(f"Total faculties affected by NU journal bogus articles: {affected}")
db.close()
