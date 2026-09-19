import sys, re, ssl, json
from pathlib import Path
import urllib.request
from urllib.parse import urljoin
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

vet_faculty_cards = []

for u in vet_departments:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='profile-item')
        for item in items:
            mailto = item.find('a', href=re.compile(r'^mailto:', re.I))
            email = mailto['href'].replace('mailto:', '').strip().lower() if mailto else None
            # Extract researcher info
            res = item.find('a', href=re.compile(r'researcher_info', re.I))
            res_url = urljoin(u, res['href']) if res else u

            # Clean text inside item
            card_text = item.get_text(' ', strip=True)
            # Avoid generic emails or missing
            if email and 'chula.ac.th' in email and not any(k in email for k in ['saraban', 'contact', 'info']):
                vet_faculty_cards.append({
                    'email': email,
                    'source': res_url,
                    'text': card_text,
                    'dept_url': u
                })
    except Exception as e:
        print(f"Error crawling {u}: {e}")

print(f"Total authentic profile cards collected: {len(vet_faculty_cards)}")

db = SessionLocal()
missing_vet = db.query(FacultyDB).filter(
    FacultyDB.university_th.like('%จุฬา%'),
    FacultyDB.faculty_th == 'คณะสัตวแพทยศาสตร์',
    (FacultyDB.email == None) | (FacultyDB.email == '')
).all()

recovered = []
unmatched = []

for f in missing_vet:
    clean_th = TITLE_STRIP_REGEX.sub('', f.full_name_th).strip()
    clean_th = re.sub(r'\(.*?\)', '', clean_th).strip()

    best_match = None
    best_score = 0
    for card in vet_faculty_cards:
        # Match against card text
        s1 = fuzz.partial_ratio(clean_th, card['text'])
        s2 = fuzz.token_set_ratio(clean_th, card['text'])
        score = max(s1, s2)
        if score > best_score:
            best_score = score
            best_match = card

    if best_score >= 85 and best_match:
        recovered.append({
            'id': f.id,
            'full_name_th': f.full_name_th,
            'clean_name': clean_th,
            'email': best_match['email'],
            'source': best_match['source'],
            'score': best_score,
            'cluster': 'Faculty of Veterinary Science'
        })
    else:
        unmatched.append({
            'id': f.id,
            'full_name_th': f.full_name_th,
            'dept': f.department_th,
            'best_score': best_score,
            'best_text': best_match['text'][:50] if best_match else 'None'
        })

print(f"\n=== RECOVERED VET FACULTY ({len(recovered)}) ===")
for r in recovered:
    print(f"[{r['score']:.1f}] {r['id']} | {r['full_name_th']} -> {r['email']} ({r['source']})")

print(f"\n=== UNMATCHED VET FACULTY ({len(unmatched)}) ===")
for u in unmatched:
    print(f"[{u['best_score']:.1f}] {u['id']} | {u['full_name_th']} | dept: {u['dept']}")
