import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google import genai

keys=[]
for p in [r"C:\Users\chaya\Documents\Program\Project\API.txt", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "API.txt")]:
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            for line in f:
                import re
                m=re.search(r"AQ\.[A-Za-z0-9_\-]+", line)
                if m:
                    keys.append(m.group(0))

# dedup
keys=list(dict.fromkeys(keys))
print(f"Found {len(keys)} keys from API.txt")
for i, k in enumerate(keys):
    print(f" {i+1:2}. {k[:20]}... len={len(k)}")

# Test each key
for i, key in enumerate(keys):
    client=genai.Client(api_key=key)
    try:
        resp=client.models.generate_content(model='gemini-3.6-flash', contents='Hello test')
        txt=resp.text[:50].replace('\n',' ') if resp.text else "no text"
        print(f"Key {i+1:2} OK: {txt[:40]}")
    except Exception as e:
        err=str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            # extract quota
            print(f"Key {i+1:2} QUOTA EXHAUSTED")
        else:
            print(f"Key {i+1:2} ERR: {err[:120]}")
