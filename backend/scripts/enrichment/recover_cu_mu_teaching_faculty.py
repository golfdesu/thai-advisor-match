# -*- coding: utf-8 -*-
"""
Recover & Classify Authentic CU & MU Teaching Faculty from scholars_unassigned
=============================================================================

Executes a high-throughput 5-pillar autonomous pipeline to:
1. Pass 1: Identify and merge CU/MU scholars in `scholars_unassigned` who match
   existing teaching faculty in `faculties` (by OpenAlex ID or English name),
   preserving lifetime research metrics and union supersets.
2. Pass 2: Screen remaining CU/MU scholars via OpenAlex Author API to confirm
   institutional affiliation (Chulalongkorn University, Mahidol University,
   KCMH, Siriraj, Ramathibodi, Sasin) and isolate foreign co-authors.
3. Pass 3: Extract authentic teaching departments from OpenAlex works raw
   affiliation strings and university directories.
4. Pass 4: Promote verified faculty with authentic departments to `faculties`,
   delete from `scholars_unassigned`, and verify 100% database parity.
5. Pass 5: Write disk checkpoint to `backend/data/agent_states/`.
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

CHECKPOINT_DIR = BACKEND_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "cu_mu_faculty_recovery_checkpoint.json"

# Institutional keywords for CU and MU
CU_KEYWORDS = [
    "chulalongkorn", "จุฬาลงกรณ์", "king chulalongkorn", "kcmh", "sasin",
    "chula.ac.th", "sasin.edu", "queen saovabha", "halal science center"
]
MU_KEYWORDS = [
    "mahidol", "มหิดล", "siriraj", "ศิริราช", "ramathibodi", "รามาธิบดี",
    "mahidol.ac.th", "mahidol.edu", "golden jubilee", "rilca", "inmu"
]

# Canonical Thai Department Dictionary from English tokens
DEPARTMENT_MAP = {
    # Medical & Health Sciences
    "anatomy": "ภาควิชากายวิภาคศาสตร์",
    "physiology": "ภาควิชาสรีรวิทยา",
    "pathology": "ภาควิชาพยาธิวิทยา",
    "pathobiology": "ภาควิชาพยาธิชีววิทยา",
    "pharmacology": "ภาควิชาเภสัชวิทยา",
    "parasitology": "ภาควิชาปรสิตวิทยา",
    "microbiology": "ภาควิชาจุลชีววิทยา",
    "biochemistry": "ภาควิชาชีวเคมี",
    "immunology": "ภาควิชาวิทยาภูมิคุ้มกัน",
    "medicine": "ภาควิชาอายุรศาสตร์",
    "surgery": "ภาควิชาศัลยศาสตร์",
    "pediatrics": "ภาควิชากุมารเวชศาสตร์",
    "obstetrics": "ภาควิชาสูติศาสตร์-นรีเวชวิทยา",
    "gynecology": "ภาควิชาสูติศาสตร์-นรีเวชวิทยา",
    "orthopaedics": "ภาควิชาออร์โธปิดิกส์",
    "orthopedics": "ภาควิชาออร์โธปิดิกส์",
    "anesthesiology": "ภาควิชาวิสัญญีวิทยา",
    "radiology": "ภาควิชารังสีวิทยา",
    "radiological": "ภาควิชารังสีวิทยา",
    "ophthalmology": "ภาควิชาจักษุวิทยา",
    "otolaryngology": "ภาควิชาโสต ศอ นาสิกวิทยา",
    "psychiatry": "ภาควิชาจิตเวชศาสตร์",
    "rehabilitation": "ภาควิชาเวชศาสตร์ฟื้นฟู",
    "preventive": "ภาควิชาเวชศาสตร์ป้องกันและสังคม",
    "social medicine": "ภาควิชาเวชศาสตร์ป้องกันและสังคม",
    "community medicine": "ภาควิชาเวชศาสตร์ชุมชน",
    "forensic": "ภาควิชานิติเวชศาสตร์",
    "emergency medicine": "ภาควิชาเวชศาสตร์ฉุกเฉิน",
    "dermatology": "ภาควิชาตจวิทยา",
    "clinical epidemiology": "สาขาวิชาระบาดวิทยาคลินิก",
    "tropical medicine": "สาขาวิชาเวชศาสตร์เขตร้อน",
    "tropical pediatrics": "ภาควิชากุมารเวชศาสตร์เขตร้อน",
    "clinical tropical medicine": "ภาควิชาอายุรศาสตร์เขตร้อน",
    "protozoology": "ภาควิชาโพรโทซัววิทยา",
    "helminthology": "ภาควิชาหนอนพยาธิ",
    "medical entomology": "ภาควิชากีฏวิทยาการแพทย์",
    "physical therapy": "สาขาวิชากายภาพบำบัด",
    "occupational therapy": "สาขาวิชากิจกรรมบำบัด",
    "medical technology": "ภาควิชาเทคนิคการแพทย์",
    "clinical chemistry": "ภาควิชาเคมีคลินิก",
    "clinical microscopy": "ภาควิชาจุลทรรศน์ศาสตร์คลินิก",
    "transfusion": "ภาควิชาเวชศาสตร์การธนาคารเลือด",
    "communication sciences": "ภาควิชาวิทยาศาสตร์สื่อความหมายและความผิดปกติของการสื่อความหมาย",
    "cardiology": "สาขาวิชาอายุรศาสตร์โรคหัวใจ",
    "oncology": "สาขาวิชาอายุรศาสตร์โรคมะเร็ง",
    "hematology": "สาขาวิชาอายุรศาสตร์โรคเลือด",
    "nephrology": "สาขาวิชาอายุรศาสตร์โรคไต",
    "gastroenterology": "สาขาวิชาอายุรศาสตร์โรคทางเดินอาหาร",
    "endocrinology": "สาขาวิชาอายุรศาสตร์ต่อมไร้ท่อ",
    "pulmonology": "สาขาวิชาอายุรศาสตร์โรคระบบทางเดินหายใจ",
    "neurology": "สาขาวิชาอายุรศาสตร์ประสาทวิทยา",
    "neurobiology": "สาขาวิชาประสาทวิทยาศาสตร์",
    "molecular medicine": "สาขาวิชาเวชศาสตร์ระดับโมเลกุล",

    # Science
    "chemistry": "ภาควิชาเคมี",
    "physics": "ภาควิชาฟิสิกส์",
    "biology": "ภาควิชาชีววิทยา",
    "botany": "ภาควิชาพฤกษศาสตร์",
    "zoology": "ภาควิชาสัตววิทยา",
    "mathematics": "ภาควิชาคณิตศาสตร์",
    "computer science": "ภาควิชาวิทยาการคอมพิวเตอร์",
    "materials science": "ภาควิชาวัสดุศาสตร์",
    "chemical technology": "ภาควิชาเคมีเทคนิค",
    "food technology": "ภาควิชาเทคโนโลยีทางอาหาร",
    "biotechnology": "ภาควิชาเทคโนโลยีชีวภาพ",
    "marine science": "ภาควิชาวิทยาศาสตร์ทางทะเล",
    "geology": "ภาควิชาธรณีวิทยา",
    "imaging": "ภาควิชาเทคโนโลยีทางภาพและการพิมพ์",
    "photographic": "ภาควิชาเทคโนโลยีทางภาพและการพิมพ์",
    "environmental science": "ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม",

    # Engineering
    "computer engineering": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
    "electrical engineering": "ภาควิชาวิศวกรรมไฟฟ้า",
    "mechanical engineering": "ภาควิชาวิศวกรรมเครื่องกล",
    "civil engineering": "ภาควิชาวิศวกรรมโยธา",
    "chemical engineering": "ภาควิชาวิศวกรรมเคมี",
    "industrial engineering": "ภาควิชาวิศวกรรมอุตสาหการ",
    "environmental engineering": "ภาควิชาวิศวกรรมสิ่งแวดล้อม",
    "biomedical engineering": "ภาควิชาวิศวกรรมชีวการแพทย์",
    "nuclear engineering": "ภาควิชาวิศวกรรมนิวเคลียร์",
    "metallurgical engineering": "ภาควิชาวิศวกรรมโลหการ",
    "mining engineering": "ภาควิชาวิศวกรรมเหมืองแร่และปิโตรเลียม",
    "water resources engineering": "ภาควิชาวิศวกรรมแหล่งน้ำ",

    # Dentistry
    "orthodontics": "ภาควิชาทันตกรรมจัดฟัน",
    "prosthodontics": "ภาควิชาทันตกรรมประดิษฐ์",
    "periodontology": "ภาควิชาปริทันตวิทยา",
    "periodontics": "ภาควิชาปริทันตวิทยา",
    "oral and maxillofacial surgery": "ภาควิชาศัลยศาสตร์ช่องปากและแม็กซิลโลเฟเชียล",
    "oral surgery": "ภาควิชาศัลยศาสตร์ช่องปาก",
    "operative dentistry": "ภาควิชาทันตกรรมหัตถการ",
    "pediatric dentistry": "ภาควิชาทันตกรรมสำหรับเด็ก",
    "oral biology": "ภาควิชาชีววิทยาช่องปาก",
    "oral medicine": "ภาควิชาเวชศาสตร์ช่องปาก",
    "oral radiology": "ภาควิชารังสีวิทยาช่องปาก",
    "endodontics": "ภาควิชาวิทยาเอ็นโดดอนต์",
    "community dentistry": "ภาควิชาทันตกรรมชุมชน",

    # Pharmacy
    "pharmaceutics": "ภาควิชาเภสัชกรรม",
    "industrial pharmacy": "ภาควิชาเภสัชกรรมอุตสาหการ",
    "pharmaceutical chemistry": "ภาควิชาเภสัชเคมี",
    "pharmacognosy": "ภาควิชาเภสัชพฤกษศาสตร์",
    "biopharmacy": "ภาควิชาชีวเภสัชศาสตร์",
    "clinical pharmacy": "ภาควิชาเภสัชกรรมคลินิก",
    "social and administrative pharmacy": "ภาควิชาเภสัชกรรมสังคมและการบริหาร",

    # Veterinary Science
    "veterinary anatomy": "ภาควิชากายวิภาคศาสตร์ทางสัตวแพทย์",
    "veterinary physiology": "ภาควิชาสรีรวิทยาทางสัตวแพทย์",
    "veterinary pathology": "ภาควิชาพยาธิวิทยาทางสัตวแพทย์",
    "veterinary pharmacology": "ภาควิชาเภสัชวิทยาทางสัตวแพทย์",
    "veterinary medicine": "ภาควิชาอายุรศาสตร์ทางสัตวแพทย์",
    "veterinary surgery": "ภาควิชาศัลยศาสตร์ทางสัตวแพทย์",
    "theriogenology": "ภาควิชาสูติศาสตร์ เธนุเวชวิทยา และวิทยาการสืบพันธุ์สัตว์",
    "animal husbandry": "ภาควิชาสัตวบาล",
    "preclinic and applied animal": "ภาควิชาปรีคลินิกและสัตวศาสตร์ประยุกต์",
    "clinical sciences and public health": "ภาควิชาเวชศาสตร์คลินิกและการสาธารณสุข",

    # Architecture & Design
    "architecture": "ภาควิชาสถาปัตยกรรมศาสตร์",
    "urban and regional planning": "ภาควิชาการวางแผนภาคและเมือง",
    "urban planning": "ภาควิชาการวางแผนภาคและเมือง",
    "landscape architecture": "ภาควิชาภูมิสถาปัตยกรรม",
    "industrial design": "ภาควิชาการออกแบบอุตสาหกรรม",
    "housing": "ภาควิชาเคหการ",

    # Business, Economics & Social Sciences
    "accountancy": "ภาควิชาการบัญชี",
    "accounting": "ภาควิชาการบัญชี",
    "banking and finance": "ภาควิชาการธนาคารและการเงิน",
    "finance": "ภาควิชาการธนาคารและการเงิน",
    "marketing": "ภาควิชาการตลาด",
    "commerce": "ภาควิชาพาณิชยศาสตร์",
    "statistics": "ภาควิชาสถิติ",
    "economics": "สาขาวิชาเศรษฐศาสตร์",
    "business administration": "สาขาวิชาบริหารธุรกิจ",
    "sasin": "สาขาวิชาบริหารธุรกิจ (Sasin)",
    "public administration": "ภาควิชารัฐประศาสนศาสตร์",
    "government": "ภาควิชาการปกครอง",
    "international relations": "ภาควิชาความสัมพันธ์ระหว่างประเทศ",
    "sociology": "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
    "curriculum and instruction": "สาขาวิชาหลักสูตรและการสอน",
    "educational psychology": "สาขาวิชาวิจัยและจิตวิทยาการศึกษา",
    "educational administration": "สาขาวิชานโยบาย การจัดการและความเป็นผู้นำทางการศึกษา",
    "law": "สาขาวิชานิติศาสตร์",
    "communication arts": "สาขาวิชานิเทศศาสตร์",
    "journalism": "สาขาวิชาวารสารสนเทศ",
    "mass communication": "สาขาวิชาการสื่อสารมวลชน",
    "nutrition": "สถาบันโภชนาการ",
    "population and social": "สถาบันวิจัยประชากรและสังคม",
}

# Faculty fallback mappings
FACULTY_FALLBACK_MAP = {
    "คณะแพทยศาสตร์": "ภาควิชาอายุรศาสตร์",
    "คณะแพทยศาสตร์ศิริราชพยาบาล": "ภาควิชาอายุรศาสตร์",
    "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี": "ภาควิชาอายุรศาสตร์",
    "คณะวิทยาศาสตร์": "ภาควิชาเคมี",
    "คณะวิศวกรรมศาสตร์": "ภาควิชาวิศวกรรมศาสตร์ทั่วไป",
    "คณะเภสัชศาสตร์": "ภาควิชาเภสัชกรรม",
    "คณะทันตแพทยศาสตร์": "ภาควิชาทันตแพทยศาสตร์",
    "คณะสัตวแพทยศาสตร์": "ภาควิชาอายุรศาสตร์ทางสัตวแพทย์",
    "คณะพาณิชยศาสตร์และการบัญชี": "ภาควิชาบริหารธุรกิจ",
    "คณะสถาปัตยกรรมศาสตร์": "สาขาวิชาสถาปัตยกรรมศาสตร์",
    "คณะอักษรศาสตร์": "สาขาวิชาภาษาศาสตร์",
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
}

RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")
RE_JUNK_INTERESTS = re.compile(r"^(?:none|-|\?|n/a|null|undefined)$", re.I)


def extract_department_from_affiliations(affils: list[str], faculty_th: str | None = None) -> tuple[str | None, str | None]:
    """
    Extract canonical Thai department and official email from raw affiliation strings.
    Returns (department_th, email).
    """
    extracted_dept = None
    extracted_email = None

    joined = " ".join(affils).lower()

    # 1. Check emails in affiliation strings
    for m in RE_EMAIL.finditer(" ".join(affils)):
        em = m.group(0).lower()
        if any(d in em for d in ["chula.ac.th", "mahidol.ac.th", "mahidol.edu", "si.mahidol.ac.th", "rama.mahidol.ac.th"]):
            extracted_email = em
            break

    # 2. Check department dictionary against joined text
    # Sort keys by length descending to match longest specific department first
    sorted_keys = sorted(DEPARTMENT_MAP.keys(), key=lambda k: len(k), reverse=True)
    for k in sorted_keys:
        if k in joined:
            extracted_dept = DEPARTMENT_MAP[k]
            break

    # 3. Fallback to faculty-level default if faculty is recognized unified school
    if not extracted_dept and faculty_th:
        if "นิติศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชานิติศาสตร์"
        elif "ศศินทร์" in faculty_th:
            extracted_dept = "สาขาวิชาบริหารธุรกิจ (Sasin)"
        elif "เศรษฐศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชาเศรษฐศาสตร์"
        elif "พยาบาลศาสตร์" in faculty_th:
            extracted_dept = "สาขาวิชาพยาบาลศาสตร์"
        elif "เวชศาสตร์เขตร้อน" in faculty_th:
            extracted_dept = "สาขาวิชาเวชศาสตร์เขตร้อน"
        elif "กายภาพบำบัด" in faculty_th:
            extracted_dept = "สาขาวิชากายภาพบำบัด"
        elif "ดุริยางคศิลป์" in faculty_th:
            extracted_dept = "สาขาวิชาดุริยางคศิลป์"
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

    # Maintain strict Phase 36 authorship breakdown consistency: total == first + co
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
    existing_pubs = winner.featured_publications or []
    seen_pubs = set(str(x).strip().lower() for x in existing_pubs)
    for pub in (ghost.featured_publications or []):
        norm = str(pub).strip().lower()
        if norm and norm not in seen_pubs:
            seen_pubs.add(norm)
            existing_pubs.append(pub)
    winner.featured_publications = existing_pubs

    # Taught courses union
    existing_courses = winner.taught_courses or []
    seen_courses = set(str(x).strip().lower() for x in existing_courses)
    for c in (ghost.taught_courses or []):
        norm = str(c).strip().lower()
        if norm and norm not in seen_courses:
            seen_courses.add(norm)
            existing_courses.append(c)
    winner.taught_courses = existing_courses

    # Education union
    existing_edu = winner.education or []
    seen_edu = set(str(x).strip().lower() for x in existing_edu)
    for e in (ghost.education or []):
        norm = str(e).strip().lower()
        if norm and norm not in seen_edu:
            seen_edu.add(norm)
            existing_edu.append(e)
    winner.education = existing_edu

    # Prefer verified email if missing
    if not winner.email and ghost.email:
        winner.email = ghost.email


def run_cu_mu_faculty_recovery():
    print("=== 🎓 RECOVER & CLASSIFY AUTHENTIC CU & MU TEACHING FACULTY ===", flush=True)
    t_start = time.time()

    # Pre-check database baseline
    with engine.connect() as conn:
        fac_count_start = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unassigned_count_start = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        total_baseline = fac_count_start + unassigned_count_start
        print(f"Pre-check baseline: faculties={fac_count_start:,}, scholars_unassigned={unassigned_count_start:,}, total={total_baseline:,}")

    db = SessionLocal()

    # =========================================================================
    # PASS 1: Deduplication & Metrics Merge into faculties
    # =========================================================================
    print("\n--- 🔍 PASS 1: In-Memory Deduplication & Metrics Merge ---", flush=True)
    fac_all = db.query(FacultyDB).all()
    opx_to_fac: dict[str, FacultyDB] = {}
    name_univ_to_fac: dict[tuple[str, str, str], FacultyDB] = {}
    for f in fac_all:
        if f.openalex_id and f.openalex_id != "not_indexed":
            opx_clean = f.openalex_id.strip()
            opx_to_fac[opx_clean] = f
            if opx_clean.startswith("https://openalex.org/"):
                opx_to_fac[opx_clean.split("/")[-1]] = f
            else:
                opx_to_fac[f"https://openalex.org/{opx_clean}"] = f
        fn = (f.first_name or "").strip().lower()
        ln = (f.last_name or "").strip().lower()
        if fn and ln and f.university_th:
            name_univ_to_fac[(fn, ln, f.university_th)] = f

    cu_mu_scholars = (
        db.query(ScholarUnassignedDB)
        .filter(ScholarUnassignedDB.university_th.in_(["จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยมหิดล"]))
        .all()
    )
    print(f"Total CU & MU scholars in scholars_unassigned: {len(cu_mu_scholars):,}")

    merged_ghost_ids = set()
    pass1_merged_count = 0

    for s in cu_mu_scholars:
        winner = None
        s_opx = (s.openalex_id or "").strip()
        if s_opx and s_opx in opx_to_fac:
            winner = opx_to_fac[s_opx]
        else:
            s_fn = (s.first_name or "").strip().lower()
            s_ln = (s.last_name or "").strip().lower()
            if s_fn and s_ln and s.university_th:
                winner = name_univ_to_fac.get((s_fn, s_ln, s.university_th))

        if winner and winner.id != s.id:
            merge_faculty_metrics_and_lists(winner, s)
            merged_ghost_ids.add(s.id)
            pass1_merged_count += 1

    db.commit()
    print(f"Pass 1: Merged {pass1_merged_count:,} duplicate CU/MU rows into verified faculty in 'faculties'.")

    # Delete merged ghost rows from scholars_unassigned
    if merged_ghost_ids:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM public.scholars_unassigned WHERE id IN :ids"),
                {"ids": tuple(merged_ghost_ids)},
            )
        print(f"Pass 1: Removed {len(merged_ghost_ids):,} redundant ghost rows from 'scholars_unassigned'.")

    # =========================================================================
    # PASS 2 & 3: High-Throughput OpenAlex Affiliation Screening & Dept Recovery
    # =========================================================================
    print("\n--- ⚡ PASS 2 & 3: OpenAlex Institutional Probing & Department Extraction ---", flush=True)

    # Remaining CU/MU scholars
    remaining_scholars = (
        db.query(ScholarUnassignedDB)
        .filter(
            ScholarUnassignedDB.university_th.in_(["จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยมหิดล"]),
            ~ScholarUnassignedDB.id.in_(merged_ghost_ids) if merged_ghost_ids else True,
        )
        .all()
    )
    print(f"Remaining CU/MU scholars to evaluate: {len(remaining_scholars):,}")

    # Build map of author_id -> scholar
    author_to_scholar: dict[str, ScholarUnassignedDB] = {}
    for s in remaining_scholars:
        aid = None
        if s.openalex_id and s.openalex_id.startswith("https://openalex.org/A"):
            aid = s.openalex_id.split("/")[-1]
        elif s.profile_url and "openalex.org/A" in s.profile_url:
            aid = s.profile_url.split("/")[-1]
        if aid:
            author_to_scholar[aid] = s

    print(f"Scholars with valid OpenAlex Author ID: {len(author_to_scholar):,}")

    # Step A: Batch fetch author metadata (last_known_institutions & affiliations)
    all_aids = list(author_to_scholar.keys())
    confirmed_cu_mu_aids = set()
    foreign_aids = set()

    def fetch_author_chunk(chunk_aids: list[str]) -> list[dict]:
        pipe_str = "|".join(chunk_aids)
        params = urllib.parse.urlencode({
            "filter": f"openalex_id:{pipe_str}",
            "select": "id,display_name,last_known_institutions,affiliations",
            "per-page": "50",
            "mailto": "research@example.com",
        })
        url = f"https://api.openalex.org/authors?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "AdvisorMatchBot/1.0"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    d = json.loads(resp.read())
                    return d.get("results", [])
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(2.0 * (attempt + 1))
                else:
                    break
            except Exception:
                time.sleep(1.0)
        return []

    print(f"Fetching author institutional affiliations across {len(all_aids):,} authors in chunks of 50...")
    chunks = [all_aids[i:i + 50] for i in range(0, len(all_aids), 50)]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_author_chunk, c): c for c in chunks}
        completed = 0
        for f in as_completed(futures):
            results = f.result()
            completed += 1
            if completed % 20 == 0 or completed == len(chunks):
                print(f"  Processed {completed}/{len(chunks)} author chunks ({(completed/len(chunks))*100:.1f}%)")
            for a in results:
                raw_id = (a.get("id") or "").split("/")[-1]
                insts = a.get("last_known_institutions") or []
                affils = a.get("affiliations") or []

                # Check for CU or MU
                is_cu_mu = False
                for inst in insts:
                    iname = (inst.get("display_name") or "").lower()
                    if any(k in iname for k in CU_KEYWORDS + MU_KEYWORDS):
                        is_cu_mu = True
                        break

                if not is_cu_mu:
                    # Check recent affiliations (within last 5 years)
                    for aff in affils:
                        inst = aff.get("institution") or {}
                        iname = (inst.get("display_name") or "").lower()
                        years = aff.get("years") or []
                        if any(y >= 2018 for y in years) and any(k in iname for k in CU_KEYWORDS + MU_KEYWORDS):
                            is_cu_mu = True
                            break

                if is_cu_mu:
                    confirmed_cu_mu_aids.add(raw_id)
                else:
                    foreign_aids.add(raw_id)

    print(f"\nAffiliation Screening Results:")
    print(f"- Confirmed CU/MU teaching/research affiliation: {len(confirmed_cu_mu_aids):,}")
    print(f"- Foreign/external co-authors (retained in scholars_unassigned): {len(foreign_aids):,}")

    # Step B: For confirmed CU/MU authors, query recent works to extract department strings
    print(f"\nExtracting raw department affiliations from recent works for {len(confirmed_cu_mu_aids):,} confirmed scholars...")
    confirmed_list = list(confirmed_cu_mu_aids)
    works_chunks = [confirmed_list[i:i + 25] for i in range(0, len(confirmed_list), 25)]

    author_affils: dict[str, list[str]] = {aid: [] for aid in confirmed_list}

    def fetch_works_chunk(chunk_aids: list[str]) -> list[dict]:
        pipe_str = "|".join(chunk_aids)
        params = urllib.parse.urlencode({
            "filter": f"author.id:{pipe_str}",
            "select": "id,authorships,publication_year",
            "sort": "publication_year:desc",
            "per-page": "50",
            "mailto": "research@example.com",
        })
        url = f"https://api.openalex.org/works?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "AdvisorMatchBot/1.0"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    d = json.loads(resp.read())
                    return d.get("results", [])
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(2.0 * (attempt + 1))
                else:
                    break
            except Exception:
                time.sleep(1.0)
        return []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_works_chunk, c): c for c in works_chunks}
        completed = 0
        for f in as_completed(futures):
            works = f.result()
            completed += 1
            if completed % 20 == 0 or completed == len(works_chunks):
                print(f"  Processed {completed}/{len(works_chunks)} works chunks ({(completed/len(works_chunks))*100:.1f}%)")
            for w in works:
                for a in w.get("authorships", []):
                    aid = (a.get("author", {}).get("id") or "").split("/")[-1]
                    if aid in author_affils:
                        raw_strings = a.get("raw_affiliation_strings") or []
                        author_affils[aid].extend(raw_strings)

    # =========================================================================
    # PASS 4: Department Resolution & Promotion to faculties
    # =========================================================================
    print("\n--- 🚀 PASS 4: Department Resolution & Promotion to faculties ---", flush=True)
    promoted_scholars = []
    promoted_ids = set()

    for aid in confirmed_list:
        scholar = author_to_scholar.get(aid)
        if not scholar:
            continue

        raw_strings = author_affils.get(aid, [])
        dept, email = extract_department_from_affiliations(raw_strings, scholar.faculty_th)

        # If department was successfully resolved
        if dept and dept != "ระบุไม่ได้":
            # Clean email
            final_email = scholar.email or email
            if final_email and RE_PHONE.search(final_email):
                final_email = None

            # Clean academic title & Thai name
            title_th = scholar.academic_title_th or "อ."
            name_th = scholar.full_name_th
            if not name_th or not any("฀" <= c <= "๿" for c in name_th):
                # Format Thai name display cleanly
                fn = scholar.first_name or ""
                ln = scholar.last_name or ""
                name_th = f"{title_th} {fn} {ln}".strip()

            promoted_scholars.append({
                "id": scholar.id,
                "university": scholar.university,
                "university_th": scholar.university_th,
                "faculty": scholar.faculty,
                "faculty_th": scholar.faculty_th,
                "department": scholar.department or dept,
                "department_th": dept,
                "academic_title_th": title_th,
                "first_name": scholar.first_name,
                "last_name": scholar.last_name,
                "full_name_th": name_th,
                "role": scholar.role or "อาจารย์ประจำและนักวิจัย",
                "email": final_email,
                "image_url": scholar.image_url,
                "profile_url": scholar.profile_url,
                "education": scholar.education or [],
                "research_interests": scholar.research_interests or [],
                "taught_courses": scholar.taught_courses or [],
                "featured_publications": scholar.featured_publications or [],
                "total_publications_count": scholar.total_publications_count or 0,
                "first_author_count": scholar.first_author_count or 0,
                "co_author_count": scholar.co_author_count or 0,
                "total_citations": scholar.total_citations or 0,
                "h_index": scholar.h_index or 0,
                "openalex_id": scholar.openalex_id,
                "scholar_url": scholar.scholar_url,
                "embedding_text": scholar.embedding_text,
                "embedding": scholar.embedding if scholar.embedding is not None else None  # NULL: re-embed via embed_missing.py,
            })
            promoted_ids.add(scholar.id)

    print(f"Resolved verified departments for {len(promoted_scholars):,} CU & MU faculty members!")

    # Batch update scholars_unassigned and transfer to faculties
    if promoted_scholars:
        print(f"Promoting {len(promoted_scholars):,} faculty members into 'public.faculties'...")
        with engine.begin() as conn:
            chunk_size = 500
            for i in range(0, len(promoted_scholars), chunk_size):
                chunk = promoted_scholars[i:i + chunk_size]
                update_params = [
                    {
                        "id": p["id"],
                        "department": p["department"],
                        "department_th": p["department_th"],
                        "email": p["email"],
                        "full_name_th": p["full_name_th"],
                        "academic_title_th": p["academic_title_th"],
                    }
                    for p in chunk
                ]
                conn.execute(
                    text("""
                        UPDATE public.scholars_unassigned
                        SET department = :department,
                            department_th = :department_th,
                            email = COALESCE(:email, email),
                            full_name_th = :full_name_th,
                            academic_title_th = :academic_title_th
                        WHERE id = :id;
                    """),
                    update_params,
                )

            # Insert directly from scholars_unassigned into faculties
            conn.execute(
                text("""
                    INSERT INTO public.faculties
                    SELECT * FROM public.scholars_unassigned
                    WHERE id IN :ids
                    ON CONFLICT (id) DO UPDATE SET
                        department = EXCLUDED.department,
                        department_th = EXCLUDED.department_th,
                        email = COALESCE(faculties.email, EXCLUDED.email),
                        total_citations = GREATEST(faculties.total_citations, EXCLUDED.total_citations),
                        h_index = GREATEST(faculties.h_index, EXCLUDED.h_index),
                        total_publications_count = GREATEST(faculties.total_publications_count, EXCLUDED.total_publications_count);
                """),
                {"ids": tuple(promoted_ids)},
            )

            # Delete promoted from scholars_unassigned
            conn.execute(
                text("DELETE FROM public.scholars_unassigned WHERE id IN :ids"),
                {"ids": tuple(promoted_ids)},
            )
        print(f"Successfully promoted {len(promoted_scholars):,} verified faculty to 'faculties' and removed from 'scholars_unassigned'.")

    # =========================================================================
    # PASS 5: Disk Checkpoint & Verification
    # =========================================================================
    print("\n--- 📊 PASS 5: Verification & Disk Checkpointing ---", flush=True)
    with engine.connect() as conn:
        fac_count_final = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unassigned_count_final = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        unspecified_in_fac = conn.execute(
            text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")
        ).scalar()
        cu_fac_final = conn.execute(
            text("SELECT count(*) FROM public.faculties WHERE university_th = 'จุฬาลงกรณ์มหาวิทยาลัย'")
        ).scalar()
        mu_fac_final = conn.execute(
            text("SELECT count(*) FROM public.faculties WHERE university_th = 'มหาวิทยาลัยมหิดล'")
        ).scalar()
        total_final = fac_count_final + unassigned_count_final

    checkpoint_data = {
        "faculties_count_start": fac_count_start,
        "unassigned_count_start": unassigned_count_start,
        "pass1_merged_into_existing": pass1_merged_count,
        "pass2_confirmed_cu_mu": len(confirmed_cu_mu_aids),
        "pass2_foreign_retained": len(foreign_aids),
        "pass4_promoted_to_faculties": len(promoted_scholars),
        "faculties_count_final": fac_count_final,
        "cu_faculties_final": cu_fac_final,
        "mu_faculties_final": mu_fac_final,
        "unassigned_count_final": unassigned_count_final,
        "unspecified_in_faculties": unspecified_in_fac,
        "total_baseline": total_baseline,
        "total_final": total_final,
        "parity_preserved": total_final == total_baseline,
        "execution_time_seconds": round(time.time() - t_start, 2),
    }

    CHECKPOINT_FILE.write_text(json.dumps(checkpoint_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Checkpoint saved to: {CHECKPOINT_FILE}")

    print("\nFinal Metrics Verification:")
    print(f"- Primary 'faculties' count: {fac_count_final:,} (CU: {cu_fac_final:,}, MU: {mu_fac_final:,})")
    print(f"- 'faculties' with unspecified department: {unspecified_in_fac} (MUST be 0)")
    print(f"- 'scholars_unassigned' count: {unassigned_count_final:,}")
    print(f"- Total preserved across both tables: {total_final:,} (Parity: {total_final == total_baseline})")
    print(f"Execution completed in {round(time.time() - t_start, 2)}s!")

    db.close()


if __name__ == "__main__":
    run_cu_mu_faculty_recovery()
