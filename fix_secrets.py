import os
import re

files = [
    'backend/app/api/routes_career_quiz.py',
    'backend/scripts/update_course_embeddings.py',
    'backend/scripts/update_embeddings.py',
    'backend/scripts/ai_university_crawler.py',
    'backend/scripts/ai_university_crawler_serp.py',
    'backend/scripts/generate_riasec_quiz.py'
]

pattern = r'API_KEYS\s*=\s*\[.*?\]'
replacement = 'API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")] if os.getenv("GEMINI_API_KEYS") else [os.getenv("GEMINI_API_KEY")]'

for file in files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            if 'import os' not in new_content:
                new_content = 'import os\n' + new_content
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Fixed secrets in {file}')
        else:
            print(f'No match in {file}')
