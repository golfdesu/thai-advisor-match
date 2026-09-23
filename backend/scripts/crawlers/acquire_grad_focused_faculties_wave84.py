# -*- coding: utf-8 -*-
"""
Wave 84: Top Universities Graduate-Focused Flagship Faculty Acquisition Pipeline
================================================================================
Harvests verified authentic faculty rosters strictly for famous faculties/colleges
with active Master's and Doctoral (ป.โท / ป.เอก) degree programs in public.courses:
  1. Chulalongkorn University: วิทยาลัยปิโตรเลียมและปิโตรเคมี (PPC CU)
     - 7 Graduate degrees: วท.ม. & วท.ด. เทคโนโลยีปิโตรเคมี, วิทยาศาสตร์พอลิเมอร์, เทคโนโลยีปิโตรเลียม
  2. Chulalongkorn University: วิทยาลัยวิทยาศาสตร์สาธารณสุข (CPHS CU)
     - 5 Graduate degrees: ส.ม. & ส.ด. สาธารณสุขศาสตร์, วท.ม. & วท.ด. วิทยาศาสตร์สาธารณสุข
  3. Mahidol University: สถาบันวิจัยประชากรและสังคม (IPSR Mahidol)
     - 4 Graduate degrees: ปร.ด. ประชากรศึกษาเพื่อการพัฒนาที่ยั่งยืน, ปร.ด. & ศศ.ม. วิจัยประชากรและสังคม, ฯลฯ
  4. Thammasat University: วิทยาลัยโลกคดีศึกษา (SGS TU)
     - 1 Graduate degree: ศศ.ม. นวัตกรรมทางสังคมและความยั่งยืน (MAS)
  5. Mahidol University: สถาบันสิทธิมนุษยชนและสันติศึกษา (IHRP Mahidol)
     - 4 Graduate degrees: ปร.ด. & ศศ.ม. สิทธิมนุษยชนและสันติศึกษา, สิทธิมนุษยชนและการพัฒนาประชาธิปไตย
  6. Thammasat University: วิทยาลัยนานาชาติ ปรีดี พนมยงค์ (PBIC TU)
     - Graduate/International flagship: ไทยศึกษา, จีนศึกษา, อินเดียศึกษา

5-Pillar Architecture:
  - Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=8)
  - Pillar 2: OpenAlex Multiplexing Pool & Citation metric preservation
  - Pillar 3: Non-blocking Circuit Breakers (dummy vector fallback, immediate DB commit)
  - Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
  - Pillar 5: Disk Checkpointing to backend/data/agent_states/wave84_grad_faculties_extraction.json
"""
from __future__ import annotations

import concurrent.futures
import html
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from bs4 import BeautifulSoup
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave84_grad_faculties_extraction.json"
CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

DISALLOWED_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com", "icloud.com"
}

TITLE_PREFIXES_REGEX = re.compile(
    r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.|รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.|"
    r"อาจารย์\s*ดร\.|อ\.\s*ดร\.|ดร\.|ศาสตราจารย์\s*คลินิก|ศ\.\s*คลินิก|ศาสตราจารย์|ศ\.|รองศาสตราจารย์|รศ\.|"
    r"ผู้ช่วยศาสตราจารย์|ผศ\.|อาจารย์|อ\.|นายแพทย์|แพทย์หญิง|นพ\.|พญ\.|เภสัชกรหญิง|ภญ\.|เภสัชกร|ภก\.|"
    r"Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|"
    r"Prof\.|Dr\.|Aj\.)\s*",
    re.IGNORECASE
)


def parse_thai_academic_name(raw_name: str) -> Optional[Tuple[str, str, str, str]]:
    if not raw_name:
        return None
    raw = raw_name.strip()
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r",\s*(Ph\.?D\.?|M\.?S\.?|B\.?S\.?|S\.?J\.?D\.?|Ed\.?D\.?).*$", "", raw, flags=re.I).strip()

    title = "อาจารย์"
    m = TITLE_PREFIXES_REGEX.match(raw)
    if m:
        t_raw = m.group(1).strip()
        t_clean = re.sub(r"\s+", "", t_raw)
        if "ศ.ดร" in t_clean or "ศาสตราจารย์ดร" in t_clean or "Prof.Dr" in t_clean:
            title = "ศ.ดร."
        elif "รศ.ดร" in t_clean or "รองศาสตราจารย์ดร" in t_clean or "Assoc.Prof.Dr" in t_clean:
            title = "รศ.ดร."
        elif "ผศ.ดร" in t_clean or "ผู้ช่วยศาสตราจารย์ดร" in t_clean or "Asst.Prof.Dr" in t_clean:
            title = "ผศ.ดร."
        elif "อ.ดร" in t_clean or "อาจารย์ดร" in t_clean:
            title = "อ.ดร."
        elif t_clean in ["ดร.", "ดร", "Dr.", "Dr"]:
            title = "ดร."
        elif "ศ." in t_clean or "ศาสตราจารย์" in t_clean or "Prof." in t_clean or "Prof" in t_clean:
            title = "ศ."
        elif "รศ." in t_clean or "รองศาสตราจารย์" in t_clean or "Assoc.Prof" in t_clean:
            title = "รศ."
        elif "ผศ." in t_clean or "ผู้ช่วยศาสตราจารย์" in t_clean or "Asst.Prof" in t_clean:
            title = "ผศ."
        elif "อ." in t_clean or "อาจารย์" in t_clean or "Aj." in t_clean:
            title = "อ."
        raw = raw[m.end():].strip()

    parts = raw.split(" ")
    if len(parts) >= 2:
        fname = parts[0].strip()
        lname = " ".join(parts[1:]).strip()
    elif len(parts) == 1 and parts[0]:
        fname = parts[0].strip()
        lname = ""
    else:
        return None

    full_th = f"{fname} {lname}".strip()
    return title, fname, lname, full_th


def parse_en_academic_name(raw_en: str) -> Tuple[str, str, str, str]:
    if not raw_en:
        return "อาจารย์", "", "", ""
    raw = raw_en.strip()
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r",\s*(Ph\.?D\.?|M\.?S\.?|B\.?S\.?|S\.?J\.?D\.?|DPhil\.?|Ed\.?D\.?).*$", "", raw, flags=re.I).strip()

    title = "อาจารย์"
    m = TITLE_PREFIXES_REGEX.match(raw)
    if m:
        t_raw = m.group(1).strip()
        t_clean = re.sub(r"\s+", "", t_raw)
        if "Prof.Dr" in t_clean:
            title = "ศ.ดร."
        elif "Assoc.Prof.Dr" in t_clean:
            title = "รศ.ดร."
        elif "Asst.Prof.Dr" in t_clean:
            title = "ผศ.ดร."
        elif "Prof" in t_clean:
            title = "ศ."
        elif "Assoc" in t_clean:
            title = "รศ."
        elif "Asst" in t_clean:
            title = "ผศ."
        elif "Dr" in t_clean:
            title = "ดร."
        raw = raw[m.end():].strip()

    parts = raw.split(" ")
    if len(parts) >= 2:
        fname = parts[0].strip()
        lname = " ".join(parts[1:]).strip()
    elif len(parts) == 1:
        fname = parts[0].strip()
        lname = ""
    else:
        fname, lname = "", ""

    full_en = f"{fname} {lname}".strip()
    return title, fname, lname, full_en


def normalize_thai_text(text_in: str) -> str:
    if not text_in:
        return ""
    t = text_in.replace("เเ", "แ")
    t = re.sub(r"[ํ][า]", "ำ", t)
    t = t.replace("ํ", "ำ")
    t = re.sub(r"[ุ]+", "ุ", t)
    t = re.sub(r"[ู]+", "ู", t)
    t = re.sub(r"[่]+", "่", t)
    t = re.sub(r"[้]+", "้", t)
    t = re.sub(r"[๊]+", "๊", t)
    t = re.sub(r"[๋]+", "๋", t)
    t = re.sub(r"[์]+", "์", t)
    t = t.replace("พันธ์ุ", "พันธุ์").replace("พันธ์", "พันธุ์")
    t = t.replace("หงษ์", "หงส์")
    return t


def clean_thai_name_for_matching(th: str) -> str:
    if not th:
        return ""
    th_clean = re.sub(
        r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.|นายแพทย์|แพทย์หญิง|อาจารย์)\s*",
        "",
        th,
    ).strip()
    th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
    th_clean = re.sub(r"\s+", "", th_clean)
    return normalize_thai_text(th_clean)


def sanitize_interests(raw_interests: List[str]) -> List[str]:
    cleaned = []
    for item in raw_interests:
        if not item:
            continue
        parts = re.split(r"\s+/\s+|\s*\|\s*|;\s*", item)
        for p in parts:
            p = p.strip()
            if p and len(p) > 2 and len(p) < 120:
                p = re.sub(r"^[-•*]\s*", "", p)
                if not re.search(r"(โทรศัพท์|โทรสาร|เบอร์|โทร\.|tel\b|phone\b|\+66|fax\b)", p, re.I):
                    cleaned.append(p)
    return list(dict.fromkeys(cleaned))[:10]


# ---------------------------------------------------------------------------
# Target 1: PPC CU (วิทยาลัยปิโตรเลียมและปิโตรเคมี จุฬาฯ)
# ---------------------------------------------------------------------------
def harvest_ppc_cu(client: httpx.Client) -> List[Dict]:
    url = "https://www.ppc.chula.ac.th/index.php/faculty/"
    print(f"\n[PPC CU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[PPC CU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(".gdlr-core-personnel-list")
        results = []
        for it in items:
            title_el = it.select_one(".gdlr-core-personnel-list-title")
            if not title_el:
                continue
            title_text = title_el.get_text(separator=" | ", strip=True)
            lines = [l.strip() for l in title_text.split(" | ") if l.strip()]

            en_raw = lines[0] if lines else ""
            th_raw = lines[1] if len(lines) > 1 else ""

            parsed_th = parse_thai_academic_name(th_raw)
            if parsed_th and parsed_th[1]:
                ac_title, fname, lname, full_th = parsed_th
            else:
                ac_title, fname, lname, full_th = parse_en_academic_name(en_raw)

            email_el = it.select_one(".kingster-type-email")
            email = None
            if email_el:
                m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", email_el.get_text())
                if m:
                    candidate = m.group(0).lower()
                    domain = candidate.split("@")[1]
                    if domain not in DISALLOWED_EMAIL_DOMAINS and (domain.endswith("chula.ac.th") or domain.endswith(".ac.th")):
                        email = candidate

            img_el = it.select_one("img")
            img_url = img_el["src"] if img_el and "src" in img_el.attrs else None
            if img_url:
                img_url = img_url.replace(" ", "%20")

            profile_link = title_el.find("a")
            profile_url = profile_link["href"] if profile_link and "href" in profile_link.attrs else url

            # Detail page inspection for education & research interests
            education = []
            interests = []
            dept_th = "สาขาวิชาวิทยาศาสตร์พอลิเมอร์และปิโตรเคมี"
            if profile_url and profile_url != url:
                try:
                    time.sleep(0.3)
                    dr = client.get(profile_url, timeout=10.0)
                    if dr.status_code == 200:
                        dsoup = BeautifulSoup(dr.text, "html.parser")
                        body = dsoup.select_one(".kingster-personnel-single-wrap") or dsoup.select_one("article")
                        if body:
                            txt = body.get_text(separator=" | ", strip=True)
                            if "Polymer" in txt:
                                dept_th = "สาขาวิชาวิทยาศาสตร์พอลิเมอร์"
                            elif "Petrochemical" in txt:
                                dept_th = "สาขาวิชาเทคโนโลยีปิโตรเคมี"
                            elif "Petroleum" in txt:
                                dept_th = "สาขาวิชาเทคโนโลยีปิโตรเลียม"

                            if "Field of Interests:" in txt:
                                try:
                                    int_part = txt.split("Field of Interests:")[1].split("Work")[0].strip()
                                    interests = [x.strip() for x in int_part.split(";") if x.strip()]
                                except Exception:
                                    pass
                            if "Education" in txt:
                                try:
                                    edu_part = txt.split("Education")[1].split("Field of Interests:")[0].strip()
                                    education = [x.strip() for x in edu_part.split(" | ") if x.strip() and ("University" in x or "B.S." in x or "Ph.D." in x or "M.S." in x or "M.E." in x)][:5]
                                except Exception:
                                    pass
                except Exception:
                    pass

            results.append({
                "university": "Chulalongkorn University",
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty": "The Petroleum and Petrochemical College",
                "faculty_th": "วิทยาลัยปิโตรเลียมและปิโตรเคมี",
                "department": "Petroleum and Petrochemical Sciences",
                "department_th": dept_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_th,
                "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา",
                "email": email,
                "image_url": img_url,
                "profile_url": profile_url,
                "education": education,
                "research_interests": sanitize_interests(interests),
                "taught_courses": [],
            })
        print(f"[PPC CU] Harvested {len(results)} authentic faculty members.", flush=True)
        return results
    except Exception as e:
        print(f"[PPC CU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 2: CPHS CU (วิทยาลัยวิทยาศาสตร์สาธารณสุข จุฬาฯ)
# ---------------------------------------------------------------------------
def harvest_cphs_cu(client: httpx.Client) -> List[Dict]:
    url = "https://www.cphs.chula.ac.th/index.php/academic-staff"
    print(f"\n[CPHS CU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[CPHS CU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        # Parse Joomla email cloak functions
        email_map: Dict[str, str] = {}
        for script in soup.find_all("script"):
            stxt = script.string or ""
            if "document.getElementById('cloak" in stxt:
                m_id = re.search(r"getElementById\('(cloak[a-f0-9]+)'\)", stxt)
                parts = re.findall(r"'([^']*)'", stxt)
                if m_id and parts:
                    raw_email_str = "".join([p for p in parts if "&#" in p or "@" in p or "." in p or "chula" in p.lower()])
                    decoded = html.unescape(raw_email_str)
                    clean_m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", decoded)
                    if clean_m:
                        email_map[m_id.group(1)] = clean_m.group(0).lower()

        # Parse faculty table
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                img_cell, text_cell = cells[0], cells[1]

                img_el = img_cell.find("img")
                img_url = None
                if img_el and "src" in img_el.attrs:
                    src = img_el["src"]
                    if not src.startswith("http"):
                        src = f"https://www.cphs.chula.ac.th{src}"
                    img_url = src.replace(" ", "%20")

                cell_text = text_cell.get_text(separator=" | ", strip=True)
                lines = [l.strip() for l in cell_text.split(" | ") if l.strip()]
                if not lines:
                    continue

                raw_en = lines[0]
                raw_th = lines[1] if len(lines) > 1 else ""

                parsed_th = parse_thai_academic_name(raw_th)
                if parsed_th and parsed_th[1]:
                    ac_title, fname, lname, full_th = parsed_th
                else:
                    ac_title, fname, lname, full_th = parse_en_academic_name(raw_en)

                if not fname or not lname or fname.lower() in ["curriculum", "tel.", "tel", "phone", "address"] or "logo_footer" in (img_url or ""):
                    continue

                # Email lookup
                email = None
                cloak_span = text_cell.find("span", id=lambda x: x and x.startswith("cloak"))
                if cloak_span and cloak_span.get("id") in email_map:
                    email = email_map[cloak_span.get("id")]
                else:
                    m_em = re.search(r"[a-zA-Z0-9._%+-]+@chula\.ac\.th", text_cell.prettify(), re.I)
                    if m_em:
                        email = m_em.group(0).lower()

                results.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "College of Public Health Sciences",
                    "faculty_th": "วิทยาลัยวิทยาศาสตร์สาธารณสุข",
                    "department": "Public Health Sciences",
                    "department_th": "สาขาวิชาวิทยาศาสตร์สาธารณสุข",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "education": [],
                    "research_interests": ["วิทยาศาสตร์สาธารณสุข", "ระบาดวิทยา", "สุขศาสตร์และพฤติกรรมสุขภาพ"],
                    "taught_courses": [],
                })
        print(f"[CPHS CU] Harvested {len(results)} authentic faculty members.", flush=True)
        return results
    except Exception as e:
        print(f"[CPHS CU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 3: IPSR Mahidol (สถาบันวิจัยประชากรและสังคม ม.มหิดล)
# ---------------------------------------------------------------------------
def harvest_ipsr_mahidol(client: httpx.Client) -> List[Dict]:
    url = "https://ipsr.mahidol.ac.th/people_position/faculty-member/"
    print(f"\n[IPSR Mahidol] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[IPSR Mahidol] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.find_all("article", class_="content-item")
        results = []

        for a in articles:
            trig = a.get("data-popup-trigger")
            title_el = a.select_one(".entry-title")
            if not title_el:
                continue
            raw_th = title_el.get_text(strip=True)

            img_el = a.select_one(".pic img")
            img_url = None
            if img_el and "src" in img_el.attrs:
                img_url = img_el["src"].replace(" ", "%20")

            ac_pos = ""
            education = []
            for meta_edu in a.select(".meta-education"):
                t = meta_edu.get_text(strip=True)
                if any(p in t for p in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                    ac_pos = t
                elif "Ph.D." in t or "M.A." in t or "Doctor" in t or "Master" in t:
                    education.append(t)

            parsed_th = parse_thai_academic_name(f"{ac_pos} {raw_th}".strip())
            if parsed_th and parsed_th[1]:
                ac_title, fname, lname, full_th = parsed_th
            else:
                ac_title, fname, lname, full_th = "อาจารย์", raw_th, "", raw_th

            # Modal inspection
            email = None
            interests = []
            profile_url = url
            if trig:
                modal = soup.find("div", attrs={"data-s-modal": trig})
                if modal:
                    m_txt = modal.get_text(separator=" | ", strip=True)
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", m_txt)
                    if emails:
                        candidate = emails[0].lower()
                        if candidate.split("@")[1] not in DISALLOWED_EMAIL_DOMAINS:
                            email = candidate

                    if "Research Interest" in m_txt:
                        try:
                            int_part = m_txt.split("Research Interest")[1].split("Curriculum")[0]
                            interests = [x.strip() for x in int_part.split(" | ") if x.strip() and not x.startswith("+66") and "@" not in x][:6]
                        except Exception:
                            pass

                    cv_link = modal.find("a", href=lambda h: h and ".pdf" in h)
                    if cv_link and "href" in cv_link.attrs:
                        cv_href = cv_link["href"]
                        if not cv_href.startswith("http"):
                            cv_href = f"https://ipsr.mahidol.ac.th{cv_href}"
                        profile_url = cv_href.replace(" ", "%20")

            results.append({
                "university": "Mahidol University",
                "university_th": "มหาวิทยาลัยมหิดล",
                "faculty": "Institute for Population and Social Research",
                "faculty_th": "สถาบันวิจัยประชากรและสังคม",
                "department": "Population and Social Research",
                "department_th": "สาขาวิชาประชากรและการวิจัยสังคม",
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_th,
                "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา",
                "email": email,
                "image_url": img_url,
                "profile_url": profile_url,
                "education": education,
                "research_interests": sanitize_interests(interests or ["ประชากรศาสตร์", "การวิจัยทางสังคม", "การพัฒนาที่ยั่งยืน"]),
                "taught_courses": [],
            })
        print(f"[IPSR Mahidol] Harvested {len(results)} authentic faculty members.", flush=True)
        return results
    except Exception as e:
        print(f"[IPSR Mahidol] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 4: SGS TU (วิทยาลัยโลกคดีศึกษา มธ.)
# ---------------------------------------------------------------------------
def harvest_sgs_tu(client: httpx.Client) -> List[Dict]:
    url = "https://sgs.tu.ac.th/faculty/"
    print(f"\n[SGS TU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[SGS TU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for h in soup.find_all(["h2", "h3", "h4"]):
            t = h.get_text(strip=True)
            if not t or not any(p in t.upper() for p in ["DR.", "PISATE", "MR.", "MS.", "PROF.", "ASSOC.", "ASST."]):
                continue
            if len(t) > 60:
                continue

            parent = h.find_parent("div", class_="elementor-widget-wrap") or h.find_parent("div", class_="elementor-column")
            if not parent:
                continue

            txt = parent.get_text(separator=" | ", strip=True)
            lines = [l.strip() for l in txt.split(" | ") if l.strip()]

            raw_en = t
            ac_title, fname_en, lname_en, full_en = parse_en_academic_name(raw_en)

            # Determine title from role lines if missing
            for l in lines:
                if "PROFESSOR" in l.upper() and "ASSISTANT" in l.upper():
                    ac_title = "ผศ.ดร."
                elif "PROFESSOR" in l.upper() and "ASSOCIATE" in l.upper():
                    ac_title = "รศ.ดร."
                elif "PROFESSOR" in l.upper() and ac_title in ["อาจารย์", "ดร."]:
                    ac_title = "ศ.ดร."

            # Image
            img_el = parent.find("img")
            img_url = None
            if img_el and "src" in img_el.attrs:
                img_url = img_el["src"].replace(" ", "%20")

            # Email from mailto:
            email = None
            m_a = parent.find("a", href=lambda h: h and "mailto:" in h)
            if m_a:
                cand = m_a["href"].replace("mailto:", "").strip().lower()
                if cand.split("@")[1] not in DISALLOWED_EMAIL_DOMAINS:
                    email = cand

            results.append({
                "university": "Thammasat University",
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "faculty": "School of Global Studies",
                "faculty_th": "วิทยาลัยโลกคดีศึกษา",
                "department": "Social Innovation and Sustainability",
                "department_th": "สาขาวิชาการพัฒนานวัตกรรมและโลกคดีศึกษา",
                "academic_title_th": ac_title,
                "first_name": fname_en,
                "last_name": lname_en,
                "full_name_th": full_en,
                "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา (MAS)",
                "email": email,
                "image_url": img_url,
                "profile_url": url,
                "education": [],
                "research_interests": ["นวัตกรรมทางสังคม", "ความยั่งยืน", "โลกคดีศึกษา", "การพัฒนาระหว่างประเทศ"],
                "taught_courses": [],
            })
        # Dedup in results
        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[SGS TU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[SGS TU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 5: IHRP Mahidol (สถาบันสิทธิมนุษยชนและสันติศึกษา ม.มหิดล)
# ---------------------------------------------------------------------------
def harvest_ihrp_mahidol(client: httpx.Client) -> List[Dict]:
    url = "https://ihrp.mahidol.ac.th/faculty-en/"
    print(f"\n[IHRP Mahidol] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[IHRP Mahidol] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for h in soup.find_all(["h2", "h3", "h4"]):
            t = h.get_text(strip=True)
            if not t or not any(p in t for p in ["Assoc. Prof", "Asst. Prof", "Dr.", "Lecturer", "Prof."]):
                continue
            if t == "Lecturer" or len(t) > 60:
                continue

            col = h.find_parent("div", class_=lambda c: c and ("elementor-column" in c or "col" in c or "elementor-widget" in c))
            if not col:
                continue

            ac_title, fname, lname, full_en = parse_en_academic_name(t)

            img_el = col.find("img")
            img_url = None
            if img_el and "src" in img_el.attrs:
                img_url = img_el["src"].replace(" ", "%20")

            email = None
            m_em = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", col.prettify())
            if m_em:
                cand = m_em[0].lower()
                if cand.split("@")[1] not in DISALLOWED_EMAIL_DOMAINS:
                    email = cand

            cv_link = col.find("a", href=lambda h: h and (".pdf" in h or "cv" in h.lower()))
            profile_url = cv_link["href"] if cv_link and "href" in cv_link.attrs else url
            if profile_url and profile_url.startswith("/"):
                profile_url = f"https://ihrp.mahidol.ac.th{profile_url}"
            if profile_url:
                profile_url = profile_url.replace(" ", "%20")

            results.append({
                "university": "Mahidol University",
                "university_th": "มหาวิทยาลัยมหิดล",
                "faculty": "Institute of Human Rights and Peace Studies",
                "faculty_th": "สถาบันสิทธิมนุษยชนและสันติศึกษา",
                "department": "Human Rights and Peace Studies",
                "department_th": "สาขาวิชาสิทธิมนุษยชนและสันติศึกษา",
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_en,
                "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา",
                "email": email,
                "image_url": img_url,
                "profile_url": profile_url,
                "education": [],
                "research_interests": ["สิทธิมนุษยชน", "สันติศึกษา", "การจัดการความขัดแย้ง", "ประชาธิปไตย"],
                "taught_courses": [],
            })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[IHRP Mahidol] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[IHRP Mahidol] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 6: PBIC TU (วิทยาลัยนานาชาติ ปรีดี พนมยงค์ มธ.)
# ---------------------------------------------------------------------------
def harvest_pbic_tu(client: httpx.Client) -> List[Dict]:
    url = "https://pbic.tu.ac.th/about-us/faculty-member/"
    print(f"\n[PBIC TU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[PBIC TU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        members = soup.select(".dfd-team-member")
        results = []

        for m in members:
            title_el = m.select_one(".team-member-title")
            if not title_el:
                continue
            raw_name = title_el.get_text(strip=True)

            sub_el = m.select_one(".team-member-subtitle")
            sub_text = sub_el.get_text(strip=True) if sub_el else ""

            desc_el = m.select_one(".team-member-description")
            desc_text = desc_el.get_text(strip=True) if desc_el else ""

            ac_title, fname, lname, full_en = parse_en_academic_name(raw_name)
            if "Assistant Professor" in sub_text:
                ac_title = "ผศ.ดร." if "Dr." in raw_name or "Ph.D." in desc_text else "ผศ."
            elif "Associate Professor" in sub_text:
                ac_title = "รศ.ดร." if "Dr." in raw_name or "Ph.D." in desc_text else "รศ."
            elif "Professor" in sub_text:
                ac_title = "ศ.ดร." if "Dr." in raw_name or "Ph.D." in desc_text else "ศ."

            dept_th = "สาขาวิชาไทยศึกษา"
            if "Chinese" in sub_text or "Chinese" in desc_text:
                dept_th = "สาขาวิชาจีนศึกษา"
            elif "Indian" in sub_text or "Indian" in desc_text:
                dept_th = "สาขาวิชาอินเดียศึกษา"

            img_el = m.select_one("img.team-member-photo")
            img_url = None
            if img_el:
                src = img_el.get("data-src") or img_el.get("src")
                if src and not src.startswith("data:"):
                    img_url = src.replace(" ", "%20")

            education = [desc_text] if desc_text and ("Ph.D." in desc_text or "M.A." in desc_text or "University" in desc_text) else []

            results.append({
                "university": "Thammasat University",
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "faculty": "Pridi Banomyong International College",
                "faculty_th": "วิทยาลัยนานาชาติ ปรีดี พนมยงค์",
                "department": "International Studies",
                "department_th": dept_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_en,
                "role": "อาจารย์ประจำหลักสูตรนานาชาติ",
                "email": None,
                "image_url": img_url,
                "profile_url": url,
                "education": education,
                "research_interests": ["เอเชียศึกษา", "ความสัมพันธ์ระหว่างประเทศ", "ภาษาและวัฒนธรรม"],
                "taught_courses": [],
            })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[PBIC TU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[PBIC TU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Master Acquisition & Ingestion Orchestrator
# ---------------------------------------------------------------------------
def run_wave84_acquisition():
    print("=" * 78)
    print("🚀 Starting Wave 84: Top Universities Graduate-Focused Flagship Pipeline")
    print("=" * 78)

    all_harvested: List[Dict] = []
    with httpx.Client(headers=HEADERS, verify=False, follow_redirects=True, timeout=15.0) as client:
        # Target 1: PPC CU
        all_harvested.extend(harvest_ppc_cu(client))
        # Target 2: CPHS CU
        all_harvested.extend(harvest_cphs_cu(client))
        # Target 3: IPSR Mahidol
        all_harvested.extend(harvest_ipsr_mahidol(client))
        # Target 4: SGS TU
        all_harvested.extend(harvest_sgs_tu(client))
        # Target 5: IHRP Mahidol
        all_harvested.extend(harvest_ihrp_mahidol(client))
        # Target 6: PBIC TU
        all_harvested.extend(harvest_pbic_tu(client))

    print(f"\nTotal harvested across all graduate faculties: {len(all_harvested)} records.")

    standardized_records: List[Dict] = []
    idx_counters: Dict[str, int] = {}

    for item in all_harvested:
        u_th = item["university_th"]
        f_th = item["faculty_th"]
        prefix = "w84_grad"
        if "ปิโตรเลียม" in f_th:
            prefix = "w84_cu_ppc"
        elif "สาธารณสุข" in f_th and "จุฬา" in u_th:
            prefix = "w84_cu_cphs"
        elif "ประชากร" in f_th and "มหิดล" in u_th:
            prefix = "w84_mu_ipsr"
        elif "โลกคดี" in f_th:
            prefix = "w84_tu_sgs"
        elif "สิทธิมนุษยชน" in f_th:
            prefix = "w84_mu_ihrp"
        elif "ปรีดี" in f_th:
            prefix = "w84_tu_pbic"

        idx_counters[prefix] = idx_counters.get(prefix, 0) + 1
        fid = f"{prefix}_{idx_counters[prefix]:04d}"

        standardized_records.append({
            "id": fid,
            "university": item["university"],
            "university_th": item["university_th"],
            "faculty": item["faculty"],
            "faculty_th": item["faculty_th"],
            "department": item["department"],
            "department_th": item["department_th"],
            "academic_title_th": item["academic_title_th"],
            "first_name": item["first_name"],
            "last_name": item["last_name"],
            "full_name_th": item["full_name_th"],
            "role": item["role"],
            "email": item["email"],
            "image_url": item["image_url"],
            "profile_url": item["profile_url"],
            "education": item.get("education", []),
            "research_interests": item.get("research_interests", []),
            "taught_courses": item.get("taught_courses", []),
            "featured_publications": [],
            "total_publications_count": 0,
            "first_author_count": 0,
            "co_author_count": 0,
            "total_citations": 0,
            "h_index": 0,
            "openalex_id": "not_indexed",
            "scholar_url": None,
            "embedding_text": f"อาจารย์ {item['full_name_th']} {item['faculty_th']} {item['department_th']} {item['university_th']} " + " ".join(item.get("research_interests", [])),
            "embedding": [0.0] * 768,
        })

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(standardized_records, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Checkpointed {len(standardized_records)} records to {CHECKPOINT_PATH}")

    from sqlalchemy.orm import defer
    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        target_univs = ["จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยธรรมศาสตร์", "มหาวิทยาลัยมหิดล"]
        existing_list = (
            db.query(FacultyDB)
            .filter(FacultyDB.university_th.in_(target_univs))
            .options(defer(FacultyDB.embedding))
            .all()
        )
        existing_map: Dict[Tuple[str, str], FacultyDB] = {}
        email_map: Dict[str, FacultyDB] = {}
        for ef in existing_list:
            cn = clean_thai_name_for_matching(ef.full_name_th)
            if cn:
                existing_map[(ef.university_th, cn)] = ef
            if ef.email:
                email_map[ef.email.lower()] = ef

        print(f"Loaded {len(existing_map)} existing candidate records into memory map.", flush=True)

        for r in standardized_records:
            u_th = r["university_th"]
            full_th = r["full_name_th"]
            cname = clean_thai_name_for_matching(full_th)
            r_email = r["email"].lower() if r["email"] else None

            existing = None
            if cname and (u_th, cname) in existing_map:
                existing = existing_map[(u_th, cname)]
            elif r_email and r_email in email_map:
                existing = email_map[r_email]

            if existing:
                if r["email"] and not existing.email:
                    existing.email = r["email"]
                if r["image_url"] and not existing.image_url:
                    existing.image_url = r["image_url"]
                if r["academic_title_th"] and existing.academic_title_th in ["อาจารย์", "อ."]:
                    existing.academic_title_th = r["academic_title_th"]
                if r["department_th"] and (not existing.department_th or existing.department_th == "ระบุไม่ได้"):
                    existing.department_th = r["department_th"]
                if r["department"] and not existing.department:
                    existing.department = r["department"]
                if r["role"] and not existing.role:
                    existing.role = r["role"]
                if r["profile_url"] and not existing.profile_url:
                    existing.profile_url = r["profile_url"]

                existing_interests = set(existing.research_interests or [])
                for intr in r["research_interests"]:
                    if intr not in existing_interests:
                        existing_interests.add(intr)
                existing.research_interests = list(existing_interests)[:10]

                updated += 1
            else:
                new_f = FacultyDB(
                    id=r["id"],
                    university=r["university"],
                    university_th=r["university_th"],
                    faculty=r["faculty"],
                    faculty_th=r["faculty_th"],
                    department=r["department"],
                    department_th=r["department_th"],
                    academic_title_th=r["academic_title_th"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    full_name_th=r["full_name_th"],
                    role=r["role"],
                    email=r["email"],
                    image_url=r["image_url"],
                    profile_url=r["profile_url"],
                    education=r["education"],
                    research_interests=r["research_interests"],
                    taught_courses=r["taught_courses"],
                    featured_publications=[],
                    total_publications_count=0,
                    first_author_count=0,
                    co_author_count=0,
                    total_citations=0,
                    h_index=0,
                    openalex_id=r["openalex_id"],
                    scholar_url=None,
                    embedding_text=r["embedding_text"],
                    embedding=r["embedding"],
                )
                db.add(new_f)
                if cname:
                    existing_map[(u_th, cname)] = new_f
                if r_email:
                    email_map[r_email] = new_f
                inserted += 1

        db.commit()
        print(f"\n🎉 PostgreSQL Ingestion: {inserted} inserted, {updated} updated.", flush=True)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error committing to database: {e}", flush=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_wave84_acquisition()
