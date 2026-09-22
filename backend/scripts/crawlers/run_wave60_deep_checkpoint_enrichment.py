"""
Wave 60: Deep Agent States & Checkpoints Harvester
Enriches missing emails, Thai names, faculties, departments, and titles
from historical agent states and extraction checkpoints.
Complies with SKILL.state 5-Pillar Architecture and Section 9 Quality Invariants.
"""

import glob
import json
import os
import re
import sys
import time
from pathlib import Path
from sqlalchemy import text

# Robust path resolution
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"

# ─────────────────────────────────────────────────────────────
# Title & Name Normalization (Strict Section 9 Compliance)
# ─────────────────────────────────────────────────────────────
RE_THAI_TITLE = re.compile(
    r"^(ศ\.\s*ดร\.|รศ\.\s*ดร\.|ผศ\.\s*ดร\.|อ\.\s*ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|"
    r"นายแพทย์|ทันตแพทย์หญิง|ทันตแพทย์|สัตวแพทย์หญิง|สัตวแพทย์|เภสัชกรหญิง|เภสัชกร|"
    r"นาย|นางสาว|นาง|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.ญ\.|ภก\.|ภญ\.)\s*",
    re.IGNORECASE
)

RE_EN_TITLE = re.compile(
    r"^(Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Mr\.|Mrs\.|Ms\.)\s*",
    re.IGNORECASE
)

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

GENERIC_OR_SHARED_EMAILS = {
    "contact@chula.ac.th", "grad@chula.ac.th", "registrar@chula.ac.th",
    "eng@eng.chula.ac.th", "info@cmu.ac.th", "grad@cmu.ac.th",
    "math@cmu.ac.th", "biology@cmu.ac.th", "intmed@cmu.ac.th", "ams@cmu.ac.th",
    "dsc@cmu.ac.th", "pediatrics@cmu.ac.th", "chemy@ku.ac.th", "fish@ku.ac.th",
    "ase@eng.ku.ac.th", "engineering@kku.ac.th", "chemistry@kmutt.ac.th",
    "microbiology@kmutt.ac.th", "stat@sci.kmutnb.ac.th", "cs@sci.kmutnb.ac.th",
    "ic@sci.kmutnb.ac.th", "agro@psu.ac.th", "allied@allied.tu.ac.th",
    "attm@med.tu.ac.th", "fac-en@silpakorn.edu", "contact@cmu.ac.th",
    "pr@chula.ac.th", "info@kku.ac.th", "admin@kku.ac.th"
}

GENERIC_PREFIXES = {
    "admin", "info", "contact", "office", "dean", "pr", "support", "help",
    "webmaster", "postmaster", "service", "academic", "registrar", "admission",
    "research", "hr", "secretary", "saraban", "center", "division", "faculty",
    "department", "staff", "public", "news", "mail", "general"
}

UNIVERSITY_DOMAINS: dict[str, list[str]] = {
    "Chulalongkorn University":                               ["chula.ac.th"],
    "Mahidol University":                                     ["mahidol.ac.th", "mahidol.edu"],
    "Prince of Songkla University":                           ["psu.ac.th"],
    "Khon Kaen University":                                   ["kku.ac.th"],
    "Thammasat University":                                   ["tu.ac.th"],
    "King Mongkut's Institute of Technology Ladkrabang":      ["kmitl.ac.th"],
    "King Mongkut's University of Technology Thonburi":       ["kmutt.ac.th"],
    "Chiang Mai University":                                  ["cmu.ac.th"],
    "Kasetsart University":                                   ["ku.ac.th", "ku.th"],
    "Silpakorn University":                                   ["su.ac.th", "silpakorn.edu"],
    "Srinakharinwirot University":                            ["swu.ac.th", "g.swu.ac.th"],
    "Burapha University":                                     ["buu.ac.th"],
    "Suranaree University of Technology":                     ["sut.ac.th"],
    "Naresuan University":                                    ["nu.ac.th"],
    "King Mongkut's University of Technology North Bangkok":  ["kmutnb.ac.th"],
    "Ramkhamhaeng University":                                ["ru.ac.th"],
    "Walailak University":                                    ["wu.ac.th"],
    "University of Phayao":                                   ["up.ac.th"],
    "Ubon Ratchathani University":                            ["ubu.ac.th"],
    "Mae Fah Luang University":                               ["mfu.ac.th"],
    "Maejo University":                                       ["mju.ac.th"],
    "National Institute of Development Administration":       ["nida.ac.th"],
    "Thaksin University":                                     ["tsu.ac.th"],
    "Mahasarakham University":                                ["msu.ac.th"],
    "Vidyasirimedhi Institute of Science and Technology":     ["vistec.ac.th"],
    "Asian Institute of Technology":                          ["ait.ac.th", "ait.asia"],
}


def is_valid_academic_email(email: str, univ_en: str = "") -> bool:
    if not email or "@" not in email:
        return False
    e = email.lower().strip().rstrip(".")
    if not RE_EMAIL.match(e):
        return False
    if e in GENERIC_OR_SHARED_EMAILS:
        return False
    local_part, domain_part = e.split("@", 1)
    if local_part in GENERIC_PREFIXES:
        return False
    # No freemails
    if any(domain_part == f or domain_part.endswith("." + f) for f in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
        return False
    if univ_en and univ_en in UNIVERSITY_DOMAINS:
        allowed = UNIVERSITY_DOMAINS[univ_en]
        return any(domain_part == d or domain_part.endswith("." + d) for d in allowed)
    return domain_part.endswith(".ac.th") or domain_part.endswith(".edu")


def clean_norm_th(name: str) -> str:
    if not name:
        return ""
    n = RE_THAI_TITLE.sub("", name.strip()).strip()
    return re.sub(r"\s+", " ", n)


def clean_norm_en(first: str, last: str) -> tuple[str, str]:
    f = RE_EN_TITLE.sub("", first or "").strip().lower()
    l = (last or "").strip().lower()
    return (re.sub(r"\s+", " ", f), re.sub(r"\s+", " ", l))


def extract_academic_title_th(name: str) -> str | None:
    if not name:
        return None
    m = RE_THAI_TITLE.match(name.strip())
    if m:
        t = m.group(1).strip()
        # Canonicalize title
        t = re.sub(r"\s+", "", t)
        if "ศ.ดร" in t: return "ศ.ดร."
        if "รศ.ดร" in t: return "รศ.ดร."
        if "ผศ.ดร" in t: return "ผศ.ดร."
        if "อ.ดร" in t: return "อ.ดร."
        if "ศ." in t or t == "ศ": return "ศ."
        if "รศ." in t or t == "รศ": return "รศ."
        if "ผศ." in t or t == "ผศ": return "ผศ."
        if "ดร." in t or t == "ดร": return "ดร."
        if "อ." in t or t == "อ": return "อ."
        return t
    return None


def run_deep_agent_states_enrichment():
    print("=" * 70)
    print("Wave 60: Deep Agent States & Historical Checkpoints Harvester")
    print("=" * 70)

    db = SessionLocal()
    files = glob.glob(str(CHECKPOINT_DIR / "*.json"))
    print(f"Scanning {len(files):,} JSON files in {CHECKPOINT_DIR}...")

    raw_records = []
    for f in files:
        # Avoid reading self-generated output files or snapshots of deletions
        fname = Path(f).name
        if "deleted" in fname or "purge" in fname:
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue

        recs = []
        if isinstance(data, list):
            recs = data
        elif isinstance(data, dict):
            if "faculties" in data:
                facs = data["faculties"]
                recs = list(facs.values()) if isinstance(facs, dict) else facs
            elif "records" in data and isinstance(data["records"], list):
                recs = data["records"]
            elif "faculty_members" in data and isinstance(data["faculty_members"], list):
                recs = data["faculty_members"]
            elif "investigated_records" in data and isinstance(data["investigated_records"], list):
                recs = data["investigated_records"]

        for r in recs:
            if isinstance(r, dict):
                raw_records.append(r)

    print(f"Loaded {len(raw_records):,} raw records from agent states.")

    # Build High-Density Multi-Index
    index_exact_th: dict[tuple[str, str], dict] = {}
    index_norm_th: dict[tuple[str, str], dict] = {}
    index_en: dict[tuple[str, str, str], dict] = {}
    index_oa: dict[str, dict] = {}
    index_url: dict[str, dict] = {}

    # Global unique indices (when name exists only once across entire dataset)
    global_norm_th_counts: dict[str, int] = {}
    global_norm_th_record: dict[str, dict] = {}

    for r in raw_records:
        th = (r.get("full_name_th") or r.get("Fullname_Thai") or "").strip()
        fn = (r.get("first_name") or r.get("NameEng") or "").strip()
        ln = (r.get("last_name") or r.get("LastNameEN") or "").strip()
        u_th = (r.get("university_th") or r.get("university") or "").strip()
        u_en = (r.get("university") or "").strip()
        oa_id = (r.get("openalex_id") or "").strip()
        p_url = (r.get("profile_url") or "").strip()

        if th:
            index_exact_th[(th, u_th)] = r
            nth = clean_norm_th(th)
            if len(nth) > 4:
                index_norm_th[(nth, u_th)] = r
                global_norm_th_counts[nth] = global_norm_th_counts.get(nth, 0) + 1
                global_norm_th_record[nth] = r

        en_pair = clean_norm_en(fn, ln)
        if en_pair[0] and en_pair[1]:
            index_en[(en_pair[0], en_pair[1], u_th)] = r
            if u_en:
                index_en[(en_pair[0], en_pair[1], u_en)] = r

        if oa_id and "openalex.org" in oa_id:
            index_oa[oa_id] = r
            # Extract bare ID (e.g. A5001234567)
            bare = oa_id.rstrip("/").split("/")[-1]
            index_oa[bare] = r

        if p_url and "openalex" not in p_url and len(p_url) > 10:
            index_url[p_url] = r

    print(f"Index Built:")
    print(f"  Exact Thai keys:      {len(index_exact_th):,}")
    print(f"  Normalized Thai keys: {len(index_norm_th):,}")
    print(f"  English pair keys:    {len(index_en):,}")
    print(f"  OpenAlex ID keys:     {len(index_oa):,}")
    print(f"  Profile URL keys:     {len(index_url):,}")

    # Fetch DB records with missing fields
    print("\nQuerying DB for faculty records with missing fields...")
    db_records = db.execute(text(
        "SELECT id, full_name_th, first_name, last_name, university, university_th, "
        "       email, faculty_th, department_th, academic_title_th, image_url, profile_url, openalex_id "
        "FROM faculties "
        "WHERE (email IS NULL OR email = '') "
        "   OR (full_name_th NOT SIMILAR TO '%[ก-๙]%') "
        "   OR (faculty_th IS NULL OR faculty_th = '') "
        "   OR (department_th IS NULL OR department_th = '') "
        "   OR (image_url IS NULL OR image_url = '') "
        "   OR (academic_title_th IS NULL OR academic_title_th = '') "
        "ORDER BY id"
    )).fetchall()
    print(f"Found {len(db_records):,} candidate records in DB to evaluate.")

    updated_emails = 0
    updated_thai_names = 0
    updated_faculties = 0
    updated_departments = 0
    updated_titles = 0
    updated_images = 0
    updated_urls = 0

    updates_batch = []
    BATCH_SIZE = 500

    for row in db_records:
        fid, fth, fn, ln, u_en, u_th, em, facth, depth, titleth, img, purl, oaid = row

        matched = None
        match_pass = 0

        # Pass 1: OpenAlex ID match
        if oaid and oaid in index_oa:
            matched = index_oa[oaid]
            match_pass = 1

        # Pass 2: Profile URL match
        if not matched and purl and purl in index_url:
            matched = index_url[purl]
            match_pass = 2

        # Pass 3: Exact Thai name + University
        if not matched and fth and (fth.strip(), u_th or "") in index_exact_th:
            matched = index_exact_th[(fth.strip(), u_th or "")]
            match_pass = 3

        # Pass 4: Normalized Thai name + University
        if not matched and fth:
            nth = clean_norm_th(fth)
            if nth and (nth, u_th or "") in index_norm_th:
                matched = index_norm_th[(nth, u_th or "")]
                match_pass = 4

        # Pass 5: Clean English name + University
        if not matched and fn and ln:
            en_pair = clean_norm_en(fn, ln)
            if en_pair[0] and (en_pair[0], en_pair[1], u_th or "") in index_en:
                matched = index_en[(en_pair[0], en_pair[1], u_th or "")]
                match_pass = 5
            elif en_pair[0] and (en_pair[0], en_pair[1], u_en or "") in index_en:
                matched = index_en[(en_pair[0], en_pair[1], u_en or "")]
                match_pass = 5

        # Pass 6: Globally unique Normalized Thai name (unique across all Thai universities)
        if not matched and fth:
            nth = clean_norm_th(fth)
            if nth and global_norm_th_counts.get(nth, 0) == 1:
                matched = global_norm_th_record[nth]
                match_pass = 6

        if not matched:
            continue

        # Evaluate what fields can be backfilled
        patch = {}

        # 1. Email
        if not em or em.strip() == "":
            candidate_email = (matched.get("email") or matched.get("Email") or "").strip()
            if candidate_email and is_valid_academic_email(candidate_email, u_en or ""):
                patch["email"] = candidate_email
                updated_emails += 1

        # 2. Thai Name (if DB currently has English only)
        if not re.search(r"[ก-๙]", fth or ""):
            candidate_th = (matched.get("full_name_th") or matched.get("Fullname_Thai") or "").strip()
            if candidate_th and re.search(r"[ก-๙]", candidate_th):
                # Ensure no breadcrumbs / page title leaks
                if not any(w in candidate_th for w in ["มหาวิทยาลัย", "คณะ", "ภาควิชา", "สำนัก", "หน้าหลัก", "ติดต่อ", "รายละเอียด"]):
                    patch["full_name_th"] = candidate_th
                    updated_thai_names += 1

        # 3. Faculty TH
        if not facth or facth.strip() == "":
            candidate_fac = (matched.get("faculty_th") or matched.get("faculty") or "").strip()
            if candidate_fac and len(candidate_fac) > 3 and not any(w in candidate_fac for w in ["Home", "หน้าหลัก", "index", "default"]):
                patch["faculty_th"] = candidate_fac
                updated_faculties += 1

        # 4. Department TH
        if not depth or depth.strip() == "":
            candidate_dep = (matched.get("department_th") or matched.get("department") or "").strip()
            if candidate_dep and len(candidate_dep) > 3 and not any(w in candidate_dep for w in ["Home", "หน้าหลัก", "index", "default"]):
                patch["department_th"] = candidate_dep
                updated_departments += 1

        # 5. Academic Title TH
        if not titleth or titleth.strip() == "":
            candidate_title = (matched.get("academic_title_th") or matched.get("AcademicTitleTH") or "").strip()
            if not candidate_title and patch.get("full_name_th"):
                candidate_title = extract_academic_title_th(patch["full_name_th"])
            if not candidate_title and fth:
                candidate_title = extract_academic_title_th(fth)
            if candidate_title:
                patch["academic_title_th"] = candidate_title
                updated_titles += 1

        # 6. Image URL
        if not img or img.strip() == "":
            candidate_img = (matched.get("image_url") or matched.get("profile_image") or "").strip()
            if candidate_img and candidate_img.startswith("http") and not any(p in candidate_img.lower() for p in ["placeholder", "default", "avatar", "no_image"]):
                patch["image_url"] = candidate_img
                updated_images += 1

        # 7. Profile URL
        if (not purl or "openalex" in purl) and matched.get("profile_url"):
            candidate_purl = matched["profile_url"].strip()
            if candidate_purl.startswith("http") and "openalex" not in candidate_purl:
                patch["profile_url"] = candidate_purl
                updated_urls += 1

        if patch:
            patch["id"] = fid
            updates_batch.append(patch)

        if len(updates_batch) >= BATCH_SIZE:
            for item in updates_batch:
                set_clauses = [f"{k} = :{k}" for k in item.keys() if k != "id"]
                sql = f"UPDATE faculties SET {', '.join(set_clauses)} WHERE id = :id"
                db.execute(text(sql), item)
            db.commit()
            print(f"    Committed batch of {len(updates_batch)} updates...")
            updates_batch.clear()

    if updates_batch:
        for item in updates_batch:
            set_clauses = [f"{k} = :{k}" for k in item.keys() if k != "id"]
            sql = f"UPDATE faculties SET {', '.join(set_clauses)} WHERE id = :id"
            db.execute(text(sql), item)
        db.commit()
        print(f"    Committed final batch of {len(updates_batch)} updates.")

    # Save Checkpoint
    checkpoint_file = CHECKPOINT_DIR / "wave60_deep_checkpoint_enrichment_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "total_evaluated": len(db_records),
        "updated_emails": updated_emails,
        "updated_thai_names": updated_thai_names,
        "updated_faculties": updated_faculties,
        "updated_departments": updated_departments,
        "updated_titles": updated_titles,
        "updated_images": updated_images,
        "updated_profile_urls": updated_urls,
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("Wave 60 Deep Checkpoint Enrichment Complete:")
    print(f"  New Verified Emails:        +{updated_emails:,}")
    print(f"  New Thai Script Names:      +{updated_thai_names:,}")
    print(f"  New Faculty Affiliations:   +{updated_faculties:,}")
    print(f"  New Department Affiliations:+{updated_departments:,}")
    print(f"  New Academic Titles:        +{updated_titles:,}")
    print(f"  New Profile Images:         +{updated_images:,}")
    print(f"  New University URLs:        +{updated_urls:,}")
    print(f"  Snapshot Saved: {checkpoint_file.name}")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    run_deep_agent_states_enrichment()
