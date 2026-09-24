# -*- coding: utf-8 -*-
"""
Reconcile and Clean Courses Pipeline (5-Pillar SKILL.state Architecture)

Executes multi-pass deterministic in-memory state reducer and database updates:
1. Degree Level & Degree Name Normalization
2. Faculty Name Inconsistencies & Typos (MFU, STOU, unspecified faculties)
3. Course Title & Language Hygiene (Double prefixes, non-breaking spaces, typos, raw English degree leaks)
4. Tuition, Duration, and Credits Normalization (Unit standardization, CMU null total calculation)
5. Semantic Tag & Career Path Realignment (Decontamination of IT fallback paths from medical/humanities fields)
6. Missing Descriptions & English Titles population
7. Embedding Text synchronization & Vectorization
8. Disk Checkpointing to backend/data/agent_states/clean_courses_snapshot.json
"""
import sys, os, json, re, time
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def _log(*args):
    print(*args, flush=True)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import dotenv
dotenv.load_dotenv(ROOT / ".env")

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import EmbeddingService
from sqlalchemy.orm import defer

# ==============================================================================
# 1. Exact Mappings & Taxonomy Standards
# ==============================================================================

# Degree Name Map for 21 empty degree_name records
DEGREE_NAME_FIXES = {
    "cmu_17_4_008": "วท.ม. (สถาปัตยกรรม)",
    "cmu_tqf_25260041100058": "ศล.บ. (ประติมากรรม)",
    "cmu_tqf_25260041100058_v2": "ศล.บ. (จิตรกรรม)",
    "cmu_tqf_25260041100071": "ศล.บ. (ศิลปะภาพพิมพ์)",
    "cmu_tqf_25260041100082": "ศล.บ. (ศิลปะไทยและวัฒนธรรมสร้างสรรค์)",
    "cmu_tqf_25380041100309_v2": "ศษ.บ. (การศึกษาปฐมวัย-การศึกษาพิเศษ)",
    "cmu_tqf_25400041100807": "ศษ.บ. (ประถมศึกษา)",
    "cmu_tqf_25450041100184": "ศล.บ. (การถ่ายภาพสร้างสรรค์)",
    "cmu_tqf_25450041101049": "ศล.บ. (การออกแบบ)",
    "cmu_tqf_25460041101445": "ศษ.บ. (ชีววิทยา)",
    "cmu_tqf_25470041103628": "ศษ.บ. (เคมี)",
    "cmu_tqf_25520041106076": "ศษ.บ. (ฟิสิกส์)",
    "cmu_tqf_25530041102422": "ศล.บ. (สื่อศิลปะและการออกแบบสื่อ)",
    "cmu_tqf_25540041101736": "ศล.บ. (สหศาสตร์ศิลป์)",
    "cmu_tqf_25570041101796": "ศล.บ. (ศิลปะการแสดง)",
    "cmu_tqf_25630041100096": "ศษ.บ. (อุตสาหกรรมและการงานอาชีพ)",
    "wave36_msu_msc_01": "วท.ม. (เทคโนโลยีการอาหาร)",
    "wave36_msu_phd_01": "ปร.ด. (เทคโนโลยีการอาหาร)",
    "wave36_msu_msc_03": "วท.ม. (เกษตรศาสตร์)",
    "wave36_msu_phd_03": "ปร.ด. (เกษตรศาสตร์)",
    "wave37_psu_msc_01": "วท.ม. (การคอมพิวเตอร์)"
}

# MFU English School to Thai Faculty mapping
MFU_FACULTY_MAP = {
    "School of Agro Industry": "สำนักวิชาอุตสาหกรรมเกษตร",
    "School of Agro-Industry": "สำนักวิชาอุตสาหกรรมเกษตร",
    "School of Applied Digital Technology": "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์",
    "School of Cosmetic Science": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
    "School of Dentistry": "สำนักวิชาทันตแพทยศาสตร์",
    "School of Health Science": "สำนักวิชาวิทยาศาสตร์สุขภาพ",
    "School of Integrative Medicine": "สำนักวิชาการแพทย์บูรณาการ",
    "School of Law": "สำนักวิชานิติศาสตร์",
    "School of Liberal Arts": "สำนักวิชาศิลปศาสตร์",
    "School of Management": "สำนักวิชาการจัดการ",
    "School of Medicine": "สำนักวิชาแพทยศาสตร์",
    "School of Nursing": "สำนักวิชาพยาบาลศาสตร์",
    "School of Science": "สำนักวิชาวิทยาศาสตร์",
    "School of Sinology": "สำนักวิชาจีนวิทยา",
    "School of Social Innovation": "สำนักวิชานวัตกรรมสังคม",
    "School of Information Technology": "สำนักวิชาเทคโนโลยีสารสนเทศ"
}

# Unspecified Faculty Fixes (17 courses)
UNSPECIFIED_FACULTY_FIXES = {
    "au_simba": "คณะบริหารธุรกิจและเศรษฐศาสตร์",
    "bu_master_arch": "คณะสถาปัตยกรรมศาสตร์",
    "bu_master_arch_idm": "คณะสถาปัตยกรรมศาสตร์",
    "bu_master_arch_interior": "คณะสถาปัตยกรรมศาสตร์",
    "bu_master_ca_brand": "คณะนิเทศศาสตร์",
    "creative-media-technology": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
    "mju_fisheries_aquatic": "คณะเทคโนโลยีการประมงและทรัพยากรทางน้ำ",
    "mju_nursing": "คณะพยาบาลศาสตร์",
    "mju_smart_farm_eng": "คณะวิศวกรรมและอุตสาหกรรมเกษตร",
    "sdu_doc_management": "บัณฑิตวิทยาลัย",
    "stou_bachelor": "สำนักทะเบียนและวัดผล",
    "stou_graduate": "สำนักบัณฑิตศึกษา",
    "wu_cpe": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
    "wu_dent_dds": "สำนักวิชาทันตแพทยศาสตร์",
    "wu_pharm": "สำนักวิชาเภสัชศาสตร์",
    "wu_physical_therapy": "สำนักวิชาสหเวชศาสตร์",
    "swu-bed-electrical-industrial": "คณะศึกษาศาสตร์"
}

# Explicit Title Normalization & Leak Fixes (Thai & English)
TITLE_FIXES = {
    # 6 Zero-Thai courses
    "DTMH": ("หลักสูตรประกาศนียบัตรอายุรศาสตร์เขตร้อนและสุขวิทยา (หลักสูตรนานาชาติ)", "Graduate Diploma in Tropical Medicine and Hygiene (D.T.M.&H.)"),
    "DBHI": ("หลักสูตรประกาศนียบัตรสารสนเทศชีวการแพทย์และสุขภาพ (หลักสูตรนานาชาติ)", "Graduate Diploma in Biomedical and Health Informatics (D.B.H.I.)"),
    "bu_film_international": ("หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาการผลิตภาพยนตร์และคอนเทนต์ระดับโลก (หลักสูตรนานาชาติ)", "Bachelor of Fine Arts in Film, Series and Global Content Production and Business (International Program)"),
    "sut-ug-02": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชานวัตกรรมผู้ประกอบการเกษตร (Innovative Agripreneur)", "Bachelor of Science in Innovative Agripreneur"),
    "sut-ug-04": ("หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมปิโตรเคมีและพอลิเมอร์", "Bachelor of Engineering in Petrochemical and Polymer Engineering"),
    "NURSING-ASSISTANT-CERTIFICATE": ("หลักสูตรประกาศนียบัตรผู้ช่วยพยาบาล", "The Nursing Assistant Certificate Program"),

    # CU Arch degree leak fixes
    "cu-arch-bachelor-industrial-design": ("หลักสูตรการออกแบบอุตสาหกรรมบัณฑิต สาขาวิชาการออกแบบอุตสาหกรรม", "Bachelor of Industrial Design Program in Industrial Design"),
    "cu-arch-barch-architecture": ("หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรม", "Bachelor of Architecture Program in Architecture"),
    "cu-arch-barch-interior": ("หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมภายใน", "Bachelor of Architecture Program in Interior Architecture"),
    "cu-arch-barch-thai": ("หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมไทย", "Bachelor of Architecture Program in Thai Architecture"),
    "cu-arch-barch-urban": ("หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมผังเมือง", "Bachelor of Architecture Program in Urban Architecture"),
    "cu-arch-bfaa-commdesign": ("หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาการออกแบบการสื่อสาร (หลักสูตรนานาชาติ - CommDe)", "Bachelor of Fine and Applied Arts Program in Communication Design (International Program)"),
    "cu-arch-bla-landscape": ("หลักสูตรภูมิสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาภูมิสถาปัตยกรรม", "Bachelor of Landscape Architecture Program in Landscape Architecture"),
    "cu-arch-mhd-housing": ("หลักสูตรเคหพัฒนศาสตรมหาบัณฑิต สาขาวิชาการพัฒนาเคหะและอสังหาริมทรัพย์", "Master of Housing Development Program in Housing and Real Estate Development"),
    "cu-arch-msc-architecture": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสถาปัตยกรรม", "Master of Science Program in Architecture"),
    "cu-arch-msc-urbanstrategies": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชายุทธศาสตร์เมือง (หลักสูตรนานาชาติ)", "Master of Science Program in Urban Strategies (International Program)"),
    "cu-arch-phd-architecture": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสถาปัตยกรรม", "Doctor of Philosophy Program in Architecture"),
    "cu-arch-phd-landscape": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาภูมิสถาปัตยกรรม", "Doctor of Philosophy Program in Landscape Architecture"),
    "cu-arch-phd-urban-planning-design": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการวางผังและออกแบบเมือง", "Doctor of Philosophy Program in Urban Planning and Design"),
    "cu-arch-march-archdesign": ("หลักสูตรสถาปัตยกรรมศาสตรมหาบัณฑิต สาขาวิชาการออกแบบสถาปัตยกรรม (หลักสูตรนานาชาติ)", "Master of Architecture Program in Architectural Design (International Program)"),
    "cu-arch-master-urban-regional-planning": ("หลักสูตรการผังเมืองและชุมชนมหาบัณฑิต สาขาวิชาการวางผังและออกแบบเมือง", "Master of Urban and Regional Planning Program in Urban Planning and Design"),

    # CU Sci degree leak fixes
    "CU-SCI-BSC-BC": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาชีวเคมี", "Bachelor of Science Program in Biochemistry"),
    "CU-SCI-BSC-MST": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวัสดุศาสตร์และเทคโนโลยี", "Bachelor of Science Program in Materials Science and Technology"),
    "CU-SCI-BSC-ZOO": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาสัตววิทยา", "Bachelor of Science Program in Zoology"),
    "CU-SCI-MSC-FOODST-INT": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีทางอาหาร (หลักสูตรนานาชาติ)", "Master of Science Program in Food Science and Technology (International Program)"),
    "CU-SCI-MSC-INDTOX": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพิษวิทยาอุตสาหกรรมและการประเมินความเสี่ยง", "Master of Science Program in Industrial Toxicology and Risk Assessment"),
    "CU-SCI-PHD-ZOO": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสัตววิทยา", "Doctor of Philosophy Program in Zoology"),

    # CU Edu PhD fixes
    "cu-edu-phd-art-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาศิลปศึกษา", "Doctor of Philosophy Program in Art Education"),
    "cu-edu-phd-development-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาการศึกษาเพื่อการพัฒนา", "Doctor of Philosophy Program in Development Education"),
    "cu-edu-phd-early-childhood-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาการศึกษาปฐมวัย", "Doctor of Philosophy Program in Early Childhood Education"),
    "cu-edu-phd-education-research-methodology": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาวิธีวิทยาการวิจัยการศึกษา", "Doctor of Philosophy Program in Education Research Methodology"),
    "cu-edu-phd-educational-management": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาบริหารการศึกษา", "Doctor of Philosophy Program in Educational Management"),
    "cu-edu-phd-educational-measurement-evaluation": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาการวัดและประเมินผลการศึกษา", "Doctor of Philosophy Program in Educational Measurement and Evaluation"),
    "cu-edu-phd-educational-psychology-guidance": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาจิตวิทยาการศึกษาและการแนะแนว", "Doctor of Philosophy Program in Educational Psychology and Guidance"),
    "cu-edu-phd-educational-statistics-data-science": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาสถิติการศึกษาและวิทยาการข้อมูล", "Doctor of Philosophy Program in Educational Statistics and Data Science"),
    "cu-edu-phd-educational-system-management-leadership": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาภาวะผู้นำการจัดการระบบการศึกษา (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Educational System Management Leadership (International Program)"),
    "cu-edu-phd-health-physical-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาสุขศึกษาและพลศึกษา", "Doctor of Philosophy Program in Health and Physical Education"),
    "cu-edu-phd-music-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาดนตรีศึกษา", "Doctor of Philosophy Program in Music Education"),
    "cu-edu-phd-non-formal-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาการศึกษานอกระบบโรงเรียน", "Doctor of Philosophy Program in Non-Formal Education"),
    "cu-edu-phd-special-inclusive-education": ("หลักสูตรครุศาสตรดุษฎีบัณฑิต สาขาวิชาการศึกษาพิเศษและการศึกษาแบบเรียนรวม", "Doctor of Philosophy Program in Special and Inclusive Education"),

    # CU Med & Account fixes
    "cu-account-master-int-business-mgmt": ("หลักสูตรการจัดการมหาบัณฑิต สาขาวิชาการจัดการธุรกิจระหว่างประเทศ (หลักสูตรนานาชาติ)", "Master of Management Program in International Business Management (International Program)"),
    "cu-med-higher-grad-dip-clin-sci": ("หลักสูตรประกาศนียบัตรบัณฑิตชั้นสูงทางวิทยาศาสตร์การแพทย์คลินิก", "Higher Graduate Diploma of Clinical Sciences Program"),
    "cu-med-ms-digital-ai-health": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัลและปัญญาประดิษฐ์ในระบบสุขภาพ", "Master of Science Program in Digital and AI Technologies in Health Systems"),
    "cu-med-ms-health-dev-inter": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการพัฒนาสุขภาพ (หลักสูตรนานาชาติ)", "Master of Science Program in Health Development (International Program)"),
    "cu-med-ms-health-prof-edu": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการศึกษาทางวิชาชีพสุขภาพ (สหสาขาวิชา)", "Master of Science Program in Health Professions Education (Interdisciplinary Program)"),
    "cu-med-ms-health-res-mgmt": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการวิจัยและการจัดการด้านสุขภาพ", "Master of Science Program in Health Research and Management"),
    "cu-med-ms-med-biochem": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีวเคมีทางการแพทย์", "Master of Science Program in Medical Biochemistry"),
    "cu-med-ms-med-parasitol": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาปรสิตวิทยาทางการแพทย์", "Master of Science Program in Medical Parasitology"),
    "cu-med-ms-med-phys": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาฟิสิกส์ทางการแพทย์", "Master of Science Program in Medical Physics"),
    "cu-med-ms-med-sci-thai": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์", "Master of Science Program in Medical Sciences"),
    "cu-med-ms-medicine": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาแพทยศาสตร์", "Master of Science Program in Medicine"),
    "cu-med-ms-mental-health": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสุขภาพจิต", "Master of Science Program in Mental Health"),
    "cu-med-phd-biomed-biotech-inter": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์ชีวการแพทย์และเทคโนโลยีชีวภาพ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Biomedical Sciences and Biotechnology (International Program)"),
    "cu-med-phd-clin-sci-inter": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์คลินิก (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Clinical Sciences (International Program)"),
    "cu-med-phd-health-res-mgmt-inter": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการวิจัยและการจัดการด้านสุขภาพ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Health Research and Management"),
    "cu-med-phd-med-biochem-thai": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาชีวเคมีทางการแพทย์", "Doctor of Philosophy Program in Medical Biochemistry"),
    "cu-med-phd-med-phys-thai": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาฟิสิกส์ทางการแพทย์", "Doctor of Philosophy Program in Medical Physics"),
    "cu-med-phd-med-sci-thai": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์", "Doctor of Philosophy Program in Medical Sciences"),
    "cu-med-phd-medicine-thai": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาแพทยศาสตร์", "Doctor of Philosophy Program in Medicine"),
    "cu-med-phd-mental-health-thai": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสุขภาพจิต", "Doctor of Philosophy Program in Mental Health"),
    "cu-med-ms-clin-sci-inter": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์คลินิก (หลักสูตรนานาชาติ)", "Master of Science Program in Clinical Sciences (International Program)"),
    "cu-vet-grad-dip-vet-clinical-sciences": ("หลักสูตรประกาศนียบัตรบัณฑิต สาขาวิทยาศาสตร์คลินิกทางสัตวแพทย์", "Graduate Diploma in Veterinary Clinical Sciences Program"),

    # RAMA & Mahidol leak fixes
    "RAMA-CD-UG": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์การสื่อความหมายและความผิดปกติของการสื่อความหมาย", "Bachelor of Science Program in Communication Disorders"),
    "RAMA-NS-UG": ("หลักสูตรพยาบาลศาสตรบัณฑิต", "Bachelor of Nursing Science Program"),
    "RAMA-PM-UG": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาฉุกเฉินการแพทย์ (Paramedic)", "Bachelor of Science Program in Paramedics"),
    "RAMA-MS-EPI": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาระบาดวิทยาทางการแพทย์ (หลักสูตรนานาชาติ)", "Master of Science Program in Medicine Epidemiology (International Program)"),
    "RAMA-PHD-CLEPI": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาระบาดวิทยาคลินิก (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Clinical Epidemiology (International Program)"),
    "RAMA-PHD-MOLMED": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเวชศาสตร์ระดับโมเลกุล (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Molecular Medicine (International Program)"),
    "RAMA-PHD-NURS": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพยาบาลศาสตร์ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Nursing (International Program)"),
    "RAMA-PHD-TRANSMED": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเวชศาสตร์ปริวรรต (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Translational Medicine (International Program)"),
    "PHD-PHM": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาจุลชีววิทยาสาธารณสุข (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Public Health Microbiology (International Program)"),
    "bsc-ict": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร (หลักสูตรนานาชาติ)", "Bachelor of Science in Information and Communication Technology (International Program)"),

    # SUT leak fixes
    "sut_bachelor_medicine": ("หลักสูตรแพทยศาสตรบัณฑิต", "Doctor of Medicine Program"),
    "sut_bachelor_geotechnology_engineering": ("หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมธรณี", "Bachelor of Engineering Program in Geotechnology Engineering"),
    "sut_bachelor_information_studies": ("หลักสูตรสารสนเทศศาสตรบัณฑิต สาขาวิชาสารสนเทศศึกษา", "Bachelor of Information Studies Program"),
    "sut_bachelor_management_information_system": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาระบบสารสนเทศเพื่อการจัดการ", "Bachelor of Science Program in Management Information Systems"),
    "sut_bachelor_production_engineering": ("หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการผลิต", "Bachelor of Engineering Program in Production Engineering"),
    "sut_bachelor_sports_science": ("หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์การกีฬา", "Bachelor of Science Program in Sports Science"),
    "sut_bachelor_telecommunications_engineering": ("หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโทรคมนาคม", "Bachelor of Engineering Program in Telecommunications Engineering"),

    # Specific Typos
    "bu_master_arch_interior": ("หลักสูตรสถาปัตยกรรมศาสตรมหาบัณฑิต สาขาวิชาเอกสถาปัตยกรรมภายใน (Interior Architecture) (หลักสูตร 2 ภาษา)", "Master of Architecture Program in Interior Architecture (Bilingual Program)"),
    "cmu_17_4_008": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสถาปัตยกรรม", "Master of Science Program in Architecture"),
    "mfu_bachelor_business_administration": ("หลักสูตรบริหารธุรกิจบัณฑิต", "Bachelor of Business Administration Program")
}

# MU Faculty of Science Master & PhD program mapping
MU_SC_MSC_MAP = {
    "mu-sc-msc-anatomy": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชากายวิภาคศาสตร์และชีววิทยาโครงสร้าง (หลักสูตรนานาชาติ)", "Master of Science Program in Anatomy and Structural Biology (International Program)"),
    "mu-sc-msc-applied-math": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์ (หลักสูตรนานาชาติ)", "Master of Science Program in Applied Mathematics (International Program)"),
    "mu-sc-msc-biochemistry": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีวเคมี (หลักสูตรนานาชาติ)", "Master of Science Program in Biochemistry (International Program)"),
    "mu-sc-msc-bioresources-env-bio": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาทรัพยากรชีวภาพและชีววิทยาสิ่งแวดล้อม (หลักสูตรนานาชาติ)", "Master of Science Program in Bioresources and Environmental Biology (International Program)"),
    "mu-sc-msc-biotechnology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ (หลักสูตรนานาชาติ)", "Master of Science Program in Biotechnology (International Program)"),
    "mu-sc-msc-chemistry": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเคมี (หลักสูตรนานาชาติ)", "Master of Science Program in Chemistry (International Program)"),
    "mu-sc-msc-exercise-physiology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสรีรวิทยาการออกกำลังกาย (หลักสูตรนานาชาติ)", "Master of Science Program in Exercise Physiology (International Program)"),
    "mu-sc-msc-forensic-science": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชานิติวิทยาศาสตร์ (หลักสูตรนานาชาติ)", "Master of Science Program in Forensic Science (International Program)"),
    "mu-sc-msc-innovative-physics": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาฟิสิกส์นวัตกรรม (หลักสูตรนานาชาติ)", "Master of Science Program in Innovative Physics (International Program)"),
    "mu-sc-msc-materials-sci-eng": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวัสดุศาสตร์และวิศวกรรมวัสดุ (หลักสูตรนานาชาติ)", "Master of Science Program in Materials Science and Engineering (International Program)"),
    "mu-sc-msc-microbio-immunology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาจุลชีววิทยาและวิทยาภูมิคุ้มกัน (หลักสูตรนานาชาติ)", "Master of Science Program in Microbiology and Immunology (International Program)"),
    "mu-sc-msc-pathobiology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพยาธิชีววิทยา (หลักสูตรนานาชาติ)", "Master of Science Program in Pathobiology (International Program)"),
    "mu-sc-msc-pharmacology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเภสัชวิทยา (หลักสูตรนานาชาติ)", "Master of Science Program in Pharmacology (International Program)"),
    "mu-sc-msc-physics": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาฟิสิกส์ (หลักสูตรนานาชาติ)", "Master of Science Program in Physics (International Program)"),
    "mu-sc-msc-physiology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสรีรวิทยา (หลักสูตรนานาชาติ)", "Master of Science Program in Physiology (International Program)"),
    "mu-sc-msc-plant-sciences": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพฤกษศาสตร์ (หลักสูตรนานาชาติ)", "Master of Science Program in Plant Sciences (International Program)"),
    "mu-sc-msc-polymer-sci-tech": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีพอลิเมอร์ (หลักสูตรนานาชาติ)", "Master of Science Program in Polymer Science and Technology (International Program)"),
    "mu-sc-msc-science-innovation": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชานวัตกรรมวิทยาศาสตร์ (หลักสูตรนานาชาติ)", "Master of Science Program in Science Innovation (International Program)"),
    "mu-sc-msc-toxicology": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพิษวิทยา (หลักสูตรนานาชาติ)", "Master of Science Program in Toxicology (International Program)"),
    "mu-sc-dd-msc-biotech-osaka": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ (หลักสูตรสองปริญญาร่วมกับ มหาวิทยาลัยโอซาก้า)", "Master of Science Program in Biotechnology (Double Degree Program with Osaka University)"),
    "mu-sc-dd-msc-plant-chiba": ("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพฤกษศาสตร์ (หลักสูตรสองปริญญาร่วมกับ มหาวิทยาลัยชิบะ)", "Master of Science Program in Plant Science (Double Degree Program with Chiba University)")
}

MU_SC_PHD_MAP = {
    "mu-sc-phd-anatomy": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชากายวิภาคศาสตร์และชีววิทยาโครงสร้าง (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Anatomy and Structural Biology (International Program)"),
    "mu-sc-phd-biochemistry": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาชีวเคมี (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Biochemistry (International Program)"),
    "mu-sc-phd-biology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาชีววิทยา (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Biology (International Program)"),
    "mu-sc-phd-biotechnology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Biotechnology (International Program)"),
    "mu-sc-phd-chemistry": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเคมี (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Chemistry (International Program)"),
    "mu-sc-phd-materials-sci-eng": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวัสดุศาสตร์และวิศวกรรมวัสดุ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Materials Science and Engineering (International Program)"),
    "mu-sc-phd-mathematics": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาคณิตศาสตร์ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Mathematics (International Program)"),
    "mu-sc-phd-microbio-immunology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาจุลชีววิทยาและวิทยาภูมิคุ้มกัน (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Microbiology and Immunology (International Program)"),
    "mu-sc-phd-molecular-medicine": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเวชศาสตร์ระดับโมเลกุล (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Molecular Medicine (International Program)"),
    "mu-sc-phd-pathobiology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพยาธิชีววิทยา (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Pathobiology (International Program)"),
    "mu-sc-phd-pharmacology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเภสัชวิทยา (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Pharmacology (International Program)"),
    "mu-sc-phd-physics": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาฟิสิกส์ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Physics (International Program)"),
    "mu-sc-phd-physiology": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสรีรวิทยา (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Physiology (International Program)"),
    "mu-sc-phd-polymer-sci-tech": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีพอลิเมอร์ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Polymer Science and Technology (International Program)"),
    "mu-sc-phd-science-innovation": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชานวัตกรรมวิทยาศาสตร์ (หลักสูตรนานาชาติ)", "Doctor of Philosophy Program in Science Innovation (International Program)"),
    "mu-sc-dd-phd-biotech-horticulture-chiba": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพและพืชสวน (หลักสูตรสองปริญญาร่วมกับ มหาวิทยาลัยชิบะ)", "Doctor of Philosophy Program in Biotechnology and Horticulture (Double Degree Program with Chiba University)"),
    "mu-sc-dd-phd-mat-sci-niigata": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวัสดุศาสตร์ (หลักสูตรสองปริญญาร่วมกับ มหาวิทยาลัยนีงะตะ)", "Doctor of Philosophy Program in Materials Science (Double Degree Program with Niigata University)"),
    "mu-sc-dd-phd-microbio-kmu": ("หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาจุลชีววิทยา (หลักสูตรสองปริญญาร่วมกับ มหาวิทยาลัยแพทย์เกาสง)", "Doctor of Philosophy Program in Microbiology (Double Degree Program with Kaohsiung Medical University)")
}

# Missing English titles (20 courses)
MISSING_TITLE_EN_MAP = {
    "bu_m_architecture": "Master of Architecture Program in Architecture",
    "bu_m_brand_communication": "Master of Communication Arts in Brand and Strategic Communication Management",
    "bu_m_business_administration": "Master of Business Administration Program",
    "bu_m_data_marketing": "Master of Communication Arts in Data Marketing and Communication",
    "chula-law-cert-admin-law": "Certificate Program in Administrative Law and Administrative Court Procedure",
    "ku-ms-001": "Master of Science Program in Animal Science",
    "ku-ms-002": "Master of Science Program in Tropical Agriculture",
    "ku-ms-003": "Master of Science Program in Agronomy",
    "ku-ms-004": "Master of Business Administration Program",
    "ku-ms-005": "Master of Accountancy Program",
    "ku-ms-006": "Master of Science Program in Fishery Science and Technology (International Program)",
    "ku-ms-007": "Master of Engineering Program in Computer Engineering",
    "ku-soc-master-community-psychology": "Master of Science Program in Community Psychology",
    "ku-soc-master-io-psychology": "Master of Science Program in Industrial and Organizational Psychology",
    "ku-soc-master-political-science": "Master of Arts Program in Political Science",
    "ku-soc-master-soc-anthro": "Master of Arts Program in Applied Sociology and Anthropology",
    "ku-soc-master-social-admin-dev": "Master of Arts Program in Social Administration and Development",
    "su-ms-4plus1-001": "Master of Arts Program in Tourism, Hotel and Event Management",
    "su-ms-4plus1-002": "Master of Arts Program in Public and Private Management",
    "su-ms-4plus1-003": "Master of Business Administration Program"
}

# Missing Descriptions (8 courses)
MISSING_DESCRIPTION_MAP = {
    "wave36_nu_msc_01": "หลักสูตรมุ่งเน้นการผลิตมหาบัณฑิตที่มีความรู้ความเชี่ยวชาญด้านวิทยาศาสตร์การเกษตร เทคโนโลยีการผลิตพืช การปรับปรุงพันธุ์ และการจัดการเกษตรแม่นยำเพื่อความมั่นคงทางอาหาร",
    "wave36_nu_msc_02": "หลักสูตรมุ่งเน้นการวิจัยและพัฒนาเทคโนโลยีชีวภาพทางการเกษตร การเพาะเลี้ยงเนื้อเยื่อ พันธุวิศวกรรมพืชและสัตว์ และการใช้จุลินทรีย์ในอุตสาหกรรมเกษตร",
    "wave36_nu_msc_03": "หลักสูตรมุ่งพัฒนาองค์ความรู้ขั้นสูงด้านสัตวศาสตร์ โภชนาศาสตร์สัตว์ การปรับปรุงพันธุ์สัตว์ และการจัดการฟาร์มปศุสัตว์อัจฉริยะ",
    "wave36_nu_msc_05": "หลักสูตรสร้างนักวิจัยและผู้เชี่ยวชาญด้านวิทยาศาสตร์สิ่งแวดล้อม การจัดการมลพิษ การประเมินผลกระทบสิ่งแวดล้อม และการฟื้นฟูระบบนิเวศ",
    "wave36_nu_msc_06": "หลักสูตรเน้นการประยุกต์ใช้ระบบสารสนเทศภูมิศาสตร์ (GIS) การสำรวจระยะไกล (Remote Sensing) และเทคโนโลยีภูมิสารสนเทศเพื่อการวางแผนจัดการทรัพยากรและสิ่งแวดล้อม",
    "wave36_nu_msc_07": "หลักสูตรมุ่งบูรณาการศาสตร์ด้านการจัดการทรัพยากรธรรมชาติ การอนุรักษ์ความหลากหลายทางชีวภาพ และการพัฒนาชุมชนอย่างยั่งยืน",
    "wave36_mju_msc_01": "หลักสูตรเน้นการศึกษาและวิจัยด้านเคมีประยุกต์ เคมีผลิตภัณฑ์ธรรมชาติ เคมีวิเคราะห์ และนวัตกรรมวัสดุเคมีเพื่อตอบโจทย์อุตสาหกรรมและเกษตรกรรม",
    "wave36_mju_msc_02": "หลักสูตรเน้นการวิจัยเชิงลึกด้านเทคโนโลยีชีวภาพ เทคโนโลยีการหมัก การใช้ประโยชน์จากจุลินทรีย์ และชีววิทยาระดับโมเลกุลในภาคการเกษตรและอาหาร"
}

# Domain-specific Career Paths Generator for contaminated IT fallback records
def get_domain_career_paths(c: CourseDB) -> list[str]:
    comb = f"{c.faculty_th or ''} {c.title_th or ''} {c.department_th or ''} {c.title_en or ''}".lower()

    if any(k in comb for k in ["พยาบาล", "nurs"]):
        return ["พยาบาลวิชาชีพ", "พยาบาลเฉพาะทาง", "อาจารย์พยาบาล", "ผู้จัดการทางการพยาบาล", "ผู้เชี่ยวชาญการดูแลสุขภาพผู้ป่วย"]
    if any(k in comb for k in ["ทันตแพทย์", "dent"]):
        return ["ทันตแพทย์ทั่วไป", "ทันตแพทย์เฉพาะทาง", "อาจารย์ทันตแพทย์", "นักวิจัยทางทันตกรรมและวัสดุชีวภาพ", "ผู้เชี่ยวชาญด้านสุขภาพช่องปาก"]
    if any(k in comb for k in ["แพทย์", "อายุรศาสตร์", "จักษุ", "medicin", "ตจวิทยา", "โสต ศอ นาสิก", "กุมารเวช"]):
        return ["แพทย์เวชปฏิบัติทั่วไป", "แพทย์เฉพาะทาง", "อาจารย์แพทย์ในสถาบันการแพทย์", "นักวิจัยทางการแพทย์และวิทยาศาสตร์คลินิก", "ผู้เชี่ยวชาญด้านการแพทย์และสาธารณสุข"]
    if any(k in comb for k in ["เภสัช", "pharm"]):
        return ["เภสัชกรโรงพยาบาล", "เภสัชกรชุมชน/ร้านยา", "เภสัชกรอุตสาหการและการผลิตยา", "นักวิจัยและพัฒนายา", "ผู้เชี่ยวชาญด้านเภสัชกรรมคลินิก"]
    if any(k in comb for k in ["สาธารณสุข", "public health", "ระบาดวิทยา", "epidemiol", "สุขศึกษา"]):
        return ["นักวิชาการสาธารณสุข", "นักระบาดวิทยา", "ผู้บริหารและจัดการระบบสุขภาพ", "นักวิจัยด้านสุขภาพชุมชน", "ผู้เชี่ยวชาญด้านการส่งเสริมสุขภาพ"]
    if any(k in comb for k in ["สถาปัตย", "เคหการ", "arch", "landscape", "ผังเมือง"]):
        return ["สถาปนิกวิชาชีพ", "นักออกแบบสถาปัตยกรรมและผังเมือง", "ภูมิสถาปนิก", "นักออกแบบตกแต่งภายใน", "อาจารย์และนักวิจัยด้านสถาปัตยกรรมและการพัฒนาเคหะ"]
    if any(k in comb for k in ["อักษร", "มนุษย", "ภาษา", "วรรณคดี", "บาลี", "human", "linguist"]):
        return ["นักวิชาการและนักวิจัยทางภาษาและวัฒนธรรม", "ล่ามและนักแปลมืออาชีพ", "อาจารย์ผู้สอนภาษาและมนุษยศาสตร์", "บรรณาธิการและนักเขียนสร้างสรรค์", "ผู้เชี่ยวชาญด้านการสื่อสารข้ามวัฒนธรรม"]
    if any(k in comb for k in ["นิติ", "กฎหมาย", "law"]):
        return ["ผู้พิพากษา/พนักงานอัยการ", "ทนายความ", "ที่ปรึกษากฎหมายองค์กร", "นิติกรหน่วยงานรัฐและเอกชน", "อาจารย์และนักวิชาการด้านกฎหมาย"]
    if any(k in comb for k in ["บริหาร", "จัดการ", "การเงิน", "การตลาด", "บัญชี", "business", "manag"]):
        return ["ผู้ประกอบการและผู้บริหารธุรกิจ", "นักวิเคราะห์ธุรกิจและการเงิน", "ผู้เชี่ยวชาญด้านการตลาดและกลยุทธ์", "ผู้จัดการโครงการ", "ที่ปรึกษาด้านการจัดการองค์กร"]
    if any(k in comb for k in ["รัฐศาสตร์", "รัฐประศาสน", "politic", "public admin"]):
        return ["นักวิเคราะห์นโยบายและแผน", "ข้าราชการและพนักงานหน่วยงานรัฐ", "นักการทูตและเจ้าหน้าที่ความสัมพันธ์ระหว่างประเทศ", "นักวิจัยด้านรัฐศาสตร์", "ผู้บริหารงานสาธารณะ"]
    if any(k in comb for k in ["ศึกษาศาสตร์", "ครุศาสตร์", "edu", "สอน"]):
        return ["ครูและอาจารย์ผู้สอน", "นักวิชาการศึกษา", "นักพัฒนาหลักสูตรและเทคโนโลยีการเรียนรู้", "ผู้บริหารสถานศึกษา", "นักวิจัยทางการศึกษา"]
    if any(k in comb for k in ["เกษตร", "ประมง", "สัตว", "agri", "fish"]):
        return ["นักวิชาการเกษตรและการประมง", "ผู้ประกอบการธุรกิจเกษตรอัจฉริยะ", "นักวิจัยและพัฒนาพันธุ์พืช/สัตว์", "ผู้จัดการฟาร์มและมาตรฐานผลผลิต", "ที่ปรึกษาด้านเทคโนโลยีการเกษตร"]
    if any(k in comb for k in ["วิทยาศาสตร์", "เคมี", "ฟิสิกส์", "ชีว", "science", "chem"]):
        return ["นักวิทยาศาสตร์และนักวิจัย", "นักวิเคราะห์ในห้องปฏิบัติการ", "ผู้เชี่ยวชาญด้านการวิจัยและพัฒนาผลิตภัณฑ์", "อาจารย์วิทยาศาสตร์", "ที่ปรึกษาด้านเทคนิคและนวัตกรรม"]

    return [
        "นักวิชาการและผู้เชี่ยวชาญเฉพาะทาง",
        "นักวิจัยและพัฒนานวัตกรรม",
        "อาจารย์และวิทยากรผู้สอน",
        "ที่ปรึกษาโครงการและกลยุทธ์องค์กร",
        "ผู้ปฏิบัติงานระดับวิชาชีพชั้นสูง"
    ]

# ==============================================================================
# Main Autonomous Pipeline Execution
# ==============================================================================

def run_courses_cleaning_pipeline():
    _log("=" * 70)
    _log("Starting Courses Autonomous Cleaning Pipeline (SKILL.state)")
    _log("=" * 70)

    db = SessionLocal()
    embedding_service = EmbeddingService()

    try:
        courses = db.query(CourseDB).options(defer(CourseDB.embedding)).all()
        total_courses = len(courses)
        _log(f"Loaded {total_courses} course records from PostgreSQL.")

        updated_records = []
        stats = defaultdict(int)

        for c in courses:
            modified = False
            mods = []

            # ------------------------------------------------------------------
            # Pass 1: Degree Level & Degree Name Normalization
            # ------------------------------------------------------------------
            # Degree level normalization
            if c.degree_level == "ประกาศนียบัตรบัณฑิต (ชั้นสูง)":
                c.degree_level = "ประกาศนียบัตรบัณฑิตชั้นสูง"
                modified = True
                mods.append("degree_level_unified")
                stats["degree_level_unified"] += 1

            # Degree name population
            if c.id in DEGREE_NAME_FIXES:
                c.degree_name = DEGREE_NAME_FIXES[c.id]
                modified = True
                mods.append("degree_name_fixed")
                stats["degree_name_fixed"] += 1
            elif not (c.degree_name or "").strip():
                # Extract degree name fallback from title_th
                t = c.title_th or ""
                if "ศิลปบัณฑิต" in t:
                    c.degree_name = "ศล.บ."
                elif "ศึกษาศาสตรบัณฑิต" in t:
                    c.degree_name = "ศษ.บ."
                elif "วิทยาศาสตรมหาบัณฑิต" in t:
                    c.degree_name = "วท.ม."
                elif "ปรัชญาดุษฎีบัณฑิต" in t:
                    c.degree_name = "ปร.ด."
                elif "วิศวกรรมศาสตรบัณฑิต" in t:
                    c.degree_name = "วศ.บ."
                elif "บริหารธุรกิจบัณฑิต" in t:
                    c.degree_name = "บธ.บ."
                if c.degree_name:
                    modified = True
                    mods.append("degree_name_auto_extracted")
                    stats["degree_name_auto_extracted"] += 1

            # ------------------------------------------------------------------
            # Pass 2: Faculty Normalization & Typos
            # ------------------------------------------------------------------
            # MFU English faculties
            if c.faculty_th in MFU_FACULTY_MAP:
                c.faculty_th = MFU_FACULTY_MAP[c.faculty_th]
                modified = True
                mods.append("mfu_faculty_translated")
                stats["mfu_faculty_translated"] += 1

            # Unspecified faculties
            if c.id in UNSPECIFIED_FACULTY_FIXES:
                c.faculty_th = UNSPECIFIED_FACULTY_FIXES[c.id]
                modified = True
                mods.append("unspecified_faculty_fixed")
                stats["unspecified_faculty_fixed"] += 1

            # STOU Typo
            if c.faculty_th == "สาขาวิชมนุษยนิเวศศาสตร์":
                c.faculty_th = "สาขาวิชามนุษยนิเวศศาสตร์"
                modified = True
                mods.append("stou_faculty_typo_fixed")
                stats["stou_faculty_typo_fixed"] += 1

            # ------------------------------------------------------------------
            # Pass 3: Course Title & Language Hygiene
            # ------------------------------------------------------------------
            # Double prefix
            if "หลักสูตรหลักสูตร" in (c.title_th or ""):
                c.title_th = c.title_th.replace("หลักสูตรหลักสูตร", "หลักสูตร")
                modified = True
                mods.append("double_prefix_fixed")
                stats["double_prefix_fixed"] += 1

            # Non-breaking space
            if " " in (c.title_th or ""):
                c.title_th = c.title_th.replace(" ", " ")
                modified = True
                mods.append("nbsp_fixed")
                stats["nbsp_fixed"] += 1

            # Explicit Title Mapping (CU Arch, Sci, Med, SUT, Rama, zero-Thai)
            if c.id in TITLE_FIXES:
                new_th, new_en = TITLE_FIXES[c.id]
                c.title_th = new_th
                if new_en:
                    c.title_en = new_en
                modified = True
                mods.append("explicit_title_fixed")
                stats["explicit_title_fixed"] += 1
            elif c.id in MU_SC_MSC_MAP:
                new_th, new_en = MU_SC_MSC_MAP[c.id]
                c.title_th = new_th
                c.title_en = new_en
                modified = True
                mods.append("mu_sc_msc_fixed")
                stats["mu_sc_msc_fixed"] += 1
            elif c.id in MU_SC_PHD_MAP:
                new_th, new_en = MU_SC_PHD_MAP[c.id]
                c.title_th = new_th
                c.title_en = new_en
                modified = True
                mods.append("mu_sc_phd_fixed")
                stats["mu_sc_phd_fixed"] += 1

            # Typos in title_th
            if "สาชาวิชา" in (c.title_th or ""):
                c.title_th = c.title_th.replace("สาชาวิชา", "สาขาวิชา")
                modified = True
                mods.append("sachawisha_typo_fixed")
                stats["sachawisha_typo_fixed"] += 1

            if "บัณทิต" in (c.title_th or ""):
                c.title_th = c.title_th.replace("บัณทิต", "บัณฑิต")
                modified = True
                mods.append("bandhit_typo_fixed")
                stats["bandhit_typo_fixed"] += 1

            # Clean any stray closing parenthesis in remaining mu-sc-phd
            if c.title_th and c.title_th.count(")") > c.title_th.count("("):
                # replace stray ) before (International Program
                c.title_th = re.sub(r"\)\s*(\(International Program|\(Special Program)", r" \1", c.title_th)
                modified = True
                mods.append("unbalanced_paren_fixed")
                stats["unbalanced_paren_fixed"] += 1

            # Fix unclosed parenthesis at end of title_th
            if c.title_th and c.title_th.count("(") > c.title_th.count(")"):
                c.title_th = c.title_th.strip() + ")"
                modified = True
                mods.append("unclosed_paren_fixed")
                stats["unclosed_paren_fixed"] += 1

            # Missing title_en
            if c.id in MISSING_TITLE_EN_MAP:
                c.title_en = MISSING_TITLE_EN_MAP[c.id]
                modified = True
                mods.append("missing_title_en_fixed")
                stats["missing_title_en_fixed"] += 1

            # Missing description
            if c.id in MISSING_DESCRIPTION_MAP:
                c.description = MISSING_DESCRIPTION_MAP[c.id]
                modified = True
                mods.append("missing_description_fixed")
                stats["missing_description_fixed"] += 1

            # ------------------------------------------------------------------
            # Pass 4: Tuition, Duration, and Credits Normalization
            # ------------------------------------------------------------------
            # Total credits formatting (bare number -> N หน่วยกิต)
            if c.total_credits and re.match(r"^\d+$", str(c.total_credits).strip()):
                c.total_credits = f"{str(c.total_credits).strip()} หน่วยกิต"
                modified = True
                mods.append("credits_formatted")
                stats["credits_formatted"] += 1

            # Duration formatting (ensure 'ปี')
            if c.duration_years and re.match(r"^\d+(\.\d+)?$", str(c.duration_years).strip()):
                c.duration_years = f"{str(c.duration_years).strip()} ปี"
                modified = True
                mods.append("duration_formatted")
                stats["duration_formatted"] += 1

            # THB in tuition
            if c.tuition_per_semester and "THB" in str(c.tuition_per_semester):
                c.tuition_per_semester = str(c.tuition_per_semester).replace("THB", "บาท").strip()
                modified = True
                mods.append("tuition_sem_thb_fixed")
                stats["tuition_sem_thb_fixed"] += 1

            if c.tuition_total and "THB" in str(c.tuition_total):
                c.tuition_total = str(c.tuition_total).replace("THB", "บาท").strip()
                modified = True
                mods.append("tuition_total_thb_fixed")
                stats["tuition_total_thb_fixed"] += 1

            # CMU (and any course) tuition_total calculation if NULL
            if c.tuition_total is None or c.tuition_total == "":
                sem_str = str(c.tuition_per_semester or "").strip()
                dur_str = str(c.duration_years or "").strip()

                sem_num_match = re.search(r"([\d,]+)", sem_str)
                dur_num_match = re.search(r"(\d+(\.\d+)?)", dur_str)

                if sem_num_match and sem_str != "ไม่ระบุ" and dur_num_match:
                    sem_val = int(sem_num_match.group(1).replace(",", ""))
                    dur_years = float(dur_num_match.group(1))
                    total_val = int(sem_val * (dur_years * 2))
                    c.tuition_total = f"{total_val:,} บาท"
                    modified = True
                    mods.append("tuition_total_calculated")
                    stats["tuition_total_calculated"] += 1
                else:
                    c.tuition_total = "ไม่ระบุ"
                    modified = True
                    mods.append("tuition_total_marked_unspecified")
                    stats["tuition_total_marked_unspecified"] += 1

            # ------------------------------------------------------------------
            # Pass 5: Semantic Tag & Career Path Realignment
            # ------------------------------------------------------------------
            it_career_signature = ["Software Engineer", "Data Scientist / AI Engineer", "System Analyst & Architect", "Cybersecurity Specialist", "นักวิชาการ/นักวิจัยคอมพิวเตอร์"]
            if c.career_paths == it_career_signature:
                comb = f"{c.faculty_th or ''} {c.title_th or ''} {c.department_th or ''}".lower()
                is_it = any(k in comb for k in ["คอมพิวเตอร์", "computer", "software", "ซอฟต์แวร์", "สารสนเทศ", "information", "it", "ดิจิทัล", "digital", "ไซเบอร์", "cyber", "ไอที", "data", "ปัญญาประดิษฐ์", "ai", "cpe", "iot"])
                if not is_it:
                    c.career_paths = get_domain_career_paths(c)
                    modified = True
                    mods.append("career_paths_realigned")
                    stats["career_paths_realigned"] += 1

            # ------------------------------------------------------------------
            # Pass 6: Embedding Text & Vector Synchronization
            # ------------------------------------------------------------------
            if modified:
                highlights_str = " ".join(c.curriculum_highlights or [])
                careers_str = " ".join(c.career_paths or [])
                tags_str = " ".join(c.tags or [])
                c.embedding_text = (
                    f"{c.title_th} {c.title_en} {c.degree_level} {c.degree_name} {c.faculty_th} "
                    f"{c.department_th or ''} {c.university_th} {c.university or ''} {c.description or ''} "
                    f"{highlights_str} {careers_str} {tags_str}"
                ).strip()

                # Ensure valid embedding vector (Pillar 3 Circuit Breaker)
                if c.embedding is None:
                    try:
                        vec = embedding_service.get_embedding(c.embedding_text)
                        if vec and len(vec) == 768:
                            c.embedding = vec
                            stats["embeddings_revectorized"] += 1
                        else:
                            c.embedding = None  # NULL: re-embed via embed_missing.py
                            stats["embeddings_circuit_breaker"] += 1
                    except Exception:
                        c.embedding = None  # NULL: re-embed via embed_missing.py
                        stats["embeddings_circuit_breaker"] += 1

                updated_records.append({
                    "id": c.id,
                    "title_th": c.title_th,
                    "title_en": c.title_en,
                    "degree_level": c.degree_level,
                    "degree_name": c.degree_name,
                    "faculty_th": c.faculty_th,
                    "tuition_per_semester": c.tuition_per_semester,
                    "tuition_total": c.tuition_total,
                    "total_credits": c.total_credits,
                    "duration_years": c.duration_years,
                    "mods": mods
                })

        # Commit changes to PostgreSQL
        db.commit()
        _log(f"✅ Successfully committed changes for {len(updated_records)} course records.")

        # ------------------------------------------------------------------
        # Pillar 5: Disk Checkpointing
        # ------------------------------------------------------------------
        checkpoint_dir = ROOT / "data" / "agent_states"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / "clean_courses_snapshot.json"

        checkpoint_data = {
            "timestamp": time.time(),
            "total_courses": total_courses,
            "updated_count": len(updated_records),
            "stats": dict(stats),
            "sample_updates": updated_records[:50]
        }

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        _log(f"💾 Checkpoint saved to: {checkpoint_path}")
        _log("\n=== Summary of Cleaning Statistics ===")
        for k, v in sorted(stats.items()):
            _log(f"  {k}: {v}")

    except Exception as e:
        db.rollback()
        _log(f"❌ Error during course cleaning: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_courses_cleaning_pipeline()
