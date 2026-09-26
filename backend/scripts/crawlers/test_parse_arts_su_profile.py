# -*- coding: utf-8 -*-
import urllib.request, ssl, re, json
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def parse_profile(url, dept_hint="", img_hint=""):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        soup = BeautifulSoup(r.read(), 'html.parser')

    main = soup.find('main') or soup

    # Title / Thai name from h1
    h1 = main.find('h1')
    raw_name_th = h1.get_text(strip=True) if h1 else ""

    # English title/name from h4 or subtitle
    h4 = main.find('h4')
    raw_name_en = h4.get_text(strip=True) if h4 else ""

    # Department
    dept_th = dept_hint
    # look for <p> containing ภาควิชา
    for p in main.find_all('p'):
        ptxt = p.get_text(strip=True)
        if ptxt.startswith('ภาควิชา'):
            dept_th = ptxt
            break

    # Email
    email = None
    for p in main.find_all(['p', 'a', 'span', 'li']):
        txt = p.get_text(strip=True)
        em_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', txt)
        if em_match:
            em = em_match.group(1).lower()
            # ignore webmaster or generic
            if em not in ['arts.silpakorn@gmail.com', 'admin@arts.su.ac.th']:
                email = em
                break

    # Image
    img_url = img_hint
    if not img_url:
        img = main.find('img')
        if img and 'src' in img.attrs:
            img_url = img['src']

    # Education
    education = []
    edu_hdr = None
    for h in main.find_all(['h2', 'h3']):
        if any(k in h.get_text(strip=True) for k in ['วุฒิการศึกษา', 'Education']):
            edu_hdr = h
            break
    if edu_hdr:
        curr = edu_hdr.find_next_sibling()
        while curr and curr.name not in ['h2', 'h3']:
            if curr.name in ['ul', 'ol']:
                for li in curr.find_all('li'):
                    txt = li.get_text(strip=True)
                    if txt: education.append(txt)
            elif curr.name == 'p':
                txt = curr.get_text(strip=True)
                if txt and len(txt) > 3: education.append(txt)
            curr = curr.find_next_sibling()

    # Research interests
    interests = []
    int_hdr = None
    for h in main.find_all(['h2', 'h3']):
        if any(k in h.get_text(strip=True) for k in ['สาขาวิชาที่สนใจ', 'Areas of Specialization', 'ความเชี่ยวชาญ', 'ความสนใจ']):
            int_hdr = h
            break
    if int_hdr:
        curr = int_hdr.find_next_sibling()
        while curr and curr.name not in ['h2', 'h3']:
            if curr.name in ['ul', 'ol']:
                for li in curr.find_all('li'):
                    txt = li.get_text(strip=True)
                    if txt: interests.append(txt)
            elif curr.name == 'p':
                txt = curr.get_text(strip=True)
                if txt and len(txt) > 3: interests.append(txt)
            curr = curr.find_next_sibling()

    # Featured publications
    publications = []
    for h in main.find_all(['h2', 'h3', 'h4']):
        htxt = h.get_text(strip=True)
        if any(k in htxt for k in ['ผลงานวิจัย', 'Publications', 'บทความทางวิชาการ', 'หนังสือและตำรา', 'ผลงานทางวิชาการ']):
            curr = h.find_next_sibling()
            while curr and curr.name not in ['h2', 'h3', 'h4']:
                if curr.name in ['ul', 'ol']:
                    for li in curr.find_all('li'):
                        txt = li.get_text(strip=True)
                        if txt and len(txt) > 10:
                            publications.append(txt)
                elif curr.name == 'p':
                    txt = curr.get_text(strip=True)
                    if txt and len(txt) > 10:
                        publications.append(txt)
                curr = curr.find_next_sibling()

    return {
        'url': url,
        'raw_name_th': raw_name_th,
        'raw_name_en': raw_name_en,
        'dept_th': dept_th,
        'email': email,
        'img_url': img_url,
        'education': education[:10],
        'research_interests': interests[:10],
        'featured_publications': publications[:10],
    }

# Test sample
test_res = parse_profile('https://arts.su.ac.th/?page_id=1360', 'ภาควิชาภาษาไทย')
print(json.dumps(test_res, ensure_ascii=False, indent=2))
