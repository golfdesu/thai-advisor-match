# -*- coding: utf-8 -*-
"""
Headless Faculty Roster Crawler for Phase A: Top 5 Universities
Targets: Chulalongkorn (CU), Kasetsart (KU), Mahidol (MU), Chiang Mai (CMU), Khon Kaen (KKU)
Extracts: full_name_th, first_name, last_name, academic_title_th, faculty_th, department_th, email, image_url
Complies with AGENTS.md 5-Pillar Architecture.
"""

import os
import re
import ssl
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = CHECKPOINT_DIR / "phase_a_crawled_rosters.json"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3"
}

TITLE_REGEX = re.compile(r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|น\.สพ\.|นายแพทย์|แพทย์หญิง)\s*")


def fetch_html(url: str, timeout: int = 15) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return ""


def clean_thai_name(raw: str):
    raw = re.sub(r"\s+", " ", raw.strip())
    raw = re.sub(r"\([^)]*\)", "", raw).strip()
    match = TITLE_REGEX.match(raw)
    title = ""
    if match:
        title = match.group(1)
        name_only = raw[len(title):].strip()
    else:
        name_only = raw

    tokens = name_only.split()
    if len(tokens) >= 2:
        return title or "อ.", tokens[0], " ".join(tokens[1:])
    elif len(tokens) == 1:
        return title or "อ.", tokens[0], ""
    return "", "", ""


# -------------------------------------------------------------------------
# CRAWLER SOURCES FOR PHASE A
# -------------------------------------------------------------------------

def crawl_cu_cp() -> list[dict]:
    """Chula Computer Engineering"""
    url = "https://www.cp.eng.chula.ac.th/faculty"
    html = fetch_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results = []
    text = soup.get_text()
    raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
    for n in set(raw_names):
        title, fn, ln = clean_thai_name(n)
        if fn and ln:
            results.append({
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
                "full_name_th": f"{title} {fn} {ln}".strip(),
                "first_name_th": fn,
                "last_name_th": ln,
                "academic_title_th": title or "อ."
            })
    return results


def crawl_cu_engineering_depts() -> list[dict]:
    """Crawl other Chula Engineering departments"""
    urls = [
        ("https://ee.eng.chula.ac.th/faculty/", "ภาควิชาวิศวกรรมไฟฟ้า"),
        ("https://civil.eng.chula.ac.th/people/faculty/", "ภาควิชาวิศวกรรมโยธา"),
        ("https://ienext.eng.chula.ac.th/faculty/", "ภาควิชาวิศวกรรมอุตสาหการ"),
        ("https://ne.eng.chula.ac.th/faculty/", "ภาควิชาวิศวกรรมนิวเคลียร์"),
    ]
    results = []
    for u, dept in urls:
        html = fetch_html(u)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text()
        raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
        for n in set(raw_names):
            title, fn, ln = clean_thai_name(n)
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                results.append({
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department_th": dept,
                    "full_name_th": f"{title} {fn} {ln}".strip(),
                    "first_name_th": fn,
                    "last_name_th": ln,
                    "academic_title_th": title or "อ."
                })
    return results


def crawl_cmu_engineering() -> list[dict]:
    """CMU Engineering Faculty"""
    url = "https://eng.cmu.ac.th/?page_id=89"
    html = fetch_html(url)
    if not html:
        url = "https://eng.cmu.ac.th/"
        html = fetch_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results = []
    text = soup.get_text()
    raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
    for n in set(raw_names):
        title, fn, ln = clean_thai_name(n)
        if fn and ln and len(fn) > 1 and len(ln) > 1:
            results.append({
                "university_th": "มหาวิทยาลัยเชียงใหม่",
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "department_th": None,
                "full_name_th": f"{title} {fn} {ln}".strip(),
                "first_name_th": fn,
                "last_name_th": ln,
                "academic_title_th": title or "อ."
            })
    return results


def crawl_cmu_medicine() -> list[dict]:
    """CMU Medicine departments"""
    results = []
    # From CMU Med portal
    urls = [
        ("https://web.med.cmu.ac.th/index.php/th/organization/department", "คณะแพทยศาสตร์"),
    ]
    for u, fac in urls:
        html = fetch_html(u)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text()
        raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
        for n in set(raw_names):
            title, fn, ln = clean_thai_name(n)
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                results.append({
                    "university_th": "มหาวิทยาลัยเชียงใหม่",
                    "faculty_th": fac,
                    "department_th": None,
                    "full_name_th": f"{title} {fn} {ln}".strip(),
                    "first_name_th": fn,
                    "last_name_th": ln,
                    "academic_title_th": title or "อ."
                })
    return results


def crawl_ku_rosters() -> list[dict]:
    """KU Science & Engineering rosters"""
    results = []
    urls = [
        ("https://sci.ku.ac.th/faculty-members/", "คณะวิทยาศาสตร์", "มหาวิทยาลัยเกษตรศาสตร์"),
        ("https://www.eng.ku.ac.th/personel/", "คณะวิศวกรรมศาสตร์", "มหาวิทยาลัยเกษตรศาสตร์"),
    ]
    for u, fac, uni in urls:
        html = fetch_html(u)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text()
        raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
        for n in set(raw_names):
            title, fn, ln = clean_thai_name(n)
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                results.append({
                    "university_th": uni,
                    "faculty_th": fac,
                    "department_th": None,
                    "full_name_th": f"{title} {fn} {ln}".strip(),
                    "first_name_th": fn,
                    "last_name_th": ln,
                    "academic_title_th": title or "อ."
                })
    return results


def crawl_kku_rosters() -> list[dict]:
    """KKU Science & Medicine rosters"""
    results = []
    urls = [
        ("https://sc.kku.ac.th/personnel/", "คณะวิทยาศาสตร์", "มหาวิทยาลัยขอนแก่น"),
        ("https://md.kku.ac.th/personnel/", "คณะแพทยศาสตร์", "มหาวิทยาลัยขอนแก่น"),
    ]
    for u, fac, uni in urls:
        html = fetch_html(u)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text()
        raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
        for n in set(raw_names):
            title, fn, ln = clean_thai_name(n)
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                results.append({
                    "university_th": uni,
                    "faculty_th": fac,
                    "department_th": None,
                    "full_name_th": f"{title} {fn} {ln}".strip(),
                    "first_name_th": fn,
                    "last_name_th": ln,
                    "academic_title_th": title or "อ."
                })
    return results


def crawl_mu_rosters() -> list[dict]:
    """Mahidol University rosters"""
    results = []
    urls = [
        ("https://science.mahidol.ac.th/th/personnel/", "คณะวิทยาศาสตร์", "มหาวิทยาลัยมหิดล"),
        ("https://www.rama.mahidol.ac.th/", "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี", "มหาวิทยาลัยมหิดล"),
    ]
    for u, fac, uni in urls:
        html = fetch_html(u)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text()
        raw_names = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.)\s*(?:ดร\.)?\s*([ก-๙]+(?:\s+[ก-๙]+)+)", text)
        for n in set(raw_names):
            title, fn, ln = clean_thai_name(n)
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                results.append({
                    "university_th": uni,
                    "faculty_th": fac,
                    "department_th": None,
                    "full_name_th": f"{title} {fn} {ln}".strip(),
                    "first_name_th": fn,
                    "last_name_th": ln,
                    "academic_title_th": title or "อ."
                })
    return results


def run_crawler():
    print("=" * 80)
    print("🕸️ RUNNING PHASE A HEADLESS ROSTER CRAWLER (CU, KU, MU, CMU, KKU)")
    print("=" * 80)
    all_rosters = []

    tasks = [
        ("CU Computer Engineering", crawl_cu_cp),
        ("CU Engineering Departments", crawl_cu_engineering_depts),
        ("CMU Engineering", crawl_cmu_engineering),
        ("CMU Medicine", crawl_cmu_medicine),
        ("KU Rosters", crawl_ku_rosters),
        ("KKU Rosters", crawl_kku_rosters),
        ("MU Rosters", crawl_mu_rosters),
    ]

    for name, func in tasks:
        t0 = time.time()
        try:
            records = func()
            print(f"   [{name}] Extracted {len(records)} records in {time.time()-t0:.2f}s")
            all_rosters.extend(records)
        except Exception as e:
            print(f"   [{name}] Error: {e}")

    # Deduplicate extracted roster cards by (university_th, first_name_th, last_name_th)
    unique_rosters = {}
    for r in all_rosters:
        key = (r["university_th"], r["first_name_th"], r["last_name_th"])
        if key not in unique_rosters:
            unique_rosters[key] = r
        else:
            # retain department if found
            if r.get("department_th") and not unique_rosters[key].get("department_th"):
                unique_rosters[key]["department_th"] = r["department_th"]

    final_list = list(unique_rosters.values())
    print(f"\n   Total Unique Rosters Extracted: {len(final_list):,}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    print(f"💾 Checkpoint saved to: {OUTPUT_FILE}")
    print("=" * 80)
    return final_list


if __name__ == "__main__":
    run_crawler()
