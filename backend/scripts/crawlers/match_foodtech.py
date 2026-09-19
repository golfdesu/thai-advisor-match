import sys, re, ssl
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

url = 'http://foodtech.sc.chula.ac.th/faculties/lecturer'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
food_cards = []
for a in soup.find_all('a', href=re.compile(r'/faculty/')):
    card = a.parent
    txt = card.get_text(' ', strip=True)
    m = re.search(r'([a-zA-Z0-9._%+-]+@chula\.ac\.th)', txt)
    if m:
        food_cards.append({
            'url': a['href'],
            'email': m.group(1).lower(),
            'text': txt
        })

print(f"Total foodtech cards: {len(food_cards)}")

db = SessionLocal()
food_targets = db.query(FacultyDB).filter(
    FacultyDB.university_th.like('%จุฬา%'),
    FacultyDB.department_th == 'ภาควิชาเทคโนโลยีทางอาหาร',
    (FacultyDB.email == None) | (FacultyDB.email == '')
).all()

recovered = []
not_found = []

for f in food_targets:
    clean = TITLE_STRIP_REGEX.sub('', f.full_name_th).strip()
    best_card = None
    best_score = 0
    for c in food_cards:
        score = fuzz.token_set_ratio(clean, c['text'])
        if score > best_score:
            best_score = score
            best_card = c
    if best_score >= 80 and best_card:
        recovered.append({
            'id': f.id,
            'full_name_th': f.full_name_th,
            'email': best_card['email'],
            'source': best_card['url'],
            'score': best_score,
            'cluster': 'Faculty of Science'
        })
    else:
        not_found.append((f.id, f.full_name_th, best_score, best_card['text'][:60] if best_card else 'None'))

print(f"\n=== RECOVERED FOODTECH ({len(recovered)}) ===")
for r in recovered:
    print(f"  [{r['score']:.1f}] {r['id']} | {r['full_name_th']} -> {r['email']} ({r['source']})")

print(f"\n=== NOT FOUND IN FOODTECH ACTIVE ({len(not_found)}) ===")
for fid, name, score, txt in not_found:
    print(f"  [{score:.1f}] {fid} | {name} (best: {txt})")
