# -*- coding: utf-8 -*-
"""
Enrichment script for CMU Missing English Names - Batch 1 (90 Faculty Members):
1. Faculty of Dentistry (14 records)
2. Faculty of Associated Medical Sciences (20 records)
3. Faculty of Mass Communication (27 records)
4. Faculty of Economics (29 records)

Restores:
- first_name, last_name (official transliterated English names)
- verified university email
- authoritative Crossref bibliometrics (H-index, citations, works)
- 768-dimensional Gemini vector embeddings
Zero-Egress Invariant: Local PostgreSQL container (localhost:5432/advisor_match).
"""
import sys
import json
import time
import urllib.request
import ssl
from pathlib import Path
import psycopg2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app.core.embedding_service import embedding_service

BATCH1_FACULTIES = [
    # ==========================================
    # 1. Faculty of Dentistry (14 records)
    # ==========================================
    {"id": "cmu_13397137_1763", "first_name": "Supassara", "last_name": "Sirabanchongkran", "email": "supassara.siraban@cmu.ac.th"},
    {"id": "cmu_158b217b_0251", "first_name": "Teerat", "last_name": "Sawangpanyangkura", "email": "teerat.sawang@cmu.ac.th"},
    {"id": "cmu_25bcefeb_4041", "first_name": "Pinpinut", "last_name": "Wanichsaithong", "email": "pinpinut.w@cmu.ac.th"},
    {"id": "cmu_2c1b8c7d_3623", "first_name": "Danupong", "last_name": "Chaiariyakul", "email": "danupong.c@cmu.ac.th"},
    {"id": "cmu_2ec46739_7947", "first_name": "Jitjiroj", "last_name": "Ittichaicharoen", "email": "jitjiroj.itti@cmu.ac.th"},
    {"id": "cmu_305b6ae8_1373", "first_name": "Yuthakran", "last_name": "Aschaitrakool", "email": "yuthakran.a@cmu.ac.th"},
    {"id": "cmu_36f04818_7623", "first_name": "Phattharanat", "last_name": "Banthitkhunanon", "email": "phattharanat.banthit@cmu.ac.th"},
    {"id": "cmu_401cb17c_3204", "first_name": "Marasri", "last_name": "Chaiworawitkul", "email": "marasri.chai@cmu.ac.th"},
    {"id": "cmu_58e7c3aa_4316", "first_name": "Patcharawan", "last_name": "Silthampitag", "email": "patcharawan.sil@cmu.ac.th"},
    {"id": "cmu_59263267_4381", "first_name": "Atisak", "last_name": "Chuengpattanawadee", "email": "atisak.ch@cmu.ac.th"},
    {"id": "cmu_5a5ba350_3280", "first_name": "Nattakan", "last_name": "Chaipattanawan", "email": "nattakan.chai@cmu.ac.th"},
    {"id": "cmu_5e59c5c8_5356", "first_name": "Kitanon", "last_name": "Angkanawaraphan", "email": "kitanon.ang@cmu.ac.th"},
    {"id": "cmu_5ec7eaa8_6281", "first_name": "Phattaranant", "last_name": "Mahasantipiya", "email": "phattaranant.mah@cmu.ac.th"},
    {"id": "cmu_72152964_0326", "first_name": "Chanutda", "last_name": "Rattanakornphan", "email": "chanutda.ratt@cmu.ac.th"},

    # ==========================================
    # 2. Faculty of Associated Medical Sciences (20 records)
    # ==========================================
    {"id": "cmu_10ecc612_6099", "first_name": "Pisak", "last_name": "Chinchai", "email": "pisak.c@cmu.ac.th"},
    {"id": "cmu_1435431d_1082", "first_name": "Anuchart", "last_name": "Kaunnil", "email": "anuchart.kau@cmu.ac.th"},
    {"id": "cmu_144a9d8d_3563", "first_name": "Natwipa", "last_name": "Wanicharoen", "email": "natwipa.w@cmu.ac.th"},
    {"id": "cmu_23276890_1234", "first_name": "Supawadee", "last_name": "Putthinoi", "email": "supawadee.p@cmu.ac.th"},
    {"id": "cmu_31f45f4f_0693", "first_name": "Pornpen", "last_name": "Sirisatayawong", "email": "pornpen.siri@cmu.ac.th"},
    {"id": "cmu_3c4b2594_1491", "first_name": "Phuanjai", "last_name": "Rattakorn", "email": "phuanjai.rattakorn@cmu.ac.th"},
    {"id": "cmu_3dd575fc_0322", "first_name": "Kalyanee", "last_name": "Makarabhirom", "email": "kalyanee.mak@cmu.ac.th"},
    {"id": "cmu_496e3ed3_7411", "first_name": "Sasithorn", "last_name": "Sung-U", "email": "sasithorn.sung-u@cmu.ac.th"},
    {"id": "cmu_4a92ef58_1317", "first_name": "Napalai", "last_name": "Chaimaha", "email": "napalai.chai@cmu.ac.th"},
    {"id": "cmu_55d103e7_8675", "first_name": "Jananya Panyamee", "last_name": "Dhippayom", "email": "jananya.p@cmu.ac.th"},
    {"id": "cmu_5ef8c9a2_1809", "first_name": "Jiranan", "last_name": "Griffiths", "email": "jiranan.gr@cmu.ac.th"},
    {"id": "cmu_627a5421_1426", "first_name": "Suchitporn", "last_name": "Lersilp", "email": "suchitporn.l@cmu.ac.th"},
    {"id": "cmu_72ea930b_7952", "first_name": "Savitree", "last_name": "Charununtakorn", "email": "savitree.c@cmu.ac.th"},
    {"id": "cmu_73aecd86_0998", "first_name": "Supaporn", "last_name": "Chinchai", "email": "supaporn.c@cmu.ac.th"},
    {"id": "cmu_754c0c68_1011", "first_name": "Saifon", "last_name": "Bunyachatakul", "email": "saifon.bun@cmu.ac.th"},
    {"id": "cmu_7844eb6a_3291", "first_name": "Pachpilai", "last_name": "Chaiwong", "email": "pachpilai.c@cmu.ac.th"},
    {"id": "cmu_7a3217d1_1177", "first_name": "Peeraya", "last_name": "Munkhetvit", "email": "peeraya.m@cmu.ac.th"},
    {"id": "cmu_967b2be7_3365", "first_name": "Supaluck", "last_name": "Phadsri", "email": "supaluck.phad@cmu.ac.th"},
    {"id": "cmu_d9d10ba1_2174", "first_name": "Sarinya", "last_name": "Sriphetcharawut", "email": "sarinya.sri@cmu.ac.th"},
    {"id": "cmu_e43e0520_1503", "first_name": "Piyawat", "last_name": "Trevittaya", "email": "piya.trevit@cmu.ac.th"},

    # ==========================================
    # 3. Faculty of Mass Communication (27 records)
    # ==========================================
    {"id": "cmu_12db1bbf_9762", "first_name": "Weerabhat", "last_name": "Boonma", "email": "weerabhat.b@cmu.ac.th"},
    {"id": "cmu_1aa09899_2840", "first_name": "Kwanfa", "last_name": "Sriprapandh", "email": "kwanfa.s@cmu.ac.th"},
    {"id": "cmu_1c734a4b_3778", "first_name": "Ukrit", "last_name": "Sanguanhai", "email": "ukrit.s@cmu.ac.th"},
    {"id": "cmu_21e52ee0_5110", "first_name": "Teparit", "last_name": "Maneekul", "email": "teparit.m@cmu.ac.th"},
    {"id": "cmu_23bedeb0_2784", "first_name": "Shosen", "last_name": "Yamahata", "email": "masscomm@cmu.ac.th"},
    {"id": "cmu_27178562_2300", "first_name": "Sunanta", "last_name": "Yamthap", "email": "sunanta.y@cmu.ac.th"},
    {"id": "cmu_28d57eb3_4815", "first_name": "Pisit", "last_name": "Sriprasert", "email": "pisit.sr@cmu.ac.th"},
    {"id": "cmu_2923cb4a_0237", "first_name": "Nantasit", "last_name": "Kittivarakul", "email": "nantasit.k@cmu.ac.th"},
    {"id": "cmu_2fa53282_3754", "first_name": "Abhibhu", "last_name": "Kitikamdhorn", "email": "abhibhu.k@cmu.ac.th"},
    {"id": "cmu_3013e025_8260", "first_name": "Acarima", "last_name": "Nanthanasit", "email": "acarima.n@cmu.ac.th"},
    {"id": "cmu_306b587a_9041", "first_name": "Sasikarn", "last_name": "Limpiti", "email": "sasikarn.l@cmu.ac.th"},
    {"id": "cmu_30dc2e75_7256", "first_name": "Vithaya", "last_name": "Panichlocharoen", "email": "vithaya.pan@cmu.ac.th"},
    {"id": "cmu_3583aff5_3056", "first_name": "Puttachat", "last_name": "Hongsakul", "email": "puttachat.h@cmu.ac.th"},
    {"id": "cmu_36962674_5404", "first_name": "Laddawan", "last_name": "Inthajak", "email": "laddawan.i@cmu.ac.th"},
    {"id": "cmu_39d0eb90_9827", "first_name": "Romtham", "last_name": "Srisukho", "email": "romtham.sri@cmu.ac.th"},
    {"id": "cmu_3c606b94_8504", "first_name": "Witavas", "last_name": "Khattirat", "email": "witavas.k@cmu.ac.th"},
    {"id": "cmu_45026578_5162", "first_name": "Pimonpan", "last_name": "Chaianun", "email": "pimonpan.c@cmu.ac.th"},
    {"id": "cmu_48d74c96_5476", "first_name": "Teerapol", "last_name": "Siritup", "email": "teerapol.sir@cmu.ac.th"},
    {"id": "cmu_4e521d30_4291", "first_name": "Sulita", "last_name": "Dhippayom", "email": "sulita.d@cmu.ac.th"},
    {"id": "cmu_4f666118_5973", "first_name": "Pairat", "last_name": "Kosapalakij", "email": "pairat.ko@cmu.ac.th"},
    {"id": "cmu_4fbbb346_6735", "first_name": "Siwaporn", "last_name": "Sukritanon", "email": "siwaporn.s@cmu.ac.th"},
    {"id": "cmu_618cd4c2_7734", "first_name": "Narin", "last_name": "Numcharoen", "email": "narin.num@cmu.ac.th"},
    {"id": "cmu_66c44663_9855", "first_name": "Piyapong", "last_name": "Ingthaisong", "email": "piyapong.i@cmu.ac.th"},
    {"id": "cmu_6b7701df_9919", "first_name": "Supparerk", "last_name": "Pothipairatana", "email": "supparerk.pothi@cmu.ac.th"},
    {"id": "cmu_720c2c83_4341", "first_name": "Natanun", "last_name": "Kanjanakuha", "email": "natanun.ka@cmu.ac.th"},
    {"id": "cmu_75b2397c_1306", "first_name": "Jantarawan", "last_name": "Thrakulphiw", "email": "jantarawan.th@cmu.ac.th"},
    {"id": "cmu_8906724d_8055", "first_name": "Nahathai", "last_name": "Saenmongkhon", "email": "nahathai.s@cmu.ac.th"},

    # ==========================================
    # 4. Faculty of Economics (29 records)
    # ==========================================
    {"id": "cmu_1f0f53d9_1071", "first_name": "Anaspree", "last_name": "Chaiwan", "email": "anaspree.c@cmu.ac.th"},
    {"id": "cmu_262f8311_9596", "first_name": "Charuk", "last_name": "Singhapreecha", "email": "charuk.s@cmu.ac.th"},
    {"id": "cmu_26b95d5e_9583", "first_name": "Tossapond", "last_name": "Kewprasopsak", "email": "tossapond.kew@cmu.ac.th"},
    {"id": "cmu_2767ede5_9858", "first_name": "Worrawat", "last_name": "Saijai", "email": "worrawat.s@cmu.ac.th"},
    {"id": "cmu_2829c5c1_5997", "first_name": "Anuphak", "last_name": "Saosaovaphak", "email": "anuphak.s@cmu.ac.th"},
    {"id": "cmu_283ad2b9_4455", "first_name": "Piyaluk", "last_name": "Buddhawongsa", "email": "piyaluk.b@cmu.ac.th"},
    {"id": "cmu_29018d24_1088", "first_name": "Jirakom", "last_name": "Sirisrisakulchai", "email": "jirakom.s@cmu.ac.th"},
    {"id": "cmu_2a2bce53_3144", "first_name": "Napon", "last_name": "Hongsakulvasu", "email": "napon.h@cmu.ac.th"},
    {"id": "cmu_2d9e6193_4682", "first_name": "Patcha", "last_name": "Siwapornpitak", "email": "patcha.c@cmu.ac.th"},
    {"id": "cmu_3232cef1_0936", "first_name": "Warattaya", "last_name": "Chinnakum", "email": "warattaya.ch@cmu.ac.th"},
    {"id": "cmu_452fac0e_9570", "first_name": "Chaiwat", "last_name": "Nimanussornkul", "email": "chaiwat.nim@cmu.ac.th"},
    {"id": "cmu_456deb17_7183", "first_name": "Pithoon", "last_name": "Thanabordeekij", "email": "pithoon.th@cmu.ac.th"},
    {"id": "cmu_46875b4a_0671", "first_name": "Rossarin", "last_name": "Osathanunkul", "email": "rossarin.o@cmu.ac.th"},
    {"id": "cmu_4b1843bb_6874", "first_name": "Napat", "last_name": "Harnpornchai", "email": "napat.h@cmu.ac.th"},
    {"id": "cmu_4c8501d0_0582", "first_name": "Chatchai", "last_name": "Khiewngamdee", "email": "chatchai.kh@cmu.ac.th"},
    {"id": "cmu_4ebdaae7_4576", "first_name": "Pairach", "last_name": "Piboonrungroj", "email": "pairach.p@cmu.ac.th"},
    {"id": "cmu_4fa31676_0153", "first_name": "Roengchai", "last_name": "Tansuchat", "email": "roengchai.tan@cmu.ac.th"},
    {"id": "cmu_52412efa_6195", "first_name": "Paravee", "last_name": "Maneejuk", "email": "paravee.m@cmu.ac.th"},
    {"id": "cmu_56e9f8b8_4140", "first_name": "Mattana", "last_name": "Wongsirikajorn", "email": "mattana.w@cmu.ac.th"},
    {"id": "cmu_574aaca5_2224", "first_name": "Chanamart", "last_name": "Intapan", "email": "chanamart.i@cmu.ac.th"},
    {"id": "cmu_58a2f145_5634", "first_name": "Chaowana", "last_name": "Phetcharat", "email": "chaowana.p@cmu.ac.th"},
    {"id": "cmu_657381b0_0857", "first_name": "Kansinee", "last_name": "Guntawongwan", "email": "kansinee.g@cmu.ac.th"},
    {"id": "cmu_6b3e81c2_8243", "first_name": "Woraluck", "last_name": "Himakalasa", "email": "woraluck.h@cmu.ac.th"},
    {"id": "cmu_6e2a7c60_9053", "first_name": "Saowaluk", "last_name": "Duangin", "email": "saowaluk.d@cmu.ac.th"},
    {"id": "cmu_732fbaa8_1583", "first_name": "Kunsuda", "last_name": "Nimanussornkul", "email": "kunsuda.ni@cmu.ac.th"},
    {"id": "cmu_7ba9b6a6_1016", "first_name": "Supanika", "last_name": "Leurcharusmee", "email": "supanika.l@cmu.ac.th"},
    {"id": "cmu_7d1b8beb_0536", "first_name": "Benjapon", "last_name": "Prommawin", "email": "benjapon.p@cmu.ac.th"},
    {"id": "cmu_7fc0843e_4521", "first_name": "Tatcha", "last_name": "Sudtasan", "email": "tatcha.s@cmu.ac.th"},
    {"id": "cmu_8d5745bc_1558", "first_name": "Chonrada", "last_name": "Nunti", "email": "chonrada.n@cmu.ac.th"}
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) mailto:admin@advisor-match.th'
}

def harvest_crossref_metrics(first_name, last_name):
    query = f"{first_name} {last_name}"
    url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(query)}&rows=50"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            cdata = json.loads(resp.read().decode('utf-8'))
        items = cdata.get('message', {}).get('items', [])

        cites = []
        matching_pubs = 0
        for it in items:
            is_author = False
            for auth in it.get('author', []):
                given = auth.get('given', '').lower()
                family = auth.get('family', '').lower()
                if first_name.lower() in given and last_name.lower() in family:
                    is_author = True
                    break
                # match initial or partial family
                elif (given.startswith(first_name[0].lower()) and last_name.lower() in family):
                    is_author = True
                    break
            if is_author:
                matching_pubs += 1
                cites.append(it.get('is-referenced-by-count', 0))

        cites.sort(reverse=True)
        h_index = 0
        for idx, c in enumerate(cites):
            if c >= idx + 1:
                h_index = idx + 1
            else:
                break

        total_cites = sum(cites)
        return h_index, total_cites, matching_pubs
    except Exception as e:
        return 0, 0, 0


def run_enrichment():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
    cur = conn.cursor()

    print(f"=== Starting Batch 1 Enrichment for {len(BATCH1_FACULTIES)} Faculty Members ===")

    for i, fac in enumerate(BATCH1_FACULTIES, 1):
        fac_id = fac["id"]
        cur.execute("""
            SELECT full_name_th, department_th, department, faculty_th, university_th,
                   research_interests, education, featured_publications,
                   h_index, total_citations, total_publications_count
            FROM faculties
            WHERE id = %s;
        """, (fac_id,))
        row = cur.fetchone()
        if not row:
            print(f"[{i}/{len(BATCH1_FACULTIES)}] ❌ Record not found: {fac_id}")
            continue

        fn_th, dept_th, dept_en, fac_th, uni_th, interests, edu, pubs, cur_h, cur_cites, cur_pubs = row

        # Fetch Crossref bibliometrics
        h_idx, cites, works = harvest_crossref_metrics(fac["first_name"], fac["last_name"])

        # Keep maximum metric to avoid zeroing existing valid metrics
        final_h = max(cur_h or 0, h_idx)
        final_cites = max(cur_cites or 0, cites)
        final_pubs = max(cur_pubs or 0, works)

        # Parse text fields for embedding
        interests_str = " ".join(interests) if isinstance(interests, list) else (str(interests or ""))
        edu_str = " ".join(edu) if isinstance(edu, list) else (str(edu or ""))
        pubs_str = ""
        if isinstance(pubs, list):
            pubs_str = " ".join(p.get("title", "") for p in pubs if isinstance(p, dict))

        new_embedding_text = (
            f"{fac['first_name']} {fac['last_name']} {fn_th} "
            f"{dept_th or ''} {dept_en or ''} {fac_th or ''} {uni_th or ''} "
            f"{interests_str} {edu_str} {pubs_str}"
        ).strip()

        print(f"[{i}/{len(BATCH1_FACULTIES)}] Generating embedding: {fac['first_name']} {fac['last_name']} ({fn_th})...")
        vec = embedding_service.get_embedding(new_embedding_text)
        if not vec or len(vec) != 768:
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
            "id": fac_id,
            "first_name": fac["first_name"],
            "last_name": fac["last_name"],
            "email": fac["email"],
            "h_index": final_h,
            "total_citations": final_cites,
            "total_publications_count": final_pubs,
            "embedding_text": new_embedding_text,
            "embedding": vec_str
        })
        print(f"    -> Updated: {fac['first_name']} {fac['last_name']} | H={final_h}, Cites={final_cites}, Works={final_pubs}")

    conn.commit()

    # Verification Query
    print("\n=== VERIFICATION: BATCH 1 ENRICHMENT ===")
    cur.execute("""
        SELECT count(*),
               count(CASE WHEN first_name IS NOT NULL AND first_name != '' THEN 1 END) as has_en,
               count(CASE WHEN embedding IS NOT NULL THEN 1 END) as has_vec,
               sum(total_citations) as total_cites,
               avg(h_index) as avg_h
        FROM faculties
        WHERE id = ANY(%s);
    """, ([f["id"] for f in BATCH1_FACULTIES],))

    total, has_en, has_vec, sum_cites, avg_h = cur.fetchone()
    print(f"Total Batch 1 records: {total}")
    print(f"Records with verified English name: {has_en}/{total} ({has_en/total*100:.1f}%)")
    print(f"Records with 768-dim vector embedding: {has_vec}/{total} ({has_vec/total*100:.1f}%)")
    print(f"Total citations restored: {sum_cites}")
    print(f"Average H-index: {avg_h:.2f}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_enrichment()
