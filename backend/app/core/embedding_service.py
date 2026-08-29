import os
import time
import json
import threading
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings
from app.models.schema import FacultyMember
from google import genai
from google.genai import types

# Comprehensive Academic Taxonomy and Thai-English Cross-Disciplinary Ontology
THAI_EN_SYNONYMS = {
    # AI, Data Science & Computer Science
    "เอไอ": "AI Artificial Intelligence",
    "ปัญญาประดิษฐ์": "AI Artificial Intelligence Deep Learning Machine Learning",
    "แมชชีนเลิร์นนิง": "Machine Learning Supervised Learning Deep Learning",
    "แมชชีนเลินนิ่ง": "Machine Learning Supervised Learning Deep Learning",
    "ดีปเลิร์นนิง": "Deep Learning Neural Networks LLM",
    "ดาต้า": "Data Science Data Mining Big Data Analytics",
    "วิทยาการข้อมูล": "Data Science Big Data Machine Learning Analytics",
    "ข้อมูลขนาดใหญ่": "Big Data Hadoop Spark Data Pipeline",
    "ภาษาธรรมชาติ": "Natural Language Processing NLP LLM Large Language Models",
    "ประมวลผลภาษา": "Natural Language Processing NLP Text Mining",
    "คอมพิวเตอร์วิทัศน์": "Computer Vision Image Processing Object Detection",
    "วิทัศน์คอมพิวเตอร์": "Computer Vision Image Processing CNN",
    "การประมวลผลภาพ": "Image Processing Computer Vision Pattern Recognition",
    "หุ่นยนต์": "Robotics Autonomous Systems Control Engineering ROS",
    "ระบบอัตโนมัติ": "Automation Control Systems Robotics Mechatronics",
    "ความปลอดภัยทางไซเบอร์": "Cyber Security Network Security Cryptography Penetration Testing",
    "ไซเบอร์": "Cybersecurity Information Security Network Defense",
    "ความมั่นคงปลอดภัย": "Cybersecurity Information Security Threat Intelligence",
    "บล็อกเชน": "Blockchain Smart Contracts Web3 Distributed Ledger",
    "ซอฟต์แวร์": "Software Engineering Cloud Architecture DevOps",
    "วิศวกรรมซอฟต์แวร์": "Software Engineering System Architecture Microservices Agile",
    "คลาวด์": "Cloud Computing Distributed Systems Kubernetes AWS",
    "ระบบสมองกลฝังตัว": "Embedded Systems IoT Microcontrollers RTOS",
    "ไอโอที": "Internet of Things IoT Sensors Smart Devices",
    "อินเทอร์เน็ตของสรรพสิ่ง": "Internet of Things IoT Wireless Sensor Networks",
    "ควอนตัม": "Quantum Computing Quantum Information Quantum Algorithms",
    "ปฏิสัมพันธ์มนุษย์กับคอมพิวเตอร์": "Human-Computer Interaction HCI UX UI Interaction Design",

    # Electrical, Electronics & Energy
    "พลังงานหมุนเวียน": "Renewable Energy Solar Photovoltaic Wind Power Microgrid",
    "พลังงานสะอาด": "Clean Energy Renewable Energy Decarbonization Carbon Neutral",
    "พลังงานแสงอาทิตย์": "Solar Energy Photovoltaic PV Microgrid Renewable Power",
    "โซลาร์เซลล์": "Solar Cell Photovoltaic Renewable Energy",
    "ไมโครกริด": "Microgrids Smart Grid Power Electronics Energy Storage",
    "สมาร์ทกริด": "Smart Grid Power Systems Renewable Integration Distribution Network",
    "พาวเวอร์อิเล็กทรอนิกส์": "Power Electronics Inverters Converters Motor Drives",
    "อิเล็กทรอนิกส์กำลัง": "Power Electronics Converters Inverters Power Management",
    "ยานยนต์ไฟฟ้า": "Electric Vehicles EV Battery Management Systems BMS Powertrain",
    "รถยนต์ไฟฟ้า": "Electric Vehicles EV Powertrain Battery Charging Infrastructure",
    "แบตเตอรี่": "Battery Management Systems BMS Energy Storage Lithium-ion",
    "กักเก็บพลังงาน": "Energy Storage Systems Supercapacitors Battery Chemistry",
    "เซมิคอนดักเตอร์": "Semiconductors VLSI Integrated Circuits Microelectronics",
    "วงจรรวม": "Integrated Circuits IC VLSI Circuit Design Microchips",
    "ระบบควบคุม": "Control Systems Optimal Control Robust Control Feedback Automation",
    "ประมวลผลสัญญาณ": "Signal Processing DSP Digital Filters Audio Video Processing",
    "การสื่อสารไร้สาย": "Wireless Communications 5G 6G MIMO RF Microwave",
    "โทรคมนาคม": "Telecommunications Network Architecture Optical Networks Antenna",

    # Health, Biomedical & Life Sciences
    "แพทย์": "Medical Biomedical Health Clinical Medicine",
    "การแพทย์": "Medicine Healthcare Biomedical Clinical Research",
    "ชีวการแพทย์": "Biomedical Engineering Medical Devices Biomaterials Health Informatics",
    "วิศวกรรมชีวการแพทย์": "Biomedical Engineering Biomechanics Biosensors Medical Imaging",
    "สุขภาพ": "Healthcare Biomedical Digital Health Medical Technology",
    "เภสัช": "Pharmacy Pharmacology Drug Delivery Pharmaceutical Sciences",
    "เภสัชกรรม": "Pharmaceutical Sciences Drug Discovery Toxicology Pharmacokinetics",
    "ยา": "Drug Delivery Pharmacology Medicinal Chemistry Nanomedicine",
    "พันธุศาสตร์": "Genetics Genomics Bioinformatics Molecular Genetics",
    "จีโนม": "Genomics Bioengineering CRISPR Gene Editing",
    "ชีวสารสนเทศ": "Bioinformatics Computational Biology Next-Gen Sequencing",
    "ภูมิคุ้มกัน": "Immunology Immunotherapy Vaccines Cellular Biology",
    "มะเร็ง": "Cancer Research Oncology Tumor Biology Precision Medicine",
    "ประสาทวิทยา": "Neuroscience Neurobiology Cognitive Science Brain-Computer Interface",
    "ทันตแพทย์": "Dentistry Dental Biomaterials Orthodontics Oral Surgery",
    "สาธารณสุข": "Public Health Epidemiology Global Health Health Policy",

    # Business, Finance & Management
    "บริหาร": "Business Administration Management Strategy Operations",
    "การเงิน": "Finance Corporate Finance Investment Asset Pricing Quantitative Finance",
    "ควอนท์": "Quantitative Finance Algorithmic Trading Financial Modeling Derivatives",
    "การตลาด": "Marketing Digital Marketing Consumer Behavior Brand Strategy",
    "เศรษฐศาสตร์": "Economics Microeconomics Macroeconomics Econometrics Behavioral Economics",
    "เศรษฐมิติ": "Econometrics Statistical Modeling Quantitative Methods Empirical Analysis",
    "บัญชี": "Accounting Auditing Financial Reporting Taxation Corporate Governance",
    "โลจิสติกส์": "Logistics Supply Chain Management Operations Research Optimization",
    "ห่วงโซ่อุปทาน": "Supply Chain Management Operations Research Inventory Routing Logistics",
    "การจัดการ": "Strategic Management Organizational Behavior Operations Leadership",

    # Materials, Mechanical, Civil & Environmental
    "วัสดุศาสตร์": "Materials Science Nanomaterials Polymers Metallurgy Advanced Composites",
    "นาโน": "Nanotechnology Nanomaterials Nanocomposites Carbon Nanotubes",
    "พอลิเมอร์": "Polymer Science Biomaterials Composites Biodegradable Plastics",
    "เครื่องกล": "Mechanical Engineering Thermodynamics Fluid Mechanics Solid Mechanics",
    "ของไหล": "Fluid Dynamics CFD Aerodynamics Turbulence Heat Transfer",
    "เทอร์โมไดนามิกส์": "Thermodynamics Heat Transfer Energy Conversion Thermal Engineering",
    "โยธา": "Civil Engineering Structural Engineering Geotechnical Concrete Mechanics",
    "โครงสร้าง": "Structural Engineering Finite Element Analysis FEA Earthquake Engineering",
    "สิ่งแวดล้อม": "Environmental Engineering Water Treatment Waste Management Pollution Control",
    "บำบัดน้ำเสีย": "Wastewater Treatment Water Purification Environmental Biotechnology Membrane",
    "การเปลี่ยนแปลงสภาพภูมิอากาศ": "Climate Change Carbon Capture Sustainability GHG Reduction",

    # Agriculture, Food & Biotechnology
    "เกษตร": "Agricultural Sciences Smart Farming Precision Agriculture AgTech",
    "เกษตรอัจฉริยะ": "Smart Agriculture Precision Farming IoT Sensors Drone Agri-AI",
    "เทคโนโลยีอาหาร": "Food Science Food Technology Functional Foods Food Processing",
    "เทคโนโลยีชีวภาพ": "Biotechnology Bioprocess Engineering Fermentation Molecular Biology",

    # Slang & General Tech Synonyms
    "แอพ": "Mobile Application Web Technologies Frontend Backend Fullstack",
    "แอป": "Mobile Application Web Technologies Software Development",
    "เว็บ": "Web Development Fullstack Cloud Microservices REST API",
    "optimize": "optimization operations research mathematical modeling heuristic algorithm",
    "optimization": "optimization operations research linear programming metaheuristic",
    "ออปติไมซ์": "optimization mathematical programming operations research genetic algorithm"
}

import re
from pathlib import Path

# Pre-compile regex for query expansion to eliminate loop overhead
_SORTED_SYNONYM_KEYS = sorted(THAI_EN_SYNONYMS.keys(), key=len, reverse=True)
_SYNONYM_REGEX = re.compile("|".join(re.escape(k) for k in _SORTED_SYNONYM_KEYS), re.IGNORECASE)
_AI_ACRONYM_REGEX = re.compile(r"\bai\b", re.IGNORECASE)

def load_all_gemini_keys() -> List[str]:
    """Load Gemini API keys from environment variables, settings, or auto-fallback to local API.txt."""
    env_keys = os.getenv("GEMINI_API_KEYS", "") or getattr(settings, "GEMINI_API_KEYS", "")
    if env_keys.strip():
        keys = [k.strip() for k in env_keys.split(",") if k.strip()]
        if keys:
            return keys

    single_key = os.getenv("GEMINI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
    if single_key.strip():
        return [single_key.strip()]

    # Auto-discover from local API.txt if env is empty
    candidate_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "API.txt",
        Path(__file__).resolve().parent.parent.parent / "API.txt",
        Path(r"C:\Users\chaya\Documents\Program\Project\API.txt")
    ]
    for p in candidate_paths:
        if p.exists() and p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
                found = re.findall(r"AQ\.[A-Za-z0-9_\-]+", text)
                if found:
                    return found
            except Exception:
                pass

    return []

class EmbeddingService:
    def __init__(self):
        self.api_keys = load_all_gemini_keys()
        self._key_lock = threading.Lock()
        self._current_key_idx = 0
        self._clients: Dict[str, genai.Client] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_lock = threading.Lock()
        self._max_cache_size = 2048

    def _get_client(self):
        if not self.api_keys:
            return None
        with self._key_lock:
            key = self.api_keys[self._current_key_idx % len(self.api_keys)]
            if key not in self._clients:
                self._clients[key] = genai.Client(api_key=key)
            return self._clients[key]

    def _rotate_key(self):
        if not self.api_keys or len(self.api_keys) <= 1:
            return
        with self._key_lock:
            self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)

    def expand_query(self, query: str) -> str:
        """Fast single-pass expansion of Thai abbreviations into English academic terms for vector matching."""
        matched_expansions = []
        for match in _SYNONYM_REGEX.finditer(query):
            term = match.group(0).lower()
            en = THAI_EN_SYNONYMS.get(term)
            if en and en not in matched_expansions:
                matched_expansions.append(en)

        expanded = query
        if matched_expansions:
            expanded += " " + " ".join(matched_expansions)

        if _AI_ACRONYM_REGEX.search(query):
            expanded += " Artificial Intelligence"

        return expanded

    def get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Generate a 768-dimensional embedding vector using Gemini with caching & key rotation."""
        if not text or not text.strip() or not self.api_keys:
            return []
            
        clean_text = text.strip()
        with self._cache_lock:
            if clean_text in self._embedding_cache:
                return self._embedding_cache[clean_text]

        expanded_text = self.expand_query(clean_text)
        
        for attempt in range(max_retries):
            client = self._get_client()
            if not client:
                return []
            try:
                response = client.models.embed_content(
                    model='gemini-embedding-2',
                    contents=expanded_text,
                    config={'output_dimensionality': 768}
                )
                vec = response.embeddings[0].values
                if vec and len(vec) == 768:
                    with self._cache_lock:
                        if len(self._embedding_cache) >= self._max_cache_size:
                            for k in list(self._embedding_cache.keys())[:200]:
                                self._embedding_cache.pop(k, None)
                        self._embedding_cache[clean_text] = vec
                return vec
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    self._rotate_key()
                    time.sleep(0.2)
                    continue
                print(f"[EmbeddingService] Failed to generate embedding: {e}")
                self._rotate_key()
                time.sleep(0.2)
        return []

    def generate_smart_explanation(
        self,
        query: str,
        faculty: FacultyMember,
        score: float,
        matched_keywords: Optional[List[str]] = None,
        matching_pubs: Optional[List[str]] = None
    ) -> str:
        """Instantly generate a contextual, high-quality match explanation in Thai synthesizing interests & papers."""
        interests = faculty.research_interests or []
        dept = faculty.department_th or faculty.department or faculty.faculty_th or ""

        # Extract tokens from expanded query
        expanded_tokens = [t.lower() for t in self.expand_query(query).split() if len(t) >= 2]
        matched_interests = []
        for interest in interests:
            interest_lower = interest.lower()
            if any(t in interest_lower for t in expanded_tokens):
                matched_interests.append(interest)

        if matched_keywords:
            for kw in matched_keywords:
                for interest in interests:
                    if kw.lower() in interest.lower() and interest not in matched_interests:
                        matched_interests.append(interest)

        # Synthesize with publication evidence if available
        pub_mention = ""
        if matching_pubs and len(matching_pubs) > 0:
            first_pub = matching_pubs[0]
            # Truncate title cleanly if too long
            short_pub = (first_pub[:65] + "...") if len(first_pub) > 68 else first_pub
            pub_mention = f" รวมถึงมีผลงานตีพิมพ์ที่เกี่ยวข้องโดยตรง เช่น '{short_pub}'"

        if matched_interests:
            focus_str = ", ".join(matched_interests[:2])
            if score >= 85:
                return f"อาจารย์มีความเชี่ยวชาญตรงสายและมีผลงานวิจัยหลักด้าน {focus_str}{pub_mention} ซึ่งสอดคล้องกับหัวข้อวิทยานิพนธ์ของคุณในระดับสูงมาก"
            elif score >= 75:
                return f"อาจารย์มีความเชี่ยวชาญด้าน {focus_str}{pub_mention} สอดคล้องกับแนวทางการทำวิจัยและระเบียบวิธีที่คุณสนใจ"
            return f"อาจารย์มีความเชี่ยวชาญด้าน {focus_str} ซึ่งสามารถประยุกต์เข้ากับขอบเขตงานวิจัยของคุณได้เป็นอย่างดี"

        if matching_pubs and len(matching_pubs) > 0:
            short_pub = (matching_pubs[0][:65] + "...") if len(matching_pubs[0]) > 68 else matching_pubs[0]
            return f"อาจารย์มีผลงานวิจัยที่เกี่ยวข้องกับหัวข้อของคุณ เช่น '{short_pub}' ประจำ{dept or 'คณะ'}"

        if interests:
            focus_str = ", ".join(interests[:2])
            if dept:
                return f"อาจารย์ประจำ{dept} มีความเชี่ยวชาญหลักด้าน {focus_str} ซึ่งมีระเบียบวิธีวิจัยและองค์ความรู้ที่ต่อยอดกับหัวข้อของคุณได้"
            return f"อาจารย์มีความเชี่ยวชาญหลักด้าน {focus_str} ซึ่งมีความใกล้เคียงกับขอบเขตที่คุณต้องการศึกษา"

        if dept:
            return f"อาจารย์ประจำ{dept} มีความเชี่ยวชาญในสาขาวิชาที่เกี่ยวข้องและพร้อมให้คำปรึกษางานวิจัยในหัวข้อของคุณ"

        return "อาจารย์ในสาขาวิชาที่สอดคล้องกับหัวข้อวิจัยที่คุณสนใจ"

    def generate_cold_email_ai(self, req: dict, faculty: FacultyMember, max_retries: int = 2) -> tuple[str, str, list[str]]:
        """Use Gemini to draft a highly professional cold email quickly."""
        if not self.api_keys:
            return "Subject", "Body", []
            
        prof_eng_name = faculty.full_name or f"{faculty.first_name or ''} {faculty.last_name or ''}".strip()
        prof_name = faculty.full_name_th if (req.get('language') == 'th' and faculty.full_name_th) else (prof_eng_name or faculty.full_name_th or 'Professor')
        prof_dept = (faculty.department_th if req.get('language') == 'th' and faculty.department_th else faculty.department) or 'Faculty'

        prompt = f"""
        Act as an expert academic advisor. Draft a highly professional cold email for a prospective graduate student to contact a university professor.
        
        Language requested: {req.get('language', 'th')} (If 'th', write in formal Thai. If 'en', write in formal academic English.)
        Student Name: {req.get('student_name', 'Student')}
        Intended Degree: {req.get('intended_degree', "Master's/Ph.D.")}
        Student's Background: {req.get('student_background', 'N/A')}
        Proposed Research Topic: {req.get('research_topic', 'N/A')}
        
        Professor's Name: {prof_name}
        Professor's Department: {prof_dept}
        Professor's Research Interests: {', '.join(faculty.research_interests or [])}
        
        Return a JSON object with this exact structure:
        {{
            "subject": "The email subject line",
            "body": "The full email body. Include placeholders for CV attachment. Must strongly link the student's research topic to the professor's specific research interests to show they did their homework.",
            "tips": ["Tip 1", "Tip 2", "Tip 3"] // 3 practical tips for sending this email
        }}
        """
        # Prioritize Fast Flash models for sub-second generation
        for model_name in ['gemini-3.6-flash', 'gemini-2.5-flash']:
            for attempt in range(max_retries):
                client = self._get_client()
                if not client:
                    continue
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.4
                        )
                    )
                    data = json.loads(response.text)
                    return data.get("subject", ""), data.get("body", ""), data.get("tips", [])
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        self._rotate_key()
                        time.sleep(0.2)
                        continue
                    print(f"[EmbeddingService] Failed to generate cold email with {model_name}: {e}")
                    self._rotate_key()
                    
        return "หัวข้อ: ติดต่อขอคำปรึกษาด้านการวิจัย", "เรียน อาจารย์\n\nกระผม/ดิฉัน มีความประสงค์จะขอคำปรึกษาและสมัครเข้าศึกษาต่อในระดับบัณฑิตศึกษา...", ["แนบ CV และ Portfolio", "ส่งอีเมลในช่วงเวลาทำการ", "ระบุความสนใจในงานวิจัยให้ชัดเจน"]

embedding_service = EmbeddingService()
