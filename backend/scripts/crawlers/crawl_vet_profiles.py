import sys, re, ssl, json, time
from pathlib import Path
import urllib.request
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.agentic_pipeline.state_reducer import TITLE_STRIP_REGEX

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# First, collect all researcher_info links from the 12 department pages
vet_departments = [
    'https://www.vet.chula.ac.th/department/anatomy',
    'https://www.vet.chula.ac.th/department/%E0%B8%AD%E0%B8%B2%E0%B8%A2%E0%B8%B8%E0%B8%A3%E0%B8%A8%E0%B8%B2%E0%B8%AA%E0%B8%95%E0%B8%A3%E0%B9%8C-ukzh',
    'https://www.vet.chula.ac.th/department/%E0%B9%80%E0%B8%A0%E0%B8%AA%E0%B8%B1%E0%B8%8A%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2-lvew',
    'https://www.vet.chula.ac.th/department/microbiology',
    'https://www.vet.chula.ac.th/department/%E0%B8%AA%E0%B8%B1%E0%B8%95%E0%B8%A7%E0%B9%81%E0%B8%9E%E0%B8%97%E0%B8%A2%E0%B8%AA%E0%B8%B2%E0%B8%98%E0%B8%B2%E0%B8%A3%E0%B8%93%E0%B8%AA%E0%B8%B8%E0%B8%82',
    'https://www.vet.chula.ac.th/department/%E0%B8%A8%E0%B8%B1%E0%B8%A5%E0%B8%A2%E0%B8%A8%E0%B8%B2%E0%B8%AA%E0%B8%95%E0%B8%A3%E0%B9%8C',
    'https://www.vet.chula.ac.th/department/%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%B4%E0%B8%A8%E0%B8%B2%E0%B8%AA%E0%B8%95%E0%B8%A3%E0%B9%8C-%E0%B9%80%E0%B8%98%E0%B8%99%E0%B8%B8%E0%B9%80%E0%B8%A7%E0%B8%8A%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2-%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%AA%E0%B8%B7%E0%B8%9A%E0%B8%9E%E0%B8%B1%E0%B8%99%E0%B8%98%E0%B8%B8%E0%B9%8C',
    'https://www.vet.chula.ac.th/department/%E0%B8%AB%E0%B8%99%E0%B9%88%E0%B8%A7%E0%B8%A2%E0%B8%9B%E0%B8%A3%E0%B8%AA%E0%B8%B4%E0%B8%95%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2',
    'https://www.vet.chula.ac.th/department/%E0%B8%AB%E0%B8%99%E0%B9%88%E0%B8%A7%E0%B8%A2%E0%B8%9E%E0%B8%A2%E0%B8%B2%E0%B8%98%E0%B8%B4%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2',
    'https://www.vet.chula.ac.th/department/%E0%B8%AA%E0%B8%A3%E0%B8%B5%E0%B8%A3%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2-ftpi',
    'https://www.vet.chula.ac.th/department/%E0%B8%AB%E0%B8%99%E0%B9%88%E0%B8%A7%E0%B8%A2%E0%B8%8A%E0%B8%B5%E0%B8%A7%E0%B9%80%E0%B8%84%E0%B8%A1%E0%B8%B5',
    'https://www.vet.chula.ac.th/department/%E0%B8%AA%E0%B8%B1%E0%B8%95%E0%B8%A7%E0%B8%9A%E0%B8%B2%E0%B8%A5-le1u'
]

res_links = set()

for u in vet_departments:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=re.compile(r'researcher_info/\d+', re.I)):
            m = re.search(r'researcher_info/(\d+)', a['href'])
            if m:
                res_links.add(int(m.group(1)))
    except Exception as e:
        print(f"Error {u}: {e}")

print(f"Found {len(res_links)} unique researcher profile IDs: {sorted(list(res_links))[:20]}...")

# Now fetch each researcher_info page
researcher_profiles = []

for rid in sorted(list(res_links)):
    rurl = f"https://www.vet.chula.ac.th/researcher_info/{rid}"
    try:
        req = urllib.request.Request(rurl, headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')

        # Check mailto on this page
        official_email = None
        for a in soup.find_all('a', href=re.compile(r'^mailto:', re.I)):
            em = a['href'].replace('mailto:', '').strip().lower()
            if 'chula.ac.th' in em and not any(k in em for k in ['saraban', 'contact', 'info', 'vetpharmaco']) and '@' in em and len(em.split('@')[0]) > 1:
                official_email = em
                break

        # Extract researcher name from h1, h2, h3, h4 or title
        # In researcher_info, let's see where the name is
        text = soup.get_text(' ', strip=True)
        researcher_profiles.append({
            'id': rid,
            'url': rurl,
            'email': official_email,
            'text': text
        })
    except Exception as e:
        pass

print(f"Scraped {len(researcher_profiles)} researcher profile pages.")

# Now match against 31 missing vet faculty
db = SessionLocal()
missing_vet = db.query(FacultyDB).filter(
    FacultyDB.university_th.like('%จุฬา%'),
    FacultyDB.faculty_th == 'คณะสัตวแพทยศาสตร์',
    (FacultyDB.email == None) | (FacultyDB.email == '')
).all()

recovered_vet = []

for f in missing_vet:
    clean_th = TITLE_STRIP_REGEX.sub('', f.full_name_th).strip()
    clean_th = re.sub(r'\(.*?\)', '', clean_th).strip()

    best_rp = None
    best_score = 0
    for rp in researcher_profiles:
        score = fuzz.token_set_ratio(clean_th, rp['text'])
        if score > best_score:
            best_score = score
            best_rp = rp

    if best_score >= 80 and best_rp and best_rp['email']:
        recovered_vet.append({
            'id': f.id,
            'full_name_th': f.full_name_th,
            'email': best_rp['email'],
            'source': best_rp['url'],
            'score': best_score,
            'cluster': 'Faculty of Veterinary Science'
        })
    elif best_score >= 80 and best_rp:
        print(f"Profile found for {f.full_name_th} at {best_rp['url']} but official email is None (or freemail)")

print(f"\n=== RECOVERED OFFICIAL EMAILS IN VET ({len(recovered_vet)}) ===")
for rv in recovered_vet:
    print(f"[{rv['score']:.1f}] {rv['id']} | {rv['full_name_th']} -> {rv['email']} ({rv['source']})")
