"""
SWU Faculty of Education WordPress JSON API -> SKILL.state Reducer pipeline.

edu.swu.ac.th exposes a real `staff` custom post type (X-WP-Total: 171) — unlike the
SPA rosters that cli_runner (httpx, no JS) cannot render, every record here is a
server-rendered page whose sidebar carries a canonical 4-line block:
    <li>Thai name + title</li> <li>English name + title</li> <li>role line</li> <li>email</li>
The API list gives name/URL/photo-id only, so we page the list (2 requests) then fetch
each detail page once (throttled). Maps to RawFacultyProfile -> FacultyStateReducer
(RapidFuzz dedup + title normalization, DB pre-check for emails already ingested),
checkpoints state and exports the dataset for faculty_massive_ingestion_runner.

Mission 05 stage 3 — Education is the #1 demand gap (7,254 grad seats/yr, zero h>=20).
Run from the REPO ROOT:  python backend/scripts/crawlers/swu_edu_api_pipeline.py
"""
import io
import json
import os
import pprint
import re
import sys
import time
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding="utf-8")

import httpx

from app.core.database import SessionLocal
from scripts.agentic_pipeline.models import (
    ExtractionAgentState,
    FacultyStatePatch,
    RawFacultyProfile,
)
from scripts.agentic_pipeline.state_reducer import FacultyStateReducer, save_state_checkpoint

BASE = "https://edu.swu.ac.th"
STAFF_API = f"{BASE}/wp-json/wp/v2/staff"

UNIV_TH = "มหาวิทยาลัยศรีนครินทรวิโรฒ"
UNIV_EN = "Srinakharinwirot University"
FAC_TH = "คณะศึกษาศาสตร์"
FAC_EN = "Faculty of Education"

# Sidebar <ul> under the sticky photo block: EN name, role line, email
SIDEBAR_RE = re.compile(
    r'id="sticky-sidebar".*?<ul>(.*?)</ul>', re.S
)
LI_RE = re.compile(r"<li>(.*?)</li>", re.S)
IMG_RE = re.compile(r'<img[^>]*\ssrc="([^"]+)"')
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w.-]+\.\w{2,}$")
# "ภาควิชา..." / "สาขา..." inside the role line
DEPT_RE = re.compile(r"(ภาควิชา[฀-๿]+(?:และการ[฀-๿]+)*)")

# English honorific prefix -> our canonical short title (Thai title still comes from
# normalize_thai_title_and_name on the Thai line; this drives first/last splitting only)
EN_PREFIX_RE = re.compile(
    r"^(Professor|Associate\s*Professor|Assistant\s*Professor|Assoc\.?\s*Prof\.?|"
    r"Asst\.?\s*Prof\.?|Dr\.?|Lecturer|Mr\.|Mrs\.|Ms\.|Ph\.?D\.?)+[\s.]*",
    re.I,
)
DR_RE = re.compile(r"\b(Dr\.|PhD|ดอกเตอร์)\b", re.I)

# Non-academic job titles seen on staff lines — this WP post type is "staff", not
# "lecturers", and support officers must not pollute the advisor ranking.
NON_FACULTY_ROLE_RE = re.compile(
    r"^(นักวิชาการศึกษา|นักวิเคราะห์|เจ้าหน้าที่|พนักงาน|ลูกจ้าง|นักจัดการ|"
    r"นักทรัพยากรบุคคล|นักประชาสัมพันธ์|นักวิชาการคอมพิวเตอร์|ผู้ปฏิบัติงาน|"
    r"ช่าง|นักพิมพ์|แม่บ้าน|ยาม)"
)
# courtesy prefixes marking non-academic staff even when a rank abbreviation leads the line
COURTESY_RE = re.compile(r"^(อ\.\s*)?(นาย|นางสาว|นาง)\S")


def academic_title_from_thai(line: str) -> str:
    """Full Thai honorific on the name line -> acronym title (with Dr. if present)."""
    has_dr = "ดร." in line
    if line.startswith("รองศาสตราจารย์"):
        t = "รศ."
    elif line.startswith("ผู้ช่วยศาสตราจารย์"):
        t = "ผศ."
    elif line.startswith("ศาสตราจารย์"):
        t = "ศ."
    elif line.startswith("อาจารย์"):
        t = "อ."
    else:
        t = ""
    return (t + "ดร.") if (has_dr and t) else (t or ("ดร." if has_dr else ""))


def parse_sidebar(html: str):
    """Return dict(en_name, role, email, image) from a staff detail page, or None."""
    m = SIDEBAR_RE.search(html)
    if not m:
        return None
    fields = [re.sub(r"<[^>]+>", "", li).strip() for li in LI_RE.findall(m.group(1))]
    fields = [f for f in fields if f]
    out = {"th_name": fields[0] if fields else "",
           "en_name": "", "role": "", "email": ""}
    # field[1] is the English name line; the rest are role/position and email —
    # but ordering drifts, so classify by shape instead of index.
    for f in fields[1:]:
        if EMAIL_RE.match(f):
            out["email"] = f
        elif re.search(r"[A-Za-z]{3}", f) and not out["en_name"] and "http" not in f:
            out["en_name"] = f
        elif not out["role"]:
            out["role"] = f
    # the personal photo is the post-thumbnail (header/nav logos carry other classes)
    im = re.search(r'<img[^>]*wp-post-image[^>]*\ssrc="([^"]+)"|<img[^>]*\ssrc="([^"]+)"[^>]*wp-post-image',
                   html)
    out["image"] = (im.group(1) or im.group(2)) if im else ""
    return out


def split_en_name(en_name: str):
    """'Assoc. Prof. Dr.Patcharaporn Srisawat' -> (Patcharaporn, Srisawat);
    'Acting 2nd LT. Kittikoon Rungruang, Ph.D' -> (Kittikoon, Rungruang)."""
    clean = en_name
    clean = re.sub(r",?\s*(Ph\.?\s?D\.?|Ed\.?\s?D\.?|D\w{1,2}\.?)\s*$", "", clean, flags=re.I)
    # strip everything up to the first Capitalized token that isn't an honorific word
    tokens = re.findall(r"[A-Za-z][A-Za-z.'-]*", clean)
    HONORIFIC = {"professor", "associate", "assistant", "prof", "assoc", "asst",
                 "dr", "mr", "mrs", "ms", "acting", "second", "2nd", "3rd", "lt",
                 "lieutenant", "general", "air", "vice", "ratchakarin"}
    i = 0
    while i < len(tokens) and tokens[i].lower().strip(".") in HONORIFIC:
        i += 1
    parts = tokens[i:]
    if len(parts) < 2:
        return None, None
    return parts[0], " ".join(p.strip(".") for p in parts[1:])


def main():
    db = SessionLocal()
    state = ExtractionAgentState(
        session_id=f"swu_edu_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        target_university_th=UNIV_TH,
        target_university_en=UNIV_EN,
        target_faculty_th=FAC_TH,
        target_faculty_en=FAC_EN,
    )
    reducer = FacultyStateReducer(db_session=db)   # DB pre-check: skip emails already ingested
    client = httpx.Client(timeout=30, headers={"User-Agent": "Mozilla/5.0"},
                          follow_redirects=True)

    # --- 1. page the staff collection (per_page caps at 100) ---
    records, page = [], 1
    while True:
        r = client.get(STAFF_API, params={"per_page": 100, "page": page})
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        records.extend(batch)
        total = int(r.headers.get("X-WP-Total", len(records)))
        print(f"page {page}: {len(batch)} records (total header {total}, have {len(records)})")
        if len(records) >= total:
            break
        page += 1
    # de-dup by post id (API paging can repeat rows under edits)
    seen_posts = {rec["id"]: rec for rec in records}
    records = list(seen_posts.values())
    print(f"unique staff posts: {len(records)}")

    # --- 2. fetch each detail page, parse the sidebar block ---
    profiles, failures, skipped_staff = [], 0, 0
    for i, rec in enumerate(records, 1):
        link = rec.get("link") or ""
        th_name_api = rec["title"]["rendered"]
        try:
            h = client.get(link).text
            parsed = parse_sidebar(h) or {}
        except Exception as e:
            parsed = None
            failures += 1
            print(f"  ! {th_name_api[:40]} {type(e).__name__}")
        th_name = (parsed.get("th_name") or th_name_api)
        if not re.search(r"[฀-๿]", th_name):
            continue
        role = parsed.get("role", "")
        # This is a "staff" post type, so support officers appear alongside academics —
        # and the site prefixes them "อ. นาย/นางสาว …" (bare courtesy titles, no academic
        # rank). Keep only holders of a real academic rank with a non-support role line.
        title = academic_title_from_thai(th_name)
        if not title or NON_FACULTY_ROLE_RE.match(role or "") or COURTESY_RE.search(th_name):
            skipped_staff += 1
            continue
        dept = DEPT_RE.search(role) if role else None
        first, last = split_en_name(parsed.get("en_name", ""))
        profiles.append(RawFacultyProfile(
            full_name_th=th_name,
            academic_title_th=title or None,
            first_name=first,
            last_name=last,
            email=parsed.get("email") or None,
            department_th=dept.group(1) if dept else None,
            image_url=parsed.get("image") or None,
            profile_url=link,
            research_interests=[],   # detail pages carry no publication/interest fields
        ))
        if i % 25 == 0:
            print(f"  ...{i}/{len(records)} parsed, state={len(state.faculties)}")
        time.sleep(0.35)   # be a good guest

    # --- 3. one patch through the reducer (dedup vs state + live DB emails) ---
    patch = FacultyStatePatch(new_profiles=profiles,
                              summary_of_changes=f"SWU Education staff API: {len(profiles)} parsed")
    state = reducer.apply_patch(state, patch, step_tokens=0)
    state.visited_urls.append(STAFF_API)
    state.status = "completed"
    save_state_checkpoint(state, output_dir="backend/data/agent_states")

    out = os.path.join("backend", "scripts", "data_sources", "swu_edu_api_extracted.py")
    code = (f"# Auto-generated from edu.swu.ac.th WordPress staff API via SKILL.state Reducer "
            f"(Session: {state.session_id})\nimport pprint\nEXTRACTED_FACULTIES = "
            + pprint.pformat(list(state.faculties.values()), width=120) + "\n")
    io.open(out, "w", encoding="utf-8").write(code)
    db.close()
    print(f"✨ SWU Edu: {len(profiles)} academic ({skipped_staff} staff-filtered, "
          f"{failures} fetch-failures) -> {len(state.faculties)} verified -> {out}")


if __name__ == "__main__":
    main()
