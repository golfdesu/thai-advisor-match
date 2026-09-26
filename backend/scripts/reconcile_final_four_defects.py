# -*- coding: utf-8 -*-
"""
Reconcile Final 4 Faculty Anomalies using Official Verified Ground Truth:
1. tu_fineart__004: Asst. Prof. Sarupong Sudprasert (ผศ. ศรุพงษ์ สุดประเสริฐ) - Official TU Fine Arts faculty page
2. tu_grad__078: Asst. Prof. Pol. Maj. Dr. Katiya Ivanovitch (ผศ. พ.ต.ต.หญิง ดร.คัติยา อิวาโนวิช) - OpenAlex A5010092192 & fph.tu.ac.th
3. stou_commarts__0261: Assoc. Prof. Pol. Lt. Col. Dr. Siriwan Anantho (รศ. พ.ต.ท. หญิง ดร.ศิริวรรณ อนันต์โท) - OpenAlex A5054726280 & stou.ac.th
4. w85_cu_cps_0022: Prof. Dr. M. Niaz Asadullah (ศ.ดร. เอ็ม นีอาซ อัสซาดุลลาห์) - OpenAlex A5091853933 & Chulalongkorn University CPS
"""
import sys
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

CACHE_PATH = Path("/app/data/agent_states/thai_romanization_cache.json")
if not CACHE_PATH.exists():
    CACHE_PATH = BACKEND_DIR / "data" / "agent_states" / "thai_romanization_cache.json"

FINAL_CORRECTIONS = {
    "tu_fineart__004": {
        "full_name_th": "ผศ. ศรุพงษ์ สุดประเสริฐ",
        "academic_title_th": "ผศ.",
        "first_name": "Sarupong",
        "last_name": "Sudprasert",
        "openalex_id": "not_indexed"
    },
    "tu_grad__078": {
        "full_name_th": "ผศ. พ.ต.ต.หญิง ดร.คัติยา อิวาโนวิช",
        "academic_title_th": "ผศ. พ.ต.ต.หญิง ดร.",
        "first_name": "Katiya",
        "last_name": "Ivanovitch",
        "openalex_id": "https://openalex.org/A5010092192"
    },
    "stou_commarts__0261": {
        "full_name_th": "รศ. พ.ต.ท. หญิง ดร.ศิริวรรณ อนันต์โท",
        "academic_title_th": "รศ. พ.ต.ท. หญิง ดร.",
        "first_name": "Siriwan",
        "last_name": "Anantho",
        "openalex_id": "https://openalex.org/A5054726280"
    },
    "w85_cu_cps_0022": {
        "full_name_th": "ศ.ดร. เอ็ม นีอาซ อัสซาดุลลาห์",
        "academic_title_th": "ศ.ดร.",
        "first_name": "M. Niaz",
        "last_name": "Asadullah",
        "openalex_id": "https://openalex.org/A5091853933"
    }
}

def main():
    db = SessionLocal()
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)

    try:
        for fid, data in FINAL_CORRECTIONS.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                fac.full_name_th = data["full_name_th"]
                fac.academic_title_th = data["academic_title_th"]
                fac.first_name = data["first_name"]
                fac.last_name = data["last_name"]
                if data["openalex_id"]:
                    fac.openalex_id = data["openalex_id"]
                cache[fid] = {
                    "first_name": data["first_name"],
                    "last_name": data["last_name"]
                }
                print(f"[{fid}] Updated to: {data['first_name']} {data['last_name']} ({data['full_name_th']})")

        db.commit()

        if CACHE_PATH.exists():
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

        print("\nAll 4 final records successfully grounded and committed!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
