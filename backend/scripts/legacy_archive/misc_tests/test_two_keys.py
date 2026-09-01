import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from google import genai
keys=[]
with open(r"C:\Users\chaya\Documents\Program\Project\API.txt", encoding='utf-8') as f:
    for line in f:
        m=re.search(r"AQ\.[A-Za-z0-9_\-]+", line)
        if m:
            keys.append(m.group(0))
print('total', len(keys))
for idx in [0, 8, 9, 16]:
    key=keys[idx]
    print(f'Testing key {idx+1} {key[:20]}...')
    try:
        c=genai.Client(api_key=key)
        r=c.models.generate_content(model='gemini-3.6-flash', contents='Hi')
        txt=r.text or ""
        print(f'  OK len={len(txt)} txt={txt[:30]}')
    except Exception as e:
        s=str(e)
        print(f'  ERR {s[:300]}')
