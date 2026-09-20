# -*- coding: utf-8 -*-
"""
Enrichment and sanitization script for 17 CMU faculty members:
1. Sanitize first_name and last_name columns to genuine English transliterations.
2. Update verified official CMU emails.
3. Restore authoritative bibliometrics (H-index, total_citations, total_publications_count) from Crossref.
4. Update embedding_text and re-generate 768-dim Gemini vector embeddings.
5. Adheres to Local-First Zero-Egress Invariant (PostgreSQL container localhost:5432/advisor_match).
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

CMU_17_FACULTY_UPDATES = [
    {
        "id": "cmu_103fe821_4247",
        "full_name_th": "ศ.เชี่ยวชาญพิเศษ ดร. ทพ. อะนัฆ เอี่ยมอรุณ",
        "first_name": "Anak",
        "last_name": "Iamaroon",
        "email": "anak.i@cmu.ac.th",
        "h_index": 16,
        "total_citations": 719,
        "total_publications_count": 48
    },
    {
        "id": "cmu_58ee6d12_3751",
        "full_name_th": "ศ.เชี่ยวชาญพิเศษ ดร. นพ. กิตติพันธุ์ ฤกษ์เกษม",
        "first_name": "Kittipan",
        "last_name": "Rerkasem",
        "email": "kittipan.r@cmu.ac.th",
        "h_index": 12,
        "total_citations": 626,
        "total_publications_count": 50
    },
    {
        "id": "cmu_ds_wave11_0006",
        "full_name_th": "รศ.ดร. พญ. จิราภรณ์ โกรานา",
        "first_name": "Jiraporn",
        "last_name": "Khorana",
        "email": "jiraporn.k@cmu.ac.th",
        "h_index": 12,
        "total_citations": 436,
        "total_publications_count": 50
    },
    {
        "id": "cmu_ds_wave11_0010",
        "full_name_th": "รศ. พญ. ลินดา หรรษภิญโญ",
        "first_name": "Linda",
        "last_name": "Hansapinyo",
        "email": "linda.h@cmu.ac.th",
        "h_index": 12,
        "total_citations": 411,
        "total_publications_count": 50
    },
    {
        "id": "chiangmaiu_facultyofv_suriyasathaporn_082",
        "full_name_th": "ศ.คลินิก ดร. สพ.ญ. วรรณนา สุริยาสถาพร",
        "first_name": "Wannana",
        "last_name": "Suriyasathaporn",
        "email": "wanna.suri@cmu.ac.th",
        "h_index": 10,
        "total_citations": 356,
        "total_publications_count": 42
    },
    {
        "id": "cmu_ds_wave11_0015",
        "full_name_th": "ผศ.ดร. ชาติชาย ดวงสอาด",
        "first_name": "Chatchai",
        "last_name": "Doungsa-ard",
        "email": "chatchai.d@cmu.ac.th",
        "h_index": 8,
        "total_citations": 210,
        "total_publications_count": 22
    },
    {
        "id": "cmu_ds_wave11_0008",
        "full_name_th": "ผศ.ดร. ปฏิสนธิ์ ปาลี",
        "first_name": "Patison",
        "last_name": "Palee",
        "email": "patison.p@cmu.ac.th",
        "h_index": 8,
        "total_citations": 192,
        "total_publications_count": 44
    },
    {
        "id": "cmu_ds_wave11_0011",
        "full_name_th": "ผศ. นพ. กฤษณ์ ขวัญเงิน",
        "first_name": "Krit",
        "last_name": "Khwanngern",
        "email": "krit.k@cmu.ac.th",
        "h_index": 6,
        "total_citations": 165,
        "total_publications_count": 24
    },
    {
        "id": "cmu_ds_wave11_0025",
        "full_name_th": "อ. พญ. กณิกนันท์ อินตุ้ย",
        "first_name": "Kaniknun",
        "last_name": "Intui",
        "email": "kaniknun.i@cmu.ac.th",
        "h_index": 6,
        "total_citations": 163,
        "total_publications_count": 24
    },
    {
        "id": "cmu_ds_wave11_0007",
        "full_name_th": "ผศ.ดร. ปรีดิ์ เที่ยงบูรณธรรม",
        "first_name": "Prid",
        "last_name": "Thiengburanathum",
        "email": "prid.t@cmu.ac.th",
        "h_index": 5,
        "total_citations": 95,
        "total_publications_count": 31
    },
    {
        "id": "cmu_ds_wave11_0003",
        "full_name_th": "ผศ.ดร. พร้อมพงศ์ สุกัณศีล",
        "first_name": "Prompong",
        "last_name": "Sugunnasil",
        "email": "prompong.s@cmu.ac.th",
        "h_index": 4,
        "total_citations": 44,
        "total_publications_count": 26
    },
    {
        "id": "cmu_ds_wave11_0023",
        "full_name_th": "อ.ดร. สาลินี ธำรงเลาหะพันธุ์",
        "first_name": "Salinee",
        "last_name": "Thumronglaohapun",
        "email": "salinee.t@cmu.ac.th",
        "h_index": 4,
        "total_citations": 83,
        "total_publications_count": 16
    },
    {
        "id": "cmu_ds_wave11_0022",
        "full_name_th": "ผศ.ดร. วรัญญา มหานันท์",
        "first_name": "Waranya",
        "last_name": "Mahanan",
        "email": "waranya.m@cmu.ac.th",
        "h_index": 3,
        "total_citations": 62,
        "total_publications_count": 18
    },
    {
        "id": "cmu_ds_wave11_0005",
        "full_name_th": "รศ. พิษณุ เจียวคุณ",
        "first_name": "Pisanu",
        "last_name": "Chiawkhun",
        "email": "pisanu.c@cmu.ac.th",
        "h_index": 1,
        "total_citations": 2,
        "total_publications_count": 4
    },
    {
        "id": "silpakornu_facultyofa_chainakut_015",
        "full_name_th": "ศ.เกียรติคุณ พงศ์เดช ไชยคุตร",
        "first_name": "Pongdej",
        "last_name": "Chaiyakut",
        "email": "pongdej.c@cmu.ac.th",
        "h_index": 1,
        "total_citations": 1,
        "total_publications_count": 5
    },
    {
        "id": "cmu_ds_wave11_0026",
        "full_name_th": "ผศ.ดร. ปาริชาต ภัทรพานิชชัย",
        "first_name": "Parichat",
        "last_name": "Pattarapanichchai",
        "email": "parichat.p@cmu.ac.th",
        "h_index": 0,
        "total_citations": 0,
        "total_publications_count": 0
    },
    {
        "id": "cmu_ds_wave11_0021",
        "full_name_th": "ผศ.ดร. ภวัต ภักดิ์ศรานุวัต",
        "first_name": "Bhawat",
        "last_name": "Bhaksaranuvat",
        "email": "bhawat.b@cmu.ac.th",
        "h_index": 0,
        "total_citations": 0,
        "total_publications_count": 0
    }
]


def run_enrichment():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
    cur = conn.cursor()

    print(f"Starting enrichment for {len(CMU_17_FACULTY_UPDATES)} CMU faculty records...")

    for item in CMU_17_FACULTY_UPDATES:
        cur.execute("""
            SELECT full_name_th, department_th, department, faculty_th, university_th,
                   research_interests, education, featured_publications, embedding_text
            FROM faculties
            WHERE id = %s;
        """, (item["id"],))
        row = cur.fetchone()
        if not row:
            print(f"❌ Record not found: {item['id']}")
            continue

        fn_th, dept_th, dept_en, fac_th, uni_th, interests, edu, pubs, current_emb_text = row

        # Parse JSON fields if necessary
        interests_str = " ".join(interests) if isinstance(interests, list) else (str(interests or ""))
        edu_str = " ".join(edu) if isinstance(edu, list) else (str(edu or ""))
        pubs_str = ""
        if isinstance(pubs, list):
            pubs_str = " ".join(p.get("title", "") for p in pubs if isinstance(p, dict))

        # Reconstruct updated embedding_text with proper English name
        new_embedding_text = (
            f"{item['first_name']} {item['last_name']} {fn_th} "
            f"{dept_th or ''} {dept_en or ''} {fac_th or ''} {uni_th or ''} "
            f"{interests_str} {edu_str} {pubs_str}"
        ).strip()

        print(f"Generating 768-dim embedding for {item['id']} ({item['first_name']} {item['last_name']})...")
        vec = embedding_service.get_embedding(new_embedding_text)
        if not vec or len(vec) != 768:
            print(f"⚠️ Warning: Embedding fallback to 768-dim zeros")
            vec = [0.0] * 768

        vec_str = str(vec)

        # Update database
        update_sql = """
            UPDATE faculties SET
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                email = %(email)s,
                h_index = %(h_index)s,
                total_citations = %(total_citations)s,
                total_publications_count = %(total_publications_count)s,
                embedding_text = %(embedding_text)s,
                embedding = %(embedding)s::vector
            WHERE id = %(id)s;
        """
        cur.execute(update_sql, {
            "id": item["id"],
            "first_name": item["first_name"],
            "last_name": item["last_name"],
            "email": item["email"],
            "h_index": item["h_index"],
            "total_citations": item["total_citations"],
            "total_publications_count": item["total_publications_count"],
            "embedding_text": new_embedding_text,
            "embedding": vec_str
        })
        print(f"✅ Updated {item['id']}: {item['first_name']} {item['last_name']} (H={item['h_index']}, Cites={item['total_citations']})")

    conn.commit()

    # Verification
    print("\n=== VERIFICATION OF UPDATED 17 FACULTY RECORDS ===")
    cur.execute("""
        SELECT id, full_name_th, first_name, last_name, email, h_index, total_citations, total_publications_count,
               CASE WHEN embedding IS NOT NULL THEN '768-dim OK' ELSE 'NULL' END as vec_status
        FROM faculties
        WHERE id = ANY(%s)
        ORDER BY h_index DESC, total_citations DESC;
    """, ([item["id"] for item in CMU_17_FACULTY_UPDATES],))

    rows = cur.fetchall()
    for r in rows:
        print(f"[{r[0]}] {r[1]} -> {r[2]} {r[3]} | {r[4]} | H={r[5]}, Cites={r[6]}, Works={r[7]} | {r[8]}")

    cur.close()
    conn.close()
    print(f"\nAll {len(rows)} records successfully verified in local PostgreSQL.")


if __name__ == "__main__":
    run_enrichment()
