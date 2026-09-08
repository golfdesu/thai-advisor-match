# -*- coding: utf-8 -*-
"""
Deep Regional Universities Extraction (NU, BUU, SU, MSU, WU, UP, MJU, TSU, UBU)
"""
import sys, os, json
sys.path.append('backend')
from app.core.database import SessionLocal
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from dotenv import load_dotenv
load_dotenv('backend/.env')

with open('data/raw_regional_universities_deep_snippets.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

snippets = []
for k, v in raw_data.items():
    for item in v:
        t = item.get('title') or ''
        s = item.get('snippet') or ''
        l = item.get('link') or ''
        snippets.append(f"{t}: {s} [URL: {l}]")

text_chunk = "\n".join(snippets)
print(f"Total input regional text length: {len(text_chunk)}")

db = SessionLocal()
agent = FacultyExtractionAgent(
    target_university_th="มหาวิทยาลัยภูมิภาค (นเรศวร, บูรพา, ศิลปากร, มหาสารคาม, วลัยลักษณ์, พะเยา, แม่โจ้, ทักษิณ, อุบลราชธานี)",
    target_university_en="Regional Universities (NU, BUU, SU, MSU, WU, UP, MJU, TSU, UBU)",
    target_faculty_th="คณาจารย์และนักวิจัย",
    target_faculty_en="Faculty Members and Researchers",
    db_session=db
)

html = f"<html><body><h1>คณาจารย์มหาวิทยาลัยภูมิภาค</h1><div>{text_chunk}</div></body></html>"
agent.step_with_html(html, current_url="https://regional.ac.th")

profiles = []
for p in agent.state.faculties.values():
    if hasattr(p, "model_dump"):
        profiles.append(p.model_dump())
    elif isinstance(p, dict):
        profiles.append(p)
    else:
        profiles.append(dict(p))

print(f"Extracted {len(profiles)} regional profiles before disambiguation.")

# Disambiguate universities
for p in profiles:
    ctx = f"{p.get('email', '')} {p.get('department_th', '')} {p.get('full_name_th', '')} {' '.join(p.get('research_interests', []))}".lower()

    if 'nu.ac.th' in ctx or 'นเรศวร' in ctx:
        p['university_th'] = 'มหาวิทยาลัยนเรศวร'
        p['university'] = 'Naresuan University'
    elif 'buu.ac.th' in ctx or 'บูรพา' in ctx:
        p['university_th'] = 'มหาวิทยาลัยบูรพา'
        p['university'] = 'Burapha University'
    elif 'su.ac.th' in ctx or 'ศิลปากร' in ctx:
        p['university_th'] = 'มหาวิทยาลัยศิลปากร'
        p['university'] = 'Silpakorn University'
    elif 'msu.ac.th' in ctx or 'มหาสารคาม' in ctx:
        p['university_th'] = 'มหาวิทยาลัยมหาสารคาม'
        p['university'] = 'Mahasarakham University'
    elif 'wu.ac.th' in ctx or 'วลัยลักษณ์' in ctx:
        p['university_th'] = 'มหาวิทยาลัยวลัยลักษณ์'
        p['university'] = 'Walailak University'
    elif 'up.ac.th' in ctx or 'พะเยา' in ctx:
        p['university_th'] = 'มหาวิทยาลัยพะเยา'
        p['university'] = 'University of Phayao'
    elif 'mju.ac.th' in ctx or 'แม่โจ้' in ctx:
        p['university_th'] = 'มหาวิทยาลัยแม่โจ้'
        p['university'] = 'Maejo University'
    elif 'tsu.ac.th' in ctx or 'ทักษิณ' in ctx:
        p['university_th'] = 'มหาวิทยาลัยทักษิณ'
        p['university'] = 'Thaksin University'
    elif 'ubu.ac.th' in ctx or 'อุบล' in ctx or 'อุบลราชธานี' in ctx:
        p['university_th'] = 'มหาวิทยาลัยอุบลราชธานี'
        p['university'] = 'Ubon Ratchathani University'
    else:
        p['university_th'] = 'มหาวิทยาลัยนเรศวร'
        p['university'] = 'Naresuan University'

out_file = 'backend/scripts/data_sources/regional_deep_ai_extracted.py'
with open(out_file, 'w', encoding='utf-8') as fp:
    fp.write("# -*- coding: utf-8 -*-\n")
    fp.write(f'"""\nRegional Deep Academic Dataset ({out_file})\n"""\n\n')
    fp.write(f"EXTRACTED_FACULTIES = {json.dumps(profiles, ensure_ascii=False, indent=2)}\n")

print(f"Saved {len(profiles)} clean profiles to {out_file} successfully!")
db.close()
