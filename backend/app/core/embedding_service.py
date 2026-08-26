import os
import time
import json
import threading
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings
from app.models.schema import FacultyMember
from google import genai
from google.genai import types

# Dictionary for mapping Thai terms/slangs to academic English terms
THAI_EN_SYNONYMS = {
    "เอไอ": "AI Artificial Intelligence",
    "ปัญญาประดิษฐ์": "AI Artificial Intelligence",
    "แมชชีนเลิร์นนิง": "Machine Learning",
    "แมชชีนเลินนิ่ง": "Machine Learning",
    "ดีปเลิร์นนิง": "Deep Learning",
    "ดาต้า": "Data Science Data Mining",
    "ข้อมูลขนาดใหญ่": "Big Data",
    "ซอฟต์แวร์": "Software Engineering",
    "บล็อกเชน": "Blockchain",
    "ความปลอดภัยทางไซเบอร์": "Cyber Security Network Security",
    "แพทย์": "Medical Biomedical Health",
    "สุขภาพ": "Healthcare Biomedical",
    "แอพ": "Mobile Application Web Technologies",
    "แอป": "Mobile Application Web Technologies",
    "optimize": "optimization operations research",
    "optimization": "optimize operations research",
    "ออปติไมซ์": "optimization optimize"
}

import re
from pathlib import Path

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
        """Expand Thai abbreviations into English academic terms for better vector matching."""
        expanded = query
        query_lower = query.lower()
        for th_term, en_terms in THAI_EN_SYNONYMS.items():
            if th_term in query_lower:
                expanded += f" {en_terms}"
        
        # Also handle purely english acronyms that might need expansion
        if "ai" in query_lower.split():
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
        matched_keywords: Optional[List[str]] = None
    ) -> str:
        """Instantly generate a contextual, high-quality match explanation in Thai without synchronous API latency."""
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

        if matched_interests:
            focus_str = ", ".join(matched_interests[:2])
            if score >= 80:
                return f"อาจารย์มีความเชี่ยวชาญและผลงานวิจัยด้าน {focus_str} ซึ่งตรงกับหัวข้อวิจัยที่คุณสนใจอย่างยิ่ง"
            return f"อาจารย์มีความเชี่ยวชาญด้าน {focus_str} สอดคล้องกับแนวทางการทำวิจัยของคุณ"

        if interests:
            focus_str = ", ".join(interests[:2])
            if dept:
                return f"อาจารย์ประจำ{dept} มีความเชี่ยวชาญหลักด้าน {focus_str} สอดคล้องกับหัวข้อวิจัยของคุณ"
            return f"อาจารย์มีความเชี่ยวชาญหลักด้าน {focus_str} ซึ่งมีความใกล้เคียงกับขอบเขตที่คุณต้องการศึกษา"

        if dept:
            return f"อาจารย์ประจำ{dept} มีความเชี่ยวชาญในสาขาวิชาที่เกี่ยวข้องกับหัวข้องานวิจัยของคุณ"

        return "อาจารย์ในสาขาวิชาที่สอดคล้องกับหัวข้อวิจัยที่คุณสนใจ"

    def _generate_explanation(self, query: str, faculty: FacultyMember, score: float, max_retries: int = 1) -> str:
        """Fast explanation generator for advisor match."""
        return self.generate_smart_explanation(query, faculty, score)


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
