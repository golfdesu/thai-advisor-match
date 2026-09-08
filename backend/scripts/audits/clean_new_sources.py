# -*- coding: utf-8 -*-
"""
Clean and disambiguate faculty profiles in new batches to guarantee single university and single faculty.
"""
import os, sys, re, json

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    mod = {}
    exec(content, mod)
    data = mod.get('EXTRACTED_FACULTIES', [])
    print(f"Cleaning {filepath}: {len(data)} profiles")

    for p in data:
        email = (p.get('email') or '').lower()
        dep = p.get('department_th') or ''
        fac = p.get('faculty_th') or ''
        name = p.get('full_name_th') or ''
        pubs = p.get('featured_publications', [])
        pub_titles = [x.get('title', '') if isinstance(x, dict) else str(x) for x in pubs]
        bio = ' '.join(p.get('research_interests', [])) + ' ' + ' '.join(pub_titles)
        full_context = f"{email} {dep} {fac} {name} {bio}".lower()

        # 1. Precise University Disambiguation
        if 'chula.ac.th' in full_context or 'จุฬา' in full_context:
            p['university_th'] = 'จุฬาลงกรณ์มหาวิทยาลัย'
            p['university'] = 'Chulalongkorn University'
        elif 'su.ac.th' in full_context or 'ศิลปากร' in full_context:
            p['university_th'] = 'มหาวิทยาลัยศิลปากร'
            p['university'] = 'Silpakorn University'
        elif 'cmu.ac.th' in full_context or 'เชียงใหม่' in full_context or 'วิจิตรศิลป์' in full_context:
            p['university_th'] = 'มหาวิทยาลัยเชียงใหม่'
            p['university'] = 'Chiang Mai University'
        elif 'kmutnb.ac.th' in full_context or 'พระจอมเกล้าพระนครเหนือ' in full_context:
            p['university_th'] = 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ'
            p['university'] = 'King Mongkut\'s University of Technology North Bangkok'
        elif 'tu.ac.th' in full_context or 'ธรรมศาสตร์' in full_context or 'วารสารศาสตร์' in full_context:
            p['university_th'] = 'มหาวิทยาลัยธรรมศาสตร์'
            p['university'] = 'Thammasat University'
        elif 'kku.ac.th' in full_context or 'ขอนแก่น' in full_context or 'ศรีนครินทร์' in full_context:
            p['university_th'] = 'มหาวิทยาลัยขอนแก่น'
            p['university'] = 'Khon Kaen University'
        elif 'psu.ac.th' in full_context or 'สงขลานครินทร์' in full_context:
            p['university_th'] = 'มหาวิทยาลัยสงขลานครินทร์'
            p['university'] = 'Prince of Songkla University'
        elif 'sut.ac.th' in full_context or 'สุรนารี' in full_context:
            p['university_th'] = 'มหาวิทยาลัยเทคโนโลยีสุรนารี'
            p['university'] = 'Suranaree University of Technology'
        else:
            # Fallback based on filename
            if 'architecture' in filepath:
                p['university_th'] = 'จุฬาลงกรณ์มหาวิทยาลัย'
                p['university'] = 'Chulalongkorn University'
            elif 'humanities' in filepath:
                p['university_th'] = 'จุฬาลงกรณ์มหาวิทยาลัย'
                p['university'] = 'Chulalongkorn University'
            elif 'regional' in filepath:
                p['university_th'] = 'มหาวิทยาลัยขอนแก่น'
                p['university'] = 'Khon Kaen University'

        # 2. Precise Faculty Disambiguation
        if 'สถาปัตย' in full_context or 'สถาปัตย์' in full_context or 'ภูมิสถาปัตย์' in full_context:
            p['faculty_th'] = 'คณะสถาปัตยกรรมศาสตร์'
            p['faculty'] = 'Faculty of Architecture'
        elif 'จิตรกรรม' in full_context or 'วิจิตรศิลป์' in full_context or 'ประติมากรรม' in full_context or 'ศิลปกรรม' in full_context:
            p['faculty_th'] = 'คณะจิตรกรรม ประติมากรรมและภาพพิมพ์'
            p['faculty'] = 'Faculty of Painting, Sculpture and Graphic Arts'
        elif 'จิตวิทยา' in full_context:
            p['faculty_th'] = 'คณะจิตวิทยา'
            p['faculty'] = 'Faculty of Psychology'
        elif 'นิเทศ' in full_context:
            p['faculty_th'] = 'คณะนิเทศศาสตร์'
            p['faculty'] = 'Faculty of Communication Arts'
        elif 'วารสาร' in full_context:
            p['faculty_th'] = 'คณะวารสารศาสตร์และสื่อสารมวลชน'
            p['faculty'] = 'Faculty of Journalism and Mass Communication'
        elif 'สังคมศาสตร์' in full_context:
            p['faculty_th'] = 'คณะสังคมศาสตร์'
            p['faculty'] = 'Faculty of Social Sciences'
        elif 'มนุษยศาสตร์' in full_context or 'อักษรศาสตร์' in full_context:
            p['faculty_th'] = 'คณะมนุษยศาสตร์'
            p['faculty'] = 'Faculty of Humanities'
        elif 'แพทย์' in full_context or 'แพทยศาสตร์' in full_context or 'กายวิภาคศาสตร์' in full_context or 'สรีรวิทยา' in full_context:
            p['faculty_th'] = 'คณะแพทยศาสตร์'
            p['faculty'] = 'Faculty of Medicine'
        elif 'วิทยาศาสตร์' in full_context:
            p['faculty_th'] = 'คณะวิทยาศาสตร์'
            p['faculty'] = 'Faculty of Science'
        elif 'วิศวกรรมศาสตร์' in full_context or 'วิศว' in full_context:
            p['faculty_th'] = 'คณะวิศวกรรมศาสตร์'
            p['faculty'] = 'Faculty of Engineering'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(f'"""\nCleaned & Disambiguated Academic Faculty Dataset ({filepath})\n"""\n\n')
        f.write(f"EXTRACTED_FACULTIES = {json.dumps(data, ensure_ascii=False, indent=2)}\n")

    print(f"Saved cleaned {filepath} successfully.")

if __name__ == '__main__':
    for p in [
        'backend/scripts/data_sources/architecture_arts_ai_extracted.py',
        'backend/scripts/data_sources/humanities_social_ai_extracted.py',
        'backend/scripts/data_sources/regional_centers_ai_extracted.py'
    ]:
        clean_file(p)
