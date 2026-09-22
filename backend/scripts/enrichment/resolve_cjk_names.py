# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_latin_name_from_openalex(oa_id):
    if not oa_id or oa_id == "not_indexed":
        return None
    short_id = oa_id.split('/')[-1]
    url = f"https://api.openalex.org/authors/{short_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:advisor-match@edu.th'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            alts = data.get('display_name_alternatives') or []
            for alt in alts:
                # check if alt is ASCII/Latin
                if re.match(r'^[a-zA-Z\s\.\,\-]+$', alt):
                    return alt.strip()
            disp = data.get('display_name') or ""
            if re.match(r'^[a-zA-Z\s\.\,\-]+$', disp):
                return disp.strip()
    except Exception as e:
        print(f"Error fetching {oa_id}: {e}")
    return None

def main():
    db = SessionLocal()
    cjk_ids = [
        'udru_w56_0286_399', 'ssru_w56_0391_821', 'rmutk_w53b_0076_940', 'rmutk_w53b_0215_486',
        'rmutk_w53b_0504_848', 'rmutk_w53b_0516_717', 'rmutk_w53b_0533_446', 'rmutr_w53b_0337_830',
        'ssru_w56_0705_479', 'up_w48_0856_445', 'rmuti_w53b_1406_486', 'rmuti_w53b_2375_664',
        'sut_w46_0911_207', 'wu_w51_2081_974', 'rmutto_w53b_0437_891', 'skru_w56_0046_783', 'mfu_w52_1811_779'
    ]

    print("Fetching Latin names for CJK faculty from OpenAlex...")
    for fid in cjk_ids:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if not f: continue
        latin = get_latin_name_from_openalex(f.openalex_id)
        print(f"{fid} ({f.full_name_th}) -> Latin: '{latin}'")
        if latin:
            parts = latin.split()
            if len(parts) >= 2:
                f.first_name = parts[0]
                f.last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                f.first_name = parts[0]
            f.full_name_th = latin
            f.embedding_text = build_faculty_embedding_text(f)

    # Also clean mfu_w52_0174_701: 'ภัทรภา ดินเหลือง (黄丽悦)' -> 'ภัทรภา ดินเหลือง'
    f_mfu = db.query(FacultyDB).filter(FacultyDB.id == 'mfu_w52_0174_701').first()
    if f_mfu:
        f_mfu.full_name_th = 'ภัทรภา ดินเหลือง'
        f_mfu.embedding_text = build_faculty_embedding_text(f_mfu)
        print("Cleaned mfu_w52_0174_701 -> ภัทรภา ดินเหลือง")

    db.commit()
    db.close()
    print("Done.")

if __name__ == "__main__":
    main()
