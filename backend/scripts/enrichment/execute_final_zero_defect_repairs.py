# -*- coding: utf-8 -*-
"""
Comprehensive Final Zero-Defect Database Repairs & Alignment:
1. Purge 42 demonstration school pupils (เด็กหญิง, เด็กชาย) from โรงเรียนสาธิตมหาวิทยาลัยทักษิณ.
2. Null out 13 wildcard freemails (@yahoo.*, @hotmail.*, @gmail.con, @icloud.*).
3. Set canonical English university name ('Chiang Mai University') on 15 CMU discovery records.
4. Set scholar_url = None for cmu_eng_civil_tantrapongsatorn_011 (empty string).
5. Restore full_name_th = 'อ.ดร. ดิเรก นวลสิงห์' on tu_eng_wave16_0018.
6. Unmerge and restore the 7 false-positive donor records from Pass 3:
   - cu_sci_wave14_b_0025 (ศ.ดร. Nattapong Paiboonvorachat, Chula Science)
   - tsu_w50_0015_950 (อ. เสาวลักษณ์ หนูสุวรรณ, Thaksin)
   - buu_w42_0402_251 (ดร. Liudmila Yarovaya, Burapha)
   - regionalun_facultymem_fac_050_050 (ผศ.ดร. วชิราภรณ์ พลวัต, Walailak)
   - wave23_0208_877 (รศ.ดร. เกรียงศักดิ์ บุญเที่ยง, MSU)
   - cmu-arch-009_43a34d (ผศ.ดร. อภิชาติ ธีระวุฒิ, CMU)
   - nu_agr_kumrop_001 (รศ.ดร. คำรพ รักษาศาสตร์, Naresuan)
7. Save full snapshots and checkpoints to backend/data/agent_states/.
"""
import os
import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy.orm import defer

def build_faculty_embedding_text(f: FacultyDB) -> str:
    parts = []
    if f.full_name_th:
        parts.append(f.full_name_th)
    en_name = f"{f.first_name or ''} {f.last_name or ''}".strip()
    if en_name:
        parts.append(en_name)
    if f.university_th:
        parts.append(f.university_th)
    if f.faculty_th:
        parts.append(f.faculty_th)
    if f.department_th:
        parts.append(f.department_th)
    if f.research_interests:
        interests = " ".join(f.research_interests) if isinstance(f.research_interests, list) else str(f.research_interests)
        parts.append(interests)
    if f.featured_publications and isinstance(f.featured_publications, list):
        pub_titles = [p.get("title", "") for p in f.featured_publications if isinstance(p, dict) and p.get("title")]
        if pub_titles:
            parts.append(" ".join(pub_titles[:5]))
    return " | ".join([p for p in parts if p.strip()])

def main():
    db = SessionLocal()

    # ---------------------------------------------------------
    # 1. Purge 42 Demonstration School Pupils
    # ---------------------------------------------------------
    pupils = db.query(FacultyDB).filter(
        (FacultyDB.full_name_th.like('%เด็กหญิง%')) |
        (FacultyDB.full_name_th.like('%เด็กชาย%')) |
        (FacultyDB.full_name_th.like('%ด.ญ.%')) |
        (FacultyDB.full_name_th.like('%ด.ช.%'))
    ).all()

    pupils_snapshot = []
    pupil_ids = []
    for p in pupils:
        pupil_ids.append(p.id)
        pupils_snapshot.append({
            "id": p.id,
            "full_name_th": p.full_name_th,
            "university_th": p.university_th,
            "faculty_th": p.faculty_th,
            "email": p.email
        })
        # Check research labs
        db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == p.id).update(
            {ResearchLabDB.lead_advisor_id: None}, synchronize_session=False
        )
        db.delete(p)

    print(f"1. Purged {len(pupils_snapshot)} demonstration school pupils.")
    snap_p = os.path.join(BACKEND_DIR, "data", "agent_states", "purge_school_pupils_checkpoint.json")
    with open(snap_p, "w", encoding="utf-8") as out:
        json.dump(pupils_snapshot, out, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------
    # 2. Null out 13 wildcard freemails
    # ---------------------------------------------------------
    freemail_patterns = ['%@yahoo.%', '%@hotmail.%', '%@gmail.con%', '%@icloud.%']
    freemail_facs = []
    for pat in freemail_patterns:
        facs = db.query(FacultyDB).filter(FacultyDB.email.ilike(pat)).all()
        for f in facs:
            if f.id not in pupil_ids and f not in freemail_facs:
                freemail_facs.append(f)

    freemail_snapshot = []
    for f in freemail_facs:
        freemail_snapshot.append({
            "id": f.id,
            "full_name_th": f.full_name_th,
            "old_email": f.email
        })
        f.email = None
        f.embedding_text = build_faculty_embedding_text(f)

    print(f"2. Nulled {len(freemail_snapshot)} remaining wildcard freemails.")
    snap_fm = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_wildcard_freemails_checkpoint.json")
    with open(snap_fm, "w", encoding="utf-8") as out:
        json.dump(freemail_snapshot, out, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------
    # 3. Canonical English university on 15 CMU discovery records
    # ---------------------------------------------------------
    cmu_disc = db.query(FacultyDB).filter(
        FacultyDB.university_th == 'มหาวิทยาลัยเชียงใหม่',
        FacultyDB.university.is_(None)
    ).all()
    for f in cmu_disc:
        f.university = 'Chiang Mai University'
    print(f"3. Set university = 'Chiang Mai University' on {len(cmu_disc)} records.")

    # ---------------------------------------------------------
    # 4. Fix scholar_url for cmu_eng_civil_tantrapongsatorn_011
    # ---------------------------------------------------------
    cmu_civ = db.query(FacultyDB).filter(FacultyDB.id == 'cmu_eng_civil_tantrapongsatorn_011').first()
    if cmu_civ and cmu_civ.scholar_url == '':
        cmu_civ.scholar_url = None
        print("4. Set scholar_url = None on cmu_eng_civil_tantrapongsatorn_011.")

    # ---------------------------------------------------------
    # 5. Restore full_name_th on tu_eng_wave16_0018
    # ---------------------------------------------------------
    tu_f = db.query(FacultyDB).filter(FacultyDB.id == 'tu_eng_wave16_0018').first()
    if tu_f:
        tu_f.full_name_th = 'อ.ดร. ดิเรก นวลสิงห์'
        tu_f.first_name = 'Direk'
        tu_f.last_name = 'Nuansing'
        tu_f.academic_title_th = 'อ.ดร.'
        tu_f.embedding_text = build_faculty_embedding_text(tu_f)
        print("5. Restored full_name_th on tu_eng_wave16_0018.")

    # ---------------------------------------------------------
    # 6. Unmerge and restore the 7 false-positive Pass 3 donors
    # ---------------------------------------------------------
    # Donor 1: cu_sci_wave14_b_0025 (Chula Science - Chemistry)
    d1 = db.query(FacultyDB).filter(FacultyDB.id == 'cu_sci_wave14_b_0025').first()
    if not d1:
        d1 = FacultyDB(
            id='cu_sci_wave14_b_0025',
            full_name_th='ศ.ดร. Nattapong Paiboonvorachat',
            first_name='Nattapong',
            last_name='Paiboonvorachat',
            academic_title_th='ศ.ดร.',
            university_th='จุฬาลงกรณ์มหาวิทยาลัย',
            university='Chulalongkorn University',
            faculty_th='คณะวิทยาศาสตร์',
            department_th='ภาควิชาเคมี',
            email='nattapong.p@chula.ac.th',
            profile_url='https://chem.sc.chula.ac.th/nattapong-paiboonvorachat/',
            openalex_id='https://openalex.org/A5002897546',
            total_citations=54,
            h_index=2,
            total_publications_count=3,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d1.embedding_text = build_faculty_embedding_text(d1)
        db.add(d1)
        print("6.1 Restored cu_sci_wave14_b_0025.")

    # Restore primary econ-cu-007_87289a metrics
    p1 = db.query(FacultyDB).filter(FacultyDB.id == 'econ-cu-007_87289a').first()
    if p1:
        p1.total_citations = 510
        p1.h_index = 13
        p1.total_publications_count = 80
        p1.embedding_text = build_faculty_embedding_text(p1)

    # Donor 2: tsu_w50_0015_950 (Thaksin - Economics & Business Administration)
    d2 = db.query(FacultyDB).filter(FacultyDB.id == 'tsu_w50_0015_950').first()
    if not d2:
        d2 = FacultyDB(
            id='tsu_w50_0015_950',
            full_name_th='อ. เสาวลักษณ์ หนูสุวรรณ',
            first_name=None,
            last_name=None,
            academic_title_th='อ.',
            university_th='มหาวิทยาลัยทักษิณ',
            university='Thaksin University',
            faculty_th='คณะเศรษฐศาสตร์และบริหารธุรกิจ',
            department_th='คณะเศรษฐศาสตร์และบริหารธุรกิจ',
            email=None,
            openalex_id=None,
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d2.embedding_text = build_faculty_embedding_text(d2)
        db.add(d2)
        print("6.2 Restored tsu_w50_0015_950.")

    # Donor 3: buu_w42_0402_251 (Burapha - Pharmacy)
    d3 = db.query(FacultyDB).filter(FacultyDB.id == 'buu_w42_0402_251').first()
    if not d3:
        d3 = FacultyDB(
            id='buu_w42_0402_251',
            full_name_th='ดร. Liudmila Yarovaya',
            first_name='Liudmila',
            last_name='Yarovaya',
            academic_title_th='ดร.',
            university_th='มหาวิทยาลัยบูรพา',
            university='Burapha University',
            faculty_th='คณะเภสัชศาสตร์',
            department_th='สาขาวิชาวิทยาศาสตร์และเทคโนโลยีเครื่องสำอาง',
            email='liudmila.ya@go.buu.ac.th',
            openalex_id=None,
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d3.embedding_text = build_faculty_embedding_text(d3)
        db.add(d3)
        # Clear email from wave21_0062_518 (ดร. ภญ. จิณห์นิภา ประจวบพงศ์)
        p3 = db.query(FacultyDB).filter(FacultyDB.id == 'wave21_0062_518').first()
        if p3:
            p3.email = None
            p3.embedding_text = build_faculty_embedding_text(p3)
        print("6.3 Restored buu_w42_0402_251.")

    # Donor 4: regionalun_facultymem_fac_050_050 (Walailak - Law)
    d4 = db.query(FacultyDB).filter(FacultyDB.id == 'regionalun_facultymem_fac_050_050').first()
    if not d4:
        d4 = FacultyDB(
            id='regionalun_facultymem_fac_050_050',
            full_name_th='ผศ.ดร. วชิราภรณ์ พลวัต',
            first_name=None,
            last_name=None,
            academic_title_th='ผศ.ดร.',
            university_th='มหาวิทยาลัยวลัยลักษณ์',
            university='Walailak University',
            faculty_th='สำนักวิชานิติศาสตร์',
            department_th='สำนักวิชานิติศาสตร์',
            email=None,
            openalex_id='not_indexed',
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d4.embedding_text = build_faculty_embedding_text(d4)
        db.add(d4)
        print("6.4 Restored regionalun_facultymem_fac_050_050.")

    # Donor 5: wave23_0208_877 (MSU - Technology, Agriculture)
    d5 = db.query(FacultyDB).filter(FacultyDB.id == 'wave23_0208_877').first()
    if not d5:
        d5 = FacultyDB(
            id='wave23_0208_877',
            full_name_th='รศ.ดร. เกรียงศักดิ์ บุญเที่ยง',
            first_name=None,
            last_name=None,
            academic_title_th='รศ.ดร.',
            university_th='มหาวิทยาลัยมหาสารคาม',
            university='Mahasarakham University',
            faculty_th='คณะเทคโนโลยี',
            department_th='สาขาเกษตรศาสตร์',
            email=None,
            openalex_id='not_indexed',
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d5.embedding_text = build_faculty_embedding_text(d5)
        db.add(d5)
        print("6.5 Restored wave23_0208_877.")

    # Donor 6: cmu-arch-009_43a34d (CMU - Architecture)
    d6 = db.query(FacultyDB).filter(FacultyDB.id == 'cmu-arch-009_43a34d').first()
    if not d6:
        d6 = FacultyDB(
            id='cmu-arch-009_43a34d',
            full_name_th='ผศ.ดร. อภิชาติ ธีระวุฒิ',
            first_name=None,
            last_name=None,
            academic_title_th='ผศ.ดร.',
            university_th='มหาวิทยาลัยเชียงใหม่',
            university='Chiang Mai University',
            faculty_th='คณะสถาปัตยกรรมศาสตร์',
            department_th='ภาควิชาสถาปัตยกรรมศาสตร์',
            email=None,
            openalex_id='not_indexed',
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d6.embedding_text = build_faculty_embedding_text(d6)
        db.add(d6)
        print("6.6 Restored cmu-arch-009_43a34d.")

    # Donor 7: nu_agr_kumrop_001 (Naresuan - Agriculture)
    d7 = db.query(FacultyDB).filter(FacultyDB.id == 'nu_agr_kumrop_001').first()
    if not d7:
        d7 = FacultyDB(
            id='nu_agr_kumrop_001',
            full_name_th='รศ.ดร. คำรพ รักษาศาสตร์',
            first_name=None,
            last_name=None,
            academic_title_th='รศ.ดร.',
            university_th='มหาวิทยาลัยนเรศวร',
            university='Naresuan University',
            faculty_th='คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม',
            department_th='ภาควิชาวิทยาศาสตร์การเกษตร',
            email=None,
            openalex_id='not_indexed',
            total_citations=0,
            h_index=0,
            total_publications_count=0,
            first_author_count=0,
            co_author_count=0,
            research_interests=[],
            featured_publications=[]
        )
        d7.embedding_text = build_faculty_embedding_text(d7)
        db.add(d7)
        print("6.7 Restored nu_agr_kumrop_001.")

    snap_unmerge = os.path.join(BACKEND_DIR, "data", "agent_states", "pass3_unmerge_false_positives_snapshot.json")
    with open(snap_unmerge, "w", encoding="utf-8") as out:
        json.dump({
            "unmerged_ids": [
                'cu_sci_wave14_b_0025',
                'tsu_w50_0015_950',
                'buu_w42_0402_251',
                'regionalun_facultymem_fac_050_050',
                'wave23_0208_877',
                'cmu-arch-009_43a34d',
                'nu_agr_kumrop_001'
            ]
        }, out, indent=2)

    db.commit()
    db.close()
    print("\nAll zero-defect repairs committed and checkpointed successfully.")

if __name__ == "__main__":
    main()
