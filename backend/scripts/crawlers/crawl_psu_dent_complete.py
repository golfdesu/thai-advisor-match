# -*- coding: utf-8 -*-
"""
Full Roster Extraction for Faculty of Dentistry, Prince of Songkla University (PSU)
Extracts official faculty members across all 6 departments.
Cross-references with OpenAlex API for publication metrics.
"""
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

DEPT_URLS = [
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ทันตกรรมหัตถการ)", "https://www.dent.psu.ac.th/unit/conser/index.php/operative_dentistry/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (วิทยาเอ็นโดดอนต์)", "https://www.dent.psu.ac.th/unit/conser/index.php/endodontics/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ปริทันตวิทยา)", "https://www.dent.psu.ac.th/unit/conser/index.php/periodontology/"),
    ("สาขาวิชาชีววิทยาช่องปาก", "https://www.dent.psu.ac.th/unit/oral/index.php/staff/"),
    ("สาขาวิชาทันตกรรมป้องกัน", "https://www.dent.psu.ac.th/unit/prevent/index.php/staff/"),
    ("สาขาวิชาทันตกรรมประดิษฐ์", "https://www.dent.psu.ac.th/unit/prost/staff/"),
    ("สาขาวิชาโอษฐวิทยา", "https://www.dent.psu.ac.th/unit/stoma/index.php/staff/"),
    ("สาขาวิชาศัลยศาสตร์ช่องปาก", "https://www.dent.psu.ac.th/unit/surgery/index.php/staff/")
]

TITLE_PATTERN = re.compile(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ทพ\.|ทพญ\.|ดร\.|นพ\.|พญ\.)")

def extract_faculty_from_page(dept_name, url):
    print(f"Fetching {dept_name} from {url}...")
    req = urllib.request.Request(url, headers=HEADERS)
    faculty_list = []
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            # Find all image/person blocks, table rows, or div cards
            # Extract text blocks
            elements = soup.find_all(['div', 'td', 'p', 'li'])
            seen_names = set()

            for el in elements:
                text = el.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                # Check if any line has Thai title
                for i, line in enumerate(lines):
                    # Clean line
                    clean_line = re.sub(r"\s+", " ", line)
                    if TITLE_PATTERN.match(clean_line) and any(c in clean_line for c in ["ทพ", "อาจารย์", "ศาสตราจารย์"]):
                        # Extract Thai name
                        name_match = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพ\.|ทพญ\.)+(?:\s*(?:ดร\.|ทพ\.|ทพญ\.))*\s*[ก-๙]{2,25}(?:\s+[ก-๙]{2,25})+)", clean_line)
                        if name_match:
                            full_name_th = name_match.group(1).strip()
                            # Avoid duplicates
                            if full_name_th in seen_names or len(full_name_th) < 8:
                                continue
                            seen_names.add(full_name_th)

                            # Look for email in surrounding lines
                            email = None
                            en_name = None
                            for surrounding in lines[max(0, i-2):min(len(lines), i+6)]:
                                email_m = re.search(r"([a-zA-Z0-9._%+-]+@(?:dent\.)?psu\.ac\.th)", surrounding)
                                if email_m and not email:
                                    email = email_m.group(1).lower()

                                # Look for English name: e.g. "Lect. Dr. Jirayu Saepoo" or "Sakarin Tangphothitham"
                                en_m = re.search(r"(?:(?:Prof|Assoc\.?\s*Prof|Asst\.?\s*Prof|Lect\.?|Dr\.?)\s*(?:Dr\.?)?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", surrounding)
                                if en_m and not en_name:
                                    candidate = en_m.group(1).strip()
                                    if candidate not in ["Faculty And", "Office Secretary", "Prince Of", "Songkla University"]:
                                        en_name = candidate

                            # Find image if in same parent
                            img_url = None
                            parent = el.find_parent(['div', 'tr', 'td'])
                            if parent:
                                img = parent.find('img')
                                if img and img.get('src'):
                                    src = img['src']
                                    if not src.startswith('http'):
                                        src = urllib.parse.urljoin(url, src)
                                    if 'logo' not in src.lower() and 'icon' not in src.lower():
                                        img_url = src

                            faculty_list.append({
                                "full_name_th": full_name_th,
                                "name_en": en_name,
                                "email": email,
                                "department_th": dept_name,
                                "faculty_th": "คณะทันตแพทยศาสตร์",
                                "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                                "profile_url": url,
                                "image_url": img_url
                            })
                            print(f"  + Found: {full_name_th} | EN: {en_name} | Email: {email}")

    except Exception as e:
        print(f"Error fetching {url}: {e}")

    return faculty_list

def main():
    all_psu_dent = []
    for dept, url in DEPT_URLS:
        facs = extract_faculty_from_page(dept, url)
        all_psu_dent.extend(facs)

    print(f"\n==================================================")
    print(f"Total authentic PSU Dentistry faculty extracted: {len(all_psu_dent)}")
    print(f"==================================================")

    with open("psu_dent_extracted.json", "w", encoding="utf-8") as f:
        json.dump(all_psu_dent, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
