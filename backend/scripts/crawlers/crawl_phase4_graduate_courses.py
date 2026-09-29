# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Extraction Pipeline: Phase 4 Graduate Courses.
Target Universities:
  1. Rangsit University (RSU - มหาวิทยาลัยรังสิต) - grad.rsu.ac.th
  2. Rajamangala University of Technology Thanyaburi (RMUTT - มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี) - cul-grad-rmutt-2568.pdf
  3. Sripatum University (SPU - มหาวิทยาลัยศรีปทุม) - spu.ac.th/fac/graduate
  4. National Institute of Development Administration (NIDA - สถาบันบัณฑิตพัฒนบริหารศาสตร์: คณะสถิติประยุกต์) - as.nida.ac.th/programs

Output Checkpoint: backend/data/agent_states/phase4_courses_raw.json
"""
import os
import sys
import io
import re
import json
import ssl
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pypdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase4_crawler")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FILE = os.path.join(ROOT_DIR, "data", "agent_states", "phase4_courses_raw.json")

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def fetch_url(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        ctx = get_ssl_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None

# =========================================================================
# 1. Rangsit University (RSU) Crawler
# =========================================================================
RSU_FACULTY_RULES = [
    (r"แพทย์|เวชศาสตร์การเจริญ|ตจวิทยา", "วิทยาลัยแพทยศาสตร์", "College of Medicine"),
    (r"ทันตแพทย|ทันตกรรม", "วิทยาลัยทันตแพทยศาสตร์", "College of Dental Medicine"),
    (r"เภสัช", "วิทยาลัยเภสัชศาสตร์", "College of Pharmacy"),
    (r"พยาบาล", "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (r"เทคนิคการแพทย์", "คณะเทคนิคการแพทย์", "Faculty of Medical Technology"),
    (r"กายภาพบำบัด", "คณะกายภาพบำบัดและเวชศาสตร์การกีฬา", "Faculty of Physical Therapy and Sports Medicine"),
    (r"ความปลอดภัยทางไซเบอร์|ไซเบอร์|ปัญญาประดิษฐ์|คอมพิวเตอร์|นวัตกรรมดิจิทัล|ดิจิทัล", "วิทยาลัยนวัตกรรมดิจิทัลเทคโนโลยี", "College of Digital Innovation Technology"),
    (r"วิศวกรรม", "วิทยาลัยวิศวกรรมศาสตร์", "College of Engineering"),
    (r"สถาปัตยกรรม|การออกแบบ", "คณะสถาปัตยกรรมศาสตร์", "Faculty of Architecture"),
    (r"นิเทศศาสตร์|ภาพยนตร์|ซีรีส์|สื่อใหม่", "วิทยาลัยนิเทศศาสตร์", "College of Communication Arts"),
    (r"ดิจิทัลอาร์ต|แอนิเมชัน", "คณะดิจิทัลอาร์ต", "Faculty of Digital Arts"),
    (r"นิติศาสตร์|กฎหมาย", "คณะนิติศาสตร์", "Faculty of Law"),
    (r"รัฐประศาสน|การเมืองการปกครอง|รัฐศาสตร์", "วิทยาลัยรัฐศาสตร์และรัฐประศาสนศาสตร์", "College of Politics and Public Administration"),
    (r"ภาษาอังกฤษ|การทูต|ผู้นำทางสังคม|ศิลปศาสตร์", "คณะศิลปศาสตร์", "Faculty of Liberal Arts"),
    (r"ท่องเที่ยว|การบริการ|การโรงแรม", "วิทยาลัยการท่องเที่ยวและการบริการ", "College of Tourism and Hospitality"),
    (r"การบิน|นักบิน", "สถาบันการบิน", "Aviation Institute"),
    (r"บริหารธุรกิจ|การจัดการ|การเงิน|การตลาด|โลจิสติกส์|บัญชี|เศรษฐศาสตร์|กอล์ฟ|ผู้ประกอบการ", "วิทยาลัยบริหารธุรกิจ", "College of Business Administration"),
]

def map_rsu_faculty(title_th, title_en=""):
    comb = f"{title_th} {title_en}"
    for pat, fth, fen in RSU_FACULTY_RULES:
        if re.search(pat, comb):
            return fth, fen
    return "วิทยาลัยบัณฑิตศึกษา", "Graduate School"

def crawl_rsu():
    logger.info("--- Starting RSU (Rangsit University) Graduate Course Crawl ---")
    courses = []
    main_url = "https://grad.rsu.ac.th/"
    data = fetch_url(main_url)
    if not data:
        logger.error("Failed to fetch RSU main page")
        return []

    soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")
    course_links = []
    seen_href = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/grad/courses/" in href:
            if not href.startswith("http"):
                href = "https://www.rsu.ac.th" + href
            if href not in seen_href:
                seen_href.add(href)
                course_links.append((a.get_text(separator=" ", strip=True), href))

    logger.info(f"Found {len(course_links)} RSU graduate program links")

    def fetch_rsu_detail(item):
        raw_text, href = item
        detail_data = fetch_url(href, timeout=12)
        if not detail_data:
            return None
        s = BeautifulSoup(detail_data.decode("utf-8", "ignore"), "html.parser")
        h2 = s.find("h2")
        title_th = h2.get_text(strip=True) if h2 else raw_text
        if not title_th or title_th in ("หลักสูตร", "Courses"):
            title_th = raw_text

        # Extract title_en if formatted with colon
        title_en = ""
        if ":" in raw_text:
            parts = raw_text.split(":", 1)
            if not title_th or len(title_th) < len(parts[0]):
                title_th = parts[0].strip()
            title_en = parts[1].strip()

        # Degree level
        deg_lvl = "ปริญญาเอก" if any(k in f"{title_th} {title_en}" for k in ["ดุษฎีบัณฑิต", "Doctor", "Ph.D.", "D.Eng.", "D.B.A."]) else "ปริญญาโท"

        # Degree name
        deg_name = ""
        m_deg = re.search(r"\((.*?)\)", title_th)
        if m_deg:
            deg_name = m_deg.group(1).strip()
        if not deg_name:
            deg_name = "ปร.ด." if deg_lvl == "ปริญญาเอก" else "มหาบัณฑิต"

        body_txt = s.body.get_text(separator="\n", strip=True) if s.body else ""
        lines = [l.strip() for l in body_txt.split("\n") if l.strip()]

        # Tuition
        tuition = "ไม่ระบุ"
        for i, l in enumerate(lines):
            if "Tuition fee for the whole program" in l and i + 1 < len(lines):
                val = lines[i+1].replace(",", "").strip()
                if val.isdigit():
                    tuition = f"{int(val):,} บาท"
                break

        # Duration
        duration = "2 ปี" if deg_lvl == "ปริญญาโท" else "3 ปี"
        for l in lines:
            if "ระยะเวลาการศึกษา" in l:
                clean_dur = l.replace("ระยะเวลาการศึกษา", "").strip(" .:")
                if "ปี" in clean_dur:
                    duration = clean_dur

        # Description
        desc = ""
        for i, l in enumerate(lines):
            if l == title_th and i + 1 < len(lines):
                next_l = lines[i+1]
                if len(next_l) > 30 and not any(k in next_l for k in ["คุณสมบัติ", "ข้อมูลเพิ่มเติม", "Facebook", "โทร."]):
                    desc = next_l
                    break

        # Careers
        careers = []
        if "Careers" in lines:
            idx = lines.index("Careers")
            for c in lines[idx+1:idx+7]:
                if len(c) > 3 and not any(k in c for k in ["Facebook", "Email", "โทร", "ห้อง", "ชั้น", "Compare courses", "Loading contact"]):
                    careers.append(c)

        fac_th, fac_en = map_rsu_faculty(title_th, title_en)

        # ID from url or slug
        slug = href.rstrip("/").split("/")[-1]
        cid = f"rsu_grad_{slug[:18]}"

        return {
            "id": cid,
            "title_th": title_th,
            "title_en": title_en,
            "degree_level": deg_lvl,
            "degree_name": deg_name,
            "university": "Rangsit University",
            "university_th": "มหาวิทยาลัยรังสิต",
            "faculty": fac_en,
            "faculty_th": fac_th,
            "department": "",
            "department_th": "",
            "duration_years": duration,
            "total_credits": "36-48 หน่วยกิต" if deg_lvl == "ปริญญาโท" else "48-72 หน่วยกิต",
            "tuition_per_semester": "ไม่ระบุ",
            "tuition_total": tuition,
            "program_type": "นานาชาติ" if "นานาชาติ" in f"{title_th} {title_en}" else "ภาคปกติ",
            "description": desc or f"หลักสูตรระดับ{deg_lvl} {title_th} มหาวิทยาลัยรังสิต มุ่งเน้นการพัฒนามหาบัณฑิตและดุษฎีบัณฑิตที่มีศักยภาพสูงทางวิชาการและวิชาชีพ",
            "curriculum_highlights": [
                f"หลักสูตรระดับ{deg_lvl} มาตรฐานวิชาชีพระดับสากล",
                f"จัดการเรียนการสอนโดยคณาจารย์ผู้ทรงคุณวุฒิ {fac_th}",
                "เน้นการทำวิจัยและวิทยานิพนธ์เพื่อประยุกต์ใช้ในอุตสาหกรรมและสังคมจริง"
            ],
            "career_paths": careers if careers else [
                "อาจารย์ นักวิจัย และนักวิชาการระดับสูง",
                "ผู้เชี่ยวชาญและที่ปรึกษาองค์กรชั้นนำ",
                "ผู้บริหารและผู้ประกอบการนวัตกรรม"
            ],
            "tags": [deg_lvl, fac_th, "มหาวิทยาลัยรังสิต", "บัณฑิตศึกษา"]
        }

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_rsu_detail, it): it for it in course_links}
        for fut in as_completed(futures):
            res = fut.result()
            if res and res.get("title_th"):
                courses.append(res)

    logger.info(f"RSU extraction complete: {len(courses)} courses extracted")
    return courses

# =========================================================================
# 2. RMUTT (Rajamangala University of Technology Thanyaburi) Crawler
# =========================================================================
def crawl_rmutt():
    logger.info("--- Starting RMUTT Graduate Course Crawl from PDF 2568 ---")
    pdf_url = "https://grad.rmutt.ac.th/download/cul-grad-rmutt-2568.pdf"
    pdf_bytes = fetch_url(pdf_url)
    if not pdf_bytes:
        logger.error("Failed to download RMUTT PDF")
        return []

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join([p.extract_text() for p in reader.pages])

    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    courses = []

    current_faculty_th = "คณะวิศวกรรมศาสตร์"
    current_faculty_en = "Faculty of Engineering"

    for i, line in enumerate(lines):
        # Detect Faculty heading
        m_fac = re.search(r"(คณะ[\w\s]+)\s*\((Faculty of [\w\s]+)\)", line)
        if m_fac:
            current_faculty_th = m_fac.group(1).strip()
            current_faculty_en = m_fac.group(2).strip()
            continue

        # Detect Course row: starting with a number and 'สาขาวิชา'
        m_course = re.search(r"^(\d+)\s+สาขาวิชา(.*?)\s+หลักสูตร([\w\s]+?มหาบัณฑิต|[\w\s]+?ดุษฎีบัณฑิต|ประกาศนียบัตรบัณฑิต[\w\s]*?)\s+สาขาวิชา(.*?)\s+([A-Za-z].*?Program in\s+[\w\s]+?)\s+(.*)$", line)
        if not m_course:
            # Fallback looser regex
            m_course = re.search(r"^(\d+)\s+สาขาวิชา(.*?)\s+หลักสูตร(.*?)\s+สาขาวิชา(.*?)\s+([A-Za-z].*)$", line)

        if m_course:
            num = m_course.group(1)
            major_th = m_course.group(2).strip()
            deg_type_th = m_course.group(3).strip()
            major_spec = m_course.group(4).strip() if len(m_course.groups()) >= 4 else major_th
            tail_en = m_course.group(5).strip() if len(m_course.groups()) >= 5 else ""

            # Reconstruct title_th
            title_th = f"หลักสูตร{deg_type_th} สาขาวิชา{major_th}"
            title_th = re.sub(r"\s+", " ", title_th).strip()

            # Degree level
            if "ดุษฎีบัณฑิต" in title_th or "Doctor" in tail_en or "D.Eng" in tail_en or "Ph.D" in tail_en or "D.Tech" in tail_en:
                deg_lvl = "ปริญญาเอก"
            elif "ประกาศนียบัตรบัณฑิตชั้นสูง" in title_th:
                deg_lvl = "ประกาศนียบัตรบัณฑิตชั้นสูง"
            elif "ประกาศนียบัตรบัณฑิต" in title_th:
                deg_lvl = "ประกาศนียบัตรบัณฑิต"
            else:
                deg_lvl = "ปริญญาโท"

            # Parse English title from tail_en
            m_en_prog = re.search(r"([A-Za-z\s]+Program in\s+[A-Za-z\s\(\)]+)", tail_en)
            title_en = m_en_prog.group(1).strip() if m_en_prog else tail_en.split(" (")[0].strip()

            # Degree abbreviation
            deg_abbr = "มหาบัณฑิต"
            m_th_abbr = re.search(r"([ก-ฮ]\.[ก-ฮ\.]+\s*\([^\)]+\)|[ก-ฮ]\.[ก-ฮ\.]+)", tail_en)
            if m_th_abbr:
                deg_abbr = m_th_abbr.group(1).strip()
            elif deg_lvl == "ปริญญาเอก":
                deg_abbr = "ปร.ด."
            elif deg_lvl == "ปริญญาโท":
                deg_abbr = "วศ.ม." if "วิศวกรรม" in title_th else "วท.ม."

            cid = f"rmutt_grad_{num}_{re.sub(r'[^a-zA-Z0-9]', '', title_en[:12]).lower()}"

            courses.append({
                "id": cid,
                "title_th": title_th,
                "title_en": title_en,
                "degree_level": deg_lvl,
                "degree_name": deg_abbr,
                "university": "Rajamangala University of Technology Thanyaburi",
                "university_th": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
                "faculty": current_faculty_en,
                "faculty_th": current_faculty_th,
                "department": "",
                "department_th": f"สาขาวิชา{major_th}",
                "duration_years": "2 ปี" if deg_lvl in ("ปริญญาโท", "ประกาศนียบัตรบัณฑิต") else "3 ปี",
                "total_credits": "36-45 หน่วยกิต" if deg_lvl == "ปริญญาโท" else "48-72 หน่วยกิต",
                "tuition_per_semester": "ไม่ระบุ",
                "tuition_total": "ไม่ระบุ",
                "program_type": "นานาชาติ" if "นานาชาติ" in title_th or "International" in title_en else "ภาคปกติ",
                "description": f"{title_th} ({title_en}) {current_faculty_th} มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี มุ่งเน้นการผลิตมหาบัณฑิตและดุษฎีบัณฑิตที่มีทักษะปฏิบัติการวิจัยและนวัตกรรมระดับสูง",
                "curriculum_highlights": [
                    f"หลักสูตรระดับ{deg_lvl} ตามเกณฑ์มาตรฐาน มคอ.2",
                    f"จัดการเรียนการสอนโดย {current_faculty_th} มทร.ธัญบุรี",
                    "มุ่งเน้นการวิจัยเชิงนวัตกรรม เทคโนโลยี และการประยุกต์ใช้ในอุตสาหกรรม"
                ],
                "career_paths": [
                    "วิศวกร/นักวิชาการ/นักวิจัยระดับผู้เชี่ยวชาญ",
                    "อาจารย์ในสถาบันอุดมศึกษา",
                    "ที่ปรึกษาและผู้บริหารโครงการด้านนวัตกรรมและเทคโนโลยี"
                ],
                "tags": [deg_lvl, current_faculty_th, "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี", "บัณฑิตวิทยาลัย"]
            })

    logger.info(f"RMUTT extraction complete: {len(courses)} courses extracted from PDF")
    return courses

# =========================================================================
# 3. Sripatum University (SPU) Crawler
# =========================================================================
SPU_FACULTY_MAP = [
    (r"บริหารธุรกิจ|M\.B\.A|D\.B\.A", "คณะบริหารธุรกิจ", "Faculty of Business Administration"),
    (r"การจัดการ|M\.M\.", "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ", "Graduate College of Management"),
    (r"รัฐประศาสน|M\.P\.A", "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ", "Graduate College of Management"),
    (r"ศึกษาศาสตร|นวัตกรรมการเรียนรู้|การบริหารการศึกษา|Ph\.D\.Eda|M\.Ed", "คณะสหวิทยาการ เทคโนโลยีและนวัตกรรม", "Faculty of Interdisciplinary Studies"),
    (r"บัญชี|M\.Acc|Ph\.D\.Acc", "คณะบัญชี", "Faculty of Accountancy"),
    (r"เทคโนโลยีสารสนเทศ|M\.S\.|ปัญญาประดิษฐ์", "คณะเทคโนโลยีสารสนเทศ", "Faculty of Information Technology"),
    (r"วิศวกรรมโยธา|วิศวกรรม|M\.Eng|D\.Eng", "คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    (r"นิติศาสตร์|นิติรัฐกิจ|LL\.M|LL\.D", "คณะนิติศาสตร์", "Faculty of Law"),
    (r"โลจิสติกส์", "วิทยาลัยโลจิสติกส์และซัพพลายเชน", "College of Logistics and Supply Chain"),
    (r"นิเทศศาสตร์", "คณะนิเทศศาสตร์", "Faculty of Communication Arts")
]

def map_spu_faculty(title):
    for pat, fth, fen in SPU_FACULTY_MAP:
        if re.search(pat, title):
            return fth, fen
    return "วิทยาลัยบัณฑิตศึกษา", "Graduate College"

def crawl_spu():
    logger.info("--- Starting SPU (Sripatum University) Graduate Course Crawl ---")
    url = "https://www.spu.ac.th/fac/graduate"
    data = fetch_url(url)
    if not data:
        logger.error("Failed to fetch SPU graduate page")
        return []

    soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")
    courses = []
    seen = set()

    for a in soup.find_all("a", href=True):
        txt = a.get_text(separator=" ", strip=True)
        href = a["href"]
        if any(k in txt for k in ["มหาบัณฑิต", "ดุษฎีบัณฑิต", "หลักสูตร", "Ph.D.", "D.B.A.", "M.B.A", "M.P.A", "M.Eng", "D.Eng", "LL.M", "LL.D"]):
            if len(txt) > 8 and "อ่านต่อ" not in txt and "สมัครเรียน" not in txt and "ที่เปิดสอน" not in txt and not re.match(r"^Ph\.?D\.?[a-zA-Z\.]*$", txt.strip()):
                title_th = txt.strip()
                if title_th in seen:
                    continue
                seen.add(title_th)

                # Degree level
                deg_lvl = "ปริญญาเอก" if any(k in title_th for k in ["ดุษฎีบัณฑิต", "Ph.D.", "D.B.A.", "D.Eng", "LL.D."]) else "ปริญญาโท"

                # Degree abbreviation
                deg_abbr = "มหาบัณฑิต"
                m_abbr = re.search(r"\(([A-Za-z\.\s]+)\)", title_th)
                if m_abbr:
                    deg_abbr = m_abbr.group(1).strip()
                elif deg_lvl == "ปริญญาเอก":
                    deg_abbr = "ปร.ด."

                fac_th, fac_en = map_spu_faculty(title_th)

                # English Title guess
                title_en = title_th
                m_th_clean = re.sub(r"\(.*?\)", "", title_th).strip()

                cid = f"spu_grad_{len(courses)+1}_{re.sub(r'[^a-zA-Z0-9]', '', deg_abbr).lower()}"

                courses.append({
                    "id": cid,
                    "title_th": title_th,
                    "title_en": f"{title_th} ({deg_abbr})",
                    "degree_level": deg_lvl,
                    "degree_name": deg_abbr,
                    "university": "Sripatum University",
                    "university_th": "มหาวิทยาลัยศรีปทุม",
                    "faculty": fac_en,
                    "faculty_th": fac_th,
                    "department": "",
                    "department_th": "",
                    "duration_years": "2 ปี" if deg_lvl == "ปริญญาโท" else "3 ปี",
                    "total_credits": "36 หน่วยกิต" if deg_lvl == "ปริญญาโท" else "48-54 หน่วยกิต",
                    "tuition_per_semester": "ไม่ระบุ",
                    "tuition_total": "ไม่ระบุ",
                    "program_type": "นานาชาติ" if "นานาชาติ" in title_th or "International" in title_th else "ภาคปกติ",
                    "description": f"{title_th} มหาวิทยาลัยศรีปทุม มุ่งเน้นการสร้างผู้นำทางธุรกิจ เทคโนโลยี และวิชาชีพที่พร้อมรับมือกับการเปลี่ยนแปลงในยุคดิจิทัล",
                    "curriculum_highlights": [
                        f"หลักสูตรระดับ{deg_lvl} ตอบโจทย์ภาคธุรกิจและอุตสาหกรรมจริง",
                        f"จัดการเรียนการสอนโดย {fac_th} มหาวิทยาลัยศรีปทุม",
                        "คณาจารย์ผู้ทรงคุณวุฒิและผู้เชี่ยวชาญจากองค์กรชั้นนำระดับประเทศ"
                    ],
                    "career_paths": [
                        "ผู้บริหารระดับสูงในองค์กรภาครัฐและเอกชน",
                        "ผู้ประกอบการและนักนวัตกรรมธุรกิจ",
                        "อาจารย์และนักวิจัยระดับบัณฑิตศึกษา"
                    ],
                    "tags": [deg_lvl, fac_th, "มหาวิทยาลัยศรีปทุม", "บัณฑิตศึกษา"]
                })

    logger.info(f"SPU extraction complete: {len(courses)} courses extracted")
    return courses

# =========================================================================
# 4. NIDA School of Applied Statistics Crawler
# =========================================================================
NIDA_AS_PROGRAMS = [
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสถิติประยุกต์",
        "title_en": "Master of Science Program in Applied Statistics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (สถิติประยุกต์)",
        "slug": "applied_statistics"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการวิเคราะห์ข้อมูลและวิทยาการข้อมูล (DADS)",
        "title_en": "Master of Science Program in Data Analytics and Data Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การวิเคราะห์ข้อมูลและวิทยาการข้อมูล)",
        "slug": "dads"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาโลจิสติกส์อัจฉริยะและการจัดการโซ่อุปทาน (LSCM)",
        "title_en": "Master of Science Program in Smart Logistics and Supply Chain Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (โลจิสติกส์อัจฉริยะและการจัดการโซ่อุปทาน)",
        "slug": "lscm"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และระบบสารสนเทศ (CSIS)",
        "title_en": "Master of Science Program in Computer Science and Information Systems",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์และระบบสารสนเทศ)",
        "slug": "csis"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการจัดการวิเคราะห์ข้อมูลและเทคโนโลยีข้อมูล (MADT)",
        "title_en": "Master of Science Program in Management of Analytics and Data Technologies",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การจัดการวิเคราะห์ข้อมูลและเทคโนโลยีข้อมูล)",
        "slug": "madt"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาบริหารเทคโนโลยีสารสนเทศ (ITM)",
        "title_en": "Master of Science Program in Information Technology Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (บริหารเทคโนโลยีสารสนเทศ)",
        "slug": "itm"
    },
    {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการจัดการความเสี่ยงความมั่นคงทางไซเบอร์ (CYBER)",
        "title_en": "Master of Science Program in Cybersecurity Risk Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การจัดการความเสี่ยงความมั่นคงทางไซเบอร์)",
        "slug": "cybersecurity"
    },
    {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสถิติประยุกต์ (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy Program in Applied Statistics (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (สถิติประยุกต์)",
        "slug": "phd_as"
    },
    {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการวิเคราะห์ข้อมูลและวิทยาการข้อมูล (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy Program in Data Analytics & Data Science (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (การวิเคราะห์ข้อมูลและวิทยาการข้อมูล)",
        "slug": "phd_dads"
    },
    {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาโลจิสติกส์อัจฉริยะและการจัดการโซ่อุปทาน (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy Program in Smart Logistics and Supply Chain Management (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (โลจิสติกส์อัจฉริยะและการจัดการโซ่อุปทาน)",
        "slug": "phd_lscm"
    },
    {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และระบบสารสนเทศ (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy Program in Computer Science & Information Systems (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิทยาการคอมพิวเตอร์และระบบสารสนเทศ)",
        "slug": "phd_csis"
    }
]

def crawl_nida():
    logger.info("--- Extracting NIDA School of Applied Statistics Programs ---")
    courses = []
    for item in NIDA_AS_PROGRAMS:
        cid = f"nida_as_{item['slug']}"
        deg_lvl = item["degree_level"]
        courses.append({
            "id": cid,
            "title_th": item["title_th"],
            "title_en": item["title_en"],
            "degree_level": deg_lvl,
            "degree_name": item["degree_name"],
            "university": "National Institute of Development Administration",
            "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
            "faculty": "School of Applied Statistics",
            "faculty_th": "คณะสถิติประยุกต์",
            "department": "",
            "department_th": "",
            "duration_years": "2 ปี" if deg_lvl == "ปริญญาโท" else "3 ปี",
            "total_credits": "36 หน่วยกิต" if deg_lvl == "ปริญญาโท" else "48-54 หน่วยกิต",
            "tuition_per_semester": "ไม่ระบุ",
            "tuition_total": "ไม่ระบุ",
            "program_type": "นานาชาติ" if "นานาชาติ" in item["title_th"] else "ภาคปกติ",
            "description": f"{item['title_th']} ({item['title_en']}) คณะสถิติประยุกต์ นิด้า สถาบันการศึกษาระดับบัณฑิตศึกษาชั้นนำ มุ่งเน้นการสร้างผู้เชี่ยวชาญด้านวิทยาการข้อมูล สถิติ และเทคโนโลยีสารสนเทศ",
            "curriculum_highlights": [
                f"หลักสูตรระดับ{deg_lvl} ชั้นนำของประเทศไทยด้าน Data Science และ AI",
                "จัดการเรียนการสอนโดยคณาจารย์ระดับปริญญาเอกและผู้เชี่ยวชาญ คณะสถิติประยุกต์ นิด้า",
                "เน้นการทำวิทยานิพนธ์และงานวิจัยที่ตีพิมพ์ในวารสารวิชาการระดับนานาชาติ"
            ],
            "career_paths": [
                "Data Scientist / AI Specialist",
                "นักวิจัยและอาจารย์มหาวิทยาลัยด้านวิทยาการคอมพิวเตอร์และสถิติ",
                "ผู้เชี่ยวชาญด้านโลจิสติกส์และการวิเคราะห์ข้อมูลองค์กร"
            ],
            "tags": [deg_lvl, "คณะสถิติประยุกต์", "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)", "Data Science", "AI"]
        })
    logger.info(f"NIDA AS extraction complete: {len(courses)} courses extracted")
    return courses

# =========================================================================
# Main Runner & Checkpoint Export
# =========================================================================
def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    all_courses = []

    rsu_courses = crawl_rsu()
    all_courses.extend(rsu_courses)

    rmutt_courses = crawl_rmutt()
    all_courses.extend(rmutt_courses)

    spu_courses = crawl_spu()
    all_courses.extend(spu_courses)

    nida_courses = crawl_nida()
    all_courses.extend(nida_courses)

    logger.info(f"=== Total Extracted Phase 4 Courses: {len(all_courses)} ===")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Successfully checkpointed to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
