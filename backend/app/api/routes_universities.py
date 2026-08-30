# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer
from sqlalchemy import or_, func
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.models.db_models import CourseDB, FacultyDB
from app.models.schema import CourseSchema, FacultyMember
from app.api.routes_courses import db_course_to_pydantic
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db

router = APIRouter(prefix="/universities", tags=["University Highlights & Signature Programs"])

class UniversitySignatureMetadata(BaseModel):
    slug: str
    name_th: str
    name_en: str
    short_name: str
    logo_color: str
    motto: str
    academic_strengths: List[str]
    region: str
    established_year: Optional[int] = None
    featured_keywords: List[str]

class UniversityHighlightResponse(BaseModel):
    metadata: UniversitySignatureMetadata
    total_courses: int
    total_advisors: int
    signature_programs: List[CourseSchema]
    distinguished_advisors: List[FacultyMember] = []

# Comprehensive Registry of Signature University Profiles & Flagship Academic Strengths
UNIVERSITIES_REGISTRY: List[UniversitySignatureMetadata] = [
    UniversitySignatureMetadata(
        slug="chula",
        name_th="จุฬาลงกรณ์มหาวิทยาลัย",
        name_en="Chulalongkorn University",
        short_name="CU / จุฬาฯ",
        logo_color="#E05A88",
        motto="เสาหลักของแผ่นดิน อันดับ 1 ของไทย ผู้นำด้าน AI วิศวกรรมศาสตร์ แพทยศาสตร์ และบริหารธุรกิจระดับโลก",
        academic_strengths=[
            "พาณิชยศาสตร์และการบัญชี (CBS / BBA Chula)",
            "วิศวกรรมคอมพิวเตอร์, AI & หุ่นยนต์ (CEDT & ISE)",
            "แพทยศาสตร์ & วิทยาศาสตร์สุขภาพคลินิก",
            "นิติศาสตร์ (กฎหมายการเงินและภาษีอากร)",
            "อักษรศาสตร์ & ภาษาศาสตร์สากล"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1917,
        featured_keywords=[
            "พาณิชยศาสตร์และการบัญชี", "บัญชี", "การเงิน",
            "วิศวกรรมคอมพิวเตอร์", "ปัญญาประดิษฐ์", "cedt",
            "แพทยศาสตร์", "นิติศาสตร์", "อักษรศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="mahidol",
        name_th="มหาวิทยาลัยมหิดล",
        name_en="Mahidol University",
        short_name="MU / มหิดล",
        logo_color="#003566",
        motto="ปัญญาของแผ่นดิน ผู้นำอันดับ 1 ด้านวิทยาศาสตร์สุขภาพ การแพทย์ ศิริราช-รามาธิบดี และชีววิทยาศาสตร์",
        academic_strengths=[
            "แพทยศาสตร์ (ศิริราชพยาบาล & รามาธิบดี)",
            "เวชศาสตร์เขตร้อน (TropMed อันดับ 1 ของเอเชีย)",
            "เภสัชศาสตร์ & การประเมินเทคโนโลยีสุขภาพ",
            "วิศวกรรมชีวการแพทย์ (Biomedical Engineering)",
            "วิทยาลัยดุริยางคศิลป์ (College of Music)"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1888,
        featured_keywords=[
            "ศิริราช", "รามาธิบดี", "เวชศาสตร์เขตร้อน", "เภสัชศาสตร์", "วิศวกรรมชีวการแพทย์", "ดุริยางคศิลป์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="tu",
        name_th="มหาวิทยาลัยธรรมศาสตร์",
        name_en="Thammasat University",
        short_name="TU / มธ.",
        logo_color="#C8102E",
        motto="มหาวิทยาลัยเพื่อประชาชน ต้นกำเนิดนิติศาสตร์ รัฐศาสตร์สิงห์แดง ธุรกิจสากล และวิศวะนานาชาติ SIIT",
        academic_strengths=[
            "นิติศาสตร์ (กฎหมายธุรกิจ & ทรัพย์สินทางปัญญา LL.M.)",
            "รัฐศาสตร์ (สิงห์แดง) & บริหารรัฐกิจ",
            "พาณิชยศาสตร์และการบัญชี (BBA Thammasat Triple Crown)",
            "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT AI & CS)",
            "วารสารศาสตร์และสื่อสารมวลชน (JC การสื่อสารองค์กร)"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1934,
        featured_keywords=[
            "นิติศาสตร์", "รัฐศาสตร์", "พาณิชยศาสตร์และการบัญชี", "SIIT", "วารสารศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="ku",
        name_th="มหาวิทยาลัยเกษตรศาสตร์",
        name_en="Kasetsart University",
        short_name="KU / มก.",
        logo_color="#006D44",
        motto="ศาสตร์แห่งแผ่นดิน ต้นตำรับเกษตรอัจฉริยะ อุตสาหกรรมอาหาร สัตวแพทย์ และวิศวกรรมการบิน-ซอฟต์แวร์",
        academic_strengths=[
            "อุตสาหกรรมเกษตร & วิทยาศาสตร์การอาหาร (Food Science)",
            "สัตวแพทยศาสตร์ & วนศาสตร์-สิ่งแวดล้อม",
            "เกษตรศาสตร์ & เทคโนโลยีการเกษตรอัจฉริยะ",
            "วิศวกรรมการบินและอวกาศ (IDDP & Aerospace)",
            "เศรษฐศาสตร์ธุรกิจและธุรกิจการเกษตร"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1943,
        featured_keywords=[
            "วิทยาศาสตร์และเทคโนโลยีการอาหาร", "สัตวแพทยศาสตร์", "เกษตรศาสตร์", "วิศวกรรมการบินและอวกาศ", "เศรษฐศาสตร์ธุรกิจ"
        ]
    ),
    UniversitySignatureMetadata(
        slug="cmu",
        name_th="มหาวิทยาลัยเชียงใหม่",
        name_en="Chiang Mai University",
        short_name="CMU / มช.",
        logo_color="#8957E5",
        motto="ขุมปัญญาแห่งล้านนา ศูนย์กลางวิทยาการข้อมูล Data Science การแพทย์สวนดอก และพลังงานสะอาด",
        academic_strengths=[
            "วิทยาการข้อมูล & นวัตกรรมดิจิทัล (Data Science CMU)",
            "แพทยศาสตร์สวนดอก & วิทยาศาสตร์สุขภาพ",
            "วิศวกรรมคอมพิวเตอร์ & พลังงานสะอาด",
            "คณะการสื่อสารมวลชน (Mass Comm มช.)",
            "สถาปัตยกรรมศาสตร์ & การออกแบบสิ่งแวดล้อม"
        ],
        region="ภาคเหนือ",
        established_year=1964,
        featured_keywords=[
            "วิทยาการข้อมูล", "แพทยศาสตร์", "วิศวกรรมคอมพิวเตอร์", "การสื่อสารมวลชน", "สถาปัตยกรรมศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="kmitl",
        name_th="สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        name_en="King Mongkut's Institute of Technology Ladkrabang",
        short_name="KMITL / ลาดกระบัง",
        logo_color="#E85D04",
        motto="ผู้นำวิศวกรรมศาสตร์ เทคโนโลยีอัจฉริยะ หุ่นยนต์-AI โทรคมนาคม วิศวะการบิน และสถาปัตย์",
        academic_strengths=[
            "วิศวกรรมคอมพิวเตอร์, AI & หุ่นยนต์อัจฉริยะ",
            "วิศวกรรมไฟฟ้า & โทรคมนาคมสื่อสาร",
            "คณะเทคโนโลยีสารสนเทศ (School of IT AIBA)",
            "สถาปัตยกรรม ศิลปะและการออกแบบ (AAD)",
            "อุตสาหกรรมอาหาร & นวัตกรรมการประกอบอาหาร"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1960,
        featured_keywords=[
            "วิศวกรรมคอมพิวเตอร์", "วิศวกรรมไฟฟ้าสื่อสาร", "เทคโนโลยีสารสนเทศ", "สถาปัตยกรรม", "อุตสาหกรรมอาหาร"
        ]
    ),
    UniversitySignatureMetadata(
        slug="kmutt",
        name_th="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        name_en="King Mongkut's University of Technology Thonburi",
        short_name="KMUTT / บางมด",
        logo_color="#DC2626",
        motto="มหาวิทยาลัยวิจัยแห่งชาติด้านวิศวกรรมขั้นสูง เทคโนโลยีสารสนเทศ SIT หุ่นยนต์ FIBO และพลังงานสะอาด",
        academic_strengths=[
            "คณะเทคโนโลยีสารสนเทศ (SIT - Software & CS)",
            "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)",
            "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม (JGSEE)",
            "วิศวกรรมโยธา, เครื่องกล และยานยนต์",
            "วิทยาศาสตร์นาโนและวิทยาการคอมพิวเตอร์ประยุกต์"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1960,
        featured_keywords=[
            "เทคโนโลยีสารสนเทศ", "วิทยาการหุ่นยนต์", "พลังงาน", "วิศวกรรมโยธา", "วิทยาการคอมพิวเตอร์ประยุกต์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="su",
        name_th="มหาวิทยาลัยศิลปากร",
        name_en="Silpakorn University",
        short_name="SU / ม.ศิลปากร",
        logo_color="#0D9488",
        motto="สถาบันอันดับ 1 ด้านความคิดสร้างสรรค์ มัณฑนศิลป์ จิตรกรรม สถาปัตยกรรมศาสตร์ และโบราณคดี",
        academic_strengths=[
            "คณะมัณฑนศิลป์ (Interior, Graphic & Fashion Design)",
            "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์",
            "คณะสถาปัตยกรรมศาสตร์ (สถาปัตย์ไทยและสากล)",
            "คณะโบราณคดี (แห่งเดียวในประเทศไทย)",
            "ICT ศิลปากร (การออกแบบเกม แอนิเมชัน และดิจิทัลมีเดีย)"
        ],
        region="ภาคกลางและปริมณฑล",
        established_year=1943,
        featured_keywords=[
            "มัณฑนศิลป์", "จิตรกรรม", "สถาปัตยกรรม", "โบราณคดี", "เกมและแอนิเมชัน"
        ]
    ),
    UniversitySignatureMetadata(
        slug="swu",
        name_th="มหาวิทยาลัยศรีนครินทรวิโรฒ",
        name_en="Srinakharinwirot University",
        short_name="SWU / มศว",
        logo_color="#BE185D",
        motto="ผู้นำด้านนวัตกรรมสื่อสารสังคม COSCI วงการบันเทิงและมีเดีย ศึกษาศาสตร์-ครุศาสตร์ และการแพทย์",
        academic_strengths=[
            "วิทยาลัยนวัตกรรมสื่อสารสังคม (COSCI ภาพยนตร์และสื่อดิจิทัล)",
            "คณะศึกษาศาสตร์ (เทคโนโลยีการศึกษาและวิชาชีพครู)",
            "คณะแพทยศาสตร์ & วิทยาศาสตร์การแพทย์",
            "คณะศิลปกรรมศาสตร์ (การแสดง กำกับการแสดง และดนตรี)",
            "คณะเภสัชศาสตร์ (การบริบาลทางเภสัชกรรม)"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1949,
        featured_keywords=[
            "ภาพยนตร์และสื่อดิจิทัล", "เทคโนโลยีการศึกษา", "วิทยาศาสตร์การแพทย์", "การแสดงและกำกับการแสดง", "การบริบาลทางเภสัชกรรม"
        ]
    ),
    UniversitySignatureMetadata(
        slug="mfu",
        name_th="มหาวิทยาลัยแม่ฟ้าหลวง",
        name_en="Mae Fah Luang University",
        short_name="MFU / มฟล.",
        logo_color="#B91C1C",
        motto="มหาวิทยาลัยนานาชาติชั้นนำ อันดับ 1 วิทยาศาสตร์เครื่องสำอาง เวชศาสตร์ชะลอวัย Anti-Aging และแพทย์บูรณาการ",
        academic_strengths=[
            "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง (Cosmetic Science)",
            "สำนักวิชาการแพทย์บูรณาการ & แพทย์แผนจีน",
            "สำนักวิชาจีนวิทยา (School of Sinology ภาษาจีนธุรกิจ)",
            "สำนักวิชาแพทยศาสตร์ & พยาบาลศาสตร์",
            "สำนักวิชานิติศาสตร์ & นวัตกรรมสังคม"
        ],
        region="ภาคเหนือ",
        established_year=1998,
        featured_keywords=[
            "วิทยาศาสตร์เครื่องสำอาง", "การแพทย์แผนจีน", "ภาษาจีนธุรกิจ", "แพทยศาสตร์", "นิติศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="kku",
        name_th="มหาวิทยาลัยขอนแก่น",
        name_en="Khon Kaen University",
        short_name="KKU / มข.",
        logo_color="#8B4513",
        motto="ขุมปัญญาแห่งอีสาน ศูนย์การแพทย์ศรีนครินทร์ ทันตแพทย์ วิศวกรรมศาสตร์ และเกษตรดิจิทัล",
        academic_strengths=[
            "แพทยศาสตร์ (ศูนย์การแพทย์ศรีนครินทร์) & ทันตแพทย์",
            "คณะเภสัชศาสตร์ (หลักสูตรนานาชาติ Pharm.D.)",
            "คณะวิศวกรรมศาสตร์ (โลจิสติกส์ หุ่นยนต์ & AI)",
            "คณะเกษตรศาสตร์ & ทรัพยากรการเกษตรเขตร้อน",
            "คณะสหวิทยาการ & วิทยาการคอมพิวเตอร์"
        ],
        region="ภาคตะวันออกเฉียงเหนือ",
        established_year=1964,
        featured_keywords=[
            "ทันตแพทยศาสตร์", "เภสัชศาสตร์", "วิศวกรรมโลจิสติกส์", "พืชศาสตร์", "วิทยาการคอมพิวเตอร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="psu",
        name_th="มหาวิทยาลัยสงขลานครินทร์",
        name_en="Prince of Songkla University",
        short_name="PSU / ม.อ.",
        logo_color="#0284C7",
        motto="มหาวิทยาลัยเพื่อภาคใต้ ผู้นำด้านการแพทย์ วิทยาลัยการคอมพิวเตอร์ เทคโนโลยียาง-โพลิเมอร์ และทรัพยากรทางทะเล",
        academic_strengths=[
            "คณะแพทยศาสตร์ (ศูนย์การแพทย์ภาคใต้)",
            "วิทยาลัยการคอมพิวเตอร์ (AI & Digital Engineering)",
            "คณะวิศวกรรมศาสตร์ (AI, คอมพิวเตอร์ & เครื่องกล)",
            "คณะเภสัชศาสตร์ & วิทยาศาสตร์การแพทย์",
            "คณะทรัพยากรธรรมชาติ & นวัตกรรมการเกษตร"
        ],
        region="ภาคใต้",
        established_year=1967,
        featured_keywords=[
            "แพทยศาสตร์", "วิทยาลัยการคอมพิวเตอร์", "วิศวกรรมศาสตร์", "เภสัชศาสตร์", "ทรัพยากรธรรมชาติ"
        ]
    ),
    UniversitySignatureMetadata(
        slug="nida",
        name_th="สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
        name_en="National Institute of Development Administration",
        short_name="NIDA / นิด้า",
        logo_color="#1E3A8A",
        motto="สถาบันบัณฑิตศึกษาเฉพาะทาง ผลิตผู้นำนโยบายสาธารณะ รัฐประศาสนศาสตร์ MPA และบริหารธุรกิจ AACSB",
        academic_strengths=[
            "คณะรัฐประศาสนศาสตร์ (MPA / D.P.A. การบริหารภาครัฐ)",
            "คณะบริหารธุรกิจ (GSBA MBA มาตรฐาน AACSB)",
            "คณะสถิติประยุกต์ & วิทยาการข้อมูล (Data Science)",
            "คณะพัฒนาการเศรษฐกิจ (เศรษฐศาสตร์การเงินและการพัฒนา)",
            "คณะนิเทศศาสตร์และนวัตกรรมการจัดการดิจิทัล"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1966,
        featured_keywords=[
            "รัฐประศาสนศาสตร์", "บริหารธุรกิจ", "สถิติประยุกต์", "พัฒนาการเศรษฐกิจ", "นิเทศศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="stou",
        name_th="มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        name_en="Sukhothai Thammathirat Open University",
        short_name="STOU / มสธ.",
        logo_color="#047857",
        motto="มหาวิทยาลัยเปิดเพื่อการศึกษาตลอดชีวิต ชั้นนำด้านนิติศาสตร์ทางไกล วิทยาการจัดการ และรัฐศาสตร์",
        academic_strengths=[
            "สาขาวิชานิติศาสตร์ (กฎหมายการศึกษาทางไกล)",
            "สาขาวิชาวิทยาการจัดการ (การจัดการ การเงิน บัญชี)",
            "สาขาวิชารัฐศาสตร์ (การเมืองการปกครองและบริหารรัฐกิจ)",
            "สาขาวิชาวิทยาศาสตร์สุขภาพ & สาธารณสุข",
            "สาขาวิชานิเทศศาสตร์ & นวัตกรรมการสื่อสาร"
        ],
        region="การศึกษาทางไกลและตลอดชีวิต",
        established_year=1978,
        featured_keywords=[
            "นิติศาสตร์", "วิทยาการจัดการ", "รัฐศาสตร์", "วิทยาศาสตร์สุขภาพ", "นิเทศศาสตร์"
        ]
    ),
    UniversitySignatureMetadata(
        slug="au",
        name_th="มหาวิทยาลัยอัสสัมชัญ",
        name_en="Assumption University (ABAC)",
        short_name="AU / เอแบค",
        logo_color="#B91C1C",
        motto="มหาวิทยาลัยนานาชาติเอกชนแห่งแรก ผู้นำบริหารธุรกิจ MSME การตลาดสากล และนิเทศศาสตร์อินเตอร์",
        academic_strengths=[
            "Martin de Tours School of Management & Economics (MSME BBA)",
            "Graduate School of Business (MBA International)",
            "Albert Laurence School of Communication Arts (นิเทศอินเตอร์)",
            "Vincent Mary School of Science & Tech (CS & AI)",
            "คณะบริหารธุรกิจ สาขาวิชาการจัดการห่วงโซ่อุปทาน"
        ],
        region="กรุงเทพมหานครและปริมณฑล",
        established_year=1969,
        featured_keywords=[
            "MSME", "MBA", "Communication Arts", "Science & Tech", "ห่วงโซ่อุปทาน"
        ]
    ),
    UniversitySignatureMetadata(
        slug="sut",
        name_th="มหาวิทยาลัยเทคโนโลยีสุรนารี",
        name_en="Suranaree University of Technology",
        short_name="SUT / มทส.",
        logo_color="#F97316",
        motto="มหาวิทยาลัยเฉพาะทางวิทยาศาสตร์และเทคโนโลยี แหล่งเครื่องกำเนิดแสงซินโครตรอน ยานยนต์ และหุ่นยนต์",
        academic_strengths=[
            "สำนักวิชาวิศวกรรมศาสตร์ (โยธา ขนส่ง ยานยนต์ และเมคาทรอนิกส์)",
            "สำนักวิชาแพทยศาสตร์ (การแพทย์ปริวรรตและการวิจัยทางคลินิก)",
            "สำนักวิชาเทคโนโลยีการเกษตร (เทคโนโลยีการผลิตพืช)",
            "สำนักวิชาวิทยาศาสตร์ (คณิตศาสตร์ประยุกต์ & ฟิสิกส์ซินโครตรอน)",
            "สำนักวิชาศาสตร์และศิลป์ดิจิทัล (Computer Science & AI)"
        ],
        region="ภาคตะวันออกเฉียงเหนือ",
        established_year=1990,
        featured_keywords=[
            "วิศวกรรมศาสตร์", "แพทยศาสตร์", "เทคโนโลยีการเกษตร", "วิทยาศาสตร์", "ดิจิทัล"
        ]
    )
]

# High-Precision Explicit Mapping of Flagship Course IDs per University & Strength
FLAGSHIP_PROGRAM_IDS: Dict[str, List[List[str]]] = {
    "chula": [
        ["chula_cbs_bacc", "chula_cbs_bba_inter", "chula_cbs_mba"],
        ["chula-cedt-eng-bs", "chula_eng_ise_ai_beng", "chula_eng_cpe_beng"],
        ["cu-med-grad-dip-dermatology", "cu_ms_health_ai_sandbox", "cu_dent_dds"],
        ["cu_llm_financial_and_tax_law", "chula-law-cert-admin-law", "chula_law_llb"],
        ["chula_arts_ma_eil", "chula_arts_ba_thai", "chula_arts_ba_eng"],
    ],
    "mahidol": [
        ["si-ophthalmology-residency", "MEDICAL-DOCTOR-PROGRAM", "mu_ra_md_bme_hybrid"],
        ["MCTM", "mu_tropmed_phd_tropical_medicine"],
        ["mu_py_hta_msc_inter", "mu_dt_endo_msc", "mu_dt_dent_dds"],
        ["mu_ra_md_bme_hybrid", "mu_eg_beng_bme"],
        ["mu_music_bmus", "mu_music_mmus"],
    ],
    "tu": [
        ["tu_law_llm_business", "tu_law_llb"],
        ["066558a3c2da8db8dbb8bebff4ee86f6", "a1b9f7323b426136c5066bd6aaaceca4"],
        ["tu_tbs_bba_inter", "f5dfd5fa9113d33ee44c28dfe30eac11"],
        ["tu_siit_beng_ai_data", "tu_siit_beng_cpe"],
        ["198f2cb524f5e34bc77dad715e7b1a8d", "tu_jc_ba_mass_comm"],
    ],
    "ku": [
        ["ku_agro_foodsci_bsc", "ku_agro_biotech_bsc"],
        ["ku_vet_vcs_phd", "ku_forest_bsc_forestry"],
        ["6c99a1706a04409d82ac69b23f70a341", "ku_agri_agron_bsc"],
        ["ku_eng_beng_aerospace", "ku_eng_cpe_beng"],
        ["ku-econ-mbe-special", "ku_econ_becon"],
    ],
    "cmu": [
        ["cmu_sci_ds_bsc", "cmu_sci_compsci_bsc", "cmu_tqf_25610041100189"],
        ["cmu_med_md", "cmu_dent_dds", "cmu_vet_dvm", "cmu-master-medicine"],
        ["cmu_eng_cpe_beng2", "cmu_06_2_014", "cmu-master-engineering"],
        ["cmu_nurse_bns", "cmu_tqf_25410041100077", "cmu-master-mass-comm"],
        ["cmu_tqf_25380041100333", "cmu_law_llb", "cmu_econ_ba"],
    ],
    "kmitl": [
        ["kmitl_eng_ce_beng", "kmitl_eng_robotics_ai_beng", "kmitl_eng_aiot_meng"],
        ["kmitl_iet_telecom_med_86480_77", "kmitl_eng_ece_meng"],
        ["kmitl_it_aiba_msc", "kmitl_it_bsc"],
        ["kmitl_arch_digital_media_bfa", "kmitl_arch_barch"],
        ["kmitl_food_bsc_culinary_sci", "kmitl_food_bsc"],
    ],
    "kmutt": [
        ["kmutt_sit_cs_bsc", "kmutt_sit_it_msc"],
        ["kmutt_fibo_robotics_meng", "kmutt_fibo_robotics_beng"],
        ["kmutt_eng_phd_energy_tech", "kmutt_jgsee_energy"],
        ["kmutt_fiet_m_ce", "kmutt_fiet_m_me", "kmutt_ce_bsc"],
        ["kmutt_applied_cs_bsc", "kmutt_sci_nano"],
    ],
    "su": [
        ["su_dec_bfa_interior_design", "su_dec_bfa"],
        ["su_art_bfa_painting", "su_art_bfa"],
        ["su_arch_architecture_barch", "su_arch_barch"],
        ["su_archaeo_ba_archaeology", "su_archaeo_ba"],
        ["su_ict_bsc_game_interactive", "su_ict_bsc"],
    ],
    "swu": [
        ["swu_cosci_ba_cinema", "swu_cosci_ba"],
        ["swu_edu_bed_edtech", "swu_edu_bed"],
        ["swu_med_medical_sciences_bsc", "swu_med_md"],
        ["swu_fa_bfa_acting_directing", "swu_fa_bfa"],
        ["swu_pharm_bpharm_care", "swu_pharm_bpharm"],
    ],
    "mfu": [
        ["mfu_phd_creative_innovation_in_cosmetic_science", "mfu_bachelor_beauty_technology"],
        ["mfu_bachelor_traditional_chinese_medicine", "mfu_med_chinese"],
        ["mfu_bachelor_chinese_language_and_culture", "mfu_bachelor_business_chinese", "mfu_sinology_ba"],
        ["mfu_bachelor_medicine", "mfu_bachelor_nursing"],
        ["mfu_bachelor_laws", "mfu_laws_llb"],
    ],
    "kku": [
        ["kku_dent_dds", "kku_dent_oral_msc"],
        ["kku_pharm_inter_pharmd", "kku_pharm_pharmd"],
        ["kku-be-logistics-engineering", "kku_eng_ai_robotics_beng"],
        ["kku_agri_agron_bsc", "kku_agri_bsc"],
        ["kku_is_cs_it_bsc", "kku_is_ece_inter_meng"],
    ],
    "psu": [
        ["psu_med_md", "psu_med_mph_epidemiology"],
        ["psu_cpt_ai_intelligent_systems_beng", "psu_coc_bsc_digital_engineering"],
        ["psu_eng_beng_ai_computer", "psu_eng_beng_mechanical"],
        ["psu_pharm_bpharm_sci", "psu_pharm_bpharm_care"],
        ["psu_nr_plant_bsc_89722_108", "psu_agro_bsc_food_science"],
    ],
    "nida": [
        ["nida_gspa_phd_pa", "nida_gspa_mpa"],
        ["nida_gsba_mba_regular", "nida_gsba_mba_flexible", "nida_nbs_msc_fi_92214_112"],
        ["nida_gsas_msc_dads", "nida_as_msc_datascience", "nida_gsas_ds_msc_92880_113"],
        ["nida_econ_phd_economics", "nida_econ_fin_msc_94807_116"],
        ["nida_gscm_comm_msc_95290_117", "nida_lc_ma_intercultural"],
    ],
    "stou": [
        ["stou-law"],
        ["stou-management"],
        ["stou-polsci"],
        ["stou_health_pub"],
        ["stou-commarts"],
    ],
    "au": [
        ["abac_msme_finance_bba", "abac_msme_marketing_bba", "abac_msme_accounting_bacc"],
        ["abac_grad_mba"],
        ["abac_ca_comm_arts_bca", "abac_ca_comm_design_bfa"],
        ["abac_grad_cs_ms"],
        ["au_m_supply_chain_management"],
    ],
    "sut": [
        ["sut-ms-10"],
        ["sut-ms-23"],
        ["sut_bachelor_crop_production_technology"],
        ["sut-ms-02"],
        ["sut_das_msc_applied_cs_ai"],
    ]
}

def _fetch_diverse_signature_courses(uni: UniversitySignatureMetadata, db: Session) -> List[CourseDB]:
    """
    Retrieves flagship signature courses guaranteeing 1 distinct course per academic strength/faculty.
    Uses explicit ID mapping first, with keyword search and faculty de-duplication as dynamic fallback.
    """
    signature_courses: List[CourseDB] = []
    seen_course_ids = set()
    seen_faculties = set()

    # 1. Try explicit flagship mapping
    explicit_groups = FLAGSHIP_PROGRAM_IDS.get(uni.slug, [])
    for group_candidates in explicit_groups:
        matched = None
        for cid in group_candidates:
            c = db.query(CourseDB).options(
                defer(CourseDB.embedding),
                defer(CourseDB.embedding_text)
            ).filter(CourseDB.id == cid).first()
            if c and c.id not in seen_course_ids:
                matched = c
                break
        if matched:
            signature_courses.append(matched)
            seen_course_ids.add(matched.id)
            if matched.faculty_th:
                seen_faculties.add(matched.faculty_th.strip())

    # 2. Dynamic keyword fallback if any slots remain unfilled (< 5)
    if len(signature_courses) < len(uni.academic_strengths):
        for kw in uni.featured_keywords:
            if len(signature_courses) >= 5:
                break
            candidates = db.query(CourseDB).options(
                defer(CourseDB.embedding),
                defer(CourseDB.embedding_text)
            ).filter(
                or_(
                    CourseDB.university_th.ilike(f"%{uni.name_th}%"),
                    CourseDB.university.ilike(f"%{uni.name_en}%")
                ),
                or_(
                    CourseDB.title_th.ilike(f"%{kw}%"),
                    CourseDB.faculty_th.ilike(f"%{kw}%"),
                    CourseDB.title_en.ilike(f"%{kw}%")
                )
            ).all()

            for c in candidates:
                fac = (c.faculty_th or "").strip()
                if c.id not in seen_course_ids and (not fac or fac not in seen_faculties):
                    signature_courses.append(c)
                    seen_course_ids.add(c.id)
                    if fac:
                        seen_faculties.add(fac)
                    break

    # 3. Final backfill if still under 4 courses
    if len(signature_courses) < 4:
        backfills = db.query(CourseDB).options(
            defer(CourseDB.embedding),
            defer(CourseDB.embedding_text)
        ).filter(
            or_(
                CourseDB.university_th.ilike(f"%{uni.name_th}%"),
                CourseDB.university.ilike(f"%{uni.name_en}%")
            )
        ).limit(6).all()
        for c in backfills:
            if c.id not in seen_course_ids:
                signature_courses.append(c)
                seen_course_ids.add(c.id)
            if len(signature_courses) >= 5:
                break

    return signature_courses

def _fetch_distinguished_advisors(uni: UniversitySignatureMetadata, advisors_pool: List[FacultyDB]) -> List[FacultyDB]:
    """
    Selects up to 5 distinguished advisors per university with high academic diversity across faculties/departments.
    """
    seen_departments = set()
    distinguished: List[FacultyDB] = []

    for a in advisors_pool:
        dep = (a.department_th or a.faculty_th or "").strip()
        if dep not in seen_departments and (a.research_interests or a.featured_publications):
            seen_departments.add(dep)
            distinguished.append(a)
            if len(distinguished) >= 5:
                break

    if len(distinguished) < 5:
        for a in advisors_pool:
            if a not in distinguished:
                distinguished.append(a)
                if len(distinguished) >= 5:
                    break

    return distinguished

@router.get("/signature-programs", response_model=List[UniversityHighlightResponse])
def get_all_university_signature_programs(db: Session = Depends(get_db)):
    """
    Returns curated signature / flagship courses, distinguished advisors, and academic strengths for top universities in Thailand.
    Guarantees cross-faculty diversity matching each institutional strength.
    """
    # Bulk fetch all faculties once for high-performance memory grouping (O(1) lookups)
    all_faculties = db.query(FacultyDB).options(
        defer(FacultyDB.embedding),
        defer(FacultyDB.embedding_text)
    ).all()

    by_uni_faculties: Dict[str, List[FacultyDB]] = {}
    for a in all_faculties:
        u_th = (a.university_th or "").strip()
        u_en = (a.university or "").strip()
        for u in UNIVERSITIES_REGISTRY:
            if u.name_th in u_th or u.name_en in u_en:
                if u.slug not in by_uni_faculties:
                    by_uni_faculties[u.slug] = []
                by_uni_faculties[u.slug].append(a)

    results: List[UniversityHighlightResponse] = []

    for uni in UNIVERSITIES_REGISTRY:
        total_courses = db.query(CourseDB).filter(
            or_(
                CourseDB.university_th.ilike(f"%{uni.name_th}%"),
                CourseDB.university.ilike(f"%{uni.name_en}%")
            )
        ).count()

        uni_faculties = by_uni_faculties.get(uni.slug, [])
        total_advisors = len(uni_faculties)

        signature_courses = _fetch_diverse_signature_courses(uni, db)
        distinguished_advs = _fetch_distinguished_advisors(uni, uni_faculties)

        results.append(
            UniversityHighlightResponse(
                metadata=uni,
                total_courses=total_courses,
                total_advisors=total_advisors,
                signature_programs=[db_course_to_pydantic(c) for c in signature_courses],
                distinguished_advisors=[db_to_pydantic(a) for a in distinguished_advs]
            )
        )

    return results

@router.get("/signature-programs/{slug}", response_model=UniversityHighlightResponse)
def get_university_signature_programs_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    Returns signature programs, distinguished advisors, and metadata for a single specific university.
    """
    uni = next((u for u in UNIVERSITIES_REGISTRY if u.slug.lower() == slug.lower()), None)
    if not uni:
        raise HTTPException(status_code=404, detail="University metadata not found")

    total_courses = db.query(CourseDB).filter(
        or_(
            CourseDB.university_th.ilike(f"%{uni.name_th}%"),
            CourseDB.university.ilike(f"%{uni.name_en}%")
        )
    ).count()

    uni_faculties = db.query(FacultyDB).options(
        defer(FacultyDB.embedding),
        defer(FacultyDB.embedding_text)
    ).filter(
        or_(
            FacultyDB.university_th.ilike(f"%{uni.name_th}%"),
            FacultyDB.university.ilike(f"%{uni.name_en}%")
        )
    ).all()

    total_advisors = len(uni_faculties)

    signature_courses = _fetch_diverse_signature_courses(uni, db)
    distinguished_advs = _fetch_distinguished_advisors(uni, uni_faculties)

    return UniversityHighlightResponse(
        metadata=uni,
        total_courses=total_courses,
        total_advisors=total_advisors,
        signature_programs=[db_course_to_pydantic(c) for c in signature_courses],
        distinguished_advisors=[db_to_pydantic(a) for a in distinguished_advs]
    )
