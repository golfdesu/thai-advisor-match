# -*- coding: utf-8 -*-
import os
import sys
import re
from collections import defaultdict
from rapidfuzz import fuzz

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_en_name(f):
    fn = (f.first_name or "").strip()
    ln = (f.last_name or "").strip()
    if fn and ln and not re.search(r'[฀-๿]', fn) and not re.search(r'[฀-๿]', ln):
        return f"{fn} {ln}".lower()
    # If full_name_th has no Thai
    if f.full_name_th and not re.search(r'[฀-๿]', f.full_name_th):
        s = re.sub(r'^(Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s*', '', f.full_name_th, flags=re.IGNORECASE).strip()
        return s.lower()
    return ""

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).filter(FacultyDB.openalex_id.isnot(None)).filter(FacultyDB.openalex_id != 'not_indexed').all()

    by_oa = defaultdict(list)
    for f in facs:
        oa = f.openalex_id.replace("https://openalex.org/", "").strip()
        if oa:
            by_oa[oa].append(f)

    truly_different = []
    for oa, cluster in by_oa.items():
        if len(cluster) > 1:
            en_names = list(set(get_en_name(f) for f in cluster if get_en_name(f)))
            if len(en_names) >= 2:
                # check similarity
                min_sim = min(fuzz.token_sort_ratio(en_names[i], en_names[j]) for i in range(len(en_names)) for j in range(i+1, len(en_names)))
                if min_sim < 60:
                    truly_different.append((oa, cluster, en_names))

    print(f"Total OpenAlex IDs shared by TRULY DIFFERENT English names: {len(truly_different)}")
    for oa, cluster, names in truly_different[:15]:
        print(f"\nOpenAlex ID: {oa} | Names: {names}")
        for f in cluster:
            print(f"   {f.id} | {f.full_name_th} | en: {f.first_name} {f.last_name} | {f.university_th} | {f.faculty_th}")

    db.close()

if __name__ == "__main__":
    main()
