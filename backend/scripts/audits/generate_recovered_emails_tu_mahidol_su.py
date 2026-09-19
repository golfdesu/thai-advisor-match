"""Harvest authentic official university emails for Thammasat, Mahidol, and Silpakorn universities.

Target Clusters:
1. Silpakorn Engineering - Food Technology (foodtech.su.ac.th)
2. Silpakorn Engineering - Materials Science (matse.su.ac.th)
3. Silpakorn Engineering - Electrical Engineering (ee-eng.su.ac.th)
4. Silpakorn Engineering - Industrial Engineering (sites.google.com/site/iesilpakorn)
5. Silpakorn Faculty of Arts (arts.su.ac.th)
6. Mahidol College of Music (www.music.mahidol.ac.th)
7. Mahidol Faculty of Science (science.mahidol.ac.th/expertise/)
8. Thammasat Faculty of Law (www.law.tu.ac.th)
9. Thammasat Faculty of Pharmacy (pharm.tu.ac.th)
10. Thammasat Faculty of Nursing (nurse.tu.ac.th)

Section 9 Quality Invariants & PDPA:
- Reject freemails (@gmail.com, @hotmail.com, @yahoo.com, @outlook.com, etc.)
- Reject generic departmental inboxes (e.g. info@, saraban@, contact@, foodtech@su.ac.th, tls@tu.ac.th, fac-en@silpakorn.edu)
- ONLY official academic emails (@su.ac.th, @silpakorn.edu, @mahidol.ac.th, @mahidol.edu, @tu.ac.th, @nurse.tu.ac.th, etc.)
- Zero personal telephone numbers collected
- Unresolvable faculty remain SQL NULL rather than fabricated
"""
from __future__ import annotations

import json
import re
import string
import sys
import threading
import urllib.parse
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from sqlalchemy import or_
from sqlalchemy.orm import defer

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

OUTPUT_FILE = BACKEND_DIR / "data" / "agent_states" / "recovered_emails_tu_mahidol_su.json"

REJECT_FREEMAILS = {
    "gmail.com",
    "hotmail.com",
    "yahoo.com",
    "yahoo.co.th",
    "live.com",
    "outlook.com",
    "icloud.com",
}

REJECT_GENERIC = {
    "foodtech@su.ac.th",
    "fac-en@silpakorn.edu",
    "tls@tu.ac.th",
    "contact@law.tu.ac.th",
    "info@music.mahidol.ac.th",
    "contact@tbs.tu.ac.th",
    "nurse@tu.ac.th",
    "pharm@tu.ac.th",
    "webmaster@tu.ac.th",
    "admin@tu.ac.th",
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
        "ศ.เกียรติคุณ ดร.ภก.", "ศ.เกียรติคุณ ดร.", "ศ.เกียรติคุณ พญ.", "ศ.เกียรติคุณ นพ.",
        "ศ.เกียรติคุณ", "ผู้ช่วยศาสตราจารย์ ดร.", "รองศาสตราจารย์ ดร.", "ศาสตราจารย์ ดร.",
        "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์",
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
        "Prof. Emeritus Dr.", "Prof. Dr.", "Assoc. Prof. Dr.", "Asst. Prof. Dr.",
        "Prof.", "Assoc. Prof.", "Asst. Prof.", "Dr.", "Mr.", "Mrs.", "Ms.", "Instructor"
    ]:
        cleaned = re.sub(rf"^{re.escape(prefix)}\s*", "", cleaned, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip()


def main() -> None:
    db = SessionLocal()
    try:
        target_unis = ["มหาวิทยาลัยศิลปากร", "มหาวิทยาลัยมหิดล", "มหาวิทยาลัยธรรมศาสตร์"]
        missing_db = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th.in_(target_unis),
                or_(FacultyDB.email.is_(None), FacultyDB.email == "")
            )
            .options(defer(FacultyDB.embedding))
            .all()
        )
        print(f"Total target faculties in DB with NULL/empty email: {len(missing_db)}", flush=True)

        recovered: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        lock = threading.Lock()

        def add_recovery(f_obj: FacultyDB, email_val: str, source_val: str, cluster_name: str) -> bool:
            fid = f_obj.id
            with lock:
                if fid in seen_ids:
                    return False
                em = urllib.parse.unquote(email_val).strip().lower()
                em = re.sub(r"\s+", "", em)
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
                    "email": em,
                    "source": source_val,
                    "cluster": cluster_name
                })
                print(f"   [+] MATCHED: {f_obj.full_name_th} -> {em} ({cluster_name})", flush=True)
                return True

        # =========================================================================
        # 1. Silpakorn Engineering - Food Technology (foodtech.su.ac.th)
        # =========================================================================
        print("\n--- 1. Silpakorn Engineering - Food Tech ---", flush=True)
        su_food_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยศิลปากร" and "อาหาร" in (f.department_th or "")
        ]
        print(f"Candidates in DB: {len(su_food_candidates)}", flush=True)
        try:
            r = requests.get("https://foodtech.su.ac.th/Faculty.aspx", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            people_links = []
            for a in soup.find_all("a", href=True):
                h = a["href"]
                m = re.search(r"PeopleID=(\d+)", h)
                if m:
                    people_links.append((m.group(1), a.get_text(strip=True)))

            for pid, raw_name in people_links:
                p_url = f"https://foodtech.su.ac.th/Teacher.aspx?PeopleID={pid}"
                pr = requests.get(p_url, headers=HEADERS, verify=False, timeout=8)
                psoup = BeautifulSoup(pr.text, "html.parser")
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@su\.ac\.th", psoup.get_text())
                valid_emails = [e for e in emails if e.lower() not in REJECT_GENERIC]
                if not valid_emails:
                    continue
                email = valid_emails[0]
                clean_web = clean_thai_name(raw_name)

                for f in su_food_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                        add_recovery(f, email, p_url, "Silpakorn Engineering - Food Tech")
                        break
        except Exception as e:
            print(f"Error in Food Tech: {e}", flush=True)

        # =========================================================================
        # 2. Silpakorn Engineering - Materials Science (matse.su.ac.th)
        # =========================================================================
        print("\n--- 2. Silpakorn Engineering - Materials Science ---", flush=True)
        su_matse_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยศิลปากร" and ("วัสดุ" in (f.department_th or "") or "ฟิสิกส์" in (f.department_th or ""))
        ]
        print(f"Candidates in DB: {len(su_matse_candidates)}", flush=True)
        try:
            r = requests.get("https://matse.su.ac.th/matse-teams/", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            profile_links = [
                a["href"] for a in soup.find_all("a", href=True)
                if "matse.su.ac.th/index.php/" in a["href"] and "matse-officers" not in a["href"] and "guest" not in a["href"] and "supporting" not in a["href"]
            ]
            for p_url in set(profile_links):
                pr = requests.get(p_url, headers=HEADERS, verify=False, timeout=8)
                psoup = BeautifulSoup(pr.text, "html.parser")
                text = psoup.get_text()
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@su\.ac\.th", text)
                valid_emails = [e for e in emails if e.lower() not in REJECT_GENERIC]
                if not valid_emails:
                    continue
                email = valid_emails[0]

                h1_or_h2 = psoup.find(["h1", "h2", "h3"])
                raw_title = h1_or_h2.get_text(strip=True) if h1_or_h2 else ""
                clean_en_web = clean_english_name(raw_title)

                # Look for Thai name in the page
                thai_name_match = re.findall(r"(?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.)\s*[ก-๙]+\s+[ก-๙]+", text)
                clean_th_web = clean_thai_name(thai_name_match[0]) if thai_name_match else ""

                for f in su_matse_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    matched = False
                    if clean_th_web and (clean_th_web in clean_db or clean_db in clean_th_web or fuzz.ratio(clean_th_web, clean_db) >= 80.0):
                        matched = True
                    if not matched and clean_en_web and f.id:
                        # check last name in slug/id
                        last_part = f.id.split("_")[-2] if len(f.id.split("_")) >= 3 else ""
                        if last_part and len(last_part) >= 4 and last_part.lower() in clean_en_web.lower():
                            matched = True
                    if matched:
                        add_recovery(f, email, p_url, "Silpakorn Engineering - Materials Science")
                        break
        except Exception as e:
            print(f"Error in MatSE: {e}", flush=True)

        # =========================================================================
        # 3. Silpakorn Engineering - Electrical Engineering (ee-eng.su.ac.th)
        # =========================================================================
        print("\n--- 3. Silpakorn Engineering - Electrical Engineering ---", flush=True)
        su_ee_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยศิลปากร" and "ไฟฟ้า" in (f.department_th or "")
        ]
        print(f"Candidates in DB: {len(su_ee_candidates)}", flush=True)
        try:
            r = requests.get("https://ee-eng.su.ac.th/Staff.aspx?Type=Lecturer", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                raw_text = a.get_text(" ", strip=True)
                m_email = re.search(r"[a-zA-Z0-9._%+-]+@su\.ac\.th", raw_text)
                if not m_email:
                    continue
                email = m_email.group(0)
                name_part = raw_text.split("email:")[0].split("หัวหน้า")[0].split("รองหัวหน้า")[0].split("ประธาน")[0].split("อาจารย์ประจำ")[0].strip()
                clean_web = clean_thai_name(name_part)

                for f in su_ee_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                        add_recovery(f, email, "https://ee-eng.su.ac.th/Staff.aspx?Type=Lecturer", "Silpakorn Engineering - Electrical")
                        break
        except Exception as e:
            print(f"Error in EE: {e}", flush=True)

        # =========================================================================
        # 4. Silpakorn Engineering - Industrial Engineering (sites.google.com/site/iesilpakorn)
        # =========================================================================
        print("\n--- 4. Silpakorn Engineering - Industrial Engineering ---", flush=True)
        su_ie_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยศิลปากร" and "อุตสาหการ" in (f.department_th or "")
        ]
        print(f"Candidates in DB: {len(su_ie_candidates)}", flush=True)
        try:
            r = requests.get("https://sites.google.com/site/iesilpakorn/staff", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for div in soup.find_all(["div", "tr", "td", "p"]):
                t = div.get_text(" ", strip=True)
                m_email = re.findall(r"[a-zA-Z0-9._%+-]+@su\.ac\.th", t)
                if not m_email:
                    continue
                email = m_email[0]
                # extract name before ตำแหน่ง or E-Mail
                name_match = re.findall(r"(?:ผศ\.ดร\.|รศ\.ดร\.|อาจารย์|อ\.ดร\.|ผศ\.|รศ\.|สุขุม)\s*[ก-๙]+(?:\s+[ก-๙]+)?", t)
                if not name_match:
                    continue
                clean_web = clean_thai_name(name_match[0])

                for f in su_ie_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                        add_recovery(f, email, "https://sites.google.com/site/iesilpakorn/staff", "Silpakorn Engineering - Industrial")
                        break
        except Exception as e:
            print(f"Error in IE: {e}", flush=True)

        # =========================================================================
        # 5. Silpakorn Faculty of Arts (arts.su.ac.th)
        # =========================================================================
        print("\n--- 5. Silpakorn Faculty of Arts ---", flush=True)
        su_arts_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยศิลปากร" and "อักษรศาสตร์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(su_arts_candidates)}", flush=True)
        try:
            r = requests.get("https://arts.su.ac.th/?page_id=1757", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                h = a["href"]
                raw_name = a.get_text(strip=True)
                if "page_id=" in h and len(raw_name) > 3:
                    pr = requests.get(h, headers=HEADERS, verify=False, timeout=8)
                    psoup = BeautifulSoup(pr.text, "html.parser")
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9.-]+\.)?su\.ac\.th", psoup.get_text())
                    valid_emails = [e for e in emails if e.lower() not in REJECT_GENERIC]
                    if not valid_emails:
                        continue
                    email = valid_emails[0]
                    clean_web = clean_thai_name(raw_name)

                    for f in su_arts_candidates:
                        if f.id in seen_ids:
                            continue
                        clean_db = clean_thai_name(f.full_name_th or "")
                        if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                            add_recovery(f, email, h, "Silpakorn Faculty of Arts")
                            break
        except Exception as e:
            print(f"Error in Arts: {e}", flush=True)

        # =========================================================================
        # 6. Mahidol College of Music (www.music.mahidol.ac.th)
        # =========================================================================
        print("\n--- 6. Mahidol College of Music ---", flush=True)
        mu_music_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยมหิดล" and "ดุริยางคศิลป์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(mu_music_candidates)}", flush=True)
        try:
            r = requests.get("https://www.music.mahidol.ac.th/faculty/", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            profiles = list(set([a["href"] for a in soup.find_all("a", href=True) if "/people/" in a["href"]]))
            print(f"Fetched {len(profiles)} profile URLs from College of Music", flush=True)

            def fetch_music_profile(u: str):
                try:
                    pr = requests.get(u, headers=HEADERS, verify=False, timeout=8)
                    psoup = BeautifulSoup(pr.text, "html.parser")
                    text = psoup.get_text()
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.(?:ac\.th|edu)", text)
                    h1 = psoup.find("h1")
                    title = h1.get_text(strip=True) if h1 else ""
                    return {"url": u, "title": title, "emails": list(set(emails))}
                except Exception:
                    return None

            with ThreadPoolExecutor(max_workers=10) as ex:
                music_results = [res for res in ex.map(fetch_music_profile, profiles) if res and res.get("emails")]

            print(f"Profiles with official emails: {len(music_results)}", flush=True)
            for m_item in music_results:
                clean_en_web = clean_english_name(m_item["title"])
                p_slug = m_item["url"].strip("/").split("/")[-1].lower()
                valid_emails = [e for e in m_item["emails"] if e.lower() not in REJECT_GENERIC]
                if not valid_emails:
                    continue
                email = valid_emails[0]

                for f in mu_music_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db_th = clean_thai_name(f.full_name_th or "")
                    matched = False

                    # Check English name slug in ID or transliteration
                    f_id_slug = f.id.lower()
                    # e.g. mahidoluni_collegeofm_reid_014
                    slug_parts = f_id_slug.split("_")
                    if len(slug_parts) >= 3:
                        donor_slug = slug_parts[-2]
                        if len(donor_slug) >= 3 and donor_slug in p_slug:
                            matched = True

                    # Direct slug match
                    if not matched and clean_en_web:
                        en_words = [w.lower() for w in clean_en_web.split() if len(w) >= 3]
                        if any(w in f_id_slug for w in en_words):
                            matched = True

                    # Direct Thai name match if full_name_th has English
                    if not matched and re.search(r"[a-zA-Z]", clean_db_th):
                        if fuzz.token_sort_ratio(clean_en_web.lower(), clean_db_th.lower()) >= 80.0:
                            matched = True

                    if matched:
                        add_recovery(f, email, m_item["url"], "Mahidol College of Music")
                        break
        except Exception as e:
            print(f"Error in Music: {e}", flush=True)

        # =========================================================================
        # 7. Mahidol Faculty of Science (science.mahidol.ac.th/expertise/)
        # =========================================================================
        print("\n--- 7. Mahidol Faculty of Science ---", flush=True)
        mu_sci_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยมหิดล" and "วิทยาศาสตร์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(mu_sci_candidates)}", flush=True)
        try:
            # Collect all researchers from alfabet.php?q=a..z
            musc_items = []
            for char in string.ascii_lowercase:
                url_letter = f"https://science.mahidol.ac.th/expertise/alfabet.php?q={char}"
                try:
                    r = requests.get(url_letter, headers=HEADERS, verify=False, timeout=6)
                    soup = BeautifulSoup(r.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        h = a["href"]
                        if "search.php?q=" in h:
                            q_name = h.split("search.php?q=")[-1].strip()
                            t_title = a.get_text(strip=True)
                            musc_items.append((t_title, q_name))
                except Exception:
                    pass

            print(f"Found {len(musc_items)} researchers in MUSC index", flush=True)

            def fetch_musc_email(item):
                t_title, q_name = item
                search_url = f"https://science.mahidol.ac.th/expertise/search.php?q={urllib.parse.quote(q_name)}"
                try:
                    pr = requests.get(search_url, headers=HEADERS, verify=False, timeout=8)
                    psoup = BeautifulSoup(pr.text, "html.parser")
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@mahidol\.(?:ac\.th|edu)", psoup.get_text())
                    valid = [e for e in emails if e.lower() not in REJECT_GENERIC]
                    if valid:
                        return {"title": t_title, "q_name": q_name, "email": valid[0], "url": search_url}
                except Exception:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=10) as ex:
                musc_results = [res for res in ex.map(fetch_musc_email, musc_items) if res]

            print(f"Fetched {len(musc_results)} MUSC researchers with valid email", flush=True)
            for m_item in musc_results:
                clean_en_web = clean_english_name(m_item["title"]).split(",")[0].strip()
                email = m_item["email"]

                for f in mu_sci_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db_th = clean_thai_name(f.full_name_th or "")
                    matched = False

                    # Check ID slug match
                    f_id_slug = f.id.lower()
                    slug_parts = f_id_slug.split("_")
                    if len(slug_parts) >= 3:
                        donor_slug = slug_parts[-2]
                        if len(donor_slug) >= 4 and donor_slug in clean_en_web.lower():
                            matched = True

                    # Check transliteration or English words
                    if not matched and clean_en_web:
                        for w in clean_en_web.split():
                            if len(w) >= 4 and w.lower() in f_id_slug:
                                matched = True
                                break

                    # Transliteration or Thai-to-English phonetic matches
                    # e.g., Jitladda Sakdapipanich -> จิตลัดดา ศักดิ์ดาพิพานิช
                    # Siwaporn Meejoo Smith -> ศิวพร มีจู สมิธ
                    # Vichai Reutrakul -> วิชัย ริ้วตระกูล
                    # Michael Allen -> ไมเคิล แอนโทนี่ เอเลน
                    name_map = {
                        "jitladda": "จิตลัดดา",
                        "sakdapipanich": "ศักดิ์ดาพิพานิช",
                        "siwaporn": "ศิวพร",
                        "meejoo": "มีจู",
                        "vichai": "วิชัย",
                        "reutrakul": "ริ้วตระกูล",
                        "michael": "ไมเคิล",
                        "allen": "เอเลน",
                        "chaiwoot": "ชัยวุฒิ",
                        "boonyasiriwat": "บุญญศิริวัฒน์",
                        "amornrat": "อมรรัตน์",
                        "naranuntarat": "นรานันทรัตน์",
                        "pornpan": "พรพรรณ",
                        "matangkasombut": "มาตังคสมบัติ",
                    }
                    if not matched:
                        for en_k, th_v in name_map.items():
                            if en_k in clean_en_web.lower() and th_v in clean_db_th:
                                matched = True
                                break

                    if matched:
                        add_recovery(f, email, m_item["url"], "Mahidol Faculty of Science")
                        break
        except Exception as e:
            print(f"Error in MUSC: {e}", flush=True)

        # =========================================================================
        # 8. Thammasat Faculty of Law (www.law.tu.ac.th)
        # =========================================================================
        print("\n--- 8. Thammasat Faculty of Law ---", flush=True)
        tu_law_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยธรรมศาสตร์" and "นิติศาสตร์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(tu_law_candidates)}", flush=True)
        try:
            r = requests.get("https://www.law.tu.ac.th/about/staff/professor/", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            teacher_links = soup.find_all("a", href=re.compile(r"/teacher/"))
            for a in teacher_links:
                curr = a
                box_email = None
                box_text = ""
                for _ in range(5):
                    if curr.parent:
                        curr = curr.parent
                        text = curr.get_text(" ", strip=True)
                        m = re.findall(r"[a-zA-Z0-9._%+-]+@tu\.ac\.th", text)
                        valid_m = [e for e in m if e.lower() not in REJECT_GENERIC]
                        if valid_m:
                            box_email = valid_m[0]
                            box_text = text
                            break
                if not box_email:
                    continue

                # extract Thai name
                th_match = re.findall(r"(?:ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อาจารย์ ดร\.|อาจารย์|ผศ\.|รศ\.|ศ\.)\s*[ก-๙]+(?:\s+[ก-๙]+)?", box_text)
                clean_web = clean_thai_name(th_match[0]) if th_match else ""

                for f in tu_law_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    matched = False
                    if clean_web and (clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0):
                        matched = True

                    # Slug match
                    if not matched and a.get("href"):
                        t_slug = a["href"].split("/")[-1].replace("-", "_").lower()
                        if t_slug and (t_slug in f.id.lower() or f.id.lower() in t_slug):
                            matched = True

                    if matched:
                        add_recovery(f, box_email, f"https://www.law.tu.ac.th{a['href']}", "Thammasat Faculty of Law")
                        break
        except Exception as e:
            print(f"Error in TU Law: {e}", flush=True)

        # =========================================================================
        # 9. Thammasat Faculty of Pharmacy (pharm.tu.ac.th)
        # =========================================================================
        print("\n--- 9. Thammasat Faculty of Pharmacy ---", flush=True)
        tu_pharm_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยธรรมศาสตร์" and "เภสัชศาสตร์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(tu_pharm_candidates)}", flush=True)
        try:
            r = requests.get("https://pharm.tu.ac.th/academicstaff", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for div in soup.find_all(["div", "tr"]):
                text = div.get_text(" ", strip=True)
                m = re.findall(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9.-]+\.)?(?:tu\.ac\.th|mahidol\.ac\.th|chula\.ac\.th)", text)
                valid = [e for e in m if e.lower() not in REJECT_GENERIC and e.split("@")[-1] not in REJECT_FREEMAILS]
                if not valid:
                    continue
                email = valid[0]

                th_match = re.findall(r"(?:ศ\.เกียรติคุณ ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.ภก\.|ผศ\.ภก\.|อ\.ดร\.ภญ\.|อ\.ดร\.ภก\.|อ\.ภญ\.|อ\.ภก\.|รศ\.ภญ\.)\s*[ก-๙]+(?:\s+[ก-๙]+)?", text)
                if not th_match:
                    continue
                clean_web = clean_thai_name(th_match[0])

                for f in tu_pharm_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                        add_recovery(f, email, "https://pharm.tu.ac.th/academicstaff", "Thammasat Faculty of Pharmacy")
                        break
        except Exception as e:
            print(f"Error in TU Pharm: {e}", flush=True)

        # =========================================================================
        # 10. Thammasat Faculty of Nursing (nurse.tu.ac.th)
        # =========================================================================
        print("\n--- 10. Thammasat Faculty of Nursing ---", flush=True)
        tu_nurse_candidates = [
            f for f in missing_db
            if f.university_th == "มหาวิทยาลัยธรรมศาสตร์" and "พยาบาลศาสตร์" in (f.faculty_th or "")
        ]
        print(f"Candidates in DB: {len(tu_nurse_candidates)}", flush=True)
        try:
            r = requests.get("https://nurse.tu.ac.th/professor", headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all(["div", "article"], class_=re.compile(r"col|card|team|member|box", re.I)):
                text = card.get_text(" ", strip=True)
                m = re.findall(r"[a-zA-Z0-9._%+-]+@nurse\.tu\.ac\.th", text)
                if not m:
                    continue
                email = m[0]
                th_match = re.findall(r"(?:รศ\.ดร\.|ผศ\.ดร\.|อาจารย์ ดร\.|อาจารย์|ผศ\.|รศ\.|ศ\.)\s*[ก-๙]+(?:\s+[ก-๙]+)?", text)
                if not th_match:
                    continue
                clean_web = clean_thai_name(th_match[0])

                for f in tu_nurse_candidates:
                    if f.id in seen_ids:
                        continue
                    clean_db = clean_thai_name(f.full_name_th or "")
                    if clean_web in clean_db or clean_db in clean_web or fuzz.ratio(clean_web, clean_db) >= 80.0:
                        add_recovery(f, email, "https://nurse.tu.ac.th/professor", "Thammasat Faculty of Nursing")
                        break
        except Exception as e:
            print(f"Error in TU Nurse: {e}", flush=True)

        # Summary and write state file
        print("\n=======================================================", flush=True)
        print(f"RECOVERY SUMMARY: Total authentic emails recovered: {len(recovered)}", flush=True)
        by_cluster: dict[str, int] = {}
        for r_item in recovered:
            by_cluster[str(r_item["cluster"])] = by_cluster.get(str(r_item["cluster"]), 0) + 1
        for c_name, c_cnt in by_cluster.items():
            print(f" - {c_name}: {c_cnt}")

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
            json.dump(recovered, f_out, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(recovered)} records to {OUTPUT_FILE}", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    main()
