# -*- coding: utf-8 -*-
"""Comprehensive Fact-Check & Hygiene Audit for All 13,559 Faculty Members.

Audits all faculty records across 7 core dimensions:
1. Non-Person & Structural Placeholder Records
2. Name Formatting, Title Contamination & Glued Text
3. Contact Hygiene & PDPA Phone Leakage
4. University & Affiliation Mapping Consistency
5. OpenAlex Metrics Sanity & Cross-Record Collisions
6. Duplicate Profiles (Thai Name, English Name, Personal Email)
7. Vector & Relational Integrity (Null Embeddings, Research Lab Links)
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from app.core.database import SessionLocal
from app.core.university_canonicalizer import (
    CANONICAL_EN_TO_TH,
    CANONICAL_TH_TO_EN,
    get_university_dedup_key,
)
from app.models.db_models import FacultyDB, ResearchLabDB
from app.models.schema import _strip_leading_title_tokens

RE_PHONE = re.compile(r"(?:\+?66|0)[ -]?[2-9]\d{1,2}[ -]?\d{3}[ -]?\d{3,4}\b")
RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_DATE_OR_REV = re.compile(r"(?:\bNEW\d*\b|\b\d{1,2}\.\d{1,2}\.\d{2,4}\b|\b2\b$)", re.IGNORECASE)
RE_ENGLISH_TITLE_PREFIX = re.compile(
    r"^(?:(?:Assoc\.?|Asst\.?|Assist\.?|Prof\.?)\s*(?:Prof\.?\s*)?(?:Dr\.?\s*)?|Dr\.?|Mrs\.?|Mr\.?|Ms\.?)\s+",
    re.IGNORECASE,
)

NON_PERSON_PATTERNS = [
    "สถานที่ติดต่อ", "ภาควิชา", "สำนักงาน", "ห้องปฏิบัติการ", "กลุ่มวิชา", "ศูนย์วิจัย",
    "เจ้าหน้าที่", "ผู้ประสานงาน", "งานบริการการศึกษา", "ติดต่อเรา", "โทรศัพท์",
    "computer science group", "science group", "academic group", "department staff"
]

SHARED_EMAIL_BLACKLIST = {
    "sci@ku.ac.th", "dent@cmu.ac.th", "civil@eng.chula.ac.th", "surgery@cmu.ac.th",
    "contact@cmu.ac.th", "info@ku.ac.th", "admin@chula.ac.th", "dean@eng.chula.ac.th",
    "water@eng.chula.ac.th", "microbiology.med@g.swu.ac.th", "medicine.med@g.swu.ac.th",
    "commarts@chula.ac.th", "cpe@eng.cmu.ac.th"
}

UNIVERSITY_DOMAIN_MAP = {
    "chula.ac.th": "Chulalongkorn University",
    "ku.ac.th": "Kasetsart University",
    "cmu.ac.th": "Chiang Mai University",
    "mahidol.ac.th": "Mahidol University",
    "kku.ac.th": "Khon Kaen University",
    "tu.ac.th": "Thammasat University",
    "psu.ac.th": "Prince of Songkla University",
    "kmitl.ac.th": "King Mongkut's Institute of Technology Ladkrabang",
    "kmutt.ac.th": "King Mongkut's University of Technology Thonburi",
    "kmutnb.ac.th": "King Mongkut's University of Technology North Bangkok",
    "sut.ac.th": "Suranaree University of Technology",
    "nu.ac.th": "Naresuan University",
    "tsu.ac.th": "Thaksin University",
    "wu.ac.th": "Walailak University",
    "swu.ac.th": "Srinakharinwirot University",
    "su.ac.th": "Silpakorn University",
    "buu.ac.th": "Burapha University",
    "ubu.ac.th": "Ubon Ratchathani University",
    "up.ac.th": "University of Phayao",
    "mju.ac.th": "Maejo University",
    "mfu.ac.th": "Mae Fah Luang University",
    "msu.ac.th": "Mahasarakham University",
    "ru.ac.th": "Ramkhamhaeng University",
    "ssru.ac.th": "Suan Sunandha Rajabhat University",
    "nida.ac.th": "National Institute of Development Administration",
}


def normalize_thai_name_for_dedup(name: str | None) -> str:
    if not name:
        return ""
    clean = _strip_leading_title_tokens(name)
    clean = re.sub(r"\(.*?\)", "", clean)
    clean = re.sub(r"[A-Za-z0-9]", "", clean)
    clean = re.sub(r"\s+", "", clean)
    return clean.strip()


def run_fact_check():
    db = SessionLocal()
    print("=" * 75)
    print("🔍 INITIATING COMPREHENSIVE FACT-CHECK OF ALL 13,559 FACULTIES")
    print("=" * 75)

    try:
        # Load all faculties (defer embedding to avoid memory ballooning)
        faculties = (
            db.query(FacultyDB)
            .options(defer(FacultyDB.embedding))
            .yield_per(1000)
            .all()
        )
        total_count = len(faculties)
        print(f"Loaded {total_count} faculties from database.\n")

        anomalies = {
            "dim1_non_person": [],
            "dim2_name_noise": [],
            "dim2_title_prefix_first_name": [],
            "dim2_glued_name": [],
            "dim3_pdpa_phone": [],
            "dim3_malformed_email": [],
            "dim4_university_mismatch": [],
            "dim4_email_domain_mismatch": [],
            "dim5_duplicate_openalex_id": [],
            "dim5_negative_or_insane_metrics": [],
            "dim6_duplicate_thai_name": [],
            "dim6_duplicate_en_name": [],
            "dim6_duplicate_personal_email": [],
            "dim7_null_embeddings": [],
            "dim7_broken_lab_advisors": [],
        }

        # Trackers for duplicates
        thai_name_map = defaultdict(list)
        en_name_map = defaultdict(list)
        email_map = defaultdict(list)
        openalex_map = defaultdict(list)
        all_ids = set()

        for f in faculties:
            all_ids.add(f.id)
            fid = f.id
            name_th = (f.full_name_th or "").strip()
            first_en = (f.first_name or "").strip()
            last_en = (f.last_name or "").strip()
            email = (f.email or "").strip().lower()
            uni_en = (f.university or "").strip()
            uni_th = (f.university_th or "").strip()
            oaid = (f.openalex_id or "").strip()

            # --- Dimension 1: Non-person / Placeholders ---
            lower_name = name_th.lower()
            lower_first = first_en.lower()
            lower_last = last_en.lower()
            for pat in NON_PERSON_PATTERNS:
                if pat in lower_name or pat in lower_first or pat in lower_last:
                    anomalies["dim1_non_person"].append({
                        "id": fid, "name_th": name_th, "en": f"{first_en} {last_en}", "pattern": pat
                    })
                    break

            if len(name_th) > 0 and len(_strip_leading_title_tokens(name_th)) < 3:
                anomalies["dim1_non_person"].append({
                    "id": fid, "name_th": name_th, "en": f"{first_en} {last_en}", "reason": "bare_title_only"
                })

            # --- Dimension 2: Name noise & formatting ---
            if RE_DATE_OR_REV.search(name_th):
                anomalies["dim2_name_noise"].append({
                    "id": fid, "name_th": name_th, "reason": "date_or_revision_suffix"
                })

            if RE_ENGLISH_TITLE_PREFIX.search(first_en):
                anomalies["dim2_title_prefix_first_name"].append({
                    "id": fid, "first_name": first_en, "last_name": last_en
                })

            # Check glued name (e.g. Thai name glued with English Assoc. Prof.)
            if re.search(r"[฀-๿]+(?:Assoc|Asst|Prof|Dr|Mr|Mrs|Ms)", name_th):
                anomalies["dim2_glued_name"].append({
                    "id": fid, "name_th": name_th, "reason": "glued_thai_english_title"
                })

            # --- Dimension 3: Contact Hygiene & PDPA ---
            # Phone leakage checks
            for field_name, val in [
                ("full_name_th", name_th),
                ("email", email),
                ("education", json.dumps(f.education or [], ensure_ascii=False)),
                ("research_interests", json.dumps(f.research_interests or [], ensure_ascii=False)),
                ("embedding_text", f.embedding_text or "")
            ]:
                if RE_PHONE.search(val):
                    anomalies["dim3_pdpa_phone"].append({
                        "id": fid, "field": field_name, "snippet": val[:100]
                    })

            # Malformed email
            if email:
                if "​" in email or "﻿" in email:
                    anomalies["dim3_malformed_email"].append({"id": fid, "email": email, "reason": "zero_width_space"})
                elif not RE_EMAIL.match(email):
                    anomalies["dim3_malformed_email"].append({"id": fid, "email": email, "reason": "invalid_syntax"})

            # --- Dimension 4: University Consistency ---
            if not uni_en or not uni_th:
                anomalies["dim4_university_mismatch"].append({
                    "id": fid, "university": uni_en, "university_th": uni_th, "reason": "empty_university"
                })
            else:
                expected_th = CANONICAL_EN_TO_TH.get(uni_en)
                if expected_th and expected_th != uni_th:
                    anomalies["dim4_university_mismatch"].append({
                        "id": fid, "university": uni_en, "current_th": uni_th, "expected_th": expected_th
                    })

            # Check email domain mismatch with institution
            if email and "@" in email:
                domain = email.split("@")[-1].strip()
                for dom_suffix, dom_uni in UNIVERSITY_DOMAIN_MAP.items():
                    if domain == dom_suffix or domain.endswith("." + dom_suffix):
                        if uni_en != dom_uni:
                            # Flag conflicting institutional email
                            anomalies["dim4_email_domain_mismatch"].append({
                                "id": fid, "name_th": name_th, "email": email, "db_university": uni_en, "email_university": dom_uni
                            })
                        break

            # --- Dimension 5: OpenAlex Metrics Sanity ---
            if oaid and oaid != "not_indexed":
                openalex_map[oaid].append(fid)

            if (f.h_index is not None and f.h_index < 0) or \
               (f.total_citations is not None and f.total_citations < 0) or \
               (f.total_publications_count is not None and f.total_publications_count < 0):
                anomalies["dim5_negative_or_insane_metrics"].append({
                    "id": fid, "h": f.h_index, "cit": f.total_citations, "works": f.total_publications_count
                })

            # --- Dimension 6: Duplicate Trackers ---
            norm_th = normalize_thai_name_for_dedup(name_th)
            uni_key = get_university_dedup_key(uni_en)
            if norm_th and len(norm_th) >= 4 and uni_key:
                thai_name_map[(uni_key, norm_th)].append(fid)

            if first_en and last_en and len(first_en) >= 2 and len(last_en) >= 2 and uni_key:
                en_name_map[(uni_key, first_en.lower(), last_en.lower())].append(fid)

            if email and email not in SHARED_EMAIL_BLACKLIST and uni_key:
                email_map[(uni_key, email)].append(fid)

            # --- Dimension 7: Null Embedding ---
            if hasattr(f, "embedding") and f.embedding is None:
                anomalies["dim7_null_embeddings"].append(fid)

        # Check OpenAlex Collisions
        for oaid, fids in openalex_map.items():
            if len(fids) > 1:
                anomalies["dim5_duplicate_openalex_id"].append({
                    "openalex_id": oaid, "faculty_ids": fids
                })

        # Check Duplicate Groups
        for (u, nth), fids in thai_name_map.items():
            if len(fids) > 1:
                anomalies["dim6_duplicate_thai_name"].append({"uni": u, "norm_name": nth, "ids": fids})

        for (u, fn, ln), fids in en_name_map.items():
            if len(fids) > 1:
                anomalies["dim6_duplicate_en_name"].append({"uni": u, "first": fn, "last": ln, "ids": fids})

        for (u, em), fids in email_map.items():
            if len(fids) > 1:
                anomalies["dim6_duplicate_personal_email"].append({"uni": u, "email": em, "ids": fids})

        # Check Relational Links with Research Labs
        labs = db.query(ResearchLabDB).all()
        for lab in labs:
            if lab.lead_advisor_id and lab.lead_advisor_id not in all_ids:
                anomalies["dim7_broken_lab_advisors"].append({
                    "lab_id": lab.id, "lab_name": lab.name_th, "broken_advisor_id": lab.lead_advisor_id
                })

        # Summary Report
        print("=" * 75)
        print("📊 FACT-CHECK AUDIT FINDINGS SUMMARY (13,559 FACULTIES)")
        print("=" * 75)
        print(f"1. Non-Person / Placeholder Records     : {len(anomalies['dim1_non_person'])}")
        print(f"2. Name Formatting & Glued Noise        : {len(anomalies['dim2_name_noise']) + len(anomalies['dim2_glued_name'])}")
        print(f"   - Title Prefix in English First Name : {len(anomalies['dim2_title_prefix_first_name'])}")
        print(f"3. PDPA Phone Number Leakage (Zero-P)   : {len(anomalies['dim3_pdpa_phone'])}")
        print(f"   - Malformed / Syntax-Invalid Emails  : {len(anomalies['dim3_malformed_email'])}")
        print(f"4. University Thai/EN Mapping Incomplete : {len(anomalies['dim4_university_mismatch'])}")
        print(f"   - Cross-University Domain Mismatches : {len(anomalies['dim4_email_domain_mismatch'])}")
        print(f"5. Cross-Record OpenAlex ID Collisions  : {len(anomalies['dim5_duplicate_openalex_id'])}")
        print(f"   - Negative / Insane Metrics          : {len(anomalies['dim5_negative_or_insane_metrics'])}")
        print(f"6. Duplicate Groups (Same University)   :")
        print(f"   - Pass 1 (Normalized Thai Name)      : {len(anomalies['dim6_duplicate_thai_name'])} groups")
        print(f"   - Pass 2 (Clean English Name)        : {len(anomalies['dim6_duplicate_en_name'])} groups")
        print(f"   - Pass 3 (Personal Academic Email)   : {len(anomalies['dim6_duplicate_personal_email'])} groups")
        print(f"7. Null Embeddings                      : {len(anomalies['dim7_null_embeddings'])}")
        print(f"   - Broken Research Lab Advisor Links  : {len(anomalies['dim7_broken_lab_advisors'])}")
        print("=" * 75)

        # Write detailed audit log to disk
        out_dir = BACKEND_DIR / "data" / "agent_states"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "fact_check_all_13559_faculties_report.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(anomalies, f, ensure_ascii=False, indent=2)
        print(f"Detailed audit log written to: {out_file}\n")

        return anomalies

    finally:
        db.close()


if __name__ == "__main__":
    run_fact_check()
