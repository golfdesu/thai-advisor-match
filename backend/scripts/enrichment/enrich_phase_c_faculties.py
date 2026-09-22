# -*- coding: utf-8 -*-
"""
Phase C Faculty Enrichment Pipeline (Regional Comprehensive & Specialized Universities)
Targets:
- มหาวิทยาลัยสงขลานครินทร์ (PSU)
- มหาวิทยาลัยศรีนครินทรวิโรฒ (SWU)
- มหาวิทยาลัยศิลปากร (SU)
- มหาวิทยาลัยบูรพา (BUU)
- มหาวิทยาลัยแม่โจ้ (MJU)

Operations:
1. Pass 1: Local Curated Rosters Matching (buu_su_mfu, psu_nu, mju_tu, wave22-26 exports)
2. Pass 2: Calibrated University Academic Domain & Research Topic Taxonomy Mapping
3. Database Batch Updates: Loss-free in-place enrichment (only empty faculty_th/faculty/department_th)
4. Checkpoint: Saved to backend/data/agent_states/roster_enrich_phase_c_snapshot.json
Complies with AGENTS.md Section 9 Quality Invariants.
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from collections import defaultdict
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "roster_enrich_phase_c_snapshot.json"

PHASE_C_UNIVERSITIES = [
    "มหาวิทยาลัยสงขลานครินทร์",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "มหาวิทยาลัยศิลปากร",
    "มหาวิทยาลัยบูรพา",
    "มหาวิทยาลัยแม่โจ้"
]

FACULTY_EN_MAP = {
    # PSU
    "คณะแพทยศาสตร์": "Faculty of Medicine",
    "คณะทันตแพทยศาสตร์": "Faculty of Dentistry",
    "คณะเภสัชศาสตร์": "Faculty of Pharmaceutical Sciences",
    "คณะพยาบาลศาสตร์": "Faculty of Nursing",
    "คณะการแพทย์แผนไทย": "Faculty of Traditional Thai Medicine",
    "คณะทรัพยากรธรรมชาติ": "Faculty of Natural Resources",
    "คณะอุตสาหกรรมเกษตร": "Faculty of Agro-Industry",
    "คณะวิทยาการจัดการ": "Faculty of Management Sciences",
    "คณะวิศวกรรมศาสตร์": "Faculty of Engineering",
    "คณะวิทยาศาสตร์": "Faculty of Science",
    "คณะนิติศาสตร์": "Faculty of Law",
    "คณะศึกษาศาสตร์ (วิทยาเขตปัตตานี)": "Faculty of Education (Pattani Campus)",
    "คณะมนุษยศาสตร์และสังคมศาสตร์": "Faculty of Humanities and Social Sciences",
    "คณะสถาปัตยกรรมศาสตร์ (วิทยาเขตตรัง)": "Faculty of Architecture (Trang Campus)",
    "วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)": "College of Computing (Phuket Campus)",
    "คณะการบริการและการท่องเที่ยว (วิทยาเขตภูเก็ต)": "Faculty of Hospitality and Tourism (Phuket Campus)",

    # SWU
    "คณะกายภาพบำบัด": "Faculty of Physical Therapy",
    "คณะศึกษาศาสตร์": "Faculty of Education",
    "คณะบริหารธุรกิจเพื่อสังคม": "Faculty of Business Administration for Society",
    "คณะมนุษยศาสตร์": "Faculty of Humanities",
    "คณะสังคมศาสตร์": "Faculty of Social Sciences",
    "คณะศิลปกรรมศาสตร์": "Faculty of Fine Arts",
    "วิทยาลัยนวัตกรรมสื่อสารสังคม": "College of Social Communication Innovation",

    # SU (Silpakorn)
    "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม": "Faculty of Engineering and Industrial Technology",
    "คณะสถาปัตยกรรมศาสตร์": "Faculty of Architecture",
    "คณะเทคโนโลยีสารสนเทศและการสื่อสาร": "Faculty of Information and Communication Technology",
    "คณะโบราณคดี": "Faculty of Archaeology",
    "คณะมัณฑนศิลป์": "Faculty of Decorative Arts",
    "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์": "Faculty of Painting, Sculpture and Graphic Arts",
    "คณะดุริยางคศาสตร์": "Faculty of Music",
    "คณะอักษรศาสตร์": "Faculty of Arts",

    # BUU (Burapha)
    "คณะสหเวชศาสตร์": "Faculty of Allied Health Sciences",
    "คณะวิทยาการสารสนเทศ": "Faculty of Informatics",
    "คณะโลจิสติกส์": "Faculty of Logistics",
    "คณะเทคโนโลยีทางทะเล": "Faculty of Marine Technology",
    "คณะการจัดการและการท่องเที่ยว": "Faculty of Management and Tourism",
    "คณะสาธารณสุขศาสตร์": "Faculty of Public Health",

    # MJU (Maejo)
    "คณะผลิตกรรมการเกษตร": "Faculty of Agricultural Production",
    "คณะสัตวศาสตร์และเทคโนโลยี": "Faculty of Animal Science and Technology",
    "คณะเทคโนโลยีการประมงและทรัพยากรทางน้ำ": "Faculty of Fisheries Technology and Aquatic Resources",
    "คณะวิศวกรรมและอุตสาหกรรมเกษตร": "Faculty of Engineering and Agro-Industry",
    "วิทยาลัยพลังงานทดแทน": "School of Renewable Energy",
    "คณะบริหารธุรกิจ": "Faculty of Business Administration",
    "คณะพัฒนาการท่องเที่ยว": "School of Tourism Development",
    "คณะเศรษฐศาสตร์": "Faculty of Economics",
    "คณะศิลปศาสตร์": "Faculty of Liberal Arts",
}

# Calibrated domain taxonomy for Phase C
DOMAIN_TAXONOMY = [
    # Dentistry
    ("ทันตแพทย์", [
        "oral and maxillofacial", "dental", "tooth", "teeth", "orthodontic", "periodont",
        "endodont", "prosthodont", "caries", "maxillofacial", "dentistry", "implant dentistry"
    ]),
    # Veterinary & Animal Science
    ("สัตวแพทย์และสัตว์ศาสตร์", [
        "veterinary", "canine", "feline", "bovine", "porcine", "equine", "animal disease",
        "zoonotic", "swine", "poultry disease", "animal nutrition", "poultry nutrition",
        "animal science", "livestock", "meat and animal", "bee products"
    ]),
    # Pharmacy
    ("เภสัชศาสตร์", [
        "pharmac", "drug delivery", "drug design", "pharmaceut", "dosage", "pharmacokinetics",
        "pharmacology", "bioactive peptides", "medicinal chemistry", "herbal medicine",
        "phytochemistry", "formulation development", "phytochemical", "essential oil"
    ]),
    # Fisheries & Aquatic Resources
    ("ประมงและทรัพยากรทางน้ำ", [
        "fisheries", "aquaculture", "shrimp culture", "tilapia", "marine biology",
        "aquatic animal", "fish nutrition", "fish disease", "algal culture", "marine organism",
        "marine science", "oceanography", "marine ecology", "aquatic resource"
    ]),
    # Agriculture & Plant Science
    ("เกษตรและพืชศาสตร์", [
        "agronomy", "crop science", "soil science", "horticulture", "plant pathology",
        "plant breeding", "entomology", "rice production", "paddy soil", "fertilizer application",
        "postharvest", "crop production", "seed technology", "plant pathogen", "plant tissue",
        "plant-microbe", "plant and animal", "fungal disease", "pollutant removal",
        "oil palm production", "remote sensing in agriculture"
    ]),
    # Agro-Industry & Food Technology
    ("อุตสาหกรรมเกษตรและอาหาร", [
        "food science", "food technology", "food processing", "fermentation technology",
        "food packaging", "shelf-life extension", "food sensory", "food safety", "bioprocess",
        "agro-industry", "food biotechnology", "food composition", "food drying"
    ]),
    # Architecture & Design
    ("สถาปัตยกรรมและมัณฑนศิลป์", [
        "architecture", "urban planning", "built environment", "landscape design",
        "sustainable building", "spatial design", "interior architecture", "decorative arts",
        "interior design", "visual arts", "product design"
    ]),
    # Archaeology & Heritage (SU specialty)
    ("โบราณคดีและประวัติศาสตร์", [
        "archaeology", "archaeological", "epigraphy", "palaeography", "prehistoric",
        "ancient history", "cultural heritage", "historical archaeology", "anthropology"
    ]),
    # Logistics & Supply Chain (BUU specialty)
    ("โลจิสติกส์และการขนส่ง", [
        "logistics", "supply chain", "freight transport", "maritime transport", "port management",
        "warehouse", "transportation system", "inventory management"
    ]),
    # Tourism & Hospitality
    ("การท่องเที่ยวและการบริการ", [
        "tourism", "hospitality", "hotel management", "destination marketing", "ecotourism",
        "tourist behavior", "diverse aspects of tourism"
    ]),
    # Law (PSU)
    ("นิติศาสตร์", [
        "legal and regulatory", "law and legal", "criminal law", "civil law", "human rights law",
        "constitutional law"
    ]),
    # Renewable Energy (MJU specialty)
    ("พลังงานทดแทน", [
        "biofuel", "biodiesel", "biogas", "biomass conversion", "solar cell", "renewable energy",
        "anaerobic digestion", "thermochemical biomass"
    ]),
    # Computing & IT
    ("เทคโนโลยีสารสนเทศและคอมพิวเตอร์", [
        "computer science", "artificial intelligence", "machine learning", "deep learning",
        "neural network", "computer vision", "natural language processing", "data science",
        "cybersecurity", "software engineering", "cloud computing", "information technology",
        "information systems", "iot", "internet of things", "big data", "wireless sensor"
    ]),
    # Engineering & Applied Technology
    ("วิศวกรรมศาสตร์", [
        "engineering", "robotics", "power system", "smart grid", "additive manufacturing",
        "fluid dynamics", "nanotechnology", "telecommunication", "structural mechanics",
        "concrete structure", "mechanical engineering", "chemical engineering", "electrical engineering",
        "civil engineering", "geotechnical", "thermal engineering", "control system",
        "membrane separation", "military technology", "aluminum alloy", "piezoelectric",
        "advanced ceramic", "concrete reinforcement", "cement materials", "metallurgy",
        "battery materials", "flood risk assessment", "hydrology"
    ]),
    # Medicine & Healthcare
    ("แพทย์และคลินิก", [
        "surgery", "surgical", "clinical", "oncology", "cancer", "tumor", "cardiovascular",
        "cardiology", "pediatric", "radiology", "pathology", "neurology", "anesthesia",
        "orthopedic", "ophthalmology", "dermatology", "covid-19", "sars-cov-2", "retinal",
        "macular", "psychiatry", "respiratory", "pulmonary", "stroke", "leukemia",
        "chemotherapy", "intensive care", "infectious diseases", "epidemiology", "endoscopy",
        "maternal and child health", "mosquito-borne", "parasite", "hemoglobinopath", "disease",
        "disorder", "health", "vital sign monitoring"
    ]),
    # Nursing
    ("พยาบาลศาสตร์", [
        "nursing", "nurse", "patient care", "palliative care", "elderly care", "gerontological",
        "clinical nursing", "nursing education", "critical care nursing"
    ]),
    # Physical Therapy & Allied Health
    ("กายภาพบำบัดและสหเวชศาสตร์", [
        "physical therapy", "physiotherapy", "rehabilitation", "biomechanics", "ergonomics",
        "gait analysis", "medical technology", "allied health", "occupational therapy"
    ]),
    # Science & Fundamental Research
    ("วิทยาศาสตร์", [
        "crystallography", "x-ray diffraction", "air quality", "chemical synthesis",
        "organic chemistry", "inorganic chemistry", "catalysis", "quantum", "optics",
        "slime mold", "myxomycetes", "biodiversity", "polymer", "biochemistry", "microbiology",
        "genetics", "molecular biology", "analytical chemistry", "materials science", "physics",
        "mathematics", "applied mathematics", "statistics", "geology", "mineralogy",
        "heavy metals", "zno doping", "spectroscopy", "chemometric", "biosensing", "pollutant",
        "genomics and phylogenetic", "wetland ecosystem"
    ]),
    # Economics & Business Management
    ("เศรษฐศาสตร์และการบริหาร", [
        "economics", "macroeconomic", "microeconomic", "econometric", "monetary policy",
        "fiscal policy", "international trade", "economic growth", "business administration",
        "marketing", "finance", "accounting", "human resource management",
        "customer service quality", "job satisfaction"
    ]),
    # Education & Pedagogy
    ("การศึกษาและครุศาสตร์", [
        "education", "curriculum", "pedagogy", "educational technology", "stem education",
        "teaching methods", "student learning", "learning achievement", "higher education",
        "efl/esl", "language learning", "language teaching", "second language acquisition"
    ]),
    # Humanities & Social Sciences
    ("มนุษยศาสตร์และสังคมศาสตร์", [
        "linguistics", "translation", "literature", "english language", "sociology",
        "political science", "public administration", "international relations", "philosophy",
        "literary studies", "sociopolitical", "southeast asian sociopolitical"
    ]),
]


def clean_name(n: str) -> str:
    if not n:
        return ""
    for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "นายแพทย์", "พญ.", "นพ.", "ทพ.", "ทพญ.", "สพ.ญ.", "น.สพ."]:
        if n.startswith(t):
            n = n[len(t):].strip()
    return re.sub(r"\s+", "", n)


def get_target_faculty(uni: str, domain_key: str) -> str:
    if uni == "มหาวิทยาลัยสงขลานครินทร์":
        mapping = {
            "ทันตแพทย์": "คณะทันตแพทยศาสตร์",
            "สัตวแพทย์และสัตว์ศาสตร์": "คณะทรัพยากรธรรมชาติ",
            "เภสัชศาสตร์": "คณะเภสัชศาสตร์",
            "ประมงและทรัพยากรทางน้ำ": "คณะทรัพยากรธรรมชาติ",
            "เกษตรและพืชศาสตร์": "คณะทรัพยากรธรรมชาติ",
            "อุตสาหกรรมเกษตรและอาหาร": "คณะอุตสาหกรรมเกษตร",
            "สถาปัตยกรรมและมัณฑนศิลป์": "คณะสถาปัตยกรรมศาสตร์ (วิทยาเขตตรัง)",
            "การท่องเที่ยวและการบริการ": "คณะการบริการและการท่องเที่ยว (วิทยาเขตภูเก็ต)",
            "นิติศาสตร์": "คณะนิติศาสตร์",
            "เทคโนโลยีสารสนเทศและคอมพิวเตอร์": "วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)",
            "วิศวกรรมศาสตร์": "คณะวิศวกรรมศาสตร์",
            "พลังงานทดแทน": "คณะวิศวกรรมศาสตร์",
            "แพทย์และคลินิก": "คณะแพทยศาสตร์",
            "พยาบาลศาสตร์": "คณะพยาบาลศาสตร์",
            "กายภาพบำบัดและสหเวชศาสตร์": "คณะการแพทย์แผนไทย",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "เศรษฐศาสตร์และการบริหาร": "คณะวิทยาการจัดการ",
            "การศึกษาและครุศาสตร์": "คณะศึกษาศาสตร์ (วิทยาเขตปัตตานี)",
            "มนุษยศาสตร์และสังคมศาสตร์": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        }
        return mapping.get(domain_key, "คณะวิทยาศาสตร์")

    elif uni == "มหาวิทยาลัยศรีนครินทรวิโรฒ":
        mapping = {
            "ทันตแพทย์": "คณะทันตแพทยศาสตร์",
            "สัตวแพทย์และสัตว์ศาสตร์": "คณะวิทยาศาสตร์",
            "เภสัชศาสตร์": "คณะเภสัชศาสตร์",
            "ประมงและทรัพยากรทางน้ำ": "คณะวิทยาศาสตร์",
            "เกษตรและพืชศาสตร์": "คณะวิทยาศาสตร์",
            "อุตสาหกรรมเกษตรและอาหาร": "คณะวิทยาศาสตร์",
            "สถาปัตยกรรมและมัณฑนศิลป์": "คณะศิลปกรรมศาสตร์",
            "การท่องเที่ยวและการบริการ": "คณะสังคมศาสตร์",
            "นิติศาสตร์": "คณะสังคมศาสตร์",
            "เทคโนโลยีสารสนเทศและคอมพิวเตอร์": "วิทยาลัยนวัตกรรมสื่อสารสังคม",
            "วิศวกรรมศาสตร์": "คณะวิศวกรรมศาสตร์",
            "พลังงานทดแทน": "คณะวิศวกรรมศาสตร์",
            "แพทย์และคลินิก": "คณะแพทยศาสตร์",
            "พยาบาลศาสตร์": "คณะพยาบาลศาสตร์",
            "กายภาพบำบัดและสหเวชศาสตร์": "คณะกายภาพบำบัด",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "เศรษฐศาสตร์และการบริหาร": "คณะบริหารธุรกิจเพื่อสังคม",
            "การศึกษาและครุศาสตร์": "คณะศึกษาศาสตร์",
            "มนุษยศาสตร์และสังคมศาสตร์": "คณะมนุษยศาสตร์",
        }
        return mapping.get(domain_key, "คณะวิทยาศาสตร์")

    elif uni == "มหาวิทยาลัยศิลปากร":
        mapping = {
            "ทันตแพทย์": "คณะวิทยาศาสตร์",
            "เภสัชศาสตร์": "คณะเภสัชศาสตร์",
            "สถาปัตยกรรมและมัณฑนศิลป์": "คณะสถาปัตยกรรมศาสตร์",
            "โบราณคดีและประวัติศาสตร์": "คณะโบราณคดี",
            "เทคโนโลยีสารสนเทศและคอมพิวเตอร์": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
            "วิศวกรรมศาสตร์": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
            "พลังงานทดแทน": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
            "แพทย์และคลินิก": "คณะเภสัชศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "เศรษฐศาสตร์และการบริหาร": "คณะวิทยาการจัดการ",
            "การศึกษาและครุศาสตร์": "คณะศึกษาศาสตร์",
            "มนุษยศาสตร์และสังคมศาสตร์": "คณะอักษรศาสตร์",
            "การท่องเที่ยวและการบริการ": "คณะวิทยาการจัดการ",
        }
        return mapping.get(domain_key, "คณะวิทยาศาสตร์")

    elif uni == "มหาวิทยาลัยบูรพา":
        mapping = {
            "ทันตแพทย์": "คณะแพทยศาสตร์",
            "เภสัชศาสตร์": "คณะเภสัชศาสตร์",
            "ประมงและทรัพยากรทางน้ำ": "คณะเทคโนโลยีทางทะเล",
            "โลจิสติกส์และการขนส่ง": "คณะโลจิสติกส์",
            "เทคโนโลยีสารสนเทศและคอมพิวเตอร์": "คณะวิทยาการสารสนเทศ",
            "วิศวกรรมศาสตร์": "คณะวิศวกรรมศาสตร์",
            "พลังงานทดแทน": "คณะวิศวกรรมศาสตร์",
            "แพทย์และคลินิก": "คณะแพทยศาสตร์",
            "พยาบาลศาสตร์": "คณะพยาบาลศาสตร์",
            "กายภาพบำบัดและสหเวชศาสตร์": "คณะสหเวชศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "เศรษฐศาสตร์และการบริหาร": "คณะการจัดการและการท่องเที่ยว",
            "การท่องเที่ยวและการบริการ": "คณะการจัดการและการท่องเที่ยว",
            "การศึกษาและครุศาสตร์": "คณะศึกษาศาสตร์",
            "มนุษยศาสตร์และสังคมศาสตร์": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        }
        return mapping.get(domain_key, "คณะวิทยาศาสตร์")

    elif uni == "มหาวิทยาลัยแม่โจ้":
        mapping = {
            "สัตวแพทย์และสัตว์ศาสตร์": "คณะสัตวศาสตร์และเทคโนโลยี",
            "ประมงและทรัพยากรทางน้ำ": "คณะเทคโนโลยีการประมงและทรัพยากรทางน้ำ",
            "เกษตรและพืชศาสตร์": "คณะผลิตกรรมการเกษตร",
            "อุตสาหกรรมเกษตรและอาหาร": "คณะวิศวกรรมและอุตสาหกรรมเกษตร",
            "วิศวกรรมศาสตร์": "คณะวิศวกรรมและอุตสาหกรรมเกษตร",
            "พลังงานทดแทน": "วิทยาลัยพลังงานทดแทน",
            "พยาบาลศาสตร์": "คณะพยาบาลศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "เศรษฐศาสตร์และการบริหาร": "คณะบริหารธุรกิจ",
            "การท่องเที่ยวและการบริการ": "คณะพัฒนาการท่องเที่ยว",
            "มนุษยศาสตร์และสังคมศาสตร์": "คณะศิลปศาสตร์",
        }
        return mapping.get(domain_key, "คณะผลิตกรรมการเกษตร")

    return "คณะวิทยาศาสตร์"


def run_phase_c_enrichment():
    print("=" * 80)
    print("🚀 STARTING PHASE C FACULTY ENRICHMENT (PSU, SWU, SU, BUU, MJU)")
    print("=" * 80)
    start_time = time.time()
    db = SessionLocal()

    try:
        # 1. Load missing faculties
        missing_rows = db.execute(text("""
            SELECT id, full_name_th, university_th, first_name, last_name, email, research_interests
            FROM faculties
            WHERE university_th IN :unis
              AND (faculty_th IS NULL OR trim(faculty_th) = :empty)
        """), {"unis": tuple(PHASE_C_UNIVERSITIES), "empty": ""}).fetchall()

        total_missing = len(missing_rows)
        print(f"📊 Total Phase C faculty missing faculty_th: {total_missing:,}")

        missing_by_name = defaultdict(list)
        missing_by_id = {}
        for r in missing_rows:
            fid, name_th, uni, fn, ln, mail, interests = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
            cn = clean_name(name_th)
            if cn:
                missing_by_name[(uni, cn)].append(fid)
            missing_by_id[fid] = {
                "uni": uni,
                "name_th": name_th,
                "fn": fn,
                "ln": ln,
                "email": mail,
                "interests": interests or []
            }

        updates = {}

        # --- PASS 1: Local Curated Rosters Matching ---
        print("\n--- Pass 1: Matching against Phase C Curated Rosters ---")
        pass1_count = 0
        raw_files = [
            CHECKPOINT_DIR / "buu_su_mfu_extracted.json",
            CHECKPOINT_DIR / "psu_nu_extracted.json",
            CHECKPOINT_DIR / "mju_tu_extracted.json",
            CHECKPOINT_DIR / "recovered_emails_tu_mahidol_su.json",
        ]

        for rf in raw_files:
            if not rf.exists():
                continue
            try:
                data = json.loads(rf.read_text(encoding="utf-8"))
                items = data if isinstance(data, list) else (data.get("faculties") or data.get("data") or list(data.values()))
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    fac_th = item.get("faculty_th") or item.get("faculty")
                    if not fac_th:
                        continue
                    uni = item.get("university_th") or item.get("university")
                    if uni not in PHASE_C_UNIVERSITIES:
                        continue
                    name = item.get("full_name_th") or item.get("thai_name") or f"{item.get('first_name','')} {item.get('last_name','')}".strip()
                    cn = clean_name(name)
                    if (uni, cn) in missing_by_name:
                        for target_fid in missing_by_name[(uni, cn)]:
                            if target_fid not in updates:
                                updates[target_fid] = {
                                    "faculty_th": fac_th,
                                    "faculty": FACULTY_EN_MAP.get(fac_th, item.get("faculty") or ("Faculty of " + fac_th.replace("คณะ", ""))),
                                    "department_th": item.get("department_th")
                                }
                                pass1_count += 1
            except Exception:
                pass

        # Scan wave22-26 export files
        export_files = list(CHECKPOINT_DIR.glob("wave2[2-6]_*_export.py"))
        for ef in export_files:
            try:
                content = ef.read_text(encoding="utf-8")
                # Parse EXTRACTED_FACULTIES entries via regex
                pattern = re.compile(r"\{\s*\"id\":\s*\"[^\"]+\",\s*\"university\":\s*\"[^\"]+\",\s*\"university_th\":\s*\"([^\"]+)\",\s*\"faculty\":\s*\"([^\"]+)\",\s*\"faculty_th\":\s*\"([^\"]+)\",\s*\"department\":\s*\"[^\"]*\",\s*\"department_th\":\s*\"([^\"]*)\",.*?\"full_name_th\":\s*\"([^\"]+)\"", re.DOTALL)
                for m in pattern.finditer(content):
                    uni_th, fac_en, fac_th, dept_th, fn_th = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
                    if uni_th in PHASE_C_UNIVERSITIES:
                        cn = clean_name(fn_th)
                        if (uni_th, cn) in missing_by_name:
                            for target_fid in missing_by_name[(uni_th, cn)]:
                                if target_fid not in updates:
                                    updates[target_fid] = {
                                        "faculty_th": fac_th,
                                        "faculty": fac_en or FACULTY_EN_MAP.get(fac_th, "Faculty of " + fac_th.replace("คณะ", "")),
                                        "department_th": dept_th if dept_th else None
                                    }
                                    pass1_count += 1
            except Exception:
                pass

        print(f"   [Pass 1] Matched {pass1_count:,} faculties from curated Phase C datasets.")

        # --- PASS 2: Calibrated Academic Domain Taxonomy Mapping ---
        print("\n--- Pass 2: Calibrated University Academic Domain Taxonomy Mapping ---")
        pass2_count = 0
        for fid, info in missing_by_id.items():
            if fid in updates:
                continue
            interests_str = " ".join(info["interests"]).lower()
            if not interests_str:
                continue

            uni = info["uni"]
            matched_domain = None

            for domain_name, keywords in DOMAIN_TAXONOMY:
                if any(kw in interests_str for kw in keywords):
                    matched_domain = domain_name
                    break

            if matched_domain:
                target_fac = get_target_faculty(uni, matched_domain)
                updates[fid] = {
                    "faculty_th": target_fac,
                    "faculty": FACULTY_EN_MAP.get(target_fac, "Faculty of " + target_fac.replace("คณะ", "")),
                    "department_th": None
                }
                pass2_count += 1

        print(f"   [Pass 2] Classified and mapped {pass2_count:,} faculties via domain taxonomy.")

        # --- DATABASE BATCH COMMIT ---
        total_enriched = len(updates)
        print(f"\n💾 Executing loss-free database updates for {total_enriched:,} faculty records...")

        batch_size = 2000
        items_list = list(updates.items())
        for i in range(0, total_enriched, batch_size):
            chunk = items_list[i : i + batch_size]
            for fid, data in chunk:
                db.execute(text("""
                    UPDATE faculties
                    SET faculty_th = :fth,
                        faculty = COALESCE(faculty, :fen),
                        department_th = COALESCE(department_th, :dth)
                    WHERE id = :fid
                      AND (faculty_th IS NULL OR trim(faculty_th) = :empty)
                """), {
                    "fid": fid,
                    "fth": data["faculty_th"],
                    "fen": data["faculty"],
                    "dth": data.get("department_th"),
                    "empty": ""
                })
            db.commit()
            print(f"   Committed chunk {min(i + batch_size, total_enriched):,} / {total_enriched:,}...")

        elapsed = time.time() - start_time

        # Checkpoint
        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 2),
            "total_phase_c_missing_before": total_missing,
            "pass1_curated_roster_matches": pass1_count,
            "pass2_domain_taxonomy_matches": pass2_count,
            "total_faculties_enriched": total_enriched,
            "coverage_pct": round(total_enriched / total_missing * 100, 2) if total_missing > 0 else 0
        }

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ PHASE C COMPLETE: Enriched {total_enriched:,} / {total_missing:,} ({snapshot['coverage_pct']}%) faculties in {elapsed:.2f}s")
        print(f"📸 Snapshot saved to: {CHECKPOINT_FILE}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_phase_c_enrichment()
