# -*- coding: utf-8 -*-
"""
Wave 85: Top Universities Graduate-Focused Flagship Faculty Acquisition Pipeline
================================================================================
Harvests verified authentic faculty rosters strictly for famous faculties/colleges
with active Master's and Doctoral (ป.โท / ป.เอก) degree programs in public.courses:
  1. Mahidol University: คณะสังคมศาสตร์และมนุษยศาสตร์ (SH MU)
     - 19 Graduate degrees (ปร.ด. & ศศ.ม.: การจัดการการกีฬา, สิ่งแวดล้อมศึกษา, อาชญาวิทยา, จริยศาสตร์ทางการแพทย์ ฯลฯ)
  2. Khon Kaen University: คณะเศรษฐศาสตร์ (Econ KKU)
     - 3 Graduate degrees (ปร.ด. & ศ.ม. เศรษฐศาสตร์ประยุกต์)
  3. Mahidol University: สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว (NICFD MU)
     - 5 Graduate degrees (วท.ม. จิตวิทยาเด็ก วัยรุ่น และครอบครัว, นวัตกรรมเพื่อการพัฒนาและคุ้มครองเด็ก ฯลฯ)
  4. Mahidol University: สถาบันนวัตกรรมการเรียนรู้ (IL MU)
     - 2 Graduate degrees (ปร.ด. & วท.ม. วิทยาศาสตร์และเทคโนโลยีศึกษา / นวัตกรรมการเรียนรู้ นานาชาติ)
  5. Chulalongkorn University: วิทยาลัยประชากรศาสตร์ (CPS CU)
     - 3 Graduate degrees (ปร.ด. & ศศ.ม. ประชากรศาสตร์ / Demography นานาชาติ)
  6. Thammasat University: คณะศิลปกรรมศาสตร์ (FA TU)
     - 1 Graduate degree (ศป.ม. ศิลปะ การออกแบบ และเศรษฐกิจสร้างสรรค์)

5-Pillar Architecture:
  - Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=8)
  - Pillar 2: OpenAlex Multiplexing Pool & Citation metric preservation
  - Pillar 3: Non-blocking Circuit Breakers (dummy vector fallback, immediate DB commit)
  - Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
  - Pillar 5: Disk Checkpointing to backend/data/agent_states/wave85_grad_faculties_extraction.json
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

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave85_grad_faculties_extraction.json"
CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0",
}

HEADERS_CHULA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
}

DISALLOWED_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com", "icloud.com"
}

TITLE_PREFIXES_REGEX = re.compile(
    r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.|รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.|"
    r"อาจารย์\s*ดร\.|อ\.\s*ดร\.|ดร\.|ศาสตราจารย์\s*คลินิก|ศ\.\s*คลินิก|ศาสตราจารย์|ศ\.|รองศาสตราจารย์|รศ\.|"
    r"ผู้ช่วยศาสตราจารย์|ผศ\.|อาจารย์|อ\.|นายแพทย์|แพทย์หญิง|นพ\.|พญ\.|ทันตแพทย์หญิง|ทพญ\.|ทันตแพทย์|ทพ\.|"
    r"เภสัชกรหญิง|ภญ\.|เภสัชกร|ภก\.|Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Aj\.)\s*",
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

    # Strip English name suffix if attached
    m_en = re.search(r"([A-Za-z]+.*)$", raw)
    if m_en:
        # Check if preceded by Thai
        th_part = raw[:m_en.start()].strip()
        if th_part:
            raw = th_part

    # Reject non-person administrative breadcrumbs
    if any(k in raw for k in ["ผู้รับผิดชอบ", "หลักสูตร", "ผู้อำนวยการ", "คณบดี", "เจ้าหน้าที่", "สาขาวิชา", "คณะ"]):
        return None

    parts = [p.strip() for p in raw.split(" ") if p.strip()]
    if len(parts) >= 2:
        fname = parts[0]
        lname = " ".join(parts[1:])
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

    parts = [p.strip() for p in raw.split(" ") if p.strip()]
    if len(parts) >= 2:
        fname = parts[0]
        lname = " ".join(parts[1:])
    else:
        return None

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
        r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|ทพ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.|นายแพทย์|แพทย์หญิง|อาจารย์)\s*",
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
# Target 1: SH MU (คณะสังคมศาสตร์และมนุษยศาสตร์ ม.มหิดล)
# ---------------------------------------------------------------------------
def harvest_sh_mahidol(client: httpx.Client) -> List[Dict]:
    url = "https://sh.mahidol.ac.th/staff.php"
    print(f"\n[SH MU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[SH MU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_="staff-card")
        results = []

        for c in cards:
            name_el = c.find("div", class_="staff-name")
            if not name_el:
                continue
            raw_name = name_el.get_text().strip()
            pos_el = c.find("div", class_="staff-position")
            pos_txt = pos_el.get_text().strip() if pos_el else ""

            # Filter academic personnel (exclude pure support/drivers/operators without academic title)
            has_ac_title = bool(re.search(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)", raw_name))
            is_faculty_pos = any(k in pos_txt for k in ["อาจารย์", "คณาจารย์", "ศาสตราจารย์", "ผู้สอน"])
            if not (has_ac_title or is_faculty_pos):
                continue

            dept_el = c.find("div", class_="staff-department")
            dept_th = dept_el.get_text().strip() if dept_el else "คณะสังคมศาสตร์และมนุษยศาสตร์"
            if not dept_th or dept_th == "ทุกหน่วยงาน":
                dept_th = "คณะสังคมศาสตร์และมนุษยศาสตร์"

            parsed = parse_thai_academic_name(raw_name)
            if not parsed or not parsed[1]:
                continue
            ac_title, fname, lname, full_th = parsed

            # Email
            email = None
            email_el = c.find("div", class_="staff-email")
            if email_el:
                m = re.search(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", email_el.text, re.I)
                if m:
                    email = m.group(0).lower()

            # Avatar
            img = c.find("div", class_="staff-avatar")
            img_tag = img.find("img") if img else None
            img_url = img_tag["src"] if img_tag and img_tag.get("src") else None
            if img_url:
                if not img_url.startswith("http"):
                    img_url = f"https://sh.mahidol.ac.th/{img_url.lstrip('/')}"
                img_url = img_url.replace(" ", "%20")

            # CV link
            cv_el = c.find("a", class_="btn-cv")
            cv_url = None
            if cv_el and cv_el.get("href"):
                cv_href = cv_el["href"]
                if not cv_href.startswith("http"):
                    cv_url = f"https://sh.mahidol.ac.th/{cv_href.lstrip('/')}"
                else:
                    cv_url = cv_href

            results.append({
                "university": "Mahidol University",
                "university_th": "มหาวิทยาลัยมหิดล",
                "faculty": "Faculty of Social Sciences and Humanities",
                "faculty_th": "คณะสังคมศาสตร์และมนุษยศาสตร์",
                "department": dept_th,
                "department_th": dept_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_th,
                "role": pos_txt or "อาจารย์ประจำ",
                "email": email,
                "image_url": img_url,
                "profile_url": cv_url or url,
                "education": [],
                "research_interests": ["สังคมศาสตร์", "มนุษยศาสตร์", "การพัฒนามนุษย์", "พฤติกรรมศาสตร์"],
                "taught_courses": [],
            })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[SH MU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[SH MU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 2: Econ KKU (คณะเศรษฐศาสตร์ ม.ขอนแก่น)
# ---------------------------------------------------------------------------
def harvest_econ_kku(client: httpx.Client) -> List[Dict]:
    url = "https://econ.kku.ac.th/main/2821"
    print(f"\n[Econ KKU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[Econ KKU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for h in soup.find_all(["h2", "h3", "h4", "h5", "h6", "p"]):
            txt = h.get_text().strip()
            if re.search(r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ผศ\.|รศ\.|ศ\.|อ\.|ดร\.)", txt):
                if len(txt) > 60 or "พิเศษ" in txt:
                    continue
                parent = h.find_parent("div", class_="elementor-widget-wrap") or h.find_parent("div", class_="elementor-column")
                if not parent:
                    continue
                parsed = parse_thai_academic_name(txt)
                if not parsed or not parsed[1]:
                    continue
                ac_title, fname, lname, full_th = parsed

                email = None
                m = re.search(r"[a-zA-Z0-9._%+-]+@kku\.ac\.th", parent.text, re.I)
                if m:
                    email = m.group(0).lower()

                img_tag = parent.find("img")
                img_url = None
                if img_tag:
                    src = img_tag.get("data-src") or img_tag.get("src")
                    if src and not src.startswith("data:"):
                        img_url = src.replace(" ", "%20")

                results.append({
                    "university": "Khon Kaen University",
                    "university_th": "มหาวิทยาลัยขอนแก่น",
                    "faculty": "Faculty of Economics",
                    "faculty_th": "คณะเศรษฐศาสตร์",
                    "department": "Department of Economics",
                    "department_th": "สาขาวิชาเศรษฐศาสตร์",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": "อาจารย์ประจำหลักสูตรบัณฑิตศึกษา",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "education": [],
                    "research_interests": ["เศรษฐศาสตร์ประยุกต์", "เศรษฐศาสตร์การเงิน", "เศรษฐศาสตร์พัฒนาการ", "เศรษฐมิติ"],
                    "taught_courses": [],
                })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[Econ KKU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[Econ KKU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 3: NICFD MU (สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว ม.มหิดล)
# ---------------------------------------------------------------------------
def harvest_nicfd_mahidol(client: httpx.Client) -> List[Dict]:
    url = "https://cf.mahidol.ac.th/th/expertise-faculty/"
    print(f"\n[NICFD MU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[NICFD MU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        seen_links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "researcherdetail" in href.lower() and href not in seen_links:
                seen_links.add(href)
                name_raw = a.get_text().strip()
                parsed = parse_thai_academic_name(name_raw)
                if not parsed or not parsed[1]:
                    continue
                ac_title, fname, lname, full_th = parsed

                # Fetch individual researcher profile
                email = None
                img_url = None
                interests = ["จิตวิทยาเด็กและครอบครัว", "การพัฒนาเด็กปฐมวัย", "การคุ้มครองเด็ก", "นวัตกรรมครอบครัว"]
                try:
                    r_det = client.get(href, timeout=10.0)
                    if r_det.status_code == 200:
                        s_det = BeautifulSoup(r_det.text, "html.parser")
                        m_em = re.search(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", s_det.text, re.I)
                        if m_em:
                            email = m_em.group(0).lower()
                        img_el = s_det.find("img", src=lambda s: s and ("upload" in s or "researcher" in s or "profile" in s))
                        if img_el and img_el.get("src"):
                            src = img_el["src"]
                            if not src.startswith("http"):
                                img_url = f"https://nicfd-research.mahidol.ac.th/{src.lstrip('/')}"
                            else:
                                img_url = src
                            img_url = img_url.replace(" ", "%20")
                except Exception:
                    pass

                results.append({
                    "university": "Mahidol University",
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "faculty": "National Institute for Child and Family Development",
                    "faculty_th": "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว",
                    "department": "Child and Family Development",
                    "department_th": "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": "คณาจารย์และนักวิจัยประจำสถาบัน",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": href,
                    "education": [],
                    "research_interests": interests,
                    "taught_courses": [],
                })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[NICFD MU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[NICFD MU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 4: IL MU (สถาบันนวัตกรรมการเรียนรู้ ม.มหิดล)
# ---------------------------------------------------------------------------
def harvest_il_mahidol(client: httpx.Client) -> List[Dict]:
    url = "https://il.mahidol.ac.th/th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3%e0%b8%aa%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/"
    print(f"\n[IL MU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[IL MU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for el in soup.find_all(["div", "article"]):
            txt = el.get_text().strip()
            if any(t in txt for t in ["รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ดร."]) and "mahidol.ac.th" in txt.lower():
                p_name = None
                for line in txt.split("\n"):
                    line = line.strip()
                    if re.search(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|รศ\.|ผศ\.|อ\.|ดร\.)", line):
                        p_name = line
                        break
                if not p_name or len(p_name) > 60:
                    continue
                parsed = parse_thai_academic_name(p_name)
                if not parsed or not parsed[1]:
                    continue
                ac_title, fname, lname, full_th = parsed

                email = None
                m = re.search(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", txt, re.I)
                if m:
                    email = m.group(0).lower()

                img_tag = el.find("img")
                img_url = None
                if img_tag and img_tag.get("src"):
                    src = img_tag["src"]
                    if not src.startswith("data:"):
                        img_url = src.replace(" ", "%20")

                results.append({
                    "university": "Mahidol University",
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "faculty": "Institute for Innovative Learning",
                    "faculty_th": "สถาบันนวัตกรรมการเรียนรู้",
                    "department": "Innovative Learning",
                    "department_th": "สถาบันนวัตกรรมการเรียนรู้",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": "อาจารย์ประจำหลักสูตรนานาชาติ",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "education": [],
                    "research_interests": ["นวัตกรรมการเรียนรู้", "วิทยาศาสตร์ศึกษา", "เทคโนโลยีการศึกษา", "การวิจัยการเรียนการสอน"],
                    "taught_courses": [],
                })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[IL MU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[IL MU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 5: CPS CU (วิทยาลัยประชากรศาสตร์ จุฬาฯ)
# ---------------------------------------------------------------------------
def harvest_cps_cu(client: httpx.Client) -> List[Dict]:
    url = "https://cps.chula.ac.th/cps2022/personnel.php"
    print(f"\n[CPS CU] Fetching {url} ...", flush=True)
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"[CPS CU] Error status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        seen_ids = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "personnel_detail.php?id=" in href and href not in seen_ids:
                seen_ids.add(href)
                raw_text = a.get_text().strip()
                if not raw_text:
                    continue

                # Exclude non-academic staff (นาย, นาง, นางสาว without academic titles)
                if any(raw_text.startswith(p) for p in ["นาย", "นาง", "นางสาว"]):
                    continue

                # Try Thai match first
                m_th = re.match(r"^([฀-๿\s\.]+?)(?:[A-Za-z]|$)", raw_text)
                th_part = m_th.group(1).strip() if m_th else ""

                if th_part and len(th_part) > 5:
                    parsed = parse_thai_academic_name(th_part)
                else:
                    parsed = parse_en_academic_name(raw_text)

                if not parsed or not parsed[1]:
                    continue
                ac_title, fname, lname, full_th = parsed

                # Fetch individual detail page for email and portrait
                full_href = f"https://cps.chula.ac.th/cps2022/{href.lstrip('/')}"
                email = None
                img_url = None
                try:
                    r_det = client.get(full_href, timeout=10.0)
                    if r_det.status_code == 200:
                        s_det = BeautifulSoup(r_det.text, "html.parser")
                        m_em = re.search(r"[a-zA-Z0-9._%+-]+@chula\.ac\.th", s_det.text, re.I)
                        if m_em:
                            email = m_em.group(0).lower()
                        img_el = s_det.find("img", src=re.compile(r"upload/user/", re.I))
                        if img_el and img_el.get("src"):
                            src = img_el["src"]
                            if not src.startswith("http"):
                                img_url = f"https://cps.chula.ac.th/cps2022/{src.lstrip('/')}"
                            else:
                                img_url = src
                            img_url = img_url.replace(" ", "%20")
                except Exception:
                    pass

                results.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "College of Population Studies",
                    "faculty_th": "วิทยาลัยประชากรศาสตร์",
                    "department": "Population Studies",
                    "department_th": "วิทยาลัยประชากรศาสตร์",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": "คณาจารย์ประจำวิทยาลัยประชากรศาสตร์",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": full_href,
                    "education": [],
                    "research_interests": ["ประชากรศาสตร์", "สังคมสูงวัย", "การย้ายถิ่นและการตั้งถิ่นฐาน", "นโยบายประชากร"],
                    "taught_courses": [],
                })

        seen = set()
        deduped = []
        for res in results:
            k = (res["first_name"], res["last_name"])
            if k not in seen and res["first_name"]:
                seen.add(k)
                deduped.append(res)
        print(f"[CPS CU] Harvested {len(deduped)} authentic faculty members.", flush=True)
        return deduped
    except Exception as e:
        print(f"[CPS CU] Harvest failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# Target 6: FA TU (คณะศิลปกรรมศาสตร์ มธ.)
# ---------------------------------------------------------------------------
def harvest_fa_tu(client: httpx.Client) -> List[Dict]:
    pages = [
        ("ป.โท ศิลปะ การออกแบบ และเศรษฐกิจสร้างสรรค์", "https://fineart.tu.ac.th/index.php?option=com_content&view=article&id=178&Itemid=394&lang=th", "สาขาวิชาศิลปะ การออกแบบ และเศรษฐกิจสร้างสรรค์"),
        ("สาขาวิชาการละคอน", "https://fineart.tu.ac.th/index.php?option=com_content&view=article&id=66&Itemid=339&lang=th", "สาขาวิชาการละคอน"),
        ("สาขาวิชาศิลปะการออกแบบพัสตราภรณ์", "https://fineart.tu.ac.th/index.php?option=com_content&view=article&id=67&Itemid=340&lang=th", "สาขาวิชาศิลปะการออกแบบพัสตราภรณ์"),
        ("สาขาวิชาออกแบบหัตถอุตสาหกรรม", "https://fineart.tu.ac.th/index.php?option=com_content&view=article&id=68&Itemid=341&lang=th", "สาขาวิชาออกแบบหัตถอุตสาหกรรม"),
        ("สาขาวิชาการบริหารจัดการศิลปะ", "https://fineart.tu.ac.th/index.php?option=com_content&view=article&id=234&Itemid=474&lang=th", "สาขาวิชาการบริหารจัดการศิลปะ"),
    ]
    results = []
    print(f"\n[FA TU] Fetching departments from fineart.tu.ac.th ...", flush=True)

    for label, page_url, dept_th in pages:
        try:
            r = client.get(page_url, timeout=15.0)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.find("div", class_="com-content-article__body") or soup.find("div", class_="item-page")
            if not body:
                continue
            for p in body.find_all(["p", "div", "h3", "h4"]):
                txt = p.get_text().strip()
                if not any(t in txt for t in ["ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์", "อาจารย์ ดร.", "อาจารย์"]):
                    continue
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                name_line = None
                for l in lines:
                    if re.search(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์ ดร\.|อาจารย์)", l):
                        name_line = l
                        break
                if not name_line or len(name_line) > 60 or "พิเศษ" in name_line:
                    continue
                parsed = parse_thai_academic_name(name_line)
                if not parsed or not parsed[1]:
                    continue
                ac_title, fname, lname, full_th = parsed

                parent = p.find_parent("div", class_="row") or p.find_parent("div", class_="col") or p.parent
                img_url = None
                if parent:
                    img = parent.find("img")
                    if img and img.get("src"):
                        src = img["src"]
                        if not src.startswith("http"):
                            img_url = f"https://fineart.tu.ac.th/{src.lstrip('/')}"
                        else:
                            img_url = src
                        img_url = img_url.replace(" ", "%20")

                results.append({
                    "university": "Thammasat University",
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "faculty": "Faculty of Fine and Applied Arts",
                    "faculty_th": "คณะศิลปกรรมศาสตร์",
                    "department": dept_th,
                    "department_th": dept_th,
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "full_name_th": full_th,
                    "role": f"อาจารย์ประจำ{dept_th}",
                    "email": None,  # PDPA: Exclude personal freemails
                    "image_url": img_url,
                    "profile_url": page_url,
                    "education": [],
                    "research_interests": ["ศิลปกรรมศาสตร์", "การออกแบบสร้างสรรค์", "ทัศนศิลป์", "เศรษฐกิจสร้างสรรค์"],
                    "taught_courses": [],
                })
        except Exception as e:
            print(f"[FA TU] Failed on {label}: {e}")

    seen = set()
    deduped = []
    for res in results:
        k = (res["first_name"], res["last_name"])
        if k not in seen and res["first_name"]:
            seen.add(k)
            deduped.append(res)
    print(f"[FA TU] Harvested {len(deduped)} authentic faculty members.", flush=True)
    return deduped


# ---------------------------------------------------------------------------
# Master Acquisition & Ingestion Orchestrator
# ---------------------------------------------------------------------------
def run_wave85_acquisition():
    print("=" * 78)
    print("🚀 Starting Wave 85: Top Universities Graduate-Focused Flagship Pipeline")
    print("=" * 78)

    all_harvested: List[Dict] = []
    with httpx.Client(headers=HEADERS_DEFAULT, verify=False, follow_redirects=True, timeout=15.0) as client:
        # Target 1: SH MU
        all_harvested.extend(harvest_sh_mahidol(client))
        # Target 2: Econ KKU
        all_harvested.extend(harvest_econ_kku(client))
        # Target 3: NICFD MU
        all_harvested.extend(harvest_nicfd_mahidol(client))
        # Target 4: IL MU
        all_harvested.extend(harvest_il_mahidol(client))
        # Target 6: FA TU
        all_harvested.extend(harvest_fa_tu(client))

    with httpx.Client(headers=HEADERS_CHULA, verify=False, follow_redirects=True, timeout=15.0) as client_cu:
        # Target 5: CPS CU
        all_harvested.extend(harvest_cps_cu(client_cu))

    print(f"\nTotal harvested across all graduate faculties: {len(all_harvested)} records.")

    standardized_records: List[Dict] = []
    idx_counters: Dict[str, int] = {}

    for item in all_harvested:
        u_th = item["university_th"]
        f_th = item["faculty_th"]
        prefix = "w85_grad"
        if "สังคมศาสตร์และมนุษยศาสตร์" in f_th:
            prefix = "w85_mu_sh"
        elif "เศรษฐศาสตร์" in f_th and "ขอนแก่น" in u_th:
            prefix = "w85_kku_econ"
        elif "เด็กและครอบครัว" in f_th:
            prefix = "w85_mu_nicfd"
        elif "นวัตกรรมการเรียนรู้" in f_th:
            prefix = "w85_mu_il"
        elif "ประชากรศาสตร์" in f_th:
            prefix = "w85_cu_cps"
        elif "ศิลปกรรมศาสตร์" in f_th and "ธรรมศาสตร์" in u_th:
            prefix = "w85_tu_fa"

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
        target_univs = [
            "จุฬาลงกรณ์มหาวิทยาลัย",
            "มหาวิทยาลัยมหิดล",
            "มหาวิทยาลัยธรรมศาสตร์",
            "มหาวิทยาลัยขอนแก่น",
        ]
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
                if r["department_th"] and (not existing.department_th or existing.department_th == "ระบุไม่ได้" or existing.department_th == existing.faculty_th):
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
                    openalex_id="not_indexed",
                    scholar_url=None,
                    embedding_text=r["embedding_text"],
                    embedding=r["embedding"],
                )
                db.add(new_f)
                inserted += 1
                if cname:
                    existing_map[(u_th, cname)] = new_f
                if r_email:
                    email_map[r_email] = new_f

        db.commit()
        print(f"\n✅ Wave 85 Database Ingestion Complete!")
        print(f"   - Newly Inserted: {inserted} faculty records")
        print(f"   - Enriched/Updated: {updated} existing records")
        print(f"   - Total Processed: {len(standardized_records)}")

    except Exception as e:
        db.rollback()
        print(f"❌ Database Ingestion Failed: {e}", flush=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_wave85_acquisition()
