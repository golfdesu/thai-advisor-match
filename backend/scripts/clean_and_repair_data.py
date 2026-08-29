import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

# 1. Standard University Name Mapping
UNIVERSITY_MAP = {
    "Chulalongkorn University": "จุฬาลงกรณ์มหาวิทยาลัย",
    "Chiang Mai University": "มหาวิทยาลัยเชียงใหม่",
    "Mahidol University": "มหาวิทยาลัยมหิดล",
    "Kasetsart University": "มหาวิทยาลัยเกษตรศาสตร์",
    "Thammasat University": "มหาวิทยาลัยธรรมศาสตร์",
    "Khon Kaen University": "มหาวิทยาลัยขอนแก่น",
    "Prince of Songkla University": "มหาวิทยาลัยสงขลานครินทร์",
    "King Mongkut's Institute of Technology Ladkrabang": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "King Mongkut's University of Technology Thonburi": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "King Mongkut's University of Technology North Bangkok": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "Suranaree University of Technology": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "Mae Fah Luang University": "มหาวิทยาลัยแม่ฟ้าหลวง",
    "National Institute of Development Administration": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
    "Srinakharinwirot University": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "Silpakorn University": "มหาวิทยาลัยศิลปากร",
    "Burapha University": "มหาวิทยาลัยบูรพา",
    "Ubon Ratchathani University": "มหาวิทยาลัยอุบลราชธานี",
    "University of Phayao": "มหาวิทยาลัยพะเยา",
    "Maejo University": "มหาวิทยาลัยแม่โจ้",
    "Walailak University": "มหาวิทยาลัยวลัยลักษณ์",
    "Suan Sunandha Rajabhat University": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
    "Suan Dusit University": "มหาวิทยาลัยสวนดุสิต",
    "Bangkok University": "มหาวิทยาลัยกรุงเทพ",
    "Assumption University": "มหาวิทยาลัยอัสสัมชัญ",
    "Rangsit University": "มหาวิทยาลัยรังสิต",
    "Sripatum University": "มหาวิทยาลัยศรีปทุม",
    "Ramkhamhaeng University": "มหาวิทยาลัยรามคำแหง",
    "Sukhothai Thammathirat Open University": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
    "Rajamangala University of Technology Thanyaburi": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
    "Rajamangala University of Technology Krungthep": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
    "Rajamangala University of Technology Phra Nakhon": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
    "University of the Thai Chamber of Commerce": "มหาวิทยาลัยหอการค้าไทย",
    "Mahasarakham University": "มหาวิทยาลัยมหาสารคาม",
    "Chiang Mai Rajabhat University": "มหาวิทยาลัยราชภัฏเชียงใหม่",
}

# 2. Specific Course Fixes Map
SPECIFIC_COURSE_FIXES = {
    "cu-med-md-thai": {
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "faculty_th": "คณะแพทยศาสตร์",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"
    },
    "RAMA-MD-UG": {
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "dt-mu-dds-international": {
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Dental Surgery Program (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "bahs-cmu": {
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชามนุษยศาสตร์และความยั่งยืน (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Arts in Humanities and Sustainability (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (มนุษยศาสตร์และความยั่งยืน)",
        "faculty_th": "คณะมนุษยศาสตร์",
        "university_th": "มหาวิทยาลัยเชียงใหม่"
    },
    "sut_phd_english_lang": {
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ภาษาอังกฤษศึกษา)"
    },
    "sut_phd_civil_eng": {
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมโยธา)"
    },
    "au_simba": {
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (AU SIMBA)",
        "title_en": "Smart MBA (AU SIMBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)"
    },
    "sut-international-engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต (หลักสูตรนานาชาติ)",
        "title_en": "International Engineering Program",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี"
    },
    "sut-hospitality-technology-innovation": {
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชานวัตกรรมเทคโนโลยีการบริการ",
        "title_en": "Bachelor of Science in Hospitality Technology Innovation",
        "faculty_th": "สำนักวิชาเทคโนโลยีสังคม",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี"
    },
    # KU Engineering Bachelor Programs
    "ku-eng-aerospace": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการบินและอวกาศ", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-computer": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-chemical": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-mechanical": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-water-resources": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมทรัพยากรน้ำ", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-electrical": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-materials": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมวัสดุ", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-civil": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-environmental": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมสิ่งแวดล้อม", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-industrial": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการ", "faculty_th": "คณะวิศวกรรมศาสตร์", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-kps-agricultural-engineering": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเกษตร", "faculty_th": "คณะวิศวกรรมศาสตร์ กำแพงแสน", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-kps-irrigation-engineering": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชลประทาน", "faculty_th": "คณะวิศวกรรมศาสตร์ กำแพงแสน", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    "ku-eng-kps-food-engineering": {"title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอาหาร", "faculty_th": "คณะวิศวกรรมศาสตร์ กำแพงแสน", "university_th": "มหาวิทยาลัยเกษตรศาสตร์"},
    # CU Science Programs
    "CU-SCI-BSC-APPCHEM-INT": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเคมีประยุกต์ (หลักสูตรนานาชาติ)", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-BIOTECH-INT": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ (หลักสูตรนานาชาติ)", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-CHE": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเคมีวิศวกรรม", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-CS": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-ENV": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์สิ่งแวดล้อม", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-FOOD": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีทางอาหาร", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-GEN": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาพันธุศาสตร์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-GEO": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาธรณีวิทยา", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-INDST-INT": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม (หลักสูตรนานาชาติ)", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-IPT": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีทางภาพและการพิมพ์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-MAR": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์ทางทะเล", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-MATH": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-MATS": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวัสดุศาสตร์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-MICRO": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาจุลชีววิทยา", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-PHYS": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาฟิสิกส์", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    "CU-SCI-BSC-STAT": {"title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาสถิติ", "faculty_th": "คณะวิทยาศาสตร์", "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"},
    # Additional English titles fixes & normalizations
    "MEDICAL-DOCTOR-PROGRAM": {
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (Doctor of Medicine International Program)",
        "title_en": "The Medical Doctor Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MCTM-PED": {
        "title_th": "หลักสูตรอายุรศาสตร์เขตร้อนคลินิกมหาบัณฑิต สาขาวิชากุมารเวชศาสตร์เขตร้อน (หลักสูตรนานาชาติ)",
        "title_en": "Master of Clinical Tropical Medicine in Tropical Pediatrics (M.C.T.M.(Trop.Ped.))",
        "degree_level": "ปริญญาโท",
        "degree_name": "อ.ข.ม. (กุมารเวชศาสตร์เขตร้อน)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MCTM": {
        "title_th": "หลักสูตรอายุรศาสตร์เขตร้อนคลินิกมหาบัณฑิต (หลักสูตรนานาชาติ)",
        "title_en": "Master of Clinical Tropical Medicine (M.C.T.M.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "อ.ข.ม. (อายุรศาสตร์เขตร้อนคลินิก)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MPH-INT": {
        "title_th": "หลักสูตรสาธารณสุขศาสตรมหาบัณฑิต (หลักสูตรนานาชาติ)",
        "title_en": "Master of Public Health International Program",
        "degree_level": "ปริญญาโท",
        "degree_name": "ส.ม. (สาธารณสุขศาสตร์)",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MSC-BHI": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสารสนเทศชีวการแพทย์และสุขภาพ (หลักสูตรนานาชาติ)",
        "title_en": "Master of Science in Biomedical and Health Informatics (M.Sc.(B.H.I.))",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (สารสนเทศชีวการแพทย์และสุขภาพ)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MSC-SCHOOL-HEALTH": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสุขภาพโรงเรียน (หลักสูตรนานาชาติ)",
        "title_en": "Master of Science (School Health)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (สุขภาพโรงเรียน)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "MSC-TROP-MED": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาอายุรศาสตร์เขตร้อน (หลักสูตรนานาชาติ)",
        "title_en": "Master of Science in Tropical Medicine (M.Sc.(Trop.Med.))",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (อายุรศาสตร์เขตร้อน)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "PHD-CLIN-TROP-MED": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาอายุรศาสตร์เขตร้อนคลินิก (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy in Clinical Tropical Medicine (Ph.D.(Clin.Trop.Med.))",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (อายุรศาสตร์เขตร้อนคลินิก)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "PHD-PH": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสุขภาพดาวเคราะห์ (หลักสูตรนานาชาติ)",
        "title_en": "PhD Program in Planetary Health",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (สุขภาพดาวเคราะห์)",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "PHD-TROP-MED": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาอายุรศาสตร์เขตร้อน (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy in Tropical Medicine (Ph.D.(Trop.Med.))",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (อายุรศาสตร์เขตร้อน)",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "PHD-WLM": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาภาวะผู้นำและการจัดการสุขภาพและสุขภาวะ (หลักสูตรนานาชาติ)",
        "title_en": "Ph.D. Program in Wellness Leadership and Management (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ภาวะผู้นำและการจัดการสุขภาพและสุขภาวะ)",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "RAMA-MNS-INT": {
        "title_th": "หลักสูตรพยาบาลศาสตรมหาบัณฑิต (หลักสูตรนานาชาติ)",
        "title_en": "Master of Nursing Science, International Program",
        "degree_level": "ปริญญาโท",
        "degree_name": "พย.ม. (พยาบาลศาสตร์)",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "RAMA-MSM-OPHTH": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์ (วิชาเอกจักษุวิทยา หลักสูตรนานาชาติ)",
        "title_en": "Master of Science in Medicine, International Program (Major in Ophthalmology)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาศาสตร์การแพทย์)",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "cu-med-grad-dip-dermatology": {
        "title_th": "หลักสูตรประกาศนียบัตรบัณฑิตชั้นสูงทางวิทยาศาสตร์การแพทย์คลินิก สาขาวิชาตจวิทยา (โรคผิวหนัง)",
        "title_en": "Higher Graduate Diploma of Clinical Sciences Program in Dermatology",
        "degree_level": "ประกาศนียบัตรบัณฑิต (ชั้นสูง)",
        "degree_name": "ป.บัณฑิตชั้นสูง (ตจวิทยา)",
        "faculty_th": "คณะแพทยศาสตร์",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"
    },
    "cu-med-grad-dip-mental-health": {
        "title_th": "หลักสูตรประกาศนียบัตรบัณฑิตทางวิทยาศาสตร์การแพทย์คลินิก สาขาวิชาสุขภาพจิต",
        "title_en": "Graduate Diploma Program in Mental Health",
        "degree_level": "ประกาศนียบัตรบัณฑิต",
        "degree_name": "ป.บัณฑิต (สุขภาพจิต)",
        "faculty_th": "คณะแพทยศาสตร์",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"
    },
    "cu-med-higher-grad-dip-otolaryngology": {
        "title_th": "หลักสูตรประกาศนียบัตรบัณฑิตชั้นสูงทางวิทยาศาสตร์การแพทย์คลินิก สาขาวิชาโสต ศอ นาสิกวิทยา",
        "title_en": "Higher Graduate Diploma of Clinical Sciences Program in Otolaryngology",
        "degree_level": "ประกาศนียบัตรบัณฑิต (ชั้นสูง)",
        "degree_name": "ป.บัณฑิตชั้นสูง (โสต ศอ นาสิกวิทยา)",
        "faculty_th": "คณะแพทยศาสตร์",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"
    },
    "cu-med-higher-grad-dip-pediatrics": {
        "title_th": "หลักสูตรประกาศนียบัตรบัณฑิตชั้นสูงทางวิทยาศาสตร์การแพทย์คลินิก สาขาวิชากุมารเวชศาสตร์",
        "title_en": "Higher Graduate Diploma in Clinical Sciences Program in Pediatrics",
        "degree_level": "ประกาศนียบัตรบัณฑิต (ชั้นสูง)",
        "degree_name": "ป.บัณฑิตชั้นสูง (กุมารเวชศาสตร์)",
        "faculty_th": "คณะแพทยศาสตร์",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย"
    },
    "msc-cs": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
        "title_en": "Master of Science in Computer Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "msc-cy": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาความมั่นคงปลอดภัยไซเบอร์และการประกันสารสนเทศ",
        "title_en": "Master of Science in Cyber Security and Information Assurance",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (ความมั่นคงปลอดภัยไซเบอร์ฯ)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "msc-gt": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีเกมและเกมมิฟิเคชัน",
        "title_en": "Master of Science in Game Technology and Gamification",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (เทคโนโลยีเกมและเกมมิฟิเคชัน)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "mu-sc-msc-env-tox-tech-mgmt": {
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพิษวิทยาสิ่งแวดล้อม เทคโนโลยีและการจัดการ (หลักสูตรนานาชาติ)",
        "title_en": "Master's Degree Program in Environmental Toxicology, Technology and Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (พิษวิทยาสิ่งแวดล้อม เทคโนโลยีและการจัดการ)",
        "faculty_th": "คณะวิทยาศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "mu-sc-phd-botany": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพฤกษศาสตร์ (หลักสูตรนานาชาติ)",
        "title_en": "Ph.D. (Botany) (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (พฤกษศาสตร์)",
        "faculty_th": "คณะวิทยาศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    "mu-sc-phd-env-tox-tech-mgmt": {
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพิษวิทยาสิ่งแวดล้อม เทคโนโลยีและการจัดการ (หลักสูตรนานาชาติ)",
        "title_en": "Doctoral Program in Environmental Toxicology, Technology and Management",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (พิษวิทยาสิ่งแวดล้อม เทคโนโลยีและการจัดการ)",
        "faculty_th": "คณะวิทยาศาสตร์",
        "university_th": "มหาวิทยาลัยมหิดล"
    },
    # Non-standard degree levels normalization
    "si-short-training-clinical-observership": {
        "degree_level": "ประกาศนียบัตร",
        "degree_name": "ประกาศนียบัตรอบรมระยะสั้น",
    },
    "si-dermatology-fellowship": {
        "degree_level": "ประกาศนียบัตรบัณฑิต (ชั้นสูง)",
        "degree_name": "วุฒิบัตร/ป.บัณฑิตชั้นสูง (Fellowship Training)",
    },
    "si-ophthalmology-residency": {
        "degree_level": "ประกาศนียบัตรบัณฑิต (ชั้นสูง)",
        "degree_name": "วุฒิบัตรแพทย์ประจำบ้าน (Residency Training)",
    },
    "si-postgrad-education": {
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. / วุฒิบัตรบัณฑิตศึกษา",
    },
    "ku-eng-graduate": {
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมศาสตร์)",
    },
    "tse-graduate-study": {
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมศาสตร์)",
    },
}

def generate_smart_description(title_th: str, title_en: str, faculty_th: str, uni_th: str, degree_level: str) -> str:
    """Generate high quality curriculum description when original is missing."""
    clean_title = (title_th or title_en or "").replace("หลักสูตร", "").replace("สาขาวิชา", "").strip()
    fac = faculty_th or "คณะ"
    uni = uni_th or "มหาวิทยาลัย"
    deg = degree_level or "ระดับอุดมศึกษา"
    
    return f"หลักสูตร{clean_title} {deg} {fac} {uni} มุ่งเน้นการผลิตบัณฑิตและนักวิจัยที่มีองค์ความรู้ความเชี่ยวชาญระดับสูง ทักษะการปฏิบัติการจริง และการบูรณาการเทคโนโลยีสมัยใหม่ เพื่อตอบสนองความต้องการของภาคอุตสาหกรรม การวิจัยทางวิชาการ และการพัฒนานวัตกรรมแห่งอนาคต"

def generate_default_career_paths(title_th: str, title_en: str, faculty_th: str) -> list[str]:
    """Generate relevant career paths based on study field."""
    text = f"{title_th} {title_en} {faculty_th}".lower()
    
    if any(k in text for k in ["คอมพิวเตอร์", "computer", "ซอฟต์แวร์", "software", "ไซเบอร์", "cyber", "data", "ข้อมูล", "ict", "สารสนเทศ", "it"]):
        return ["Software Engineer", "Data Scientist / AI Engineer", "System Analyst & Architect", "Cybersecurity Specialist", "นักวิชาการ/นักวิจัยคอมพิวเตอร์"]
    elif any(k in text for k in ["วิศว", "engineer"]):
        return ["วิศวกรวิชาชีพประจำสถานประกอบการ", "วิศวกรควบคุมและวางแผนระบบ", "วิศวกรวิจัยและพัฒนานวัตกรรม (R&D)", "ที่ปรึกษาด้านวิศวกรรม", "ผู้ประกอบการด้านเทคโนโลยี"]
    elif any(k in text for k in ["แพทย์", "medicine", "medical", "doctor"]):
        return ["แพทย์เวชปฏิบัติทั่วไป/แพทย์เฉพาะทาง", "อาจารย์แพทย์และนักวิจัยทางการแพทย์", "ผู้บริหารงานบริการสุขภาพและโรงพยาบาล"]
    elif any(k in text for k in ["ทันต", "dental", "dentist"]):
        return ["ทันตแพทย์ทั่วไปและทันตแพทย์เฉพาะทาง", "อาจารย์ทันตแพทย์", "เจ้าของคลินิกทันตกรรม"]
    elif any(k in text for k in ["พยาบาล", "nurs"]):
        return ["พยาบาลวิชาชีพ", "พยาบาลเฉพาะทาง", "ผู้จัดการทางการพยาบาล", "อาจารย์พยาบาล"]
    elif any(k in text for k in ["เภสัช", "pharm"]):
        return ["เภสัชกรโรงพยาบาล/คลินิก", "เภสัชกรอุตสาหการ/ผลิตยา", "เภสัชกรวิจัยและพัฒนา", "ผู้ประกอบการร้านยา"]
    elif any(k in text for k in ["บริหาร", "business", "การตลาด", "market", "การจัดการ", "management", "mba"]):
        return ["ผู้จัดการและผู้บริหารฝ่ายธุรกิจ", "นักวิเคราะห์ธุรกิจและการตลาด", "ที่ปรึกษากลยุทธ์ทางธุรกิจ", "ผู้ประกอบการสตาร์ทอัพ/ธุรกิจส่วนตัว"]
    elif any(k in text for k in ["บัญชี", "account", "การเงิน", "financ"]):
        return ["นักบัญชีวิชาชีพ / ผู้สอบบัญชี (CPA)", "นักวิเคราะห์การเงินและการลงทุน", "ที่ปรึกษาด้านภาษีและการเงิน"]
    elif any(k in text for k in ["วิทยาศาสตร์", "science", "เคมี", "chem", "ฟิสิกส์", "physic", "ชีว", "bio", "พฤกษ"]):
        return ["นักวิทยาศาสตร์และนักวิจัยประจำห้องปฏิบัติการ", "นักควบคุมและประกันคุณภาพ (QA/QC)", "ผู้เชี่ยวชาญผลิตภัณฑ์ทางวิทยาศาสตร์", "อาจารย์/นักวิชาการ"]
    elif any(k in text for k in ["นิติ", "law", "กฎหมาย"]):
        return ["นิติกรประจำหน่วยงานรัฐและเอกชน", "ทนายความและที่ปรึกษากฎหมาย", "ผู้พิพากษา/พนักงานอัยการ"]
    elif any(k in text for k in ["ศิลปะ", "art", "นิเทศ", "comm", "สื่อ", "media", "ดีไซน์", "design"]):
        return ["Content Creator / สื่อสารมวลชน", "Creative Director & Graphic Designer", "นักสื่อสารองค์กรและประชาสัมพันธ์"]
    elif any(k in text for k in ["ศึกษา", "ครุ", "educat", "teach"]):
        return ["ครูและอาจารย์ประจำสถานศึกษา", "นักวิชาการศึกษา", "นักพัฒนาสื่อและนวัตกรรมการเรียนรู้"]
    else:
        return ["ผู้เชี่ยวชาญเฉพาะสาขาวิชาชีพ", "นักวิเคราะห์และพัฒนากลยุทธ์", "นักวิจัยและวิชาการ", "ผู้ประกอบการธุรกิจสร้างสรรค์"]

def generate_default_highlights(title_th: str, title_en: str, faculty_th: str) -> list[str]:
    """Generate default highlights for courses lacking highlights."""
    clean_title = (title_th or title_en or "").replace("หลักสูตร", "").replace("สาขาวิชา", "").strip()
    return [
        f"การเรียนรู้เชิงลึกและบูรณาการด้าน {clean_title}",
        "การฝึกปฏิบัติการจริงร่วมกับเครื่องมือและเทคโนโลยีทันสมัย",
        "เน้นการทำวิจัยและโครงงานที่ตอบโจทย์ภาคอุตสาหกรรมและสังคม"
    ]

def build_course_embedding_text(c: CourseDB) -> str:
    parts = [
        c.title_th or "",
        c.title_en or "",
        c.degree_level or "",
        c.degree_name or "",
        c.faculty_th or "",
        c.department_th or "",
        c.university_th or "",
        c.university or "",
        c.description or "",
        " ".join(c.curriculum_highlights) if c.curriculum_highlights else "",
        " ".join(c.career_paths) if c.career_paths else "",
        " ".join(c.tags) if c.tags else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

def clean_and_repair_all_data():
    print("=========================================================")
    print("🚀 เริ่มกระบวนการคลีนและแก้ไขข้อมูลทั้งหมดในฐานข้อมูล")
    print("=========================================================")
    
    db = SessionLocal()
    
    # ---------------------------------------------------------
    # STEP 0: FIX INVALID ID 'ไม่ระบุ' (CHULA BOTANY)
    # ---------------------------------------------------------
    print("\n[0/5] ตรวจสอบและแก้ไข Course ID ที่ไม่ถูกต้อง ('ไม่ระบุ')...")
    weird = db.query(CourseDB).filter(CourseDB.id == 'ไม่ระบุ').first()
    if weird:
        print(f"  -> พบหลักสูตร ID 'ไม่ระบุ': {weird.title_th} ({weird.university})")
        new_course = CourseDB(
            id="CU-SCI-BSC-BOTANY",
            title_th="หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาพฤกษศาสตร์",
            title_en="Bachelor of Science Program in Botany",
            degree_level="ปริญญาตรี",
            degree_name="วท.บ. (พฤกษศาสตร์)",
            university="Chulalongkorn University",
            university_th="จุฬาลงกรณ์มหาวิทยาลัย",
            faculty="Faculty of Science",
            faculty_th="คณะวิทยาศาสตร์",
            department="Department of Botany",
            department_th="ภาควิชาพฤกษศาสตร์",
            program_type="ภาคปกติ",
            duration_years="4 ปี",
            total_credits="134 หน่วยกิต",
            tuition_per_semester="21,000 บาท",
            tuition_total="168,000 บาท",
            description="มุ่งเน้นการศึกษาด้านพฤกษศาสตร์ ชีววิทยาของพืช อนุกรมวิธาน สรีรวิทยา พันธุศาสตร์ และเทคโนโลยีชีวภาพทางพืช",
            curriculum_highlights=["พฤกษศาสตร์เชิงลึกและการวิจัยพืชพรรณไทย", "การศึกษาพันธุศาสตร์และเทคโนโลยีชีวภาพพืช", "การฝึกปฏิบัติการภาคสนามและห้องปฏิบัติการมาตรฐานสูง"],
            career_paths=["นักวิทยาศาสตร์/นักวิจัยด้านพืช", "นักวิชาการเกษตรและสิ่งแวดล้อม", "ผู้เชี่ยวชาญด้านความหลากหลายทางชีวภาพ", "อาจารย์และนักวิชาการ"],
            tags=["Botany", "Plant Science", "Biology", "Science"],
            website_url="https://www.chula.ac.th/en/programs/25510011108862/"
        )
        emb_text = build_course_embedding_text(new_course)
        new_course.embedding_text = emb_text
        vec = embedding_service.get_embedding(emb_text)
        if vec:
            new_course.embedding = vec
        db.add(new_course)
        db.delete(weird)
        db.commit()
        print("  -> แก้ไขและแทนที่ด้วย ID 'CU-SCI-BSC-BOTANY' สำเร็จ!")
    else:
        print("  -> ไม่พบ Course ID 'ไม่ระบุ'")

    # ---------------------------------------------------------
    # STEP 1: FIX COURSES SPECIFIC & SYSTEMIC ISSUES
    # ---------------------------------------------------------
    print("\n[1/5] ดำเนินการแก้ไขชื่อมหาวิทยาลัย ระดับปริญญา และชื่อหลักสูตร...")
    courses = db.query(CourseDB).options(defer(CourseDB.embedding)).all()
    courses_to_reembed = []
    
    for c in courses:
        modified = False
        
        # 1.1 Fix University TH
        if c.university in UNIVERSITY_MAP:
            expected_th = UNIVERSITY_MAP[c.university]
            if c.university_th != expected_th:
                c.university_th = expected_th
                modified = True
                
        # 1.2 Apply Specific Fixes Map
        if c.id in SPECIFIC_COURSE_FIXES:
            fixes = SPECIFIC_COURSE_FIXES[c.id]
            for key, val in fixes.items():
                if getattr(c, key) != val:
                    setattr(c, key, val)
                    modified = True
            
        # 1.3 Fix Degree Levels systemically
        t_all = f"{c.title_th or ''} {c.title_en or ''} {c.degree_name or ''}"
        is_med_bachelor = any(med in t_all for med in ['แพทยศาสตรบัณฑิต', 'ทันตแพทยศาสตรบัณฑิต', 'สัตวแพทยศาสตรบัณฑิต', 'เภสัชศาสตรบัณฑิต', 'DDS', 'MD', 'Pharm.D.', 'DVM', 'พ.บ.', 'ท.บ.'])
        
        if not is_med_bachelor:
            if any(k in t_all for k in ['ดุษฎีบัณฑิต', 'Ph.D.', 'Doctor of Philosophy', 'D.Eng', 'ปร.ด.', 'วศ.ด.', 'วท.ด.']):
                if c.degree_level != 'ปริญญาเอก':
                    c.degree_level = 'ปริญญาเอก'
                    modified = True
            elif any(k in t_all for k in ['มหาบัณฑิต', 'Master of', 'M.Sc', 'M.Eng', 'MBA', 'วท.ม.', 'วศ.ม.', 'บธ.ม.', 'ศศ.ม.']):
                if c.degree_level not in ['ปริญญาโท', 'ปริญญาเอก', 'ประกาศนียบัตรบัณฑิต', 'ประกาศนียบัตรบัณฑิต (ชั้นสูง)']:
                    c.degree_level = 'ปริญญาโท'
                    modified = True
        else:
            if c.degree_level != 'ปริญญาตรี':
                c.degree_level = 'ปริญญาตรี'
                modified = True

        # 1.4 Fix missing or 'ไม่ระบุ' descriptions
        if not c.description or c.description.strip() in ['ไม่ระบุ', 'None', ''] or len(c.description.strip()) < 15:
            c.description = generate_smart_description(c.title_th, c.title_en, c.faculty_th, c.university_th, c.degree_level)
            modified = True

        # 1.5 Fix missing career_paths
        if not c.career_paths or len(c.career_paths) == 0:
            c.career_paths = generate_default_career_paths(c.title_th, c.title_en, c.faculty_th)
            modified = True

        # 1.6 Fix missing curriculum_highlights
        if not c.curriculum_highlights or len(c.curriculum_highlights) == 0:
            c.curriculum_highlights = generate_default_highlights(c.title_th, c.title_en, c.faculty_th)
            modified = True

        # 1.7 Clean remaining English prefixes in title_th if applicable
        if c.title_th and c.title_th.startswith("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาMaster of"):
            clean_part = c.title_th.replace("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาMaster of Science in ", "").replace("หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาMaster of ", "")
            c.title_th = f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{clean_part} (หลักสูตรนานาชาติ)"
            modified = True

        if modified:
            new_txt = build_course_embedding_text(c)
            c.embedding_text = new_txt
            courses_to_reembed.append(c.id)

    db.commit()
    print(f"  -> บันทึกการแก้ไขหลักสูตรเสร็จสิ้น: {len(courses_to_reembed)} หลักสูตรที่ต้องอัปเดตเวกเตอร์")

    # ---------------------------------------------------------
    # STEP 2: FIX FACULTIES ISSUES
    # ---------------------------------------------------------
    print("\n[2/5] ดำเนินการตรวจสอบและแก้ไขข้อมูลอาจารย์ (Faculties)...")
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
    faculties_to_reembed = []
    
    for f in faculties:
        fac_modified = False
        
        # 2.1 University TH mapping
        if f.university in UNIVERSITY_MAP:
            expected_th = UNIVERSITY_MAP[f.university]
            if f.university_th != expected_th:
                f.university_th = expected_th
                fac_modified = True
                
        # 2.2 Clean research interests
        if f.research_interests:
            clean_res = [str(r).strip() for r in f.research_interests if len(str(r).strip()) >= 2 and '404' not in str(r) and 'error' not in str(r).lower()]
            if clean_res != f.research_interests:
                f.research_interests = clean_res
                fac_modified = True

        if fac_modified:
            interests = ", ".join(f.research_interests) if f.research_interests else ""
            courses_str = ", ".join(f.taught_courses) if f.taught_courses else ""
            pubs_str = " | ".join(f.featured_publications) if f.featured_publications else ""
            txt = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
            txt += f"University: {f.university_th or ''} {f.university or ''}. "
            txt += f"Department: {f.department or ''} {f.department_th or ''}. "
            txt += f"Research Interests: {interests}. "
            txt += f"Taught Courses: {courses_str}. "
            txt += f"Publications: {pubs_str}."
            f.embedding_text = txt[:6000]
            faculties_to_reembed.append(f.id)
            
    db.commit()
    print(f"  -> ปรับปรุงข้อมูลอาจารย์เสร็จสิ้น: {len(faculties_to_reembed)} ท่านที่ต้องอัปเดตเวกเตอร์")

    # ---------------------------------------------------------
    # STEP 3: SAFELY RECOMPUTE EMBEDDINGS IN CHUNKS
    # ---------------------------------------------------------
    print(f"\n[3/5] คำนวณและอัปเดต AI Vector Embeddings อย่างปลอดภัย...")
    
    # 3.1 Course Embeddings in small batches
    if courses_to_reembed:
        print(f"  -> กำลังประมวลผล Vector สำหรับ {len(courses_to_reembed)} หลักสูตร...")
        
        def fetch_course_vec(cid):
            with SessionLocal() as s:
                item = s.query(CourseDB).filter(CourseDB.id == cid).first()
                if item and item.embedding_text:
                    vec = embedding_service.get_embedding(item.embedding_text)
                    return cid, vec
            return cid, None

        CHUNK_SIZE = 25
        for i in range(0, len(courses_to_reembed), CHUNK_SIZE):
            chunk = courses_to_reembed[i:i+CHUNK_SIZE]
            vec_map = {}
            with ThreadPoolExecutor(max_workers=min(8, len(chunk))) as executor:
                futures = {executor.submit(fetch_course_vec, cid): cid for cid in chunk}
                for fut in as_completed(futures):
                    cid, vec = fut.result()
                    if vec:
                        vec_map[cid] = vec
            
            # Save chunk to DB
            if vec_map:
                with SessionLocal() as s:
                    for cid, vec in vec_map.items():
                        c_obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
                        if c_obj:
                            c_obj.embedding = vec
                    s.commit()
            print(f"     หลักสูตรสำเร็จ: {min(i+CHUNK_SIZE, len(courses_to_reembed))}/{len(courses_to_reembed)}")

    # 3.2 Faculty Embeddings in small batches
    if faculties_to_reembed:
        print(f"  -> กำลังประมวลผล Vector สำหรับ {len(faculties_to_reembed)} อาจารย์...")
        
        def fetch_fac_vec(fid):
            with SessionLocal() as s:
                item = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if item and item.embedding_text:
                    vec = embedding_service.get_embedding(item.embedding_text)
                    return fid, vec
            return fid, None

        CHUNK_SIZE = 25
        for i in range(0, len(faculties_to_reembed), CHUNK_SIZE):
            chunk = faculties_to_reembed[i:i+CHUNK_SIZE]
            vec_map = {}
            with ThreadPoolExecutor(max_workers=min(8, len(chunk))) as executor:
                futures = {executor.submit(fetch_fac_vec, fid): fid for fid in chunk}
                for fut in as_completed(futures):
                    fid, vec = fut.result()
                    if vec:
                        vec_map[fid] = vec
            
            if vec_map:
                with SessionLocal() as s:
                    for fid, vec in vec_map.items():
                        f_obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                        if f_obj:
                            f_obj.embedding = vec
                    s.commit()
            print(f"     อาจารย์สำเร็จ: {min(i+CHUNK_SIZE, len(faculties_to_reembed))}/{len(faculties_to_reembed)}")

    db.close()
    print("\n=========================================================")
    print("✅ การคลีนและแก้ไขข้อมูลทั้งหมดเสร็จสมบูรณ์เรียบร้อย 100%!")
    print("=========================================================")

if __name__ == "__main__":
    clean_and_repair_all_data()
