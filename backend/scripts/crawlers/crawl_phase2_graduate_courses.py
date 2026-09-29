# -*- coding: utf-8 -*-
"""
Headless Autonomous Crawler for Phase 2 Graduate Courses (โท/เอก):
  1. Mahasarakham University (MSU - มหาวิทยาลัยมหาสารคาม)
  2. Burapha University (BUU - มหาวิทยาลัยบูรพา)
  3. Naresuan University (NU - มหาวิทยาลัยนเรศวร)
  4. Prince of Songkla University (PSU - มหาวิทยาลัยสงขลานครินทร์)
  5. Silpakorn University (SU - มหาวิทยาลัยศิลปากร)
  6. Ubon Ratchathani University (UBU - มหาวิทยาลัยอุบลราชธานี)

Outputs raw extracted courses to backend/data/agent_states/phase2_courses_raw.json.
"""
import os
import sys
import re
import json
import logging
import ssl
import io
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "phase2_courses_raw.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("crawl_phase2")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.read()
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None

# ==========================================
# 1. MSU Crawler
# ==========================================
def crawl_msu():
    logger.info("--- Starting MSU Graduate Course Crawl ---")
    courses = []
    base_url = "https://gradis.msu.ac.th/admission/admin_academic/apply/curricula?page={}"

    for page in range(1, 7):
        url = base_url.format(page)
        data = fetch_url(url)
        if not data:
            continue
        soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")

        for h3 in soup.find_all("h3"):
            th_title = h3.text.strip()
            if not th_title:
                continue

            parent = h3.find_parent("div", class_=lambda x: x and any(c in x for c in ["bg-white", "rounded", "border"]))
            card_text = parent.text if parent else ""

            en_title = ""
            for sib in h3.find_next_siblings(["p", "div", "span"]):
                txt = sib.text.strip()
                if txt and re.search(r"^[A-Za-z\s\(\)\.,'-]+$", txt) and len(txt) > 5:
                    en_title = txt
                    break

            fac_match = re.search(r"[🏛️\s]*คณะ([^\n\|]+)", card_text) or re.search(r"[🏛️\s]*วิทยาลัย([^\n\|]+)", card_text)
            if fac_match:
                fac_th = fac_match.group(0).replace("🏛️", "").strip()
            else:
                fac_th = "บัณฑิตวิทยาลัย"

            deg_level = "ปริญญาเอก" if ("ดุษฎีบัณฑิต" in th_title or "ปริญญาเอก" in card_text or "Doctor" in en_title or "Ph.D." in en_title) else "ปริญญาโท"
            dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"

            deg_name_m = re.search(r"\(([ก-ฮa-zA-Z\.]+)\)", th_title)
            deg_name = deg_name_m.group(1) if deg_name_m else ("ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต")

            courses.append({
                "title_th": th_title,
                "title_en": en_title,
                "degree_level": deg_level,
                "degree_name": deg_name,
                "university": "Mahasarakham University",
                "university_th": "มหาวิทยาลัยมหาสารคาม",
                "faculty": "",
                "faculty_th": fac_th,
                "department": "",
                "department_th": "",
                "duration_years": dur,
                "tuition_per_semester": "20,000 - 35,000 บาท",
                "tuition_total": "",
                "program_type": "ภาคปกติ",
                "description": f"{th_title} {en_title} {fac_th} มหาวิทยาลัยมหาสารคาม",
                "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยมหาสารคาม"],
                "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                "tags": [deg_level, fac_th, "มมส", "MSU"],
                "website_url": url
            })

    logger.info(f"MSU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 2. NU Crawler (Naresuan University)
# ==========================================
NU_FACULTIES = [
    (209, "คณะแพทยศาสตร์", "Faculty of Medicine"),
    (212, "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (213, "คณะทันตแพทยศาสตร์", "Faculty of Dentistry"),
    (211, "คณะวิทยาศาสตร์การแพทย์", "Faculty of Medical Science"),
    (204, "คณะเภสัชศาสตร์", "Faculty of Pharmaceutical Sciences"),
    (214, "คณะสหเวชศาสตร์", "Faculty of Allied Health Sciences"),
    (210, "คณะสาธารณสุขศาสตร์", "Faculty of Public Health"),
    (203, "คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม", "Faculty of Agriculture Natural Resources and Environment"),
    (215, "คณะสถาปัตยกรรมศาสตร์ ศิลปะและการออกแบบ", "Faculty of Architecture, Art and Design"),
    (207, "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (206, "คณะวิทยาศาสตร์", "Faculty of Science"),
    (123, "คณะโลจิสติกส์และดิจิทัลซัพพลายเชน", "Faculty of Logistics and Digital Supply Chain"),
    (120, "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี", "School of Renewable Energy Technology"),
    (124, "วิทยาลัยเพื่อการค้นคว้าระดับรากฐาน", "The Institute for Fundamental Study"),
    (218, "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "Faculty of Business, Economics and Communications"),
    (208, "คณะศึกษาศาสตร์", "Faculty of Education"),
    (217, "คณะมนุษยศาสตร์", "Faculty of Humanities"),
    (216, "คณะนิติศาสตร์", "Faculty of Law"),
    (219, "คณะสังคมศาสตร์", "Faculty of Social Sciences"),
    (196, "วิทยาลัยนานาชาติ", "Naresuan University International College")
]

def crawl_nu_course_detail(c_link, fac_th, fac_en):
    url = f"https://www.acad.nu.ac.th/course/{c_link}"
    data = fetch_url(url)
    if not data:
        return None
    soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")

    lines = [l.strip() for l in soup.text.split("\n") if l.strip()]
    th_title = ""
    en_title = ""
    duration = "2 ปี"
    tuition = ""

    for i, line in enumerate(lines):
        if "หลักสูตร" in line and any(k in line for k in ["มหาบัณฑิต", "ดุษฎีบัณฑิต"]):
            if not th_title:
                th_title = line
        elif re.search(r"^(Master|Doctor|Doctoral)\s+of", line, re.I):
            if not en_title:
                en_title = line
        elif "ระยะเวลาการศึกษา" in line and i + 1 < len(lines):
            duration = lines[i+1]
        elif "ค่าธรรมเนียมการศึกษา" in line and i + 1 < len(lines):
            tuition = lines[i+1]

    if not th_title:
        return None

    deg_level = "ปริญญาเอก" if ("ดุษฎีบัณฑิต" in th_title or "Doctor" in en_title or "levelid=3" in c_link) else "ปริญญาโท"
    deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

    return {
        "title_th": th_title,
        "title_en": en_title,
        "degree_level": deg_level,
        "degree_name": deg_name,
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": fac_en,
        "faculty_th": fac_th,
        "department": "",
        "department_th": "",
        "duration_years": duration if duration in ["2 ปี", "3 ปี", "4 ปี", "5 ปี"] else ("3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"),
        "tuition_per_semester": tuition or "25,000 บาท/ภาคการศึกษา",
        "tuition_total": "",
        "program_type": "ภาคปกติ",
        "description": f"{th_title} {en_title} {fac_th} มหาวิทยาลัยนเรศวร",
        "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยนเรศวร"],
        "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
        "tags": [deg_level, fac_th, "มน", "NU"],
        "website_url": url
    }

def crawl_nu():
    logger.info("--- Starting NU Graduate Course Crawl ---")
    courses = []

    tasks = []
    for fac_id, fac_th, fac_en in NU_FACULTIES:
        url = f"https://www.acad.nu.ac.th/course/faculty.php?facultyid={fac_id}"
        data = fetch_url(url)
        if not data:
            continue
        soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "course.php?" in href and ("levelid=2" in href or "levelid=3" in href):
                tasks.append((href, fac_th, fac_en))

    logger.info(f"NU found {len(tasks)} graduate course links across 20 faculties. Fetching details...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(crawl_nu_course_detail, h, fth, fen): h for h, fth, fen in tasks}
        for future in as_completed(futures):
            res = future.result()
            if res:
                courses.append(res)

    logger.info(f"NU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 3. SU Crawler (Silpakorn University)
# ==========================================
SU_DEPTS = [
    (1, "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "Faculty of Painting, Sculpture and Graphic Arts"),
    (2, "คณะสถาปัตยกรรมศาสตร์", "Faculty of Architecture"),
    (3, "คณะโบราณคดี", "Faculty of Archaeology"),
    (4, "คณะมัณฑนศิลป์", "Faculty of Decorative Arts"),
    (5, "คณะอักษรศาสตร์", "Faculty of Arts"),
    (6, "คณะศึกษาศาสตร์", "Faculty of Education"),
    (7, "คณะวิทยาศาสตร์", "Faculty of Science"),
    (8, "คณะเภสัชศาสตร์", "Faculty of Pharmacy"),
    (9, "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "Faculty of Engineering and Industrial Technology"),
    (10, "คณะดุริยางคศาสตร์", "Faculty of Music"),
    (11, "คณะสัตวศาสตร์และเทคโนโลยีการเกษตร", "Faculty of Animal Sciences and Agricultural Technology"),
    (12, "คณะวิทยาการจัดการ", "Faculty of Management Science"),
    (13, "คณะเทคโนโลยีสารสนเทศและการสื่อสาร", "Faculty of Information and Communication Technology")
]

def crawl_su():
    logger.info("--- Starting SU Graduate Course Crawl ---")
    courses = []

    for dept_id, fac_th, fac_en in SU_DEPTS:
        url = f"https://graduate.su.ac.th/course-detail.php?dept={dept_id:02d}"
        data = fetch_url(url)
        if not data:
            continue
        soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")

        boxes = soup.find_all("div", class_="box_course")
        seen_in_dept = set()
        for box in boxes:
            lines = [l.strip() for l in box.text.split("\n") if l.strip()]
            for line in lines:
                if any(k in line for k in ["มหาบัณฑิต", "ดุษฎีบัณฑิต"]):
                    th_title = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                    if "ไม่มีหลักสูตร" in th_title or len(th_title) < 10 or th_title in seen_in_dept:
                        continue
                    seen_in_dept.add(th_title)

                    deg_level = "ปริญญาเอก" if "ดุษฎีบัณฑิต" in th_title else "ปริญญาโท"
                    dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"
                    deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                    courses.append({
                        "title_th": th_title,
                        "title_en": "",
                        "degree_level": deg_level,
                        "degree_name": deg_name,
                        "university": "Silpakorn University",
                        "university_th": "มหาวิทยาลัยศิลปากร",
                        "faculty": fac_en,
                        "faculty_th": fac_th,
                        "department": "",
                        "department_th": "",
                        "duration_years": dur,
                        "tuition_per_semester": "25,000 - 45,000 บาท",
                        "tuition_total": "",
                        "program_type": "ภาคปกติ",
                        "description": f"{th_title} {fac_th} มหาวิทยาลัยศิลปากร",
                        "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยศิลปากร"],
                        "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                        "tags": [deg_level, fac_th, "มศก", "SU"],
                        "website_url": url
                    })

    logger.info(f"SU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 4. UBU Crawler (Ubon Ratchathani University)
# ==========================================
UBU_FACULTIES = [
    (11, "คณะวิทยาศาสตร์", "Faculty of Science"),
    (12, "คณะเกษตรศาสตร์", "Faculty of Agriculture"),
    (13, "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (14, "คณะศิลปศาสตร์", "Faculty of Liberal Arts"),
    (15, "คณะเภสัชศาสตร์", "Faculty of Pharmaceutical Sciences"),
    (17, "คณะบริหารศาสตร์", "Faculty of Management Science"),
    (18, "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (19, "วิทยาลัยแพทยศาสตร์และการสาธารณสุข", "College of Medicine and Public Health"),
    (20, "คณะศิลปประยุกต์และสถาปัตยกรรมศาสตร์", "Faculty of Applied Arts and Architecture"),
    (21, "คณะนิติศาสตร์", "Faculty of Law"),
    (23, "คณะรัฐศาสตร์", "Faculty of Political Science"),
    (26, "คณะศึกษาศาสตร์", "Faculty of Education")
]

def crawl_ubu():
    logger.info("--- Starting UBU Graduate Course Crawl ---")
    courses = []

    for fac_id, fac_th, fac_en in UBU_FACULTIES:
        url = f"https://www.ubu.ac.th/UBU2025/course_faculty.php?id={fac_id}"
        data = fetch_url(url)
        if not data:
            continue
        soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")

        accordions = soup.find_all("div", class_="accrodion-title")
        for title_div in accordions:
            degree_header = title_div.text.strip()
            if not any(k in degree_header for k in ["มหาบัณฑิต", "ดุษฎีบัณฑิต"]):
                continue

            deg_level = "ปริญญาเอก" if "ดุษฎีบัณฑิต" in degree_header else "ปริญญาโท"
            dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"
            deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

            content_div = title_div.find_next_sibling("div", class_=lambda x: x and "content" in x)
            if not content_div:
                continue

            raw_text = content_div.text
            major_blocks = re.split(r"สาขา", raw_text)
            for block in major_blocks:
                block = block.strip()
                if not block:
                    continue
                m_name = block.split("\n")[0].strip()
                m_name = re.sub(r"ค่าธรรมเนียม.*$", "", m_name).strip()
                if not m_name or len(m_name) < 2:
                    continue

                fee_match = re.search(r"ค่าธรรมเนียมการศึกษาต่อเทอม\s*:\s*([^\n]+)", block)
                tuition = fee_match.group(1).strip() if fee_match else "18,000 - 30,000 บาท"

                dur_match = re.search(r"ระยะเวลาการศึกษา\s*:\s*([^\n]+)", block)
                if dur_match:
                    dur_val = dur_match.group(1).strip()
                    if any(d in dur_val for d in ["2 ปี", "3 ปี", "4 ปี"]):
                        dur = dur_val

                full_title = f"หลักสูตร{degree_header} สาขาวิชา{m_name}"
                courses.append({
                    "title_th": full_title,
                    "title_en": "",
                    "degree_level": deg_level,
                    "degree_name": deg_name,
                    "university": "Ubon Ratchathani University",
                    "university_th": "มหาวิทยาลัยอุบลราชธานี",
                    "faculty": fac_en,
                    "faculty_th": fac_th,
                    "department": "",
                    "department_th": "",
                    "duration_years": dur,
                    "tuition_per_semester": tuition,
                    "tuition_total": "",
                    "program_type": "ภาคปกติ",
                    "description": f"{full_title} {fac_th} มหาวิทยาลัยอุบลราชธานี",
                    "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยอุบลราชธานี"],
                    "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                    "tags": [deg_level, fac_th, "มอบ", "UBU"],
                    "website_url": url
                })

    logger.info(f"UBU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 5. BUU Crawler (Burapha University)
# ==========================================
BUU_FACULTY_RULES = [
    (r"วิทยาการสารสนเทศ|สารสนเทศ|วิทยาการข้อมูล", "คณะวิทยาการสารสนเทศ", "Faculty of Informatics"),
    (r"โลจิสติกส์", "คณะโลจิสติกส์", "Faculty of Logistics"),
    (r"เภสัช", "คณะเภสัชศาสตร์", "Faculty of Pharmaceutical Sciences"),
    (r"พยาบาล", "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (r"วิศวกรรม", "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (r"วิทยาศาสตร์|วาริช|เคมี|ฟิสิกส์|ชีว|คณิต|สถิติ", "คณะวิทยาศาสตร์", "Faculty of Science"),
    (r"ศึกษาศาสตร์|การสอน|กศ\.|หลักสูตรและการสอน", "คณะศึกษาศาสตร์", "Faculty of Education"),
    (r"นิติศาสตร์", "คณะนิติศาสตร์", "Faculty of Law"),
    (r"รัฐศาสตร์", "คณะรัฐศาสตร์และนิติศาสตร์", "Faculty of Political Science and Law"),
    (r"ศิลปกรรม|ทัศนศิลป์", "คณะศิลปกรรมศาสตร์", "Faculty of Fine and Applied Arts"),
    (r"ดนตรี|การแสดง", "คณะดนตรีและการแสดง", "Faculty of Music and Performing Arts"),
    (r"มนุษยศาสตร์|สังคมศาสตร์|ภาษา", "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences"),
    (r"สาธารณสุข", "คณะสาธารณสุขศาสตร์", "Faculty of Public Health"),
    (r"พาณิชยศาสตร์|บริหารธุรกิจ", "วิทยาลัยพาณิชยศาสตร์", "Graduate School of Commerce"),
    (r"วิทยาศาสตร์การกีฬา", "คณะวิทยาศาสตร์การกีฬา", "Faculty of Allied Health and Sport Science"),
    (r"เทคโนโลยีทางทะเล", "คณะเทคโนโลยีทางทะเล", "Faculty of Marine Technology"),
    (r"ภูมิสารสนเทศ", "คณะภูมิสารสนเทศศาสตร์", "Faculty of Geoinformatics"),
]

def crawl_buu():
    logger.info("--- Starting BUU Graduate Course Crawl ---")
    courses = []
    admission_hub = "https://grd.buu.ac.th/admission-information/"
    data = fetch_url(admission_hub)
    if not data:
        return courses

    soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")
    targets = []
    for a in soup.find_all("a", href=True):
        t = a.text.strip()
        h = a["href"]
        if t in ["ปริญญาโท", "ปริญญาเอก"]:
            parent = a.find_parent("tr") or a.find_parent("div")
            ctx_txt = parent.text.strip().replace("\n", " ") if parent else ""
            targets.append((t, h, ctx_txt))

    logger.info(f"BUU found {len(targets)} admission target links. Fetching details...")

    seen_titles = set()
    for deg_level, page_url, ctx_txt in targets:
        p_data = fetch_url(page_url)
        if not p_data:
            continue
        p_soup = BeautifulSoup(p_data.decode("utf-8", "ignore"), "html.parser")

        for el in p_soup.find_all(["li", "p", "a", "td"]):
            txt = el.text.strip().replace("\n", " ")
            if any(k in txt for k in ["มหาบัณฑิต", "ดุษฎีบัณฑิต"]) and len(txt) < 140:
                cleaned = re.sub(r"^\d+[\.\)]\s*", "", txt).strip()
                if not cleaned or any(ign in cleaned for ign in ["ระเบียบ", "ประกาศ", "คู่มือ", "คำร้อง", "หน้าหลัก", "ติดต่อ"]):
                    continue
                if cleaned in seen_titles:
                    continue
                seen_titles.add(cleaned)

                # Attribute faculty from context or title
                fac_th = "บัณฑิตวิทยาลัย"
                fac_en = "Graduate School"
                combined = f"{ctx_txt} {cleaned}"
                for pat, fth, fen in BUU_FACULTY_RULES:
                    if re.search(pat, combined):
                        fac_th = fth
                        fac_en = fen
                        break

                dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"
                deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                courses.append({
                    "title_th": cleaned,
                    "title_en": "",
                    "degree_level": deg_level,
                    "degree_name": deg_name,
                    "university": "Burapha University",
                    "university_th": "มหาวิทยาลัยบูรพา",
                    "faculty": fac_en,
                    "faculty_th": fac_th,
                    "department": "",
                    "department_th": "",
                    "duration_years": dur,
                    "tuition_per_semester": "25,000 - 45,000 บาท",
                    "tuition_total": "",
                    "program_type": "ภาคปกติ",
                    "description": f"{cleaned} {fac_th} มหาวิทยาลัยบูรพา",
                    "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยบูรพา"],
                    "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                    "tags": [deg_level, fac_th, "มบบ", "BUU"],
                    "website_url": page_url
                })

    logger.info(f"BUU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 6. PSU Crawler (Prince of Songkla University)
# ==========================================
PSU_FACULTY_MAP = [
    (r"การจัดการทองเที่ยว|การท่องเที่ยว|การบริการและการท่องเที่ยว", "คณะการบริการและการท่องเที่ยว", "Faculty of Hospitality and Tourism"),
    (r"การจัดการทรัพยากรทะเล|ทรัพยากรทางทะเล", "คณะเทคโนโลยีและสิ่งแวดล้อม", "Faculty of Technology and Environment"),
    (r"การแพทยแผนไทย|การแพทย์แผนไทย", "คณะการแพทย์แผนไทย", "Faculty of Traditional Thai Medicine"),
    (r"เกษตร|พืชศาสตร์|พืชศาสตร|สัตวศาสตร์|ปฐพี|กีฏ", "คณะทรัพยากรธรรมชาติ", "Faculty of Natural Resources"),
    (r"ทันต|สุขภาพช่องปาก", "คณะทันตแพทยศาสตร์", "Faculty of Dentistry"),
    (r"พยาบาล", "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (r"แพทย|กายวิภาค|สรีร|พยาธิ|ชีวเคมีทางการแพทย์|วิทยาศาสตร์การแพทย์", "คณะแพทยศาสตร์", "Faculty of Medicine"),
    (r"เภสัช", "คณะเภสัชศาสตร์", "Faculty of Pharmaceutical Sciences"),
    (r"วิศวกรรม|โยธา|เครื่องกล|ไฟฟ้า|คอมพิวเตอร์|เคมี|เหมืองแร่", "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (r"เคมี|ฟิสิกส์|ชีว|คณิต|วิทยาการคอมพิวเตอร์|วัสดุ|วิทยาศาสตร์|สถิติ", "คณะวิทยาศาสตร์", "Faculty of Science"),
    (r"อุตสาหกรรมเกษตร|เทคโนโลยีชีวภาพ|เทคโนโลยีอาหาร|บรรจุภัณฑ์|อาหารเพื่อสุขภาพ", "คณะอุตสาหกรรมเกษตร", "Faculty of Agro-Industry"),
    (r"วิทยาการจัดการ|บริหารธุรกิจ|การบัญชี|การตลาด|การเงิน|การจัดการ", "คณะวิทยาการจัดการ", "Faculty of Management Sciences"),
    (r"เศรษฐศาสตร์", "คณะเศรษฐศาสตร์", "Faculty of Economics"),
    (r"นิติศาสตร์", "คณะนิติศาสตร์", "Faculty of Law"),
    (r"รัฐศาสตร์|รัฐประศาสน", "คณะรัฐศาสตร์", "Faculty of Political Science"),
    (r"ศึกษาศาสตร์|การศึกษา", "คณะศึกษาศาสตร์", "Faculty of Education"),
    (r"มนุษยศาสตร์|สังคมศาสตร์|ภาษาไทย|ภาษาอังกฤษ|พัฒนามนุษย์", "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences"),
    (r"อิสลามศึกษา", "วิทยาลัยอิสลามศึกษา", "College of Islamic Studies"),
    (r"ศิลปศาสตร์", "คณะศิลปศาสตร์", "Faculty of Liberal Arts"),
    (r"สิ่งแวดล้อม", "คณะการจัดการสิ่งแวดล้อม", "Faculty of Environmental Management"),
]

def crawl_psu():
    logger.info("--- Starting PSU Graduate Course Crawl ---")
    courses = []

    pdf_base = "https://admission.psu.ac.th/wp-content/uploads/2025/11/"
    pdf_name = "doc-ประกาศรับสมัครสอบคัดเลือก2569.pdf"
    pdf_url = pdf_base + urllib.parse.quote(pdf_name)

    pdf_data = fetch_url(pdf_url)
    if pdf_data:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_data))
            logger.info(f"PSU PDF downloaded, total pages: {len(reader.pages)}")

            for p in range(4, min(7, len(reader.pages))):
                txt = reader.pages[p].extract_text()
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                for line in lines:
                    m = re.match(r"(ป\.(?:โท|เอก))\s+(.*?)(?:\s+(?:เปดรับ|เปิดรับ|X|\d+))", line)
                    if m:
                        deg_tag = m.group(1).strip()
                        raw_major = m.group(2).strip()

                        raw_major = raw_major.replace("ทองเที่ยว", "ท่องเที่ยว")
                        raw_major = raw_major.replace("ฝง", "ฝั่ง")
                        raw_major = raw_major.replace("แพทย", "แพทย์")
                        raw_major = raw_major.replace("ศาสตร", "ศาสตร์")
                        raw_major = raw_major.replace("คณิตศาสตร", "คณิตศาสตร์")
                        raw_major = raw_major.replace("อยางยั่งยืน", "อย่างยั่งยืน")

                        deg_level = "ปริญญาเอก" if deg_tag == "ป.เอก" else "ปริญญาโท"
                        deg_prefix = "ปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                        if "มหาบัณฑิต" in raw_major or "ดุษฎีบัณฑิต" in raw_major:
                            th_title = f"หลักสูตร{raw_major}"
                        else:
                            th_title = f"หลักสูตร{deg_prefix} สาขาวิชา{raw_major}"

                        fac_th = "บัณฑิตวิทยาลัย"
                        fac_en = "Graduate School"
                        for pat, fth, fen in PSU_FACULTY_MAP:
                            if re.search(pat, raw_major):
                                fac_th = fth
                                fac_en = fen
                                break

                        dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"
                        deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                        courses.append({
                            "title_th": th_title,
                            "title_en": "",
                            "degree_level": deg_level,
                            "degree_name": deg_name,
                            "university": "Prince of Songkla University",
                            "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                            "faculty": fac_en,
                            "faculty_th": fac_th,
                            "department": "",
                            "department_th": "",
                            "duration_years": dur,
                            "tuition_per_semester": "25,000 - 45,000 บาท",
                            "tuition_total": "",
                            "program_type": "ภาคปกติ",
                            "description": f"{th_title} {fac_th} มหาวิทยาลัยสงขลานครินทร์",
                            "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยสงขลานครินทร์"],
                            "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                            "tags": [deg_level, fac_th, "ม.อ.", "PSU"],
                            "website_url": pdf_url
                        })
        except Exception as e:
            logger.error(f"Error parsing PSU PDF: {e}")

    list_thai_url = "https://admission.psu.ac.th/list-thai/"
    lt_data = fetch_url(list_thai_url)
    if lt_data:
        soup = BeautifulSoup(lt_data.decode("utf-8", "ignore"), "html.parser")
        for a in soup.find_all("a", href=True):
            t = a.text.strip().replace("\n", " ")
            if any(k in t for k in ["สาขาวิชา", "มหาบัณฑิต", "ดุษฎีบัณฑิต"]) and len(t) < 120:
                deg_level = "ปริญญาเอก" if ("ป.เอก" in a["href"] or "ดุษฎีบัณฑิต" in t) else "ปริญญาโท"
                deg_prefix = "ปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                if "มหาบัณฑิต" in t or "ดุษฎีบัณฑิต" in t:
                    th_title = f"หลักสูตร{t}"
                else:
                    th_title = f"หลักสูตร{deg_prefix} {t}"

                fac_th = "บัณฑิตวิทยาลัย"
                fac_en = "Graduate School"
                for pat, fth, fen in PSU_FACULTY_MAP:
                    if re.search(pat, t):
                        fac_th = fth
                        fac_en = fen
                        break

                dur = "3 ปี" if deg_level == "ปริญญาเอก" else "2 ปี"
                deg_name = "ปร.ด." if deg_level == "ปริญญาเอก" else "มหาบัณฑิต"

                courses.append({
                    "title_th": th_title,
                    "title_en": "",
                    "degree_level": deg_level,
                    "degree_name": deg_name,
                    "university": "Prince of Songkla University",
                    "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                    "faculty": fac_en,
                    "faculty_th": fac_th,
                    "department": "",
                    "department_th": "",
                    "duration_years": dur,
                    "tuition_per_semester": "25,000 - 45,000 บาท",
                    "tuition_total": "",
                    "program_type": "ภาคปกติ",
                    "description": f"{th_title} {fac_th} มหาวิทยาลัยสงขลานครินทร์",
                    "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยสงขลานครินทร์"],
                    "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัย", "ผู้เชี่ยวชาญเฉพาะทาง"],
                    "tags": [deg_level, fac_th, "ม.อ.", "PSU"],
                    "website_url": list_thai_url
                })

    logger.info(f"PSU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# Main Execution
# ==========================================
def main():
    logger.info("=== Starting Phase 2 Graduate Course Autonomous Crawl ===")
    all_courses = []

    msu = crawl_msu()
    all_courses.extend(msu)

    nu = crawl_nu()
    all_courses.extend(nu)

    su = crawl_su()
    all_courses.extend(su)

    ubu = crawl_ubu()
    all_courses.extend(ubu)

    buu = crawl_buu()
    all_courses.extend(buu)

    psu = crawl_psu()
    all_courses.extend(psu)

    logger.info(f"=== Crawl Summary across 6 Universities ===")
    logger.info(f"  MSU: {len(msu)}")
    logger.info(f"  NU : {len(nu)}")
    logger.info(f"  SU : {len(su)}")
    logger.info(f"  UBU: {len(ubu)}")
    logger.info(f"  BUU: {len(buu)}")
    logger.info(f"  PSU: {len(psu)}")
    logger.info(f"  Total Raw Extracted: {len(all_courses)}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Successfully checkpointed raw courses to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
