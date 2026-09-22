# -*- coding: utf-8 -*-
"""
Execute cleaning for Regional & Specialized Universities Cluster:
- Deletes 23 phantom, non-person, and support staff records
- Fixes 33 double/repeated titles, English titles, trailing punctuation, and spacing issues
- Re-syncs embedding_text
"""
import os
import sys
import json
import re
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "clean_regional_univs_deleted.json"
)

DELETE_IDS = [
    # 6 Phantoms (name is purely "อ.")
    "ubonratcha_collegeofl_xiaowen_019",
    "ubonratcha_collegeofl_jing_020",
    "ubonratcha_collegeofl_kondo_027",
    "ubonratcha_collegeofl_masaki_028",
    "ubonratcha_collegeofl_sasaki_029",
    "ubonratcha_collegeofl_chenchi_018",
    # 6 Non-persons & Breadcrumbs
    "wave21_0212_272",
    "buu_w42_0245_825",
    "buu_w42_0246_581",
    "kmutnb_w40_0017_843",
    "kmutnb_w40_0018_224",
    "sut_w46_0027_114",
    # 11 Support Staff (MFU)
    "mfu_w52_0278_498",
    "mfu_w52_0279_482",
    "mfu_w52_0280_165",
    "mfu_w52_0281_166",
    "mfu_w52_0282_812",
    "mfu_w52_0283_354",
    "mfu_w52_0284_752",
    "mfu_w52_0285_117",
    "mfu_w52_0286_819",
    "mfu_w52_0287_769",
    "mfu_w52_0288_814",
]

def main():
    db = SessionLocal()
    try:
        # 1. Snapshot and Delete
        targets = db.query(FacultyDB).filter(FacultyDB.id.in_(DELETE_IDS)).all()
        print(f"Found {len(targets)} records to delete in Regional cluster")

        snapshot = []
        for r in targets:
            snapshot.append({
                "id": r.id,
                "full_name_th": r.full_name_th,
                "university_th": r.university_th,
                "faculty_th": r.faculty_th,
                "department_th": r.department_th,
                "role": r.role,
                "deleted_at": datetime.now().isoformat()
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        # Unlink foreign keys in research_labs
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(DELETE_IDS)).all()
        if labs:
            for l in labs:
                l.lead_advisor_id = None
            print(f"Unlinked {len(labs)} lab lead advisor references")

        for r in targets:
            db.delete(r)
        print(f"Deleted {len(targets)} records")

        # 2. Fixes & Normalizations
        # Double titles
        double_title_map = {
            "wave22_0152_622": ("นพ.", "นพ. ดร. วิพุธ ลักษณานันต์"),
            "wave22_0153_166": ("นพ.", "นพ. ดร. สมบูรณ์ ปัญญาดิลก"),
            "wave22_0141_212": ("พญ.", "พญ. นวพร นภาอำไพรศรี"),
            "wave22_0142_417": ("พญ.", "พญ. ชนิดา สุวรรณสิงห์"),
            "wave22_0143_347": ("พญ.", "พญ. พิริยา สิทธิประภา"),
            "wave22_0144_485": ("นพ.", "นพ. ศตวรรษ กลิ่นจันทร์"),
            "wave22_0218_333": ("ทพญ.", "ทพญ. นลิน ตรีวิทยาพันธุ์"),
            "wave22_0226_296": ("ทพญ.", "ทพญ. มัลลิกา ศิริสัมพันธ์"),
            "wave22_0227_890": ("ทพญ.", "ทพญ. นภาพร จรดล"),
            "wave22_0249_956": ("ทพญ.", "ทพญ. วชิรพร ภู่สำลี"),
            "wave22_0219_109": ("ทพญ.", "ทพญ. ชลพรรษ มหาดำรงค์กุล"),
            "wave22_0250_213": ("ทพญ.", "ทพญ. จีรภา อุดมเลิศ"),
            "wave22_0872_386": ("ภญ.", "ภญ. มิ่งขวัญ โพธิ์ศิริผล"),
            "ubonratcha_facultyofa_urosophon_034": ("น.สพ.ดร.", "น.สพ.ดร. นนทกรณ์ อุรโสภณ"),
        }
        for fid, (title, name) in double_title_map.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                fac.academic_title_th = title
                fac.full_name_th = name
                fac.embedding_text = build_faculty_embedding_text(fac)

        # SUT English titles
        sut_map = {
            "sut_w46_0375_824": ("รศ.ดร.", "รศ.ดร. Chatchai Jothiyangkoon"),
            "sut_w46_0452_673": ("ศ.ดร.", "ศ.ดร. Kongpan Areerak"),
            "sut_w46_0661_166": ("ผศ.ดร.", "ผศ.ดร. Suthatip Pueboobpaphan"),
            "sut_w46_0694_360": ("อ.ดร.", "อ.ดร. I-soon Raungratanaamporn"),
            "sut_w46_0767_953": ("ผศ.ดร.", "ผศ.ดร. Asadullah"),
        }
        for fid, (title, name) in sut_map.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                fac.academic_title_th = title
                fac.full_name_th = name
                fac.embedding_text = build_faculty_embedding_text(fac)

        # MFU truncated name
        fac = db.query(FacultyDB).filter(FacultyDB.id == "mfu_im_76672").first()
        if fac:
            fac.full_name_th = "อ. พจ. Chin Jia Wei"
            fac.academic_title_th = "อ.พจ."
            fac.embedding_text = build_faculty_embedding_text(fac)

        # Trailing dashes
        dashes_map = [
            ("msu_w47_1060_777", "Preecha Noiumkar"),
            ("tsu_w50_0018_247", "ผศ.ดร. วาทิต โสดานิล"),
            ("tsu_w50_0188_330", "อ. อนุสรณ์ ปานคง"),
            ("tsu_w50_0205_492", "อ. ชนกฤต ชลภาพ"),
            ("tsu_w50_0243_892", "อ.ดร. มารุต นวนใจเสือ"),
            ("tsu_w50_0251_649", "ผศ.ดร. พินทุสร จิตสวัสดิ์"),
            ("tsu_w50_0275_410", "ผศ.ดร. อุไร หัสจำนง"),
            ("tsu_w50_0345_123", "ผศ.ดร. วันดี สุตเธียรกุล"),
        ]
        for fid, clean_name in dashes_map:
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                fac.full_name_th = clean_name
                fac.embedding_text = build_faculty_embedding_text(fac)

        # Zero-width chars
        zero_width_ids = ["su_w43_0020_998", "su_w43_0096_389", "su_w43_0097_121", "nu_w45_0324_431"]
        for fid in zero_width_ids:
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac and fac.full_name_th:
                fac.full_name_th = fac.full_name_th.replace("​", "").replace("﻿", "").strip()
                fac.embedding_text = build_faculty_embedding_text(fac)

        # SWU trailing Ph.D.
        fac = db.query(FacultyDB).filter(FacultyDB.id == "swu_w44_0101_161").first()
        if fac:
            fac.full_name_th = "CHALAO THEPCHALERM"
            fac.embedding_text = build_faculty_embedding_text(fac)

        # Compound title spacing
        spacing_map = {
            "mfu_med_komsan_001": ("รศ.ดร.นพ.", "รศ.ดร.นพ. คมสันต์ เกียรติรุ่งฤทธิ์"),
            "su_pharm_pornsak_001": ("ศ.ดร.ภก.", "ศ.ดร.ภก. พรศักดิ์ ศรีอมรศักดิ์"),
            "mfu_antiaging_001": ("ศ.ดร.พญ.", "ศ.ดร.พญ. ธันวรังค์ ทิวาวรรณวงศ์"),
            "swu_dent_adv_001": ("ศ.คลินิก ทพญ.", "ศ.คลินิก ทพญ. มนทิรา ลิลิตภักดี"),
        }
        for fid, (title, name) in spacing_map.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                fac.academic_title_th = title
                fac.full_name_th = name
                fac.embedding_text = build_faculty_embedding_text(fac)

        db.commit()
        print("Regional cluster updates and deletions committed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
