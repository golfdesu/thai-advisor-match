# -*- coding: utf-8 -*-
"""
Enrichment script for Faculty of Engineering, Chiang Mai University.
Fixes corrupted English/Thai names, restores official emails from SKILL.state,
and links verified authoritative OpenAlex author IDs and bibliometrics.
Target: Local PostgreSQL container (localhost:5432/advisor_match) - Zero Egress.
"""
import sys
import os
import psycopg2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UPDATES = [
    # 1. Environmental Engineering
    {
        "id": "cmu_eng_department__120",
        "first_name": "Saoharit", "last_name": "Nitayavardhana",
        "email": "saoharit@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5053086076",
        "h_index": 13, "total_citations": 831, "total_publications_count": 36
    },
    {
        "id": "cmu_eng_department__121",
        "first_name": "Patiroop", "last_name": "Pholchan",
        "email": "patiroop@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5046473499",
        "h_index": 8, "total_citations": 207, "total_publications_count": 20
    },
    {
        "id": "cmu_eng_department__122",
        "first_name": "Pimluck", "last_name": "Kijjanapanich",
        "email": "pimluck@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5046951298",
        "h_index": 14, "total_citations": 571, "total_publications_count": 23
    },
    {
        "id": "cmu_eng_department__123",
        "first_name": "Aunnop", "last_name": "Wongrueng",
        "email": "aunnop@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5009775530",
        "h_index": 9, "total_citations": 328, "total_publications_count": 39
    },
    {
        "id": "cmu_eng_department__124",
        "first_name": "Sulak", "last_name": "Sumitsawan",
        "email": "sulak.sumit@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department__125",
        "first_name": "Puangrat", "last_name": "Kaewlom",
        "email": "kpuangrat@gmail.com",
        "openalex_id": "https://openalex.org/A5056654065",
        "h_index": 31, "total_citations": 4567, "total_publications_count": 92
    },
    {
        "id": "cmu_eng_department__127",
        "first_name": "Sirichai", "last_name": "Koonaphapdeelert",
        "email": "sirichai@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5081015091",
        "h_index": 9, "total_citations": 460, "total_publications_count": 25
    },
    {
        "id": "cmu_eng_department__128",
        "first_name": "Anuchit", "last_name": "Sonwai",
        "email": "anuchit.son@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department__129",
        "first_name": "Napat", "last_name": "Jakrawatana",
        "email": "napat.ja@cmu.ac.th",
        "openalex_id": "https://openalex.org/A5048197864",
        "h_index": 13, "total_citations": 377, "total_publications_count": 33
    },
    {
        "id": "cmu_eng_department__130",
        "first_name": "Sarunnoud", "last_name": "Phupisut",
        "email": "sarunnoud.p@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department__131",
        "first_name": "Pharkphum", "last_name": "Rakruam",
        "email": "pharkphum@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5030124035",
        "h_index": 8, "total_citations": 205, "total_publications_count": 21
    },

    # 2. Civil Engineering
    {
        "id": "cmu_eng_department_kronprasert_49",
        "first_name": "Nopadon", "last_name": "Kronprasert",
        "email": "nopkron@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5053851606",
        "h_index": 15, "total_citations": 646, "total_publications_count": 53
    },
    {
        "id": "cmu_eng_department_pichayapan_48",
        "first_name": "Preda", "last_name": "Pichayapan",
        "email": "preda.p@cmu.ac.th",
        "openalex_id": "https://openalex.org/A5065828619",
        "h_index": 6, "total_citations": 180, "total_publications_count": 22
    },
    {
        "id": "cmu_eng_department_buachart_38",
        "first_name": "Chinapat", "last_name": "Buachart",
        "email": "chinapat@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5052787555",
        "h_index": 7, "total_citations": 134, "total_publications_count": 33
    },
    {
        "id": "cmu_eng_department_kanangkaew_62",
        "first_name": "Somjintana", "last_name": "Kanangkaew",
        "email": "somjintana@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5035688457",
        "h_index": 2, "total_citations": 61, "total_publications_count": 11
    },
    {
        "id": "cmu_eng_department_tanchaisawat_45",
        "first_name": "Tawatchai", "last_name": "Tanchaisawat",
        "email": "tawatchai@eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5029182143",
        "h_index": 9, "total_citations": 274, "total_publications_count": 31
    },
    {
        "id": "cmu_eng_department_wongchana_47",
        "first_name": "Pongsakorn", "last_name": "Wongchana",
        "email": "pongsakorn.w@cmu.ac.th",
        "openalex_id": "https://openalex.org/A5074211029",
        "h_index": 2, "total_citations": 14, "total_publications_count": 8
    },
    {
        "id": "cmu_eng_department_arunotayanun_56",
        "first_name": "Kriangkrai", "last_name": "Arunotayanun",
        "email": "kriangkrai@eng.cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_sinsabvarodo_61",
        "first_name": "Chana", "last_name": "Sinsabvaradom",
        "email": "chana.sinsabvaradom@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_upayokin_52",
        "first_name": "Auttawit", "last_name": "Upayokin",
        "email": "auttawit.u@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_sethabouppha_42",
        "first_name": "Sethapong", "last_name": "Sethabouppha",
        "email": "sethapong.s@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_thongmunee_46",
        "first_name": "Suriyah", "last_name": "Thongmunee",
        "email": "suriyah.t@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_prof_58",
        "first_name": "Poon", "last_name": "Thiangburanathum",
        "email": "poon@eng.cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_kittikun_44",
        "first_name": "Kittikun", "last_name": "Jitpirod",
        "email": "kittikun.j@cmu.ac.th"
    },

    # 3. Mechanical & Interdisciplinary Engineering
    {
        "id": "cmu_eng_department_james_84",
        "full_name_th": "รศ.ดร. เจมส์ คริสโตเฟอร์ มอแรน",
        "first_name": "James Christopher", "last_name": "Moran",
        "email": "james.moran@cmu.ac.th",
        "openalex_id": "https://openalex.org/A5090064900",
        "h_index": 11, "total_citations": 464, "total_publications_count": 57
    },
    {
        "id": "cmu_eng_department_matthew_69",
        "full_name_th": "ศ.ดร. แมทธิว โอ. ที. โคล",
        "first_name": "Matthew", "last_name": "Cole",
        "email": "motcole@dome.eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5059632839",
        "h_index": 19, "total_citations": 1100, "total_publications_count": 85
    },
    {
        "id": "cmu_eng_department_natawit_83",
        "first_name": "Nattawit", "last_name": "Promma",
        "email": "nattawit@dome.eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5043406856",
        "h_index": 4, "total_citations": 187, "total_publications_count": 16
    },
    {
        "id": "cmu_eng_department_anusarn_81",
        "first_name": "Anusarn", "last_name": "Permsuwan",
        "email": "anusan@dome.eng.cmu.ac.th",
        "openalex_id": "https://openalex.org/A5036986913",
        "h_index": 4, "total_citations": 54, "total_publications_count": 5
    },
    {
        "id": "cmu_eng_department_kengkamol_100",
        "first_name": "Kengkamon", "last_name": "Wiratkasem",
        "email": "kengkamon.w@cmu.ac.th"
    },
    {
        "id": "cmu_eng_department_kordkwan_79",
        "first_name": "Kordkwan", "last_name": "Namsanguan",
        "email": "kordkwan@dome.eng.cmu.ac.th"
    },
    {
        "id": "chiangmaiu_facultyofe_phimphilai_006",
        "first_name": "Kajorndaj", "last_name": "Phimphilai",
        "email": "kajorndej.p@cmu.ac.th"
    }
]


def run_enrichment():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
    cur = conn.cursor()

    updated_count = 0
    for u in UPDATES:
        fid = u["id"]
        set_clauses = []
        params = []

        if "full_name_th" in u:
            set_clauses.append("full_name_th = %s")
            params.append(u["full_name_th"])
        if "first_name" in u:
            set_clauses.append("first_name = %s")
            params.append(u["first_name"])
        if "last_name" in u:
            set_clauses.append("last_name = %s")
            params.append(u["last_name"])
        if "email" in u:
            set_clauses.append("email = %s")
            params.append(u["email"])
        if "openalex_id" in u:
            set_clauses.append("openalex_id = %s")
            params.append(u["openalex_id"])
        if "h_index" in u:
            set_clauses.append("h_index = %s")
            params.append(u["h_index"])
        if "total_citations" in u:
            set_clauses.append("total_citations = %s")
            params.append(u["total_citations"])
        if "total_publications_count" in u:
            set_clauses.append("total_publications_count = %s")
            params.append(u["total_publications_count"])

        # Also update embedding_text with the new English names
        set_clauses.append("embedding_text = COALESCE(%s, '') || ' ' || COALESCE(%s, '') || ' ' || COALESCE(embedding_text, '')")
        params.append(u.get("first_name", ""))
        params.append(u.get("last_name", ""))

        params.append(fid)
        sql = f"""
            UPDATE faculties
            SET {', '.join(set_clauses)}
            WHERE id = %s;
        """
        cur.execute(sql, tuple(params))
        updated_count += cur.rowcount

    conn.commit()
    print(f"✅ Successfully updated {updated_count} records in local PostgreSQL database.")

    # Verification query
    cur.execute("""
        SELECT id, full_name_th, first_name, last_name, email, h_index, total_citations, openalex_id
        FROM faculties
        WHERE id IN (
            'cmu_eng_department_kronprasert_49',
            'cmu_eng_department__121',
            'cmu_eng_department__125',
            'cmu_eng_department_james_84',
            'cmu_eng_department_matthew_69',
            'cmu_eng_department__122',
            'cmu_eng_department__120'
        )
        ORDER BY id;
    """)
    rows = cur.fetchall()
    print("\n=== Verification Sample (Local DB) ===")
    for r in rows:
        print(f"[{r[0]}] {r[1]} -> {r[2]} {r[3]} | Email: {r[4]} | H: {r[5]}, Cites: {r[6]} | Alex: {r[7]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_enrichment()
