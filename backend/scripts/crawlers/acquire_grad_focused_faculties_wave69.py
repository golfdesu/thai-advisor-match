# -*- coding: utf-8 -*-
"""
Wave 69 Autonomous Acquisition of Graduate-Level Faculty
========================================================
5-Pillar Architecture Headless Crawler for Graduate Faculties with Deficits:
1. Chulalongkorn University College of Population Studies (วิทยาลัยประชากรศาสตร์ จุฬาฯ - M.A. & Ph.D. Demography)
   - Source: https://cps.chula.ac.th/cps2022/personnel.php
2. Khon Kaen University Faculty of Education (คณะศึกษาศาสตร์ มข. - M.Ed. & Ph.D. Education)
   - Source: https://ednet.kku.ac.th/ (4 departments)
3. Naresuan University Faculty of Nursing (คณะพยาบาลศาสตร์ ม.นเรศวร - Master of Nursing Science)
   - Source: http://www.nurse.nu.ac.th/webdpmnr/persont1.html
4. Chulalongkorn University Sasin School of Management (สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ จุฬาฯ - MBA & Ph.D. Business)
   - Source: https://www.sasin.edu/team/faculty
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave69_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =====================================================================
# 1. Targeted Headless Crawlers (Pillar 1)
# =====================================================================

def crawl_chula_population_studies(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic demographic faculty from Chulalongkorn University College of Population Studies."""
    print("\n[Crawler 1/4] Scraping Chulalongkorn College of Population Studies (วิทยาลัยประชากรศาสตร์ จุฬาฯ)...", flush=True)
    url = "https://cps.chula.ac.th/cps2022/personnel.php"
    results = []

    try:
        r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()

        for div in soup.find_all("div"):
            if not div.find("div") and "@chula.ac.th" in div.get_text():
                parent = div.find_parent("div", class_=lambda c: c and ("card" in c or "col" in c or "team" in c))
                if not parent:
                    parent = div.parent
                txt = parent.get_text(" ", strip=True)

                # Check if academic faculty (excluding administrative support staff)
                if not any(txt.startswith(p) for p in ["ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์", "อาจารย์", "ดร."]):
                    continue

                img = parent.find("img")
                img_src = img["src"] if img and img.get("src") else None
                if img_src and not img_src.startswith("http"):
                    img_src = "https://cps.chula.ac.th/cps2022/" + img_src.lstrip("/ ")

                email_m = re.search(r"([a-zA-Z0-9._%+-]+@chula\.ac\.th)", txt, re.IGNORECASE)
                email = email_m.group(1).strip() if email_m else None

                # Extract Thai Name
                m_th = re.match(r"^((?:ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์|อาจารย์|ดร\.)(?:\s*ดร\.)?\s*([ก-๙\s]+?))\s+(?:Assistant|Associate|Professor|Dr\.)", txt)
                if m_th:
                    raw_name_th = m_th.group(1).strip()
                else:
                    raw_name_th = txt.split("Assistant")[0].split("Associate")[0].split("Professor")[0].split("Dr.")[0].strip()

                if raw_name_th in seen_names:
                    continue
                seen_names.add(raw_name_th)

                # Extract English Name
                m_en = re.search(r"((?:Assistant|Associate|Professor|Dr\.)\s+[A-Za-z\s.,-]+?)(?:\s*,?\s*Ph\.?D\.?)?\s*[​\s]*[a-zA-Z0-9._%+-]+@chula\.ac\.th", txt)
                name_en = m_en.group(1).strip() if m_en else None

                results.append({
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "university_en": "Chulalongkorn University",
                    "faculty_th": "วิทยาลัยประชากรศาสตร์",
                    "faculty_en": "College of Population Studies",
                    "department_th": "สาขาวิชาประชากรศาสตร์",
                    "raw_name_th": raw_name_th,
                    "raw_name_en": name_en,
                    "email": email,
                    "image_url": urllib.parse.quote(img_src, safe=":/%?=") if img_src else None,
                    "profile_url": url,
                    "research_interests": ["Demography", "Population Studies", "Aging Society", "Social Demography"],
                })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from CU College of Population Studies.")
    return results


def crawl_kku_education(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic education faculty from Khon Kaen University Faculty of Education across 4 departments."""
    print("\n[Crawler 2/4] Scraping Khon Kaen University Faculty of Education (คณะศึกษาศาสตร์ มข.)...", flush=True)
    dept_urls = [
        ("สาขาวิชาการศึกษาคณิตศาสตร์ วิทยาศาสตร์ และคอมพิวเตอร์", "Department of Mathematics, Science and Computer Education", "https://ednet.kku.ac.th/mathscicom/"),
        ("สาขาวิชาการศึกษาภาษา", "Department of Language Education", "https://ednet.kku.ac.th/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3%e0%b8%a8%e0%b8%b6%e0%b8%81%e0%b8%a9%e0%b8%b2%e0%b8%a0%e0%b8%b2%e0%b8%a9%e0%b8%b2/"),
        ("สาขาวิชาการศึกษาด้านการพัฒนาวิชาชีพ", "Department of Professional Development Education", "https://ednet.kku.ac.th/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3%e0%b8%a8%e0%b8%b6%e0%b8%81%e0%b8%a9%e0%b8%b2%e0%b8%94%e0%b9%89%e0%b8%b2%e0%b8%99%e0%b8%81%e0%b8%b2/"),
        ("สาขาวิชาการศึกษาสังคมศึกษา ศิลปศึกษา พลศึกษา", "Department of Social Studies, Art, and Physical Education", "https://ednet.kku.ac.th/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3%e0%b8%a8%e0%b8%b6%e0%b8%81%e0%b8%a9%e0%b8%b2%e0%b8%aa%e0%b8%b1%e0%b8%87%e0%b8%84%e0%b8%a1%e0%b8%a8/"),
    ]

    results = []
    seen_names = set()

    for dept_th, dept_en, url in dept_urls:
        try:
            r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
            if r.status_code != 200:
                print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "uploads" in src and not any(k in src.lower() for k in ["logo", "svg"]):
                    card = img.find_parent("div", class_="elementor-widget-wrap")
                    if card:
                        txt = card.get_text(" ", strip=True)
                        if not any(p in txt for p in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                            continue

                        # Extract email
                        email_m = re.search(r"([a-zA-Z0-9._%+-]+@kku\.ac\.th)", txt)
                        email = email_m.group(1).strip() if email_m else None

                        # Extract Scholar URL
                        scholar = card.find("a", href=lambda h: h and "scholar.google" in h)
                        scholar_url = scholar["href"] if scholar else None

                        # Match Name and Academic Rank
                        # Format in card is typically: "ชื่อ นามสกุล ตำแหน่งทางวิชาการ"
                        m_rank = re.search(r"(ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|อาจารย์\s*ดร\.|ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)", txt)
                        if not m_rank:
                            continue
                        rank_str = m_rank.group(1).strip()
                        txt_before = txt[:m_rank.start()].strip()
                        txt_after = txt[m_rank.end():].strip()

                        # Determine if name is before or after rank
                        clean_name = None
                        if txt_before and not any(k in txt_before for k in ["วิชาเอก", "สาขาวิชา", "คณะ"]):
                            name_cand = txt_before.split()
                            if 1 <= len(name_cand) <= 3:
                                clean_name = " ".join(name_cand)
                        if not clean_name and txt_after:
                            # Strip email and english from txt_after
                            clean_after = re.sub(r"[a-zA-Z0-9._%+-]+@kku\.ac\.th", "", txt_after).strip()
                            name_cand = clean_after.split()
                            if name_cand:
                                clean_name = " ".join(name_cand[:2])

                        if not clean_name:
                            continue

                        full_name_th = f"{rank_str} {clean_name}"
                        if clean_name in seen_names:
                            continue
                        seen_names.add(clean_name)

                        # Extract English name if available in scholar URL query
                        name_en = None
                        if scholar_url and "q=" in scholar_url:
                            q_val = urllib.parse.parse_qs(urllib.parse.urlparse(scholar_url).query).get("q", [])
                            if q_val and not q_val[0].isdigit():
                                name_en = q_val[0].replace("+", " ").strip()

                        results.append({
                            "university_th": "มหาวิทยาลัยขอนแก่น",
                            "university_en": "Khon Kaen University",
                            "faculty_th": "คณะศึกษาศาสตร์",
                            "faculty_en": "Faculty of Education",
                            "department_th": dept_th,
                            "raw_name_th": full_name_th,
                            "raw_name_en": name_en,
                            "email": email,
                            "scholar_url": scholar_url,
                            "image_url": urllib.parse.quote(src, safe=":/%?=") if src else None,
                            "profile_url": url,
                            "research_interests": ["Education", "Curriculum and Instruction", dept_th.replace("สาขาวิชาการศึกษา", "").strip()],
                        })
        except Exception as exc:
            print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from KKU Faculty of Education.")
    return results


def crawl_nu_nursing(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic nursing faculty from Naresuan University Faculty of Nursing."""
    print("\n[Crawler 3/4] Scraping Naresuan University Faculty of Nursing (คณะพยาบาลศาสตร์ ม.นเรศวร)...", flush=True)
    url = "http://www.nurse.nu.ac.th/webdpmnr/persont1.html"
    results = []

    try:
        r = client.get(url, follow_redirects=True, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        content = r.content.decode("cp874", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")
        seen_names = set()

        for td in soup.find_all("td"):
            txt = td.get_text(" ", strip=True)
            if "view_person_detail.asp" in str(td) and any(p in txt for p in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "น.ส.", "Ms.", "Mr.", "Mrs."]):
                img = td.find("img")
                img_src = img["src"] if img and img.get("src") else None
                if img_src and not img_src.startswith("http"):
                    img_src = "http://www.nurse.nu.ac.th/webdpmnr/" + img_src.lstrip("/ ")

                links = td.find_all("a", href=True)
                name_line = None
                email = None
                profile_url = None

                for a in links:
                    t = a.get_text(strip=True)
                    h = a["href"]
                    if "view_person_detail.asp" in h:
                        profile_url = h if h.startswith("http") else f"http://www.nurse.nu.ac.th/mis/person/{h.lstrip('/ ')}"
                        if any(p in t for p in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "น.ส.", "Ms.", "Mr.", "Mrs."]) and not any(t.startswith(k) for k in ["Email", "โทรศัพท์", "ลา"]):
                            name_line = t
                    if "Email" in t or "@" in t:
                        em = re.search(r"([a-zA-Z0-9._%+-]+@nu\.ac\.th)", t, re.IGNORECASE)
                        if em:
                            email = em.group(1).strip()

                if not name_line:
                    continue

                # Clean and split name_line into English and Thai
                # e.g. "Assist.Prof.Dr.Pratuma Rithphoผศ.ดร.ประทุมา ฤทธิ์โพธิ์"
                m_split = re.match(r"^([A-Za-z\s.,-]+?)((?:ผศ\.|รศ\.|ศ\.|อ\.|ดร\.|น\.ส\.|นาย|นาง)[\s\S]+)$", name_line)
                if m_split:
                    name_en = m_split.group(1).strip()
                    name_th = m_split.group(2).strip()
                else:
                    name_en = None
                    name_th = name_line

                # Remove non-breaking spaces
                name_th = name_th.replace("\xa0", " ").strip()
                name_th = re.sub(r"\s+", " ", name_th)

                if name_th in seen_names:
                    continue
                seen_names.add(name_th)

                results.append({
                    "university_th": "มหาวิทยาลัยนเรศวร",
                    "university_en": "Naresuan University",
                    "faculty_th": "คณะพยาบาลศาสตร์",
                    "faculty_en": "Faculty of Nursing",
                    "department_th": "ภาควิชาการพยาบาลศาสตร์",
                    "raw_name_th": name_th,
                    "raw_name_en": name_en,
                    "email": email,
                    "image_url": urllib.parse.quote(img_src, safe=":/%?=") if img_src else None,
                    "profile_url": profile_url or url,
                    "research_interests": ["Nursing Science", "Clinical Nursing", "Community Health Nursing", "Gerontological Nursing"],
                })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from NU Faculty of Nursing.")
    return results


def crawl_chula_sasin(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic business & management faculty from Chulalongkorn University Sasin School of Management."""
    print("\n[Crawler 4/4] Scraping Chulalongkorn University Sasin School of Management (สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ จุฬาฯ)...", flush=True)
    url = "https://www.sasin.edu/team/faculty"
    results = []

    try:
        r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        grid = soup.find("div", class_=lambda c: c and "tw:grid" in c and "tw:gap-4" in c)
        if not grid:
            print("  [Warn] Sasin grid element not found.")
            return results

        seen_names = set()

        for a in grid.find_all("a", href=True):
            if "/team/profile/" not in a["href"]:
                continue

            txt = a.get_text(" ", strip=True)
            img = a.find("img")
            img_src = img.get("src") if img else None

            # Clean name
            clean_txt = txt.replace("View Profile", "").strip()
            name_clean = re.sub(
                r"(Resident|Visiting|Deputy Director|Director|Assistant Director|Senior Fellow and|Fellow and|Senior Research Fellow and)",
                "", clean_txt
            ).strip()

            if not name_clean or len(name_clean) < 3:
                continue

            # Strip trailing degrees like , Ph.D., CFA
            m_deg = re.match(r"^([^,]+?)(?:,\s*(?:Ph\.?D\.?|CFA|DIC|CStat|M\.?D\.?|M\.?B\.?A\.?))*$", name_clean)
            base_name = m_deg.group(1).strip() if m_deg else name_clean

            if base_name in seen_names:
                continue
            seen_names.add(base_name)

            # Map English rank to Thai prefix
            rank_th = "อาจารย์"
            if "Professor" in base_name and "Associate" not in base_name and "Assistant" not in base_name:
                rank_th = "ศ."
            elif "Associate Professor" in base_name:
                rank_th = "รศ."
            elif "Assistant Professor" in base_name:
                rank_th = "ผศ."
            elif "Dr." in base_name:
                rank_th = "ดร."

            clean_person_en = re.sub(r"^(Professor|Associate Professor|Assistant Professor|Dr\.)\s*", "", base_name).strip()
            name_parts = clean_person_en.split()
            first_name = name_parts[0] if name_parts else clean_person_en
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else first_name

            raw_name_th = f"{rank_th} {clean_person_en}"
            profile_href = a["href"]
            profile_url = f"https://www.sasin.edu{profile_href}" if profile_href.startswith("/") else profile_href

            results.append({
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "university_en": "Chulalongkorn University",
                "faculty_th": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์",
                "faculty_en": "Sasin School of Management",
                "department_th": "สาขาวิชาบริหารธุรกิจ",
                "raw_name_th": raw_name_th,
                "raw_name_en": base_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": None,
                "image_url": urllib.parse.quote(img_src, safe=":/%?=") if img_src else None,
                "profile_url": profile_url,
                "research_interests": ["Business Administration", "Finance", "Management", "Marketing", "Sustainable Development"],
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from CU Sasin School of Management.")
    return results


# =====================================================================
# 2. State Reducer, Normalization & OpenAlex Disambiguation (Pillar 4 & 2)
# =====================================================================

TITLE_PREFIXES = [
    ("ศาสตราจารย์ ดร.", "ศ.ดร."),
    ("รองศาสตราจารย์ ดร.", "รศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ ดร.", "ผศ.ดร."),
    ("อาจารย์ ดร.", "อ.ดร."),
    ("ศาสตราจารย์", "ศ."),
    ("รองศาสตราจารย์", "รศ."),
    ("ผู้ช่วยศาสตราจารย์", "ผศ."),
    ("อาจารย์", "อ."),
    ("ศ.ดร.", "ศ.ดร."),
    ("รศ.ดร.", "รศ.ดร."),
    ("ผศ.ดร.", "ผศ.ดร."),
    ("อ.ดร.", "อ.ดร."),
    ("ดร.", "ดร."),
    ("ศ.", "ศ."),
    ("รศ.", "รศ."),
    ("ผศ.", "ผศ."),
    ("อ.", "อ."),
    ("Assoc. Prof. Dr.", "รศ.ดร."),
    ("Asst. Prof. Dr.", "ผศ.ดร."),
    ("Assoc. Prof.", "รศ."),
    ("Asst. Prof.", "ผศ."),
    ("Prof. Dr.", "ศ.ดร."),
    ("Prof.", "ศ."),
    ("Dr.", "ดร."),
]


def normalize_thai_title_and_name(raw_name: str) -> tuple[str, str, str]:
    """Splits academic rank and extracts clean full name and title."""
    clean = re.sub(
        r"(หัวหน้าภาควิชา|รองคณบดี.*|คณบดี.*|ผู้ช่วยคณบดี.*|ผู้อำนวยการ.*|ประธานหลักสูตร.*|ประธานสาขา.*)",
        "", raw_name
    ).strip()
    clean = re.sub(r"\s+", " ", clean)

    matched_title = ""
    for full_p, norm_p in TITLE_PREFIXES:
        if clean.startswith(full_p):
            matched_title = norm_p
            clean = clean[len(full_p):].strip()
            break

    if not matched_title:
        matched_title = "อาจารย์"

    # Strip redundant secondary prefixes
    if clean.startswith("ดร.") or clean.startswith("ดร "):
        clean = re.sub(r"^ดร\.?\s*", "", clean).strip()
        if "ดร." not in matched_title:
            matched_title = f"{matched_title}ดร." if matched_title.endswith(".") else f"{matched_title}.ดร."

    full_th = f"{matched_title} {clean}" if matched_title else clean
    return matched_title, clean, full_th


def enrich_openalex_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex for author citations, h-index, and featured publications (Pillar 2)."""
    search_query = record.get("raw_name_en") or record["clean_name_th"]
    url = f"https://api.openalex.org/authors?search={urllib.parse.quote(search_query)}&per-page=5"
    data = fetch_oa_with_retry(url)

    record["openalex_id"] = "not_indexed"
    record["total_citations"] = 0
    record["h_index"] = 0
    record["total_publications_count"] = 0
    record["first_author_count"] = 0
    record["co_author_count"] = 0
    record["featured_publications"] = []

    if data and "results" in data and len(data["results"]) > 0:
        cands = data["results"]
        matched_cand = None

        univ_th = record["university_th"]
        univ_en = TH_TO_EN_CANONICAL.get(univ_th, "")

        for cand in cands:
            insts = cand.get("last_known_institutions") or []
            cand_affil_str = " ".join([i.get("display_name", "") for i in insts if isinstance(i, dict)]).lower()

            # 2-Factor Disambiguation: match institution name keywords
            if any(k in cand_affil_str for k in ["chulalongkorn", "khon kaen", "naresuan", "sasin", "thailand"]):
                matched_cand = cand
                break

        if not matched_cand and cands:
            cand0 = cands[0]
            if (cand0.get("works_count") or 0) > 0:
                matched_cand = cand0

        if matched_cand:
            oa_id = matched_cand.get("id", "").replace("https://openalex.org/", "")
            record["openalex_id"] = oa_id
            record["total_citations"] = matched_cand.get("cited_by_count") or 0
            summary = matched_cand.get("summary_stats") or {}
            record["h_index"] = summary.get("h_index") or 0
            record["total_publications_count"] = matched_cand.get("works_count") or 0

            # Pull up to 3 featured publications
            works_url = matched_cand.get("works_api_url")
            if works_url:
                works_data = fetch_oa_with_retry(f"{works_url}?per-page=3")
                if works_data and "results" in works_data:
                    f_pubs = []
                    for w in works_data["results"]:
                        title = w.get("title")
                        if title:
                            venue = (w.get("primary_location") or {}).get("source") or {}
                            f_pubs.append({
                                "title": title,
                                "year": w.get("publication_year"),
                                "venue": venue.get("display_name") if isinstance(venue, dict) else None,
                                "url": w.get("doi") or f"https://openalex.org/{w.get('id', '')}",
                                "citation_count": w.get("cited_by_count") or 0,
                            })
                    record["featured_publications"] = f_pubs

    return record


# =====================================================================
# 3. Execution Pipeline & PostgreSQL Ingestion
# =====================================================================

def execute_wave69_acquisition():
    print("=" * 70, flush=True)
    print("🚀 EXECUTING WAVE 69 GRADUATE-FOCUSED FACULTIES ACQUISITION", flush=True)
    print("=" * 70, flush=True)

    if CHECKPOINT_FILE.exists() and CHECKPOINT_FILE.stat().st_size > 1000:
        print(f"  [Resume] Loading pre-extracted records from checkpoint {CHECKPOINT_FILE}...", flush=True)
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            enriched_records = json.load(f)
        print(f"  -> Successfully resumed {len(enriched_records)} records from checkpoint.", flush=True)
    else:
        client = httpx.Client(headers=CLIENT_HEADERS, verify=False, timeout=15.0)
        all_harvested: List[Dict[str, Any]] = []

        # Execute targeted headless crawlers
        all_harvested.extend(crawl_chula_population_studies(client))
        all_harvested.extend(crawl_kku_education(client))
        all_harvested.extend(crawl_nu_nursing(client))
        all_harvested.extend(crawl_chula_sasin(client))

        print(f"\n📊 Total raw harvested faculty records: {len(all_harvested)}", flush=True)

        # State Reducer & Normalization
        processed_records: List[Dict[str, Any]] = []
        seen_dedup = set()

        for r in all_harvested:
            title, clean_name, full_th = normalize_thai_title_and_name(r["raw_name_th"])
            name_parts = clean_name.split()
            first_name = r.get("first_name") or (name_parts[0] if name_parts else clean_name)
            last_name = r.get("last_name") or (" ".join(name_parts[1:]) if len(name_parts) > 1 else first_name)

            dedup_key = (r["university_th"], full_th)
            if dedup_key in seen_dedup:
                continue
            seen_dedup.add(dedup_key)

            r["academic_title_th"] = title
            r["clean_name_th"] = clean_name
            r["full_name_th"] = full_th
            r["first_name"] = first_name
            r["last_name"] = last_name

            processed_records.append(r)

        print(f"🧹 After deduplication: {len(processed_records)} unique faculty candidates.", flush=True)

        # Enrich via OpenAlex Multiplexer (ThreadPoolExecutor)
        print("\n🔍 Enriching with OpenAlex research metrics (Pillar 2)...", flush=True)
        with ThreadPoolExecutor(max_workers=5) as executor:
            enriched_records = list(executor.map(enrich_openalex_record, processed_records))

        # Disk Checkpoint (Pillar 5)
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(enriched_records, f, ensure_ascii=False, indent=2)
        print(f"💾 Checkpoint safely written to {CHECKPOINT_FILE}", flush=True)

    # Commit to Database with ID Sequence Separators
    print("\n📥 Ingesting into PostgreSQL 'faculties' table...", flush=True)
    db = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        counters = {
            "cu_cps": 1,
            "kku_ed": 1,
            "nu_nurse": 1,
            "cu_sasin": 1,
        }

        for r in enriched_records:
            if "ประชากรศาสตร์" in r["faculty_th"]:
                prefix = "cu_cps"
            elif "ศึกษาศาสตร์" in r["faculty_th"] and "ขอนแก่น" in r["university_th"]:
                prefix = "kku_ed"
            elif "พยาบาลศาสตร์" in r["faculty_th"] and "นเรศวร" in r["university_th"]:
                prefix = "nu_nurse"
            elif "ศศินทร์" in r["faculty_th"]:
                prefix = "cu_sasin"
            else:
                prefix = "wave69"

            # Check if person already exists by (university_th, clean_name)
            existing = db.query(FacultyDB).filter(
                FacultyDB.university_th == r["university_th"],
                FacultyDB.full_name_th.like(f"%{r['clean_name_th']}%")
            ).first()

            if existing:
                if (r["total_citations"] or 0) > (existing.total_citations or 0):
                    existing.total_citations = r["total_citations"]
                    existing.h_index = r["h_index"]
                    existing.openalex_id = r["openalex_id"]
                if not existing.image_url and r["image_url"]:
                    existing.image_url = r["image_url"]
                if not existing.email and r["email"]:
                    existing.email = r["email"]
                updated_count += 1
            else:
                while True:
                    candidate_id = f"{prefix}__{counters.get(prefix, 1):03d}"
                    counters[prefix] = counters.get(prefix, 1) + 1
                    if not db.query(FacultyDB).filter(FacultyDB.id == candidate_id).first():
                        break

                new_fac = FacultyDB(
                    id=candidate_id,
                    university_th=r["university_th"],
                    university=r["university_en"],
                    faculty=r["faculty_en"],
                    faculty_th=r["faculty_th"],
                    department_th=r["department_th"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    academic_title_th=r["academic_title_th"],
                    full_name_th=r["full_name_th"],
                    email=r["email"],
                    image_url=r["image_url"],
                    profile_url=r["profile_url"],
                    scholar_url=r.get("scholar_url"),
                    research_interests=r.get("research_interests") or [],
                    featured_publications=r.get("featured_publications") or [],
                    total_citations=r.get("total_citations") or 0,
                    h_index=r.get("h_index") or 0,
                    total_publications_count=r.get("total_publications_count") or 0,
                    first_author_count=r.get("first_author_count") or 0,
                    co_author_count=r.get("co_author_count") or 0,
                    openalex_id=r.get("openalex_id") or "not_indexed",
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,  # Non-blocking circuit breaker (Pillar 3)
                )
                db.add(new_fac)
                inserted_count += 1

        db.commit()
        print(f"✅ Ingestion successful: {inserted_count} new faculty inserted, {updated_count} existing faculty updated.")
    finally:
        db.close()


if __name__ == "__main__":
    execute_wave69_acquisition()
