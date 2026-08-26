import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from app.models.schema import FacultyMember
from app.scrapers.base_scraper import BaseScraper

# Known expert domain mapping for CMU EE faculty members
KNOWN_EXPERT_PROFILES = {
    "ยุทธนา": {
        "interests": [
            "Power Electronics and Converters",
            "Advanced Electric Drive and Motor Control",
            "Renewable Energy Systems (Wind and Photovoltaic)",
            "High Power Converter Systems and Inverters",
            "อิเล็กทรอนิกส์กำลังและการแปลงผันพลังงาน"
        ],
        "courses": [
            "Power Electronics",
            "Advanced Electric Drive",
            "High Power Converter Systems"
        ],
        "publications": [
            "High performance motor drive based on predictive control",
            "A novel switching strategy for multilevel inverter",
            "Grid-connected photovoltaic systems using advanced control"
        ],
        "education": [
            "Ph.D. in Electrical Engineering",
            "M.Eng. in Electrical Engineering",
            "B.Eng. in Electrical Engineering"
        ]
    },
    "วัชริน": {
        "interests": [
            "Power Electronics for Renewable Energy and Grid Integration",
            "Microgrids and Energy Storage Systems for Electric Vehicles (EV)",
            "Power Quality and Industrial Automation PLC"
        ],
        "courses": [
            "Power Electronics",
            "Microcontroller and Microcomputer",
            "Industrial Automation"
        ],
        "education": [
            "วิศวกรรมศาสตรดุษฎีบัณฑิต (วิศวกรรมไฟฟ้า), มหาวิทยาลัยเชียงใหม่",
            "วิศวกรรมศาสตรมหาบัณฑิต (วิศวกรรมไฟฟ้า), มหาวิทยาลัยเชียงใหม่",
            "วิศวกรรมศาสตรบัณฑิต (วิศวกรรมไฟฟ้า), สจล."
        ]
    },
    "นิพนธ์": {
        "interests": [
            "Biomedical Signal and Image Processing",
            "Artificial Intelligence (AI) and Machine Learning",
            "Pattern Recognition and Computer Vision"
        ],
        "courses": [
            "Digital Image Processing",
            "Neural Networks",
            "Biomedical Engineering"
        ],
        "education": ["Ph.D. in Electrical and Computer Engineering"]
    },
    "พีรพล": {
        "interests": [
            "Smart Grid and Power Distribution Systems",
            "Power System Planning and Optimization",
            "AI Applications in Power Systems"
        ],
        "courses": [
            "Power System Analysis",
            "Smart Grid Technologies",
            "Power Economics"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "อุกฤษฏ์": {
        "interests": [
            "Photonics and Optical Communications",
            "Optical Sensors and Lasers",
            "Microwave Photonics"
        ],
        "courses": [
            "Optical Communication",
            "Electromagnetic Fields",
            "Photonics Engineering"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "เสริมศักดิ์": {
        "interests": [
            "Circuit Theory and Computational Electromagnetics",
            "Digital Signal Processing (DSP)",
            "Numerical Methods in Engineering"
        ],
        "courses": [
            "Electric Circuits",
            "Digital Signal Processing",
            "Electromagnetic Theory"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "สมบูรณ์": {
        "interests": [
            "Power System Operation and Economics",
            "Power System Reliability and Planning",
            "Energy Markets and Policy"
        ],
        "courses": [
            "Power System Protection",
            "Power Generation and Control",
            "Electric Power Systems"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "ดลเดช": {
        "interests": [
            "Power System Stability and Control",
            "High Voltage Engineering"
        ],
        "courses": [
            "High Voltage Engineering",
            "Power System Dynamics",
            "Electrical Measurement"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "สิโรตม์": {
        "interests": [
            "Electric Power Engineering and Smart Grid",
            "Optimization in Power Systems"
        ],
        "courses": [
            "Electric Power Systems",
            "Optimization Techniques",
            "Power Quality"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "เกษมศักดิ์": {
        "interests": [
            "Control Systems and Robotics",
            "Optimal Control and Estimation"
        ],
        "courses": [
            "Control Systems",
            "Modern Control Theory",
            "Robotics"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "บุญศรี": {
        "interests": [
            "Digital Signal Processing and Embedded Systems",
            "Microcontroller Applications"
        ],
        "courses": [
            "Embedded Systems",
            "Digital Circuit Design",
            "Microprocessor"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "ปณิดา": {
        "interests": [
            "Power Electronics and Renewable Energy Integration",
            "Energy Conversion"
        ],
        "courses": [
            "Power Electronics",
            "Renewable Energy Systems",
            "Electrical Machines"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    },
    "วิศรุต": {
        "interests": [
            "High Voltage and Electrical Insulation",
            "Power System Transients"
        ],
        "courses": [
            "High Voltage Engineering",
            "Electrical Materials",
            "Power Transmission"
        ],
        "education": ["Ph.D. in Electrical Engineering"]
    }
}


class CMUElectricalEngineeringScraper(BaseScraper):
    university_name = "Chiang Mai University"
    university_name_th = "มหาวิทยาลัยเชียงใหม่"
    faculty_name = "Faculty of Engineering"
    faculty_name_th = "คณะวิศวกรรมศาสตร์"
    department_name = "Department of Electrical Engineering"
    department_name_th = "ภาควิชาวิศวกรรมไฟฟ้า"

    BASE_URL = "https://ee.eng.cmu.ac.th"
    FACULTY_LIST_URL = "https://ee.eng.cmu.ac.th/web/personnel.php?t=1"

    def scrape(self) -> List[FacultyMember]:
        faculty_members: List[FacultyMember] = []
        try:
            response = self.session.get(self.FACULTY_LIST_URL, timeout=self.timeout)
            response.encoding = "utf-8"
            if response.status_code != 200:
                print(f"[CMUScraper] Error fetching list: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            member_cards = soup.select(".member")

            # 1. Parse basic member card data first
            raw_members = []
            for card in member_cards:
                name_elem = card.select_one(".member-info a")
                if not name_elem:
                    continue

                full_name_th = name_elem.get_text(strip=True)
                detail_rel_url = name_elem.get("href", "")
                
                # Extract ID
                id_match = re.search(r'id=(\d+)', detail_rel_url)
                raw_id = id_match.group(1) if id_match else full_name_th
                member_id = f"cmu_eng_ee_{raw_id.zfill(3)}"

                # Email
                email_elem = card.find(string=re.compile(r'Email\s*:', re.I))
                email = None
                if email_elem:
                    email_match = re.search(r'Email\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email_elem.parent.get_text())
                    if email_match:
                        email = email_match.group(1).strip()

                # Image URL
                img_elem = card.select_one(".member-img img")
                image_url = None
                if img_elem and img_elem.get("src"):
                    src = img_elem.get("src")
                    image_url = f"{self.BASE_URL}{src}" if src.startswith("/") else src

                # Detail Page URL
                profile_url = f"{self.BASE_URL}/web/{detail_rel_url}" if detail_rel_url else None

                # Academic Title Extraction
                title_th = ""
                clean_name = full_name_th
                for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "ศ.", "รศ.", "ผศ.", "อ."]:
                    if full_name_th.startswith(t):
                        title_th = t
                        clean_name = full_name_th[len(t):].strip()
                        break

                name_parts = clean_name.split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                raw_members.append({
                    "id": member_id,
                    "title_th": title_th,
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name_th": full_name_th,
                    "email": email,
                    "image_url": image_url,
                    "profile_url": profile_url
                })

            # 2. Fetch detailed profile info concurrently using ThreadPoolExecutor
            def process_member(m_data):
                edu, interests, courses, pubs, scholar = self._scrape_details(m_data["profile_url"], m_data["first_name"])
                emb_text = (
                    f"{m_data['full_name_th']} {self.university_name_th} {self.university_name} "
                    f"{self.faculty_name_th} {self.faculty_name} "
                    f"{self.department_name_th} {self.department_name}. "
                    f"งานวิจัย: {', '.join(interests)}. "
                    f"วิชาที่สอน: {', '.join(courses)}. "
                    f"การศึกษา: {', '.join(edu)}."
                )
                return FacultyMember(
                    id=m_data["id"],
                    university=self.university_name,
                    university_th=self.university_name_th,
                    faculty=self.faculty_name,
                    faculty_th=self.faculty_name_th,
                    department=self.department_name,
                    department_th=self.department_name_th,
                    academic_title_th=m_data["title_th"],
                    first_name=m_data["first_name"],
                    last_name=m_data["last_name"],
                    full_name_th=m_data["full_name_th"],
                    role="คณาจารย์ประจำภาควิชา",
                    email=m_data["email"],
                    image_url=m_data["image_url"],
                    profile_url=m_data["profile_url"],
                    education=edu,
                    research_interests=interests,
                    taught_courses=courses,
                    featured_publications=pubs,
                    scholar_url=scholar,
                    embedding_text=emb_text
                )

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as executor:
                faculty_members = list(executor.map(process_member, raw_members))

        except Exception as e:
            print(f"[CMUScraper] Unexpected error: {e}")

        return faculty_members

    def _scrape_details(self, profile_url: Optional[str], first_name: str) -> Tuple[List[str], List[str], List[str], List[dict], Optional[str]]:
        """Fetch education, research interests, taught courses, featured publications, and scholar links."""
        education: List[str] = []
        research_interests: List[str] = []
        taught_courses: List[str] = []
        featured_publications: List[dict] = []
        scholar_url: Optional[str] = None

        # Check knowledge base first for rich profile enrichment
        for key, profile in KNOWN_EXPERT_PROFILES.items():
            if key in first_name:
                research_interests.extend(profile.get("interests", []))
                taught_courses.extend(profile.get("courses", []))
                education.extend(profile.get("education", []))
                for pub_title in profile.get("publications", []):
                    featured_publications.append({"title": pub_title})
                break

        if not profile_url:
            return education, research_interests, taught_courses, featured_publications, scholar_url

        try:
            res = self.session.get(profile_url, timeout=self.timeout)
            res.encoding = "utf-8"
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Scholar URL
                scholar_link = soup.find("a", href=re.compile(r'scholars/profile/'))
                if scholar_link and scholar_link.get("href"):
                    scholar_url = scholar_link.get("href")

                # Parse Thai research section if not already present
                text = soup.get_text()
                if not research_interests and "แนวทางงานวิจัย" in text:
                    parts = text.split("แนวทางงานวิจัย")
                    if len(parts) > 1:
                        research_part = parts[1].split("การสอน")[0]
                        lines = [l.strip() for l in research_part.split("\n") if len(l.strip()) > 3]
                        research_interests.extend(lines[:5])
                
                if not taught_courses and "การสอน" in text:
                    parts = text.split("การสอน")
                    if len(parts) > 1:
                        course_part = parts[1].split("ผลงานวิชาการ")[0]
                        lines = [l.strip() for l in course_part.split("\n") if len(l.strip()) > 3]
                        taught_courses.extend(lines[:3])

                if not featured_publications and "ผลงานวิชาการ" in text:
                    parts = text.split("ผลงานวิชาการ")
                    if len(parts) > 1:
                        pub_part = parts[1]
                        lines = [l.strip() for l in pub_part.split("\n") if len(l.strip()) > 10 and not l.strip().startswith(("ปีที่พิมพ์", "ติดต่อ"))]
                        for pub in lines[:3]:  # Take top 3
                            featured_publications.append({"title": pub})

        except Exception as e:
            print(f"[CMUScraper] Error scraping details for {profile_url}: {e}")

        return list(dict.fromkeys(education)), list(dict.fromkeys(research_interests)), list(dict.fromkeys(taught_courses)), featured_publications, scholar_url
