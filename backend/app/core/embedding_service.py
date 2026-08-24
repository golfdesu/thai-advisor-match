import math
from typing import List
from app.core.config import settings
from app.models.schema import FacultyMember
from google import genai

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
    "แอป": "Mobile Application Web Technologies"
}

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[EmbeddingService] Gemini client initialization error: {e}")

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

    def get_embedding(self, text: str) -> List[float]:
        """Generate a 768-dimensional embedding vector using Gemini."""
        if not self.client:
            return []
            
        expanded_text = self.expand_query(text)
        
        try:
            response = self.client.models.embed_content(
                model='gemini-embedding-2',
                contents=expanded_text,
                config={'output_dimensionality': 768}
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"[EmbeddingService] Failed to generate embedding: {e}")
            return []

    def _generate_explanation(self, query: str, faculty: FacultyMember, score: float) -> str:
        """Create a human-readable AI explanation of why this faculty member matches."""
        interests_str = ", ".join(faculty.research_interests[:3]) if faculty.research_interests else "ความเชี่ยวชาญเฉพาะทาง"
        
        if score >= 80:
            return f"ผลงานและความเชี่ยวชาญของอาจารย์ตรงกับหัวข้อ '{query}' ของคุณสูงมาก โดยเฉพาะด้าน {interests_str}"
        elif score >= 50:
            return f"อาจารย์ในภาควิชา {faculty.department_th} มีงานวิจัยที่สอดคล้องกับคุณในด้าน {interests_str}"
        else:
            return f"อาจารย์มีพื้นฐานในภาควิชา {faculty.department_th} ซึ่งอาจให้คำปรึกษาที่เกี่ยวข้องได้ในด้าน {interests_str}"

embedding_service = EmbeddingService()
