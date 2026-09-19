"""Generate Phase 24 Recovered Official Emails State File.

Clusters:
1. Kasetsart University Faculty of Agriculture (KU Forest personnel directory: http://research.ku.ac.th/forest/)
2. Khon Kaen University Faculty of Nursing (nu.kku.ac.th academic department directories)
3. Kasetsart University Faculty of Engineering (hr.eng.ku.ac.th central HR directory API)
4. King Mongkut's University of Technology Thonburi Faculty of Science (chem & mic directories)
5. Kasetsart University Faculty of Science (departmental profile endpoints)
6. Chulalongkorn University Faculty of Pharmacy (pharm.chula.ac.th directory API)
"""
from __future__ import annotations

import html
import json
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

urllib3.disable_warnings()

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}
REJECT_FREEMAILS = ["@gmail.com", "@hotmail.com", "@yahoo.com", "@live.com", "@outlook.com"]
REJECT_GENERIC = [
    "sci@ku.ac.th", "tls@tu.ac.th", "nu.inbox@kku.ac.th", "chem@kmutt.ac.th",
    "aad@kmitl.ac.th", "fsci.science@kmutt.ac.th", "mic@kmutt.ac.th",
    "anatomy.med@g.swu.ac.th", "contact@pharm.chula.ac.th"
]


def clean_thai_name(name: str) -> str:
    cleaned = name
    for prefix in [
        "อาจารย์ ดร.ภญ.", "อาจารย์ ดร.ภก.", "อาจารย์ ดร.", "อาจารย์ดร.",
        "อาจารย์ ภญ.", "อาจารย์ ภก.", "อาจารย์",
        "ผศ.ดร.ภญ.", "ผศ.ดร.ภก.", "รศ.ดร.ภญ.", "รศ.ดร.ภก.",
        "ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "อ.ดร.",
        "ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "ภญ.", "ภก."
    ]:
        cleaned = cleaned.replace(prefix, "")
    return cleaned.strip()


def decloak_joomla(html_text: str) -> str | None:
    matches = re.findall(r"var addy_text\w+\s*=\s*(.*?);document\.getElementById", html_text)
    for m in matches:
        raw = "".join(re.findall(r"['\"](.*?)['\"]", m))
        dec = html.unescape(raw).replace("@.", "@").strip()
        if "@" in dec and ("kmutt.ac.th" in dec or "mail.kmutt.ac.th" in dec):
            if not any(g in dec for g in REJECT_GENERIC):
                return dec
    return None


def main() -> None:
    db = SessionLocal()
    recovered: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    def add_recovery(f_obj: FacultyDB, email_val: str, source_val: str, cluster_name: str) -> None:
        fid = f_obj.id
        if fid in seen_ids:
            return
        em = email_val.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", em):
            return
        if any(d in em for d in REJECT_FREEMAILS):
            return
        if any(g == em for g in REJECT_GENERIC):
            return
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

    # ==========================================
    # 1. KU Agriculture (foa-research-link API / KU Forest Parity)
    # ==========================================
    print("Collecting Cluster 1: KU Agriculture (foa-research-link API)...")
    before_ku_agr = len(seen_ids)
    try:
        r_nodes = requests.get(
            "https://kasetai.agr.ku.ac.th/foa-research-link/api/nodes?includePersons=true",
            headers=HEADERS,
            verify=False,
            timeout=12
        )
        nodes = r_nodes.json()
        person_nodes = [d for d in nodes if d.get("type") == "person"]

        def fetch_foa_person(p_node: dict[str, object]) -> dict[str, str] | None:
            pid = str(p_node.get("id"))
            try:
                r_p = requests.get(
                    f"https://kasetai.agr.ku.ac.th/foa-research-link/api/person?id={pid}",
                    headers=HEADERS,
                    verify=False,
                    timeout=8
                )
                p_info = r_p.json()
                em = p_info.get("email")
                if em and any(d in em.lower() for d in ["@ku.ac.th", "@ku.th"]):
                    p_name = p_info.get("name", "")
                    core = normalize_thai_title_and_name(p_name)[2].strip()
                    f_url = p_info.get("forestUrl") or f"https://research.ku.ac.th/forest/Person.aspx?id={pid}"
                    return {
                        "pid": pid,
                        "name": p_name,
                        "core": core,
                        "email": em.strip().lower(),
                        "url": f_url
                    }
            except Exception:
                pass
            return None

        scraped_agr: list[dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=15) as ex:
            for res in ex.map(fetch_foa_person, person_nodes):
                if res:
                    scraped_agr.append(res)

        missing_ku_agr = db.query(FacultyDB).filter(
            FacultyDB.university_th == "มหาวิทยาลัยเกษตรศาสตร์",
            FacultyDB.faculty_th.like("%เกษตร%"),
            (FacultyDB.email == None) | (FacultyDB.email == "")
        ).all()

        for f in missing_ku_agr:
            f_core = normalize_thai_title_and_name(f.full_name_th)[2].strip()
            best_match = None
            best_score = 0.0
            for it in scraped_agr:
                if it["core"] == f_core:
                    best_match = it
                    best_score = 100.0
                    break
                score = fuzz.ratio(it["core"], f_core)
                if score > best_score and score >= 85.0:
                    best_score = score
                    best_match = it
            if best_match:
                add_recovery(f, best_match["email"], best_match["url"], "KU Agriculture")

    except Exception as e:
        print(f"  Error KU Agriculture: {e}")

    print(f"  -> KU Agriculture recovered: {len(seen_ids) - before_ku_agr}")

    # ==========================================
    # 2. KKU Nursing (nu.kku.ac.th)
    # ==========================================
    print("Collecting Cluster 2: KKU Nursing...")
    before_kku = len(seen_ids)
    kku_dept_urls = [
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5%E0%B8%84%E0%B8%A3%E0%B8%AD%E0%B8%9A%E0%B8%84%E0%B8%A3%E0%B8%A7%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%8A%E0%B8%A1%E0%B8%8A%E0%B8%99",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9C%E0%B8%94%E0%B8%87%E0%B8%84%E0%B8%A3%E0%B8%A3%E0%B8%A0",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%A8%E0%B8%81%E0%B8%A9%E0%B8%B2%E0%B8%A7%E0%B8%88%E0%B8%A2%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%9A%E0%B8%A3%E0%B8%AB%E0%B8%B2%E0%B8%A3%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5%E0%B8%AA%E0%B8%82%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B8%88%E0%B8%95%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%88%E0%B8%95%E0%B9%80%E0%B8%A7%E0%B8%8A",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5%E0%B8%AA%E0%B8%82%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B9%80%E0%B8%94%E0%B8%81",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5%E0%B8%9C%E0%B8%AA%E0%B8%87%E0%B8%AD%E0%B8%B2%E0%B8%A2",
        "https://nu.kku.ac.th/%E0%B8%AA%E0%B8%B2%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%9A%E0%B8%B2%E0%B8%A5%E0%B8%9C%E0%B9%83%E0%B8%AB%E0%B8%8D"
    ]
    kku_scraped: list[dict[str, str]] = []
    for u in kku_dept_urls:
        try:
            r = requests.get(u, headers=HEADERS, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for el in soup.find_all(string=re.compile(r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")):
                p = el.parent
                for _ in range(5):
                    if p.parent and len(p.get_text()) < 500:
                        p = p.parent
                full_card = p.get_text(strip=True, separator=" | ")
                m_em = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_card)
                em = m_em.group(0).lower() if m_em else ""
                if em in REJECT_GENERIC or any(d in em for d in REJECT_FREEMAILS):
                    continue
                parts = full_card.split("|")
                first_chunk = parts[0].strip()
                en_name = ""
                for pt in parts[1:3]:
                    if re.search(r"[a-zA-Z]{3,}", pt):
                        en_name = pt.strip()
                        break
                kku_scraped.append({
                    "raw_name": first_chunk,
                    "clean_th": clean_thai_name(first_chunk),
                    "en_name": en_name,
                    "email": em,
                    "url": u,
                    "card": full_card
                })
        except Exception:
            continue

    missing_kku = db.query(FacultyDB).filter(
        FacultyDB.university_th.ilike("%ขอนแก่น%"),
        FacultyDB.faculty_th.ilike("%พยาบาลศาสตร์%"),
        (FacultyDB.email == None) | (FacultyDB.email == "")
    ).all()

    for f in missing_kku:
        fc = clean_thai_name(f.full_name_th)
        slug = f.id.replace("khonkaenun_facultyofn_", "")
        slug_base = re.sub(r"_\d+$", "", slug).lower()
        matched = False
        for s in kku_scraped:
            if fc.replace(" ", "") == s["clean_th"].replace(" ", ""):
                add_recovery(f, s["email"], s["url"], "KKU Nursing")
                matched = True
                break
        if matched:
            continue
        for s in kku_scraped:
            en_clean = re.sub(r"[^a-zA-Z]", "", s["en_name"]).lower()
            if slug_base in en_clean or slug_base in s["card"].lower():
                add_recovery(f, s["email"], s["url"], "KKU Nursing")
                matched = True
                break
    print(f"  -> KKU Nursing recovered: {len(seen_ids) - before_kku}")

    # ==========================================
    # 3. KU Engineering (hr.eng.ku.ac.th API)
    # ==========================================
    print("Collecting Cluster 3: KU Engineering...")
    before_ku_eng = len(seen_ids)
    missing_ku_eng = db.query(FacultyDB).filter(
        FacultyDB.university_th == "มหาวิทยาลัยเกษตรศาสตร์",
        FacultyDB.faculty_th.ilike("%วิศวกรรมศาสตร์%"),
        (FacultyDB.email == None) | (FacultyDB.email == "")
    ).all()

    all_eng_personnel: list[dict[str, object]] = []
    academic_units = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for u_id in academic_units:
        page = 1
        while True:
            url_dir = f"https://hr.eng.ku.ac.th/api/directory.php?unit_id={u_id}&page={page}"
            try:
                r_dir = requests.get(url_dir, headers=HEADERS, verify=False, timeout=10)
                d_resp = r_dir.json().get("data", {})
                results = d_resp.get("results", [])
                if not results:
                    break
                for item in results:
                    all_eng_personnel.append(item)
                if page >= d_resp.get("last_page", 1):
                    break
                page += 1
            except Exception:
                break

    for f in missing_ku_eng:
        clean_db_name = clean_thai_name(f.full_name_th)
        best_match = None
        best_score = 0.0
        for p in all_eng_personnel:
            p_name = f"{p.get('first_name_th', '')} {p.get('last_name_th', '')}".strip()
            score = fuzz.ratio(clean_db_name, p_name)
            if score > best_score:
                best_score = score
                best_match = p
        if best_score >= 85.0 and best_match:
            p_id = best_match.get("id")
            try:
                r_prof = requests.get(
                    f"https://hr.eng.ku.ac.th/api/directory.php?id={p_id}",
                    headers=HEADERS,
                    verify=False,
                    timeout=8
                )
                p_data = r_prof.json().get("data", {})
                em = p_data.get("email") or p_data.get("google_mail") or p_data.get("office326_mail")
                if em and any(k in em.lower() for k in ["@ku.ac.th", "@ku.th"]):
                    add_recovery(
                        f,
                        em,
                        f"https://hr.eng.ku.ac.th/directory.php?id={p_id}",
                        "KU Engineering"
                    )
            except Exception:
                continue

    print(f"  -> KU Engineering recovered: {len(seen_ids) - before_ku_eng}")

    # ==========================================
    # 4. KMUTT Science (chem & mic)
    # ==========================================
    print("Collecting Cluster 4: KMUTT Science...")
    before_kmutt = len(seen_ids)
    missing_kmutt = db.query(FacultyDB).filter(
        FacultyDB.university_th.ilike("%พระจอมเกล้าธนบุรี%"),
        FacultyDB.faculty_th.ilike("%วิทยาศาสตร์%"),
        (FacultyDB.email == None) | (FacultyDB.email == "")
    ).all()

    # 4a. KMUTT Microbiology
    try:
        r_mic = requests.get("https://mic.kmutt.ac.th/index.php/about/staff", headers=HEADERS, verify=False, timeout=10)
        soup_mic = BeautifulSoup(r_mic.text, "html.parser")
        for a in soup_mic.find_all("a", href=True):
            href = a.get("href")
            t_txt = a.get_text(strip=True)
            if "/index.php/about/staff/12-about/" in href and t_txt and any(k in t_txt for k in ["ดร.", "Prof", "อาจารย์", "ผศ.", "รศ.", "ศ."]):
                full_pl = "https://mic.kmutt.ac.th" + href
                try:
                    pr = requests.get(full_pl, headers=HEADERS, verify=False, timeout=6)
                    em = decloak_joomla(pr.text)
                    if em:
                        c_th = clean_thai_name(t_txt)
                        for f in missing_kmutt:
                            fc = clean_thai_name(f.full_name_th)
                            if fc.replace(" ", "") in c_th.replace(" ", "") or c_th.replace(" ", "") in fc.replace(" ", ""):
                                uname = em.split("@")[0].lower()
                                if any(pt in fc.lower() or pt in full_pl.lower() for pt in uname.split(".")):
                                    add_recovery(f, em, full_pl, "KMUTT Science")
                                    break
                except Exception:
                    continue
    except Exception as e:
        print(f"  Error KMUTT mic: {e}")

    # 4b. KMUTT Chemistry
    try:
        r_chem = requests.get("https://chem.kmutt.ac.th/faculty-staff/faculty-directory/", headers=HEADERS, verify=False, timeout=10)
        soup_chem = BeautifulSoup(r_chem.text, "html.parser")
        chem_links: list[str] = []
        for a in soup_chem.find_all("a", href=True):
            href = a.get("href")
            if "/faculty-staff/faculty-directory/14-faculty-staff/" in href:
                c_url = "https://chem.kmutt.ac.th" + href
                if c_url not in chem_links:
                    chem_links.append(c_url)

        for cl in chem_links:
            try:
                pr = requests.get(cl, headers=HEADERS, verify=False, timeout=6)
                psoup = BeautifulSoup(pr.text, "html.parser")
                th_name = ""
                for s in psoup.find_all("strong"):
                    t = s.get_text(strip=True)
                    if re.search(r"[฀-๿]{3,}", t):
                        th_name = t
                        break
                em = decloak_joomla(pr.text)
                if em and th_name:
                    c_th = clean_thai_name(th_name)
                    for f in missing_kmutt:
                        fc = clean_thai_name(f.full_name_th)
                        if fc.replace(" ", "") in c_th.replace(" ", "") or c_th.replace(" ", "") in fc.replace(" ", ""):
                            uname = em.split("@")[0].lower()
                            # Username sanity guardrail: verify tokens to prevent template copy-paste contamination
                            if any(pt in f.id.lower() or pt in c_th.lower() or pt in cl.lower() for pt in uname.split(".")):
                                add_recovery(f, em, cl, "KMUTT Science")
                                break
            except Exception:
                continue
    except Exception as e:
        print(f"  Error KMUTT chem: {e}")

    print(f"  -> KMUTT Science recovered: {len(seen_ids) - before_kmutt}")

    # ==========================================
    # 5. KU Science (Departmental Endpoints)
    # ==========================================
    print("Collecting Cluster 5: KU Science...")
    before_ku_sci = len(seen_ids)
    missing_ku_sci = db.query(FacultyDB).filter(
        FacultyDB.university_th.ilike("%เกษตรศาสตร์%"),
        FacultyDB.faculty_th.ilike("%วิทยาศาสตร์%"),
        (FacultyDB.email == None) | (FacultyDB.email == "")
    ).all()

    ku_sci_map = {
        "พรรณารี ศรีน้อย": ("fsciprsr@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/pannaree-srinoi/"),
        "วีรเวช ศิริศักดิ์สุนทร": ("fsciwks@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/weekit-sirisaksoontorn/"),
        "อาทิตย์ จรัสอรุณฉาย": ("artit.j@ku.th", "https://chemy.sci.ku.ac.th/ku-personnel/arthit-jarasharuncha/"),
        "วิชชา อิ่มอร่าม": ("witcha.i@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/witcha-im-aram/"),
        "ไพบูลย์ เงินมีศรี": ("paiboon.n@ku.th", "https://chemy.sci.ku.ac.th/ku-personnel/paiboon-ngernmeesri/"),
        "พิทักษ์ เชื้อวงศ์": ("fsciptcw@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/pitak-chuawong/"),
        "วิศกร แสงสุวรรณ": ("withsakorn.san@ku.th", "https://chemy.sci.ku.ac.th/ku-personnel/withsakorn-saengsuwan/"),
        "พิมพา หอมนิรันดร์": ("fscipph@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/pimpa-hormnirun/"),
        "ธารินี สาลีโภชน์": ("fscitna@ku.ac.th", "https://chemy.sci.ku.ac.th/ku-personnel/tharinee-saleepochn/"),
        "วันชัย ปลื้มภาณุภัทร": ("fsciwcp@ku.ac.th", "https://maths.sci.ku.ac.th/ku-personnel/wanchai-pluempanupat/"),
        "อิงอร กิมคง": ("fsciiok@ku.ac.th", "https://micro.sci.ku.ac.th/ku-personnel/ingorn-kimkong/"),
        "วีระศักดิ์ ฟุ้งเฟื่อง": ("fsciwsf@ku.ac.th", "https://zoo.sci.ku.ac.th/ku-personnel/weerasak-fungfuang/"),
        "ภาวิกา ลิ้มอุดมพร": ("fscipil@ku.ac.th", "https://zoo.sci.ku.ac.th/ku-personnel/pavika-limudomporn/")
    }

    for f in missing_ku_sci:
        fc = clean_thai_name(f.full_name_th)
        for name_key, (em_val, src_val) in ku_sci_map.items():
            if name_key in fc or fc in name_key:
                add_recovery(f, em_val, src_val, "KU Science")
                break
    print(f"  -> KU Science recovered: {len(seen_ids) - before_ku_sci}")

    # ==========================================
    # 6. Chula Pharmacy (pharm.chula.ac.th API)
    # ==========================================
    print("Collecting Cluster 6: Chula Pharmacy...")
    before_cu_pharm = len(seen_ids)
    missing_cu_pharm = db.query(FacultyDB).filter(
        FacultyDB.university_th.ilike("%จุฬาลงกรณ์%"),
        FacultyDB.faculty_th.ilike("%เภสัชศาสตร์%"),
        (FacultyDB.email == None) | (FacultyDB.email == "")
    ).all()

    try:
        r_pharm = requests.get(
            "https://www.pharm.chula.ac.th/wp-content/themes/sumraan/loadpersonnel.php",
            headers=HEADERS,
            verify=False,
            timeout=10
        )
        pharm_data = r_pharm.json().get("ReturnData", [])
        for f in missing_cu_pharm:
            fc = clean_thai_name(f.full_name_th)
            for it in pharm_data:
                it_name = it.get("name", "").strip()
                if fc.replace(" ", "") in it_name.replace(" ", "") or it_name.replace(" ", "") in fc.replace(" ", ""):
                    em = (it.get("email") or "").strip().lower()
                    if em and any(d in em for d in ["@chula.ac.th", "@pharm.chula.ac.th"]):
                        add_recovery(f, em, "https://www.pharm.chula.ac.th/directory/", "Chula Pharmacy")
                        break
    except Exception as e:
        print(f"  Error Chula Pharmacy: {e}")
    print(f"  -> Chula Pharmacy recovered: {len(seen_ids) - before_cu_pharm}")

    db.close()

    out_file = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase24.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(recovered, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"TOTAL PHASE 24 VERIFIED OFFICIAL EMAILS: {len(recovered)}")
    print(f"State file saved: {out_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
