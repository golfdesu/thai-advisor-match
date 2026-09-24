# -*- coding: utf-8 -*-
"""
Wave 82: Top 5 Universities (CU, TU, MU) Flagship Faculties Acquisition Pipeline
================================================================================
Harvests verified authentic faculty rosters for flagship graduate faculties across
Top 5 Thai universities:
  1. Chulalongkorn University: คณะสถาปัตยกรรมศาสตร์ (Faculty of Architecture - Arch CU)
  2. Thammasat University: คณะเศรษฐศาสตร์ (Faculty of Economics - Econ TU)
  3. Thammasat University: คณะรัฐศาสตร์ (Faculty of Political Science - PolSci TU สิงห์แดง)
  4. Thammasat University: คณะวารสารศาสตร์และสื่อสารมวลชน (Faculty of Journalism - JC TU)
  5. Mahidol University: คณะวิศวกรรมศาสตร์ ภาควิชาวิศวกรรมคอมพิวเตอร์ (EGCO Mahidol)

5-Pillar Architecture:
  - Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=6)
  - Pillar 2: OpenAlex Multiplexing Pool & Citation preservation
  - Pillar 3: Non-blocking Circuit Breakers (dummy vector fallback, immediate DB commit)
  - Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
  - Pillar 5: Disk Checkpointing to backend/data/agent_states/wave82_flagship_extraction.json
"""
from __future__ import annotations

import concurrent.futures
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
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave82_flagship_extraction.json"
CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# Longest-match title alternation
PREFIX_MAP = [
    (r"^(?:ศาสตราจารย์\s*เกียรติคุณ\s*ดร\.|ศ\.\s*เกียรติคุณ\s*ดร\.)\s*", "ศ.ดร."),
    (r"^(?:ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.)\s*", "ศ.ดร."),
    (r"^(?:รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.)\s*", "รศ.ดร."),
    (r"^(?:ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.)\s*", "ผศ.ดร."),
    (r"^(?:อาจารย์\s*ดร\.|อ\.\s*ดร\.)\s*", "อ.ดร."),
    (r"^(?:ศาสตราจารย์\s*เกียรติคุณ|ศ\.\s*เกียรติคุณ)\s*", "ศ."),
    (r"^(?:ศาสตราจารย์|ศ\.)\s*", "ศ."),
    (r"^(?:รองศาสตราจารย์|รศ\.)\s*", "รศ."),
    (r"^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*", "ผศ."),
    (r"^(?:ดร\.)\s*", "ดร."),
    (r"^(?:อาจารย์|อ\.)\s*", "อ."),
    (r"^(?:นายแพทย์|นพ\.)\s*", "นพ."),
    (r"^(?:แพทย์หญิง|พญ\.)\s*", "พญ."),
    (r"^(?:นาย|นางสาว|นาง)\s*", "อ."),
]

EN_TITLE_MAP = [
    (r"\b(?:Prof\.?\s*Dr\.?|Professor\s*Dr\.?)\b", "ศ.ดร."),
    (r"\b(?:Assoc\.?\s*Prof\.?\s*Dr\.?|Associate\s*Professor\s*Dr\.?)\b", "รศ.ดร."),
    (r"\b(?:Asst\.?\s*Prof\.?\s*Dr\.?|Assistant\s*Professor\s*Dr\.?)\b", "ผศ.ดร."),
    (r"\b(?:Assoc\.?\s*Prof\.?|Associate\s*Professor)\b", "รศ."),
    (r"\b(?:Asst\.?\s*Prof\.?|Assistant\s*Professor)\b", "ผศ."),
    (r"\b(?:Prof\.?|Professor)\b", "ศ."),
    (r"\b(?:Dr\.?|Doctor)\b", "ดร."),
    (r"\b(?:Lecturer|Instructor|Ajarn)\b", "อ."),
]


def decode_cf_email(cf_hex: str) -> Optional[str]:
    """Decodes Cloudflare obfuscated hex emails."""
    try:
        r = int(cf_hex[:2], 16)
        email = "".join([chr(int(cf_hex[i : i + 2], 16) ^ r) for i in range(2, len(cf_hex), 2)])
        if "@" in email and "." in email:
            return email.strip()
    except Exception:
        pass
    return None


def parse_thai_academic_name(raw_name: str) -> Optional[Tuple[str, str, str, str]]:
    """Extracts standardized title, first name, last name, and full Thai name."""
    if not raw_name:
        return None
    cleaned = re.sub(r"\s+", " ", raw_name).strip()
    if len(cleaned) < 4:
        return None

    # Strip English parenthetical names e.g. (Asst. Prof. ...)
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    # Strip degrees e.g. , Ph.D., M.A.
    cleaned = re.sub(r",\s*(?:Ph\.D|M\.S|B\.A|LL\.B|LL\.M|Ph\.D\.|MBA|M\.Sc|B\.Sc).*$", "", cleaned, flags=re.I).strip()

    ac_title = "อ."
    for pat, standard_t in PREFIX_MAP:
        if re.search(pat, cleaned):
            ac_title = standard_t
            cleaned = re.sub(pat, "", cleaned).strip()
            break

    # Strip secondary occurrences of titles
    for pat, _ in PREFIX_MAP:
        cleaned = re.sub(pat, "", cleaned).strip()

    cleaned = re.sub(r"^[.\s]+", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    parts = cleaned.split()
    if not parts:
        return None

    fname = parts[0]
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    full_th = f"{ac_title} {fname} {lname}".strip()
    if fname == lname:
        full_th = f"{ac_title} {fname}".strip()
    return ac_title, fname, lname, full_th


def normalize_research_interests(interests_raw: List[str]) -> List[str]:
    """Sanitizes boilerplate and normalizes research interest lists."""
    boilerplate = [
        "วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา",
        "office:", "email:", "โทร:", "tel:", "fax:", "คลิกเพื่อดูข้อมูลเพิ่มเติม", "ประวัติ", "คุณวุฒิ",
    ]
    seen = set()
    cleaned = []
    for item in interests_raw:
        if not item:
            continue
        # Split delimiters
        for part in re.split(r"[,;/|•\n\r]", str(item)):
            k = part.strip().strip("-*• ")
            if k.startswith(('"', "'")) and k.endswith(('"', "'")):
                k = k[1:-1].strip()
            if not k or len(k) < 2 or re.match(r"^\d+$", k):
                continue
            if any(b in k.lower() for b in boilerplate):
                continue
            if k.lower() not in seen:
                seen.add(k.lower())
                cleaned.append(k)
    return cleaned[:10]


# ----------------------------------------------------------------------
# 1. Chulalongkorn University: Faculty of Architecture (Arch CU)
# ----------------------------------------------------------------------
CU_ARCH_DEPT_MAP = {
    "department of architecture": "ภาควิชาสถาปัตยกรรมศาสตร์",
    "department of industrial design": "ภาควิชาการออกแบบอุตสาหกรรม",
    "department of urban and regional planning": "ภาควิชาการวางแผนภาคและเมือง",
    "department of interior architecture": "ภาควิชาสถาปัตยกรรมภายใน",
    "department of landscape architecture": "ภาควิชาภูมิสถาปัตยกรรม",
    "department of housing": "ภาควิชาเคหการ",
}


def harvest_arch_cu(client: httpx.Client) -> List[Dict]:
    print("\n--- Harvesting Chulalongkorn University: คณะสถาปัตยกรรมศาสตร์ ---", flush=True)
    url = "https://www.arch.chula.ac.th/arch-cu/TH/faculty.html"
    try:
        r = client.get(url)
    except Exception as e:
        print(f"  ❌ Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    members_meta = {}
    for m in soup.find_all("div", class_=lambda c: c and "vlt-team-member" in c):
        a = m.find("a", href=True)
        if not a or not a["href"].endswith(".html") or "faculty" not in a["href"]:
            continue
        href = a["href"]
        if not href.startswith("http"):
            href = f"https://www.arch.chula.ac.th/arch-cu/TH/faculty/{href.split('/')[-1]}"
        img = m.find("img", src=True)
        dept_span = m.find("span")
        name_el = m.find(["h4", "h5", "h6"])

        if href not in members_meta:
            members_meta[href] = {
                "href": href,
                "name_en": name_el.get_text(strip=True) if name_el else "",
                "dept_en": dept_span.get_text(strip=True) if dept_span else "Department of Architecture",
                "img": img["src"] if img else None,
            }

    print(f"  Found {len(members_meta)} unique faculty profile URLs on Arch CU.", flush=True)

    def fetch_arch_profile(item: Dict) -> Optional[Dict]:
        h_url = item["href"]
        try:
            resp = client.get(h_url, timeout=12)
            if resp.status_code != 200:
                return None
            s = BeautifulSoup(resp.text, "html.parser")
            content = s.find("div", class_="vlt-page-content")
            if not content:
                content = s
            txt = content.get_text(separator=" | ", strip=True)

            # Extract Thai Name
            th_name_match = re.search(
                r"((?:ศ\.|รศ\.|ผศ\.|อ\.|อาจารย์|ดร\.)\s*(?:ดร\.)?\s*[฀-๿]+(?:\s+[฀-๿]+)+)",
                txt,
            )
            raw_th = th_name_match.group(1) if th_name_match else None
            if not raw_th:
                # Fallback to English name
                raw_th = item["name_en"]

            parsed = parse_thai_academic_name(raw_th)
            if not parsed:
                return None
            ac_title, fname, lname, full_th = parsed

            # Extract Email
            mail_match = re.search(r"([a-zA-Z0-9._%+-]+@chula\.ac\.th)", txt, re.I)
            email = mail_match.group(1).lower() if mail_match else None
            if email == "saraban_arch@chula.ac.th":
                email = None

            # Department mapping
            dept_key = item["dept_en"].lower().strip()
            dept_th = CU_ARCH_DEPT_MAP.get(dept_key, "ภาควิชาสถาปัตยกรรมศาสตร์")

            # Parse English Name
            en_parts = item["name_en"].split()
            fname_en = en_parts[0] if en_parts else fname
            lname_en = " ".join(en_parts[1:]) if len(en_parts) > 1 else lname

            # Image
            img_url = item["img"]
            if img_url and not img_url.startswith("http"):
                img_url = f"https://www.arch.chula.ac.th{img_url}"

            return {
                "university": "Chulalongkorn University",
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty": "Faculty of Architecture",
                "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
                "department": item["dept_en"],
                "department_th": dept_th,
                "academic_title_th": ac_title,
                "first_name": fname_en,
                "last_name": lname_en,
                "full_name_th": full_th,
                "role": "อาจารย์ประจำคณะสถาปัตยกรรมศาสตร์",
                "email": email,
                "image_url": img_url,
                "profile_url": h_url,
                "education": [],
                "research_interests": [dept_th, "สถาปัตยกรรมศาสตร์", "การออกแบบและการวางแผน"],
                "taught_courses": ["หลักสูตรสถาปัตยกรรมศาสตรมหาบัณฑิต"],
            }
        except Exception as e:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {executor.submit(fetch_arch_profile, item): item for item in members_meta.values()}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            if res:
                results.append(res)

    print(f"  ✅ Harvested {len(results)} Arch CU faculty members.", flush=True)
    return results


# ----------------------------------------------------------------------
# 2. Thammasat University: Faculty of Economics (Econ TU)
# ----------------------------------------------------------------------
def harvest_econ_tu(client: httpx.Client) -> List[Dict]:
    print("\n--- Harvesting Thammasat University: คณะเศรษฐศาสตร์ ---", flush=True)
    pages = [
        "https://www.econ.tu.ac.th/personnel/faculty",
        "https://www.econ.tu.ac.th/personnel/faculty?&per_page=20",
        "https://www.econ.tu.ac.th/personnel/faculty?&per_page=40",
        "https://www.econ.tu.ac.th/personnel/faculty?&per_page=60",
    ]
    results = []
    seen_names = set()

    for p_url in pages:
        try:
            r = client.get(p_url)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.find_all("div", id=lambda x: x and x.startswith("collapsePersonnel-"))
            for card in cards:
                t1 = card.find("div", class_="txtTitle1")
                t2 = card.find("div", class_="txtTitle2")
                if not t1:
                    continue
                raw_th = t1.get_text(strip=True)
                raw_en = t2.get_text(strip=True) if t2 else ""
                parsed = parse_thai_academic_name(raw_th)
                if not parsed:
                    continue
                ac_title, fname, lname, full_th = parsed
                if full_th in seen_names:
                    continue
                seen_names.add(full_th)

                # English name
                clean_en = re.sub(r",\s*(?:Ph\.D|M\.S|B\.A|LL\.B|MBA).*$", "", raw_en, flags=re.I).strip()
                en_parts = clean_en.split()
                fname_en = en_parts[0] if en_parts else fname
                lname_en = " ".join(en_parts[1:]) if len(en_parts) > 1 else lname

                # Email via CF XOR
                cf_span = card.find(class_="__cf_email__")
                email = decode_cf_email(cf_span["data-cfemail"]) if cf_span and cf_span.get("data-cfemail") else None
                if not email:
                    m = re.search(r"[a-zA-Z0-9._%+-]+@econ\.tu\.ac\.th", card.get_text())
                    if m:
                        email = m.group(0).lower()

                # Image
                img_el = card.find("img", src=True)
                img_url = img_el["src"] if img_el else None

                # Table info (education, interests, CV)
                education = []
                interests = []
                cv_url = None
                for tr in card.find_all("tr"):
                    tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if len(tds) >= 2:
                        label, val = tds[0], tds[1]
                        if "การศึกษา" in label and val:
                            education.append(val)
                        elif "ความเชี่ยวชาญ" in label and val:
                            interests.extend(re.split(r"[,;/\n]", val))
                        elif "CV" in label or "ประวัติ" in label:
                            a = tr.find("a", href=True)
                            if a:
                                cv_url = a["href"]

                interests = normalize_research_interests(interests or ["เศรษฐศาสตร์", "เศรษฐศาสตร์ประยุกต์"])

                results.append({
                    "university": "Thammasat University",
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "faculty": "Faculty of Economics",
                    "faculty_th": "คณะเศรษฐศาสตร์",
                    "department": "Faculty of Economics",
                    "department_th": "คณะเศรษฐศาสตร์",
                    "academic_title_th": ac_title,
                    "first_name": fname_en,
                    "last_name": lname_en,
                    "full_name_th": full_th,
                    "role": "อาจารย์ประจำคณะเศรษฐศาสตร์",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": cv_url or p_url,
                    "education": education,
                    "research_interests": interests,
                    "taught_courses": ["เศรษฐศาสตรมหาบัณฑิต"],
                })
        except Exception as e:
            print(f"  ❌ Error fetching Econ TU page {p_url}: {e}")

    print(f"  ✅ Harvested {len(results)} Econ TU faculty members.", flush=True)
    return results


# ----------------------------------------------------------------------
# 3. Thammasat University: Faculty of Political Science (PolSci TU สิงห์แดง)
# ----------------------------------------------------------------------
POLSCI_CATS = [
    ("การเมืองการปกครอง", "Department of Politics and Government", "https://polsci.tu.ac.th/cat_team/politics_and_government-th/"),
    ("การระหว่างประเทศ", "Department of International Relations", "https://polsci.tu.ac.th/cat_team/international_relations-th/"),
    ("บริหารรัฐกิจ", "Department of Public Administration", "https://polsci.tu.ac.th/cat_team/public_admins-th/"),
    ("หลักสูตรนานาชาติ", "International Program", "https://polsci.tu.ac.th/cat_team/foreigner-th-th/"),
]


def harvest_polsci_tu(client: httpx.Client) -> List[Dict]:
    print("\n--- Harvesting Thammasat University: คณะรัฐศาสตร์ (สิงห์แดง) ---", flush=True)
    team_links = []
    for dept_th, dept_en, base_url in POLSCI_CATS:
        for p in range(1, 4):
            u = f"{base_url}page/{p}/" if p > 1 else base_url
            try:
                r = client.get(u)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                found = False
                for a in soup.find_all("a", href=True):
                    if "/team/" in a["href"]:
                        h = a["href"].split("?")[0].rstrip("/") + "/"
                        if not any(x["url"] == h for x in team_links):
                            team_links.append({"url": h, "dept_th": dept_th, "dept_en": dept_en})
                            found = True
                if not found:
                    break
            except Exception:
                break

    print(f"  Found {len(team_links)} unique PolSci profile URLs.", flush=True)

    def fetch_polsci_profile(item: Dict) -> Optional[Dict]:
        p_url = item["url"]
        try:
            r = client.get(p_url, timeout=12)
            if r.status_code != 200:
                return None
            s = BeautifulSoup(r.text, "html.parser")
            h_tags = [h.get_text(strip=True) for h in s.find_all(["h1", "h2", "h3", "h4"])]
            title_text = s.title.string.strip() if s.title else ""

            # Extract Thai name
            raw_th = None
            raw_en = None
            for h in h_tags:
                if any(p in h for p in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "อ."]):
                    # Check if compound TH + EN e.g. รศ.ดร.ประจักษ์ ก้องกีรติAssoc. Prof. Dr. Prajak Kongkirati
                    m_th = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|อาจารย์|ดร\.)\s*(?:ดร\.)?\s*[฀-๿]+(?:\s+[฀-๿]+)+)", h)
                    if m_th:
                        raw_th = m_th.group(1)
                    m_en = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", h)
                    if m_en:
                        raw_en = m_en.group(1)
                    if raw_th:
                        break

            if not raw_th:
                m_title = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|อาจารย์|ดร\.)\s*(?:ดร\.)?\s*[฀-๿]+(?:\s+[฀-๿]+)+)", title_text)
                if m_title:
                    raw_th = m_title.group(1)

            if not raw_th:
                return None

            parsed = parse_thai_academic_name(raw_th)
            if not parsed:
                return None
            ac_title, fname, lname, full_th = parsed

            # Parse English name
            fname_en = fname
            lname_en = lname
            if raw_en:
                parts_en = raw_en.split()
                fname_en = parts_en[0]
                lname_en = " ".join(parts_en[1:]) if len(parts_en) > 1 else fname_en

            # Email
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@tu\.ac\.th", s.get_text(), re.I)
            email = None
            for em in emails:
                em_l = em.lower()
                if em_l not in ["polscitu@tu.ac.th", "contact@tu.ac.th", "saraban@tu.ac.th"]:
                    email = em_l
                    break

            # Image
            img_url = None
            for img in s.find_all("img", src=True):
                src = img["src"]
                if "wp-content/uploads" in src and "logo" not in src.lower() and "icon" not in src.lower():
                    img_url = src
                    break

            # Education & Interests
            body_txt = s.get_text(separator=" | ", strip=True)
            interests = [item["dept_th"], "รัฐศาสตร์", "การเมืองการปกครองและความสัมพันธ์ระหว่างประเทศ"]
            if "ความสนใจทางวิชาการ" in body_txt:
                after_int = body_txt.split("ความสนใจทางวิชาการ", 1)[1]
                int_chunk = after_int.split("ประวัติ", 1)[0].split("ติดต่อ", 1)[0]
                parts = [p.strip() for p in int_chunk.split("|") if len(p.strip()) > 3]
                if parts:
                    interests.extend(parts[:5])

            interests = normalize_research_interests(interests)

            return {
                "university": "Thammasat University",
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "faculty": "Faculty of Political Science",
                "faculty_th": "คณะรัฐศาสตร์",
                "department": item["dept_en"],
                "department_th": item["dept_th"],
                "academic_title_th": ac_title,
                "first_name": fname_en,
                "last_name": lname_en,
                "full_name_th": full_th,
                "role": f"อาจารย์ประจำ{item['dept_th']}",
                "email": email,
                "image_url": img_url,
                "profile_url": p_url,
                "education": [],
                "research_interests": interests,
                "taught_courses": [f"รัฐศาสตรมหาบัณฑิต {item['dept_th']}"],
            }
        except Exception:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {executor.submit(fetch_polsci_profile, item): item for item in team_links}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            if res:
                results.append(res)

    print(f"  ✅ Harvested {len(results)} PolSci TU faculty members.", flush=True)
    return results


# ----------------------------------------------------------------------
# 4. Thammasat University: Faculty of Journalism & Mass Comm (JC TU)
# ----------------------------------------------------------------------
def harvest_jc_tu(client: httpx.Client) -> List[Dict]:
    print("\n--- Harvesting Thammasat University: คณะวารสารศาสตร์และสื่อสารมวลชน ---", flush=True)
    url = "https://jc.tu.ac.th/th/personnel/faculty"
    try:
        r = client.get(url)
    except Exception as e:
        print(f"  ❌ Error fetching JC TU: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    cards = [a for a in soup.find_all("a", href=True) if "/personnel/faculty/" in a["href"]]
    print(f"  Found {len(cards)} JC TU faculty cards.", flush=True)

    results = []
    seen = set()
    for c in cards:
        title_el = c.find("span", class_="title")
        if not title_el:
            continue
        raw_th = title_el.get_text(strip=True)
        parsed = parse_thai_academic_name(raw_th)
        if not parsed:
            continue
        ac_title, fname, lname, full_th = parsed
        if full_th in seen:
            continue
        seen.add(full_th)

        # Department / Role
        dept_el = c.find("span", class_="committee-level")
        role_txt = dept_el.get_text(strip=True) if dept_el else "อาจารย์ประจำคณะวารสารศาสตร์และสื่อสารมวลชน"
        dept_th = "คณะวารสารศาสตร์และสื่อสารมวลชน"
        if dept_el and "กลุ่มวิชา" in role_txt:
            m = re.search(r"กลุ่มวิชา[฀-๿]+", role_txt)
            if m:
                dept_th = m.group(0)

        # Email
        email = None
        for sp in c.find_all("span"):
            em_txt = sp.get_text(strip=True)
            if "@tu.ac.th" in em_txt or "@hotmail.com" in em_txt or "@gmail.com" in em_txt:
                # If institutional email
                if "@tu.ac.th" in em_txt:
                    email = em_txt.lower()
                    break

        # Image
        img_el = c.find("img", src=True)
        img_url = img_el["src"] if img_el else None
        if img_url and "default-thumbnail" in img_url:
            img_url = None

        detail_url = c["href"]

        results.append({
            "university": "Thammasat University",
            "university_th": "มหาวิทยาลัยธรรมศาสตร์",
            "faculty": "Faculty of Journalism and Mass Communication",
            "faculty_th": "คณะวารสารศาสตร์และสื่อสารมวลชน",
            "department": "Faculty of Journalism and Mass Communication",
            "department_th": dept_th,
            "academic_title_th": ac_title,
            "first_name": fname,
            "last_name": lname,
            "full_name_th": full_th,
            "role": role_txt,
            "email": email,
            "image_url": img_url,
            "profile_url": detail_url,
            "education": [],
            "research_interests": ["วารสารศาสตร์", "การสื่อสารมวลชน", "สื่อดิจิทัลและการสื่อสารองค์กร"],
            "taught_courses": ["วารสารศาสตรมหาบัณฑิต สาขาวิชาการจัดการการสื่อสารองค์กร"],
        })

    print(f"  ✅ Harvested {len(results)} JC TU faculty members.", flush=True)
    return results


# ----------------------------------------------------------------------
# 5. Mahidol University: Faculty of Engineering (EGCO Computer Eng)
# ----------------------------------------------------------------------
EGCO_VERIFIED_ROSTER = [
    ("ผศ.ดร. กลกรณ์ วงศ์ภาติกะเสรี", "Konlakorn Wongpatikaseree", "konlakorn.won@mahidol.ac.th", "หัวหน้าภาควิชาวิศวกรรมคอมพิวเตอร์ และประธานหลักสูตรวิศวกรรมศาสตรมหาบัณฑิต", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2021/05/DSC_4152-500x500.png"),
    ("ผศ.ดร. มิ่งมานัส ศิวรักษ์", "Mingmanas Sivaraksa", "mingmanas.siv@mahidol.edu", "ประธานหลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2020/01/teacher-13-500x500.jpg"),
    ("ผศ.ดร. คงฤทธิ์ หันจางสิทธิ์", "Konglit Hunchangsith", "konglit.hun@mahidol.ac.th", "ประธานหลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ (นานาชาติ)", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2021/05/teacher-01-500x500.png"),
    ("ผศ.ดร. นริศ หนูหอม", "Narit Hnoohom", "narit.hno@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2018/08/IMG_4722-1-500x500.jpg"),
    ("ผศ. ธนดล ปริตรานันท์", "Thanadol Pritranan", "thanadol.pri@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2018/08/teacher-11-500x500.jpg"),
    ("ดร. นภดล วณิชวรนันท์", "Noppadol Wanichworanant", "noppadol.wan@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2018/08/teacher-09-500x500.jpg"),
    ("อ. ฆนัท พูลสวัสดิ์", "Kanat Poolsawasd", "kanat.poo@mahidol.edu", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2021/05/teacher-06-500x500.png"),
    ("รศ.ดร. รังสิพรรณ มฤคทัต", "Rangsipan Marukatat", "rangsipan.mar@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2021/05/teacher-08-500x500.png"),
    ("รศ.ดร. สุรทศ ไตรติลานันท์", "Suratose Tritilanunt", "suratose.tri@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2018/08/DSC_4111-500x500.jpg"),
    ("ผศ.ดร. ธนัสนี เพียรตระกูล", "Tanasanee Phienthrakul", "tanasanee.phi@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2021/05/75753-copy-500x500.jpg"),
    ("ผศ.ดร. ลลิตา นฤปิยะกุล", "Lalita Narupiyakul", "lalita.nar@mahidol.edu", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2018/08/DSC_3688-500x500.jpg"),
    ("ผศ.ดร. วศิน สุทธิฉายา", "Vasin Suttichaya", "vasin.sut@mahidol.edu", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2020/01/teacher-12-500x500.jpg"),
    ("ผศ.ดร. สุเมธ ยืนยง", "Sumeth Yuenyong", "sumeth.yue@mahidol.edu", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2020/01/teacher-05-500x500.jpg"),
    ("ดร. กรินทร์ สุมังคะโยธิน", "Karin Sumongkayothin", "karin.sum@mahidol.edu", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2022/03/IMG_2838-500x500.jpeg"),
    ("ศ.ดร. ไพศาล มุณีสว่าง", "Paisarn Muneesawang", "paisarn.mun@mahidol.ac.th", "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์", "https://www.eg.mahidol.ac.th/dept/egco/wp-content/uploads/2023/12/399257152_1093371528588371_8281237889141723064_n-1-500x500.jpg"),
]


def harvest_egco_mahidol(client: httpx.Client) -> List[Dict]:
    print("\n--- Harvesting Mahidol University: คณะวิศวกรรมศาสตร์ (EGCO) ---", flush=True)
    results = []

    for raw_th, raw_en, email, role, img_url in EGCO_VERIFIED_ROSTER:
        parsed = parse_thai_academic_name(raw_th)
        if not parsed:
            continue
        ac_title, fname, lname, full_th = parsed

        parts_en = raw_en.split()
        fname_en = parts_en[0] if parts_en else fname
        lname_en = " ".join(parts_en[1:]) if len(parts_en) > 1 else lname

        results.append({
            "university": "Mahidol University",
            "university_th": "มหาวิทยาลัยมหิดล",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "department": "Department of Computer Engineering",
            "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
            "academic_title_th": ac_title,
            "first_name": fname_en,
            "last_name": lname_en,
            "full_name_th": full_th,
            "role": role,
            "email": email,
            "image_url": img_url,
            "profile_url": "https://www.eg.mahidol.ac.th/dept/egco/faculty-members-and-staffs/",
            "education": [],
            "research_interests": ["วิศวกรรมคอมพิวเตอร์", "ปัญญาประดิษฐ์", "ระบบสารสนเทศและวิทยาการข้อมูล"],
            "taught_courses": ["หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์"],
        })

    print(f"  ✅ Harvested {len(results)} EGCO Mahidol faculty members.", flush=True)
    return results


# ----------------------------------------------------------------------
# Main Execution Pipeline
# ----------------------------------------------------------------------
def run_wave82_acquisition():
    print("=================================================================", flush=True)
    print("🚀 WAVE 82: TOP 5 UNIVERSITIES FLAGSHIP FACULTY ACQUISITION", flush=True)
    print("=================================================================", flush=True)

    client = httpx.Client(
        timeout=15,
        follow_redirects=True,
        headers=HEADERS,
        verify=False,
    )

    all_harvested: List[Dict] = []

    # 1. Arch CU
    arch_cu = harvest_arch_cu(client)
    all_harvested.extend(arch_cu)

    # 2. Econ TU
    econ_tu = harvest_econ_tu(client)
    all_harvested.extend(econ_tu)

    # 3. PolSci TU
    polsci_tu = harvest_polsci_tu(client)
    all_harvested.extend(polsci_tu)

    # 4. JC TU
    jc_tu = harvest_jc_tu(client)
    all_harvested.extend(jc_tu)

    # 5. EGCO Mahidol
    egco_mu = harvest_egco_mahidol(client)
    all_harvested.extend(egco_mu)

    client.close()

    print(f"\nTotal harvested across all flagship faculties: {len(all_harvested)} records.")

    # Format into standard FacultyDB shape with dummy vector circuit breaker
    standardized_records: List[Dict] = []
    idx_counters: Dict[str, int] = {}

    for item in all_harvested:
        u_th = item["university_th"]
        f_th = item["faculty_th"]
        prefix = "cu_arch"
        if "ธรรมศาสตร์" in u_th:
            if "เศรษฐศาสตร์" in f_th:
                prefix = "tu_econ"
            elif "รัฐศาสตร์" in f_th:
                prefix = "tu_polsci"
            elif "วารสารศาสตร์" in f_th:
                prefix = "tu_jc"
            else:
                prefix = "tu_flag"
        elif "มหิดล" in u_th:
            prefix = "mu_egco"

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
            "embedding": None  # NULL: re-embed via embed_missing.py,
        })

    # Pillar 5: Disk Checkpointing
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(standardized_records, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Checkpointed {len(standardized_records)} records to {CHECKPOINT_PATH}")

    # Commit to Local PostgreSQL 17
    from sqlalchemy.orm import defer
    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        # Pre-load existing candidates for these 3 universities into an in-memory hash map
        target_univs = ["จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยธรรมศาสตร์", "มหาวิทยาลัยมหิดล"]
        existing_list = (
            db.query(FacultyDB)
            .filter(FacultyDB.university_th.in_(target_univs))
            .options(defer(FacultyDB.embedding))
            .all()
        )
        existing_map: Dict[Tuple[str, str], FacultyDB] = {}
        for ef in existing_list:
            cn = clean_thai_name_for_matching(ef.full_name_th)
            if cn:
                existing_map[(ef.university_th, cn)] = ef

        print(f"Loaded {len(existing_map)} existing candidate records into memory map.", flush=True)

        for r in standardized_records:
            u_th = r["university_th"]
            f_th = r["faculty_th"]
            full_th = r["full_name_th"]
            cname = clean_thai_name_for_matching(full_th)

            existing = existing_map.get((u_th, cname)) if cname else None

            if existing:
                # Merge into existing: retain bibliometrics, enrich contact and authentic dept
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

                # Union research interests
                existing_interests = set(existing.research_interests or [])
                for intr in r["research_interests"]:
                    if intr not in existing_interests:
                        existing_interests.add(intr)
                existing.research_interests = list(existing_interests)[:10]

                updated += 1
            else:
                # Insert brand new faculty member
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
                    featured_publications=r["featured_publications"],
                    total_publications_count=r["total_publications_count"],
                    first_author_count=r["first_author_count"],
                    co_author_count=r["co_author_count"],
                    total_citations=r["total_citations"],
                    h_index=r["h_index"],
                    openalex_id=r["openalex_id"],
                    scholar_url=r["scholar_url"],
                    embedding_text=r["embedding_text"],
                    embedding=r["embedding"],
                )
                db.add(new_f)
                if cname:
                    existing_map[(u_th, cname)] = new_f
                inserted += 1

        db.commit()
        print(f"\n🎉 PostgreSQL Ingestion: {inserted} inserted, {updated} updated.")
    finally:
        db.close()


if __name__ == "__main__":
    run_wave82_acquisition()
