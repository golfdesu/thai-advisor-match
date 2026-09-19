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

vet_all_cards = []

for u in vet_departments:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='profile-item')
        for item in items:
            mailto = item.find('a', href=re.compile(r'^mailto:', re.I))
            email = mailto['href'].replace('mailto:', '').strip() if mailto else None
            res = item.find('a', href=re.compile(r'researcher_info', re.I))
            res_url = urljoin(u, res['href']) if res else u
            card_text = item.get_text(' ', strip=True)
            vet_all_cards.append({
                'email': email,
                'source': res_url,
                'text': card_text,
                'dept_url': u
            })
    except Exception as e:
        print(f"Error crawling {u}: {e}")

db = SessionLocal()
missing_vet = db.query(FacultyDB).filter(
    FacultyDB.university_th.like('%จุฬา%'),
    FacultyDB.faculty_th == 'คณะสัตวแพทยศาสตร์',
    (FacultyDB.email == None) | (FacultyDB.email == '')
).all()

print(f"Total missing vet in DB: {len(missing_vet)}")
print(f"Total cards found across all 12 vet depts: {len(vet_all_cards)}")

for f in missing_vet:
    clean_th = TITLE_STRIP_REGEX.sub('', f.full_name_th).strip()
    clean_th = re.sub(r'\(.*?\)', '', clean_th).strip()
    # Find match in cards
    best_card = None
    best_score = 0
    for c in vet_all_cards:
        s = fuzz.token_set_ratio(clean_th, c['text'])
        if s > best_score:
            best_score = s
            best_card = c
    if best_score >= 80 and best_card:
        em = best_card['email']
        print(f"MATCH [{best_score:.1f}] {f.id} | {f.full_name_th} -> email: {em} | source: {best_card['source']}")
    else:
        print(f"NO MATCH [{best_score:.1f}] {f.id} | {f.full_name_th} | dept: {f.department_th}")
