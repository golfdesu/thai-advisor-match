# -*- coding: utf-8 -*-
"""
Phase 1: Academic Title Alignment, English Name Hygiene & Repeated Prefix Cleaning:
1. Clean 28 records with civic titles in academic_title_th or full_name_th.
2. Fix 19 records with repeated compound titles in full_name_th.
3. Clean 90 records with English title prefixes in first_name/last_name.
4. Clear generic departmental email on tu_6f157d02_7209 (dean@ap.tu.ac.th).
5. Align academic_title_th with full_name_th across all records.
6. Rebuild embedding_text for all modified records.
"""
import os
import sys
import re
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from sqlalchemy.orm import defer

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "phase1_title_and_en_clean_snapshot.json"
)

RE_TITLE = re.compile(
    r"^(ศ\.เชี่ยวชาญพิเศษ\s+ดร\.\s+นพ\.|ศ\.คลินิก\s+ดร\.\s+สพ\.ญ\.|ศ\.คลินิก\s+ทพญ\.|"
    r"ศ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|ศ\.ดร\.ภก\.|ศ\.ดร\.ภญ\.|ศ\.ดร\.น\.สพ\.|ศ\.ดร\.สพ\.ญ\.|"
    r"รศ\.ดร\.นพ\.|รศ\.ดร\.พญ\.|รศ\.ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.น\.สพ\.|รศ\.ดร\.สพ\.ญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|"
    r"ผศ\.ดร\.นพ\.|ผศ\.ดร\.พญ\.|ผศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.น\.สพ\.|ผศ\.ดร\.สพ\.ญ\.|ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|"
    r"ศ\.นพ\.|ศ\.พญ\.|ศ\.ภก\.|ศ\.ภญ\.|ศ\.น\.สพ\.|ศ\.สพ\.ญ\.|ศ\.ทพ\.|ศ\.ทพญ\.|"
    r"รศ\.นพ\.|รศ\.พญ\.|รศ\.ภก\.|รศ\.ภญ\.|รศ\.น\.สพ\.|รศ\.สพ\.ญ\.|รศ\.ทพ\.|รศ\.ทพญ\.|"
    r"ผศ\.นพ\.|ผศ\.พญ\.|ผศ\.ภก\.|ผศ\.ภญ\.|ผศ\.น\.สพ\.|ผศ\.สพ\.ญ\.|ผศ\.ทพ\.|ผศ\.ทพญ\.|"
    r"อ\.นพ\.|อ\.พญ\.|อ\.ภก\.|อ\.ภญ\.|อ\.น\.สพ\.|อ\.สพ\.ญ\.|อ\.ทพ\.|อ\.ทพญ\.|"
    r"ศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+นพ\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\)|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*"
)

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

REPEATED_TITLE_MAP = {
    "cu_vet_swine_001": ("ศ.น.สพ.ดร.", "ศ.น.สพ.ดร. รุ่งโรจน์ ธนาวงษ์นุเวช"),
    "mu_vet_parntep_001": ("รศ.น.สพ.", "รศ.น.สพ. ปานเทพ รัตนากร"),
    "cu_vet_achariya_001": ("ศ.ดร.สพ.ญ.", "ศ.ดร.สพ.ญ. อัจฉริยา ไศละสูต"),
    "ku_vet_theera_001": ("ศ.ดร.น.สพ.", "ศ.ดร.น.สพ. ธีระ รักความสุข"),
    "rama_med_010_358e74": ("รศ.ดร.นพ.", "รศ.ดร.นพ. อาทิตย์ จินาวัฒน์"),
    "rama_med_013_8eae76": ("ศ.ดร.นพ.", "ศ.ดร.นพ. ฉัตรชัย มวนประสาท"),
    "rama_med_019_4b41d7": ("รศ.ดร.นพ.", "รศ.ดร.นพ. ถาวรชัย ลิ้มจินดาพร"),
    "chulalongk_facultyofp_mangkang_048": ("อ.ดร. นาวาเอก", "อ.ดร. นาวาเอก หัสไชยญ์ มั่งคั่ง"),
    "wave24_0426_574": ("ดร.", "ดร. อิทธิภูมิ พรหมมา"),
    "wave30_0060_848": ("รศ.ดร.ภก.", "รศ.ดร.ภก. ประมณฑ์ วิวัฒนากุลวาณิชย์"),
    "wave22_0583_512": ("ผศ.ดร. พ.ต.หญิง", "ผศ.ดร. พ.ต.หญิง ปิยอร วจนะทินภัทร"),
    "wave22_0974_419": ("ดร. ว่าที่ร้อยเอก", "ดร. ว่าที่ร้อยเอก กรณภว์ กนกลภัสกุล"),
    "wave22_1155_677": ("ดร. ว่าที่ ร.ต.", "ดร. ว่าที่ ร.ต. มาโนชญ์ ตนสิงห์"),
    "wave23_0115_679": ("รศ.ดร. เรือเอก", "รศ.ดร. เรือเอก สราวุธ ลักษณะโต"),
    "wave24_0022_947": ("ผศ.ดร. ว่าที่ ร.ต.", "ผศ.ดร. ว่าที่ ร.ต. ชนวัฒน์ สรรพสิทธิ์"),
    "wave30_0027_320": ("รศ.ดร. ว่าที่ร้อยตรี", "รศ.ดร. ว่าที่ร้อยตรี จงกล พรมยะ"),
    "wave30_0028_411": ("ผศ.ดร. ว่าที่ร้อยตรี", "ผศ.ดร. ว่าที่ร้อยตรี อานุภาพ วรรณคนาพล"),
    "wave30_0084_944": ("ผศ.ดร. ว่าที่ร้อยตรี", "ผศ.ดร. ว่าที่ร้อยตรี ธรรมศักดิ์ พันธุ์แสนศรี"),
    "wave30_0147_254": ("ผศ.ดร. ว่าที่ร้อยตรี", "ผศ.ดร. ว่าที่ร้อยตรี ชัยยศ ดำรงกิจโกศล"),
}

def execute_phase1():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        print(f"Loaded {len(faculties)} faculty records for Phase 1 cleaning.")

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "modified": []
        }

        modified_count = 0

        # 1. Repeated titles fix
        for fid, (t, n) in REPEATED_TITLE_MAP.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                snapshot["modified"].append({
                    "id": f.id,
                    "field": "repeated_title",
                    "old_title": f.academic_title_th,
                    "old_name": f.full_name_th,
                    "new_title": t,
                    "new_name": n
                })
                f.academic_title_th = t
                f.full_name_th = n
                f.embedding_text = build_faculty_embedding_text(f)
                modified_count += 1

        # 2. Generic email clear on TU dean
        tu_dean = db.query(FacultyDB).filter(FacultyDB.id == "tu_6f157d02_7209").first()
        if tu_dean and tu_dean.email == "dean@ap.tu.ac.th":
            snapshot["modified"].append({
                "id": tu_dean.id,
                "field": "generic_email",
                "old_email": tu_dean.email,
                "new_email": None
            })
            tu_dean.email = None
            modified_count += 1

        # 3. Clean civic titles in academic_title_th & full_name_th
        for f in faculties:
            name = (f.full_name_th or "").strip()
            title = (f.academic_title_th or "").strip()
            changed = False

            # Fix "นาง อ. นาง ..." or "นาย อ. ..."
            m_cbs = re.match(r"^(?:นาย|นาง|นางสาว)\s+(อ\.|ผศ\.|รศ\.|ศ\.|ดร\.)\s+(?:นาย|นาง|นางสาว)?\s*(.*)", name)
            if m_cbs:
                t_pfx = m_cbs.group(1)
                r_name = m_cbs.group(2).strip()
                name = f"{t_pfx} {r_name}"
                title = t_pfx
                changed = True

            # Fix pure civic title in name e.g. "นางสาวพูนสิริ ใจลังการ์" -> "พูนสิริ ใจลังการ์"
            m_civic_only = re.match(r"^(นาย|นางสาว|นาง)(.*)", name)
            if m_civic_only and not name.startswith(("อ.", "ผศ.", "รศ.", "ศ.", "ดร.")):
                civic_prefix = m_civic_only.group(1)
                name = m_civic_only.group(2).strip()
                if title == civic_prefix:
                    title = None
                changed = True

            # If title is pure civic title, extract from name or clear
            if title in ["นาย", "นาง", "นางสาว"]:
                m_t = RE_TITLE.match(name)
                title = m_t.group(1).strip() if m_t else None
                changed = True

            # Fix title mismatch if name has clear academic title
            m_name_title = RE_TITLE.match(name)
            if m_name_title:
                expected_title = m_name_title.group(1).strip()
                if not title or title in ["นาย", "นาง", "นางสาว"]:
                    title = expected_title
                    changed = True

            if changed:
                snapshot["modified"].append({
                    "id": f.id,
                    "field": "title_alignment",
                    "old_title": f.academic_title_th,
                    "old_name": f.full_name_th,
                    "new_title": title,
                    "new_name": name
                })
                f.full_name_th = name
                f.academic_title_th = title
                f.embedding_text = build_faculty_embedding_text(f)
                modified_count += 1

        # 4. English Name Hygiene (first_name, last_name)
        for f in faculties:
            first = (f.first_name or "").strip()
            last = (f.last_name or "").strip()
            changed_en = False

            # Check if first_name is purely a title token
            if first.lower() in ["dr.", "dr", "prof.", "prof", "assoc. prof.", "asst. prof.", "mr.", "mr", "mrs.", "mrs", "ms.", "ms"]:
                parts = last.split(maxsplit=1)
                if len(parts) == 2:
                    first = parts[0]
                    last = parts[1]
                    changed_en = True
                elif len(parts) == 1:
                    first = last
                    last = ""
                    changed_en = True
            elif RE_EN_PREFIX.match(first):
                # e.g. "DR.KITTIRAT" or "Dr. Kittirat" -> "KITTIRAT"
                first = RE_EN_PREFIX.sub("", first).strip()
                changed_en = True

            if changed_en:
                snapshot["modified"].append({
                    "id": f.id,
                    "field": "en_name_hygiene",
                    "old_first": f.first_name,
                    "old_last": f.last_name,
                    "new_first": first,
                    "new_last": last
                })
                f.first_name = first
                f.last_name = last
                f.embedding_text = build_faculty_embedding_text(f)
                modified_count += 1

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as out:
            json.dump(snapshot, out, ensure_ascii=False, indent=2)
        print(f"Saved snapshot with {len(snapshot['modified'])} actions to {SNAPSHOT_PATH}")

        db.commit()
        print(f"Phase 1 successfully committed: {modified_count} modifications applied.")

    except Exception as e:
        db.rollback()
        print(f"Error in Phase 1: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_phase1()
