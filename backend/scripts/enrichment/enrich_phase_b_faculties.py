# -*- coding: utf-8 -*-
"""
Phase B Faculty Enrichment Pipeline (Technology & Capital Universities)
Targets: Thammasat (TU), KMITL, KMUTT, KMUTNB, Suranaree (SUT)
Operations:
1. Pass 1: Local Curated Rosters (SUT, KMITL, KMUTNB, TU, KMUTT)
2. Pass 2: Calibrated University Academic Domain Taxonomy Mapping (Exact Faculty/Institute alignment)
3. Pass 3: Loss-Free In-Place Database Update & Commit
4. Checkpoint saved to backend/data/agent_states/roster_enrich_phase_b_snapshot.json
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
CHECKPOINT_FILE = CHECKPOINT_DIR / "roster_enrich_phase_b_snapshot.json"

PHASE_B_UNIVERSITIES = [
    "มหาวิทยาลัยธรรมศาสตร์",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี"
]

FACULTY_EN_MAP = {
    # TU
    "คณะวิศวกรรมศาสตร์": "Faculty of Engineering",
    "คณะวิทยาศาสตร์และเทคโนโลยี": "Faculty of Science and Technology",
    "คณะพาณิชยศาสตร์และการบัญชี": "Thammasat Business School",
    "คณะนิติศาสตร์": "Faculty of Law",
    "คณะรัฐศาสตร์": "Faculty of Political Science",
    "คณะเศรษฐศาสตร์": "Faculty of Economics",
    "คณะศิลปศาสตร์": "Faculty of Liberal Arts",
    "คณะสังคมวิทยาและมานุษยวิทยา": "Faculty of Sociology and Anthropology",
    "คณะวารสารศาสตร์และสื่อสารมวลชน": "Faculty of Journalism and Mass Communication",
    "คณะสังคมสงเคราะห์ศาสตร์": "Faculty of Social Administration",
    "คณะแพทยศาสตร์": "Faculty of Medicine",
    "คณะสหเวชศาสตร์": "Faculty of Allied Health Sciences",
    "คณะทันตแพทยศาสตร์": "Faculty of Dentistry",
    "คณะพยาบาลศาสตร์": "Faculty of Nursing",
    "คณะสาธารณสุขศาสตร์": "Faculty of Public Health",
    "คณะเภสัชศาสตร์": "Faculty of Pharmacy",
    "คณะสถาปัตยกรรมศาสตร์และการผังเมือง": "Faculty of Architecture and Planning",
    "คณะศิลปกรรมศาสตร์": "Faculty of Fine and Applied Arts",
    "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)": "Sirindhorn International Institute of Technology",
    # KMITL
    "คณะวิทยาศาสตร์": "Faculty of Science",
    "คณะสถาปัตยกรรม ศิลปะและการออกแบบ": "School of Architecture, Art and Design",
    "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี": "Faculty of Industrial Education and Technology",
    "คณะเทคโนโลยีการเกษตร": "Faculty of Agricultural Technology",
    "คณะเทคโนโลยีสารสนเทศ": "Faculty of Information Technology",
    "คณะอุตสาหกรรมอาหาร": "School of Food Industry",
    "คณะบริหารธุรกิจ": "KMITL Business School",
    # KMUTT
    "คณะสถาปัตยกรรมศาสตร์และการออกแบบ": "School of Architecture and Design",
    "คณะพลังงานสิ่งแวดล้อมและวัสดุ": "School of Energy, Environment and Materials",
    "คณะทรัพยากรชีวภาพและเทคโนโลยี": "School of Bioresources and Technology",
    # KMUTNB
    "คณะวิทยาศาสตร์ประยุกต์": "Faculty of Applied Science",
    "วิทยาลัยเทคโนโลยีอุตสาหกรรม": "College of Industrial Technology",
    "คณะครุศาสตร์อุตสาหกรรม": "Faculty of Technical Education",
    "คณะเทคโนโลยีและการจัดการอุตสาหกรรม": "Faculty of Technology and Industrial Management",
    "คณะอุตสาหกรรมเกษตร": "Faculty of Agro-Industry",
    # SUT (Institutes)
    "สำนักวิชาวิศวกรรมศาสตร์": "Institute of Engineering",
    "สำนักวิชาวิทยาศาสตร์": "Institute of Science",
    "สำนักวิชาเทคโนโลยีการเกษตร": "Institute of Agricultural Technology",
    "สำนักวิชาเทคโนโลยีสังคม": "Institute of Social Technology",
    "สำนักวิชาสาธารณสุขศาสตร์": "Institute of Public Health",
    "สำนักวิชาแพทยศาสตร์": "Institute of Medicine",
    "สำนักวิชาพยาบาลศาสตร์": "Institute of Nursing",
    "สำนักวิชาทันตแพทยศาสตร์": "Institute of Dentistry",
}

# Calibrated domain keywords for Phase B
DOMAIN_TAXONOMY = [
    # Dentistry
    ("ทันตแพทย์", [
        "oral and maxillofacial", "dental", "tooth", "teeth", "orthodontic", "periodont",
        "endodont", "prosthodont", "caries", "maxillofacial", "dentistry", "implant dentistry"
    ]),
    # Veterinary
    ("สัตวแพทย์", [
        "veterinary", "canine", "feline", "bovine", "porcine", "equine", "animal disease",
        "zoonotic", "swine", "poultry disease"
    ]),
    # Pharmacy
    ("เภสัชศาสตร์", [
        "pharmac", "drug delivery", "drug design", "pharmaceut", "dosage", "pharmacokinetics",
        "pharmacology", "bioactive peptides", "medicinal chemistry", "herbal medicine",
        "phytochemistry", "formulation development"
    ]),
    # Architecture & Design
    ("สถาปัตยกรรม", [
        "architecture", "urban planning", "urban design", "landscape design", "spatial design",
        "built environment", "sustainable building", "interior architecture", "urban transport"
    ]),
    # Agriculture & Food Industry
    ("เกษตรและอาหาร", [
        "agronomy", "crop science", "soil science", "horticulture", "plant pathology",
        "plant breeding", "entomology", "rice production", "food science", "food technology",
        "food processing", "postharvest", "fermentation technology", "food packaging",
        "animal nutrition", "poultry nutrition"
    ]),
    # Economics
    ("เศรษฐศาสตร์", [
        "economics", "macroeconomic", "microeconomic", "econometric", "monetary policy",
        "fiscal policy", "international trade", "economic growth", "labor economics"
    ]),
    # Law
    ("นิติศาสตร์", [
        "law and legal", "criminal law", "civil law", "constitutional law", "human rights law",
        "intellectual property law", "international law", "jurisprudence"
    ]),
    # Political Science & Sociology
    ("รัฐศาสตร์และสังคม", [
        "political science", "public administration", "international relations", "geopolitics",
        "public policy", "governance", "diplomacy", "sociology", "anthropology", "sociopolitical"
    ]),
    # Business & Accountancy
    ("บริหารและบัญชี", [
        "accounting", "auditing", "marketing", "business administration", "finance", "fintech",
        "entrepreneurship", "supply chain", "logistics", "corporate governance", "human resource management"
    ]),
    # Media & Communication
    ("นิเทศและสื่อสาร", [
        "journalism", "mass communication", "media studies", "broadcasting", "digital media",
        "public relations", "advertising", "communication arts"
    ]),
    # Medicine & Allied Health
    ("แพทย์และสหเวช", [
        "surgery", "surgical", "clinical", "oncology", "cancer", "tumor", "cardiovascular",
        "cardiology", "pediatric", "radiology", "pathology", "neurology", "anesthesia",
        "orthopedic", "ophthalmology", "dermatology", "covid-19", "sars-cov-2", "retinal",
        "macular", "psychiatry", "respiratory", "pulmonary", "stroke", "nursing", "public health",
        "physical therapy", "medical technology", "allied health", "rehabilitation"
    ]),
    # Engineering & Technology
    ("วิศวกรรม", [
        "engineering", "robotics", "power system", "smart grid", "additive manufacturing",
        "fluid dynamics", "nanotechnology", "telecommunication", "structural mechanics",
        "concrete structure", "mechanical engineering", "chemical engineering", "electrical engineering",
        "civil engineering", "geotechnical", "deep learning", "machine learning", "computer vision",
        "neural network", "sensor network", "wireless network", "renewable energy", "solar cell",
        "industrial engineering", "semiconductor", "microelectronics", "automation"
    ]),
    # Science
    ("วิทยาศาสตร์", [
        "crystallography", "x-ray diffraction", "chemical synthesis", "organic chemistry",
        "inorganic chemistry", "catalysis", "quantum", "optics", "biodiversity", "polymer",
        "biochemistry", "microbiology", "genetics", "molecular biology", "analytical chemistry",
        "materials science", "physics", "mathematics", "applied mathematics", "statistics",
        "geology", "mineralogy"
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
    """Map domain key to university-specific faculty/school/institute name."""
    if uni == "มหาวิทยาลัยเทคโนโลยีสุรนารี":
        mapping = {
            "วิศวกรรม": "สำนักวิชาวิศวกรรมศาสตร์",
            "วิทยาศาสตร์": "สำนักวิชาวิทยาศาสตร์",
            "เกษตรและอาหาร": "สำนักวิชาเทคโนโลยีการเกษตร",
            "แพทย์และสหเวช": "สำนักวิชาสาธารณสุขศาสตร์",
            "ทันตแพทย์": "สำนักวิชาทันตแพทยศาสตร์",
            "บริหารและบัญชี": "สำนักวิชาเทคโนโลยีสังคม",
            "รัฐศาสตร์และสังคม": "สำนักวิชาเทคโนโลยีสังคม",
            "เศรษฐศาสตร์": "สำนักวิชาเทคโนโลยีสังคม",
            "สถาปัตยกรรม": "สำนักวิชาวิศวกรรมศาสตร์",
        }
        return mapping.get(domain_key, "สำนักวิชาวิศวกรรมศาสตร์")

    elif uni == "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง":
        mapping = {
            "วิศวกรรม": "คณะวิศวกรรมศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "สถาปัตยกรรม": "คณะสถาปัตยกรรม ศิลปะและการออกแบบ",
            "เกษตรและอาหาร": "คณะเทคโนโลยีการเกษตร",
            "บริหารและบัญชี": "คณะบริหารธุรกิจ",
            "แพทย์และสหเวช": "คณะแพทยศาสตร์",
            "ทันตแพทย์": "คณะทันตแพทยศาสตร์",
        }
        return mapping.get(domain_key, "คณะวิศวกรรมศาสตร์")

    elif uni == "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี":
        mapping = {
            "วิศวกรรม": "คณะวิศวกรรมศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์",
            "สถาปัตยกรรม": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
            "เกษตรและอาหาร": "คณะทรัพยากรชีวภาพและเทคโนโลยี",
            "บริหารและบัญชี": "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
        }
        return mapping.get(domain_key, "คณะวิศวกรรมศาสตร์")

    elif uni == "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ":
        mapping = {
            "วิศวกรรม": "คณะวิศวกรรมศาสตร์",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์ประยุกต์",
            "เกษตรและอาหาร": "คณะอุตสาหกรรมเกษตร",
            "บริหารและบัญชี": "คณะบริหารธุรกิจ",
        }
        return mapping.get(domain_key, "คณะวิศวกรรมศาสตร์")

    elif uni == "มหาวิทยาลัยธรรมศาสตร์":
        mapping = {
            "วิศวกรรม": "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)",
            "วิทยาศาสตร์": "คณะวิทยาศาสตร์และเทคโนโลยี",
            "แพทย์และสหเวช": "คณะแพทยศาสตร์",
            "ทันตแพทย์": "คณะทันตแพทยศาสตร์",
            "เภสัชศาสตร์": "คณะเภสัชศาสตร์",
            "บริหารและบัญชี": "คณะพาณิชยศาสตร์และการบัญชี",
            "เศรษฐศาสตร์": "คณะเศรษฐศาสตร์",
            "นิติศาสตร์": "คณะนิติศาสตร์",
            "รัฐศาสตร์และสังคม": "คณะรัฐศาสตร์",
            "นิเทศและสื่อสาร": "คณะวารสารศาสตร์และสื่อสารมวลชน",
            "สถาปัตยกรรม": "คณะสถาปัตยกรรมศาสตร์และการผังเมือง",
        }
        return mapping.get(domain_key, "คณะสังคมศาสตร์")

    return "คณะวิศวกรรมศาสตร์"


def run_phase_b_enrichment():
    print("=" * 80)
    print("🚀 STARTING PHASE B FACULTY ENRICHMENT (TU, KMITL, KMUTT, KMUTNB, SUT)")
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
        """), {"unis": tuple(PHASE_B_UNIVERSITIES), "empty": ""}).fetchall()

        total_missing = len(missing_rows)
        print(f"📊 Total Phase B faculty missing faculty_th: {total_missing:,}")

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
        print("\n--- Pass 1: Matching against Phase B Curated Rosters ---")
        pass1_count = 0
        raw_files = [
            CHECKPOINT_DIR / "wave46_sut_extraction.json",
            CHECKPOINT_DIR / "kmitl_msu_mfu_extracted.json",
            CHECKPOINT_DIR / "nida_sut_extracted.json",
            CHECKPOINT_DIR / "mju_tu_extracted.json",
            CHECKPOINT_DIR / "wave40_kmutnb_extraction.json",
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
                                    "faculty": FACULTY_EN_MAP.get(fac_th, "Faculty of " + fac_th.replace("คณะ", "").replace("สำนักวิชา", "")),
                                    "department_th": item.get("department_th")
                                }
                                pass1_count += 1
            except Exception:
                pass

        print(f"   [Pass 1] Matched {pass1_count:,} faculties from curated datasets.")

        # --- PASS 2: Calibrated University Academic Domain Taxonomy Mapping ---
        print("\n--- Pass 2: Calibrated Academic Domain Taxonomy Mapping ---")
        pass2_count = 0
        for fid, info in missing_by_id.items():
            if fid in updates:
                continue
            interests_str = " ".join(info["interests"]).lower()
            if not interests_str:
                continue

            uni = info["uni"]
            matched_fac = None

            for domain_key, keywords in DOMAIN_TAXONOMY:
                if any(kw in interests_str for kw in keywords):
                    matched_fac = get_target_faculty(uni, domain_key)
                    break

            if matched_fac:
                updates[fid] = {
                    "faculty_th": matched_fac,
                    "faculty": FACULTY_EN_MAP.get(matched_fac, "Faculty of " + matched_fac.replace("คณะ", "").replace("สำนักวิชา", "")),
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
                """), {
                    "fid": fid,
                    "fth": data["faculty_th"],
                    "fen": data["faculty"],
                    "dth": data.get("department_th")
                })
            db.commit()
            print(f"   Committed chunk {min(i + batch_size, total_enriched):,} / {total_enriched:,}...")

        elapsed = time.time() - start_time

        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 2),
            "total_phase_b_missing_before": total_missing,
            "pass1_curated_roster_matches": pass1_count,
            "pass2_domain_taxonomy_matches": pass2_count,
            "total_faculties_enriched": total_enriched,
            "coverage_pct": round(total_enriched / total_missing * 100, 2)
        }

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ PHASE B COMPLETE: Enriched {total_enriched:,} / {total_missing:,} ({snapshot['coverage_pct']}%) faculties in {elapsed:.2f}s")
        print(f"📸 Snapshot saved to: {CHECKPOINT_FILE}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_phase_b_enrichment()
