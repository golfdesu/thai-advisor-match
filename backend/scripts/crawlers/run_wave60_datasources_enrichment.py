"""
Wave 60: Data Sources & Python Extraction Checkpoint Harvester
Enriches faculties table with hand-verified academic records from backend/scripts/data_sources/*.py.
Complies with SKILL.state 5-Pillar Architecture and Section 9 Quality Invariants.
"""

import ast
import glob
import json
import os
import re
import sys
import time
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal

DATA_SOURCES_DIR = BASE_DIR / "backend" / "scripts" / "data_sources"
CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"

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


def run_datasources_enrichment():
    print("=" * 70)
    print("Wave 60: Python Data Sources Harvester (backend/scripts/data_sources/)")
    print("=" * 70)

    db = SessionLocal()
    files = glob.glob(str(DATA_SOURCES_DIR / "*.py"))
    print(f"Parsing {len(files)} python data source files...")

    all_ds_records = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                tree = ast.parse(fp.read(), filename=f)
        except Exception:
            continue

        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                for el in node.value.elts:
                    if isinstance(el, ast.Dict):
                        d = {}
                        for k, v in zip(el.keys, el.values):
                            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                d[k.value] = v.value
                        if "full_name_th" in d or "first_name" in d or "email" in d:
                            all_ds_records.append(d)

    print(f"Extracted {len(all_ds_records):,} faculty records from python data sources.")

    # Build Index
    index_exact_th = {}
    index_norm_th = {}
    index_en = {}
    global_norm_th_counts = {}
    global_norm_th_record = {}

    for r in all_ds_records:
        th = (r.get("full_name_th") or "").strip()
        fn = (r.get("first_name") or "").strip()
        ln = (r.get("last_name") or "").strip()
        u_th = (r.get("university_th") or r.get("university") or "").strip()
        u_en = (r.get("university") or "").strip()

        if th:
            index_exact_th[(th, u_th)] = r
            index_exact_th[(th, u_en)] = r
            nth = clean_norm_th(th)
            if len(nth) > 4:
                index_norm_th[(nth, u_th)] = r
                index_norm_th[(nth, u_en)] = r
                global_norm_th_counts[nth] = global_norm_th_counts.get(nth, 0) + 1
                global_norm_th_record[nth] = r

        en_pair = clean_norm_en(fn, ln)
        if en_pair[0] and en_pair[1]:
            index_en[(en_pair[0], en_pair[1], u_th)] = r
            index_en[(en_pair[0], en_pair[1], u_en)] = r
            index_en[(en_pair[0], en_pair[1], "")] = r

    print(f"Index Built:")
    print(f"  Exact Thai keys:      {len(index_exact_th):,}")
    print(f"  Normalized Thai keys: {len(index_norm_th):,}")
    print(f"  English pair keys:    {len(index_en):,}")

    # Fetch DB records with missing fields
    db_records = db.execute(text(
        "SELECT id, full_name_th, first_name, last_name, university, university_th, "
        "       email, faculty_th, department_th, academic_title_th, image_url, profile_url "
        "FROM faculties "
        "WHERE (email IS NULL OR email = '') "
        "   OR (full_name_th NOT SIMILAR TO '%[ก-๙]%') "
        "   OR (faculty_th IS NULL OR faculty_th = '') "
        "   OR (department_th IS NULL OR department_th = '') "
        "   OR (image_url IS NULL OR image_url = '') "
        "   OR (academic_title_th IS NULL OR academic_title_th = '') "
        "ORDER BY id"
    )).fetchall()
    print(f"Candidate DB records: {len(db_records):,}")

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
        fid, fth, fn, ln, u_en, u_th, em, facth, depth, titleth, img, purl = row

        matched = None

        # 1. Exact Thai Name + University
        if fth and (fth.strip(), u_th or "") in index_exact_th:
            matched = index_exact_th[(fth.strip(), u_th or "")]
        elif fth and (fth.strip(), u_en or "") in index_exact_th:
            matched = index_exact_th[(fth.strip(), u_en or "")]

        # 2. Normalized Thai Name + University
        if not matched and fth:
            nth = clean_norm_th(fth)
            if nth and (nth, u_th or "") in index_norm_th:
                matched = index_norm_th[(nth, u_th or "")]
            elif nth and (nth, u_en or "") in index_norm_th:
                matched = index_norm_th[(nth, u_en or "")]

        # 3. Clean English Name + University
        if not matched and fn and ln:
            en_pair = clean_norm_en(fn, ln)
            if en_pair[0] and (en_pair[0], en_pair[1], u_th or "") in index_en:
                matched = index_en[(en_pair[0], en_pair[1], u_th or "")]
            elif en_pair[0] and (en_pair[0], en_pair[1], u_en or "") in index_en:
                matched = index_en[(en_pair[0], en_pair[1], u_en or "")]
            elif en_pair[0] and (en_pair[0], en_pair[1], "") in index_en:
                matched = index_en[(en_pair[0], en_pair[1], "")]

        # 4. Globally unique Thai name
        if not matched and fth:
            nth = clean_norm_th(fth)
            if nth and global_norm_th_counts.get(nth, 0) == 1:
                matched = global_norm_th_record[nth]

        if not matched:
            continue

        patch = {}

        # 1. Email
        if not em or em.strip() == "":
            candidate_email = (matched.get("email") or "").strip()
            if candidate_email and is_valid_academic_email(candidate_email, u_en or ""):
                patch["email"] = candidate_email
                updated_emails += 1

        # 2. Thai Name
        if not re.search(r"[ก-๙]", fth or ""):
            candidate_th = (matched.get("full_name_th") or "").strip()
            if candidate_th and re.search(r"[ก-๙]", candidate_th):
                if not any(w in candidate_th for w in ["มหาวิทยาลัย", "คณะ", "ภาควิชา", "สำนัก", "หน้าหลัก", "ติดต่อ"]):
                    patch["full_name_th"] = candidate_th
                    updated_thai_names += 1

        # 3. Faculty TH
        if not facth or facth.strip() == "":
            candidate_fac = (matched.get("faculty_th") or matched.get("faculty") or "").strip()
            if candidate_fac and len(candidate_fac) > 3 and not any(w in candidate_fac for w in ["Home", "หน้าหลัก", "index"]):
                patch["faculty_th"] = candidate_fac
                updated_faculties += 1

        # 4. Department TH
        if not depth or depth.strip() == "":
            candidate_dep = (matched.get("department_th") or matched.get("department") or "").strip()
            if candidate_dep and len(candidate_dep) > 3 and not any(w in candidate_dep for w in ["Home", "หน้าหลัก", "index"]):
                patch["department_th"] = candidate_dep
                updated_departments += 1

        # 5. Academic Title TH
        if not titleth or titleth.strip() == "":
            candidate_title = (matched.get("academic_title_th") or "").strip()
            if not candidate_title and patch.get("full_name_th"):
                candidate_title = extract_academic_title_th(patch["full_name_th"])
            if not candidate_title and fth:
                candidate_title = extract_academic_title_th(fth)
            if candidate_title:
                patch["academic_title_th"] = candidate_title
                updated_titles += 1

        # 6. Image URL
        if not img or img.strip() == "":
            candidate_img = (matched.get("image_url") or "").strip()
            if candidate_img and candidate_img.startswith("http") and not any(p in candidate_img.lower() for p in ["placeholder", "default", "avatar"]):
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

    checkpoint_file = CHECKPOINT_DIR / "wave60_datasources_enrichment_snapshot.json"
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
    print("Wave 60 Python Data Sources Enrichment Complete:")
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
    run_datasources_enrichment()
