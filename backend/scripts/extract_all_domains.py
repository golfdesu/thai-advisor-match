# -*- coding: utf-8 -*-
"""
Execute SKILL.state Extraction for Architecture, Fine Arts, Humanities, Social Sciences & Regional Centers
"""
import sys, os, json
sys.path.append('backend')
from app.core.database import SessionLocal
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from dotenv import load_dotenv
load_dotenv('backend/.env')

def extract_domain(target_uni_th, target_uni_en, target_fac_th, target_fac_en, queries, raw_file, out_file):
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    snippets = []
    for q in queries:
        for item in raw_data.get(q, []):
            t = item.get('title') or ''
            s = item.get('snippet') or ''
            l = item.get('link') or ''
            snippets.append(f"{t}: {s} [Link: {l}]")

    text_chunk = "\n".join(snippets)
    print(f"[{target_fac_th}] Input text length: {len(text_chunk)}")

    db = SessionLocal()
    agent = FacultyExtractionAgent(
        target_university_th=target_uni_th,
        target_university_en=target_uni_en,
        target_faculty_th=target_fac_th,
        target_faculty_en=target_fac_en,
        db_session=db
    )

    html_content = f"<html><body><h1>รายนามคณาจารย์ประจำและที่ปรึกษา {target_fac_th}</h1><div>{text_chunk}</div></body></html>"
    patch = agent.step_with_html(html_content, current_url="https://academic.ac.th/faculty")
    print(f"Extracted {len(agent.state.faculties)} verified profiles for {target_fac_th}!")

    profiles_list = []
    for p in agent.state.faculties.values():
        if hasattr(p, "model_dump"):
            profiles_list.append(p.model_dump())
        elif isinstance(p, dict):
            profiles_list.append(p)
        else:
            profiles_list.append(dict(p))

    # Write python dataset
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(f'"""\nDeduplicated Academic Faculty Dataset ({out_file})\n"""\n\n')
        f.write(f"EXTRACTED_FACULTIES = {json.dumps(profiles_list, ensure_ascii=False, indent=2)}\n")

    print(f"Saved dataset to {out_file} successfully.")
    db.close()
    return len(profiles_list)

if __name__ == '__main__':
    # 1. Architecture & Fine Arts
    extract_domain(
        target_uni_th="มหาวิทยาลัยศิลปากร และ จุฬาลงกรณ์มหาวิทยาลัย",
        target_uni_en="Silpakorn University & Chulalongkorn University",
        target_fac_th="คณะสถาปัตยกรรมศาสตร์ และ คณะจิตรกรรมประติมากรรมและภาพพิมพ์",
        target_fac_en="Faculty of Architecture & Faculty of Fine Arts",
        queries=[
            'arch.chula.ac.th คณาจารย์',
            'arch.su.ac.th คณาจารย์ สถาปัตย์ ศิลปากร',
            'finearts.su.ac.th คณะจิตรกรรม ศิลปากร คณาจารย์',
            'finearts.cmu.ac.th คณะวิจิตรศิลป์ มหาวิทยาลัยเชียงใหม่ คณาจารย์',
            'arch.kmutnb.ac.th คณะสถาปัตยกรรมศาสตร์ คณาจารย์'
        ],
        raw_file='data/raw_creative_humanities_snippets.json',
        out_file='backend/scripts/data_sources/architecture_arts_ai_extracted.py'
    )

    # 2. Humanities, Social Sciences, Communication Arts & Psychology
    extract_domain(
        target_uni_th="จุฬาลงกรณ์มหาวิทยาลัย, มหาวิทยาลัยธรรมศาสตร์ และ มหาวิทยาลัยเชียงใหม่",
        target_uni_en="Chulalongkorn University, Thammasat University, Chiang Mai University",
        target_fac_th="คณะนิเทศศาสตร์, จิตวิทยา, มนุษยศาสตร์ และ สังคมศาสตร์",
        target_fac_en="Faculty of Communication Arts, Psychology, Humanities, Social Sciences",
        queries=[
            'psy.chula.ac.th คณะจิตวิทยา จุฬาฯ คณาจารย์',
            'soc.cmu.ac.th คณะสังคมศาสตร์ มหาวิทยาลัยเชียงใหม่ คณาจารย์',
            'commarts.chula.ac.th คณะนิเทศศาสตร์ จุฬาฯ คณาจารย์',
            'jc.tu.ac.th คณะวารสารศาสตร์ มหาวิทยาลัยธรรมศาสตร์ คณาจารย์',
            'human.cmu.ac.th คณะมนุษยศาสตร์ มหาวิทยาลัยเชียงใหม่ คณาจารย์'
        ],
        raw_file='data/raw_creative_humanities_snippets.json',
        out_file='backend/scripts/data_sources/humanities_social_ai_extracted.py'
    )

    # 3. Regional Research Centers (KKU, PSU, CMU, SUT)
    extract_domain(
        target_uni_th="มหาวิทยาลัยขอนแก่น, มหาวิทยาลัยสงขลานครินทร์, มหาวิทยาลัยเทคโนโลยีสุรนารี",
        target_uni_en="Khon Kaen University, Prince of Songkla University, Suranaree University of Technology",
        target_fac_th="คณะแพทยศาสตร์ และ สำนักวิชาวิทยาศาสตร์และวิศวกรรมศาสตร์",
        target_fac_en="Faculty of Medicine, Science, and Engineering",
        queries=[
            'md.kku.ac.th คณะแพทยศาสตร์ มหาวิทยาลัยขอนแก่น คณาจารย์',
            'med.psu.ac.th คณะแพทยศาสตร์ มหาวิทยาลัยสงขลานครินทร์ คณาจารย์',
            'med.cmu.ac.th คณะแพทยศาสตร์ มหาวิทยาลัยเชียงใหม่ คณาจารย์',
            'science.sut.ac.th สำนักวิชาวิทยาศาสตร์ มหาวิทยาลัยเทคโนโลยีสุรนารี คณาจารย์',
            'sci.psu.ac.th คณะวิทยาศาสตร์ มหาวิทยาลัยสงขลานครินทร์ คณาจารย์',
            'sci.kku.ac.th คณะวิทยาศาสตร์ มหาวิทยาลัยขอนแก่น คณาจารย์',
            'eng.psu.ac.th คณะวิศวกรรมศาสตร์ มหาวิทยาลัยสงขลานครินทร์ คณาจารย์',
            'en.kku.ac.th คณะวิศวกรรมศาสตร์ มหาวิทยาลัยขอนแก่น คณาจารย์'
        ],
        raw_file='data/raw_regional_excellence_snippets.json',
        out_file='backend/scripts/data_sources/regional_centers_ai_extracted.py'
    )
