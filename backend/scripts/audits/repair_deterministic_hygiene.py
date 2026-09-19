"""Apply evidence-backed local faculty hygiene repairs.

This script does not infer identities or merge people. It applies only repairs
whose source evidence was inspected: confirmed shared inboxes, MJU navigation
categories stored as departments, confirmed CMU directory artifacts and
publication-page boilerplate, URL whitespace normalization, and the KKU
Waranuch record whose English identity and OpenAlex affiliation are verified.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB, ResearchLabDB


# The MJU official pages expose these values as executive-board navigation
# categories, not academic departments.
SOURCE_BACKED_DEPARTMENT_REPAIRS = {
    "mju_28c9494a_3259",
    "mju_3d45eb1b_4854",
    "mju_f549a6a5_9889",
    "mju_20192677_2639",
    "mju_3f07ddbf_1431",
    "mju_6eab228f_5009",
}

# These records all point to the same CMU Rehabilitation Medicine directory
# page, have no person identity fields, and contain generated composite-name
# publication text. The official page lists named personnel separately.
CMU_REHABILITATION_ARTIFACT_IDS = {
    "cmu_2304eb6b_5173",
    "cmu_3320eb3a_9591",
    "cmu_4e7b6e1d_7745",
    "cmu_701e201b_5751",
    "cmu_430bd821_6417",
}

# These publication strings are page-card metadata, not publications. They
# contain an Email label and were extracted from the CMU personnel directory.
CMU_PUBLICATION_BOILERPLATE_HOSTS = {
    "math.science.cmu.ac.th",
    "w1.med.cmu.ac.th",
}

# These values are navigation/contact categories from Kasetsart directory
# pages, not research interests. The exact strings are removed only for these
# inspected records; no broad keyword deletion is used.
SOURCE_BACKED_INTEREST_REPAIRS = {
    "ku_wave18_econsrc_0006": {
        "โทรศัทพ์ทางไกลระหว่างประเทศ",
        "โทรศัพท์เคลื่อนที่",
        "โทรศัพท์ทางไกลภายในประเทศ",
        "โทรศัพท์ประจำที่",
        "โทรศัพท์สาธารณะ",
    },
    "ku_wave18_econsrc_0007": {
        "โทรศัทพ์ทางไกลระหว่างประเทศ",
        "โทรศัพท์เคลื่อนที่",
        "โทรศัพท์ทางไกลภายในประเทศ",
        "โทรศัพท์ประจำที่",
        "โทรศัพท์สาธารณะ",
    },
    "ku_wave18_lams_0012": {
        "email ที่ใช้งานประจำ : kanyarat.suk@ku.th เท่านั้น",
    },
}

# Publication titles repeated within a single source record. Deduplicate by
# case-insensitive trimmed title while retaining the first complete object.
SOURCE_BACKED_PUBLICATION_DEDUP_IDS = {
    "buu_eng_pattarapong",
    "cbs-003_d0d191",
    "chulalongk_facultyofc_akrachantachote_016",
    "cu_eng_ee_vision_001",
    "kku_cpeng_001",
    "mu_ict_akara_001",
    "mu_si_prasit_001",
    "silpakornu_facultyoff_chanlun_014",
    "su_eng_teacher_112",
}

KKU_WARANUCH_ID = "kku_dent_waranuch_001"
KKU_WARANUCH_THAI_NAME = "ศ.ทพญ.ดร. วรานุช ปิติพัฒน์"

# Exact shared contacts already classified by the local audit history.
SHARED_DEPARTMENTAL_EMAILS = {
    "sci@ku.ac.th", "dent@cmu.ac.th", "agr@ku.ac.th", "med@cmu.ac.th",
    "surgery@cmu.ac.th", "eng@kku.ac.th", "science@kku.ac.th",
    "sc@mahidol.ac.th", "eng@cmu.ac.th", "cpe@cmu.ac.th",
    "ee@eng.chula.ac.th", "civil@eng.chula.ac.th", "chem@eng.ku.ac.th",
    "pediatr@cmu.ac.th", "ortho@cmu.ac.th", "ent@cmu.ac.th",
    "ophth@cmu.ac.th", "obgyn@cmu.ac.th", "psychiat@cmu.ac.th",
    "radiology@cmu.ac.th", "anesthes@cmu.ac.th", "rehab@cmu.ac.th",
    "forensic@cmu.ac.th", "family@cmu.ac.th", "community@cmu.ac.th",
    "patho@cmu.ac.th", "micro@cmu.ac.th", "pharmacol@cmu.ac.th",
    "physiol@cmu.ac.th", "biochem@cmu.ac.th", "anatomy@cmu.ac.th",
    "parasit@cmu.ac.th", "dental@kku.ac.th", "vet@cmu.ac.th",
    "nurse@cmu.ac.th", "pharmacy@cmu.ac.th", "cmfm@med.tu.ac.th",
    "tds@ap.tu.ac.th",
}

DEPARTMENTAL_LOCAL_PREFIXES = (
    "sci@", "dent@", "civil@", "chem@", "eng@", "med@", "surgery@",
    "agr@", "nurse@", "vet@",
)

# Only collapse identical whitespace-delimited academic prefixes. Professional
# credentials such as ผศ. ทพ. นพ. are intentionally left unchanged.
DUPLICATE_PREFIX_RE = re.compile(
    r"^(?P<prefix>(?:รศ|ผศ|ศ|อ)(?:\.|\.ดร\.)?)"
    r"\s+(?P=prefix)\s+"
)


def is_shared_departmental_email(email: str) -> bool:
    normalized = email.strip().lower()
    return normalized in SHARED_DEPARTMENTAL_EMAILS or normalized.startswith(
        DEPARTMENTAL_LOCAL_PREFIXES
    )


def replace_lab_references(db, old_id: str, new_id: str | None) -> None:
    """Repoint or remove references before deleting a confirmed artifact."""
    for lab in db.query(ResearchLabDB).yield_per(500):
        changed = False
        if lab.lead_advisor_id == old_id:
            lab.lead_advisor_id = new_id
            changed = True
        if isinstance(lab.member_faculty_ids, list):
            updated = [member for member in lab.member_faculty_ids if member != old_id]
            if updated != lab.member_faculty_ids:
                lab.member_faculty_ids = updated
                changed = True
        if changed:
            print(f"[lab] updated {lab.id}: removed {old_id}")


def publication_is_confirmed_boilerplate(faculty: FacultyDB, item: object) -> bool:
    """Identify directory-card text without deleting real publication titles."""
    if not isinstance(item, dict):
        return False
    title = str(item.get("title") or "")
    if not re.search(r"email\s*:", title, re.IGNORECASE):
        return False
    url = faculty.profile_url or ""
    host = re.sub(r"^https?://", "", url).split("/", 1)[0].lower()
    return host in CMU_PUBLICATION_BOILERPLATE_HOSTS


def clean_confirmed_publication_boilerplate(faculty: FacultyDB) -> bool:
    """Remove only confirmed directory metadata from publication JSON."""
    items = faculty.featured_publications
    if not isinstance(items, list):
        return False
    cleaned = [item for item in items if not publication_is_confirmed_boilerplate(faculty, item)]
    if cleaned == items:
        return False
    faculty.featured_publications = cleaned
    faculty.embedding_text = build_faculty_embedding_text(faculty)
    return True


def trim_url_whitespace(value: str | None) -> str | None:
    """Remove only surrounding whitespace; preserve URL query contents."""
    return value.strip() if value is not None and value != value.strip() else value


def clean_source_backed_interests(faculty: FacultyDB) -> bool:
    """Remove inspected directory categories from research interests."""
    removals = SOURCE_BACKED_INTEREST_REPAIRS.get(faculty.id)
    if not removals or not isinstance(faculty.research_interests, list):
        return False
    cleaned = [item for item in faculty.research_interests if str(item).strip() not in removals]
    if cleaned == faculty.research_interests:
        return False
    faculty.research_interests = cleaned
    faculty.embedding_text = build_faculty_embedding_text(faculty)
    return True


def deduplicate_publications(faculty: FacultyDB) -> bool:
    """Keep the first publication object for each normalized title."""
    if faculty.id not in SOURCE_BACKED_PUBLICATION_DEDUP_IDS:
        return False
    items = faculty.featured_publications
    if not isinstance(items, list):
        return False
    seen: set[str] = set()
    cleaned = []
    for item in items:
        title = item.get("title") if isinstance(item, dict) else item
        key = str(title or "").strip().casefold()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        cleaned.append(item)
    if cleaned == items:
        return False
    faculty.featured_publications = cleaned
    faculty.embedding_text = build_faculty_embedding_text(faculty)
    return True


def main() -> None:
    db = SessionLocal()
    email_updates = 0
    title_updates = 0
    department_updates = 0
    deleted_cmu_artifacts = 0
    publication_updates = 0
    publication_dedup_updates = 0
    interest_updates = 0
    url_updates = 0
    kku_name_updates = 0
    try:
        rows = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for faculty in rows:
            email = (faculty.email or "").strip()
            if email and "@" in email and is_shared_departmental_email(email):
                print(f"[email] {faculty.id}: {faculty.email!r} -> NULL")
                faculty.email = None
                email_updates += 1

            name = faculty.full_name_th or ""
            fixed_name = DUPLICATE_PREFIX_RE.sub("", name, count=1)
            if fixed_name != name:
                print(f"[title] {faculty.id}: {name!r} -> {fixed_name!r}")
                faculty.full_name_th = fixed_name
                faculty.embedding_text = build_faculty_embedding_text(faculty)
                title_updates += 1

            if clean_confirmed_publication_boilerplate(faculty):
                print(f"[publication] removed confirmed directory metadata: {faculty.id}")
                publication_updates += 1

            if deduplicate_publications(faculty):
                print(f"[publication] removed duplicate titles: {faculty.id}")
                publication_dedup_updates += 1

            if clean_source_backed_interests(faculty):
                print(f"[interest] removed confirmed directory categories: {faculty.id}")
                interest_updates += 1

            for field in ("profile_url", "image_url"):
                value = getattr(faculty, field)
                trimmed = trim_url_whitespace(value)
                if trimmed != value:
                    print(f"[url] {faculty.id}.{field}: surrounding whitespace removed")
                    setattr(faculty, field, trimmed)
                    url_updates += 1

        for faculty_id in SOURCE_BACKED_DEPARTMENT_REPAIRS:
            faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if faculty is None:
                raise RuntimeError(f"Expected MJU record not found: {faculty_id}")
            if faculty.department is not None or faculty.department_th is not None:
                print(
                    f"[department] {faculty.id}: "
                    f"{faculty.department_th!r} / {faculty.department!r} -> NULL / NULL"
                )
                faculty.department = None
                faculty.department_th = None
                faculty.embedding_text = build_faculty_embedding_text(faculty)
                department_updates += 1

        for faculty_id in CMU_REHABILITATION_ARTIFACT_IDS:
            faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if faculty is None:
                print(f"[delete] CMU artifact already absent: {faculty_id}")
                continue
            replace_lab_references(db, faculty_id, None)
            print(f"[delete] confirmed CMU directory artifact: {faculty_id}")
            db.delete(faculty)
            deleted_cmu_artifacts += 1

        waranuch = db.query(FacultyDB).filter(FacultyDB.id == KKU_WARANUCH_ID).first()
        if waranuch is None:
            raise RuntimeError(f"Expected KKU record not found: {KKU_WARANUCH_ID}")
        if waranuch.full_name_th != KKU_WARANUCH_THAI_NAME:
            print(
                f"[name] {waranuch.id}: {waranuch.full_name_th!r} -> "
                f"{KKU_WARANUCH_THAI_NAME!r}"
            )
            waranuch.full_name_th = KKU_WARANUCH_THAI_NAME
            waranuch.embedding_text = build_faculty_embedding_text(waranuch)
            kku_name_updates += 1

        db.commit()
        print(f"Departmental inboxes nulled: {email_updates}")
        print(f"Exact duplicate academic prefixes removed: {title_updates}")
        print(f"MJU source-backed department fields cleared: {department_updates}")
        print(f"CMU directory artifacts deleted: {deleted_cmu_artifacts}")
        print(f"Confirmed publication boilerplate cleaned: {publication_updates}")
        print(f"Duplicate publication-title records cleaned: {publication_dedup_updates}")
        print(f"Confirmed interest-directory leaks cleaned: {interest_updates}")
        print(f"URL surrounding whitespace trimmed: {url_updates}")
        print(f"KKU Thai name fields repaired: {kku_name_updates}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
