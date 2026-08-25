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
    "แอป": "Mobile Application Web Technologies",
    "optimize": "optimization operations research",
    "optimization": "optimize operations research",
    "ออปติไมซ์": "optimization optimize"
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
        """Use Gemini 3.6 Flash to create a human-readable AI explanation of why this faculty member matches."""
        if not self.client:
            interests_str = ", ".join(faculty.research_interests[:3]) if faculty.research_interests else "ไม่ระบุข้อมูลการวิจัย"
            return f"ตรงกับความสนใจเรื่อง {interests_str}"
            
        prompt = f"""
        Student's Thesis Idea: "{query}"
        Professor's Name: {faculty.full_name_th}
        Professor's Department: {faculty.department_th}
        Professor's Research Interests: {', '.join(faculty.research_interests)}
        
        Write a concise, convincing 2-sentence explanation in Thai (max 40 words) for the student, explaining exactly WHY this professor is a great fit for their thesis idea. Tone: Professional, encouraging.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[EmbeddingService] Failed to generate explanation: {e}")
            interests_str = ", ".join(faculty.research_interests[:3]) if faculty.research_interests else "หัวข้อวิจัยที่เกี่ยวข้อง"
            return f"อาจารย์มีความเชี่ยวชาญด้าน {interests_str} ซึ่งสอดคล้องกับความสนใจของคุณ"

    def generate_cold_email_ai(self, req: dict, faculty: FacultyMember) -> tuple[str, str, list[str]]:
        """Use Gemini Pro to draft a highly professional cold email."""
        if not self.client:
            return "Subject", "Body", []
            
        prompt = f"""
        Act as an expert academic advisor. Draft a highly professional cold email for a prospective graduate student to contact a university professor.
        
        Language requested: {req.get('language', 'th')} (If 'th', write in formal Thai. If 'en', write in formal academic English.)
        Student Name: {req.get('student_name', 'Student')}
        Intended Degree: {req.get('intended_degree', "Master's/Ph.D.")}
        Student's Background: {req.get('student_background', 'N/A')}
        Proposed Research Topic: {req.get('research_topic', 'N/A')}
        
        Professor's Name: {faculty.full_name_th if req.get('language') == 'th' else faculty.first_name + ' ' + faculty.last_name}
        Professor's Department: {faculty.department_th if req.get('language') == 'th' else faculty.department}
        Professor's Research Interests: {', '.join(faculty.research_interests)}
        
        Return a JSON object with this exact structure:
        {{
            "subject": "The email subject line",
            "body": "The full email body. Include placeholders for CV attachment. Must strongly link the student's research topic to the professor's specific research interests to show they did their homework.",
            "tips": ["Tip 1", "Tip 2", "Tip 3"] // 3 practical tips for sending this email
        }}
        """
        try:
            from google.genai import types
            import json
            response = self.client.models.generate_content(
                model='gemini-3.1-pro',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4
                )
            )
            data = json.loads(response.text)
            return data.get("subject", ""), data.get("body", ""), data.get("tips", [])
        except Exception as e:
            print(f"[EmbeddingService] Failed to generate cold email: {e}")
            return "Error generating email", "Please try again later or check your API key limits.", []

embedding_service = EmbeddingService()
