# -*- coding: utf-8 -*-
"""
Enrich Faculty Research Interests across all 3,015 under-indexed profiles.
Extracts research interests from:
1. Publication titles (featured_publications)
2. Comprehensive Academic Department & Discipline Taxonomy
3. Re-generates 768-dim Gemini vector embeddings and updates local PostgreSQL.
"""

import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import func

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Domain Taxonomy Mapping (Thai Department/Faculty -> Research Interests)
TAXONOMY_INTERESTS_MAP = {
    "คอมพิวเตอร์": [
        "Computer Systems & Architecture",
        "Artificial Intelligence & Machine Learning",
        "Software Engineering & Cloud Systems",
        "Cybersecurity & Distributed Computing"
    ],
    "สารสนเทศ": [
        "Information Systems & Knowledge Management",
        "Cloud Computing & Big Data Analytics",
        "Human-Computer Interaction",
        "Enterprise Digital Transformation"
    ],
    "ข้อมูล": [
        "Data Science & Predictive Analytics",
        "Machine Learning & Deep Learning",
        "Big Data Engineering",
        "Statistical Modeling & Visualization"
    ],
    "ปัญญาประดิษฐ์": [
        "Artificial Intelligence & Autonomous Systems",
        "Deep Learning & Computer Vision",
        "Natural Language Processing",
        "Robotics & Intelligent Automation"
    ],
    "ซอฟต์แวร์": [
        "Software Architecture & DevOps",
        "Agile Software Development",
        "Cloud-native Application Engineering",
        "Software Quality & Testing"
    ],
    "เคมี": [
        "Chemical Reaction Engineering & Catalysis",
        "Polymer Science & Biomaterials",
        "Organic Synthesis & Medicinal Chemistry",
        "Process Simulation & Separation Technology"
    ],
    "ไฟฟ้า": [
        "Smart Grid & Power Systems Engineering",
        "Renewable Energy & Energy Storage",
        "Control Systems, Robotics & Automation",
        "Telecommunications & Signal Processing"
    ],
    "เครื่องกล": [
        "Thermal & Fluid Engineering",
        "Mechanical Design & Mechatronics",
        "Automotive & Transportation Engineering",
        "Energy Systems & Thermodynamics"
    ],
    "โยธา": [
        "Structural Engineering & Dynamics",
        "Geotechnical & Earthquake Engineering",
        "Transportation Systems & Infrastructure",
        "Water Resources & Environmental Engineering"
    ],
    "อุตสาหการ": [
        "Supply Chain & Operations Research",
        "Quality Management & Six Sigma",
        "Smart Manufacturing & Industry 4.0",
        "Ergonomics & Work System Design"
    ],
    "สิ่งแวดล้อม": [
        "Wastewater Treatment & Water Quality",
        "Air Pollution Control & Climate Change",
        "Waste Management & Circular Economy",
        "Environmental Impact Assessment"
    ],
    "อาหาร": [
        "Food Processing & Preservation Technology",
        "Functional Foods & Bioactive Compounds",
        "Food Safety & Quality Management",
        "Sensory Analysis & Product Development"
    ],
    "ชีว": [
        "Bioprocess & Fermentation Technology",
        "Molecular Biology & Genetic Engineering",
        "Agricultural & Industrial Biotechnology",
        "Microbial Technology & Bio-products"
    ],
    "วัสดุ": [
        "Advanced Materials & Nanotechnology",
        "Polymer Composites & Biomaterials",
        "Metallurgy & Materials Characterization",
        "Electronic & Photonic Materials"
    ],
    "เกษตร": [
        "Smart Agriculture & Precision Farming",
        "Plant Breeding & Crop Improvement",
        "Soil Science & Plant Nutrition",
        "Post-harvest Technology"
    ],
    "สัตว์": [
        "Animal Nutrition & Feed Technology",
        "Livestock Production & Management",
        "Animal Genetics & Breeding",
        "Veterinary Science & Disease Prevention"
    ],
    "ประมง": [
        "Aquaculture & Aquatic Animal Health",
        "Fisheries Resource Management",
        "Marine Biology & Coastal Ecology",
        "Fish Nutrition & Feed Technology"
    ],
    "เภสัช": [
        "Pharmaceutical Formulation & Drug Delivery",
        "Pharmacology & Molecular Toxicology",
        "Clinical Pharmacy & Pharmacokinetics",
        "Natural Products & Pharmacognosy"
    ],
    "แพทย์": [
        "Clinical Medicine & Translational Research",
        "Epidemiology & Global Public Health",
        "Cardiovascular & Metabolic Diseases",
        "Medical Genetics & Precision Medicine"
    ],
    "พยาบาล": [
        "Adult & Gerontological Nursing",
        "Community Health & Preventive Care",
        "Maternal & Child Health Care",
        "Mental Health & Psychiatric Nursing"
    ],
    "ทันต": [
        "Oral Biology & Pathology",
        "Implantology & Prosthodontics",
        "Periodontology & Preventive Dentistry",
        "Orthodontics & Maxillofacial Care"
    ],
    "สาธารณสุข": [
        "Public Health Policy & Healthcare Systems",
        "Occupational Health & Environmental Safety",
        "Infectious Disease Epidemiology",
        "Health Promotion & Behavior Change"
    ],
    "เทคนิคการแพทย์": [
        "Clinical Chemistry & Hematology",
        "Medical Microbiology & Virology",
        "Immunology & Serological Diagnostics",
        "Molecular Diagnostics & Laboratory Medicine"
    ],
    "กายภาพบำบัด": [
        "Musculoskeletal Rehabilitation",
        "Neurological Physical Therapy",
        "Sports Physical Therapy & Biomechanics",
        "Geriatric Mobility & Rehabilitation"
    ],
    "บริหาร": [
        "Strategic Management & Organizational Behavior",
        "Digital Marketing & Consumer Analytics",
        "Supply Chain & Operations Management",
        "Corporate Finance & Investment Strategy"
    ],
    "บัญชี": [
        "Financial Accounting & Reporting Standards",
        "Managerial Accounting & Cost Control",
        "Auditing & Corporate Governance",
        "Tax Planning & Forensic Accounting"
    ],
    "เศรษฐศาสตร์": [
        "Macroeconomic Policy & Monetary Economics",
        "Applied Microeconomics & Industrial Organization",
        "Development Economics & Environmental Policy",
        "Econometrics & Quantitative Financial Analysis"
    ],
    "นิเทศ": [
        "Strategic Communication & Brand Media",
        "Digital Journalism & New Media Production",
        "Visual Communication & Advertising",
        "Media Analytics & Audience Research"
    ],
    "สถาปัตย": [
        "Sustainable Architecture & Green Design",
        "Urban Planning & Smart Cities",
        "Building Technology & Energy Simulation",
        "Interior Architecture & Cultural Preservation"
    ],
    "ศิลปกรรม": [
        "Creative Arts & Digital Media Design",
        "Contemporary Art Practice & Curation",
        "Visual Arts & Interactive Installation",
        "Craft Design & Cultural Heritage"
    ],
    "นิติ": [
        "Commercial & Corporate Law",
        "Public Law & Constitutional Governance",
        "International Trade & Intellectual Property",
        "Cyber Law & Data Privacy Regulation"
    ],
    "ครุศาสตร์": [
        "Instructional Design & Educational Innovation",
        "STEM Education & Digital Pedagogy",
        "Curriculum Development & Evaluation",
        "Educational Leadership & Policy"
    ],
    "ศึกษาศาสตร์": [
        "Educational Measurement & Assessment",
        "Learning Technologies & Distance Education",
        "Teacher Professional Development",
        "Child Development & Inclusive Education"
    ],
    "มนุษย": [
        "Applied Linguistics & Language Teaching",
        "Literature & Cross-Cultural Communication",
        "Translation & Interpreting Studies",
        "Historical & Cultural Analysis"
    ],
    "สังคม": [
        "Social Development & Community Studies",
        "Sociology & Anthropology",
        "Public Administration & Public Policy",
        "International Relations & Global Governance"
    ],
    "ฟิสิกส์": [
        "Condensed Matter & Solid State Physics",
        "Applied Optics, Lasers & Photonics",
        "Computational Physics & Simulation",
        "Nuclear & High-Energy Physics"
    ],
    "คณิตศาสตร์": [
        "Applied Mathematics & Differential Equations",
        "Numerical Analysis & Scientific Computing",
        "Optimization Theory & Operations Research",
        "Financial Mathematics & Actuarial Science"
    ],
    "สถิติ": [
        "Applied Statistics & Experimental Design",
        "Statistical Quality Control & Reliability",
        "Predictive Modeling & Machine Learning",
        "Biostatistics & Clinical Trial Analysis"
    ]
}

# Scientific Publication Keyword Extractor
PUB_KEYWORD_PATTERNS = [
    (re.compile(r"\b(machine learning|deep learning|neural network|artificial intelligence|ai)\b", re.I), "Artificial Intelligence & Machine Learning"),
    (re.compile(r"\b(computer vision|object detection|image processing|cnn|yolo)\b", re.I), "Computer Vision & Image Processing"),
    (re.compile(r"\b(natural language processing|nlp|transformer|large language model|llm)\b", re.I), "Natural Language Processing (NLP)"),
    (re.compile(r"\b(data mining|big data|predictive model|analytics)\b", re.I), "Data Analytics & Predictive Modeling"),
    (re.compile(r"\b(iot|internet of things|sensor|embedded system|smart)\b", re.I), "Internet of Things (IoT) & Smart Systems"),
    (re.compile(r"\b(cloud|microservices|distributed system|serverless)\b", re.I), "Cloud Computing & Distributed Systems"),
    (re.compile(r"\b(cybersecurity|network security|cryptography|privacy)\b", re.I), "Cybersecurity & Network Defense"),
    (re.compile(r"\b(renewable energy|solar|wind|photovoltaic|clean energy)\b", re.I), "Renewable Energy & Photovoltaics"),
    (re.compile(r"\b(battery|energy storage|supercapacitor|fuel cell)\b", re.I), "Energy Storage & Battery Technology"),
    (re.compile(r"\b(smart grid|power system|power electronics|inverter)\b", re.I), "Smart Grid & Power Electronics"),
    (re.compile(r"\b(biopolymer|composite|nanomaterial|nanoparticle|graphene)\b", re.I), "Advanced Materials & Nanotechnology"),
    (re.compile(r"\b(catalyst|catalytic|catalysis|biodiesel|biofuel)\b", re.I), "Catalysis & Biofuel Technology"),
    (re.compile(r"\b(wastewater|adsorption|heavy metal|water treatment)\b", re.I), "Wastewater Treatment & Environmental Engineering"),
    (re.compile(r"\b(drug delivery|pharmacokinetics|anticancer|pharmaceutical)\b", re.I), "Drug Delivery Systems & Pharmacology"),
    (re.compile(r"\b(antioxidant|bioactive|extract|herbal|phytochemical)\b", re.I), "Natural Bioactive Compounds & Phytochemistry"),
    (re.compile(r"\b(food preservation|shelf life|fermentation|probiotic)\b", re.I), "Food Processing & Fermentation"),
    (re.compile(r"\b(microbiology|bacterial|fungal|pathogen|antimicrobial)\b", re.I), "Applied Microbiology & Antimicrobial Research"),
    (re.compile(r"\b(supply chain|logistics|inventory|routing|optimization)\b", re.I), "Supply Chain & Operations Optimization"),
    (re.compile(r"\b(biomechanics|rehabilitation|ergonomics|posture)\b", re.I), "Biomechanics & Ergonomics"),
    (re.compile(r"\b(soil|crop|yield|irrigation|agriculture)\b", re.I), "Agricultural Science & Crop Management"),
]


def extract_interests_from_publications(pubs: List[Any]) -> List[str]:
    extracted = set()
    for p in pubs:
        title = ""
        if isinstance(p, dict):
            title = p.get("title", "")
        elif isinstance(p, str):
            title = p
        if not title:
            continue
        for pat, interest in PUB_KEYWORD_PATTERNS:
            if pat.search(title):
                extracted.add(interest)
    return list(extracted)[:4]


def get_interests_for_faculty(f: FacultyDB) -> List[str]:
    interests = []
    # 1. From publications if available
    if f.featured_publications:
        pub_ints = extract_interests_from_publications(f.featured_publications)
        interests.extend(pub_ints)

    # 2. From department / faculty taxonomy
    combined_dept = f"{f.department_th or ''} {f.department or ''} {f.faculty_th or ''} {f.faculty or ''}"
    matched_taxo = []
    for key, taxo_list in TAXONOMY_INTERESTS_MAP.items():
        if key in combined_dept:
            for item in taxo_list:
                if item not in interests and item not in matched_taxo:
                    matched_taxo.append(item)

    interests.extend(matched_taxo)

    # Fallback if still empty
    if not interests:
        interests = [
            f.faculty_th or "วิจัยและพัฒนาวิชาการ",
            "นวัตกรรมและเทคโนโลยีประยุกต์",
            "Academic Research & Development"
        ]

    # Return top 4-5 distinctive interests
    return interests[:5]


def build_embedding_text(f: FacultyDB, interests: List[str]) -> str:
    interests_str = ", ".join(interests)
    pubs_str = ", ".join([p.get("title", "") if isinstance(p, dict) else str(p) for p in (f.featured_publications or [])[:4]])
    edu_str = ", ".join([e if isinstance(e, str) else str(e) for e in (f.education or [])[:3]])
    return (
        f"{f.full_name_th or ''} ({f.first_name or ''} {f.last_name or ''}). "
        f"Title: {f.academic_title_th or ''}. "
        f"University: {f.university or ''} ({f.university_th or ''}). "
        f"Faculty: {f.faculty or ''} ({f.faculty_th or ''}). "
        f"Department: {f.department or ''} ({f.department_th or ''}). "
        f"Role: {f.role or ''}. "
        f"Research Interests: {interests_str}. "
        f"Featured Publications: {pubs_str}. "
        f"Education: {edu_str}."
    )[:6000]


def run_enrichment():
    logger.info("=======================================================================")
    logger.info("🚀 STARTING RESEARCH INTERESTS ENRICHMENT (TASK 1)")
    logger.info("=======================================================================")

    db = SessionLocal()
    empty_profiles = (
        db.query(FacultyDB)
        .filter(func.json_array_length(FacultyDB.research_interests) == 0)
        .all()
    )
    total_target = len(empty_profiles)
    logger.info(f"Found {total_target} faculty profiles with empty research_interests.")

    if total_target == 0:
        logger.info("No profiles with empty research_interests. Exiting.")
        db.close()
        return

    # Assign new interests
    enriched_items = []
    for f in empty_profiles:
        new_interests = get_interests_for_faculty(f)
        emb_text = build_embedding_text(f, new_interests)
        enriched_items.append({
            "id": f.id,
            "interests": new_interests,
            "embedding_text": emb_text
        })

    logger.info(f"✨ Computed new research interests for {len(enriched_items)} profiles.")

    # Re-embed using Gemini with ThreadPoolExecutor
    logger.info(f"🧠 Generating updated 768-dim Gemini vector embeddings (4 workers, chunked commit)...")

    def embed_item(item: Dict[str, Any]) -> Dict[str, Any]:
        vec = embedding_service.get_embedding(item["embedding_text"], max_retries=3)
        if vec and len(vec) == 768:
            item["embedding"] = vec
        return item

    prof_map = {f.id: f for f in empty_profiles}
    vectorized_cnt = 0
    updated_cnt = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(embed_item, item): item for item in enriched_items}
        for future in as_completed(futures):
            res = future.result()
            f_id = res.get("id")
            if res.get("embedding") and f_id in prof_map:
                f_obj = prof_map[f_id]
                f_obj.research_interests = res["interests"]
                f_obj.embedding_text = res["embedding_text"]
                f_obj.embedding = res["embedding"]
                vectorized_cnt += 1
                updated_cnt += 1
                if updated_cnt % 25 == 0:
                    db.commit()
                    logger.info(f"   Committed {updated_cnt}/{len(enriched_items)} enriched profiles to Postgres...")

    db.commit()
    db.close()

    logger.info(f"🎉 TASK 1 COMPLETE! Updated {updated_cnt} faculty profiles with active research interests and vectors.")


if __name__ == "__main__":
    run_enrichment()
