import json
import os
import sys
import time
from pydantic import BaseModel
from google import genai
from google.genai import types

# Use one of the working keys
API_KEY = os.getenv("GEMINI_API_KEY")

class QuestionItem(BaseModel):
    text: str
    dimension: str

class QuestionList(BaseModel):
    questions: list[QuestionItem]

def generate_questions_for_dimension(dimension: str, count: int) -> list[dict]:
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    You are an expert academic career counselor specializing in the RIASEC Holland Code model.
    Generate EXACTLY {count} unique, high-quality, engaging, and diverse psychological test questions 
    in THAI language that measure the '{dimension}' dimension.
    
    IMPORTANT: The questions MUST heavily feature "Academic" contexts and university-level scenarios.
    Blend the standard RIASEC traits with academic situations (e.g., studying, researching, writing thesis, lab work, university clubs, academic competitions, solving theoretical problems, organizing campus events).
    
    The questions should be relatable to modern Thai high school students choosing a major, or university students choosing a research topic.
    Avoid repetitive phrasing. Do NOT use emojis in the text.
    Format as JSON matching the schema.
    
    Dimension context:
    - R (Realistic): Hands-on lab experiments, building prototypes, fieldwork, agricultural research, operating scientific equipment, engineering workshops.
    - I (Investigative): Academic research, theoretical physics/math, data science analysis, writing academic papers, literature review, lab analysis.
    - A (Artistic): Creative writing, performing arts, architectural design, studying literature/philosophy, media production, unstructured creative projects.
    - S (Social): Tutoring, leading study groups, sociology research, psychology case studies, nursing practicums, educational outreach.
    - E (Enterprising): Business case competitions, student council leadership, marketing research, pitching startup ideas, debating, economics.
    - C (Conventional): Statistics, accounting principles, coding algorithms, managing databases, organizing research data, strict methodological compliance.
    """
    
    print(f"Generating {count} questions for {dimension}...")
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuestionList,
                temperature=0.7
            ),
        )
        data = json.loads(response.text)
        return data.get("questions", [])
    except Exception as e:
        print(f"Error for {dimension}: {e}")
        return []

def main():
    dimensions = ["R", "I", "A", "S", "E", "C"]
    all_questions = []
    
    # 34 per dimension = 204 questions total
    for dim in dimensions:
        q_list = generate_questions_for_dimension(dim, 34)
        
        # Format them properly
        for q in q_list:
            all_questions.append({
                "id": len(all_questions) + 1,
                "text": q["text"],
                "dimension": dim
            })
            
        time.sleep(2) # Avoid rate limits
        
    # Ensure frontend data directory exists
    import pathlib
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "frontend" / "src" / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    out_path = str(data_dir / "riasec_questions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {len(all_questions)} questions to {out_path}")

if __name__ == '__main__':
    main()
