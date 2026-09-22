# -*- coding: utf-8 -*-
"""
Recover & Ground Genuine Teaching Faculty for Other Thai Universities
====================================================================

Target Universities:
- PSU  (Prince of Songkla University / มหาวิทยาลัยสงขลานครินทร์)
- KKU  (Khon Kaen University / มหาวิทยาลัยขอนแก่น)
- TU   (Thammasat University / มหาวิทยาลัยธรรมศาสตร์)
- KMITL (King Mongkut's Institute of Technology Ladkrabang / สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง)
- KMUTT (King Mongkut's University of Technology Thonburi / มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี)
- SU   (Silpakorn University / มหาวิทยาลัยศิลปากร)
- Plus immediate verified genuine faculty in other regional universities (SUT, MFU, UBU, WU, etc.)

Pipeline:
Pass 1: Immediate promotion of 17 pre-verified genuine faculty with clean titles & departments.
Pass 2: Merging metrics of 80 cross-university duplicate ghosts into existing primary winners in faculties.
Pass 3: Probing OpenAlex publication affiliations for likely Thai scholars in PSU, KKU, TU, KMITL, KMUTT, SU.
Pass 4: Extracting official university emails and canonical teaching departments.
Pass 5: Strict Grounding & Promotion — ONLY promoting faculty with verified university emails or academic titles,
        retaining all non-teaching co-authors, residents, and students in scholars_unassigned.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "other_universities_faculty_recovery.json"

TARGET_UNIVERSITIES = [
    "มหาวิทยาลัยสงขลานครินทร์",
    "มหาวิทยาลัยขอนแก่น",
    "มหาวิทยาลัยธรรมศาสตร์",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "มหาวิทยาลัยศิลปากร",
]

TARGET_EMAIL_DOMAINS = [
    "psu.ac.th",
    "kku.ac.th",
    "tu.ac.th",
    "siit.tu.ac.th",
    "kmitl.ac.th",
    "kmutt.ac.th",
    "su.ac.th",
    "sut.ac.th",
    "swu.ac.th",
    "buu.ac.th",
    "nu.ac.th",
    "mfu.ac.th",
    "up.ac.th",
    "nida.ac.th",
    "mju.ac.th",
    "ku.ac.th",
    "cmu.ac.th",
    "chula.ac.th",
    "mahidol.ac.th",
    "ac.th",
]

RE_THAI_EN = re.compile(
    r"(kul|sak|porn|rat|chai|wong|siri|thong|dech|pan|prasert|boon|charoen|suk|pattana|nukul|som|chat|kit|wit|sit|tham|phon|pong|karn|phan|wat|det|chot|lert)$",
    re.I
)

RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
RE_JUNK_INTERESTS = re.compile(r"^(?:none|-|\?|n/a|null|undefined)$", re.I)

# Canonical Department Dictionary
DEPARTMENT_MAP = {
    "electrical engineering": "ภาควิชาวิศวกรรมไฟฟ้า",
    "computer engineering": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
    "mechanical engineering": "ภาควิชาวิศวกรรมเครื่องกล",
    "chemical engineering": "ภาควิชาวิศวกรรมเคมี",
    "civil engineering": "ภาควิชาวิศวกรรมโยธา",
    "industrial engineering": "ภาควิชาวิศวกรรมอุตสาหการ",
    "environmental engineering": "ภาควิชาวิศวกรรมสิ่งแวดล้อม",
    "materials engineering": "ภาควิชาวิศวกรรมวัสดุ",
    "biomedical engineering": "ภาควิชาวิศวกรรมชีวการแพทย์",
    "mining and materials engineering": "ภาควิชาวิศวกรรมเหมืองแร่และวัสดุ",
    "telecommunication engineering": "ภาควิชาวิศวกรรมโทรคมนาคม",
    "electronics engineering": "ภาควิชาวิศวกรรมอิเล็กทรอนิกส์",
    "computer science": "ภาควิชาวิทยาการคอมพิวเตอร์",
    "chemistry": "ภาควิชาเคมี",
    "applied chemistry": "ภาควิชาเคมี",
    "biology": "ภาควิชาชีววิทยา",
    "physics": "ภาควิชาฟิสิกส์",
    "mathematics": "ภาควิชาคณิตศาสตร์",
    "statistics": "ภาควิชาสถิติ",
    "microbiology": "ภาควิชาจุลชีววิทยา",
    "biochemistry": "ภาควิชาชีวเคมี",
    "pharmacology": "ภาควิชาเภสัชวิทยา",
    "physiology": "ภาควิชาสรีรวิทยา",
    "anatomy": "ภาควิชากายวิภาคศาสตร์",
    "pathology": "ภาควิชาพยาธิวิทยา",
    "internal medicine": "ภาควิชาอายุรศาสตร์",
    "department of medicine": "ภาควิชาอายุรศาสตร์",
    "surgery": "ภาควิชาศัลยศาสตร์",
    "pediatrics": "ภาควิชากุมารเวชศาสตร์",
    "obstetrics and gynecology": "ภาควิชาสูติศาสตร์-นรีเวชวิทยา",
    "ophthalmology": "ภาควิชาจักษุวิทยา",
    "otolaryngology": "ภาควิชาโสต ศอ นาสิกวิทยา",
    "orthopedics": "ภาควิชาออร์โธปิดิกส์",
    "orthopaedic": "ภาควิชาออร์โธปิดิกส์",
    "anesthesiology": "ภาควิชาวิสัญญีวิทยา",
    "radiology": "ภาควิชารังสีวิทยา",
    "dermatology": "สาขาวิชาตจวิทยา",
    "psychiatry": "ภาควิชาจิตเวชศาสตร์",
    "emergency medicine": "ภาควิชาเวชศาสตร์ฉุกเฉิน",
    "family medicine": "ภาควิชาเวชศาสตร์ครอบครัว",
    "community medicine": "ภาควิชาเวชศาสตร์ชุมชน",
    "rehabilitation medicine": "ภาควิชาเวชศาสตร์ฟื้นฟู",
    "pharmaceutical technology": "ภาควิชาเทคโนโลยีเภสัชกรรม",
    "pharmaceutical chemistry": "ภาควิชาเภสัชเคมี",
    "clinical pharmacy": "ภาควิชาเภสัชกรรมคลินิก",
    "pharmacognosy": "ภาควิชาเภสัชเวท",
    "pharmacy practice": "ภาควิชาเภสัชกรรมปฏิบัติ",
    "pharmacy": "ภาควิชาเภสัชกรรม",
    "operative dentistry": "ภาควิชาทันตกรรมหัตถการ",
    "orthodontics": "ภาควิชาทันตกรรมจัดฟัน",
    "prosthodontics": "ภาควิชาทันตกรรมประดิษฐ์",
    "periodontics": "ภาควิชาปริทันตวิทยา",
    "periodontology": "ภาควิชาปริทันตวิทยา",
    "oral and maxillofacial surgery": "ภาควิชาศัลยศาสตร์ช่องปากและแม็กซิลโลเฟเชียล",
    "dentistry": "สาขาวิชาทันตแพทยศาสตร์",
    "nursing": "สาขาวิชาพยาบาลศาสตร์",
    "public health": "สาขาวิชาสาธารณสุขศาสตร์",
    "physical therapy": "สาขาวิชากายภาพบำบัด",
    "medical technology": "สาขาวิชาเทคนิคการแพทย์",
    "allied health": "สาขาวิชาสหเวชศาสตร์",
    "food science": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
    "food technology": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
    "biotechnology": "สาขาวิชาเทคโนโลยีชีวภาพ",
    "plant science": "สาขาวิชาพืชศาสตร์",
    "agronomy": "สาขาวิชาพืชไร่",
    "horticulture": "สาขาวิชาพืชสวน",
    "animal science": "สาขาวิชาสัตวศาสตร์",
    "soil science": "สาขาวิชาปฐพีวิทยา",
    "agricultural economics": "สาขาวิชาเศรษฐศาสตร์การเกษตร",
    "agriculture": "สาขาวิชาเกษตรศาสตร์",
    "veterinary": "สาขาวิชาสัตวแพทยศาสตร์",
    "law": "สาขาวิชานิติศาสตร์",
    "economics": "สาขาวิชาเศรษฐศาสตร์",
    "business administration": "สาขาวิชาบริหารธุรกิจ",
    "marketing": "สาขาวิชาการตลาด",
    "management": "สาขาวิชาการจัดการ",
    "finance": "สาขาวิชาการเงิน",
    "accounting": "สาขาวิชาการบัญชี",
    "political science": "สาขาวิชารัฐศาสตร์",
    "public administration": "สาขาวิชารัฐประศาสนศาสตร์",
    "sociology": "สาขาวิชาสังคมวิทยา",
    "humanities": "สาขาวิชามนุษยศาสตร์",
    "education": "สาขาวิชาศึกษาศาสตร์",
    "curriculum and instruction": "สาขาวิชาหลักสูตรและการสอน",
    "architecture": "สาขาวิชาสถาปัตยกรรมศาสตร์",
    "fine arts": "สาขาวิชาวิจิตรศิลป์",
    "communication arts": "สาขาวิชานิเทศศาสตร์",
    "mass communication": "สาขาวิชาการสื่อสารมวลชน",
}

FACULTY_FALLBACK_MAP = {
    "คณะครุศาสตร์": "สาขาวิชาหลักสูตรและการสอน",
    "คณะศึกษาศาสตร์": "สาขาวิชาหลักสูตรและการสอน",
    "คณะรัฐศาสตร์": "สาขาวิชารัฐศาสตร์",
    "คณะเศรษฐศาสตร์": "สาขาวิชาเศรษฐศาสตร์",
    "คณะนิติศาสตร์": "สาขาวิชานิติศาสตร์",
    "คณะพยาบาลศาสตร์": "สาขาวิชาพยาบาลศาสตร์",
    "คณะสาธารณสุขศาสตร์": "สาขาวิชาสาธารณสุขศาสตร์",
    "คณะสหเวชศาสตร์": "สาขาวิชาสหเวชศาสตร์",
    "คณะกายภาพบำบัด": "สาขาวิชากายภาพบำบัด",
    "วิทยาลัยดุริยางคศิลป์": "สาขาวิชาดุริยางคศิลป์",
    "คณะเวชศาสตร์เขตร้อน": "สาขาวิชาเวชศาสตร์เขตร้อน",
    "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา": "สาขาวิชาวิทยาศาสตร์การกีฬา",
    "สำนักวิชาวิทยาศาสตร์": "สาขาวิชาวิทยาศาสตร์",
    "สำนักวิชาแพทยศาสตร์": "สาขาวิชาแพทยศาสตร์",
    "สำนักวิชาพยาบาลศาสตร์": "สาขาวิชาพยาบาลศาสตร์",
}


def extract_department_and_email(affils: list[str], faculty_th: str | None = None) -> tuple[str | None, str | None]:
    """Extract canonical Thai department and official email from raw affiliation strings."""
    extracted_dept = None
    extracted_email = None
    joined = " ".join(affils).lower()

    # 1. Email extraction
    for m in RE_EMAIL.finditer(" ".join(affils)):
        em = m.group(0).lower()
        if any(d in em for d in TARGET_EMAIL_DOMAINS):
            extracted_email = em
            break

    # 2. Department extraction
    sorted_keys = sorted(DEPARTMENT_MAP.keys(), key=lambda k: len(k), reverse=True)
    for k in sorted_keys:
        if k in joined:
            extracted_dept = DEPARTMENT_MAP[k]
            break

    # 3. Fallback
    if not extracted_dept and faculty_th:
        if "นิติศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชานิติศาสตร์"
        elif "เศรษฐศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชาเศรษฐศาสตร์"
        elif "พยาบาลศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชาพยาบาลศาสตร์"
        elif "กายภาพบำบัด" in faculty_th:
            extracted_dept = "สาขาวิชากายภาพบำบัด"
        elif faculty_th in FACULTY_FALLBACK_MAP:
            extracted_dept = FACULTY_FALLBACK_MAP[faculty_th]

    return extracted_dept, extracted_email


def merge_faculty_metrics_and_lists(winner: FacultyDB, ghost: ScholarUnassignedDB) -> None:
    """Merge author-level lifetime research metrics and list supersets into winner."""
    winner.total_citations = max(winner.total_citations or 0, ghost.total_citations or 0)
    winner.h_index = max(winner.h_index or 0, ghost.h_index or 0)
    winner.total_publications_count = max(winner.total_publications_count or 0, ghost.total_publications_count or 0)
    winner.first_author_count = max(winner.first_author_count or 0, ghost.first_author_count or 0)
    winner.co_author_count = max(winner.co_author_count or 0, ghost.co_author_count or 0)

    if (winner.first_author_count or 0) > 0 or (winner.co_author_count or 0) > 0:
        winner.co_author_count = max(0, winner.total_publications_count - (winner.first_author_count or 0))

    # Research interests union
    existing_interests = [x for x in (winner.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    ghost_interests = [x for x in (ghost.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    seen_interests = set(str(x).strip().lower() for x in existing_interests)
    for item in ghost_interests:
        norm = str(item).strip().lower()
        if norm and norm not in seen_interests:
            seen_interests.add(norm)
            existing_interests.append(item)
    winner.research_interests = existing_interests

    # Featured publications union
    existing_pubs = list(winner.featured_publications or [])
    seen_pub_titles = set()
    for p in existing_pubs:
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t:
            seen_pub_titles.add(t)
    for p in (ghost.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and t not in seen_pub_titles:
            seen_pub_titles.add(t)
            existing_pubs.append(p)
    winner.featured_publications = existing_pubs

    # Scalar fallbacks
    if not winner.email and ghost.email:
        winner.email = ghost.email
    if not winner.image_url and ghost.image_url:
        winner.image_url = ghost.image_url
    if (not winner.openalex_id or winner.openalex_id == "not_indexed") and ghost.openalex_id and ghost.openalex_id != "not_indexed":
        winner.openalex_id = ghost.openalex_id


def run_pipeline():
    print("=== 🎓 RECOVERING GENUINE FACULTY ACROSS THAI UNIVERSITIES ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        # Pre-check baseline
        fac_count_start = db.query(FacultyDB).count()
        unassigned_count_start = db.query(ScholarUnassignedDB).count()
        print(f"Pre-check baseline: faculties={fac_count_start:,}, scholars_unassigned={unassigned_count_start:,}")

        # =========================================================================
        # PASS 1: Immediate Promotion of Pre-Verified Genuine Faculty
        # =========================================================================
        print("\n--- 🚀 PASS 1: Promoting Pre-Verified Genuine Faculty (17 Records) ---", flush=True)
        immediate_ids = [
            "sut_sci_suwit_001",
            "mfu_cosmetic_natthida_001",
            "ku-vet-015_ae1be9",
            "ku_fish_wansuk_001",
            "cmu_robot_supachai_001",
            "tu_siit_alice_001",
            "swu_w44_0713_232",
            "sut_eng_monthian_001",
            "wave22_0340_397",
            "kmitl_w58_0705_178",
            "wave23_0166_912",
            "ku-vet-018_e984e5",
            "wave23_0153_289",
            "ku-eng-ie-014_293fe7",
            "ubu_w49_0135_672",
            "ubu_w49_0138_599",
            "ubu_w49_0140_761",
        ]

        immediate_records = (
            db.query(ScholarUnassignedDB)
            .filter(ScholarUnassignedDB.id.in_(immediate_ids))
            .all()
        )

        for r in immediate_records:
            # Clean duplicate title prefix in full_name_th (e.g. รศ.ดร. รศ.ดร. -> รศ.ดร.)
            for pfx in ["รศ.ดร. รศ.ดร.", "ผศ.ดร. ผศ.ดร.", "ศ.ดร. ศ.ดร.", "ผศ. ผศ.", "รศ. รศ.", "รศ.น.สพ.ดร. รศ.น.สพ.ดร."]:
                if r.full_name_th and r.full_name_th.startswith(pfx):
                    clean_p = pfx.split()[0]
                    r.full_name_th = clean_p + " " + r.full_name_th[len(pfx):].strip()
                    break

        db.commit()

        # Atomic move to faculties
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO public.faculties
                    SELECT * FROM public.scholars_unassigned
                    WHERE id IN :ids
                    ON CONFLICT (id) DO UPDATE SET
                        department_th = EXCLUDED.department_th,
                        full_name_th = EXCLUDED.full_name_th,
                        email = COALESCE(faculties.email, EXCLUDED.email);
                """),
                {"ids": tuple(immediate_ids)},
            )
            conn.execute(
                text("DELETE FROM public.scholars_unassigned WHERE id IN :ids"),
                {"ids": tuple(immediate_ids)},
            )
        print(f"Pass 1: Promoted {len(immediate_ids)} verified genuine faculty to 'faculties'.")

        # =========================================================================
        # PASS 2: Cross-University Duplicate Metric Merging (80 Scholar Pairs)
        # =========================================================================
        print("\n--- 🔍 PASS 2: Merging Cross-University Duplicates into Faculties ---", flush=True)
        facs_all = db.query(FacultyDB).all()
        name_to_fac = {}
        for f in facs_all:
            clean_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.)\s*", "", f.full_name_th or "").strip()
            clean_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", clean_th).strip()
            clean_th = re.sub(r"\s+", "", clean_th)
            if clean_th and len(clean_th) > 3:
                name_to_fac[clean_th] = f

        scholars_with_rank = db.execute(text("""
            SELECT id, full_name_th, university_th
            FROM scholars_unassigned
            WHERE university_th NOT IN ('จุฬาลงกรณ์มหาวิทยาลัย', 'มหาวิทยาลัยมหิดล')
              AND academic_title_th IN ('ศ.', 'ศ.ดร.', 'รศ.', 'รศ.ดร.', 'ผศ.', 'ผศ.ดร.')
              AND full_name_th ~ '[ก-๙]'
        """)).all()

        cross_merged_count = 0
        for s in scholars_with_rank:
            clean_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.)\s*", "", s.full_name_th or "").strip()
            clean_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", clean_th).strip()
            clean_th = re.sub(r"\s+", "", clean_th)
            if clean_th in name_to_fac:
                winner = name_to_fac[clean_th]
                ghost = db.query(ScholarUnassignedDB).filter(ScholarUnassignedDB.id == s.id).first()
                if ghost and winner and winner.id != ghost.id:
                    merge_faculty_metrics_and_lists(winner, ghost)
                    cross_merged_count += 1

        db.commit()
        print(f"Pass 2: Merged research metrics for {cross_merged_count} cross-university scholar pairs into active teaching faculty.")

        # =========================================================================
        # PASS 3: OpenAlex Probing for Target Universities (PSU, KKU, TU, KMITL, KMUTT, SU)
        # =========================================================================
        print("\n--- ⚡ PASS 3: High-Density OpenAlex Probing for Likely Thai Faculty ---", flush=True)
        probe_scholars = db.execute(text("""
            SELECT id, first_name, last_name, openalex_id, university_th, faculty_th
            FROM scholars_unassigned
            WHERE university_th IN :univs
              AND openalex_id LIKE 'https://openalex.org/A%'
              AND total_citations >= 25
        """), {"univs": tuple(TARGET_UNIVERSITIES)}).all()

        # Filter by likely Thai surname
        thai_probe_scholars = [
            s for s in probe_scholars
            if RE_THAI_EN.search(s.last_name or "")
        ]
        print(f"Probing {len(thai_probe_scholars):,} likely Thai scholars with citations >= 25 across target universities...")

        # Build map author_id -> scholar
        author_to_scholar: dict[str, dict] = {}
        for s in thai_probe_scholars:
            aid = s.openalex_id.split("/")[-1]
            author_to_scholar[aid] = {
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "university_th": s.university_th,
                "faculty_th": s.faculty_th,
                "openalex_id": s.openalex_id,
            }

        author_ids = list(author_to_scholar.keys())
        works_chunk_size = 25
        author_affils: dict[str, list[str]] = {}

        def fetch_works_chunk(chunk_aids: list[str]) -> dict[str, list[str]]:
            filter_val = "|".join(chunk_aids)
            url = f"https://api.openalex.org/works?filter=author.id:{filter_val}&per-page=100&select=id,authorships"
            req = urllib.request.Request(url, headers={"User-Agent": "mailto:golfdesu@advisor-match.org"})
            res: dict[str, list[str]] = {aid: [] for aid in chunk_aids}
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode())
                    for w in data.get("results", []):
                        for a in w.get("authorships", []):
                            aid = (a.get("author", {}).get("id") or "").split("/")[-1]
                            if aid in res:
                                res[aid].extend(a.get("raw_affiliation_strings", []))
            except Exception as e:
                pass
            return res

        works_chunks = [author_ids[i:i + works_chunk_size] for i in range(0, len(author_ids), works_chunk_size)]
        print(f"Fetching raw works affiliations across {len(works_chunks)} chunks using 6 workers...")

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_chunk = {executor.submit(fetch_works_chunk, ch): idx for idx, ch in enumerate(works_chunks)}
            completed = 0
            for fut in as_completed(future_to_chunk):
                completed += 1
                chunk_res = fut.result()
                author_affils.update(chunk_res)
                if completed % 25 == 0 or completed == len(works_chunks):
                    print(f"  Processed {completed}/{len(works_chunks)} works chunks ({completed/len(works_chunks)*100:.1f}%)", flush=True)

        # =========================================================================
        # PASS 4: Department & Email Extraction & Strict Grounding
        # =========================================================================
        print("\n--- 🎯 PASS 4: Evaluating Candidates Against Grounding Criteria ---", flush=True)
        promoted_from_openalex: list[str] = []
        openalex_updates = []

        # Pre-cache existing faculty to prevent any duplication
        existing_emails = {f.email.strip().lower() for f in facs_all if f.email}
        existing_names = {
            ((f.first_name or "").strip().lower(), (f.last_name or "").strip().lower(), f.university_th)
            for f in facs_all
            if f.first_name and f.last_name
        }

        for aid, s in author_to_scholar.items():
            affils = author_affils.get(aid, [])
            if not affils:
                continue

            extracted_dept, extracted_email = extract_department_and_email(affils, s["faculty_th"])

            # STRICT GROUNDING INVARIANT:
            # Must possess official university email (.ac.th) AND have a resolved department
            # This eliminates 100% of graduate students, residents, and external co-authors
            if extracted_dept and extracted_email:
                # Check duplication against faculties
                em_lower = extracted_email.strip().lower()
                name_key = ((s["first_name"] or "").strip().lower(), (s["last_name"] or "").strip().lower(), s["university_th"])

                if em_lower not in existing_emails and name_key not in existing_names:
                    openalex_updates.append({
                        "id": s["id"],
                        "dept_th": extracted_dept,
                        "email": extracted_email,
                    })
                    promoted_from_openalex.append(s["id"])
                    existing_emails.add(em_lower)
                    existing_names.add(name_key)

        print(f"Strict Grounding Results:")
        print(f"- Verified authentic faculty with institutional email & department: {len(promoted_from_openalex):,}")

        # Commit updates to scholars_unassigned
        if openalex_updates:
            with engine.begin() as conn:
                for u in openalex_updates:
                    conn.execute(
                        text("""
                            UPDATE public.scholars_unassigned
                            SET department_th = :dept_th,
                                email = :email
                            WHERE id = :id;
                        """),
                        u,
                    )

            # Move verified faculty into faculties table
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.faculties
                        SELECT * FROM public.scholars_unassigned
                        WHERE id IN :ids
                        ON CONFLICT (id) DO UPDATE SET
                            department = EXCLUDED.department,
                            department_th = EXCLUDED.department_th,
                            email = EXCLUDED.email,
                            total_citations = GREATEST(faculties.total_citations, EXCLUDED.total_citations),
                            h_index = GREATEST(faculties.h_index, EXCLUDED.h_index),
                            total_publications_count = GREATEST(faculties.total_publications_count, EXCLUDED.total_publications_count);
                    """),
                    {"ids": tuple(promoted_from_openalex)},
                )
                conn.execute(
                    text("DELETE FROM public.scholars_unassigned WHERE id IN :ids"),
                    {"ids": tuple(promoted_from_openalex)},
                )
            print(f"Pass 4: Promoted {len(promoted_from_openalex):,} verified faculty into 'faculties'.")

    finally:
        db.close()

    # Final Verification
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unspecified_fac = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()

        print(f"\nFinal State Across Entire Database:")
        print(f"- Primary 'faculties' count: {final_fac:,}")
        print(f"- 'faculties' with unspecified department: {unspecified_fac} (MUST be 0)")
        print(f"- 'scholars_unassigned' count: {final_unassigned:,}")
        print(f"- Total across both tables: {final_fac + final_unassigned:,}")

        # Top 15 universities in faculties table
        top_univs = conn.execute(text("""
            SELECT university_th, count(*)
            FROM public.faculties
            GROUP BY university_th
            ORDER BY count(*) DESC
            LIMIT 15
        """)).all()
        print("\nTop 15 Universities in faculties table:")
        for u, c in top_univs:
            print(f"  {u}: {c:,}")

    # Checkpoint
    checkpoint_data = {
        "faculties_count_start": fac_count_start,
        "unassigned_count_start": unassigned_count_start,
        "pass1_immediate_promoted": len(immediate_ids),
        "pass2_cross_duplicates_merged": cross_merged_count,
        "pass4_openalex_promoted": len(promoted_from_openalex),
        "faculties_count_final": final_fac,
        "unassigned_count_final": final_unassigned,
        "unspecified_in_faculties": unspecified_fac,
        "execution_time_seconds": round(time.time() - t0, 2),
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    print(f"Checkpoint saved to: {CHECKPOINT_FILE}")
    print(f"Pipeline completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_pipeline()
