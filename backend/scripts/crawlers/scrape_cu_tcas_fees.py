import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

import urllib3
urllib3.disable_warnings()

def scrape_cu_tcas_and_programs():
    print("=== Step 1: Scraping Official Chulalongkorn Programs via AJAX ===")
    url = 'https://www.chula.ac.th/academics/programs/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, timeout=15, headers=headers, verify=False)
        nonce_match = re.search(r'programsFilterData\s*=\s*\{.*?nonce:\s*\'([^\']+)\'', r.text, re.DOTALL)
        nonce = nonce_match.group(1) if nonce_match else ''
    except Exception as e:
        print(f"Error fetching CU main page: {e}")
        nonce = ''

    cu_programs = []
    if nonce:
        for p in range(1, 30):
            payload = {'action': 'filter_programs', 'nonce': nonce, 'paged': p}
            try:
                resp = requests.post('https://www.chula.ac.th/wp-admin/admin-ajax.php', data=payload, headers=headers, verify=False, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                html = data.get('html', '')
                if not html:
                    break
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('div', attrs={'data-degree-program': True})
                if not items:
                    break
                for it in items:
                    h2 = it.find('h2')
                    h3 = it.find('h3')
                    title_th = h2.get_text(strip=True) if h2 else ''
                    fac_th = h3.get_text(strip=True) if h3 else ''
                    deg_slug = it.get('data-degree-program', '')
                    lang = it.get('data-program-language', '')
                    a_tag = it.find('a', href=True)
                    link = a_tag['href'] if a_tag else 'https://www.chula.ac.th/academics/programs/'

                    deg_level = "ปริญญาตรี"
                    if "master" in deg_slug or "โท" in deg_slug:
                        deg_level = "ปริญญาโท"
                    elif "doctor" in deg_slug or "phd" in deg_slug or "เอก" in deg_slug:
                        deg_level = "ปริญญาเอก"
                    elif "certificate" in deg_slug:
                        deg_level = "ประกาศนียบัตรบัณฑิต"

                    if title_th:
                        cu_programs.append({
                            'title_th': title_th,
                            'faculty_th': fac_th,
                            'degree_level': deg_level,
                            'deg_slug': deg_slug,
                            'lang': lang,
                            'link': link
                        })
                print(f"  CU Page {p}: {len(items)} programs scraped")
            except Exception as ex:
                print(f"  Page {p} error: {ex}")
                break

    print(f"Total CU Programs scraped from central portal: {len(cu_programs)}")

    # Save to data directory
    out_path = os.path.join(backend_dir, "data", "cu_scraped_programmes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cu_programs, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")

    return cu_programs

if __name__ == "__main__":
    scrape_cu_tcas_and_programs()
