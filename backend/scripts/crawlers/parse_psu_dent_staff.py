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

SUFFIX_PATTERNS = [
    r"หัวหน้าอนุสาขาวิชา[^\n\r]*",
    r"หัวหน้าสาขาวิชา[^\n\r]*",
    r"รองหัวหน้าสาขาวิชา[^\n\r]*",
    r"รองหัวหน้า[^\n\r]*",
    r"ผู้ช่วยศาสตราจารย์[^\n\r]*",
    r"รองศาสตราจารย์[^\n\r]*",
    r"ศาสตราจารย์[^\n\r]*",
    r"ผู้ช่วยอาจารย์[^\n\r]*",
    r"อาจารย์พิเศษ[^\n\r]*",
    r"อาจารย์[^\n\r]*",
    r"\(ลาศึกษาต่อ\)",
    r"\(เกษียณอายุราชการ\)",
    r"Asst\.?\s*Prof\.?[^\n\r]*",
    r"Assoc\.?\s*Prof\.?[^\n\r]*",
    r"Prof\.?[^\n\r]*",
    r"Lect\.?[^\n\r]*",
    r"Dr\.?[^\n\r]*",
]

def clean_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_staff():
    all_staff = []
    seen_names = set()

    for dept, url in URLS:
        print(f"\nCrawling {dept}: {url}")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')

                # Look for all text blocks
                # We can find blocks that contain Thai titles
                # Titles in PSU Dent: ศ.ดร.ทพ., รศ.ดร.ทพ., ผศ.ดร.ทพ., อ.ดร.ทพ., ทพ., ทพญ., etc.
                pattern = re.compile(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ทพ\.|ทพญ\.|นพ\.|พญ\.)[^\n\r<]{3,80})')

                # Find all paragraph, td, div tags
                text = soup.get_text(separator="\n")
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                for i, line in enumerate(lines):
                    # Check if line starts with or contains an academic title
                    m = re.search(r'((?:ศ\.|รศ\.|ผศ\.|อ\.)(?:\s*ดร\.)?(?:\s*(?:ทพ\.|ทพญ\.|นพ\.|พญ\.))?|(?:ดร\.)?\s*(?:ทพ\.|ทพญ\.|นพ\.|พญ\.))\s*([ก-๙]{2,25})\s+([ก-๙]{2,25})', line)
                    if m:
                        title = m.group(1).strip()
                        fname = m.group(2).strip()
                        raw_lname = m.group(3).strip()

                        # Check if surname has junk attached
                        lname = raw_lname
                        for sp in [
                            "หัวหน้า", "รองหัวหน้า", "ผู้ช่วย", "อาจารย์", "ศาสตราจารย์",
                            "Asst", "Lect", "Dr", "viram", "tanapat", "("
                        ]:
                            if sp in lname:
                                lname = lname.split(sp)[0].strip()

                        # Ensure valid Thai name length
                        if len(fname) < 2 or len(lname) < 2:
                            continue

                        full_name_th = f"{title} {fname} {lname}".strip()
                        # Normalise title spaces
                        full_name_th = re.sub(r"\s+", " ", full_name_th)

                        # Filter out false positives
                        if any(bad in full_name_th for bad in ["หลังปริญญา", "ปริญญาตรี", "ทันตแพทย์", "สาขาวิชา", "คณะทันต"]):
                            continue

                        if f"{fname} {lname}" in seen_names:
                            continue
                        seen_names.add(f"{fname} {lname}")

                        # Look around line i for email and English name
                        email = None
                        en_name = None
                        surrounding = " ".join(lines[max(0, i-2):min(len(lines), i+8)])

                        email_m = re.search(r'([a-zA-Z0-9._%+-]+@(?:dent\.)?psu\.ac\.th)', surrounding)
                        if email_m:
                            email = email_m.group(1).lower()

                        en_m = re.search(r'(?:(?:Prof|Assoc\.?\s*Prof|Asst\.?\s*Prof|Lect\.?|Dr\.?)\s*(?:Dr\.?)?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', surrounding)
                        if en_m:
                            cand = en_m.group(1).strip()
                            if not any(bad in cand for bad in ["Prince Of", "Songkla", "Dentistry", "Faculty", "Staff", "Department"]):
                                en_name = cand

                        all_staff.append({
                            "academic_title_th": title,
                            "first_name_th": fname,
                            "last_name_th": lname,
                            "full_name_th": full_name_th,
                            "name_en": en_name,
                            "email": email,
                            "department_th": dept,
                            "faculty_th": "คณะทันตแพทยศาสตร์",
                            "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                            "profile_url": url
                        })
                        print(f"  [{len(all_staff)}] {full_name_th} | EN: {en_name} | Email: {email}")

        except Exception as e:
            print(f"Error {url}: {e}")

    print(f"\n==========================================")
    print(f"Total PSU Dentistry Faculty Extracted: {len(all_staff)}")
    print(f"==========================================")
    with open("psu_dent_parsed.json", "w", encoding="utf-8") as f:
        json.dump(all_staff, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parse_staff()
