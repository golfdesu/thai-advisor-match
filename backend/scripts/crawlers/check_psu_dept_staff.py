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

URLS = [
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ทันตกรรมหัตถการ)", "https://www.dent.psu.ac.th/unit/conser/index.php/operative_dentistry/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (วิทยาเอ็นโดดอนต์)", "https://www.dent.psu.ac.th/unit/conser/index.php/endodontics/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ปริทันตวิทยา)", "https://www.dent.psu.ac.th/unit/conser/index.php/periodontology/"),
    ("สาขาวิชาชีววิทยาช่องปาก", "https://www.dent.psu.ac.th/unit/oral/index.php/staff/"),
    ("สาขาวิชาทันตกรรมป้องกัน", "https://www.dent.psu.ac.th/unit/prevent/index.php/staff/"),
    ("สาขาวิชาทันตกรรมประดิษฐ์", "https://www.dent.psu.ac.th/unit/prost/staff/"),
    ("สาขาวิชาโอษฐวิทยา", "https://www.dent.psu.ac.th/unit/stoma/index.php/staff/"),
    ("สาขาวิชาศัลยศาสตร์ช่องปากและแม็กซิลโลเฟเชียล", "https://www.dent.psu.ac.th/unit/surgery/index.php/staff/")
]

TITLE_RE = re.compile(r'^(ศ\.|รศ\.|ผศ\.|อ\.|ทพ\.|ทพญ\.|นพ\.|พญ\.)')

def clean_academic_title(raw_title):
    raw_title = raw_title.strip()
    return re.sub(r"\s+", "", raw_title)

def extract_all():
    faculty_records = []
    seen_th_names = set()

    for dept, url in URLS:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            soup = BeautifulSoup(resp.read(), 'html.parser')
            lines = [l.strip() for l in soup.get_text(separator='\n').split('\n') if l.strip()]

            i = 0
            while i < len(lines):
                line = lines[i]

                # Check if line starts with an academic title
                if TITLE_RE.match(line) and not any(b in line for b in ["หลังปริญญา", "ปริญญาตรี", "ทันตแพทย์"]):
                    # Parse line: could be "รศ.ดร.ทพ.บัญชา" OR "อ. ดร. ทพญ. สมจินต์ รัตนเสถียร"
                    # Split title and Thai name
                    # Title matches prefix
                    m_title = re.match(r'^((?:ศ\.|รศ\.|ผศ\.|อ\.)?(?:\s*ดร\.)?(?:\s*(?:ทพ\.|ทพญ\.|นพ\.|พญ\.))?|(?:ดร\.)?\s*(?:ทพ\.|ทพญ\.|นพ\.|พญ\.)|\bทพญ?\b\.?)\s*(.*)', line)
                    if m_title:
                        title_part = m_title.group(1).strip()
                        name_part = m_title.group(2).strip()

                        # If name_part has spaces, it might be "First Last"
                        fname = ""
                        lname = ""
                        if " " in name_part:
                            parts = [p.strip() for p in name_part.split() if p.strip()]
                            fname = parts[0]
                            lname = " ".join(parts[1:])
                        else:
                            # Name part is just first name; check next line for surname
                            fname = name_part
                            if i + 1 < len(lines):
                                next_line = lines[i+1]
                                # Check if next line is Thai surname
                                if re.match(r'^[ก-๙]{2,25}$', next_line):
                                    lname = next_line
                                    i += 1  # consumed surname
                                elif re.match(r'^[ก-๙]{2,25}\s+[ก-๙]{2,25}$', next_line):
                                    # Could be first + last if name_part was empty
                                    if not fname:
                                        p = next_line.split()
                                        fname, lname = p[0], p[1]
                                        i += 1

                        # Clean surname if it has junk
                        for sp in ["หัวหน้า", "รองหัวหน้า", "ผู้ช่วย", "อาจารย์", "ศาสตราจารย์", "Asst", "Lect", "Dr"]:
                            if sp in lname:
                                lname = lname.split(sp)[0].strip()

                        if fname and lname and len(fname) >= 2 and len(lname) >= 2:
                            # Normalize title
                            norm_title = re.sub(r"\s+", "", title_part)
                            full_name_th = f"{norm_title} {fname} {lname}"

                            if f"{fname} {lname}" not in seen_th_names:
                                seen_th_names.add(f"{fname} {lname}")

                                # Scan next 8 lines for English name and email
                                email = None
                                en_first = None
                                en_last = None

                                window = lines[i+1:min(len(lines), i+9)]
                                for w in window:
                                    # Email
                                    em = re.search(r'([a-zA-Z0-9._%+-]+@(?:dent\.)?psu\.ac\.th)', w)
                                    if em and not email:
                                        email = em.group(1).lower()

                                    # English name in parentheses or standalone
                                    # e.g. "(Associate Professor Dr.Nattapon Rotpenpian)" or "Dr. Somjin Ratanasathien, D.D.S."
                                    en_m = re.search(r'(?:(?:Prof|Assoc\.?\s*Prof|Asst\.?\s*Prof|Lect\.?|Dr\.?)\s*(?:Dr\.?)?\s*)?([A-Z][a-z]+)\s+([A-Z][a-z]+)', w)
                                    if en_m and not en_first:
                                        c1, c2 = en_m.group(1), en_m.group(2)
                                        if c1 not in ["Prince", "Songkla", "Faculty", "Staff", "Department", "Thai", "American", "Doctor", "Dental"]:
                                            en_first = c1
                                            en_last = c2

                                faculty_records.append({
                                    "academic_title_th": norm_title,
                                    "first_name_th": fname,
                                    "last_name_th": lname,
                                    "full_name_th": full_name_th,
                                    "first_name": en_first,
                                    "last_name": en_last,
                                    "email": email,
                                    "department_th": dept,
                                    "faculty_th": "คณะทันตแพทยศาสตร์",
                                    "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                                    "profile_url": url
                                })
                                print(f"[{len(faculty_records)}] {full_name_th} | EN: {en_first} {en_last} | Email: {email}")

                i += 1

    print(f"\n==========================================")
    print(f"Total authentic PSU Dentistry faculty parsed: {len(faculty_records)}")
    print(f"==========================================")
    with open("psu_dent_verified.json", "w", encoding="utf-8") as f:
        json.dump(faculty_records, f, ensure_ascii=False, indent=2)

extract_all()
