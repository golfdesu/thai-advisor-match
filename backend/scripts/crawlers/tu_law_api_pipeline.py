# -*- coding: utf-8 -*-
"""
Thammasat University Faculty of Law — WordPress `teacher` post type -> SKILL.state Reducer.

law.tu.ac.th is WordPress with a REAL academic custom post type (X-WP-Total: 102) exposed
via wp-json/wp/v2/teacher, whose content.rendered carries the full profile in labeled
<h6> sections: การศึกษา (degree <li> lines), ความเชี่ยวชาญ (expertise), and
ผลงานวิชาการคัดสรร (curated publications — full citations with DOI links). Header block
holds Thai name, academic rank line, @tu.ac.th email and English name. This is the
Law-field acquisition for Mission 05 (282 law rows in DB, max h=6 — Thai jurists publish
in Thai law journals, invisible to OpenAlex; their curated publication lists are the
honest elite signal).

Publication strings are converted to the enrichment dict-shape {title, venue, url, year,
citation_count:0} AFTER reducer sanitization so they merge cleanly with ThaiJO/OpenAlex data.

Run from REPO ROOT:  python backend/scripts/crawlers/tu_law_api_pipeline.py
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

BASE = "https://law.tu.ac.th"
TEACHER_API = "https://www.law.tu.ac.th/wp-json/wp/v2/teacher"
MEDIA_API = "https://www.law.tu.ac.th/wp-json/wp/v2/media"

UNIV_TH = "มหาวิทยาลัยธรรมศาสตร์"
UNIV_EN = "Thammasat University"
FAC_TH = "คณะนิติศาสตร์"
FAC_EN = "Faculty of Law"

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<iframe[^>]*>.*?</iframe>",
                       re.S | re.I)
ALL_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}")
WIDGET_JS_RE = re.compile(r"\(function\(\$\) *\{.*?\}\)\(jQuery\);?", re.S)
DATE_PREFIX_RE = re.compile(r"^\d{1,2} [฀-๿]+ \d{4}\s+")  # CV export noise: "30 สิงหาคม 2561 ..."
H6_RE = re.compile(r"<h6[^>]*>(.*?)</h6>(.*?)(?=<h6|\Z)", re.S)
LI_RE = re.compile(r"<li>(.*?)</li>", re.S)
EMAIL_RE = re.compile(r"[\w.+-]+@tu\.ac\.th", re.I)
EN_NAME_RE = re.compile(r"(?:(?:Assoc(?:iation)?\.?|Asst\.?)\s*)?(?:Professor\.?|Prof\.?\s+)*"
                        r"((?:[A-Z][A-Za-z'.-]+)(?:\s+[A-Z][A-Za-z'.-]+){1,3})")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
DOI_RE = re.compile(r"https?://(?:doi\.org|dx\.doi\.org)/\S+")
IMG_URL_RE = re.compile(r'<img[^>]*src="([^"]+)"')
RANK_RE = re.compile(r"(รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|ศาสตราจารย์|อาจารย์)(?:\s+|)(ดร\.)?")

# label normalization for section headers (they contain <br> and stray whitespace)
def norm_label(h6_html: str) -> str:
    return re.sub(r"\s+", "", TAG_RE.sub("", h6_html))


def academic_title_from_rank_tokens(rank_text: str) -> str:
    has_dr = bool(re.search(r"ดร\.", rank_text))
    if "รองศาสตราจารย์" in rank_text:
        t = "รศ."
    elif "ผู้ช่วยศาสตราจารย์" in rank_text:
        t = "ผศ."
    elif "ศาสตราจารย์" in rank_text:
        t = "ศ."
    elif re.search(r"(?<!วิชา)อาจารย์", rank_text):
        t = "อ."
    else:
        t = ""
    return (t + "ดร.") if (has_dr and t) else (t or ("ดร." if has_dr else ""))


def clean_li_items(seg_html):
    out = []
    for li in LI_RE.findall(seg_html):
        s = re.sub(r"\s+", " ", TAG_RE.sub(" ", li)).strip()
        if s and s not in out:
            out.append(s)
    if not out:  # some sections use <p> instead of <ul>
        for p in re.findall(r"<p[^>]*>(.*?)</p>", seg_html, re.S):
            s = re.sub(r"\s+", " ", TAG_RE.sub(" ", p)).strip()
            if s and s not in out:
                out.append(s)
    return out


def pub_to_dict(citation: str) -> dict:
    text = citation.strip().strip("“”\"")
    doi = DOI_RE.search(text)
    year = None
    for m in YEAR_RE.finditer(text):
        y = int(m.group(0))
        if 1980 <= y <= 2030:
            year = y
    return {
        "title": text,
        "venue": "คณะนิติศาสตร์ มธ. (ผลงานวิชาการคัดสรร)",
        "url": doi.group(0).rstrip(".,") if doi else None,
        "year": year,
        "citation_count": 0,
    }


def main():
    db = SessionLocal()
    state = ExtractionAgentState(
        session_id=f"tu_law_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        target_university_th=UNIV_TH,
        target_university_en=UNIV_EN,
        target_faculty_th=FAC_TH,
        target_faculty_en=FAC_EN,
    )
    reducer = FacultyStateReducer(db_session=db)
    client = httpx.Client(timeout=httpx.Timeout(90, connect=20),
                          headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)

    records, page = [], 1
    while True:
        for attempt in range(4):
            try:
                r = client.get(TEACHER_API, params={"per_page": 100, "page": page})
                r.raise_for_status()
                batch = r.json()
                break
            except Exception as e:
                print(f"  page {page} attempt {attempt+1} failed: {type(e).__name__}")
                time.sleep(4 * (attempt + 1))
        else:
            raise RuntimeError(f"teacher API page {page} unreachable after retries")
        if not batch:
            break
        records.extend(batch)
        total = int(r.headers.get("X-WP-Total", len(records)))
        print(f"page {page}: {len(batch)} (total {total}, have {len(records)})")
        if len(records) >= total:
            break
        page += 1
    records = {rec["id"]: rec for rec in records}.values()
    records = list(records)
    print(f"unique teacher posts: {len(records)}")

    # one batched media lookup for profile photos (featured ids)
    media_ids = sorted({rec["featured_media"] for rec in records if rec.get("featured_media")})
    img_by_id = {}
    for i in range(0, len(media_ids), 100):
        for attempt in range(3):
            try:
                mr = client.get(MEDIA_API, params={"include": ",".join(map(str, media_ids[i:i+100])),
                                                   "per_page": 100})
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
                mr = None
        if mr is not None and mr.status_code == 200:
            for m in mr.json():
                img_by_id[m["id"]] = m.get("source_url") or ""

    profiles, no_email, no_rank = [], 0, 0
    for i, rec in enumerate(records, 1):
        th_name = re.sub(r"\s+", " ", TAG_RE.sub("", rec["title"]["rendered"])).strip()
        if not re.search(r"[฀-๿]", th_name):
            continue
        content = rec["content"]["rendered"]
        # content.rendered keeps raw vc shortcodes + html. Inline icon-list JS blobs
        # "(function($){...})(jQuery);" leak as visible text with the site's related-teacher
        # widget (OTHER lecturers' names!) — strip the blobs; the visible latin name between
        # them is the widget's, so we take the English name from the post SLUG instead.
        content = WIDGET_JS_RE.sub(" ", content)
        plain = SCRIPT_RE.sub(" ", content)
        plain = re.sub(r"\[[^\]]*\]", " ", plain)
        text = re.sub(r"\s+", " ", TAG_RE.sub(" ", plain))
        email_m = EMAIL_RE.search(text) or ALL_EMAIL_RE.search(text[:300])
        email = email_m.group(0).lower() if email_m else None
        if not email:
            no_email += 1
        # rank token — look in the header area near the Thai name (first ~300 chars)
        header = text[:text.find("การศึกษา")] if "การศึกษา" in text[:1000] else text[:400]
        rank_m = RANK_RE.search(header)
        title = academic_title_from_rank_tokens(rank_m.group(0)) if rank_m else ""
        if not title:
            no_rank += 1
        education, interests, pubs = [], [], []
        for h6_html, seg in H6_RE.findall(plain):
            label = norm_label(h6_html)
            if label.startswith("การศึกษา"):
                education = [DATE_PREFIX_RE.sub("", s) for s in clean_li_items(seg)]
            elif label.startswith("ความเชี่ยวชาญ"):
                for it in clean_li_items(seg):
                    interests.extend([x.strip() for x in re.split(r"[,؛;]| และ ", it) if len(x.strip()) > 1])
            elif "ผลงาน" in label and "คัดสรร" in label:
                pubs = clean_li_items(seg)[:12]
        # English name from the post slug — deterministic, cannot be polluted by the
        # related-teacher widget text (WP slugs are romanizations of the person's name).
        first, last = None, None
        slug_tokens = [t for t in rec["slug"].split("-") if re.match(r"^[a-z]+$", t)]
        if len(slug_tokens) >= 2:
            first = slug_tokens[0].capitalize()
            last = " ".join(w.capitalize() for w in slug_tokens[1:])
        img = img_by_id.get(rec.get("featured_media")) or None
        profiles.append(RawFacultyProfile(
            full_name_th=(title + " " + th_name).strip(),
            academic_title_th=title or None,
            first_name=first,
            last_name=last,
            email=email,
            image_url=img,
            profile_url=rec["link"],
            education=education,
            research_interests=interests[:10],
            featured_publications=pubs,   # strings for now; converted post-reducer
        ))
        if i % 20 == 0:
            print(f"  ...{i}/{len(records)} parsed, kept={len(profiles)}")

    patch = FacultyStatePatch(new_profiles=profiles,
                              summary_of_changes=f"Law TU teacher API: {len(profiles)} parsed")
    state = reducer.apply_patch(state, patch, step_tokens=0)
    state.visited_urls.append(TEACHER_API)
    state.status = "completed"

    # post-reducer: citations -> enrichment-compatible dict shape (string already sanitized)
    for fac in state.faculties.values():
        fac["featured_publications"] = [pub_to_dict(p) if isinstance(p, str) else p
                                        for p in fac.get("featured_publications", [])]
    save_state_checkpoint(state, output_dir="backend/data/agent_states")

    out = os.path.join("backend", "scripts", "data_sources", "tu_law_api_extracted.py")
    code = ("# Auto-generated from law.tu.ac.th WordPress teacher API via SKILL.state Reducer "
            f"(Session: {state.session_id})\nimport pprint\nEXTRACTED_FACULTIES = "
            + pprint.pformat(list(state.faculties.values()), width=120) + "\n")
    io.open(out, "w", encoding="utf-8").write(code)
    db.close()
    print(f"✨ TU Law: {len(profiles)} parsed ({no_email} without email, {no_rank} without rank) "
          f"-> {len(state.faculties)} verified -> {out}")


if __name__ == "__main__":
    main()
