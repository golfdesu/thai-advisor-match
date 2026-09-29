# -*- coding: utf-8 -*-
"""
Headless Autonomous Crawler for Phase 3 Graduate Courses (โท/เอก):
  1. Mae Fah Luang University (MFU - มหาวิทยาลัยแม่ฟ้าหลวง)
  2. Maejo University (MJU - มหาวิทยาลัยแม่โจ้)

Outputs raw extracted courses to backend/data/agent_states/phase3_courses_raw.json.
"""
import os
import sys
import re
import json
import logging
import ssl
import io
import urllib.request
from bs4 import BeautifulSoup
import pypdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "phase3_courses_raw.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("crawl_phase3")

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
# 1. MFU Crawler (Mae Fah Luang University)
# ==========================================
MFU_SCHOOL_EN = {
    "สำนักวิชาศิลปศาสตร์": "School of Liberal Arts",
    "สำนักวิชานิติศาสตร์": "School of Law",
    "สำนักวิชาแพทยศาสตร์": "School of Medicine",
    "สำนักวิชาทันตแพทยศาสตร์": "School of Dentistry",
    "สำนักวิชานวัตกรรมสังคม": "School of Social Innovation",
    "สำนักวิชาการแพทย์บูรณาการ": "School of Integrative Medicine",
    "สำนักวิชาการจัดการ": "School of Management",
    "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์": "School of Applied Digital Technology",
    "สำนักวิชาอุตสาหกรรมเกษตร": "School of Agro-Industry",
    "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง": "School of Cosmetic Science",
    "สำนักวิชาวิทยาศาสตร์": "School of Science",
    "สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ": "School of Anti-Aging and Regenerative Medicine",
    "สำนักวิชาวิทยาศาสตร์สุขภาพ": "School of Health Science",
    "สำนักวิชาพยาบาลศาสตร์": "School of Nursing",
    "สำนักวิชาจีนวิทยา": "School of Sinology"
}

def crawl_mfu():
    logger.info("--- Starting MFU Graduate Course Crawl ---")
    courses = []

    pages = [
        ("https://programme.mfu.ac.th/mfu-programme/programme-master-degree.html", "ปริญญาโท", "2 ปี", "มหาบัณฑิต"),
        ("https://programme.mfu.ac.th/mfu-programme/programme-doctoral-degree.html", "ปริญญาเอก", "3 ปี", "ปร.ด.")
    ]

    seen = set()
    for page_url, deg_level, dur, deg_name in pages:
        data = fetch_url(page_url)
        if not data:
            continue
        soup = BeautifulSoup(data.decode("utf-8", "ignore"), "html.parser")

        # Traverse headings and sections
        for h in soup.find_all(["h3", "h4", "h5"]):
            school_th = h.text.strip().replace("\n", " ")
            if "สำนักวิชา" not in school_th:
                continue

            school_en = MFU_SCHOOL_EN.get(school_th, "School of Postgraduate Studies")

            # Find associated program links in the parent container
            container = h.find_parent("div", class_=lambda x: x and any(c in x for c in ["col", "row", "card", "section", "accordion", "item", "box"]))
            if not container:
                continue

            for a in container.find_all("a"):
                raw_text = a.text.strip().replace("\n", " ")
                href = a.get("href", "")
                if not raw_text or len(raw_text) < 5 or "สำนักวิชา" in raw_text or "อ่านต่อ" in raw_text:
                    continue

                # Extract English title from href slug if available
                slug_match = re.search(r"/(?:master|doctor)-of-[^/]+\.html", href)
                en_title = ""
                if slug_match:
                    slug = slug_match.group(0).replace("/", "").replace(".html", "")
                    en_title = slug.replace("-", " ").title()

                degree_prefix = "หลักสูตรปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "หลักสูตรมหาบัณฑิต"
                if "มหาบัณฑิต" in raw_text or "ดุษฎีบัณฑิต" in raw_text:
                    full_th = f"หลักสูตร{raw_text}" if not raw_text.startswith("หลักสูตร") else raw_text
                elif raw_text.startswith("สาขา"):
                    full_th = f"{degree_prefix} {raw_text}"
                else:
                    full_th = f"{degree_prefix} สาขาวิชา{raw_text}"

                full_th = re.sub(r"\s+", " ", full_th).strip()
                if (full_th, deg_level) in seen:
                    continue
                seen.add((full_th, deg_level))

                courses.append({
                    "title_th": full_th,
                    "title_en": en_title,
                    "degree_level": deg_level,
                    "degree_name": deg_name,
                    "university": "Mae Fah Luang University",
                    "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
                    "faculty": school_en,
                    "faculty_th": school_th,
                    "department": "",
                    "department_th": "",
                    "duration_years": dur,
                    "tuition_per_semester": "45,000 - 90,000 บาท",
                    "tuition_total": "",
                    "program_type": "นานาชาติ",
                    "description": f"{full_th} {en_title} {school_th} มหาวิทยาลัยแม่ฟ้าหลวง",
                    "curriculum_highlights": ["หลักสูตรนานาชาติ", school_th, "มหาวิทยาลัยแม่ฟ้าหลวง"],
                    "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัยระดับนานาชาติ", "ผู้เชี่ยวชาญเฉพาะทาง"],
                    "tags": [deg_level, school_th, "มฟล", "MFU", "International Program"],
                    "website_url": "https://programme.mfu.ac.th" + href if href.startswith("/") else href
                })

    logger.info(f"MFU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# 2. MJU Crawler (Maejo University)
# ==========================================
MJU_FACULTY_MAP = [
    (r"การท่องเที่ยว|ท่องเที", "คณะพัฒนาการท่องเที่ยว", "Faculty of Tourism Development"),
    (r"เกษตรอินทรีย์|ปฐพี|พืชไร่|พืชสวน|ส่งเสริมการเกษตร|อารักขาพืช|เทคโนโลยีชีวภาพทางพืช", "คณะผลิตกรรมการเกษตร", "Faculty of Agricultural Production"),
    (r"เศรษฐศาสตร์|บริหารธุรกิจ|บัญชี|บริหารศาสตร์|การตลาด|การเงิน", "คณะบริหารธุรกิจ", "Faculty of Business Administration"),
    (r"สหวิทยาการเกษตร|นวัตกรรมเทคโนโลยี", "คณะผลิตกรรมการเกษตร", "Faculty of Agricultural Production"),
    (r"บริหารสาธารณะ|รัฐประศาสน", "วิทยาลัยบริหารศาสตร์", "School of Administrative Studies"),
    (r"วิศวกรรมพลังงาน|พลังงานทดแทน", "วิทยาลัยพลังงานทดแทน", "School of Renewable Energy"),
    (r"สุขภาพชุมชน|พยาบาล", "คณะพยาบาลศาสตร์", "Faculty of Nursing"),
    (r"ประมง|ทรัพยากรทางนำ|ทรัพยากรทางน้ำ|เพาะเลี้ยง", "คณะเทคโนโลยีการประมงและทรัพยากรทางน้ำ", "Faculty of Fisheries Technology and Aquatic Resources"),
    (r"ผังเมือง|ภูมิทัศน์|สถาปัตยกรรม|การออกแบบ", "คณะสถาปัตยกรรมศาสตร์และการออกแบบสิ่งแวดล้อม", "Faculty of Architecture and Environmental Design"),
    (r"วิศวกรรมอาหาร|วิศวกรรมเกษตร|นวัตกรรมวิทยาศาสตร์และเทคโนโลยีอาหาร|วิทยาศาสตร์และเทคโนโลยีอาหาร", "คณะวิศวกรรมและอุตสาหกรรมเกษตร", "Faculty of Engineering and Agro-Industry"),
    (r"สัตวศาสตร์|สัตว์ปีก|โคนม", "คณะสัตวศาสตร์และเทคโนโลยี", "Faculty of Animal Science and Technology"),
    (r"เคมี|ฟิสิกส์|ชีว|พันธุศาสตร์|นาโน|วิทยาการคอมพิวเตอร์|เทคโนโลยีสารสนเทศ", "คณะวิทยาศาสตร์", "Faculty of Science"),
    (r"ศิลปศาสตร์|ภาษา", "คณะศิลปศาสตร์", "Faculty of Liberal Arts"),
    (r"สัตวแพทย์", "คณะสัตวแพทยศาสตร์", "Faculty of Veterinary Medicine"),
]

def decode_mju_pdf_text(s: str) -> str:
    def repl(m):
        code = int(m.group(1), 16)
        return chr(code)
    cleaned = re.sub(r'/uni([0-9A-Fa-f]{4})', repl, s)
    cleaned = cleaned.replace('.small', '').replace('.narrow', '').replace('/', '')
    # Thai tone mark fix
    cleaned = cleaned.replace("ท่องเที", "ท่องเที่ยว")
    cleaned = cleaned.replace("อย่างยั", "อย่างยั่งยืน")
    cleaned = cleaned.replace("ทรัพยากรทางนำ้", "ทรัพยากรทางน้ำ")
    cleaned = cleaned.replace("เศรษฐศาสตร์ดิจิทัลและ", "เศรษฐศาสตร์ดิจิทัลและนวัตกรรม")
    cleaned = cleaned.replace("การจัดการป", "การจัดการป่าไม้")
    cleaned = cleaned.replace("เทคโนโลยีสิ", "เทคโนโลยีสิ่งแวดล้อม")
    return cleaned

def crawl_mju():
    logger.info("--- Starting MJU Graduate Course Crawl ---")
    courses = []

    base_url = "https://admissions.mju.ac.th/graduate/"
    pdfs = [
        ("FileUpload/TuitionFeeMaster.pdf", "ปริญญาโท", "2 ปี", "มหาบัณฑิต", "25,000 - 45,000 บาท"),
        ("FileUpload/TuitionFeeDoctoral.pdf", "ปริญญาเอก", "3 ปี", "ปร.ด.", "45,000 - 85,000 บาท")
    ]

    seen = set()
    for pdf_rel, deg_level, dur, deg_name, tuition in pdfs:
        pdf_url = base_url + pdf_rel
        data = fetch_url(pdf_url)
        if not data:
            continue
        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
            for page in reader.pages:
                raw_txt = page.extract_text() or ""
                decoded = decode_mju_pdf_text(raw_txt)
                for line in decoded.split("\n"):
                    line = line.strip()
                    if "สาขาวิชา" not in line and "สาขา" not in line:
                        continue
                    m = re.search(r"สาขาวิชา\s*([ก-๙a-zA-Z\s]+)", line)
                    if not m:
                        continue
                    maj = m.group(1).strip()
                    maj = re.sub(r"[\d,]+.*$", "", maj).strip()
                    maj = re.sub(r"\s+", " ", maj)
                    if not maj or len(maj) < 3 or (maj, deg_level) in seen:
                        continue
                    seen.add((maj, deg_level))

                    deg_prefix = "หลักสูตรปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "หลักสูตรวิทยาศาสตรมหาบัณฑิต"
                    if any(b in maj for b in ["บริหาร", "บัญชี", "การจัดการ"]):
                        deg_prefix = "หลักสูตรปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "หลักสูตรบริหารธุรกิจมหาบัณฑิต"
                    elif "เศรษฐศาสตร์" in maj:
                        deg_prefix = "หลักสูตรปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "หลักสูตรเศรษฐศาสตรมหาบัณฑิต"
                    elif "วิศวกรรม" in maj:
                        deg_prefix = "หลักสูตรปรัชญาดุษฎีบัณฑิต" if deg_level == "ปริญญาเอก" else "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต"

                    full_th = f"{deg_prefix} สาขาวิชา{maj}"

                    fac_th = "บัณฑิตวิทยาลัย"
                    fac_en = "Graduate School"
                    for pat, fth, fen in MJU_FACULTY_MAP:
                        if re.search(pat, maj):
                            fac_th = fth
                            fac_en = fen
                            break

                    courses.append({
                        "title_th": full_th,
                        "title_en": "",
                        "degree_level": deg_level,
                        "degree_name": deg_name,
                        "university": "Maejo University",
                        "university_th": "มหาวิทยาลัยแม่โจ้",
                        "faculty": fac_en,
                        "faculty_th": fac_th,
                        "department": "",
                        "department_th": "",
                        "duration_years": dur,
                        "tuition_per_semester": tuition,
                        "tuition_total": "",
                        "program_type": "ภาคปกติ",
                        "description": f"{full_th} {fac_th} มหาวิทยาลัยแม่โจ้",
                        "curriculum_highlights": ["หลักสูตรบัณฑิตศึกษา", fac_th, "มหาวิทยาลัยแม่โจ้"],
                        "career_paths": ["อาจารย์มหาวิทยาลัย", "นักวิจัยด้านการเกษตรและเทคโนโลยี", "ผู้เชี่ยวชาญเฉพาะทาง"],
                        "tags": [deg_level, fac_th, "มช", "ม.แม่โจ้", "MJU"],
                        "website_url": pdf_url
                    })
        except Exception as e:
            logger.error(f"Error parsing MJU PDF {pdf_url}: {e}")

    logger.info(f"MJU Extracted: {len(courses)} courses")
    return courses

# ==========================================
# Main Execution
# ==========================================
def main():
    logger.info("=== Starting Phase 3 Graduate Course Autonomous Crawl ===")
    all_courses = []

    mfu = crawl_mfu()
    all_courses.extend(mfu)

    mju = crawl_mju()
    all_courses.extend(mju)

    logger.info(f"=== Crawl Summary ===")
    logger.info(f"  MFU: {len(mfu)} courses")
    logger.info(f"  MJU: {len(mju)} courses")
    logger.info(f"  Total Raw Extracted: {len(all_courses)}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Successfully checkpointed raw courses to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
