import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

r = requests.get('https://reg.kmutnb.ac.th/registrar/program_info.asp', timeout=15, headers=headers, verify=False)
content = r.content.decode('cp874', errors='ignore')
soup = BeautifulSoup(content, 'html.parser')

print("Page HTML excerpt:")
print(content[:1500])

# find all links or frames
frames = soup.find_all(['frame', 'iframe'])
print(f"Frames: {len(frames)}")
for f in frames:
    print(f"  Frame src: {f.get('src')}")

links = soup.find_all('a', href=True)
print(f"Links: {len(links)}")
for a in links[:20]:
    print(f"  {a.get_text(strip=True)} -> {a['href']}")
