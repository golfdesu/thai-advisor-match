import os
import re

file = 'backend/scripts/generate_riasec_quiz.py'
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'API_KEY\s*=\s*\".*?\"', 'API_KEY = os.getenv("GEMINI_API_KEY")', content)

with open(file, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed generate_riasec_quiz.py')
