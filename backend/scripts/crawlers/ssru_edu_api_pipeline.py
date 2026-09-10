# -*- coding: utf-8 -*-
"""
SSRU Faculty of Education (คณะครุศาสตร์ ม.ราชภัฏสวนสุนันทา) -> SKILL.state Reducer pipeline.

edu.ssru.ac.th/th/page/facmembers is server-rendered Bootstrap accordion panels — one per
สาขาวิชา (9 panels, 59 lecturer cards). Each card carries: personal photo (useruploads),
Thai name with academic rank, a profile button linking to ssrudlp.ssru.ac.th/teacher/<Name>,
and full วุฒิการศึกษา (degree abbreviation + branch + university lines). The /en/ mirror
lists the same people in the same order with English names — panels are matched by ordinal
(One..Nine vs OneENG/TwoEng... mismatched case, so we index by position, not suffix).
Emails exist nowhere on the listing; each teacher's DLP page carries their @ssru.ac.th email,
so we fetch it per person (throttled) — emails feed the reducer's live-DB dedup pre-check.

Mission 05 stage 3 — Education is the #1 demand gap. Run from REPO ROOT:
    python backend/scripts/crawlers/ssru_edu_api_pipeline.py
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

BASE = "https://edu.ssru.ac.th"
TH_PAGE = f"{BASE}/th/page/facmembers"
EN_PAGE = f"{BASE}/en/page/facmembers"

UNIV_TH = "มหาวิทยาลัยราชภัฏสวนสุนันทา"
UNIV_EN = "Suan Sunandha Rajabhat University"
FAC_TH = "คณะครุศาสตร์"
FAC_EN = "Faculty of Education"

PANEL_SPLIT_RE = re.compile(r'id="collapse(\w+)"')
HEAD_RE = re.compile(r'data-toggle="collapse"[^>]*href="#collapse(\w+)"[^>]*>(.*?)</a>', re.S)
CARD_SPLIT_RE = re.compile(r'<div\s+class="col-lg-4"')
H5_NAME_RE = re.compile(r"<h5[^>]*>\s*<strong>(.*?)</strong>", re.S)
DLP_LINK_RE = re.compile(r'href="(https://ssrudlp\.ssru\.ac\.th/teacher/[^"]+)"')
CARD_IMG_RE = re.compile(r'<img[^>]*src="(https://edu\.ssru\.ac\.th/useruploads/images/[^"]+)"')
SSRU_EMAIL_RE = re.compile(r"[\w.+-]+@ssru\.ac\.th", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# courtesy-only prefixes = support staff / assistants, never academic advisors
COURTESY_RE = re.compile(r"^(นาย|นางสาว|นาง)\S")
EN_HONORIFIC = {"professor", "associate", "assistant", "prof", "assoc", "asst", "dr",
                "mr", "mrs", "ms", "acting", "2nd", "3rd", "lt", "lieutenant"}
# cards write honorifics glued to the name: "Dr.Duangkamol", "Assoc.Prof.Dr.Nantiya"
EN_PREFIX_RE = re.compile(r"^(Assoc\.?|Asst\.?|Professor|Associate|Assistant|Prof\.?|"
                          r"Dr\.?|Mr\.?|Mrs\.?|Ms\.?)+[\s.]*", re.I)


def strip_en_honorifics(en_name: str) -> str:
    """Peel leading honorifics even when glued: 'Assoc.Prof.Dr.Nantiya' -> 'Nantiya'."""
    prev = None
    while prev != en_name:
        prev = en_name
        en_name = EN_PREFIX_RE.sub("", en_name).strip()
    # token form ("Professor Nantiya") handled by the stoplist loop at call site
    return en_name


def academic_title_from_thai(line: str) -> str:
    """Full Thai honorific prefix on the card name -> canonical acronym title (+ดร. if held)."""
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


def name_after_title(line: str) -> str:
    """Strip leading rank tokens so we can test for bare courtesy prefixes."""
    return re.sub(r"^((รอง|ผู้ช่วย)?ศาสตราจารย์|อาจารย์|ดร\.?|(ศ|รศ|ผศ|อ)\.)[\s.]*", "", line).strip()


def parse_education_lines(card_html: str):
    """Degree lines under วุฒิการศึกษา: — keep '- <degree> (…) <uni>' bullets, drop boilerplate."""
    out = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", card_html, re.S):
        # <br> is the ONLY line break inside a card paragraph — literal \n in source HTML
        # is soft wrapping ("Ph.D. in\nEducation, Keele") and must not split a degree line
        text = TAG_RE.sub(" ", re.sub(r"<br\s*/?>", "\x00", p, flags=re.I))
        for line in text.split("\x00"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line.startswith("-"):
                continue
            deg = line.lstrip("-").strip()
            if deg and "ตัวย่อ" not in deg and "Abbreviation" not in deg and deg not in out:
                out.append(deg)
    return out


def split_panels(html: str):
    """Return [(dept_name, [card_html...]), ...] in document order."""
    heads = {hid: re.sub(r"<[^>]+>", " ", txt).strip() for hid, txt in HEAD_RE.findall(html)}
    parts = PANEL_SPLIT_RE.split(html)
    panels = []
    for i in range(1, len(parts) - 1, 2):
        pid, body = parts[i], parts[i + 1]
        cards = CARD_SPLIT_RE.split(body)[1:]
        dept = heads.get(pid, "")
        panels.append((dept, cards))
    return panels


def main():
    db = SessionLocal()
    state = ExtractionAgentState(
        session_id=f"ssru_edu_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        target_university_th=UNIV_TH,
        target_university_en=UNIV_EN,
        target_faculty_th=FAC_TH,
        target_faculty_en=FAC_EN,
    )
    reducer = FacultyStateReducer(db_session=db)
    client = httpx.Client(timeout=30, headers={"User-Agent": "Mozilla/5.0"},
                          follow_redirects=True)

    th_html = client.get(TH_PAGE).text
    en_html = client.get(EN_PAGE).text
    th_panels = split_panels(th_html)
    en_panels = split_panels(en_html)
    print(f"TH panels: {[(d, len(c)) for d, c in th_panels]}")
    print(f"EN panels: {[(d, len(c)) for d, c in en_panels]}")
    assert [len(c) for _, c in th_panels] == [len(c) for _, c in en_panels], \
        "TH/EN card counts drifted — abort rather than mis-pair names"

    profiles, emails_found, skipped = [], 0, 0
    total_cards = sum(len(c) for _, c in th_panels)
    done = 0
    for (dept_th, cards), (_, en_cards) in zip(th_panels, en_panels):
        for card, en_card in zip(cards, en_cards):
            done += 1
            raw_name = re.sub(r"\s+", " ", TAG_RE.sub("", H5_NAME_RE.search(card).group(1))).strip() \
                if H5_NAME_RE.search(card) else ""
            if not raw_name or not re.search(r"[฀-๿]", raw_name):
                skipped += 1
                continue
            title = academic_title_from_thai(raw_name)
            if not title or COURTESY_RE.match(name_after_title(raw_name)):
                skipped += 1
                continue
            en_name = re.sub(r"\s+", " ", TAG_RE.sub("", H5_NAME_RE.search(en_card).group(1))).strip() \
                if H5_NAME_RE.search(en_card) else ""
            en_name = strip_en_honorifics(en_name)
            # drop trailing degree suffix: "Kittikoon Rungruang, Ph.D"
            en_name = re.sub(r",?\s*(Ph\.?\s?D\.?|Ed\.?\s?D\.?|D\w{1,2}\.?)\s*$", "", en_name, flags=re.I)
            tokens = re.findall(r"[A-Za-z][A-Za-z.'-]*", en_name)
            i = 0
            while i < len(tokens) and tokens[i].lower().strip(".") in EN_HONORIFIC:
                i += 1
            parts_en = tokens[i:]
            first, last = (parts_en[0], " ".join(p.strip(".") for p in parts_en[1:])) \
                if len(parts_en) >= 2 else (None, None)

            dlp = DLP_LINK_RE.search(card)
            dlp_url = dlp.group(1) if dlp else None
            email = None
            if dlp_url:
                try:
                    page = client.get(dlp_url).text
                    found = [e.lower() for e in SSRU_EMAIL_RE.findall(page)]
                    email = found[0] if found else None
                    if email:
                        emails_found += 1
                except Exception as e:
                    print(f"  ! dlp fetch {dlp_url}: {type(e).__name__}")
                time.sleep(0.3)

            img = CARD_IMG_RE.search(card)
            profiles.append(RawFacultyProfile(
                full_name_th=raw_name,
                academic_title_th=title,
                first_name=first,
                last_name=last,
                email=email,
                department_th=dept_th or None,
                image_url=img.group(1) if img else None,
                profile_url=dlp_url,
                education=parse_education_lines(card),
                research_interests=[],   # listing carries no research-interest field
            ))
            if done % 10 == 0:
                print(f"  ...{done}/{total_cards} cards, {len(profiles)} kept")

    patch = FacultyStatePatch(new_profiles=profiles,
                              summary_of_changes=f"SSRU Education faculty pages: {len(profiles)} parsed")
    state = reducer.apply_patch(state, patch, step_tokens=0)
    state.visited_urls.extend([TH_PAGE, EN_PAGE])
    state.status = "completed"
    save_state_checkpoint(state, output_dir="backend/data/agent_states")

    out = os.path.join("backend", "scripts", "data_sources", "ssru_edu_api_extracted.py")
    code = ("# Auto-generated from edu.ssru.ac.th TH/EN faculty pages + ssrudlp emails via "
            f"SKILL.state Reducer (Session: {state.session_id})\nimport pprint\nEXTRACTED_FACULTIES = "
            + pprint.pformat(list(state.faculties.values()), width=120) + "\n")
    io.open(out, "w", encoding="utf-8").write(code)
    db.close()
    print(f"✨ SSRU Edu: {len(profiles)} academic ({skipped} non-academic filtered, "
          f"{emails_found} emails) -> {len(state.faculties)} verified -> {out}")


if __name__ == "__main__":
    main()
