# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SWU_SOURCES = [
    ("สาขาวิชาภาษาตะวันออก", "http://g.hu.swu.ac.th/personal01", "swu_hum_oriental_ba_64426_67"),
    ("สาขาวิชาวรรณกรรมสำหรับเด็ก", "http://g.hu.swu.ac.th/personal02", "swu_hum_ba_language_for_career"),
    ("สาขาวิชาภาษาอังกฤษ", "http://g.hu.swu.ac.th/personal03", "swu_hum_eng_ba_63854_66"),
    ("สาขาวิชาปรัชญาเเละศาสนา", "http://g.hu.swu.ac.th/personal04", "swu_hum_ba_language_for_career"),
    ("สาขาวิชาภาษาไทย", "http://g.hu.swu.ac.th/personal05", "swu_hum_ba_language_for_career"),
    ("สาขาวิชาสารสนเทศศึกษา", "http://g.hu.swu.ac.th/personal06", "swu_hum_ba_language_for_career"),
    ("สาขาวิชาภาษาและวัฒนธรรมอาเซียน", "http://g.hu.swu.ac.th/personal07", "swu_hum_oriental_ba_64426_67"),
    ("สาขาวิชาจิตวิทยา", "http://g.hu.swu.ac.th/personal08", "swu_hum_ba_language_for_career"),
    ("สาขาวิชาการศึกษา (ภาษาไทย)", "http://g.hu.swu.ac.th/personal09", "swu_hum_ba_language_for_career"),
    ("บัณฑิตศึกษา สาขาวิชาภาษาอังกฤษ", "https://cgs.hu.swu.ac.th/people/en", "swu_hum_eng_ba_63854_66"),
    ("บัณฑิตศึกษา สาขาวิชาภาษาไทย", "https://cgs.hu.swu.ac.th/people/th", "swu_hum_ba_language_for_career"),
    ("คณะผู้บริหาร คณะมนุษยศาสตร์", "https://hu.swu.ac.th/boardhu", "swu_hum_ba_language_for_career"),
]

def extract_swu():
    faculty = []
    seen = set()

    for dept, url, course_id in SWU_SOURCES:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text(separator="\n")
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                for i, l in enumerate(lines):
                    # Check for Thai title + name pattern
                    # e.g. "ผศ.ดร. นันทนา วงษ์ไทย" or "ดร.สยุมพร ฉันทสิทธิพร"
                    m = re.search(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)(?:\s*ดร\.)?)\s*([ก-๙]{2,25})\s+([ก-๙]{2,25})', l)
                    if m:
                        title = m.group(1).strip()
                        fname = m.group(2).strip()
                        raw_lname = m.group(3).strip()

                        # Strip position junk from surname
                        lname = raw_lname
                        for sp in ["หัวหน้า", "ประธาน", "รองคณบดี", "คณบดี", "เลขานุการ", "อาจารย์", "ผู้ช่วย"]:
                            if sp in lname:
                                lname = lname.split(sp)[0].strip()

                        if len(fname) < 2 or len(lname) < 2:
                            continue

                        full_name_th = f"{title} {fname} {lname}".strip()
                        full_name_th = re.sub(r"\s+", " ", full_name_th)

                        key = f"{fname} {lname}"
                        if key in seen:
                            continue
                        seen.add(key)

                        # Look around for email
                        email = None
                        surrounding = " ".join(lines[max(0, i-2):min(len(lines), i+6)])
                        em = re.search(r'([a-zA-Z0-9._%+-]+@(?:g\.)?swu\.ac\.th)', surrounding)
                        if em:
                            email = em.group(1).lower()

                        faculty.append({
                            "academic_title_th": title,
                            "first_name_th": fname,
                            "last_name_th": lname,
                            "full_name_th": full_name_th,
                            "email": email,
                            "department_th": dept,
                            "faculty_th": "คณะมนุษยศาสตร์",
                            "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
                            "course_id": course_id,
                            "profile_url": url
                        })
                        print(f"  + [{len(faculty)}] {full_name_th} | Dept: {dept} | Email: {email}")

        except Exception as e:
            print(f"Error {url}: {e}")

    print(f"\nTotal authentic SWU Humanities extracted: {len(faculty)}")
    with open("swu_hu_verified.json", "w", encoding="utf-8") as f:
        json.dump(faculty, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extract_swu()
