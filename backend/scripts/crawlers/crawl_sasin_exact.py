import sys, re, ssl, json
from pathlib import Path
import urllib.request
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

def decode_cf(cf):
    k = int(cf[:2], 16)
    return ''.join([chr(int(cf[i:i+2], 16) ^ k) for i in range(2, len(cf), 2)])

# 1. Fetch main faculty page
main_url = 'https://sasin.edu/team/faculty'
req = urllib.request.Request(main_url, headers=headers)
with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=re.compile(r'/team/profile/[a-zA-Z0-9_-]+', re.I))

profile_urls = {}
for a in links:
    href = a['href']
    full_url = href if href.startswith('http') else f"https://sasin.edu{href}"
    txt = a.get_text(' ', strip=True)
    slug = href.split('/')[-1]
    if slug not in profile_urls:
        profile_urls[slug] = {'url': full_url, 'text': txt}

print(f"Total Sasin faculty profiles discovered: {len(profile_urls)}")

sasin_faculty_data = []

generic_sasin_emails = {
    'marketing@sasin.edu', 'admissions@sasin.edu', 'registrar@sasin.edu', 'it@sasin.edu',
    'hr@sasin.edu', 'research@sasin.edu', 'consulting@sasin.edu', 'finance@sasin.edu',
    'facilities@sasin.edu', 'procurement@sasin.edu', 'exchange@sasin.edu', 'sasahouse@sasin.edu',
    'sasin.library@sasin.edu', 'studentexperience@sasin.edu', 'afeec@sasin.edu',
    'executiveeducation@sasin.edu', 'sasin.next@sasin.edu', 'iiethai@bkk.iie.org'
}

for slug, p in profile_urls.items():
    try:
        req = urllib.request.Request(p['url'], headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
            p_html = resp.read().decode('utf-8', errors='ignore')
        p_soup = BeautifulSoup(p_html, 'html.parser')

        # Check cloudflare emails
        cf_tags = p_soup.find_all(attrs={'data-cfemail': True})
        candidate_emails = []
        for t in cf_tags:
            em = decode_cf(t['data-cfemail']).strip().lower()
            if em.endswith('@sasin.edu') and em not in generic_sasin_emails:
                candidate_emails.append(em)

        # Regex fallback on raw html
        raw_emails = re.findall(r'([a-zA-Z0-9._%+-]+@sasin\.edu)', p_html, re.I)
        for re_em in raw_emails:
            re_em = re_em.lower()
            if re_em not in generic_sasin_emails and not re_em.startswith('u003e'):
                if re_em not in candidate_emails:
                    candidate_emails.append(re_em)

        # Determine resident vs visiting
        page_text = p_soup.get_text(' ', strip=True)
        is_resident = 'Resident' in page_text
        is_visiting = 'Visiting' in page_text

        # Extract person's display name
        h1 = p_soup.find('h1')
        title_name = h1.get_text(strip=True) if h1 else slug.replace('-', ' ').title()

        sasin_faculty_data.append({
            'slug': slug,
            'name': title_name,
            'url': p['url'],
            'emails': candidate_emails,
            'is_resident': is_resident,
            'is_visiting': is_visiting,
            'text': page_text[:1000]
        })
    except Exception as e:
        print(f"Error scraping {slug}: {e}")

print(f"Scraped {len(sasin_faculty_data)} Sasin profiles.")

# Query DB missing Sasin faculty
db = SessionLocal()
missing_sasin = db.query(FacultyDB).filter(
    FacultyDB.university_th.like('%จุฬา%'),
    (FacultyDB.faculty_th.like('%สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์%') | FacultyDB.faculty_th.like('%ศศินทร์%')),
    (FacultyDB.email == None) | (FacultyDB.email == '')
).all()

recovered = []
unrecoverable_visiting = []
unrecoverable_no_email = []

for f in missing_sasin:
    name_clean = f.full_name_th.replace('อ.', '').replace('ดร.', '').replace('ศ.', '').replace('ผศ.', '').replace('รศ.', '').strip()

    best_match = None
    best_score = 0
    for s_fac in sasin_faculty_data:
        # Match against name or slug
        score1 = fuzz.token_set_ratio(name_clean.lower(), s_fac['name'].lower())
        score2 = fuzz.token_set_ratio(name_clean.lower(), s_fac['slug'].replace('-', ' ').lower())
        score = max(score1, score2)
        if score > best_score:
            best_score = score
            best_match = s_fac

    if best_score >= 75 and best_match:
        if best_match['emails']:
            recovered.append({
                'id': f.id,
                'full_name_th': f.full_name_th,
                'name_en': best_match['name'],
                'email': best_match['emails'][0],
                'source': best_match['url'],
                'score': best_score,
                'cluster': 'Sasin School of Management'
            })
        else:
            if best_match['is_visiting']:
                unrecoverable_visiting.append({
                    'id': f.id,
                    'full_name_th': f.full_name_th,
                    'status': 'Visiting Faculty (external institution/practitioner, no @sasin.edu published)'
                })
            else:
                unrecoverable_no_email.append({
                    'id': f.id,
                    'full_name_th': f.full_name_th,
                    'status': 'Resident Faculty but email omitted from public profile'
                })
    else:
        unrecoverable_no_email.append({
            'id': f.id,
            'full_name_th': f.full_name_th,
            'status': 'Not listed in active Sasin faculty directory'
        })

print(f"\n=== RECOVERED SASIN OFFICIAL EMAILS ({len(recovered)}) ===")
for r in recovered:
    print(f"[{r['score']:.1f}] {r['id']} | {r['full_name_th']} -> {r['email']} ({r['source']})")

print(f"\n=== SASIN UNRECOVERABLE VISITING FACULTY ({len(unrecoverable_visiting)}) ===")
for u in unrecoverable_visiting:
    print(f"  {u['id']} | {u['full_name_th']} -> {u['status']}")

print(f"\n=== SASIN NOT LISTED / OMITTED ({len(unrecoverable_no_email)}) ===")
for u in unrecoverable_no_email:
    print(f"  {u['id']} | {u['full_name_th']} -> {u['status']}")
