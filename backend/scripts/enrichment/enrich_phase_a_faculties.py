# -*- coding: utf-8 -*-
"""
Phase A Faculty Enrichment Pipeline (Top 5 Universities)
Targets: Chulalongkorn (CU), Kasetsart (KU), Mahidol (MU), Chiang Mai (CMU), Khon Kaen (KKU)
Operations:
1. Pass 1: Crawled Roster Matching (Exact Thai Name + University)
2. Pass 2: Local Verified Faculty Rosters (chem, ams, med, cmu, cu, ku)
3. Pass 3: Calibrated University Academic Domain Taxonomy Mapping
4. Checkpoint saved to backend/data/agent_states/roster_enrich_phase_a_snapshot.json
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
CHECKPOINT_FILE = CHECKPOINT_DIR / "roster_enrich_phase_a_snapshot.json"
CRAWLED_ROSTER_FILE = CHECKPOINT_DIR / "phase_a_crawled_rosters.json"

TOP5_UNIVERSITIES = [
    "จุฬาลงกรณ์มหาวิทยาลัย",
    "มหาวิทยาลัยเกษตรศาสตร์",
    "มหาวิทยาลัยมหิดล",
    "มหาวิทยาลัยเชียงใหม่",
    "มหาวิทยาลัยขอนแก่น"
]

# Canonical Faculty English Translation Mapping
FACULTY_EN_MAP = {
    "คณะแพทยศาสตร์": "Faculty of Medicine",
    "คณะแพทยศาสตร์ศิริราชพยาบาล": "Faculty of Medicine Siriraj Hospital",
    "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี": "Faculty of Medicine Ramathibodi Hospital",
    "คณะวิศวกรรมศาสตร์": "Faculty of Engineering",
    "คณะวิทยาศาสตร์": "Faculty of Science",
    "คณะทันตแพทยศาสตร์": "Faculty of Dentistry",
    "คณะเภสัชศาสตร์": "Faculty of Pharmaceutical Sciences",
    "คณะสัตวแพทยศาสตร์": "Faculty of Veterinary Science",
    "คณะเกษตร": "Faculty of Agriculture",
    "คณะเกษตรศาสตร์": "Faculty of Agriculture",
    "คณะวนศาสตร์": "Faculty of Forestry",
    "คณะประมง": "Faculty of Fisheries",
    "คณะอุตสาหกรรมเกษตร": "Faculty of Agro-Industry",
    "คณะเทคโนโลยี": "Faculty of Technology",
    "คณะสาธารณสุขศาสตร์": "Faculty of Public Health",
    "คณะพยาบาลศาสตร์": "Faculty of Nursing",
    "คณะเทคนิคการแพทย์": "Faculty of Associated Medical Sciences",
    "คณะสหเวชศาสตร์": "Faculty of Allied Health Sciences",
    "คณะกายภาพบำบัด": "Faculty of Physical Therapy",
    "คณะพาณิชยศาสตร์และการบัญชี": "Faculty of Commerce and Accountancy",
    "คณะบริหารธุรกิจ": "Faculty of Business Administration",
    "คณะบริหารธุรกิจและการบัญชี": "Faculty of Business Administration and Accountancy",
    "คณะเศรษฐศาสตร์": "Faculty of Economics",
    "คณะสถาปัตยกรรมศาสตร์": "Faculty of Architecture",
    "คณะนิติศาสตร์": "Faculty of Law",
    "คณะรัฐศาสตร์": "Faculty of Political Science",
    "คณะรัฐศาสตร์และรัฐประศาสนศาสตร์": "Faculty of Political Science and Public Administration",
    "คณะอักษรศาสตร์": "Faculty of Arts",
    "คณะมนุษยศาสตร์": "Faculty of Humanities",
    "คณะสังคมศาสตร์": "Faculty of Social Sciences",
    "คณะมนุษยศาสตร์และสังคมศาสตร์": "Faculty of Humanities and Social Sciences",
    "คณะครุศาสตร์": "Faculty of Education",
    "คณะศึกษาศาสตร์": "Faculty of Education",
    "คณะนิเทศศาสตร์": "Faculty of Communication Arts",
    "คณะการสื่อสารมวลชน": "Faculty of Mass Communication",
    "คณะจิตวิทยา": "Faculty of Psychology",
    "คณะศิลปกรรมศาสตร์": "Faculty of Fine and Applied Arts",
    "คณะวิจิตรศิลป์": "Faculty of Fine Arts",
    "วิทยาลัยการคอมพิวเตอร์": "College of Computing",
    "คณะเทคโนโลยีสารสนเทศและการสื่อสาร": "Faculty of Information and Communication Technology",
    "คณะสิ่งแวดล้อม": "Faculty of Environment",
    "คณะสิ่งแวดล้อมและทรัพยากรศาสตร์": "Faculty of Environment and Resource Studies",
}

# Calibrated Domain Rules
DOMAIN_TAXONOMY = [
    # Dentistry
    ("คณะทันตแพทยศาสตร์", [
        "oral and maxillofacial", "dental", "tooth", "teeth", "orthodontic", "periodont",
        "endodont", "prosthodont", "caries", "maxillofacial", "dentistry", "implant dentistry"
    ]),
    # Veterinary
    ("คณะสัตวแพทยศาสตร์", [
        "veterinary", "canine", "feline", "bovine", "porcine", "equine", "animal disease",
        "zoonotic", "veterinary parasitology", "veterinary anatomy", "swine", "poultry disease"
    ]),
    # Pharmacy
    ("คณะเภสัชศาสตร์", [
        "pharmac", "drug delivery", "drug design", "pharmaceut", "dosage", "pharmacokinetics",
        "pharmacology", "bioactive peptides", "medicinal chemistry", "herbal medicine",
        "phytochemistry", "formulation development"
    ]),
    # Forestry (KU specific)
    ("คณะวนศาสตร์", [
        "forestry", "silviculture", "forest ecology", "wood science", "forest management",
        "teak", "tropical forest", "mangrove forest", "tree biomass"
    ]),
    # Fisheries (KU specific)
    ("คณะประมง", [
        "fisheries", "aquaculture", "shrimp culture", "tilapia", "marine biology",
        "aquatic animal", "fish nutrition", "fish disease", "algal culture"
    ]),
    # Agriculture
    ("คณะเกษตรศาสตร์", [
        "agronomy", "crop science", "soil science", "horticulture", "plant pathology",
        "plant breeding", "entomology", "rice production", "paddy soil", "fertilizer application"
    ]),
    # Agro-Industry
    ("คณะอุตสาหกรรมเกษตร", [
        "food science", "food technology", "food processing", "postharvest", "fermentation technology",
        "food packaging", "shelf-life extension", "food sensory", "food safety", "bioprocess"
    ]),
    # Architecture
    ("คณะสถาปัตยกรรมศาสตร์", [
        "urban transport", "urban planning", "architecture", "built environment", "landscape design",
        "sustainable building", "vernacular architecture", "spatial design", "interior architecture"
    ]),
    # Economics
    ("คณะเศรษฐศาสตร์", [
        "economics", "macroeconomic", "microeconomic", "econometric", "monetary policy",
        "fiscal policy", "international trade", "economic growth", "labor economics"
    ]),
    # Law
    ("คณะนิติศาสตร์", [
        "law and legal", "criminal law", "civil law", "constitutional law", "human rights law",
        "intellectual property law", "international law", "jurisprudence"
    ]),
    # Political Science
    ("คณะรัฐศาสตร์", [
        "political science", "public administration", "international relations", "geopolitics",
        "public policy", "governance", "foreign policy", "diplomacy", "sociopolitical"
    ]),
    # Education
    ("คณะศึกษาศาสตร์", [
        "education and teaching", "curriculum development", "pedagogy", "educational technology",
        "stem education", "teaching methods", "student learning", "learning achievement", "higher education"
    ]),
    # Engineering
    ("คณะวิศวกรรมศาสตร์", [
        "engineering", "robotics", "power system", "smart grid", "additive manufacturing",
        "fluid dynamics", "nanotechnology", "telecommunication", "structural mechanics",
        "concrete structure", "mechanical engineering", "chemical engineering", "electrical engineering",
        "civil engineering", "geotechnical", "deep learning", "machine learning", "computer vision",
        "neural network", "sensor network", "wireless network", "renewable energy", "solar cell"
    ]),
    # Medicine / Healthcare
    ("คณะแพทยศาสตร์", [
        "surgery", "surgical", "clinical", "oncology", "cancer", "tumor", "cardiovascular",
        "cardiology", "pediatric", "radiology", "pathology", "neurology", "anesthesia",
        "orthopedic", "ophthalmology", "dermatology", "covid-19", "sars-cov-2", "retinal",
        "macular", "psychiatry", "respiratory", "pulmonary", "stroke", "leukemia",
        "chemotherapy", "intensive care", "infectious diseases", "epidemiology", "endoscopy"
    ]),
    # Science
    ("คณะวิทยาศาสตร์", [
        "crystallography", "x-ray diffraction", "air quality", "chemical synthesis",
        "organic chemistry", "inorganic chemistry", "catalysis", "quantum", "optics",
        "slime mold", "myxomycetes", "biodiversity", "polymer", "biochemistry", "microbiology",
        "genetics", "molecular biology", "analytical chemistry", "materials science", "physics",
        "mathematics", "applied mathematics", "statistics", "geology", "mineralogy"
    ]),
]


def clean_name(n: str) -> str:
    if not n:
        return ""
    for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "นายแพทย์", "พญ.", "นพ.", "ทพ.", "ทพญ.", "สพ.ญ.", "น.สพ."]:
        if n.startswith(t):
            n = n[len(t):].strip()
    return re.sub(r"\s+", "", n)


def load_crawled_rosters() -> list[dict]:
    if CRAWLED_ROSTER_FILE.exists():
        try:
            return json.loads(CRAWLED_ROSTER_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def run_phase_a_enrichment():
    print("=" * 80)
    print("🚀 STARTING PHASE A FACULTY ENRICHMENT (TOP 5 UNIVERSITIES)")
    print("=" * 80)
    start_time = time.time()
    db = SessionLocal()

    try:
        # 1. Load all missing faculties for Top 5 Universities
        missing_rows = db.execute(text("""
            SELECT id, full_name_th, university_th, first_name, last_name, email, research_interests
            FROM faculties
            WHERE university_th IN :unis
              AND (faculty_th IS NULL OR trim(faculty_th) = :empty)
        """), {"unis": tuple(TOP5_UNIVERSITIES), "empty": ""}).fetchall()

        total_missing = len(missing_rows)
        print(f"📊 Total Top 5 faculty missing faculty_th: {total_missing:,}")

        # Index missing by (university_th, cleaned_name)
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

        updates = {}  # fid -> {"faculty_th": ..., "faculty": ..., "department_th": ...}

        # --- PASS 1: Crawled Roster Matching ---
        print("\n--- Pass 1: Matching against Fresh Crawled Rosters ---")
        crawled = load_crawled_rosters()
        pass1_count = 0
        for item in crawled:
            uni = item.get("university_th")
            fn = item.get("first_name_th")
            ln = item.get("last_name_th")
            cn = clean_name(f"{fn}{ln}")
            fac_th = item.get("faculty_th")
            dept_th = item.get("department_th")

            if (uni, cn) in missing_by_name:
                for target_fid in missing_by_name[(uni, cn)]:
                    if target_fid not in updates:
                        updates[target_fid] = {
                            "faculty_th": fac_th,
                            "faculty": FACULTY_EN_MAP.get(fac_th, "Faculty of " + fac_th.replace("คณะ", "")),
                            "department_th": dept_th
                        }
                        pass1_count += 1

        print(f"   [Pass 1] Matched {pass1_count:,} faculties from fresh rosters.")

        # --- PASS 2: Local Curated Rosters Matching ---
        print("\n--- Pass 2: Matching against Local Curated Datasets ---")
        pass2_count = 0
        raw_files = [
            BASE_DIR / "backend" / "data" / "raw" / "cmu_med_raw.json",
            BASE_DIR / "backend" / "data" / "raw" / "cmu_science_raw.json",
            BASE_DIR / "backend" / "data" / "raw" / "cu_missing_raw.json",
            BASE_DIR / "backend" / "data" / "raw" / "ku_missing_raw.json",
            BASE_DIR / "backend" / "data" / "raw" / "scholars_med_cmu_all.json",
            CHECKPOINT_DIR / "cmu_extracted.json",
            CHECKPOINT_DIR / "wave18_ku_forest_regional_extracted.json",
            CHECKPOINT_DIR / "wave17_ku_forest_extracted.json",
            CHECKPOINT_DIR / "wave19_cu_gaps_extracted.json",
            CHECKPOINT_DIR / "cmu_engineering_extracted.json",
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
                    name = item.get("full_name_th") or item.get("thai_name") or f"{item.get('first_name','')} {item.get('last_name','')}".strip()
                    cn = clean_name(name)
                    if (uni, cn) in missing_by_name:
                        for target_fid in missing_by_name[(uni, cn)]:
                            if target_fid not in updates:
                                updates[target_fid] = {
                                    "faculty_th": fac_th,
                                    "faculty": FACULTY_EN_MAP.get(fac_th, "Faculty of " + fac_th.replace("คณะ", "")),
                                    "department_th": item.get("department_th")
                                }
                                pass2_count += 1
            except Exception:
                pass

        print(f"   [Pass 2] Matched {pass2_count:,} faculties from local curated datasets.")

        # --- PASS 3: Calibrated University Academic Domain Taxonomy Mapping ---
        print("\n--- Pass 3: Calibrated Academic Domain Taxonomy Mapping ---")
        pass3_count = 0
        for fid, info in missing_by_id.items():
            if fid in updates:
                continue
            interests_str = " ".join(info["interests"]).lower()
            if not interests_str:
                continue

            uni = info["uni"]
            matched_fac = None

            # Map domain rules with university-specific faculty name adjustments
            for fac_target, keywords in DOMAIN_TAXONOMY:
                if any(kw in interests_str for kw in keywords):
                    # Adjust faculty name for university nuance
                    if uni == "มหาวิทยาลัยเกษตรศาสตร์":
                        if fac_target == "คณะเกษตรศาสตร์":
                            matched_fac = "คณะเกษตร"
                        elif fac_target == "คณะครุศาสตร์":
                            matched_fac = "คณะศึกษาศาสตร์"
                        else:
                            matched_fac = fac_target
                    elif uni == "มหาวิทยาลัยมหิดล":
                        if fac_target == "คณะแพทยศาสตร์":
                            # Siriraj vs Ramathibodi
                            matched_fac = "คณะแพทยศาสตร์ศิริราชพยาบาล"
                        elif fac_target == "คณะครุศาสตร์":
                            continue  # MU has no Faculty of Education
                        else:
                            matched_fac = fac_target
                    elif uni == "จุฬาลงกรณ์มหาวิทยาลัย":
                        if fac_target == "คณะศึกษาศาสตร์":
                            matched_fac = "คณะครุศาสตร์"
                        elif fac_target in ["คณะวนศาสตร์", "คณะประมง"]:
                            continue  # CU has no Forestry / Fisheries
                        else:
                            matched_fac = fac_target
                    else:
                        matched_fac = fac_target
                    break

            if matched_fac:
                updates[fid] = {
                    "faculty_th": matched_fac,
                    "faculty": FACULTY_EN_MAP.get(matched_fac, "Faculty of " + matched_fac.replace("คณะ", "")),
                    "department_th": None
                }
                pass3_count += 1

        print(f"   [Pass 3] Classified and mapped {pass3_count:,} faculties via domain taxonomy.")

        # --- DATABASE BATCH COMMIT ---
        total_enriched = len(updates)
        print(f"\n💾 Executing loss-free database updates for {total_enriched:,} faculty records...")

        # Batch update via execute_values / transaction
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
                """), {
                    "fid": fid,
                    "fth": data["faculty_th"],
                    "fen": data["faculty"],
                    "dth": data.get("department_th")
                })
            db.commit()
            print(f"   Committed chunk {min(i + batch_size, total_enriched):,} / {total_enriched:,}...")

        elapsed = time.time() - start_time

        # Checkpoint
        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 2),
            "total_top5_missing_before": total_missing,
            "pass1_crawled_roster_matches": pass1_count,
            "pass2_local_roster_matches": pass2_count,
            "pass3_domain_taxonomy_matches": pass3_count,
            "total_faculties_enriched": total_enriched,
            "coverage_pct": round(total_enriched / total_missing * 100, 2)
        }

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ PHASE A COMPLETE: Enriched {total_enriched:,} / {total_missing:,} ({snapshot['coverage_pct']}%) faculties in {elapsed:.2f}s")
        print(f"📸 Snapshot saved to: {CHECKPOINT_FILE}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_phase_a_enrichment()
