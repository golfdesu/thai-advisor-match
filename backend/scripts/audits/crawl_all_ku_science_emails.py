# Deep Multi-threaded Crawler for all Kasetsart University Faculty of Science Departments
import sys, ssl, urllib.request, re, json, time
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def clean_th(name):
    if not name:
        return ""
    name = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|สัตวแพทย์|อาจารย์|ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์|\s+)+", "", name)
    name = re.sub(r"^(?:ดร\.|Dr\.)\s*", "", name)
    return re.sub(r"\s+", "", name).strip()

def is_valid_ku_email(e):
    return bool(re.search(r"@(.*\.)?ku\.(?:ac\.)?th$", e))

def fetch_soup(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser"), html

def get_profile_data(p_url):
    try:
        soup, html = fetch_soup(p_url, timeout=8)
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else ""
        
        # Look for mailto inside h1.parent
        emails = []
        if h1 and h1.parent:
            for a in h1.parent.find_all("a", href=re.compile(r"mailto:")):
                m = re.search(r"mailto:([\w\.-]+@[\w\.-]+)", a.get("href") or "")
                if m:
                    em = m.group(1).lower().strip()
                    if is_valid_ku_email(em):
                        emails.append(em)
        
        # If none in h1.parent, check card container
        if not emails:
            for card in soup.find_all(class_=re.compile(r"elementor-widget-container|profile|contact", re.I)):
                for a in card.find_all("a", href=re.compile(r"mailto:")):
                    m = re.search(r"mailto:([\w\.-]+@[\w\.-]+)", a.get("href") or "")
                    if m:
                        em = m.group(1).lower().strip()
                        # ignore footer dept head
                        if em not in ["fsciasb@ku.ac.th", "fsciwcp@ku.ac.th"] and is_valid_ku_email(em):
                            emails.append(em)
                            
        if emails:
            return p_url, name, emails[0]
    except Exception as e:
        pass
    return p_url, None, None

def main():
    print("=== Multi-Threaded Deep Crawl Kasetsart Faculty of Science ===")
    
    listing_sources = [
        ("Physics", "https://physics.sci.ku.ac.th/personnel-group/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/"),
        ("Maths", "https://maths.sci.ku.ac.th/personnel-group/lecturer/"),
        ("Zoo", "https://zoo.sci.ku.ac.th/personnel-group/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/"),
        ("Genetics", "https://genetics.sci.ku.ac.th/personnel-group/lecturer/"),
        ("Earth", "https://earth.sci.ku.ac.th/personnel-group/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/"),
        ("Stat", "https://stat.sci.ku.ac.th/personnel-group/lecturer/"),
        ("AppRad", "https://apprad.sci.ku.ac.th/personnel-group/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3%e0%b8%a0%e0%b8%b2%e0%b8%84%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%a3%e0%b8%b1%e0%b8%87%e0%b8%aa%e0%b8%b5%e0%b8%9b%e0%b8%a3%e0%b8%b0/"),
        ("Admin Board", "https://sci.ku.ac.th/web2024/personnel-group/administrative-board/"),
        ("Heads", "https://sci.ku.ac.th/web2024/personnel-group/head-of-departments/"),
        ("Committee", "https://sci.ku.ac.th/web2024/personnel-group/faculty-of-science-committee/")
    ]
    
    harvested_profiles = set()
    for label, list_url in listing_sources:
        try:
            soup, _ = fetch_soup(list_url, timeout=10)
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                if "ku-personnel" in href:
                    harvested_profiles.add(href)
        except Exception as e:
            print(f"  Error fetching {label}: {e}")

    print(f"Total unique 1-to-1 profile URLs to inspect: {len(harvested_profiles)}")
    
    crawled_data = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(get_profile_data, url) for url in harvested_profiles]
        for f in as_completed(futures):
            p_url, name, em = f.result()
            if name and em:
                crawled_data.append({"profile_url": p_url, "name": name, "email": em})
                print(f"[Profile] Found: {name} -> {em}")

    # 2. Add Botany direct parsing
    print("Fetching Botany staff...")
    try:
        b_url = "http://www.botany.sci.ku.ac.th/staff/"
        soup, _ = fetch_soup(b_url, timeout=10)
        for p in soup.find_all(["p", "div", "td"]):
            txt = p.get_text(strip=True)
            if "@ku." in txt and len(txt) < 150:
                m = re.search(r"([฀-๿\.\s]+?)(?:[a-zA-Z0-9_\.-]+@[\w\.-]+)", txt)
                em_m = re.search(r"([a-zA-Z0-9_\.-]+@(?:ku\.ac\.th|ku\.th))", txt)
                if m and em_m:
                    tname = m.group(1).strip()
                    temail = em_m.group(1).lower().strip()
                    if clean_th(tname) and len(clean_th(tname)) > 4 and is_valid_ku_email(temail):
                        crawled_data.append({"profile_url": b_url, "name": tname, "email": temail})
                        print(f"[Botany] Found: {tname} -> {temail}")
    except Exception as e:
        print(f"Botany error: {e}")

    # 3. Add Biochemistry direct parsing
    print("Fetching Biochem staff...")
    try:
        biochem_url = "https://biochemistry.sci.ku.ac.th/?page_id=298"
        soup, _ = fetch_soup(biochem_url, timeout=10)
        for el in soup.find_all(string=re.compile(r"@ku\.")):
            card = el.parent
            for _ in range(4):
                if card.parent:
                    card = card.parent
            card_text = card.get_text(separator=" ", strip=True)
            em_match = re.search(r"[\w\.-]+@(?:ku\.ac\.th|ku\.th)", card_text)
            name_match = re.search(r"([฀-๿\.\s]{5,40})", card_text)
            if em_match and name_match:
                em = em_match.group(0).lower()
                nm = name_match.group(1).strip()
                if clean_th(nm) and len(clean_th(nm)) > 4 and is_valid_ku_email(em):
                    crawled_data.append({"profile_url": biochem_url, "name": nm, "email": em})
                    print(f"[Biochem] Found: {nm} -> {em}")
    except Exception as e:
        print(f"Biochem error: {e}")

    print(f"Total crawled items before deduplication: {len(crawled_data)}")

    # Deduplicate crawled_data by (clean_th(name), email)
    dedup_crawled = []
    seen_pairs = set()
    for item in crawled_data:
        cname = clean_th(item["name"])
        if not cname:
            continue
        pair = (cname, item["email"])
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            dedup_crawled.append(item)

    from collections import defaultdict
    email_to_names = defaultdict(set)
    for item in dedup_crawled:
        email_to_names[item["email"]].add(clean_th(item["name"]))

    print(f"Total dedup crawled items: {len(dedup_crawled)}")
    shared_emails = {em for em, names in email_to_names.items() if len(names) > 1}
    print(f"Shared emails excluded: {len(shared_emails)} -> {shared_emails}")

    # Match against PostgreSQL faculties
    db = SessionLocal()
    matched_results = []
    seen_db_ids = set()
    seen_emails = set()

    try:
        db_facs = db.query(FacultyDB).filter(
            FacultyDB.email.is_(None),
            FacultyDB.university_th.like("%เกษตรศาสตร์%")
        ).all()
        print(f"Total KU faculties in DB with NULL email: {len(db_facs)}")

        for item in dedup_crawled:
            em = item["email"]
            # Exclude department heads or shared inboxes appearing for multiple distinct people
            if em in shared_emails:
                continue
            if em in seen_emails:
                continue

            c_crawled_name = clean_th(item["name"])
            if not c_crawled_name:
                continue

            for f in db_facs:
                if f.id in seen_db_ids:
                    continue
                c_db_name = clean_th(f.full_name_th)
                if c_db_name and c_db_name == c_crawled_name:
                    seen_db_ids.add(f.id)
                    seen_emails.add(em)
                    matched_results.append({
                        "id": f.id,
                        "full_name_th": f.full_name_th,
                        "university_th": f.university_th,
                        "faculty_th": f.faculty_th,
                        "department_th": f.department_th,
                        "email": em,
                        "profile_url": item["profile_url"]
                    })
                    break

        print(f"Successfully matched: {len(matched_results)} faculty members in DB!")
        out_file = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase17.json"
        out_file.write_text(json.dumps(matched_results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved matched results to {out_file}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
