import os
import re
import time
import random
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings
from app.models.schema import FacultyMember
from app.core.dsa_utils import LRUCache  # Trie removed: never used in this module
from app.core.security import sanitize_input_text
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
    "เภสัชศาสตร์": "Pharmacy Pharmaceutical Sciences Pharmacology Drug Discovery",
    "ยารักษาโรค": "Pharmaceutical Sciences Pharmacology Drug Delivery Nanomedicine",
    "พัฒนายา": "Drug Discovery Pharmacology Medicinal Chemistry Nanomedicine",
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
    "ออปติไมซ์": "optimization mathematical programming operations research genetic algorithm",

    # Humanities, Social Sciences & Education — added from the 2026-09-10
    # search_quality_benchmark Thai queries that scored 46-84 (all out-of-dictionary)
    "การแปล": "Translation Studies Interpreting Translation",
    "ล่าม": "Interpretation Interpreting Conference Interpreting",
    "ภาษาญี่ปุ่น": "Japanese Japanese Language Japanese Studies Nihongo",
    "ภาษาจีน": "Chinese Chinese Language Sinology",
    "ภาษาเกาหลี": "Korean Korean Language Korean Studies",
    "ภาษาอังกฤษ": "English Language English Linguistics TESOL",
    "ภาษาศาสตร์": "Linguistics Phonology Syntax Semantics Applied Linguistics",
    "วรรณคดี": "Literature Literary Studies Comparative Literature",
    "ประวัติศาสตร์": "History Historical Studies Historiography",
    "โบราณคดี": "Archaeology Prehistory Excavation Artifacts Anthropology",
    "มนุษย์วิทยา": "Anthropology Ethnography Cultural Studies",
    "สังคมวิทยา": "Sociology Social Research Demography",
    "รัฐศาสตร์": "Political Science Public Policy Governance International Relations",
    "กฎหมาย": "Law Legal Studies Jurisprudence",
    "นิติศาสตร์": "Law Legal Studies Jurisprudence Civil Law",
    "รัฐธรรมนูญ": "Constitutional Law Public Law Human Rights Law",
    "กฎหมายระหว่างประเทศ": "International Law Treaties Diplomacy",
    "การศึกษา": "Education Pedagogical Sciences Teaching Learning",
    "ครุศาสตร์": "Education Teacher Training Pedagogy Curriculum",
    "หลักสูตร": "Curriculum Instructional Design Learning Outcomes",
    "ปฐมวัย": "Early Childhood Education Preschool Developmental Psychology",
    "จิตวิทยา": "Psychology Cognitive Psychology Behavioral Science",
    "พหุปัญญา": "Multiple Intelligences Cognitive Psychology Learning Styles Intelligence",
    "คณิตศาสตร์": "Mathematics Mathematics Education Numeracy",
    "การละคอน": "Theater Drama Performing Arts",
    "นาฏศิลป์": "Dance Performing Arts Thai Dance Aesthetics",
    "ดนตรี": "Music Musicology Ethnomusicology Performance",
    "ศิลปะ": "Fine Arts Visual Arts Aesthetics Art History",
    "สื่อ": "Media Studies Communication Journalism Digital Media",
    "นิเทศศาสตร์": "Communication Arts Media Studies Public Relations Advertising",
    # Health & life-science gaps from the same benchmark
    "ปรสิต": "Parasitology Parasitic Diseases Helminthiology Protozoa Tropical Medicine",
    "โรคติดเชื้อ": "Infectious Diseases Infectiology Pathogenesis",
    "ระบาดวิทยา": "Epidemiology Public Health Disease Surveillance Biostatistics",
    "ผู้สูงอายุ": "Gerontology Geriatrics Aging Elderly Care Long-term Care",
    "สุขภาพจิต": "Mental Health Psychiatry Psychology Wellbeing",
    "กายภาพบำบัด": "Physical Therapy Rehabilitation Exercise Science",
    "โภชนาการ": "Nutrition Dietetics Food Science Nutritional Sciences",
    # Engineering/business gaps from the same benchmark
    "ปฐพี": "Geotechnical Engineering Soil Mechanics Rock Mechanics Foundation Engineering Slope Stability",
    "แหล่งน้ำ": "Hydrology Water Resources Civil Engineering",
    "การบิน": "Aerospace Aviation Aeronautical Engineering",
    "ต้นทุน": "Cost Accounting Managerial Accounting Activity-Based Costing",
    "การตรวจสอบ": "Auditing Internal Audit Assurance Forensic",
    "การเงินยั่งยืน": "Sustainable Finance ESG Green Finance",
    "นวัตกรรม": "Innovation Entrepreneurship Technology Management Startup",
    "การท่องเที่ยว": "Tourism Hospitality Tourism Management Ecotourism",
}

# Pre-compile regex for query expansion to eliminate loop overhead
_SORTED_SYNONYM_KEYS = sorted(THAI_EN_SYNONYMS.keys(), key=len, reverse=True)
_SYNONYM_REGEX = re.compile("|".join(re.escape(k) for k in _SORTED_SYNONYM_KEYS), re.IGNORECASE)
_AI_ACRONYM_REGEX = re.compile(r"\bai\b", re.IGNORECASE)

# ── Retry / circuit-breaker tunables ──────────────────────────────────────────
_EMBED_TIMEOUT_MS = 15_000          # 15 s per HTTP call (was 60 s)
_TOTAL_BUDGET_S   = 30.0            # hard wall per get_embedding() call
_BACKOFF_BASE_S   = 1.0             # exponential base: 1 s, 2 s, 4 s …
_BACKOFF_MAX_S    = 30.0            # cap individual sleep
_BACKOFF_JITTER_S = 0.5             # uniform [0, 0.5] jitter
_CB_FAILURE_THRESHOLD = 3           # failures before a key enters OPEN state
_CB_OPEN_DURATION_S   = 120.0       # seconds a tripped key stays OPEN
# ─────────────────────────────────────────────────────────────────────────────


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

        # O(1) Doubly Linked List + Hash Map LRU Cache
        self._embedding_cache = LRUCache[str, List[float]](capacity=2048)
        # expand_query is pure but runs a 139-alternative regex; memoize for O(1) repeats.
        self._expand_cache = LRUCache[str, str](capacity=4096)

        # ── Single-flight: deduplicate concurrent embed requests for same text ──
        # key → (threading.Event, result_holder)
        self._inflight: Dict[str, threading.Event] = {}
        self._inflight_results: Dict[str, List[float]] = {}
        self._inflight_lock = threading.Lock()

        # ── Per-key circuit breaker ────────────────────────────────────────────
        # Counts consecutive failures per key; when >= threshold, key is OPENed
        # until _cb_open_until[key] timestamp passes.
        self._cb_failures: Dict[str, int] = {}
        self._cb_open_until: Dict[str, float] = {}
        self._cb_lock = threading.Lock()

    # ── Client pool ──────────────────────────────────────────────────────────

    def _get_client(self, key: str) -> genai.Client:
        """Return a cached genai.Client for the given key, creating one if needed."""
        if key not in self._clients:
            self._clients[key] = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(timeout=_EMBED_TIMEOUT_MS),
            )
        return self._clients[key]

    # ── Key rotation ─────────────────────────────────────────────────────────

    def _rotate_key(self):
        if not self.api_keys or len(self.api_keys) <= 1:
            return
        with self._key_lock:
            self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)

    def _current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        with self._key_lock:
            return self.api_keys[self._current_key_idx % len(self.api_keys)]

    # ── Circuit breaker ───────────────────────────────────────────────────────

    def _cb_is_open(self, key: str) -> bool:
        """Return True if this key is in the OPEN (tripped) state."""
        with self._cb_lock:
            open_until = self._cb_open_until.get(key, 0.0)
            if open_until and time.monotonic() < open_until:
                return True
            # HALF-OPEN or CLOSED: reset failure counter so the next attempt is clean
            if key in self._cb_open_until:
                del self._cb_open_until[key]
                self._cb_failures[key] = 0
            return False

    def _cb_record_success(self, key: str):
        with self._cb_lock:
            self._cb_failures[key] = 0
            self._cb_open_until.pop(key, None)

    def _cb_record_failure(self, key: str):
        with self._cb_lock:
            self._cb_failures[key] = self._cb_failures.get(key, 0) + 1
            if self._cb_failures[key] >= _CB_FAILURE_THRESHOLD:
                self._cb_open_until[key] = time.monotonic() + _CB_OPEN_DURATION_S
                print(f"[EmbeddingService] Circuit OPEN for key ...{key[-6:]}: "
                      f"tripped after {self._cb_failures[key]} failures, "
                      f"resetting in {_CB_OPEN_DURATION_S:.0f}s")

    # ── Retry-After parser ────────────────────────────────────────────────────

    @staticmethod
    def _parse_retry_after(err_str: str) -> Optional[float]:
        """Extract Retry-After seconds from a 429 error string, if present."""
        m = re.search(r"[Rr]etry[-_\s]?[Aa]fter[:\s]+(\d+\.?\d*)", err_str)
        if m:
            return min(float(m.group(1)), 60.0)
        return None

    # ── Query expansion ───────────────────────────────────────────────────────

    def expand_query(self, query: str) -> str:
        """Fast single-pass expansion of Thai abbreviations into English academic terms.

        Memoized: the endpoint path calls this once per candidate via
        generate_smart_explanation, always with the SAME query — avoids
        repeated 139-alternative regex scans. The function is pure so an LRU
        on the input is exact and free.
        """
        cached = self._expand_cache.get(query)
        if cached is not None:
            return cached

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

        self._expand_cache.put(query, expanded)
        return expanded

    # ── Core embedding with full reliability fixes ────────────────────────────

    def get_embedding(
        self,
        text: str,
        max_retries: int = 3,
        timeout_budget: float = _TOTAL_BUDGET_S,
    ) -> List[float]:
        """Generate a 768-dim embedding with O(1) LRU cache, single-flight dedup,
        per-key circuit breaker, exponential backoff, Retry-After honoring, and
        a hard total-budget wall.

        Returns [] on failure so callers can fall back to lexical search.
        """
        if not text or not text.strip() or not self.api_keys:
            return []

        clean_text = text.strip()

        # ① LRU cache hit — instant return
        cached_vec = self._embedding_cache.get(clean_text)
        if cached_vec is not None:
            return cached_vec

        deadline = time.monotonic() + timeout_budget

        # ② Single-flight: if another thread is already embedding this exact text,
        #    wait for its result instead of issuing a duplicate provider call.
        leader_evt: Optional[threading.Event] = None
        follower_evt: Optional[threading.Event] = None

        with self._inflight_lock:
            if clean_text in self._inflight:
                # Follower: grab the existing event
                follower_evt = self._inflight[clean_text]
            else:
                # Leader: create and register the event
                leader_evt = threading.Event()
                self._inflight[clean_text] = leader_evt

        if follower_evt is not None:
            # Wait up to remaining budget, then return whatever leader stored
            remaining = max(0.0, deadline - time.monotonic())
            follower_evt.wait(timeout=remaining)
            # Successful leaders also populate the LRU, so check it first; the
            # in-flight holder only bridges the gap until the leader cleans up.
            cached_vec = self._embedding_cache.get(clean_text)
            if cached_vec is not None:
                return cached_vec
            with self._inflight_lock:
                return self._inflight_results.get(clean_text, [])

        # Leader: perform the actual embedding then wake all followers
        result: List[float] = []
        try:
            result = self._do_embed(clean_text, max_retries, deadline)
        finally:
            with self._inflight_lock:
                if result:
                    self._inflight_results[clean_text] = result
                self._inflight.pop(clean_text, None)
            # Signal followers *after* releasing the lock so they can read results
            assert leader_evt is not None
            leader_evt.set()
            # Drop the hand-off entry: it was never evicted and leaked ~25 KB per
            # unique query. Followers read the bounded LRU cache instead.
            with self._inflight_lock:
                if self._inflight.get(clean_text) is None:
                    self._inflight_results.pop(clean_text, None)

        return result

    def _do_embed(self, clean_text: str, max_retries: int, deadline: float) -> List[float]:
        """Internal: attempt embedding with retry, backoff, circuit breaker."""
        expanded_text = self.expand_query(clean_text)
        n_keys = len(self.api_keys)

        for attempt in range(max_retries):
            # ③ Budget check before each attempt
            remaining = deadline - time.monotonic()
            if remaining < 2.0:
                print(f"[EmbeddingService] Budget exhausted before attempt {attempt + 1}, giving up.")
                return []

            # ④ Pick the current key; skip OPEN keys (rotate up to n_keys times)
            skipped = 0
            while skipped < n_keys:
                key = self._current_key()
                if key and not self._cb_is_open(key):
                    break
                self._rotate_key()
                skipped += 1
            else:
                # All keys are tripped
                print("[EmbeddingService] All keys in OPEN state — returning [].")
                return []

            if not key:
                return []

            client = self._get_client(key)

            # ⑤ Try each model in priority order
            for model_name in ["gemini-embedding-2", "gemini-embedding-001"]:
                try:
                    response = client.models.embed_content(
                        model=model_name,
                        contents=expanded_text,
                        config={"output_dimensionality": 768},
                    )
                    vec = response.embeddings[0].values
                    if vec and len(vec) == 768:
                        self._embedding_cache.put(clean_text, vec)
                        self._cb_record_success(key)
                        return vec
                except Exception as e:
                    err_str = str(e)

                    if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED"]):
                        # ⑥ Honor Retry-After if present
                        retry_after = self._parse_retry_after(err_str)
                        if retry_after:
                            sleep_s = min(retry_after, max(0.0, deadline - time.monotonic() - 1.0))
                            if sleep_s > 0:
                                time.sleep(sleep_s)
                        self._cb_record_failure(key)
                        continue  # try next model

                    if any(code in err_str for code in ["401", "UNAUTHENTICATED", "403", "PERMISSION_DENIED"]):
                        self._cb_record_failure(key)
                        break  # auth failure — rotate key, don't try other model

                    print(f"[EmbeddingService] embed failed ({model_name}): {e}")
                    self._cb_record_failure(key)

            # ⑦ Rotate key after exhausting models for this attempt
            self._rotate_key()

            # ⑧ Exponential backoff with jitter before next attempt
            if attempt < max_retries - 1:
                backoff = min(_BACKOFF_BASE_S * (2 ** attempt), _BACKOFF_MAX_S)
                jitter = random.uniform(0, _BACKOFF_JITTER_S)
                sleep_s = min(backoff + jitter, max(0.0, deadline - time.monotonic() - 1.0))
                if sleep_s > 0:
                    time.sleep(sleep_s)

        return []

    # ── Smart explanation (pure Python, no provider call) ────────────────────

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


embedding_service = EmbeddingService()
