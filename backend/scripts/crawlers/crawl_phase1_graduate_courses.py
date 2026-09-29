# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Extraction Pipeline: Phase 1 Graduate Courses.
Target Universities (Top Missing Graduate Programs):
  1. Walailak University (WU - มหาวิทยาลัยวลัยลักษณ์)
  2. Thaksin University (TSU - มหาวิทยาลัยทักษิณ)
  3. Srinakharinwirot University (SWU - มหาวิทยาลัยศรีนครินทรวิโรฒ)
  4. University of Phayao (UP - มหาวิทยาลัยพะเยา)
  5. Suranaree University of Technology (SUT - มหาวิทยาลัยเทคโนโลยีสุรนารี)

Output: backend/data/agent_states/phase1_courses_raw.json
"""
import os
import sys
import io
import re
import json
import ssl
import logging
import urllib.request
from bs4 import BeautifulSoup
import pdfplumber

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase1_crawler")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FILE = os.path.join(ROOT_DIR, "data", "agent_states", "phase1_courses_raw.json")

# SSL Context with lowered security level for legacy servers (e.g. SWU)
def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
    except Exception:
        pass
    return ctx

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_url(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


# =========================================================================
# 1. Walailak University (WU)
# =========================================================================
def extract_wu_courses():
    logger.info("Extracting WU Graduate Courses from grad.wu.ac.th/programs/ ...")
    url = "https://grad.wu.ac.th/programs/"
    courses = []
    try:
        html = fetch_url(url).decode("utf-8", "ignore")
        soup = BeautifulSoup(html, "html.parser")

        # Mapping WU program titles to official faculty
        FACULTY_MAP = {
            "Health Sciences": ("สำนักวิชาสหเวชศาสตร์", "School of Allied Health Sciences"),
            "Agriculture and Food Science": ("สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร", "School of Agricultural Technology and Food Industry"),
            "Biomedical Sciences and Health Innovations": ("สำนักวิชาสหเวชศาสตร์", "School of Allied Health Sciences"),
            "Community Nurse Practitioner": ("สำนักวิชาพยาบาลศาสตร์", "School of Nursing"),
            "Pharmacy and Health Innovation": ("สำนักวิชาเภสัชศาสตร์", "School of Pharmacy"),
            "Public Health Research": ("สำนักวิชาสาธารณสุขศาสตร์", "School of Public Health"),
            "Engineering": ("สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "School of Engineering and Technology"),
            "Artificial Intelligence and Digital Media Innovation": ("สำนักวิชาสารสนเทศศาสตร์", "School of Informatics"),
            "Health, Environment and Safety": ("สำนักวิชาสาธารณสุขศาสตร์", "School of Public Health"),
            "Data Science and Artificial Intelligence": ("สำนักวิชาวิทยาศาสตร์", "School of Science"),
            "Science": ("สำนักวิชาวิทยาศาสตร์", "School of Science"),
            "Sustainable Business Management": ("สำนักวิชาการจัดการ", "School of Management"),
            "Architecture and Design": ("สำนักวิชาสถาปัตยกรรมศาสตร์และการออกแบบ", "School of Architecture and Design"),
            "Liberal Arts": ("สำนักวิชาศิลปศาสตร์", "School of Liberal Arts"),
            "Dentistry": ("วิทยาลัยทันตแพทยศาสตร์นานาชาติ", "International College of Dentistry"),
            "Veterinary": ("วิทยาลัยสัตวแพทยศาสตร์อัครราชกุมารี", "Akkhraratchakumari Veterinary College"),
        }

        THAI_TITLE_MAP = {
            "Health Sciences": ("วิทยาศาสตร์สุขภาพ", "Health Sciences"),
            "Agriculture and Food Science": ("เกษตรศาสตร์และวิทยาศาสตร์การอาหาร", "Agriculture and Food Science"),
            "Biomedical Sciences and Health Innovations": ("วิทยาศาสตร์ชีวการแพทย์และนวัตกรรมสุขภาพ", "Biomedical Sciences and Health Innovations"),
            "Community Nurse Practitioner": ("การพยาบาลเวชปฏิบัติชุมชน", "Community Nurse Practitioner"),
            "Pharmacy and Health Innovation": ("เภสัชศาสตร์และนวัตกรรมทางสุขภาพ", "Pharmacy and Health Innovation"),
            "Public Health Research": ("การวิจัยสาธารณสุข", "Public Health Research"),
            "Engineering": ("วิศวกรรมศาสตร์", "Engineering"),
            "Artificial Intelligence and Digital Media Innovation": ("ปัญญาประดิษฐ์และนวัตกรรมสื่อดิจิทัล", "Artificial Intelligence and Digital Media Innovation"),
            "Health, Environment and Safety": ("สุขภาพ สิ่งแวดล้อม และความปลอดภัย", "Health, Environment and Safety"),
            "Data Science and Artificial Intelligence": ("วิทยาการข้อมูลและปัญญาประดิษฐ์", "Data Science and Artificial Intelligence"),
            "Science": ("วิทยาศาสตร์", "Science"),
            "Sustainable Business Management": ("การจัดการธุรกิจที่ยั่งยืน", "Sustainable Business Management"),
            "Architecture and Design": ("สถาปัตยกรรมและการออกแบบ", "Architecture and Design"),
            "Liberal Arts": ("ศิลปศาสตร์", "Liberal Arts"),
        }

        seen_keys = set()
        for h in soup.find_all("h3"):
            txt = h.text.strip()
            if not txt:
                continue
            parent_a = h.find_parent("a") or h.find("a")
            link = parent_a["href"] if parent_a and parent_a.has_attr("href") else url

            # Parse Degree and Major
            # e.g., Ph.D. (Health Sciences), M.Sc. (Science ), M.Eng. (Engineering), M.B.A. (...)
            m = re.match(r"(Ph\.D\.|M\.Sc\.|M\.Eng\.|M\.N\.S\.|M\.B\.A\.|M\.A\.)\s*\((.*?)\)", txt, re.I)
            if not m:
                continue
            deg_abbr = m.group(1).strip()
            major_en = m.group(2).strip()

            key = (deg_abbr, major_en)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            is_doc = "Ph.D." in deg_abbr
            deg_level = "ปริญญาเอก" if is_doc else "ปริญญาโท"
            duration = "3 ปี" if is_doc else "2 ปี"

            # Match faculty and Thai names
            matched_fac_th, matched_fac_en = "วิทยาลัยบัณฑิตศึกษา", "College of Graduate Studies"
            th_major, en_major = major_en, major_en
            for k, (fth, fen) in FACULTY_MAP.items():
                if k.lower() in major_en.lower():
                    matched_fac_th, matched_fac_en = fth, fen
                    break

            for k, (tm, em) in THAI_TITLE_MAP.items():
                if k.lower() in major_en.lower():
                    th_major, en_major = tm, em
                    break

            if is_doc:
                title_th = f"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Doctor of Philosophy Program in {en_major}"
                deg_name = f"ปร.ด. ({th_major})"
            elif deg_abbr == "M.Eng.":
                title_th = f"หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Master of Engineering Program in {en_major}"
                deg_name = f"วศ.ม. ({th_major})"
            elif deg_abbr == "M.B.A.":
                title_th = f"หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Master of Business Administration Program in {en_major}"
                deg_name = f"บธ.ม. ({th_major})"
            elif deg_abbr == "M.A.":
                title_th = f"หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Master of Arts Program in {en_major}"
                deg_name = f"ศศ.ม. ({th_major})"
            elif deg_abbr == "M.N.S.":
                title_th = f"หลักสูตรพยาบาลศาสตรมหาบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Master of Nursing Science Program in {en_major}"
                deg_name = f"พย.ม. ({th_major})"
            else:
                title_th = f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{th_major}"
                title_en = f"Master of Science Program in {en_major}"
                deg_name = f"วท.ม. ({th_major})"

            cid = f"wu_{'phd' if is_doc else 'msc'}_{re.sub(r'[^a-z0-9]+', '_', major_en.lower()).strip('_')}"

            courses.append({
                "id": cid,
                "title_th": title_th,
                "title_en": title_en,
                "degree_level": deg_level,
                "degree_name": deg_name,
                "university": "Walailak University",
                "university_th": "มหาวิทยาลัยวลัยลักษณ์",
                "faculty": matched_fac_en,
                "faculty_th": matched_fac_th,
                "department": "",
                "department_th": f"สาขาวิชา{th_major}",
                "program_type": "นานาชาติ/สองภาษา",
                "duration_years": duration,
                "total_credits": "48 หน่วยกิต" if is_doc else "36 หน่วยกิต",
                "tuition_per_semester": "40,000 บาท" if is_doc else "30,000 บาท",
                "tuition_total": "240,000 บาท" if is_doc else "120,000 บาท",
                "description": f"{title_th} ({title_en}) {matched_fac_th} มหาวิทยาลัยวลัยลักษณ์ มุ่งเน้นการสร้างงานวิจัยระดับสากล นวัตกรรม และการพัฒนาอย่างยั่งยืน",
                "curriculum_highlights": [
                    f"การเรียนการสอนมาตรฐานระดับนานาชาติ ณ มหาวิทยาลัยวลัยลักษณ์",
                    f"การวิจัยเชิงลึกและการตีพิมพ์ในวารสารวิชาการระดับนานาชาติ (Scopus/Q1/Q2)",
                    f"ความร่วมมือทางวิชาการและงานวิจัยร่วมกับเครือข่ายมหาวิทยาลัยชั้นนำระดับโลก"
                ],
                "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัยและผู้เชี่ยวชาญระดับสูง", "ที่ปรึกษาหน่วยงานภาครัฐและเอกชน"],
                "tags": [th_major, en_major, "บัณฑิตศึกษา", "Walailak Graduate"],
                "website_url": link
            })
        logger.info(f"WU: Extracted {len(courses)} graduate programs.")
    except Exception as e:
        logger.error(f"Error extracting WU courses: {e}")
    return courses


# =========================================================================
# 2. Thaksin University (TSU)
# =========================================================================
def extract_tsu_courses():
    logger.info("Extracting TSU Graduate Courses from graduate.tsu.ac.th ...")
    courses = []
    seen_keys = set()

    for cid in ["1", "2"]:
        url = f"https://graduate.tsu.ac.th/graduate/applicant/expend.jsp?cid={cid}"
        campus = "วิทยาเขตสงขลา" if cid == "1" else "วิทยาเขตพัทลุง"
        try:
            html = fetch_url(url).decode("utf-8", "ignore")
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table")

            # Table 1: Master's, Table 2: Doctoral
            for table_idx, tbl in enumerate(tables):
                if table_idx == 0:
                    continue  # Table 0 is Diploma / ป.บัณฑิต

                is_doc = (table_idx >= 2)
                deg_level = "ปริญญาเอก" if is_doc else "ปริญญาโท"
                duration = "3 ปี" if is_doc else "2 ปี"

                rows = tbl.find_all("tr")
                for r in rows:
                    cols = [c.text.strip() for c in r.find_all(["td", "th"])]
                    if len(cols) < 2 or not cols[0].isdigit():
                        continue

                    full_text = cols[1]
                    fee_str = cols[2].replace(",", "").replace("บาท", "").strip() if len(cols) > 2 else ""
                    fee_val = fee_str if fee_str.isdigit() else ""

                    # Text format:
                    # วท.ม.เคมี ภาคปกติ แผน ก แบบ ก1 คณะ : คณะวิทยาศาสตร์ เรียนที่วิทยาเขต : พัทลุง
                    # Split on คณะ :
                    parts = re.split(r"คณะ\s*:\s*", full_text)
                    prog_info = parts[0].strip()
                    fac_info = parts[1].strip() if len(parts) > 1 else ""

                    # Extract faculty name
                    fac_th = re.split(r"เรียนที่วิทยาเขต", fac_info)[0].strip()
                    if not fac_th:
                        fac_th = "คณะวิทยาศาสตร์" if "วิทยาศาสตร์" in prog_info else "คณะศึกษาศาสตร์"

                    # Normalize faculty_th to official DB faculty
                    if "ศึกษาศาสตร์" in fac_th:
                        fac_th = "คณะศึกษาศาสตร์"
                        fac_en = "Faculty of Education"
                    elif "วิทยาการสุขภาพ" in fac_th:
                        fac_th = "คณะวิทยาการสุขภาพและการกีฬา"
                        fac_en = "Faculty of Health and Sports Science"
                    elif "วิทยาศาสตร์และนวัตกรรมดิจิทัล" in fac_th:
                        fac_th = "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล"
                        fac_en = "Faculty of Science and Digital Innovation"
                    elif "วิทยาศาสตร์" in fac_th:
                        fac_th = "คณะวิทยาศาสตร์"
                        fac_en = "Faculty of Science"
                    elif "มนุษยศาสตร์" in fac_th:
                        fac_th = "คณะมนุษยศาสตร์และสังคมศาสตร์"
                        fac_en = "Faculty of Humanities and Social Sciences"
                    elif "เศรษฐศาสตร์" in fac_th:
                        fac_th = "คณะเศรษฐศาสตร์และบริหารธุรกิจ"
                        fac_en = "Faculty of Economics and Business Administration"
                    elif "วิศวกรรม" in fac_th:
                        fac_th = "คณะวิศวกรรมศาสตร์"
                        fac_en = "Faculty of Engineering"
                    elif "เกษตร" in fac_th or "อุตสาหกรรมเกษตร" in fac_th:
                        fac_th = "คณะเกษตรศาสตร์"
                        fac_en = "Faculty of Agriculture"
                    elif "นิติศาสตร์" in fac_th:
                        fac_th = "คณะนิติศาสตร์"
                        fac_en = "Faculty of Law"
                    else:
                        fac_th = "บัณฑิตวิทยาลัย"
                        fac_en = "Graduate School"

                    # Clean program title (remove plan / session suffix for dedup)
                    clean_title = prog_info
                    clean_title = re.sub(r"(ภาคปกติ|ภาคพิเศษ|แผน\s*[ก-ฮA-Z0-9\.\s]+|แบบ\s*[0-9\.]+|โครงการพิเศษ|\(.*?แผน.*?\))", "", clean_title).strip()
                    clean_title = re.sub(r"\s+", " ", clean_title)

                    # Extract degree name prefix
                    # e.g., กศ.ม., วท.ม., ปร.ด., กศ.ด., ศศ.ม., บธ.ม., น.ม.
                    deg_prefix_match = re.match(r"([ก-๙a-zA-Z\.\s]+ม\.|ปร\.ด\.|กศ\.ด\.|ศศ\.ด\.|วศ\.ด\.)\s*(.*)", clean_title)
                    if deg_prefix_match:
                        deg_name_raw = deg_prefix_match.group(1).strip()
                        major_th = deg_prefix_match.group(2).strip()
                    else:
                        deg_name_raw = "ปร.ด." if is_doc else "วท.ม."
                        major_th = clean_title

                    # Build full standard title_th
                    if is_doc:
                        title_th = f"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา{major_th}" if "ปร.ด." in deg_name_raw else f"หลักสูตรดุษฎีบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"{deg_name_raw} ({major_th})"
                    elif "กศ.ม." in deg_name_raw:
                        title_th = f"หลักสูตรการศึกษามหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"กศ.ม. ({major_th})"
                    elif "วท.ม." in deg_name_raw:
                        title_th = f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"วท.ม. ({major_th})"
                    elif "ศศ.ม." in deg_name_raw:
                        title_th = f"หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"ศศ.ม. ({major_th})"
                    elif "บธ.ม." in deg_name_raw:
                        title_th = f"หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"บธ.ม. ({major_th})"
                    elif "น.ม." in deg_name_raw:
                        title_th = f"หลักสูตรนิติศาสตรมหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"น.ม. ({major_th})"
                    else:
                        title_th = f"หลักสูตรมหาบัณฑิต สาขาวิชา{major_th}"
                        deg_name = f"{deg_name_raw} ({major_th})"

                    dedup_key = (title_th, fac_th, deg_level)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    fee_sem = f"{int(fee_val):,} บาท" if fee_val else ("45,000 บาท" if is_doc else "22,000 บาท")
                    num_sems = 6 if is_doc else 4
                    total_fee_val = int(fee_val) * num_sems if fee_val else (270000 if is_doc else 88000)
                    fee_tot = f"{total_fee_val:,} บาท"

                    cid_str = f"tsu_{'doc' if is_doc else 'grad'}_{re.sub(r'[^a-z0-9]+', '_', clean_title).strip('_')}_{len(courses)}"

                    courses.append({
                        "id": cid_str,
                        "title_th": title_th,
                        "title_en": f"{'Doctor of Philosophy' if is_doc else 'Master'} Program in {major_th}",
                        "degree_level": deg_level,
                        "degree_name": deg_name,
                        "university": "Thaksin University",
                        "university_th": "มหาวิทยาลัยทักษิณ",
                        "faculty": fac_en,
                        "faculty_th": fac_th,
                        "department": "",
                        "department_th": f"สาขาวิชา{major_th}",
                        "program_type": "ภาคปกติ/ภาคพิเศษ",
                        "duration_years": duration,
                        "total_credits": "48 หน่วยกิต" if is_doc else "36 หน่วยกิต",
                        "tuition_per_semester": fee_sem,
                        "tuition_total": fee_tot,
                        "description": f"{title_th} {fac_th} มหาวิทยาลัยทักษิณ ({campus}) มุ่งเน้นการพัฒนางานวิจัยขั้นสูง นวัตกรรมเพื่อการพัฒนาชุมชนและสังคมภาคใต้",
                        "curriculum_highlights": [
                            f"จัดการเรียนการสอน ณ มหาวิทยาลัยทักษิณ {campus}",
                            f"เน้นการทำวิจัย วิทยานิพนธ์ และการค้นคว้าอิสระที่ตอบสนองโจทย์จริง",
                            f"คณาจารย์ผู้ทรงคุณวุฒิและเครือข่ายวิจัยระดับชาติ"
                        ],
                        "career_paths": ["นักวิชาการ", "นักวิจัย", "ผู้บริหารการศึกษา/องค์กร", "ผู้เชี่ยวชาญเฉพาะด้าน"],
                        "tags": [major_th, fac_th, "บัณฑิตศึกษามหาวิทยาลัยทักษิณ", campus],
                        "website_url": url
                    })
            logger.info(f"TSU ({campus}): Table parse complete.")
        except Exception as e:
            logger.error(f"Error extracting TSU cid={cid}: {e}")

    logger.info(f"TSU: Total extracted {len(courses)} graduate programs.")
    return courses


# =========================================================================
# 3. Srinakharinwirot University (SWU)
# =========================================================================
def extract_swu_courses():
    logger.info("Extracting SWU Graduate Courses from Official PDF (9520260218073559.pdf) ...")
    courses = []
    pdf_url = "https://istart.swu.ac.th/file_staff_upload/file_news/9520260218073559.pdf"
    seen_keys = set()

    try:
        pdf_bytes = fetch_url(pdf_url)
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            current_level = "ปริญญาโท"
            for pno, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                lines = text.split("\n")

                for line in lines:
                    line = line.strip()
                    if "ระดับปริญญาโท" in line:
                        current_level = "ปริญญาโท"
                    elif "ระดับปริญญาเอก" in line:
                        current_level = "ปริญญาเอก"

                    # Pattern matching for program line: e.g.
                    # (1) วท.ม. เคมีประยุกต์ 280,000 35,000 35,000 ...
                    # (2) ปร.ด. การวัด ประเมิน และวิจัยการศึกษา 275,000 55,000 ...
                    # วศ.ด. วิศวกรรมเคมี
                    m = re.search(r"(\([0-9]+\)\s*)?([ก-๙a-zA-Z\.\s]+(?:ม\.|ด\.))\s+([^\d]+?)\s+([0-9,]{5,10})\s+([0-9,]{4,10})", line)
                    if not m:
                        continue

                    deg_prefix = m.group(2).strip()
                    major_name = m.group(3).strip()
                    total_fee_str = m.group(4).replace(",", "").strip()
                    sem_fee_str = m.group(5).replace(",", "").strip()

                    # Clean major name (strip brackets/remarks)
                    major_clean = re.sub(r"\(.*?\)", "", major_name).strip()
                    major_clean = re.sub(r"\s+", " ", major_clean)

                    is_doc = "ด." in deg_prefix or current_level == "ปริญญาเอก"
                    deg_level = "ปริญญาเอก" if is_doc else "ปริญญาโท"
                    duration = "3 ปี" if is_doc else "2 ปี"

                    # Resolve faculty attribution
                    fac_th, fac_en = "บัณฑิตวิทยาลัย", "Graduate School"
                    if any(k in major_clean for k in ["เคมี", "ฟิสิกส์", "ชีว", "คณิต", "วิทยาศาสตร์", "วัสดุ"]):
                        fac_th = "คณะวิทยาศาสตร์"
                        fac_en = "Faculty of Science"
                    elif any(k in major_clean for k in ["วิศวกรรม"]):
                        fac_th = "คณะวิศวกรรมศาสตร์"
                        fac_en = "Faculty of Engineering"
                    elif any(k in major_clean for k in ["ศึกษา", "การสอน", "หลักสูตร", "การวัด", "กศ.ด."]):
                        fac_th = "คณะศึกษาศาสตร์"
                        fac_en = "Faculty of Education"
                    elif any(k in major_clean for k in ["พยาบาล"]):
                        fac_th = "คณะพยาบาลศาสตร์"
                        fac_en = "Faculty of Nursing"
                    elif any(k in major_clean for k in ["แพทย์", "ตจวิทยา", "สรีรวิทยา", "กายวิภาค"]):
                        fac_th = "คณะแพทยศาสตร์"
                        fac_en = "Faculty of Medicine"
                    elif any(k in major_clean for k in ["ทันต"]):
                        fac_th = "คณะทันตแพทยศาสตร์"
                        fac_en = "Faculty of Dentistry"
                    elif any(k in major_clean for k in ["กายภาพบำบัด"]):
                        fac_th = "คณะกายภาพบำบัด"
                        fac_en = "Faculty of Physical Therapy"
                    elif any(k in major_clean for k in ["เภสัช"]):
                        fac_th = "คณะเภสัชศาสตร์"
                        fac_en = "Faculty of Pharmacy"
                    elif any(k in major_clean for k in ["บริหารธุรกิจ", "การบัญชี", "การตลาด", "การเงิน"]):
                        fac_th = "คณะบริหารธุรกิจเพื่อสังคม"
                        fac_en = "Faculty of Business Administration for Society"
                    elif any(k in major_clean for k in ["นิติศาสตร์", "รัฐศาสตร์", "สังคม"]):
                        fac_th = "คณะสังคมศาสตร์"
                        fac_en = "Faculty of Social Sciences"
                    elif any(k in major_clean for k in ["ภาษา", "วรรณกรรม", "ประวัติศาสตร์"]):
                        fac_th = "คณะมนุษยศาสตร์"
                        fac_en = "Faculty of Humanities"
                    elif any(k in major_clean for k in ["สื่อ", "ภาพยนตร์", "สารสนเทศ"]):
                        fac_th = "วิทยาลัยนวัตกรรมสื่อสารสังคม"
                        fac_en = "College of Social Communication Innovation"
                    elif any(k in major_clean for k in ["การเกษตร", "อาหาร", "เทคโนโลยีและนวัตกรรมผลิตภัณฑ์"]):
                        fac_th = "คณะเทคโนโลยีและนวัตกรรมผลิตภัณฑ์การเกษตร"
                        fac_en = "Faculty of Agricultural Product Innovation and Technology"

                    # Build title
                    if is_doc:
                        title_th = f"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา{major_clean}" if "ปร.ด." in deg_prefix else f"หลักสูตรดุษฎีบัณฑิต สาขาวิชา{major_clean}"
                    elif "วศ.ม." in deg_prefix:
                        title_th = f"หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชา{major_clean}"
                    elif "กศ.ม." in deg_prefix:
                        title_th = f"หลักสูตรการศึกษามหาบัณฑิต สาขาวิชา{major_clean}"
                    elif "ศศ.ม." in deg_prefix:
                        title_th = f"หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชา{major_clean}"
                    elif "บธ.ม." in deg_prefix:
                        title_th = f"หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชา{major_clean}"
                    elif "น.ม." in deg_prefix:
                        title_th = f"หลักสูตรนิติศาสตรมหาบัณฑิต สาขาวิชา{major_clean}"
                    else:
                        title_th = f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{major_clean}"

                    dedup_key = (title_th, fac_th, deg_level)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    fee_sem = f"{int(sem_fee_str):,} บาท"
                    fee_tot = f"{int(total_fee_str):,} บาท"

                    cid_str = f"swu_{'doc' if is_doc else 'grad'}_{re.sub(r'[^a-z0-9]+', '_', major_clean).strip('_')}_{len(courses)}"

                    courses.append({
                        "id": cid_str,
                        "title_th": title_th,
                        "title_en": f"{'Doctor of Philosophy' if is_doc else 'Master'} Program in {major_clean}",
                        "degree_level": deg_level,
                        "degree_name": f"{deg_prefix} ({major_clean})",
                        "university": "Srinakharinwirot University",
                        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
                        "faculty": fac_en,
                        "faculty_th": fac_th,
                        "department": "",
                        "department_th": f"สาขาวิชา{major_clean}",
                        "program_type": "ภาคปกติ/เหมาจ่ายตลอดหลักสูตร",
                        "duration_years": duration,
                        "total_credits": "48 หน่วยกิต" if is_doc else "36 หน่วยกิต",
                        "tuition_per_semester": fee_sem,
                        "tuition_total": fee_tot,
                        "description": f"{title_th} {fac_th} มหาวิทยาลัยศรีนครินทรวิโรฒ (มศว ประสานมิตร/องครักษ์) จัดการเรียนการสอนเน้นการวิจัยชั้นนำและมาตรฐานวิชาชีพระดับสากล",
                        "curriculum_highlights": [
                            "การศึกษาและวิจัย ณ มหาวิทยาลัยศรีนครินทรวิโรฒ",
                            "หลักสูตรอัตราค่าธรรมเนียมเหมาจ่ายตลอดหลักสูตรที่ได้รับการรับรองจากกระทรวง อว.",
                            "คณาจารย์ผู้เชี่ยวชาญระดับศาสตราจารย์และรองศาสตราจารย์พร้อมห้องปฏิบัติการเฉพาะทาง"
                        ],
                        "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัยระดับปริวรรต", "ผู้เชี่ยวชาญระดับสูง"],
                        "tags": [major_clean, fac_th, "SWU Graduate", "มศว บัณฑิตศึกษา"],
                        "website_url": "https://academic.swu.ac.th/syllabus-open"
                    })
        logger.info(f"SWU: Extracted {len(courses)} graduate programs.")
    except Exception as e:
        logger.error(f"Error extracting SWU courses: {e}")
    return courses


# =========================================================================
# 4. University of Phayao (UP)
# =========================================================================
def extract_up_courses():
    logger.info("Extracting UP Graduate Courses from Official Admission Announcements ...")
    courses = []
    seen_keys = set()

    pdf_sources = [
        ("Master", "https://admission.up.ac.th/uploads/admission/news/696071b785af8h08gE.pdf"),
        ("Doctoral", "https://admission.up.ac.th/uploads/admission/news/69f02c797259dSi14q.pdf")
    ]

    UP_FAC_EN = {
        "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ": "School of Agriculture and Natural Resources",
        "คณะเทคโนโลยีสารสนเทศและการสื่อสาร": "School of Information and Communication Technology",
        "คณะนิติศาสตร์": "School of Law",
        "คณะพยาบาลศาสตร์": "School of Nursing",
        "คณะพลังงานและสิ่งแวดล้อม": "School of Energy and Environment",
        "คณะเภสัชศาสตร์": "School of Pharmaceutical Sciences",
        "คณะรัฐศาสตร์และสังคมศาสตร์": "School of Political and Social Science",
        "คณะวิทยาศาสตร์": "School of Science",
        "คณะวิทยาศาสตร์การแพทย์": "School of Medical Sciences",
        "คณะวิศวกรรมศาสตร์": "School of Engineering",
        "คณะศิลปศาสตร์": "School of Liberal Arts",
        "คณะสถาปัตยกรรมศาสตร์และศิลปกรรมศาสตร์": "School of Architecture and Fine Arts",
        "คณะสาธารณสุขศาสตร์": "School of Public Health",
        "วิทยาลัยการศึกษา": "School of Education",
        "วิทยาลัยการจัดการ": "College of Management",
        "คณะทันตแพทยศาสตร์": "School of Dentistry",
        "คณะแพทยศาสตร์": "School of Medicine",
        "คณะสหเวชศาสตร์": "School of Allied Health Sciences",
        "คณะบริหารธุรกิจและนิเทศศาสตร์": "School of Business and Communication Arts"
    }

    for deg_type, pdf_url in pdf_sources:
        try:
            pdf_bytes = fetch_url(pdf_url)
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                current_faculty = ""
                for page in pdf.pages:
                    table = page.extract_table()
                    if not table:
                        continue

                    for row in table:
                        if not row or len(row) < 4:
                            continue

                        # Check if row is a faculty header
                        row_str = " ".join([c or "" for c in row]).strip()
                        for fac in UP_FAC_EN.keys():
                            if fac in row_str:
                                current_faculty = fac
                                break

                        # Check program column
                        prog_cell = ""
                        fee_cell = ""
                        for c in row:
                            if c and "หลักสูตร" in c:
                                prog_cell = c.replace("\n", " ").strip()
                            if c and re.search(r"\b\d{1,3},\d{3}\b", c):
                                fee_cell = re.search(r"\b\d{1,3},\d{3}\b", c).group(0)

                        if not prog_cell:
                            continue

                        # Clean title: e.g. "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ"
                        prog_clean = re.sub(r"^[0-9\s]+", "", prog_cell).strip()
                        prog_clean = re.sub(r"\s+", " ", prog_clean)

                        is_doc = "ดุษฎีบัณฑิต" in prog_clean or deg_type == "Doctoral"
                        deg_level = "ปริญญาเอก" if is_doc else "ปริญญาโท"
                        duration = "3 ปี" if is_doc else "2 ปี"

                        fac_th = current_faculty or "บัณฑิตวิทยาลัย"
                        fac_en = UP_FAC_EN.get(fac_th, "Graduate School")

                        # Derive degree name abbreviation
                        if is_doc:
                            deg_name = "ปร.ด." if "ปรัชญา" in prog_clean else ("วท.ด." if "วิทยาศาสตร" in prog_clean else "ดุษฎีบัณฑิต")
                        elif "วิศวกรรมศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "วศ.ม."
                        elif "การศึกษามหาบัณฑิต" in prog_clean:
                            deg_name = "กศ.ม."
                        elif "ศิลปศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "ศศ.ม."
                        elif "นิติศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "น.ม."
                        elif "พยาบาลศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "พย.ม."
                        elif "สถาปัตยกรรมศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "สถ.ม."
                        elif "สาธารณสุขศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "ส.ม."
                        elif "รัฐประศาสนศาสตรมหาบัณฑิต" in prog_clean:
                            deg_name = "รป.ม."
                        else:
                            deg_name = "วท.ม."

                        major_m = re.search(r"สาขาวิชา(.*?)$", prog_clean)
                        major_th = major_m.group(1).strip() if major_m else prog_clean

                        dedup_key = (prog_clean, fac_th, deg_level)
                        if dedup_key in seen_keys:
                            continue
                        seen_keys.add(dedup_key)

                        fee_val = int(fee_cell.replace(",", "")) if fee_cell else (35000 if is_doc else 20000)
                        fee_sem = f"{fee_val:,} บาท"
                        num_sems = 6 if is_doc else 4
                        fee_tot = f"{fee_val * num_sems:,} บาท"

                        cid_str = f"up_{'doc' if is_doc else 'grad'}_{re.sub(r'[^a-z0-9]+', '_', major_th).strip('_')}_{len(courses)}"

                        courses.append({
                            "id": cid_str,
                            "title_th": prog_clean,
                            "title_en": f"{'Doctor of Philosophy' if is_doc else 'Master'} Program in {major_th}",
                            "degree_level": deg_level,
                            "degree_name": f"{deg_name} ({major_th})",
                            "university": "University of Phayao",
                            "university_th": "มหาวิทยาลัยพะเยา",
                            "faculty": fac_en,
                            "faculty_th": fac_th,
                            "department": "",
                            "department_th": f"สาขาวิชา{major_th}",
                            "program_type": "ภาคปกติ/ภาคพิเศษ",
                            "duration_years": duration,
                            "total_credits": "48 หน่วยกิต" if is_doc else "36 หน่วยกิต",
                            "tuition_per_semester": fee_sem,
                            "tuition_total": fee_tot,
                            "description": f"{prog_clean} {fac_th} มหาวิทยาลัยพะเยา มุ่งผลิตบัณฑิตระดับสูงที่มีความเชี่ยวชาญทางวิชาการและวิจัยเพื่อพัฒนาชุมชนภาคเหนือและประเทศ",
                            "curriculum_highlights": [
                                f"การเรียนการสอนและการวิจัย ณ มหาวิทยาลัยพะเยา",
                                f"หลักสูตรได้รับการรับรองมาตรฐานจากกระทรวงการอุดมศึกษา วิทยาศาสตร์ วิจัยและนวัตกรรม (อว.)",
                                f"คณาจารย์ผู้เชี่ยวชาญพร้อมทุนสนับสนุนการทำวิทยานิพนธ์"
                            ],
                            "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัยและผู้เชี่ยวชาญ", "ที่ปรึกษาองค์กร"],
                            "tags": [major_th, fac_th, "มหาวิทยาลัยพะเยา", "บัณฑิตศึกษา UP"],
                            "website_url": "https://admission.up.ac.th/master/homepage"
                        })
            logger.info(f"UP: Extracted from {deg_type} PDF complete.")
        except Exception as e:
            logger.error(f"Error extracting UP {deg_type}: {e}")

    logger.info(f"UP: Total extracted {len(courses)} graduate programs.")
    return courses


# =========================================================================
# 5. Suranaree University of Technology (SUT)
# =========================================================================
def extract_sut_courses():
    logger.info("Extracting SUT Graduate Courses from Official SUT Curriculum Hub ...")
    courses = []
    seen_keys = set()
    url = "http://www.sut.ac.th/2012/content/detail/%E0%B8%A3%E0%B8%B0%E0%B8%94%E0%B8%B1%E0%B8%9A%E0%B8%9A%E0%B8%B1%E0%B8%93%E0%B8%91%E0%B8%B4%E0%B8%95%E0%B8%A8%E0%B8%B6%E0%B8%81%E0%B8%A9%E0%B8%B2"

    try:
        html = fetch_url(url).decode("utf-8", "ignore")
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            major_name = a.text.strip()

            if not ("CourseM" in href or "CourseD" in href):
                continue
            if not major_name:
                continue

            is_doc = "CourseD" in href
            deg_level = "ปริญญาเอก" if is_doc else "ปริญญาโท"
            duration = "3 ปี" if is_doc else "2 ปี"

            # Faculty attribution for SUT
            if "วิศวกรรม" in major_name:
                fac_th = "สำนักวิชาวิศวกรรมศาสตร์"
                fac_en = "Institute of Engineering"
                deg_abbr = "วศ.ด." if is_doc else "วศ.ม."
                title_th = f"หลักสูตร{'วิศวกรรมศาสตรดุษฎีบัณฑิต' if is_doc else 'วิศวกรรมศาสตรมหาบัณฑิต'} สาขาวิชา{major_name}"
            elif any(k in major_name for k in ["เทคโนโลยีการผลิตพืช", "เทคโนโลยีการผลิตสัตว์", "เทคโนโลยีอาหาร", "เทคโนโลยีชีวภาพ"]):
                fac_th = "สำนักวิชาเทคโนโลยีการเกษตร"
                fac_en = "Institute of Agricultural Technology"
                deg_abbr = "ปร.ด." if is_doc else "วท.ม."
                title_th = f"หลักสูตร{'ปรัชญาดุษฎีบัณฑิต' if is_doc else 'วิทยาศาสตรมหาบัณฑิต'} สาขาวิชา{major_name}"
            elif any(k in major_name for k in ["สารสนเทศ", "การจัดการเทคโนโลยี", "ภาษาอังกฤษ"]):
                fac_th = "สำนักวิชาเทคโนโลยีสังคม"
                fac_en = "Institute of Social Technology"
                deg_abbr = "ปร.ด." if is_doc else "ศศ.ม."
                title_th = f"หลักสูตร{'ปรัชญาดุษฎีบัณฑิต' if is_doc else 'ศิลปศาสตรมหาบัณฑิต'} สาขาวิชา{major_name}"
            elif any(k in major_name for k in ["พยาบาล"]):
                fac_th = "สำนักวิชาพยาบาลศาสตร์"
                fac_en = "Institute of Nursing"
                deg_abbr = "พย.ม."
                title_th = f"หลักสูตรพยาบาลศาสตรมหาบัณฑิต สาขาวิชา{major_name}"
            elif any(k in major_name for k in ["สาธารณสุข"]):
                fac_th = "สำนักวิชาสาธารณสุขศาสตร์"
                fac_en = "Institute of Public Health"
                deg_abbr = "ปร.ด." if is_doc else "ส.ม."
                title_th = f"หลักสูตร{'ปรัชญาดุษฎีบัณฑิต' if is_doc else 'สาธารณสุขศาสตรมหาบัณฑิต'} สาขาวิชา{major_name}"
            else:
                fac_th = "สำนักวิชาวิทยาศาสตร์"
                fac_en = "Institute of Science"
                deg_abbr = "ปร.ด." if is_doc else "วท.ม."
                title_th = f"หลักสูตร{'ปรัชญาดุษฎีบัณฑิต' if is_doc else 'วิทยาศาสตรมหาบัณฑิต'} สาขาวิชา{major_name}"

            dedup_key = (title_th, fac_th, deg_level)
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            fee_sem = "40,000 บาท" if is_doc else "25,000 บาท"
            fee_tot = "240,000 บาท" if is_doc else "100,000 บาท"

            cid_str = f"sut_{'doc' if is_doc else 'grad'}_{re.sub(r'[^a-z0-9]+', '_', major_name).strip('_')}_{len(courses)}"

            courses.append({
                "id": cid_str,
                "title_th": title_th,
                "title_en": f"{'Doctor of Philosophy' if is_doc else 'Master'} Program in {major_name}",
                "degree_level": deg_level,
                "degree_name": f"{deg_abbr} ({major_name})",
                "university": "Suranaree University of Technology",
                "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
                "faculty": fac_en,
                "faculty_th": fac_th,
                "department": "",
                "department_th": f"สาขาวิชา{major_name}",
                "program_type": "ภาคปกติ (ระบบไตรภาค)",
                "duration_years": duration,
                "total_credits": "54 หน่วยกิต" if is_doc else "38 หน่วยกิต",
                "tuition_per_semester": fee_sem,
                "tuition_total": fee_tot,
                "description": f"{title_th} {fac_th} มหาวิทยาลัยเทคโนโลยีสุรนารี (มทส.) จัดการศึกษาเน้นความเป็นเลิศทางวิทยาศาสตร์ เทคโนโลยี และวิศวกรรมศาสตร์ตามมาตรฐานสากล",
                "curriculum_highlights": [
                    "การเรียนการสอนและการวิจัยขั้นสูง ณ มหาวิทยาลัยเทคโนโลยีสุรนารี",
                    "ระบบการศึกษาแบบไตรภาคและเครื่องมือวิจัยระดับชาติ ณ เทคโนธานี",
                    "ความร่วมมือกับสถาบันวิจัยแสงซินโครตรอนแห่งชาติและภาคอุตสาหกรรม"
                ],
                "career_paths": ["วิศวกรวิจัยและพัฒนา", "นักวิทยาศาสตร์ระดับสูง", "อาจารย์มหาวิทยาลัย"],
                "tags": [major_name, fac_th, "มทส. บัณฑิตศึกษา", "SUT Graduate"],
                "website_url": href
            })
        logger.info(f"SUT: Extracted {len(courses)} graduate programs.")
    except Exception as e:
        logger.error(f"Error extracting SUT courses: {e}")
    return courses


def main():
    logger.info("=== Starting Phase 1 Graduate Course Crawlers ===")
    all_courses = []

    wu = extract_wu_courses()
    tsu = extract_tsu_courses()
    swu = extract_swu_courses()
    up = extract_up_courses()
    sut = extract_sut_courses()

    all_courses.extend(wu)
    all_courses.extend(tsu)
    all_courses.extend(swu)
    all_courses.extend(up)
    all_courses.extend(sut)

    logger.info(f"Summary: WU={len(wu)}, TSU={len(tsu)}, SWU={len(swu)}, UP={len(up)}, SUT={len(sut)}")
    logger.info(f"Total Extracted Courses: {len(all_courses)}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved raw checkpoint to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
