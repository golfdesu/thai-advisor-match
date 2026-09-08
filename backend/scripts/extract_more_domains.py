# -*- coding: utf-8 -*-
"""
Fine Arts, Communication Arts, Journalism, Humanities & SUT Science extraction
"""
import sys, os, json
sys.path.append('backend')
from app.core.database import SessionLocal
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from dotenv import load_dotenv
load_dotenv('backend/.env')

with open('data/raw_more_humanities_arts_snippets.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

def run_extraction(target_uni_th, target_uni_en, target_fac_th, target_fac_en, queries, out_file):
    snippets = []
    for q in queries:
        for item in raw_data.get(q, []):
            t = item.get('title') or ''
            s = item.get('snippet') or ''
            l = item.get('link') or ''
            snippets.append(f"{t}: {s} [URL: {l}]")

    text_chunk = "\n".join(snippets)
    db = SessionLocal()
    agent = FacultyExtractionAgent(
        target_university_th=target_uni_th,
        target_university_en=target_uni_en,
        target_faculty_th=target_fac_th,
        target_faculty_en=target_fac_en,
        db_session=db
    )
    html = f"<html><body><h1>{target_fac_th} คณาจารย์</h1><p>{text_chunk}</p></body></html>"
    agent.step_with_html(html, current_url="https://academic.ac.th")

    profiles = []
    for p in agent.state.faculties.values():
        if hasattr(p, "model_dump"):
            profiles.append(p.model_dump())
        elif isinstance(p, dict):
            profiles.append(p)
        else:
            profiles.append(dict(p))

    # Disambiguate individual records
    for p in profiles:
        email = (p.get('email') or '').lower()
        dep = p.get('department_th') or ''
        name = p.get('full_name_th') or ''
        bio = ' '.join(p.get('research_interests', []))
        ctx = f"{email} {dep} {name} {bio}".lower()

        if 'chula' in ctx or 'นิเทศ' in ctx:
            p['university_th'] = 'จุฬาลงกรณ์มหาวิทยาลัย'
            p['university'] = 'Chulalongkorn University'
            p['faculty_th'] = 'คณะนิเทศศาสตร์'
            p['faculty'] = 'Faculty of Communication Arts'
        elif 'tu.ac.th' in ctx or 'วารสาร' in ctx or 'ธรรมศาสตร์' in ctx:
            p['university_th'] = 'มหาวิทยาลัยธรรมศาสตร์'
            p['university'] = 'Thammasat University'
            p['faculty_th'] = 'คณะวารสารศาสตร์และสื่อสารมวลชน'
            p['faculty'] = 'Faculty of Journalism and Mass Communication'
        elif 'su.ac.th' in ctx or 'ศิลปากร' in ctx or 'จิตรกรรม' in ctx or 'อักษร' in ctx:
            p['university_th'] = 'มหาวิทยาลัยศิลปากร'
            p['university'] = 'Silpakorn University'
            if 'อักษร' in ctx:
                p['faculty_th'] = 'คณะอักษรศาสตร์'
                p['faculty'] = 'Faculty of Arts'
            else:
                p['faculty_th'] = 'คณะจิตรกรรม ประติมากรรมและภาพพิมพ์'
                p['faculty'] = 'Faculty of Painting, Sculpture and Graphic Arts'
        elif 'cmu.ac.th' in ctx or 'วิจิตรศิลป์' in ctx or 'สังคมศาสตร์' in ctx or 'มนุษยศาสตร์' in ctx or 'เชียงใหม่' in ctx:
            p['university_th'] = 'มหาวิทยาลัยเชียงใหม่'
            p['university'] = 'Chiang Mai University'
            if 'วิจิตรศิลป์' in ctx:
                p['faculty_th'] = 'คณะวิจิตรศิลป์'
                p['faculty'] = 'Faculty of Fine Arts'
            elif 'มนุษย์' in ctx or 'มนุษยศาสตร์' in ctx:
                p['faculty_th'] = 'คณะมนุษยศาสตร์'
                p['faculty'] = 'Faculty of Humanities'
            else:
                p['faculty_th'] = 'คณะสังคมศาสตร์'
                p['faculty'] = 'Faculty of Social Sciences'
        elif 'sut.ac.th' in ctx or 'สุรนารี' in ctx or 'มทส' in ctx:
            p['university_th'] = 'มหาวิทยาลัยเทคโนโลยีสุรนารี'
            p['university'] = 'Suranaree University of Technology'
            p['faculty_th'] = 'สำนักวิชาวิทยาศาสตร์'
            p['faculty'] = 'Institute of Science'

    with open(out_file, 'w', encoding='utf-8') as fp:
        fp.write("# -*- coding: utf-8 -*-\n")
        fp.write(f'"""\nAcademic Dataset ({out_file})\n"""\n\n')
        fp.write(f"EXTRACTED_FACULTIES = {json.dumps(profiles, ensure_ascii=False, indent=2)}\n")

    print(f"Saved {len(profiles)} profiles into {out_file}")
    db.close()

if __name__ == '__main__':
    # Batch 1: CommArts & Journalism
    run_extraction(
        target_uni_th="จุฬาลงกรณ์มหาวิทยาลัย และ มหาวิทยาลัยธรรมศาสตร์",
        target_uni_en="Chulalongkorn University & Thammasat University",
        target_fac_th="คณะนิเทศศาสตร์ และ คณะวารสารศาสตร์และสื่อสารมวลชน",
        target_fac_en="Faculty of Communication Arts & Journalism",
        queries=['commarts.chula.ac.th อาจารย์ประจำ', 'jc.tu.ac.th อาจารย์ประจำ คณะวารสารศาสตร์'],
        out_file='backend/scripts/data_sources/commarts_journalism_ai_extracted.py'
    )

    # Batch 2: Fine Arts & Humanities
    run_extraction(
        target_uni_th="มหาวิทยาลัยศิลปากร และ มหาวิทยาลัยเชียงใหม่",
        target_uni_en="Silpakorn University & Chiang Mai University",
        target_fac_th="คณะจิตรกรรม, คณะวิจิตรศิลป์, คณะอักษรศาสตร์, คณะมนุษยศาสตร์ และ คณะสังคมศาสตร์",
        target_fac_en="Faculty of Fine Arts, Humanities & Social Sciences",
        queries=[
            'finearts.su.ac.th คณะจิตรกรรม ศิลปากร อาจารย์ประจำ',
            'finearts.cmu.ac.th อาจารย์ คณะวิจิตรศิลป์ มหาวิทยาลัยเชียงใหม่',
            'arts.su.ac.th คณะอักษรศาสตร์ ศิลปากร อาจารย์',
            'human.cmu.ac.th อาจารย์ประจำ คณะมนุษยศาสตร์',
            'soc.cmu.ac.th อาจารย์ประจำ คณะสังคมศาสตร์'
        ],
        out_file='backend/scripts/data_sources/finearts_humanities_ai_extracted.py'
    )

    # Batch 3: SUT Science & Regional Excellence
    run_extraction(
        target_uni_th="มหาวิทยาลัยเทคโนโลยีสุรนารี",
        target_uni_en="Suranaree University of Technology",
        target_fac_th="สำนักวิชาวิทยาศาสตร์",
        target_fac_en="Institute of Science",
        queries=['science.sut.ac.th คณาจารย์ สำนักวิชาวิทยาศาสตร์ มทส'],
        out_file='backend/scripts/data_sources/sut_science_ai_extracted.py'
    )
