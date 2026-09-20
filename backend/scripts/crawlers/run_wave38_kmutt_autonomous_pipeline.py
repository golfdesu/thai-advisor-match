"""Wave 38 KMUTT Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: King Mongkut's University of Technology Thonburi (KMUTT)
Scope:
1. Faculty of Engineering:
   - Chemical Engineering (https://chemeng.kmutt.ac.th/lecturer/)
   - Environmental Engineering (https://env.kmutt.ac.th/about-us/team)
   - Tool & Materials Engineering (https://tme.kmutt.ac.th/about-us/staff/)
   - Production Engineering (https://pe.kmutt.ac.th/myteam)
   - Control Systems & Instrumentation (https://inc.kmutt.ac.th/home/page/th/people)
   - Electrical Engineering (https://ee.kmutt.ac.th/page3.php)
2. Faculty of Science:
   - Mathematics - Math (https://math.kmutt.ac.th/คณาจารย์/สาขาคณิตศาสตร์/)
   - Mathematics - Stat & Data (https://math.kmutt.ac.th/คณาจารย์/สาขาสถิติ/)
   - Mathematics - Applied CS (https://math.kmutt.ac.th/คณาจารย์/สาขาวิทยาการคอมพิวเตอร/)
   - Chemistry (https://chem.kmutt.ac.th/faculty-staff/faculty-directory)
   - Physics (https://physics.kmutt.ac.th/page/staff_acad)
   - Microbiology (https://mic.kmutt.ac.th/index.php/about/staff)

Execution Standard:
- Headless SKILL.state extraction via FacultyExtractionAgent.
- Checkpoints persisted to backend/data/agent_states/.
- RapidFuzz token_set_ratio deduplication against existing DB.
- 768-dim Gemini vector embeddings for net new records.
- Atomic commit to local PostgreSQL (localhost:5432/advisor_match).
"""
import os
import re
import sys
import time
import json
import random
import threading
import urllib.parse
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz, process

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from scripts.agentic_pipeline.state_reducer import (
    load_state_checkpoint,
    save_state_checkpoint,
    normalize_thai_title_and_name
)
from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

AGENT_STATES_DIR = BACKEND_DIR / "data" / "agent_states"
AGENT_STATES_DIR.mkdir(parents=True, exist_ok=True)

KMUTT_TH = "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี"
KMUTT_EN = "King Mongkut's University of Technology Thonburi"

TARGETS = [
    {
        "name": "kmutt_eng_che",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมเคมี",
        "dept_en": "Department of Chemical Engineering",
        "url": "https://chemeng.kmutt.ac.th/lecturer/",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_che_export.py"
    },
    {
        "name": "kmutt_eng_env",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมสิ่งแวดล้อม",
        "dept_en": "Department of Environmental Engineering",
        "url": "https://env.kmutt.ac.th/about-us/team",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_env_export.py"
    },
    {
        "name": "kmutt_eng_tme",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมเครื่องมือและวัสดุ",
        "dept_en": "Department of Tool and Materials Engineering",
        "url": "https://tme.kmutt.ac.th/about-us/staff/",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_tme_export.py"
    },
    {
        "name": "kmutt_eng_pe",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมอุตสาหการ",
        "dept_en": "Department of Production Engineering",
        "url": "https://pe.kmutt.ac.th/myteam",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_pe_export.py"
    },
    {
        "name": "kmutt_eng_inc",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมระบบควบคุมและเครื่องมือวัด",
        "dept_en": "Department of Control Systems and Instrumentation Engineering",
        "url": "https://inc.kmutt.ac.th/home/page/th/people",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_inc_export.py"
    },
    {
        "name": "kmutt_eng_ee",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "dept_en": "Department of Electrical Engineering",
        "url": "https://ee.kmutt.ac.th/page3.php",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_ee_export.py"
    },
    {
        "name": "kmutt_sci_math",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาคณิตศาสตร์",
        "dept_en": "Department of Mathematics",
        "url": "https://math.kmutt.ac.th/คณาจารย์/สาขาคณิตศาสตร์/",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_math_export.py"
    },
    {
        "name": "kmutt_sci_stat",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาคณิตศาสตร์ (สาขาสถิติและวิทยาการข้อมูล)",
        "dept_en": "Department of Mathematics (Statistics and Data Science)",
        "url": "https://math.kmutt.ac.th/คณาจารย์/สาขาสถิติ/",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_stat_export.py"
    },
    {
        "name": "kmutt_sci_appcs",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาคณิตศาสตร์ (สาขาวิทยาการคอมพิวเตอร์ประยุกต์)",
        "dept_en": "Department of Mathematics (Applied Computer Science)",
        "url": "https://math.kmutt.ac.th/คณาจารย์/สาขาวิทยาการคอมพิวเตอร/",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_appcs_export.py"
    },
    {
        "name": "kmutt_sci_chem",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาเคมี",
        "dept_en": "Department of Chemistry",
        "url": "https://chem.kmutt.ac.th/faculty-staff/faculty-directory",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_chem_export.py"
    },
    {
        "name": "kmutt_sci_phys",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาฟิสิกส์",
        "dept_en": "Department of Physics",
        "url": "https://physics.kmutt.ac.th/page/staff_acad",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_phys_export.py"
    },
    {
        "name": "kmutt_sci_mic",
        "faculty_th": "คณะวิทยาศาสตร์",
        "faculty_en": "Faculty of Science",
        "dept_th": "ภาควิชาจุลชีววิทยา",
        "dept_en": "Department of Microbiology",
        "url": "https://mic.kmutt.ac.th/index.php/about/staff",
        "export_file": AGENT_STATES_DIR / "kmutt_sci_mic_export.py"
    },
    {
        "name": "kmutt_eng_ce",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมโยธา",
        "dept_en": "Department of Civil Engineering",
        "url": "https://ce.kmutt.ac.th/staffs-teachers/",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_ce_export.py"
    },
    {
        "name": "kmutt_eng_me",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมเครื่องกล",
        "dept_en": "Department of Mechanical Engineering",
        "url": "https://me.kmutt.ac.th/about-us/staff/",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_me_export.py"
    },
    {
        "name": "kmutt_eng_ene",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมอิเล็กทรอนิกส์และโทรคมนาคม",
        "dept_en": "Department of Electronic and Telecommunication Engineering",
        "url": "https://ene.kmutt.ac.th/th/staff.php",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_ene_export.py"
    },
    {
        "name": "kmutt_eng_fe",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "dept_th": "ภาควิชาวิศวกรรมอาหาร",
        "dept_en": "Department of Food Engineering",
        "url": "https://foodeng.kmutt.ac.th/member/",
        "export_file": AGENT_STATES_DIR / "kmutt_eng_fe_export.py"
    },
    {
        "name": "kmutt_soad",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
        "faculty_en": "School of Architecture and Design",
        "dept_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
        "dept_en": "School of Architecture and Design",
        "url": "https://soad.kmutt.ac.th/people/",
        "export_file": AGENT_STATES_DIR / "kmutt_soad_export.py"
    },
    {
        "name": "kmutt_seem",
        "faculty_th": "คณะพลังงานสิ่งแวดล้อมและวัสดุ",
        "faculty_en": "School of Energy, Environment and Materials",
        "dept_th": "คณะพลังงานสิ่งแวดล้อมและวัสดุ",
        "dept_en": "School of Energy, Environment and Materials",
        "url": "https://seem.kmutt.ac.th/staff/",
        "export_file": AGENT_STATES_DIR / "kmutt_seem_export.py"
    },
]

RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
RE_BAD_NAME = re.compile(r'(?:ข่าว|ประกาศ|เจ้าหน้าที่|บุคลากร|ห้องสมุด|ติดต่อ|facebook|โทรศัพท์)', re.I)


def safe_url(u: str) -> str:
    parts = urllib.parse.urlsplit(u)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))


def extract_target(tgt: dict) -> list[dict]:
    export_file = tgt["export_file"]
    if export_file.exists():
        print(f"📂 [SKILL.state] Found existing export: {export_file.name}, loading...")
        ns = {}
        try:
            exec(export_file.read_text(encoding="utf-8"), {}, ns)
            faculties = ns.get("EXTRACTED_FACULTIES", [])
            print(f"   Loaded {len(faculties)} profiles from {export_file.name}")
            return faculties
        except Exception as e:
            print(f"   Warning loading {export_file.name}: {e}, re-running agent...")

    target_url = safe_url(tgt["url"])
    print(f"\n🚀 [SKILL.state] Running FacultyExtractionAgent for: {tgt['dept_th']} ({target_url})")
    agent = FacultyExtractionAgent(
        target_university_th=KMUTT_TH,
        target_university_en=KMUTT_EN,
        target_faculty_th=tgt["faculty_th"],
        target_faculty_en=tgt["faculty_en"],
        max_steps=5,
        auto_lookup_wiki=False
    )
    agent.add_seed_urls([target_url])
    agent.run_crawl_loop()

    code = agent.export_as_dataset_python()
    export_file.write_text(code, encoding="utf-8")
    print(f"💾 Exported {len(agent.state.faculties)} verified profiles to {export_file}")

    # Attach departmental metadata
    results = []
    for f in agent.state.faculties.values():
        if isinstance(f, dict):
            f["department_th"] = tgt["dept_th"]
            f["department"] = tgt["dept_en"]
            results.append(f)
    return results


def clean_faculty_record(r: dict, tgt: dict) -> dict | None:
    name = (r.get("full_name_th") or "").strip()
    if not name or len(name) < 4:
        return None
    if RE_BAD_NAME.search(name):
        return None

    # Title normalization
    try:
        title, clean_name, _ = normalize_thai_title_and_name(name)
    except Exception:
        clean_name = name
        title = r.get("academic_title_th") or ""

    if not clean_name or len(clean_name.split()) < 2:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    # Filter shared/generic emails
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@"]):
        email = ""

    return {
        "university_th": KMUTT_TH,
        "university": KMUTT_EN,
        "faculty_th": tgt["faculty_th"],
        "faculty": tgt["faculty_en"],
        "department_th": tgt["dept_th"],
        "department": tgt["dept_en"],
        "academic_title_th": title or r.get("academic_title_th") or "",
        "full_name_th": clean_name,
        "first_name": r.get("first_name") or "",
        "last_name": r.get("last_name") or "",
        "email": email,
        "image_url": r.get("image_url") or "",
        "profile_url": r.get("profile_url") or tgt["url"],
        "research_interests": r.get("research_interests") or [],
        "featured_publications": r.get("featured_publications") or [],
        "education": r.get("education") or [],
        "taught_courses": r.get("taught_courses") or [],
    }


def main():
    print("======================================================================")
    print("🎓 WAVE 38: KMUTT AUTONOMOUS EXTRACTION & INGESTION PIPELINE")
    print("   Enforcing SKILL.state Architecture, Zero-Defect Invariants & Local-First")
    print("======================================================================")

    all_extracted_candidates = []
    for tgt in TARGETS:
        raw_list = extract_target(tgt)
        valid_count = 0
        for r in raw_list:
            cleaned = clean_faculty_record(r, tgt)
            if cleaned:
                all_extracted_candidates.append(cleaned)
                valid_count += 1
        print(f"   -> Valid cleaned candidates from {tgt['name']}: {valid_count} / {len(raw_list)}")

    print(f"\n📊 Total Cleaned Faculty Candidates Across All Targets: {len(all_extracted_candidates)}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_kmutt = db.query(FacultyDB).filter(
            FacultyDB.university_th == KMUTT_TH
        ).all()
        print(f"Current KMUTT faculty in database: {len(existing_kmutt)}")

        existing_names_cache = {}
        for ex in existing_kmutt:
            clean_th = strip_all_titles(ex.full_name_th or "")
            existing_names_cache[ex.id] = clean_th

        new_members = []
        updated_members = 0
        seen_in_batch = set()

        for cand in all_extracted_candidates:
            cand_clean = strip_all_titles(cand["full_name_th"])
            if not cand_clean or cand_clean in seen_in_batch:
                continue

            # Check matching against DB
            match_id = None
            if existing_names_cache:
                hit = process.extractOne(
                    cand_clean,
                    existing_names_cache,
                    scorer=fuzz.token_set_ratio,
                    score_cutoff=90
                )
                if hit:
                    match_id = hit[2]

            if match_id:
                # Existing record: check if we can enrich missing email or profile
                ex_rec = next((e for e in existing_kmutt if e.id == match_id), None)
                if ex_rec:
                    changed = False
                    if not ex_rec.email and cand["email"]:
                        ex_rec.email = cand["email"]
                        changed = True
                    if not ex_rec.image_url and cand["image_url"]:
                        ex_rec.image_url = cand["image_url"]
                        changed = True
                    if changed:
                        updated_members += 1
            else:
                seen_in_batch.add(cand_clean)
                new_members.append(cand)

        print(f"✨ Net New Members to Ingest: {len(new_members)}")
        print(f"🔄 Existing Members Enriched: {updated_members}")

        if not new_members and updated_members == 0:
            print("ℹ️ No database changes required.")
            return

        # Vectorization for Net New Members
        if new_members:
            print(f"\n--- Generating 768-dim Vector Embeddings for {len(new_members)} New Members ---")
            raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
            api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()] if raw_keys else []
            if not api_keys:
                raise ValueError("No Gemini API key available for embedding generation.")

            from google import genai
            from google.genai import types

            clients = [genai.Client(api_key=k) for k in api_keys]
            key_lock = threading.Lock()
            key_box = [0]

            def get_embedding(text: str) -> list[float]:
                for attempt in range(5):
                    with key_lock:
                        c = clients[key_box[0] % len(clients)]
                        key_box[0] += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            resp = c.models.embed_content(
                                model=model,
                                contents=text,
                                config=types.EmbedContentConfig(output_dimensionality=768)
                            )
                            vec = resp.embeddings[0].values
                            if vec and len(vec) == 768:
                                return vec
                        except Exception as e:
                            if "429" in str(e) or "Quota" in str(e):
                                time.sleep(1.0 * (attempt + 1))
                    time.sleep(1.0 * (attempt + 1))
                raise RuntimeError(f"Failed to generate embedding after retries for: {text[:50]}")

            def make_embed_text(m: dict) -> str:
                interests_str = ", ".join(m.get("research_interests") or [])
                return (
                    f"อาจารย์และนักวิจัย: {m.get('full_name_th', '')} ({m.get('academic_title_th', '')})\n"
                    f"สังกัด: {m.get('department_th', '')}, {m.get('faculty_th', '')}, {m.get('university_th', '')}\n"
                    f"ความเชี่ยวชาญและงานวิจัย: {interests_str}"
                )

            embed_texts = [make_embed_text(m) for m in new_members]
            vectors = [None] * len(new_members)

            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_idx = {
                    executor.submit(get_embedding, t): i for i, t in enumerate(embed_texts)
                }
                for f in as_completed(future_to_idx):
                    idx = future_to_idx[f]
                    vectors[idx] = f.result()
                    if (idx + 1) % 25 == 0 or idx + 1 == len(new_members):
                        print(f"  Vectorized {idx + 1}/{len(new_members)} faculty members...")

            # Commit to Database
            print("\n--- Committing Records to Local PostgreSQL ---")
            have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
            seq = 0
            for m, vec in zip(new_members, vectors):
                seq += 1
                uid = f"kmutt_w38_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"kmutt_w38_{seq:04d}_{random.randint(100, 999)}"
                have_ids.add(uid)

                db.add(FacultyDB(
                    id=uid,
                    university=m["university"],
                    university_th=m["university_th"],
                    faculty=m["faculty"],
                    faculty_th=m["faculty_th"],
                    department=m["department"],
                    department_th=m["department_th"],
                    academic_title_th=m["academic_title_th"],
                    full_name_th=m["full_name_th"],
                    first_name=m["first_name"],
                    last_name=m["last_name"],
                    email=m["email"],
                    image_url=m["image_url"],
                    profile_url=m["profile_url"],
                    research_interests=m["research_interests"],
                    featured_publications=m["featured_publications"],
                    education=m["education"],
                    taught_courses=m["taught_courses"],
                    embedding=vec
                ))

        db.commit()
        total_now = db.query(FacultyDB).filter(FacultyDB.university_th == KMUTT_TH).count()
        print(f"\n🎉 SUCCESS! Database Commit Complete.")
        print(f"   KMUTT faculty count before: {len(existing_kmutt)}")
        print(f"   KMUTT faculty count now:    {total_now} (+{len(new_members)} net new)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
