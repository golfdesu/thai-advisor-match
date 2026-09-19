# -*- coding: utf-8 -*-
"""
Database Hygiene & Deduplication Pipeline (2026-09-13)

Performs comprehensive data cleaning and deduplication on local PostgreSQL:
1. Deletes confirmed non-person records (webpage navigation dumps, placeholders, support staff).
2. Cleans corruptions in full_name_th (glued positions, revision suffixes, emails, center affiliations).
3. Repairs malformed emails (strips glued non-ASCII prefixes and zero-width spaces).
4. Merges and deduplicates same-university faculty duplicates while preserving research metrics.
5. Updates any research lab foreign key references (lead_advisor_id, member_faculty_ids).
6. Deduplicates redundant course record in Mahasarakham University.
7. Sanitizes phone numbers from embedding_text for PDPA compliance.

Usage:
    python backend/scripts/audits/clean_and_deduplicate_database_2026_09_13.py            # Dry-run
    python backend/scripts/audits/clean_and_deduplicate_database_2026_09_13.py --apply    # Commit to DB
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Adjust pythonpath to find backend app
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.core.university_canonicalizer import canonicalize_university_th, get_university_dedup_key
from app.models.db_models import CourseDB, FacultyDB, ResearchLabDB
from app.models.schema import _strip_leading_title_tokens
from sqlalchemy import text


def deduplicate_list(items: list | None) -> list:
    """Deduplicate a list of primitives or dicts while preserving order."""
    if not items:
        return []
    seen = set()
    res = []
    for x in items:
        if isinstance(x, dict):
            key = json.dumps(x, sort_keys=True, ensure_ascii=False)
        else:
            key = str(x).strip()
        if key and key not in seen:
            seen.add(key)
            res.append(x)
    return res


# 1. Definite Non-Person IDs to delete
NON_PERSON_IDS = [
    # KU Veterinary "อ. สถานที่ติดต่อ"
    "ku_forest_wave15_0007", "ku_forest_wave15_0015", "ku_forest_wave15_0020",
    "ku_forest_wave15_0031", "ku_forest_wave15_0033", "ku_forest_wave15_0040",
    "ku_forest_wave15_0041", "ku_forest_wave15_0054", "ku_forest_wave15_0066",
    "ku_forest_wave15_0079",
    # KMUTT menu dump & board header
    "kmutt_2c9f4a65_6458", "kmutt_a93ad2fa_2676",
    # KU Science page headers & placeholders
    "ku_4afb3b7f_2108", "ku_sci_wave13_0031", "ku_sci_wave13_0074",
    "ku_sci_wave13_0058", "ku_sci_wave13_b_0032", "ku_sci_wave13_b_0035",
    # CMU placeholder
    "cmu_40c290eb_7426",
    # KKU Agriculture support staff (not academic faculty/advisors)
    "kku_agri_wave14_b_0090", "kku_agri_wave14_b_0091",
    "kku_agri_wave14_b_0092", "kku_agri_wave14_b_0093",
    # CMU multi-doctor composite artifact (individual records exist)
    "cmu_5b09d356_4228",
]

SHARED_DEPARTMENTAL_EMAILS = {
    "sci@ku.ac.th", "dent@cmu.ac.th", "agr@ku.ac.th", "med@cmu.ac.th", "surgery@cmu.ac.th",
    "eng@kku.ac.th", "science@kku.ac.th", "sc@mahidol.ac.th", "eng@cmu.ac.th", "cpe@cmu.ac.th",
    "ee@eng.chula.ac.th", "civil@eng.chula.ac.th", "chem@eng.ku.ac.th", "pediatr@cmu.ac.th",
    "ortho@cmu.ac.th", "ent@cmu.ac.th", "ophth@cmu.ac.th", "obgyn@cmu.ac.th", "psychiat@cmu.ac.th",
    "radiology@cmu.ac.th", "anesthes@cmu.ac.th", "rehab@cmu.ac.th", "forensic@cmu.ac.th",
    "family@cmu.ac.th", "community@cmu.ac.th", "patho@cmu.ac.th", "micro@cmu.ac.th",
    "pharmacol@cmu.ac.th", "physiol@cmu.ac.th", "biochem@cmu.ac.th", "anatomy@cmu.ac.th",
    "parasit@cmu.ac.th", "dental@kku.ac.th", "vet@cmu.ac.th", "nurse@cmu.ac.th", "pharmacy@cmu.ac.th",
    "math@cmu.ac.th", "attm@med.tu.ac.th", "anatomy.med@g.swu.ac.th", "forensic.med@g.swu.ac.th",
    "medicine.med@g.swu.ac.th", "webadmin@sit.kmutt.ac.th", "allied@allied.tu.ac.th",
}


def is_pure_thai(s: str | None) -> bool:
    """Return True if string contains meaningful Thai text and no Latin, Arabic, or Greek characters."""
    if not s:
        return False
    has_th = bool(re.search(r"[ก-๙]{3,}", s))
    has_foreign = bool(re.search(r"[a-zA-Z؀-ۿͰ-Ͽ]", s))
    return has_th and not has_foreign


def is_shared_email(em: str | None) -> bool:
    """Check if email is a shared institutional/departmental contact rather than personal."""
    if not em:
        return False
    em_lower = em.lower().strip()
    if em_lower in SHARED_DEPARTMENTAL_EMAILS:
        return True
    return em_lower.startswith(("sci@", "dent@", "civil@", "chem@", "eng@", "med@", "surgery@", "agr@", "nurse@", "vet@"))


def clean_name_noise(name: str | None) -> str:
    """Clean known boilerplate suffixes, numbers, dates, and glued text from full_name_th."""
    if not name:
        return ""
    s = name.strip()

    # Strip revision markers & dates
    s = re.sub(r"NEW2$", "", s).strip()
    s = re.sub(r"\s*27\.02\.68\s*$", "", s).strip()
    s = re.sub(r"\s*\(2\)\s*$", "", s).strip()
    # Strip trailing single digit 2 at end of name (e.g. 'ผศ.ดร. กัญญาณัฐ เปี่ยมงาม2')
    s = re.sub(r"([ก-๙a-zA-Z])\s*2$", r"\1", s).strip()

    # Strip English names in parentheses at the end of Thai names (e.g. '(Tuwanut)', '(Prof. Dr. Ian Fenwick)')
    s = re.sub(r"\s*\([A-Za-z\s.,'\-]+\)\s*$", "", s).strip()

    # Strip glued center affiliations
    s = re.sub(r"สังกัดศูนย์ศรีพัฒน์.*$", "", s).strip()
    s = re.sub(r"สังกัดศูนย์ความเป็นเลิศทางการแพทย์.*$", "", s).strip()
    s = re.sub(r"หัวหน้าศูนย์วิจัยนิวเคลียร์เทคโนโลยี.*$", "", s).strip()

    # Strip glued head of department in title (CU Pharmacy)
    s = re.sub(r"\(หัวหน้าภาควิชา\)\s*", "", s).strip()
    s = re.sub(r"\(หัวหน้าภาค\)\s*", "", s).strip()

    # Strip CMU Math / Surgery boilerplate & glued academic titles
    s = re.sub(r"Email\s*:\s*ข้อมูลเพิ่มเติม.*$", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"ข้อมูลเพิ่มเติม.*$", "", s).strip()
    s = re.sub(r"\(อาจารย์พิเศษ\).*$", "", s).strip()
    s = re.sub(r"หัวหน้าหน่วย.*$", "", s).strip()
    s = re.sub(r"หัวหน้าภาควิชา.*$", "", s).strip()
    s = re.sub(r"อาจารย์ภาควิชา.*$", "", s).strip()
    s = re.sub(r"กรรมการสภามหาวิทยาลัย.*$", "", s).strip()
    s = re.sub(r"ผู้ช่วยอธิการบดี.*$", "", s).strip()

    # Strip targeted English academic title prefix glued directly to Thai name
    # (e.g. 'รศ. นพ.สมเจริญ แซ่เต็งAssoc.Prof.Somcharoen Saeteng, MD.')
    title_pattern = r"(?:Assoc\.?\s*Prof|Assist\.?\s*Prof|Asst\.?\s*Prof|Prof\.|Dr\.|Email\s*:|CV|M\.D\.|MD\b)"
    m_title = re.search(title_pattern, s, re.IGNORECASE)
    if m_title:
        prefix = s[:m_title.start()].strip()
        if re.search(r"[ก-๙]{3,}", prefix):
            s = prefix

    # Strip KKU Agriculture boilerplate
    s = re.sub(r"(?:รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)[\s​﻿]*Email\s*:.*$", "", s, flags=re.IGNORECASE).strip()

    # Strip glued email and CV text
    s = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?:CV.*)?$", "", s).strip()
    s = re.sub(r"CVข้อมูลเพิ่มเติม.*$", "", s).strip()

    # Clean trailing dangling punctuation
    s = re.sub(r"[\s\(\[\{\-–]+$", "", s).strip()

    return s


def clean_email_str(email: str | None) -> str | None:
    """Extract valid email address, stripping non-ASCII prefixes and zero-width spaces."""
    if not email:
        return None
    # Remove zero-width spaces
    clean = re.sub(r"[​‌‍﻿]", "", email).strip()
    # Search for standard email pattern
    m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", clean)
    if m:
        return m.group(1).lower()
    return None


def run_pipeline(apply: bool = False):
    print(f"=== 🧹 DATABASE HYGIENE & DEDUPLICATION PIPELINE (Apply={apply}) ===")
    db = SessionLocal()
    audit_report = {
        "apply": apply,
        "deleted_non_person_count": 0,
        "deleted_non_person_ids": [],
        "cleaned_names_count": 0,
        "cleaned_names": [],
        "cleaned_emails_count": 0,
        "cleaned_emails": [],
        "cleaned_cmu_researchers_count": 0,
        "cleaned_cmu_researchers": [],
        "merged_faculty_groups_count": 0,
        "merged_faculty_donor_ids": [],
        "updated_lab_references_count": 0,
        "deduplicated_courses_count": 0,
        "sanitized_phone_embeddings_count": 0,
    }

    try:
        # ==========================================
        # PART 1: DELETE NON-PERSON RECORDS
        # ==========================================
        print("\n--- Part 1: Purging Non-Person & Structural Records ---")
        existing_non_person = db.query(FacultyDB).filter(FacultyDB.id.in_(NON_PERSON_IDS)).all()
        for rec in existing_non_person:
            print(f"  Deleting non-person record: [{rec.id}] {rec.full_name_th}")
            audit_report["deleted_non_person_ids"].append(rec.id)
            if apply:
                db.delete(rec)
        audit_report["deleted_non_person_count"] = len(existing_non_person)
        if apply:
            db.flush()
        print(f"Purged {len(existing_non_person)} non-person records.")

        # ==========================================
        # PART 2: DATA CLEANING & REPAIR
        # ==========================================
        print("\n--- Part 2: Cleaning Corrupted Names, Positions, & Emails ---")

        # 2.1 Specific row repairs
        # Chula Biology composite string: cu_sci_wave14_b_0160 -> ผศ. สพ.ญ.ดร. วัชราภรณ์ ติยะสัตย์กุลโกวิท
        rec_cu_sci = db.query(FacultyDB).filter(FacultyDB.id == "cu_sci_wave14_b_0160").first()
        if rec_cu_sci:
            old_val = rec_cu_sci.full_name_th
            rec_cu_sci.full_name_th = "ผศ. สพ.ญ.ดร. วัชราภรณ์ ติยะสัตย์กุลโกวิท"
            rec_cu_sci.first_name = "Watcharaporn"
            rec_cu_sci.last_name = "Tiyasatkulkovit"
            audit_report["cleaned_names"].append({"id": rec_cu_sci.id, "old": old_val, "new": rec_cu_sci.full_name_th})
            audit_report["cleaned_names_count"] += 1

        # Chula Pharmacy department fixes for heads of department
        cu_pharm_depts = {
            "cu_pharm_wave16_0017": "ภาควิชาเภสัชเวทและเภสัชพฤกษศาสตร์",
            "cu_pharm_wave16_0021": "ภาควิชาชีวเคมีและจุลชีววิทยา",
            "cu_pharm_wave16_0023": "ภาควิชาเภสัชกรรมปฏิบัติ",
            "cu_pharm_wave16_0055": "ภาควิชาชีวเคมีและจุลชีววิทยา",
            "cu_pharm_wave16_0066": "ภาควิชาสรีรวิทยา",
            "cu_pharm_wave16_0086": "ภาควิชาเภสัชกรรมปฏิบัติ",
        }
        for fid, dept in cu_pharm_depts.items():
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.department_th = dept
                r.full_name_th = clean_name_noise(r.full_name_th)

        # MFU foreign names with email username in name fields
        rec_mfu_1 = db.query(FacultyDB).filter(FacultyDB.id == "mfu_shanmugamnandagopalanmfu__6638").first()
        if rec_mfu_1:
            rec_mfu_1.first_name = "Shanmugam"
            rec_mfu_1.last_name = "Nandagopalan"
            rec_mfu_1.full_name_th = "ศ. Shanmugam Nandagopalan, Ph.D."
        rec_mfu_2 = db.query(FacultyDB).filter(FacultyDB.id == "mfu_nanghsumonpyaemfu__9408").first()
        if rec_mfu_2:
            rec_mfu_2.first_name = "Nang Hsu"
            rec_mfu_2.last_name = "Mon Pyae"
            rec_mfu_2.full_name_th = "อ. Nang Hsu Mon Pyae, Ph.D."

        # Explicit name fixes for ligature/OCR issues and split surnames
        explicit_name_fixes = {
            "mu_cmmu_012": ("ผศ.ดร. บุญยิ่ง คงอาชาภัทร", "Boonying", "Kongarchapatara"),
            "mu_cmmu_019": ("รศ.ดร. สุภารักษ์ สุริยันเกียรติแก้ว", "Suparak", "Suriyankietkaew"),
            "chula_eng_ee_034": ("ดร. อภิวัฒน์ เล็กอุทัย", "Apiwat", "Lek-uthai"),
            "kmutnb_393009e6_2960": ("อ.ดร. มนัสยา ละอองแก้ว", "Manussaya", "La-ongkaew"),
        }
        for fid, (th, fn, ln) in explicit_name_fixes.items():
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                old_th = r.full_name_th
                r.full_name_th = th
                if fn:
                    r.first_name = fn
                if ln:
                    r.last_name = ln
                audit_report["cleaned_names"].append({"id": fid, "old": old_th, "new": th})
                audit_report["cleaned_names_count"] += 1

        # CMU researchers with wrongly assigned Nipon Chat
        cmu_researcher_fixes = {
            "cmu_1bd2c55a_0062": ("รศ.ดร. จิรภาส ศรีเพชรวรรณดี", "jirapas.sripetch@cmu.ac.th"),
            "cmu_302fed10_6692": ("ผศ.ดร. นพ.อภิเศรษฐ ปลื้มสำราญ", "apisate.p@cmu.ac.th"),
            "cmu_3087979c_3291": ("ผศ.ดร. ภูเนตร วีรธีรางกูร", "punate.w@cmu.ac.th"),
            "cmu_43a9df6c_3267": ("อ.ดร. พัชรพงษ์ ปันทิยะ", "patcharapong.pan@cmu.ac.th"),
            "cmu_51fbc97d_9152": ("รศ.ดร. ณัฐยาภรณ์ อภัยใจ", "nattayaporn.a@cmu.ac.th"),
            "cmu_5e50c009_6145": ("รศ.ดร. พญ.ชนิศา โทนุสิน", "chanisa.t@cmu.ac.th"),
            "cmu_656758b8_5946": ("ผศ.ดร. นพ.พงศ์สันติ์ ใยเจริญ", "pongson.y@cmu.ac.th"),
            "cmu_68b73c4d_6438": ("รศ.ดร. วาสนา ปรัชญาสกุล", "wasana.pratcha@cmu.ac.th"),
            "cmu_34324605_6372": ("อ. นพ.ณัฐภัทร ศิริอังกุล", "natthaphat.s@cmu.ac.th"),
            "cmu_195e5c01_5932": ("อ. นพ.ปวีร์ ชลิดาพงศ์", "pawee.c@cmu.ac.th"),
            "cmu_22b3f0d0_4522": ("อ. นพ.รนกฤต เมธังกูร", "ronnakrit.m@cmu.ac.th"),
            "cmu_5c148fe3_1380": ("อ. นพ.ธีร์ธัช โตสุโขวงศ์", "theetouch.t@cmu.ac.th"),
            "cmu_616d74e8_0135": ("อ. พญ.นฤภร ปาโกวงศ์", "narueporn.p@cmu.ac.th"),
        }
        for fid, (th_name, real_email) in cmu_researcher_fixes.items():
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.full_name_th = th_name
                r.email = real_email
                if r.first_name == "Nipon" and r.last_name == "Chat":
                    r.first_name = ""
                    r.last_name = ""
                audit_report["cleaned_cmu_researchers"].append({"id": fid, "name": th_name, "email": real_email})
        audit_report["cleaned_cmu_researchers_count"] = len(cmu_researcher_fixes)

        # General loop over all faculties to clean name noise and malformed emails
        all_faculties = db.query(FacultyDB).all()
        for f in all_faculties:
            # Clean email
            if f.email:
                cleaned_em = clean_email_str(f.email)
                if cleaned_em != f.email:
                    audit_report["cleaned_emails"].append({"id": f.id, "old": f.email, "new": cleaned_em})
                    f.email = cleaned_em
                    audit_report["cleaned_emails_count"] += 1

            # Clean full_name_th noise
            if f.full_name_th:
                cleaned_th = clean_name_noise(f.full_name_th)
                if cleaned_th != f.full_name_th:
                    audit_report["cleaned_names"].append({"id": f.id, "old": f.full_name_th, "new": cleaned_th})
                    f.full_name_th = cleaned_th
                    audit_report["cleaned_names_count"] += 1

            # Sanitize office phone numbers from embedding_text (+66 ...)
            if f.embedding_text and "+66" in f.embedding_text:
                f.embedding_text = re.sub(r"\+66[\d\s\-]{8,15}", "", f.embedding_text).strip()
                audit_report["sanitized_phone_embeddings_count"] += 1

        if apply:
            db.flush()
        print(f"Cleaned {audit_report['cleaned_names_count']} names, {audit_report['cleaned_emails_count']} emails, and sanitized {audit_report['sanitized_phone_embeddings_count']} embeddings.")

        # ==========================================
        # PART 3: DEDUPLICATE SAME-UNIVERSITY FACULTIES
        # ==========================================
        print("\n--- Part 3: Merging & Deduplicating Same-University Faculty Duplicates ---")

        # 3.0 Fix role title in first_name/last_name fields
        role_fixes = {
            "cmu_58ee6d12_3751": ("Kittipan", "Rerkasem"),
            "srinakhari_facultyofe_sompongjaideech_002": ("Sompong", "Jaideechoey"),
            "kku_sci_wave14_b_0134": ("Florian", "Schevenels"),
            "kku_sci_wave14_b_0143": ("Andrew", "Hunt"),
            "kku_sci_wave14_b_0030": ("David", "Nugroho"),
        }
        for fid, (fn, ln) in role_fixes.items():
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.first_name = fn
                r.last_name = ln

        # Load research labs to prepare for foreign key re-pointing
        all_labs = db.query(ResearchLabDB).all()

        donor_to_primary_map: dict[str, str] = {}
        merged_groups = 0

        def score_faculty(f: FacultyDB) -> tuple:
            th_score = 1000 if is_pure_thai(f.full_name_th) else 0
            has_img = 500 if f.image_url else 0
            em = (f.email or "").strip().lower()
            has_em = 300 if (em and "@" in em and not is_shared_email(em)) else 0
            has_en = 100 if (f.first_name and f.first_name.lower() not in ("none", "computer", "")) else 0
            cites = f.total_citations or 0
            pubs = len(f.featured_publications or [])
            interests = len(f.research_interests or [])
            has_oa = 50 if (f.openalex_id and f.openalex_id != "not_indexed") else 0
            return (th_score, has_img, has_em, has_en, cites, pubs, interests, has_oa)

        def merge_donor(primary: FacultyDB, donor: FacultyDB):
            # Prefer pure Thai name on primary
            if not is_pure_thai(primary.full_name_th) and is_pure_thai(donor.full_name_th):
                primary.full_name_th = donor.full_name_th

            # Prefer personal email over shared or empty
            if (not primary.email or is_shared_email(primary.email)) and (donor.email and not is_shared_email(donor.email)):
                primary.email = donor.email
            elif not primary.email and donor.email:
                primary.email = donor.email

            # Image & URLs
            if not primary.image_url and donor.image_url:
                primary.image_url = donor.image_url
            if not primary.profile_url and donor.profile_url:
                primary.profile_url = donor.profile_url
            if not primary.scholar_url and donor.scholar_url:
                primary.scholar_url = donor.scholar_url
            if not primary.department_th and donor.department_th:
                primary.department_th = donor.department_th
            if (not primary.first_name or primary.first_name.lower() in ("none", "computer", "")) and donor.first_name and donor.first_name.lower() not in ("none", "computer", ""):
                primary.first_name = donor.first_name
                primary.last_name = donor.last_name

            # Merge list fields
            primary.featured_publications = deduplicate_list((primary.featured_publications or []) + (donor.featured_publications or []))
            primary.research_interests = deduplicate_list((primary.research_interests or []) + (donor.research_interests or []))
            primary.education = deduplicate_list((primary.education or []) + (donor.education or []))
            primary.taught_courses = deduplicate_list((primary.taught_courses or []) + (donor.taught_courses or []))

            # Preserve maximum authoritative metrics
            primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
            primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
            primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0, len(primary.featured_publications))

            if (not primary.openalex_id or primary.openalex_id == "not_indexed") and donor.openalex_id and donor.openalex_id != "not_indexed":
                primary.openalex_id = donor.openalex_id

            donor_to_primary_map[donor.id] = primary.id
            audit_report["merged_faculty_donor_ids"].append(donor.id)

            if apply:
                db.delete(donor)

        # 3.1 Pass 1: Deduplicate by exact same-university Thai name
        groups_th = defaultdict(list)
        for f in all_faculties:
            if f.id in audit_report["deleted_non_person_ids"] or f.id in donor_to_primary_map:
                continue
            uni_key = get_university_dedup_key(f.university_th or f.university)
            th_norm = _strip_leading_title_tokens((f.full_name_th or "").strip())
            th_clean = "".join(th_norm.split())
            if uni_key and th_clean and len(th_clean) >= 4:
                groups_th[(uni_key, th_clean)].append(f)

        for key, members in groups_th.items():
            active_members = [m for m in members if m.id not in donor_to_primary_map]
            if len(active_members) <= 1:
                continue
            primary = max(active_members, key=score_faculty)
            for donor in active_members:
                if donor.id != primary.id:
                    merge_donor(primary, donor)
            merged_groups += 1

        # 3.2 Pass 2: Deduplicate by exact same-university English first & last name
        groups_en = defaultdict(list)
        for f in all_faculties:
            if f.id in audit_report["deleted_non_person_ids"] or f.id in donor_to_primary_map:
                continue
            uni_key = get_university_dedup_key(f.university_th or f.university)
            en_first = (f.first_name or "").strip().lower()
            en_last = (f.last_name or "").strip().lower()
            if uni_key and en_first and en_last and en_first not in ("none", "computer", "international", "group") and len(en_first) >= 2 and len(en_last) >= 2:
                groups_en[(uni_key, en_first, en_last)].append(f)

        for key, members in groups_en.items():
            active_members = [m for m in members if m.id not in donor_to_primary_map]
            if len(active_members) <= 1:
                continue
            primary = max(active_members, key=score_faculty)
            for donor in active_members:
                if donor.id != primary.id:
                    merge_donor(primary, donor)
            merged_groups += 1

        audit_report["merged_faculty_groups_count"] = merged_groups
        print(f"Merged {len(donor_to_primary_map)} donor records across {merged_groups} duplicate groups.")

        # Re-point research labs references if any pointed to donor IDs
        lab_updates = 0
        for lab in all_labs:
            updated = False
            if lab.lead_advisor_id and lab.lead_advisor_id in donor_to_primary_map:
                new_lead = donor_to_primary_map[lab.lead_advisor_id]
                print(f"  Re-pointing lab [{lab.id}] lead_advisor_id {lab.lead_advisor_id} -> {new_lead}")
                lab.lead_advisor_id = new_lead
                updated = True

            if lab.member_faculty_ids:
                new_members = []
                for m_id in lab.member_faculty_ids:
                    if m_id in donor_to_primary_map:
                        new_members.append(donor_to_primary_map[m_id])
                        updated = True
                    else:
                        new_members.append(m_id)
                if updated:
                    lab.member_faculty_ids = deduplicate_list(new_members)

            if updated:
                lab_updates += 1

        audit_report["updated_lab_references_count"] = lab_updates
        print(f"Updated {lab_updates} research lab references.")

        # ==========================================
        # PART 4: DEDUPLICATE COURSES (MSU)
        # ==========================================
        print("\n--- Part 4: Deduplicating Duplicate Course (MSU) ---")
        c_primary = db.query(CourseDB).filter(CourseDB.id == "msu_inf_it_msc").first()
        c_donor = db.query(CourseDB).filter(CourseDB.id == "msu_it_msc_it").first()
        if c_primary and c_donor:
            print(f"  Merging course [{c_donor.id}] into [{c_primary.id}]")
            c_primary.curriculum_highlights = deduplicate_list((c_primary.curriculum_highlights or []) + (c_donor.curriculum_highlights or []))
            c_primary.career_paths = deduplicate_list((c_primary.career_paths or []) + (c_donor.career_paths or []))
            c_primary.tags = deduplicate_list((c_primary.tags or []) + (c_donor.tags or []))
            if apply:
                db.delete(c_donor)
            audit_report["deduplicated_courses_count"] = 1
            print("  Course deduplicated successfully.")
        else:
            print("  Course duplicate already resolved.")

        # Save checkpoint audit report
        out_path = CURRENT_DIR.parents[1] / "data" / "agent_states" / "db_clean_and_dedup_2026_09_13.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, ensure_ascii=False, indent=2)
        print(f"\nAudit checkpoint saved to: {out_path}")

        if apply:
            db.commit()
            print("\n✅ All changes COMMITTED successfully to PostgreSQL (advisor_match).")
        else:
            db.rollback()
            print("\n🔍 DRY-RUN COMPLETE (No changes committed. Use --apply to execute).")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Pipeline failed with error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and deduplicate local PostgreSQL database.")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()

    run_pipeline(apply=args.apply)
