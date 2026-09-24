# -*- coding: utf-8 -*-
"""
Ingestion script for newly discovered / recovered faculty members in CMU Engineering:
1. Dr. Warakorn Tantrapongsatorn (อ.ดร. วรากร ตันตระพงศธร) - Civil Engineering (Structural)
2. Assoc. Prof. Dr. Sakgasit Ramingwong (รศ.ดร. ศักดิ์กษิต ระมิงค์วงศ์) - Computer Engineering

Generates 768-dimensional Gemini embeddings and inserts/upserts into local PostgreSQL container
(localhost:5432/advisor_match) - Zero Egress Invariant.
"""
import sys
import json
from pathlib import Path
import psycopg2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app.core.embedding_service import embedding_service

RECOVERED_FACULTIES = [
    {
        "id": "cmu_eng_civil_tantrapongsatorn_011",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา (สาขาวิชาวิศวกรรมโครงสร้าง)",
        "academic_title_th": "อ.ดร.",
        "first_name": "Warakorn",
        "last_name": "Tantrapongsatorn",
        "full_name_th": "อ.ดร. วรากร ตันตระพงศธร",
        "role": "อาจารย์ประจำ",
        "email": "warakorn.tan@cmu.ac.th",
        "image_url": "",
        "profile_url": "https://civil.eng.cmu.ac.th/?page_id=1096",
        "education": [
            "Ph.D. in Civil Engineering, Chiang Mai University",
            "M.Eng. in Civil Engineering (Structure), Sirindhorn International Institute of Technology, Thammasat University",
            "B.Eng. (Honors) in Civil Engineering, Chiang Mai University"
        ],
        "research_interests": [
            "Structural Engineering",
            "Civil Engineering",
            "Reinforced Concrete Members",
            "Impact Load and Response",
            "Finite Element Analysis",
            "Precast Concrete"
        ],
        "taught_courses": [
            "Structural Analysis",
            "Reinforced Concrete Design",
            "Advanced Concrete Technology"
        ],
        "featured_publications": [
            {"title": "FLEXURAL REINFORCED CONCRETE MEMBERS WITH MINIMUM REINFORCEMENT UNDER LOW-VELOCITY IMPACT LOAD (2018)", "citations": 10},
            {"title": "Impact Response of Reinforced Concrete Columns with Different Axial Load under Low-Velocity Impact Loading (2019)", "citations": 4},
            {"title": "Nonlinear Response of RC Columns Subjected to Equal Energy-Double Impact Loads (2022)", "citations": 2},
            {"title": "Investigation of Optimal Ratios of EPS Foam Waste and Solvents as Alternative Green Polymer-Based Additives for Enhancing Cement Properties (2025)", "citations": 1},
            {"title": "Enhancing Shear Connectors Behavior of Precast Concrete Walls with Embedded Shear Keys (2025)", "citations": 0}
        ],
        "scholar_url": "",
        "total_publications_count": 7,
        "first_author_count": 5,
        "co_author_count": 2,
        "total_citations": 17,
        "h_index": 2,
        "openalex_id": None
    },
    {
        "id": "cmu_eng_cpe_sakgasit_025",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sakgasit",
        "last_name": "Ramingwong",
        "full_name_th": "รศ.ดร. ศักดิ์กษิต ระมิงค์วงศ์",
        "role": "อาจารย์ประจำ",
        "email": "sakgasit@eng.cmu.ac.th",
        "image_url": "",
        "profile_url": "https://cpe.eng.cmu.ac.th/lecturer-viewenglish.php?view_id=Sakgasit",
        "education": [
            "(Ph.D.) School of Science and Technology, University of New England, Australia",
            "(M.Sc. in Information Technology for Manufacture) Warwick Manufacturing Group, University of Warwick, United Kingdom",
            "(B.Eng. in Computer Engineering) Faculty of Engineering, Chiang Mai University, Thailand"
        ],
        "research_interests": [
            "Software project management",
            "Software risk management",
            "Software process improvement",
            "Global system development",
            "Game-based learning",
            "Quality management",
            "Agile Software Development",
            "Cloud Computing"
        ],
        "taught_courses": [
            "Software Engineering",
            "Software Project Management",
            "Object-Oriented Programming",
            "Information Systems"
        ],
        "featured_publications": [
            {"title": "Offshore outsourcing (2007)", "citations": 36},
            {"title": "A Framework for Designing Usability: Usability Redesign of a Mobile Government Application (2022)", "citations": 19},
            {"title": "Fundamental analysis and technical analysis integrated system for stock filtration (2016)", "citations": 16},
            {"title": "Top twenty risks in software projects: A content analysis and Delphi study (2014)", "citations": 9},
            {"title": "Implementing a Personal Software Process (PSPSM) Course: A Case Study (2012)", "citations": 6}
        ],
        "scholar_url": "https://www.scopus.com/authid/detail.uri?authorId=18038191700",
        "total_publications_count": 50,
        "first_author_count": 24,
        "co_author_count": 26,
        "total_citations": 176,
        "h_index": 6,
        "openalex_id": None
    }
]


def ingest_faculty():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
    cur = conn.cursor()

    for fac in RECOVERED_FACULTIES:
        print(f"\nProcessing {fac['full_name_th']} ({fac['first_name']} {fac['last_name']})...")

        # Construct comprehensive embedding text
        pub_titles = " ".join(p["title"] for p in fac["featured_publications"])
        interests = " ".join(fac["research_interests"])
        edu = " ".join(fac["education"])
        embedding_text = (
            f"{fac['first_name']} {fac['last_name']} {fac['full_name_th']} "
            f"{fac['department_th']} {fac['department']} {fac['faculty_th']} {fac['university_th']} "
            f"{interests} {edu} {pub_titles}"
        )

        print(f"Generating 768-dim embedding for {fac['first_name']}...")
        vec = embedding_service.get_embedding(embedding_text)
        if not vec or len(vec) != 768:
            print(f"⚠️ Warning: Embedding generation returned {len(vec) if vec else 0} dimensions. Trying fallback...")
            vec = None  # NULL: re-embed via embed_missing.py

        vec_str = str(vec)

        upsert_sql = """
            INSERT INTO faculties (
                id, university, university_th, faculty, faculty_th,
                department, department_th, academic_title_th, first_name, last_name,
                full_name_th, role, email, image_url, profile_url,
                education, research_interests, taught_courses, featured_publications,
                scholar_url, embedding_text, embedding, total_publications_count,
                first_author_count, co_author_count, total_citations, h_index, openalex_id
            ) VALUES (
                %(id)s, %(university)s, %(university_th)s, %(faculty)s, %(faculty_th)s,
                %(department)s, %(department_th)s, %(academic_title_th)s, %(first_name)s, %(last_name)s,
                %(full_name_th)s, %(role)s, %(email)s, %(image_url)s, %(profile_url)s,
                %(education)s, %(research_interests)s, %(taught_courses)s, %(featured_publications)s,
                %(scholar_url)s, %(embedding_text)s, %(embedding)s::vector, %(total_publications_count)s,
                %(first_author_count)s, %(co_author_count)s, %(total_citations)s, %(h_index)s, %(openalex_id)s
            )
            ON CONFLICT (id) DO UPDATE SET
                university = EXCLUDED.university,
                university_th = EXCLUDED.university_th,
                faculty = EXCLUDED.faculty,
                faculty_th = EXCLUDED.faculty_th,
                department = EXCLUDED.department,
                department_th = EXCLUDED.department_th,
                academic_title_th = EXCLUDED.academic_title_th,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                full_name_th = EXCLUDED.full_name_th,
                role = EXCLUDED.role,
                email = EXCLUDED.email,
                profile_url = EXCLUDED.profile_url,
                education = EXCLUDED.education,
                research_interests = EXCLUDED.research_interests,
                taught_courses = EXCLUDED.taught_courses,
                featured_publications = EXCLUDED.featured_publications,
                scholar_url = EXCLUDED.scholar_url,
                embedding_text = EXCLUDED.embedding_text,
                embedding = EXCLUDED.embedding,
                total_publications_count = EXCLUDED.total_publications_count,
                first_author_count = EXCLUDED.first_author_count,
                co_author_count = EXCLUDED.co_author_count,
                total_citations = EXCLUDED.total_citations,
                h_index = EXCLUDED.h_index,
                openalex_id = EXCLUDED.openalex_id;
        """

        params = {
            "id": fac["id"],
            "university": fac["university"],
            "university_th": fac["university_th"],
            "faculty": fac["faculty"],
            "faculty_th": fac["faculty_th"],
            "department": fac["department"],
            "department_th": fac["department_th"],
            "academic_title_th": fac["academic_title_th"],
            "first_name": fac["first_name"],
            "last_name": fac["last_name"],
            "full_name_th": fac["full_name_th"],
            "role": fac["role"],
            "email": fac["email"],
            "image_url": fac["image_url"],
            "profile_url": fac["profile_url"],
            "education": json.dumps(fac["education"], ensure_ascii=False),
            "research_interests": json.dumps(fac["research_interests"], ensure_ascii=False),
            "taught_courses": json.dumps(fac["taught_courses"], ensure_ascii=False),
            "featured_publications": json.dumps(fac["featured_publications"], ensure_ascii=False),
            "scholar_url": fac["scholar_url"],
            "embedding_text": embedding_text,
            "embedding": vec_str,
            "total_publications_count": fac["total_publications_count"],
            "first_author_count": fac["first_author_count"],
            "co_author_count": fac["co_author_count"],
            "total_citations": fac["total_citations"],
            "h_index": fac["h_index"],
            "openalex_id": fac["openalex_id"]
        }

        cur.execute(upsert_sql, params)
        print(f"✅ Upserted {fac['id']} successfully!")

    conn.commit()

    # Verification query
    print("\n=== Verification Query (Local DB) ===")
    cur.execute("""
        SELECT id, full_name_th, first_name, last_name, email, department_th, h_index, total_citations,
               CASE WHEN embedding IS NOT NULL THEN '768-dim OK' ELSE 'NULL' END AS vector_status
        FROM faculties
        WHERE id IN ('cmu_eng_civil_tantrapongsatorn_011', 'cmu_eng_cpe_sakgasit_025')
        ORDER BY id;
    """)
    for r in cur.fetchall():
        print(f"[{r[0]}] {r[1]} -> {r[2]} {r[3]} | {r[4]} | {r[5]} | H={r[6]}, Cites={r[7]} | Vector: {r[8]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    ingest_faculty()
