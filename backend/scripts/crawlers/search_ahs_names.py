import sys, re, ssl
from pathlib import Path
import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import quote

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

targets = [
    ('ปิยะพงษ์ จันทร์ใหม่มูล', 'chulalongk_facultyofa_janmaimool_005'),
    ('นันทวัฒน์ อู่ดี', 'chulalongk_facultyofa_udee_017'),
    ('ดนัย วังสตุรค', 'chulalongk_facultyofa_wangsaturak_020'),
    ('ธีระวุฒิ จันทร์มี', 'chulalongk_facultyofa_chanmee_004'),
    ('ศุภชัย ตั้งวงศ์ศานต์', 'chulalongk_facultyofa_tangwongsan_027'),
    ('นภาพงษ์ พงษ์นภางค์', 'chulalongk_facultyofa_pongnapang_031'),
    ('มรกต ชาตาธิคุณ', 'chulalongk_facultyofa_chatathikun_009'),
    ('นวพร วรศิลป์ชัย', 'chulalongk_facultyofa_worasinchai_013'),
    ('นวลเพ็ญ ดำรงกิจอุดม', 'chulalongk_facultyofa_damrongkitudom_019'),
    ('วีระพงศ์ ปรัช', 'chulalongk_facultyofa_prach_006'),
    ('ปิติ เตชะวิจิตร์', 'chulalongk_facultyofa_techavichit_021'),
    ('ฐิติพงศ์ แก้วเหล็ก', 'chulalongk_facultyofa_kaewlek_018'),
    ('โยธิน รักวงษ์ไทย', 'chulalongk_facultyofa_rakvongthai_016')
]

for th_name, fid in targets:
    s_url = f"https://www.ahs.chula.ac.th/?s={quote(th_name)}"
    try:
        req = urllib.request.Request(s_url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        staff_links = soup.find_all('a', href=re.compile(r'/academic-staff/'))
        if staff_links:
            target_url = staff_links[0]['href']
            # Fetch staff page
            req2 = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req2, context=ssl_ctx, timeout=10) as resp2:
                p_html = resp2.read().decode('utf-8', errors='ignore')
            m = re.findall(r'[a-zA-Z0-9._%+-]+@chula\.ac\.th', p_html)
            clean_m = [e.lower() for e in set(m) if not any(k in e.lower() for k in ['saraban', 'contact', 'info'])]
            print(f"FOUND: {fid} | {th_name} -> {target_url} -> email: {clean_m}")
        else:
            # Check article snippets
            articles = soup.find_all('article')
            print(f"NOT FOUND: {fid} | {th_name} -> articles: {len(articles)}")
    except Exception as e:
        print(f"ERROR: {fid} | {th_name} -> {e}")
