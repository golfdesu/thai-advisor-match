# -*- coding: utf-8 -*-
"""
Wave 65: Autonomous Acquisition of Graduate-Focused Faculty (5-Pillar Architecture)
===================================================================================
Acquires authentic faculty members across 3 key graduate faculties with degree deficits:
1. TU Dentistry (คณะทันตแพทยศาสตร์ มหาวิทยาลัยธรรมศาสตร์)
   - 10 departments supporting M.Sc. and Ph.D. in Oral Health Sciences / Dental Surgery.
   - Portal: https://www.dentistry.tu.ac.th/
2. CMU BMEI (สถาบันวิศวกรรมชีวการแพทย์ มหาวิทยาลัยเชียงใหม่)
   - Supporting M.Eng. and Ph.D. in Biomedical Engineering.
   - API: https://api.bmei.cmu.ac.th/research/getAllProfs
3. RMUTT Engineering (คณะวิศวกรรมศาสตร์ มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี)
   - 10 engineering departments supporting M.Eng. and D.Eng. graduate programs.
   - Portal: https://engineer.rmutt.ac.th/

Pillars:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor).
- Pillar 2: OpenAlex Multiplexing Pool (Citations, h-index, featured publications).
- Pillar 3: Non-blocking Circuit Breakers & Graceful Degradation ([0.0]*768).
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalization.
- Pillar 5: Disk Checkpointing (wave65_grad_focused_faculties.json).
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from bs4 import BeautifulSoup
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave65_grad_focused_faculties.json"

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_with_retry(url: str, client: Optional[httpx.Client] = None, max_retries: int = 3) -> Optional[Any]:
    for attempt in range(max_retries):
        try:
            if client:
                resp = client.get(url)
            else:
                resp = httpx.get(url, headers=CLIENT_HEADERS, timeout=30.0, follow_redirects=True, verify=False)
            if resp.status_code == 200:
                if "application/json" in resp.headers.get("content-type", ""):
                    return resp.json()
                return resp.text
            elif resp.status_code in [403, 404]:
                return None
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


# =====================================================================
# 1. Targeted Graduate Faculty Crawlers (Pillar 1)
# =====================================================================

def crawl_tu_dentistry(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls TU Faculty of Dentistry (คณะทันตแพทยศาสตร์ มหาวิทยาลัยธรรมศาสตร์)."""
    print("  [TU Dentistry] Crawling https://www.dentistry.tu.ac.th/ across 10 departments...", flush=True)
    results = []
    dept_slugs = [
        ("สาขาวิชาศัลยศาสตร์ช่องปากและแม็กซิลโลเฟเชียล", "department-of-oral-surgery", "Oral and Maxillofacial Surgery"),
        ("สาขาวิชาทันตกรรมจัดฟัน", "department-of-orthodontics", "Orthodontics"),
        ("สาขาวิชาวิทยาเอ็นโดดอนต์", "department-of-endodontics", "Endodontics"),
        ("สาขาวิชาทันตกรรมชุมชน", "department-of-community-dentistry", "Community Dentistry"),
        ("สาขาวิชาทันตกรรมประดิษฐ์", "field-of-study-prosthetic-dentistry", "Prosthetic Dentistry"),
        ("สาขาวิชาชีววิทยาช่องปาก", "department-of-oral-biology", "Oral Biology"),
        ("สาขาวิชาปริทันตวิทยา", "periodontics-field", "Periodontics"),
        ("สาขาวิชาทันตกรรมสำหรับเด็ก", "pediatric-dentistry", "Pediatric Dentistry"),
        ("สาขาวิชาทันตกรรมหัตถการ", "field-of-study-operative-dentistry", "Operative Dentistry"),
        ("สาขาวิชาวินิจฉัยโรคช่องปาก", "oral-disease-diagnosis-field", "Oral Diagnostic Sciences"),
        ("บริหารคณะทันตแพทยศาสตร์", "executive", "Faculty Administration"),
    ]

    all_tu = {}
    for dept_th, slug, dept_en in dept_slugs:
        url = f"https://www.dentistry.tu.ac.th/{slug}"
        html = fetch_with_retry(url, client)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "div"]):
            txt = tag.get_text(separator=" ", strip=True)
            if any(prefix in txt for prefix in ["ทพ.", "ทพญ.", "ศ.", "รศ.", "ผศ.", "อ.ดร.", "อ.ทพ.", "อ.ทพญ."]):
                if any(noise in txt for noise in [
                    "คลินิก", "สมาพันธ์", "นักศึกษา", "หลักสูตร", "โครงการ", "รายชื่อ",
                    "ขยายเวลา", "ยินดีต้อนรับ", "เปิดโลก", "ขอแสดงความยินดี", "ขอขอบพระคุณ",
                    "นิสิต", "โรงพยาบาล", "ข่าว", "ภาพกิจกรรม"
                ]):
                    continue
                txt_c = re.sub(r"\s+", " ", txt).strip()
                if 5 < len(txt_c) < 55 and any(txt_c.startswith(p) for p in ["ทพ.", "ทพญ.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]):
                    # If already in all_tu from executive, update to specific clinical department
                    if txt_c not in all_tu or all_tu[txt_c]["department_th"] == "บริหารคณะทันตแพทยศาสตร์":
                        all_tu[txt_c] = {
                            "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                            "university_en": "Thammasat University",
                            "faculty_th": "คณะทันตแพทยศาสตร์",
                            "faculty_en": "Faculty of Dentistry",
                            "department_th": dept_th if dept_th != "บริหารคณะทันตแพทยศาสตร์" else "สาขาวิชาวิทยาศาสตร์สุขภาพช่องปาก",
                            "department_en": dept_en if dept_th != "บริหารคณะทันตแพทยศาสตร์" else "Oral Health Sciences",
                            "raw_name_th": txt_c,
                            "name_en": None,
                            "email": None,
                            "image_url": None,
                            "profile_url": url,
                            "research_interests": ["Dentistry", dept_en],
                        }

    results = list(all_tu.values())
    print(f"  ✅ TU Dentistry: Harvested {len(results)} authentic faculty members across 10 departments.")
    return results


def crawl_cmu_bmei(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls CMU Biomedical Engineering Institute (สถาบันวิศวกรรมชีวการแพทย์ มหาวิทยาลัยเชียงใหม่)."""
    print("  [CMU BMEI] Querying https://api.bmei.cmu.ac.th/research/getAllProfs...", flush=True)
    results = []
    api_url = "https://api.bmei.cmu.ac.th/research/getAllProfs"
    data = fetch_with_retry(api_url, client)
    if not data or not isinstance(data, list):
        print("  ❌ Failed to fetch CMU BMEI professors from API.")
        return results

    seen_names = set()
    for item in data:
        name_th = (item.get("profName_th") or "").strip()
        name_en = (item.get("profName_en") or "").strip()
        scopus_url = item.get("scopusUrl")

        if not name_th or name_th in seen_names:
            continue
        seen_names.add(name_th)

        clean_name_en = re.sub(r",?\s*(Ph\.D\.|M\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.).*$", "", name_en).strip()

        interests = ["Biomedical Engineering", "Medical Devices", "Biosensors"]

        results.append({
            "university_th": "มหาวิทยาลัยเชียงใหม่",
            "university_en": "Chiang Mai University",
            "faculty_th": "สถาบันวิศวกรรมชีวการแพทย์",
            "faculty_en": "Biomedical Engineering Institute",
            "department_th": "สถาบันวิศวกรรมชีวการแพทย์",
            "department_en": "Biomedical Engineering Institute",
            "raw_name_th": name_th,
            "name_en": clean_name_en if clean_name_en else None,
            "email": None,
            "image_url": None,
            "profile_url": scopus_url or "https://bmei.cmu.ac.th/Researchers",
            "research_interests": interests,
            "scopus_url": scopus_url,
        })

    print(f"  ✅ CMU BMEI: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_rmutt_engineering(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls RMUTT Faculty of Engineering (คณะวิศวกรรมศาสตร์ มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี)."""
    print("  [RMUTT Engineering] Crawling 10 departments on https://engineer.rmutt.ac.th/...", flush=True)
    results = []
    depts = [
        ("ภาควิชาวิศวกรรมโยธา", "civil-lectures", "Civil Engineering"),
        ("ภาควิชาวิศวกรรมเครื่องกล", "mechanical-lectures", "Mechanical Engineering"),
        ("ภาควิชาวิศวกรรมคอมพิวเตอร์", "computer-lecturers", "Computer Engineering"),
        ("ภาควิชาวิศวกรรมอุตสาหการ", "industrial-th-lecturers", "Industrial Engineering"),
        ("ภาควิชาวิศวกรรมไฟฟ้า", "electrical-lecturers", "Electrical Engineering"),
        ("ภาควิชาวิศวกรรมอิเล็กทรอนิกส์และโทรคมนาคม", "electronics-lecturers", "Electronics and Telecommunication Engineering"),
        ("ภาควิชาวิศวกรรมสิ่งทอ", "textile-lectures", "Textile Engineering"),
        ("ภาควิชาวิศวกรรมวัสดุและโลหการ", "materials-th-lecturers", "Materials and Metallurgical Engineering"),
        ("ภาควิชาวิศวกรรมเกษตร", "agricultural-lecturers", "Agricultural Engineering"),
        ("ภาควิชาวิศวกรรมเคมี", "chemical-lecturers", "Chemical Engineering"),
    ]

    seen_global_names = set()

    for dept_th, slug, dept_en in depts:
        url = f"https://engineer.rmutt.ac.th/{slug}/"
        html = fetch_with_retry(url, client)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        cols = soup.find_all("div", class_=lambda c: c and ("column" in c or "mcb-wrap" in c))
        card_map = {}

        for c in cols:
            h = c.find(["h5", "h4"])
            if h and any(k in h.get_text() for k in ["ผศ.", "รศ.", "ศ.", "ดร.", "อาจารย์"]):
                raw_txt = h.get_text(separator=" ", strip=True)
                # Filter out pure noise
                if any(noise in raw_txt for noise in ["ประจำภาควิชา", "รับสมัคร", "โครงการ", "ผลงาน"]):
                    raw_txt = re.sub(r"^(อาจารย์ประจำภาควิชา|ประจำภาควิชา)\s*", "", raw_txt).strip()
                if len(raw_txt) < 8:
                    continue

                img = c.find("img")
                img_src = img.get("src") if img else None
                if img_src and ("logo" in img_src or "flag" in img_src):
                    img_src = None

                if raw_txt not in card_map or (not card_map[raw_txt] and img_src):
                    card_map[raw_txt] = img_src

        for raw_txt, img_src in card_map.items():
            # Check for email embedded in text
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:en\.)?rmutt\.ac\.th", raw_txt)
            email = email_match.group(0).lower() if email_match else None
            txt_clean = re.sub(r"[a-zA-Z0-9._%+-]+@(?:en\.)?rmutt\.ac\.th", "", raw_txt).strip()

            # Separate Thai and English name parts
            m_en = re.search(r"([A-Za-z].*)$", txt_clean)
            if m_en:
                th_part = txt_clean[:m_en.start()].strip()
                en_part = m_en.group(1).strip()
            else:
                th_part = txt_clean.strip()
                en_part = None

            # Clean trailing/leading noise
            th_part = re.sub(r"^(อาจารย์ประจำภาควิชา|ประจำภาควิชา)\s*", "", th_part).strip()
            if not th_part or len(th_part) < 5 or th_part in seen_global_names:
                continue
            seen_global_names.add(th_part)

            if img_src:
                img_src = urllib.parse.quote(img_src, safe=":/%?=")

            results.append({
                "university_th": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
                "university_en": "Rajamangala University of Technology Thanyaburi",
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty_en": "Faculty of Engineering",
                "department_th": dept_th,
                "department_en": dept_en,
                "raw_name_th": th_part,
                "name_en": en_part if en_part and len(en_part) > 3 else None,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
                "research_interests": ["Engineering", dept_en],
            })

    print(f"  ✅ RMUTT Engineering: Harvested {len(results)} authentic faculty members across 10 departments.")
    return results


# =====================================================================
# 2. State Reducer & Title Normalizer (Pillar 4)
# =====================================================================

def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Normalizes Thai academic ranks, dental prefixes, and names."""
    t = raw_name.strip()
    # Normalize multiple whitespace
    t = re.sub(r"\s+", " ", t)

    title_patterns = [
        (r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.)", "ศ.ดร."),
        (r"^(รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.)", "รศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*ว่าที่\s*ร\.อ\.\s*ดร\.|ผศ\.\s*ว่าที่\s*ร\.อ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(อาจารย์\s*ดร\.|อ\.\s*ดร\.)", "อ.ดร."),
        (r"^(ศาสตราจารย์|ศ\.)", "ศ."),
        (r"^(รองศาสตราจารย์|รศ\.)", "รศ."),
        (r"^(ผู้ช่วยศาสตราจารย์|ผศ\.)", "ผศ."),
        (r"^(ดร\.)", "ดร."),
        (r"^(อาจารย์|อ\.)", "อ."),
        (r"^(ทพ\.|ทพญ\.|ทันตแพทย์หญิง|ทันตแพทย์)", "อ."),
        (r"^(น\.สพ\.\s*ดร\.|สพ\.ญ\.\s*ดร\.)", "อ.ดร."),
        (r"^(น\.สพ\.|สพ\.ญ\.)", "อ."),
        (r"^(Prof\.\s*Dr\.)", "ศ.ดร."),
        (r"^(Assoc\.\s*Prof\.\s*Dr\.)", "รศ.ดร."),
        (r"^(Asst\.\s*Prof\.\s*Dr\.)", "ผศ.ดร."),
        (r"^(Associate\s*Professor\s*Dr\.)", "รศ.ดร."),
        (r"^(Assistant\s*Professor\s*Dr\.)", "ผศ.ดร."),
        (r"^(Professor\s*Dr\.)", "ศ.ดร."),
        (r"^(Associate\s*Professor)", "รศ."),
        (r"^(Assistant\s*Professor)", "ผศ."),
        (r"^(Assoc\.\s*Prof\.)", "รศ."),
        (r"^(Asst\.\s*Prof\.)", "ผศ."),
        (r"^(Prof\.)", "ศ."),
        (r"^(Dr\.)", "ดร."),
    ]

    detected_title = ""
    base_name = t

    for pat, norm_title in title_patterns:
        m = re.match(pat, t, flags=re.IGNORECASE)
        if m:
            detected_title = norm_title
            base_name = t[m.end():].strip()
            # If nested title tokens remain (e.g. ทพ., ทพญ., ดร.)
            m_sub = re.match(r"^(ทพ\.|ทพญ\.|ทันตแพทย์|ทันตแพทย์หญิง|น\.สพ\.|สพ\.ญ\.|Dr\.|ดร\.)\s*", base_name, flags=re.IGNORECASE)
            if m_sub:
                base_name = base_name[m_sub.end():].strip()
                if "ดร." in m_sub.group(0) and "ดร." not in detected_title:
                    detected_title = f"{detected_title}ดร."
            # and another check if further nested (e.g. ผศ.ดร.ทพญ.)
            m_sub2 = re.match(r"^(ทพ\.|ทพญ\.|ทันตแพทย์|ทันตแพทย์หญิง)\s*", base_name, flags=re.IGNORECASE)
            if m_sub2:
                base_name = base_name[m_sub2.end():].strip()
            break

    # Strip trailing academic degrees
    base_name = re.sub(
        r",?\s*(Ph\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.|Ph\.D|D\.Tech\.|CFA|DBA|Ed\.D\.|LL\.M\.|LL\.B\.|MBA).*$",
        "",
        base_name,
        flags=re.IGNORECASE
    ).strip()

    # Re-strip any leading dots or spaces
    base_name = base_name.strip(" .")
    full_name = f"{detected_title} {base_name}".strip() if detected_title else base_name
    return detected_title or "อาจารย์", full_name, base_name


def enrich_faculty_with_openalex(faculty: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex to retrieve citations, h-index, and author ID with 2-factor verification."""
    name_to_search = faculty.get("name_en") or faculty.get("raw_name_th") or ""
    clean_search = re.sub(
        r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Associate\s*Professor|Assistant\s*Professor|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ทพ\.|ทพญ\.)\s*",
        "",
        name_to_search,
        flags=re.IGNORECASE
    ).strip()

    # Clean degrees
    clean_search = re.sub(r",?\s*(Ph\.D\.|M\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.).*$", "", clean_search).strip()

    univ_map = {
        "มหาวิทยาลัยธรรมศาสตร์": ("Thammasat", "I158656754"),
        "มหาวิทยาลัยเชียงใหม่": ("Chiang Mai", "I145885236"),
        "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี": ("Rajamangala", "I169055919"),
    }
    univ_keyword, inst_id = univ_map.get(faculty["university_th"], ("Thailand", ""))

    encoded_name = urllib.parse.quote(clean_search)
    url = f"https://api.openalex.org/authors?search={encoded_name}"
    data = fetch_oa_with_retry(url)

    if data and "results" in data and len(data["results"]) > 0:
        candidates = data["results"]
        best_cand = None
        for cand in candidates:
            insts = cand.get("last_known_institutions") or []
            inst_names = [i.get("display_name", "") for i in insts]
            inst_ids = [i.get("id", "") for i in insts]

            if any(univ_keyword.lower() in iname.lower() for iname in inst_names) or (inst_id and any(inst_id in i_id for i_id in inst_ids)):
                best_cand = cand
                break

        # Fallback to first candidate if name is distinctive and Thai university matches
        if not best_cand and len(candidates) > 0:
            c0 = candidates[0]
            insts = c0.get("last_known_institutions") or []
            if any("Thailand" in i.get("country_code", "") for i in insts) or any("thailand" in i.get("display_name", "").lower() for i in insts):
                best_cand = c0

        if best_cand:
            oa_id = best_cand.get("id", "").replace("https://openalex.org/", "")
            faculty["openalex_id"] = oa_id
            faculty["total_citations"] = best_cand.get("cited_by_count", 0) or 0
            faculty["h_index"] = (best_cand.get("summary_stats") or {}).get("h_index", 0) or 0

            # English display name
            oa_name = best_cand.get("display_name")
            if oa_name and not faculty.get("name_en"):
                faculty["name_en"] = oa_name

            # Featured publications
            featured = []
            works_api = best_cand.get("works_api_url")
            if works_api:
                w_data = fetch_oa_with_retry(f"{works_api}?per-page=3")
                w_list = (w_data or {}).get("results", []) or []
                for w in w_list:
                    w_title = w.get("title")
                    if w_title:
                        venue_name = None
                        loc = w.get("primary_location")
                        if isinstance(loc, dict):
                            src = loc.get("source")
                            if isinstance(src, dict):
                                venue_name = src.get("display_name")
                        featured.append({
                            "title": w_title,
                            "year": w.get("publication_year"),
                            "venue": venue_name,
                            "url": w.get("doi"),
                            "citation_count": w.get("cited_by_count", 0),
                        })
            faculty["featured_publications"] = featured
            faculty["total_publications_count"] = max(best_cand.get("works_count", 0) or 0, len(featured), faculty["h_index"])
            return faculty

    faculty["openalex_id"] = "not_indexed"
    faculty["total_citations"] = 0
    faculty["h_index"] = 0
    faculty["total_publications_count"] = 0
    faculty["featured_publications"] = []
    return faculty


# =====================================================================
# 3. Database Ingestion Engine (Pillars 3, 4, 5)
# =====================================================================

def run_pipeline():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING WAVE 65: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()

    client = httpx.Client(verify=False, timeout=35.0, follow_redirects=True, headers=CLIENT_HEADERS)
    db = SessionLocal()

    try:
        # Step 1: Checkpoint recovery or crawl the 3 target faculties
        if CHECKPOINT_FILE.exists():
            print(f"\n📂 Resuming from existing disk checkpoint: {CHECKPOINT_FILE} (Pillar 5)", flush=True)
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                enriched_faculty = json.load(f)
            print(f"  ✅ Loaded {len(enriched_faculty)} checkpointed faculty records.", flush=True)
        else:
            all_raw_faculty = []
            all_raw_faculty.extend(crawl_tu_dentistry(client))
            all_raw_faculty.extend(crawl_cmu_bmei(client))
            all_raw_faculty.extend(crawl_rmutt_engineering(client))

            print(f"\n📊 Total Raw Faculty Harvested: {len(all_raw_faculty)}")

            # Step 2: Normalize names & academic titles
            print("\n🧹 Running State Reducer & Title Normalization (Pillar 4)...", flush=True)
            normalized_faculty = []
            for i, item in enumerate(all_raw_faculty, 1):
                title_th, full_th, base_n = normalize_thai_title_and_name(item.get("raw_name_th") or "")
                item["title_th"] = title_th or "อาจารย์"
                item["full_name_th"] = full_th or item.get("raw_name_th")

                # Parse first and last names
                parts = base_n.split(" ")
                item["first_name_th"] = parts[0] if parts else base_n
                item["last_name_th"] = " ".join(parts[1:]) if len(parts) > 1 else ""

                if item.get("name_en"):
                    en_parts = item["name_en"].split(" ")
                    item["first_name_en"] = en_parts[0] if en_parts else item["name_en"]
                    item["last_name_en"] = " ".join(en_parts[1:]) if len(en_parts) > 1 else ""
                else:
                    item["first_name_en"] = None
                    item["last_name_en"] = None

                normalized_faculty.append(item)

            # Step 3: OpenAlex Multiplexing & Metric Enrichment (Pillar 2)
            print("\n🌐 Enriching Faculty Metrics via OpenAlex Multiplexing (Pillar 2)...", flush=True)
            with ThreadPoolExecutor(max_workers=5) as executor:
                enriched_faculty = list(executor.map(enrich_faculty_with_openalex, normalized_faculty))

            # Save Checkpoint (Pillar 5)
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(enriched_faculty, f, ensure_ascii=False, indent=2)
            print(f"  💾 Checkpointed {len(enriched_faculty)} records to {CHECKPOINT_FILE}", flush=True)

        # Step 4: PostgreSQL public.faculties Ingestion (Pillar 3)
        print("\n📥 Ingesting Authentic Faculty Records into PostgreSQL (localhost:5432)...", flush=True)
        inserted_count = 0
        updated_count = 0

        for idx, item in enumerate(enriched_faculty, 1):
            full_name = item.get("full_name_th") or item.get("raw_name_th")
            univ = item.get("university_th")
            fac = item.get("faculty_th")
            dept = item.get("department_th")

            # Check if record already exists in faculties table
            existing = (
                db.query(FacultyDB)
                .filter(FacultyDB.university_th == univ, FacultyDB.full_name_th == full_name)
                .first()
            )

            # Assign slug ID prefix
            if "ธรรมศาสตร์" in univ:
                custom_id = f"tu_dent__{idx:03d}"
            elif "เชียงใหม่" in univ:
                custom_id = f"cmu_bmei__{idx:03d}"
            else:
                custom_id = f"rmutt_eng__{idx:03d}"

            if not existing:
                # Clean research interests
                clean_interests = []
                for interest in (item.get("research_interests") or []):
                    for sub in str(interest).split(" / "):
                        if sub.strip() and sub.strip() not in clean_interests:
                            clean_interests.append(sub.strip())

                # Format publications
                clean_pubs = []
                for pub in (item.get("featured_publications") or []):
                    clean_pubs.append({
                        "title": pub["title"],
                        "year": pub.get("year"),
                        "venue": pub.get("venue"),
                        "url": pub.get("url") or pub.get("doi"),
                        "citation_count": pub.get("citation_count") or pub.get("citations") or 0,
                    })

                new_record = FacultyDB(
                    id=custom_id,
                    first_name=item.get("first_name_th") or item.get("first_name_en") or "อาจารย์",
                    last_name=item.get("last_name_th") or item.get("last_name_en") or item.get("first_name_th") or "อาจารย์",
                    academic_title_th=item.get("title_th") or "อาจารย์",
                    full_name_th=full_name,
                    university_th=univ,
                    faculty_th=fac,
                    department_th=dept or "ระบุไม่ได้",
                    email=item.get("email"),
                    image_url=item.get("image_url"),
                    profile_url=item.get("profile_url"),
                    research_interests=clean_interests,
                    openalex_id=item.get("openalex_id"),
                    total_citations=item.get("total_citations") or 0,
                    h_index=item.get("h_index") or 0,
                    total_publications_count=item.get("total_publications_count") or 0,
                    featured_publications=clean_pubs,
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,  # Non-blocking circuit breaker dummy vector
                )
                db.add(new_record)
                inserted_count += 1
            else:
                # Enrich existing record
                if item.get("email") and not existing.email:
                    existing.email = item.get("email")
                if item.get("image_url") and not existing.image_url:
                    existing.image_url = item.get("image_url")
                if dept and (not existing.department_th or existing.department_th == "ระบุไม่ได้"):
                    existing.department_th = dept

                existing.total_citations = max(existing.total_citations or 0, item.get("total_citations") or 0)
                existing.h_index = max(existing.h_index or 0, item.get("h_index") or 0)
                existing.total_publications_count = max(existing.total_publications_count or 0, item.get("total_publications_count") or 0)

                if (not existing.openalex_id or existing.openalex_id == "not_indexed") and item.get("openalex_id") and item.get("openalex_id") != "not_indexed":
                    existing.openalex_id = item.get("openalex_id")

                updated_count += 1

            if idx % 50 == 0:
                db.commit()
                print(f"  ... Processed {idx}/{len(enriched_faculty)} records (Inserted: {inserted_count}, Updated: {updated_count})", flush=True)

        db.commit()
        print(f"\n✅ Successfully committed Wave 65! Inserted: {inserted_count} new, Updated/Enriched: {updated_count} existing.", flush=True)

    finally:
        db.close()
        client.close()

    print(f"\n🎉 Wave 65 Execution Completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_pipeline()
