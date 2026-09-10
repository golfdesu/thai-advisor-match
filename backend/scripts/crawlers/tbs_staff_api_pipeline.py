# -*- coding: utf-8 -*-
"""
Thammasat Business School (thammasat.tbs / tbs.tu.ac.th) staff directory -> SKILL.state Reducer.

tbs.tu.ac.th is WordPress exposing /staff-sitemap.xml (280 URLs, 195 unique people once the
_th/_en/_director/_management-team/_secretary variants are collapsed to a base slug). Each
staff page renders a clean block:
    <h2 class="single_staff_name">ศ.ดร.ภวิดา ปานะนนท์</h2>
    <h6 class="single_staff_position">Full-time Faculty Member, Department of International Business...</h6>
    <div class="single_staff_desc">...[สาขาวิชา...]  Education  - B.Acc. ... - Ph.D. ...</div>
    <a href="mailto:pavida@tbs.tu.ac.th">
plus a profile photo (wp-content/uploads, before the info block). The position line carries
both the English department and the Thai branch in brackets.

Mission 05 stage 3 — Marketing/Business is a priority gap (95 rows, zero h>=20). Business
scholars publish in English (OpenAlex-visible) but were never acquired here; this fills the
roster and ThaiJO/OpenAlex waves can then credit them. Run from REPO ROOT:
    python backend/scripts/crawlers/tbs_staff_api_pipeline.py
"""
import io
import os
import pprint
import re
import sys
import time
import urllib.parse
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

BASE = "https://tbs.tu.ac.th"
SITEMAP = f"{BASE}/staff-sitemap.xml"

UNIV_TH = "มหาวิทยาลัยธรรมศาสตร์"
UNIV_EN = "Thammasat University"
FAC_TH = "คณะพาณิชยศาสตร์และการบัญชี"
FAC_EN = "Thammasat Business School"

NAME_RE = re.compile(r'single_staff_name">\s*([^<]+?)\s*</h2>', re.S)
POS_RE = re.compile(r'single_staff_position">\s*([^<]+?)\s*</h6>', re.S)
DESC_RE = re.compile(r'single_staff_desc">(.*?)(?:<div|<footer|$)', re.S)
MAILTO_RE = re.compile(r'mailto:([\w.+-]+@[\w.-]+\.\w{2,})', re.I)
TAG_RE = re.compile(r"<[^>]+>")
BRACKET_TH_RE = re.compile(r"\[([^\]]*?(?:ภาควิชา|สาขาวิชา|โครงการ)[^\]]*?)\]")
DEPT_EN_RE = re.compile(r"(Department of [A-Za-z ,&/-]+|Program in [A-Za-z ,&/-]+)")
# the personal photo is the <img> immediately closing the wrapper div before the
# staff_generated_info block — an unanchored search matches the site logo instead
PHOTO_RE = re.compile(r'<img[^>]*?src="(https?://tbs\.tu\.ac\.th/wp-content/uploads/[^"]+)"'
                      r'[^>]*/?>\s*</div>\s*<div class="staff_generated_info"', re.S)
RANK_RE = re.compile(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)")
NON_FACULTY_POS_RE = re.compile(r"(?i)(secretary|เจ้าหน้าที่|นักวิชา|staff member|administrative)")


def academic_title_from_thai(line: str) -> str:
    has_dr = "ดร." in line
    if line.startswith("รองศาสตราจารย์") or line.startswith("รศ."):
        t = "รศ."
    elif line.startswith("ผู้ช่วยศาสตราจารย์") or line.startswith("ผศ."):
        t = "ผศ."
    elif line.startswith("ศาสตราจารย์") or line.startswith("ศ."):
        t = "ศ."
    elif line.startswith("อาจารย์") or line.startswith("อ."):
        t = "อ."
    else:
        t = ""
    return (t + "ดร.") if (has_dr and t) else (t or ("ดร." if has_dr else ""))


def parse_education(desc_html: str):
    """Degree bullets under the 'Education' label inside single_staff_desc."""
    text = TAG_RE.sub(" ", desc_html)
    text = re.sub(r"\s+", " ", text)
    seg = text.split("Education", 1)
    if len(seg) < 2:
        return []
    tail = seg[1]
    # stop at the next section label if present
    for stop in ("Experience", "Work Experience", "Research", "Publication", "Contact", "Email"):
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    out = []
    for chunk in re.split(r"\s-\s", tail):
        line = chunk.strip(" .,-")
        if len(line) > 4 and line not in out:
            out.append(line)
    return out[:8]


def main():
    db = SessionLocal()
    state = ExtractionAgentState(
        session_id=f"tbs_staff_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        target_university_th=UNIV_TH,
        target_university_en=UNIV_EN,
        target_faculty_th=FAC_TH,
        target_faculty_en=FAC_EN,
    )
    reducer = FacultyStateReducer(db_session=db)
    client = httpx.Client(timeout=httpx.Timeout(60, connect=20),
                          headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)

    sm = client.get(SITEMAP).text
    urls = re.findall(r"<loc>(.*?)</loc>", sm)
    by_base = {}
    for u in urls:
        slug = urllib.parse.unquote(u.split("/staff/")[1]).strip("/")
        base = re.sub(r"_(th|en|director|management-team|secretary)$", "", slug)
        # prefer the plain base URL when present, else first variant
        by_base.setdefault(base, u)
    targets = list(by_base.values())
    print(f"sitemap urls: {len(urls)} -> unique people: {len(targets)}")

    profiles, skipped_staff, no_name = [], 0, 0
    for i, u in enumerate(targets, 1):
        try:
            h = client.get(u).text
        except Exception as e:
            print(f"  ! {u.split('/staff/')[1][:40]} {type(e).__name__}")
            continue
        nm = NAME_RE.search(h)
        if not nm or not re.search(r"[฀-๿]", nm.group(1)):
            no_name += 1
            continue
        th_name = re.sub(r"\s+", " ", nm.group(1)).strip()
        pos_m = POS_RE.search(h)
        position = re.sub(r"\s+", " ", pos_m.group(1)).strip() if pos_m else ""
        title = academic_title_from_thai(th_name)
        # keep only ranked academics; drop secretaries/administrative staff
        if not title or NON_FACULTY_POS_RE.search(position):
            skipped_staff += 1
            continue
        email_m = MAILTO_RE.search(h)
        email = email_m.group(1).lower() if email_m else None
        dept_m = BRACKET_TH_RE.search(position) or DEPT_EN_RE.search(position)
        dept = dept_m.group(1).strip() if dept_m else None
        desc_m = DESC_RE.search(h)
        education = parse_education(desc_m.group(1)) if desc_m else []
        photo_m = PHOTO_RE.search(h)
        profiles.append(RawFacultyProfile(
            full_name_th=th_name,
            academic_title_th=title,
            email=email,
            department_th=dept,
            image_url=photo_m.group(1) if photo_m else None,
            profile_url=u,
            education=education,
            research_interests=[],
        ))
        if i % 30 == 0:
            print(f"  ...{i}/{len(targets)} scanned, kept={len(profiles)}")
        time.sleep(0.25)

    patch = FacultyStatePatch(new_profiles=profiles,
                              summary_of_changes=f"TBS staff directory: {len(profiles)} academic")
    state = reducer.apply_patch(state, patch, step_tokens=0)
    state.visited_urls.append(SITEMAP)
    state.status = "completed"
    save_state_checkpoint(state, output_dir="backend/data/agent_states")

    out = os.path.join("backend", "scripts", "data_sources", "tbs_staff_api_extracted.py")
    code = ("# Auto-generated from tbs.tu.ac.th staff-sitemap + per-profile pages via SKILL.state "
            f"Reducer (Session: {state.session_id})\nimport pprint\nEXTRACTED_FACULTIES = "
            + pprint.pformat(list(state.faculties.values()), width=120) + "\n")
    io.open(out, "w", encoding="utf-8").write(code)
    db.close()
    print(f"✨ TBS: {len(profiles)} academic ({skipped_staff} staff-filtered, {no_name} no-name) "
          f"-> {len(state.faculties)} verified -> {out}")


if __name__ == "__main__":
    main()
