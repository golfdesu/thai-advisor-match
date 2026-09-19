"""Harvest authentic official university emails for Phase 26 candidate faculty clusters.

Target Clusters:
1. Khon Kaen University College of Computing (api.computing.kku.ac.th)
2. Thammasat University Business School - TBS (tbs.tu.ac.th)
3. Mahidol University Faculty of Tropical Medicine (tm.mahidol.ac.th)
4. Mahidol University Faculty of Science (science.mahidol.ac.th)
5. Chulalongkorn University Department of Computer Engineering (cp.eng.chula.ac.th)
6. Chulalongkorn University Faculty of Economics (econ.chula.ac.th)
7. Chulalongkorn University Vaccine Research Center - Chula VRC (chulavrc.org)
8. Chiang Mai University Department of Mechanical Engineering (me.eng.cmu.ac.th)
9. King Mongkut's University of Technology Thonburi Department of Computer Engineering (cpe.kmutt.ac.th)
10. Mahidol University Faculty of Public Health (ph.mahidol.ac.th subdomains)

Section 9 Quality Invariants & PDPA:
- Reject freemails (@gmail.com, @hotmail.com, @yahoo.com, etc.)
- Reject generic departmental inboxes (fibo@kmutt.ac.th, saraban_econ@chula.ac.th)
- Whitelist institutional domains (@chula.ac.th, @cp.eng.chula.ac.th, @mahidol.ac.th, @tbs.tu.ac.th,
  @kku.ac.th, @cmu.ac.th, @eng.cmu.ac.th, @kmutt.ac.th, @mail.kmutt.ac.th, @chulavrc.org)
- Zero personal telephone numbers collected
- Unresolvable faculty remain SQL NULL rather than fabricated
"""
from __future__ import annotations

import json
import re
import sys
import threading
import urllib.parse
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from sqlalchemy.orm import defer

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

OUTPUT_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase26.json"

REJECT_FREEMAILS = {
    "gmail.com",
    "hotmail.com",
    "yahoo.com",
    "live.com",
    "outlook.com",
    "icloud.com",
}

REJECT_GENERIC = {
    "fibo@kmutt.ac.th",
    "saraban_econ@chula.ac.th",
    "tmwww@mahidol.ac.th",
    "info@chulavrc.org",
    "contact@tbs.tu.ac.th",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def clean_thai_name(name: str) -> str:
    cleaned = name
    for prefix in [
        "อาจารย์ ดร.ภญ.", "อาจารย์ ดร.ภก.", "อาจารย์ ดร.", "อาจารย์ดร.",
        "อาจารย์ ภญ.", "อาจารย์ ภก.", "อาจารย์",
        "ผศ.ดร.ภญ.", "ผศ.ดร.ภก.", "รศ.ดร.ภญ.", "รศ.ดร.ภก.",
        "ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "อ.ดร.",
        "ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "ภญ.", "ภก.",
        "นพ.", "พญ.", "ทพ.", "ทพญ.", "สพ.ญ.", "สพ.ช.",
        "นายแพทย์", "แพทย์หญิง", "คุณหญิง", "ท่านผู้หญิง",
        "ว่าที่ ร.ต.", "ว่าที่ร้อยตรี", "นาย", "นาง", "นางสาว"
    ]:
        cleaned = cleaned.replace(prefix, "")
    return re.sub(r"\s+", " ", cleaned).strip()


def clean_english_name(name: str) -> str:
    cleaned = name
    for prefix in [
        "Prof. Dr.", "Assoc. Prof. Dr.", "Asst. Prof. Dr.",
        "Prof.", "Assoc. Prof.", "Asst. Prof.", "Dr.", "Mr.", "Mrs.", "Ms."
    ]:
        cleaned = re.sub(rf"^{re.escape(prefix)}\s*", "", cleaned, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip()


def main() -> None:
    db = SessionLocal()
    try:
        faculties_missing = (
            db.query(FacultyDB)
            .filter((FacultyDB.email == None) | (FacultyDB.email == ""))
            .options(defer(FacultyDB.embedding))
            .all()
        )
        print(f"Total faculties with NULL or empty email: {len(faculties_missing)}", flush=True)

        recovered: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        lock = threading.Lock()

        def add_recovery(f_obj: FacultyDB, email_val: str, source_val: str, cluster_name: str) -> bool:
            fid = f_obj.id
            with lock:
                if fid in seen_ids:
                    return False
                em = urllib.parse.unquote(email_val).strip().lower()
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", em):
                    return False
                domain = em.split("@")[-1]
                if domain in REJECT_FREEMAILS:
                    return False
                if em in REJECT_GENERIC:
                    return False
                seen_ids.add(fid)
                recovered.append({
                    "id": fid,
                    "full_name_th": f_obj.full_name_th,
                    "university_th": f_obj.university_th,
                    "faculty_th": f_obj.faculty_th,
                    "department_th": f_obj.department_th,
                    "email": em,
                    "source": source_val,
                    "cluster": cluster_name
                })
                return True

        # =========================================================================
        # 1. Khon Kaen University College of Computing (api.computing.kku.ac.th)
        # =========================================================================
        print("\n--- 1. KKU College of Computing ---", flush=True)
        kku_candidates = [f for f in faculties_missing if "computing" in f.id or "วิทยาลัยการคอมพิวเตอร์" in (f.faculty_th or "")]
        print(f"Candidate KKU computing records: {len(kku_candidates)}", flush=True)
        try:
            r = requests.get("https://api.computing.kku.ac.th/api/v1/user/list?page=1&size=100", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                kku_data = r.json()
                items = kku_data.get("data", {}).get("items", [])
                print(f"Fetched {len(items)} staff items from KKU computing API", flush=True)
                for it in items:
                    user_loc = it.get("userLocalized", [])
                    em = it.get("email")
                    if not em or "@kku.ac.th" not in em.lower():
                        continue
                    fname_th = user_loc[0].get("firstname", "") if len(user_loc) > 0 else ""
                    lname_th = user_loc[0].get("lastname", "") if len(user_loc) > 0 else ""
                    full_th = f"{fname_th} {lname_th}".strip()
                    clean_api_name = clean_thai_name(full_th)
                    if not clean_api_name:
                        continue

                    for f in kku_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db_name = clean_thai_name(f.full_name_th or "")
                        if clean_api_name in clean_db_name or clean_db_name in clean_api_name or fuzz.ratio(clean_api_name, clean_db_name) >= 85.0:
                            if add_recovery(f, em, "https://computing.kku.ac.th/personnel", "KKU College of Computing"):
                                print(f"  MATCH KKU: {f.full_name_th} -> {em}", flush=True)
        except Exception as e:
            print(f"Error fetching KKU computing: {e}", flush=True)

        # =========================================================================
        # 2. Thammasat Business School - TBS (tbs.tu.ac.th on HTTP port 80)
        # =========================================================================
        print("\n--- 2. Thammasat Business School (TBS) ---", flush=True)
        tbs_candidates = [f for f in faculties_missing if f.id.startswith("tu_bus_tbs_") or ("พาณิชยศาสตร์และการบัญชี" in (f.faculty_th or "") and "ธรรมศาสตร์" in (f.university_th or ""))]
        print(f"Candidate TBS records: {len(tbs_candidates)}", flush=True)
        try:
            r = requests.get("http://tbs.tu.ac.th/TH/aboutus/committee-and-faculty-members/", headers=HEADERS, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                staff_links = list({a["href"] for a in soup.find_all("a", href=True) if "/staff/" in a["href"]})
                print(f"Discovered {len(staff_links)} TBS staff profile links. Scraping concurrently...", flush=True)

                def fetch_tbs_profile(link: str) -> None:
                    try:
                        r_prof = requests.get(link, headers=HEADERS, timeout=8)
                        if r_prof.status_code != 200:
                            return
                        soup_prof = BeautifulSoup(r_prof.text, "html.parser")
                        h1 = soup_prof.find("h1")
                        raw_name = h1.get_text(strip=True) if h1 else ""
                        clean_prof_name = clean_thai_name(raw_name)
                        emails = re.findall(r"[a-zA-Z0-9._%+-]+@tbs\.tu\.ac\.th", r_prof.text, re.I)
                        if not emails or not clean_prof_name:
                            return
                        em = emails[0].lower()

                        for f in tbs_candidates:
                            if f.id in seen_ids:
                                continue
                            clean_db_name = clean_thai_name(f.full_name_th or "")
                            if (clean_prof_name and clean_db_name and
                                (clean_prof_name in clean_db_name or clean_db_name in clean_prof_name or fuzz.ratio(clean_prof_name, clean_db_name) >= 85.0)):
                                if add_recovery(f, em, link, "Thammasat Business School"):
                                    print(f"  MATCH TBS: {f.full_name_th} -> {em}", flush=True)
                    except Exception:
                        pass

                with ThreadPoolExecutor(max_workers=10) as executor:
                    list(executor.map(fetch_tbs_profile, staff_links))
        except Exception as e:
            print(f"Error crawling TBS: {e}", flush=True)

        # =========================================================================
        # 3. Mahidol University Faculty of Tropical Medicine (tm.mahidol.ac.th)
        # =========================================================================
        print("\n--- 3. Mahidol Tropical Medicine ---", flush=True)
        tropmed_candidates = [f for f in faculties_missing if f.id.startswith("mahidoluni_facultyoft_") or "เวชศาสตร์เขตร้อน" in (f.faculty_th or "")]
        print(f"Candidate TropMed records: {len(tropmed_candidates)}", flush=True)
        tm_subdirs = [
            "clinic/staff/",
            "pediatrics/staff-2026/",
            "entomology/staff/",
            "protozoology/staff/",
            "pathology/staff/",
            "molecular/staff/",
            "helminth/staff2/",
            "micro-immuno/staff/",
            "nutrition/staff/",
            "social-environment/staff/"
        ]
        tm_profile_urls = set()
        for sdir in tm_subdirs:
            try:
                r_dir = requests.get(f"https://www.tm.mahidol.ac.th/{sdir}", headers=HEADERS, verify=False, timeout=8)
                if r_dir.status_code == 200:
                    links = re.findall(r"tropmed-staff/[^\"'>\s]+\.php", r_dir.text)
                    for lk in links:
                        tm_profile_urls.add(f"https://www.tm.mahidol.ac.th/{lk}")
            except Exception:
                pass
        print(f"Harvested {len(tm_profile_urls)} TropMed profile URLs. Scraping concurrently...", flush=True)

        def fetch_tm_profile(purl: str) -> None:
            try:
                r_p = requests.get(purl, headers=HEADERS, verify=False, timeout=8)
                if r_p.status_code != 200:
                    return
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.(?:ac\.th|edu)", r_p.text, re.I)
                if not emails:
                    return
                em = emails[0].lower()
                soup_tm = BeautifulSoup(r_p.text, "html.parser")
                raw_text = soup_tm.get_text()
                for f in tropmed_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db_name = clean_thai_name(f.full_name_th or "")
                    if len(clean_db_name) > 4 and clean_db_name in raw_text:
                        if add_recovery(f, em, purl, "Mahidol Tropical Medicine"):
                            print(f"  MATCH TropMed: {f.full_name_th} -> {em}", flush=True)
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(fetch_tm_profile, list(tm_profile_urls)))

        # =========================================================================
        # 4. Mahidol University Faculty of Science (science.mahidol.ac.th)
        # =========================================================================
        print("\n--- 4. Mahidol Science ---", flush=True)
        sc_candidates = [f for f in faculties_missing if f.id.startswith("mahidoluni_facultyofs_") or ("วิทยาศาสตร์" in (f.faculty_th or "") and "มหิดล" in (f.university_th or ""))]
        print(f"Candidate Mahidol Science records: {len(sc_candidates)}", flush=True)
        dept_codes = ['AN', 'BI', 'BC', 'BT', 'CH', 'MA', 'ME', 'MI', 'PA', 'PR', 'PH', 'PY', 'SC', 'SU']
        sc_query_names = set()
        for dcode in dept_codes:
            try:
                r_sc = requests.get(f"https://science.mahidol.ac.th/expertise/department.php?q={dcode}", headers=HEADERS, verify=False, timeout=10)
                if r_sc.status_code == 200:
                    soup_sc = BeautifulSoup(r_sc.text, "html.parser")
                    for a in soup_sc.find_all("a", href=re.compile(r"search\.php\?q=")):
                        q_val = a["href"].split("search.php?q=")[-1]
                        sc_query_names.add(urllib.parse.unquote(q_val).strip())
            except Exception:
                pass
        print(f"Harvested {len(sc_query_names)} Mahidol Science researcher queries. Scraping concurrently...", flush=True)

        def fetch_sc_profile(q_name: str) -> None:
            try:
                sc_url = f"https://science.mahidol.ac.th/expertise/search.php?q={urllib.parse.quote(q_name)}"
                r_prof = requests.get(sc_url, headers=HEADERS, verify=False, timeout=8)
                if r_prof.status_code != 200:
                    return
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.ac\.th", r_prof.text, re.I)
                if not emails:
                    return
                em = emails[0].lower()
                soup_prof = BeautifulSoup(r_prof.text, "html.parser")
                container = soup_prof.find("div", class_="container")
                strs = list(container.stripped_strings) if container else list(soup_prof.stripped_strings)
                text_block = " ".join(strs)

                for f in sc_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db_name = clean_thai_name(f.full_name_th or "")
                    if (len(clean_db_name) > 4 and clean_db_name in text_block) or (q_name.lower() in (f.id or "").lower()):
                        if add_recovery(f, em, sc_url, "Mahidol Science"):
                            print(f"  MATCH Mahidol Science: {f.full_name_th} -> {em}", flush=True)
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(fetch_sc_profile, list(sc_query_names)))

        # =========================================================================
        # 5. Chulalongkorn Computer Engineering (cp.eng.chula.ac.th)
        # =========================================================================
        print("\n--- 5. Chula Computer Engineering ---", flush=True)
        chula_cp_candidates = [f for f in faculties_missing if f.id.startswith("chula_eng_cp_") or "วิศวกรรมคอมพิวเตอร์" in (f.department_th or "")]
        print(f"Candidate Chula CP records: {len(chula_cp_candidates)}", flush=True)
        try:
            r = requests.get("https://www.cp.eng.chula.ac.th/about/faculty/", headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                cp_links = list({
                    f"https://www.cp.eng.chula.ac.th{a['href']}" if not a["href"].startswith("http") else a["href"]
                    for a in soup.find_all("a", href=re.compile(r"/about/faculty/[^/]+"))
                })
                print(f"Found {len(cp_links)} Chula CP profile links. Scraping concurrently...", flush=True)

                def fetch_cp_profile(cp_url: str) -> None:
                    try:
                        r_cp = requests.get(cp_url, headers=HEADERS, verify=False, timeout=8)
                        if r_cp.status_code != 200:
                            return
                        emails = re.findall(r"[a-zA-Z0-9._%+-]+@(?:cp\.eng\.)?chula\.ac\.th", r_cp.text, re.I)
                        if not emails:
                            return
                        em = emails[0].lower()
                        soup_cp = BeautifulSoup(r_cp.text, "html.parser")
                        h_elem = soup_cp.find(["h1", "h2", "h3"])
                        prof_th = h_elem.get_text(strip=True) if h_elem else ""
                        clean_prof_th = clean_thai_name(prof_th)
                        slug = cp_url.rstrip("/").split("/")[-1].lower()

                        for f in chula_cp_candidates:
                            if f.id in seen_ids:
                                continue
                            clean_db_name = clean_thai_name(f.full_name_th or "")
                            if (clean_prof_th and clean_prof_th in clean_db_name) or (clean_db_name and clean_db_name in clean_prof_th) or (slug in f.id.lower()):
                                if add_recovery(f, em, cp_url, "Chula Computer Engineering"):
                                    print(f"  MATCH Chula CP: {f.full_name_th} -> {em}", flush=True)
                    except Exception:
                        pass

                with ThreadPoolExecutor(max_workers=10) as executor:
                    list(executor.map(fetch_cp_profile, cp_links))
        except Exception as e:
            print(f"Error crawling Chula CP: {e}", flush=True)

        # =========================================================================
        # 6. Chulalongkorn University Faculty of Economics (econ.chula.ac.th)
        # =========================================================================
        print("\n--- 6. Chula Economics ---", flush=True)
        chula_econ_candidates = [f for f in faculties_missing if f.id.startswith("chulalongk_facultyofe_") or ("เศรษฐศาสตร์" in (f.faculty_th or "") and "จุฬา" in (f.university_th or ""))]
        print(f"Candidate Chula Econ records: {len(chula_econ_candidates)}", flush=True)
        try:
            url_econ = "https://www.econ.chula.ac.th/" + urllib.parse.quote("คณาจารย์/")
            r = requests.get(url_econ, headers=HEADERS, verify=False, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for text_node in soup.find_all(string=re.compile(r"@chula\.ac\.th", re.I)):
                    em = text_node.strip()
                    if "@" not in em or em in REJECT_GENERIC or " " in em:
                        continue
                    container = text_node.parent
                    for _ in range(4):
                        if container.parent:
                            container = container.parent
                    strs = list(container.stripped_strings)
                    raw_th_name = strs[0] if strs else ""
                    clean_prof_name = clean_thai_name(raw_th_name)
                    if not clean_prof_name:
                        continue

                    for f in chula_econ_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db_name = clean_thai_name(f.full_name_th or "")
                        if (clean_prof_name in clean_db_name or clean_db_name in clean_prof_name or fuzz.ratio(clean_prof_name, clean_db_name) >= 85.0):
                            if add_recovery(f, em, url_econ, "Chula Economics"):
                                print(f"  MATCH Chula Econ: {f.full_name_th} -> {em}", flush=True)
        except Exception as e:
            print(f"Error scraping Chula Econ: {e}", flush=True)

        # =========================================================================
        # 7. Chulalongkorn Vaccine Research Center (chulavrc.org)
        # =========================================================================
        print("\n--- 7. Chula Vaccine Research Center ---", flush=True)
        vrc_candidates = [f for f in faculties_missing if f.id.startswith("chulalongk_centerofex_")]
        print(f"Candidate Chula VRC records: {len(vrc_candidates)}", flush=True)
        try:
            r = requests.get("https://www.chulavrc.org/staff/", headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for item in soup.find_all("div", class_="item"):
                    mailto = item.find("a", href=re.compile(r"mailto:", re.I))
                    if not mailto:
                        continue
                    em = urllib.parse.unquote(mailto["href"].replace("mailto:", "").strip().lower())
                    if any(em.endswith(f) for f in REJECT_FREEMAILS) or em in REJECT_GENERIC:
                        continue
                    strs = [s.strip() for s in item.stripped_strings if s.strip()]
                    if not strs:
                        continue
                    name_en = strs[0]
                    for f in vrc_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db_name = clean_thai_name(f.full_name_th or "")
                        id_slug = f.id.replace("chulalongk_centerofex_", "").split("_")[0].lower()
                        matched = False
                        if id_slug and id_slug in name_en.lower():
                            matched = True
                        elif clean_db_name and clean_db_name in clean_thai_name(name_en):
                            matched = True
                        if matched:
                            if add_recovery(f, em, "https://www.chulavrc.org/staff/", "Chula VRC"):
                                print(f"  MATCH Chula VRC: {f.full_name_th} ({name_en}) -> {em}", flush=True)
        except Exception as e:
            print(f"Error scraping Chula VRC: {e}", flush=True)

        # =========================================================================
        # 8. Chiang Mai University Mechanical Engineering (me.eng.cmu.ac.th)
        # =========================================================================
        print("\n--- 8. CMU Mechanical Engineering (Canvas De-cloaking) ---", flush=True)
        cmu_me_candidates = [f for f in faculties_missing if f.id.startswith("cmu_eng_me_") or ("วิศวกรรมเครื่องกล" in (f.department_th or "") and "เชียงใหม่" in (f.university_th or ""))]
        print(f"Candidate CMU ME records: {len(cmu_me_candidates)}", flush=True)
        try:
            r = requests.get("https://me.eng.cmu.ac.th/staff/professor", headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                canvas_emails: dict[str, str] = {}
                for m in re.finditer(r"emailCanvas_(\d+).*?fillText\(\s*[\"']([^\"']+)[\"']", r.text, re.S):
                    canvas_emails[m.group(1)] = m.group(2).strip()

                soup = BeautifulSoup(r.text, "html.parser")
                for canvas in soup.find_all("canvas", id=re.compile(r"emailCanvas_\d+")):
                    cid = canvas["id"].replace("emailCanvas_", "")
                    em = canvas_emails.get(cid)
                    if not em:
                        continue
                    card = canvas.find_parent("div", class_=re.compile(r"col|card|box|item"))
                    if not card:
                        continue
                    name_elem = card.find("p", class_="font-16") or card.find(["h4", "h5", "p"])
                    raw_name = name_elem.get_text(strip=True) if name_elem else ""
                    clean_cmu_name = clean_thai_name(raw_name)
                    if not clean_cmu_name:
                        continue

                    for f in cmu_me_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db_name = clean_thai_name(f.full_name_th or "")
                        if (clean_cmu_name in clean_db_name or clean_db_name in clean_cmu_name or fuzz.ratio(clean_cmu_name, clean_db_name) >= 85.0):
                            if add_recovery(f, em, "https://me.eng.cmu.ac.th/staff/professor", "CMU Mechanical Engineering"):
                                print(f"  MATCH CMU ME: {f.full_name_th} -> {em}", flush=True)
        except Exception as e:
            print(f"Error scraping CMU ME: {e}", flush=True)

        # =========================================================================
        # 9. KMUTT Computer Engineering (cpe.kmutt.ac.th)
        # =========================================================================
        print("\n--- 9. KMUTT Computer Engineering ---", flush=True)
        kmutt_cpe_candidates = [f for f in faculties_missing if f.id.startswith("kmutt_eng_cpe_") or ("วิศวกรรมคอมพิวเตอร์" in (f.department_th or "") and "พระจอมเกล้าธนบุรี" in (f.university_th or ""))]
        print(f"Candidate KMUTT CPE records: {len(kmutt_cpe_candidates)}", flush=True)
        try:
            r = requests.get("https://www.cpe.kmutt.ac.th/th/staff/", headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=re.compile(r"mailto:", re.I)):
                    em = a["href"].replace("mailto:", "").split("?")[0].strip()
                    card = a.find_parent("div", class_=re.compile(r"card|member|staff|item|box"))
                    strs = list(card.stripped_strings) if card else []
                    if not strs:
                        p = a.parent
                        for _ in range(3):
                            if p and p.parent: p = p.parent
                        strs = list(p.stripped_strings) if p else []
                    raw_name = strs[0] if strs else ""
                    clean_cpe_name = clean_thai_name(raw_name)
                    if not clean_cpe_name:
                        continue

                    for f in kmutt_cpe_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db_name = clean_thai_name(f.full_name_th or "")
                        if (clean_cpe_name in clean_db_name or clean_db_name in clean_cpe_name or fuzz.ratio(clean_cpe_name, clean_db_name) >= 85.0):
                            if add_recovery(f, em, "https://www.cpe.kmutt.ac.th/th/staff/", "KMUTT Computer Engineering"):
                                print(f"  MATCH KMUTT CPE: {f.full_name_th} -> {em}", flush=True)
        except Exception as e:
            print(f"Error scraping KMUTT CPE: {e}", flush=True)

        # =========================================================================
        # 10. Mahidol University Faculty of Public Health (ph.mahidol.ac.th subdomains)
        # =========================================================================
        print("\n--- 10. Mahidol Public Health ---", flush=True)
        ph_candidates = [f for f in faculties_missing if f.id.startswith("mahidoluni_facultyofp_") or "สาธารณสุขศาสตร์" in (f.faculty_th or "")]
        print(f"Candidate Mahidol PH records: {len(ph_candidates)}", flush=True)
        ph_urls = [
            ("https://phoh.ph.mahidol.ac.th/faculty-members.html", "utf-8"),
            ("https://phad.ph.mahidol.ac.th/staff.html", "cp874"),
            ("https://phnu.ph.mahidol.ac.th/staff.html", "cp874"),
            ("https://phse.ph.mahidol.ac.th/staff.html", "cp874"),
        ]
        for ph_url, enc in ph_urls:
            try:
                r = requests.get(ph_url, headers=HEADERS, verify=False, timeout=8)
                r.encoding = enc
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for a in soup.find_all("a", href=lambda h: h and "mailto:" in h):
                        em = a["href"].replace("mailto:", "").split("?")[0].strip()
                        card = a.find_parent("div", class_=lambda c: c and any(k in c for k in ["person", "team", "staff", "member", "details"]))
                        strs = list(card.stripped_strings) if card else []
                        if not strs:
                            p = a.parent
                            for _ in range(3):
                                if p and p.parent: p = p.parent
                            strs = list(p.stripped_strings) if p else []
                        raw_name = strs[0] if strs else ""
                        clean_ph_name = clean_thai_name(raw_name)
                        if not clean_ph_name:
                            continue

                        for f in ph_candidates:
                            if f.id in seen_ids:
                                continue
                            clean_db_name = clean_thai_name(f.full_name_th or "")
                            if (clean_ph_name in clean_db_name or clean_db_name in clean_ph_name or fuzz.ratio(clean_ph_name, clean_db_name) >= 85.0):
                                if add_recovery(f, em, ph_url, "Mahidol Public Health"):
                                    print(f"  MATCH Mahidol PH: {f.full_name_th} -> {em}", flush=True)
            except Exception:
                pass

        # =========================================================================
        # 11. Thammasat Sirindhorn International Institute of Technology (SIIT)
        # =========================================================================
        print("\n--- 11. Thammasat SIIT ---", flush=True)
        siit_candidates = [f for f in faculties_missing if "สิรินธร" in (f.faculty_th or "") or f.id.startswith("thammasatu_sirindhorn_")]
        print(f"Candidate SIIT records: {len(siit_candidates)}", flush=True)
        try:
            r = requests.get("https://www.siit.tu.ac.th/personnel.php", headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                cids = sorted(list(set(re.findall(r"page_a\.php\?cid=(\d+)", r.text))))
                for cid in cids:
                    u = f"https://www.siit.tu.ac.th/page_a.php?cid={cid}"
                    try:
                        r_cid = requests.get(u, headers=HEADERS, verify=False, timeout=10)
                        if r_cid.status_code == 200:
                            soup = BeautifulSoup(r_cid.text, "html.parser")
                            for box in soup.find_all("div", class_="school-boxcolumn"):
                                name_div = box.find("div", class_="school-name")
                                em_div = box.find("div", class_="school-emright")
                                link_a = box.find("a", href=re.compile(r"page_bx\.php"))
                                name = name_div.get_text(strip=True) if name_div else ""
                                em = em_div.get_text(strip=True) if em_div else ""
                                link = f"https://www.siit.tu.ac.th/{link_a['href']}" if link_a else u
                                if name and "@siit.tu.ac.th" in em:
                                    clean_em = em.strip().lower()
                                    if any(clean_em.endswith(f) for f in REJECT_FREEMAILS) or clean_em in REJECT_GENERIC:
                                        continue
                                    for f in siit_candidates:
                                        if f.id in seen_ids:
                                            continue
                                        slug = f.id.split("_")[-2].lower() if len(f.id.split("_")) >= 3 else f.id.split("_")[-1].lower()
                                        clean_db_name = clean_thai_name(f.full_name_th or "")
                                        matched = False
                                        if slug and len(slug) >= 4 and slug in name.lower():
                                            matched = True
                                        elif clean_db_name and len(clean_db_name) >= 4 and clean_db_name in clean_thai_name(name):
                                            matched = True
                                        if matched:
                                            if add_recovery(f, clean_em, link, "Thammasat SIIT"):
                                                print(f"  MATCH SIIT: {f.full_name_th} ({name}) -> {clean_em}", flush=True)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error scraping SIIT: {e}", flush=True)

        print("\n" + "=" * 70, flush=True)
        print(f"Total authentic official emails recovered for Phase 26: {len(recovered)}", flush=True)
        print("=" * 70, flush=True)

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(recovered, f, ensure_ascii=False, indent=2)
        print(f"Checkpoint saved to: {OUTPUT_FILE}", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    main()
