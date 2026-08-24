import math
import re
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.models.schema import FacultyMember, SearchMatchResult

# Bilingual Domain Concept Synonyms Dictionary for Electrical & Computer Engineering
DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    "power electronics": [
        "อิเล็กทรอนิกส์กำลัง", "power electronic", "inverter", "converter", "dc-dc", "ac-dc", "rectifier",
        "อินเวอร์เตอร์", "คอนเวอร์เตอร์", "pwm", "switched-mode", "high power converter", "แปลงผันพลังงาน"
    ],
    "อิเล็กทรอนิกส์กำลัง": [
        "power electronics", "power electronic", "inverter", "converter", "อินเวอร์เตอร์", "คอนเวอร์เตอร์", "การแปลงผันพลังงาน"
    ],
    "microgrid": [
        "ไมโครกริด", "smart grid", "สมาร์ทกริด", "grid-connected", "distributed generation", "ระบบโครงข่ายไฟฟ้าขนาดเล็ก"
    ],
    "ไมโครกริด": [
        "microgrid", "microgrids", "smart grid", "สมาร์ทกริด", "ระบบจำหน่ายไฟฟ้า"
    ],
    "electric vehicle": [
        "ev", "ยานยนต์ไฟฟ้า", "รถยนต์ไฟฟ้า", "ยานยนต์", "battery storage", "ระบบกักเก็บพลังงาน", "charging station"
    ],
    "ยานยนต์ไฟฟ้า": [
        "electric vehicle", "ev", "electric vehicles", "รถยนต์ไฟฟ้า", "ระบบกักเก็บพลังงาน", "battery"
    ],
    "motor drive": [
        "electric drive", "มอเตอร์ไดรฟ์", "การควบคุมเครื่องจักรกลไฟฟ้า", "motor control", "electrical machine", "dfig", "pmsg"
    ],
    "เครื่องจักรกลไฟฟ้า": [
        "motor drive", "electric drive", "electrical machine", "มอเตอร์", "เครื่องกำเนิดไฟฟ้า", "การควบคุมมอเตอร์"
    ],
    "มอเตอร์ไดรฟ์": [
        "motor drive", "electric drive", "motor control", "การควบคุมเครื่องจักรกลไฟฟ้า", "electrical machine"
    ],
    "renewable energy": [
        "พลังงานหมุนเวียน", "พลังงานทดแทน", "solar", "photovoltaic", "wind energy", "พลังงานแสงอาทิตย์", "โซลาร์เซลล์", "พลังงานลม"
    ],
    "พลังงานหมุนเวียน": [
        "renewable energy", "solar", "photovoltaic", "wind", "พลังงานทดแทน", "พลังงานแสงอาทิตย์", "พลังงานลม"
    ],
    "biomedical": [
        "ชีวการแพทย์", "สัญญาณชีวการแพทย์", "biomedical signal", "biomedical image", "ภาพทางการแพทย์", "ecg", "eeg"
    ],
    "ชีวการแพทย์": [
        "biomedical", "biomedical engineering", "สัญญาณชีวการแพทย์", "ภาพทางการแพทย์", "medical image"
    ],
    "ai": [
        "artificial intelligence", "machine learning", "deep learning", "ปัญญาประดิษฐ์", "การเรียนรู้ของเครื่อง",
        "neural network", "pattern recognition", "computer vision"
    ],
    "ปัญญาประดิษฐ์": [
        "ai", "artificial intelligence", "machine learning", "deep learning", "neural network", "การเรียนรู้ของเครื่อง"
    ],
    "smart grid": [
        "สมาร์ทกริด", "ระบบไฟฟ้าอัจฉริยะ", "power system", "distribution system", "ระบบไฟฟ้ากำลัง"
    ],
    "สมาร์ทกริด": [
        "smart grid", "power system planning", "distribution system", "ระบบไฟฟ้ากำลัง"
    ],
    "photonics": [
        "โฟโทนิกส์", "optical communication", "fiber optic", "ใยแก้วนำแสง", "laser", "เลเซอร์", "optical sensor"
    ],
    "โฟโทนิกส์": [
        "photonics", "optical", "fiber optic", "ใยแก้วนำแสง", "เลเซอร์"
    ]
}


def _tokenize(text: str) -> List[str]:
    """Tokenize Thai and English text into words and n-grams."""
    if not text:
        return []
    text = text.lower()
    tokens = re.findall(r'[a-zA-Z0-9]+|[\u0E00-\u0E7F]+', text)
    return tokens


def _expand_query_concepts(query: str) -> List[str]:
    """Expand query with bilingual domain synonyms."""
    query_lower = query.lower()
    expanded = [query_lower]
    
    for concept, synonyms in DOMAIN_SYNONYMS.items():
        if concept in query_lower:
            expanded.extend(synonyms)
        else:
            for syn in synonyms:
                if syn in query_lower:
                    expanded.append(concept)
                    expanded.extend(synonyms)
                    break
    return list(dict.fromkeys(expanded))


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[EmbeddingService] Gemini client initialization error: {e}")

    def calculate_text_match(self, query: str, faculty: FacultyMember) -> Tuple[float, List[str]]:
        """Calculate hybrid match score between query and faculty profile with bilingual concept expansion."""
        expanded_concepts = _expand_query_concepts(query)
        expanded_query_text = " ".join(expanded_concepts)
        query_tokens = set(_tokenize(expanded_query_text))

        if not query_tokens:
            return 0.0, []

        interests_text = " ".join(faculty.research_interests).lower()
        courses_text = " ".join(faculty.taught_courses).lower() if faculty.taught_courses else ""
        pubs_text = " ".join([pub.title for pub in faculty.featured_publications]).lower() if faculty.featured_publications else ""
        
        full_corpus = " ".join([
            faculty.full_name_th or "",
            faculty.full_name or "",
            faculty.department_th or "",
            interests_text,
            courses_text,
            pubs_text,
            faculty.embedding_text or ""
        ]).lower()

        # Helper function for safer substring matching + Typo Tolerance
        def _word_in_text(word: str, text: str) -> bool:
            import re
            from rapidfuzz import fuzz
            
            word_lower = word.lower().strip()
            text_lower = text.lower()
            
            # 1. Exact Match Logic
            # If word is purely English alphanumeric, enforce word boundary to avoid "ai" matching "photovoltaic"
            if re.match(r'^[a-z0-9\s]+$', word_lower):
                # Check for exact word boundaries
                if re.search(rf'\b{re.escape(word_lower)}\b', text_lower):
                    return True
            elif word_lower in text_lower:
                return True
                
            # 2. Fuzzy Match Logic (Typo Tolerance)
            # Only apply to longer words (>= 4 chars) to prevent short abbreviations from matching random words
            if len(word_lower) >= 4:
                # Check phrase partial similarity
                if fuzz.partial_ratio(word_lower, text_lower) >= 85:
                    return True
                    
                # Check individual word similarities (fixes swapped characters, missed keys)
                text_words = text_lower.split()
                query_words = word_lower.split()
                
                # If query is a single word, check against all words in text
                if len(query_words) == 1:
                    for t_word in text_words:
                        if fuzz.ratio(word_lower, t_word) >= 80:
                            return True

            return False

        # 1. Research Interest & Publication Match (Weight: 65%)
        research_match_score = 0.0
        matched_keywords = []
        
        # Check interests
        for interest in faculty.research_interests:
            interest_lower = interest.lower()
            if _word_in_text(query, interest_lower):
                research_match_score += 0.65
                matched_keywords.append(interest)
            for concept in expanded_concepts:
                if len(concept) >= 3 and _word_in_text(concept, interest_lower):
                    research_match_score += 0.35
                    matched_keywords.append(interest)
                    break
                    
        # Check publications
        for pub in faculty.featured_publications:
            pub_lower = pub.title.lower()
            if _word_in_text(query, pub_lower):
                research_match_score += 0.65
                matched_keywords.append(f"ผลงานวิจัย: {pub.title[:50]}...")
            for concept in expanded_concepts:
                if len(concept) >= 3 and _word_in_text(concept, pub_lower):
                    research_match_score += 0.35
                    matched_keywords.append(f"ผลงานวิจัย: {pub.title[:50]}...")
                    break

        # 2. Taught Courses Match (Weight: 25%)
        courses_match_score = 0.0
        if faculty.taught_courses:
            for course in faculty.taught_courses:
                course_lower = course.lower()
                if _word_in_text(query, course_lower):
                    courses_match_score += 0.50
                    matched_keywords.append(f"สอนวิชา: {course}")
                for concept in expanded_concepts:
                    if len(concept) >= 3 and _word_in_text(concept, course_lower):
                        courses_match_score += 0.25
                        matched_keywords.append(f"สอนวิชา: {course}")
                        break

        # 3. General Corpus Token Overlap (Weight: 10%)
        corpus_tokens = set(_tokenize(full_corpus))
        matched_tokens = query_tokens.intersection(corpus_tokens)
        token_overlap = len(matched_tokens) / (math.sqrt(len(query_tokens)) * math.sqrt(max(1, len(corpus_tokens))) + 1e-5)

        raw_score = (min(1.0, research_match_score) * 0.65) + (min(1.0, courses_match_score) * 0.25) + (min(1.0, token_overlap * 3.5) * 0.10)
        
        # Scale to percentage (10% - 98%)
        match_percentage = min(98.5, max(12.0, round(float(raw_score * 100), 1)))

        # If no specific research/course keyword matched, reduce generic token baseline
        if not matched_keywords:
            match_percentage = min(35.0, round(float(token_overlap * 50.0) + 12.0, 1))

        return match_percentage, list(dict.fromkeys(matched_keywords))

    def rank_faculty(
        self,
        query: str,
        faculty_list: List[FacultyMember],
        top_k: int = 10
    ) -> List[SearchMatchResult]:
        """Rank faculty members using semantic embedding or hybrid lexical matching."""
        results = []
        
        for faculty in faculty_list:
            score, matched_kw = self.calculate_text_match(query, faculty)
            explanation = self._generate_explanation(query, faculty, matched_kw, score)
            
            results.append(SearchMatchResult(
                faculty=faculty,
                match_score=score,
                ai_explanation=explanation,
                matched_keywords=matched_kw
            ))

        # Sort by match score descending
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results[:top_k]

    def _generate_explanation(
        self,
        query: str,
        faculty: FacultyMember,
        matched_keywords: List[str],
        score: float
    ) -> str:
        """Create a human-readable AI explanation of why this faculty member matches."""
        interests_str = ", ".join(faculty.research_interests[:3]) if faculty.research_interests else "วิศวกรรมไฟฟ้าขั้นสูง"
        
        if score >= 70:
            return f"อาจารย์มีความเชี่ยวชาญตรงกับ '{query}' สูงมาก โดยเฉพาะด้าน {interests_str}"
        elif score >= 40:
            return f"มีความสอดคล้องกับแนวทางงานวิจัยในสาขา {faculty.department_th} โดยมุ่งเน้น {interests_str}"
        else:
            return f"สังกัด {faculty.department_th} มหาวิทยาลัยเชียงใหม่ มีพื้นฐานงานวิจัยที่เกี่ยวข้องในด้าน {interests_str}"


embedding_service = EmbeddingService()
