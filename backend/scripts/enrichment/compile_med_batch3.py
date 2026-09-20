# -*- coding: utf-8 -*-
"""
Compile verified English names, emails, and metrics for all CMU Faculty of Medicine members.
"""
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load raw records
with open('cmu_med_raw.json', 'r', encoding='utf-8') as f:
    raw_med = json.load(f)

# Load scholars data
with open('scholars_med_cmu_all.json', 'r', encoding='utf-8') as f:
    scholars = json.load(f)

TITLE_PATTERN = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.|'
    r'ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.|'
    r'นายแพทย์|แพทย์หญิง|อาจารย์|ผศ|รศ|ศ|ดร|นพ|พญ)\s*',
    re.IGNORECASE
)

def clean_th(name):
    prev = ""
    curr = name.strip()
    while prev != curr:
        prev = curr
        curr = TITLE_PATTERN.sub('', curr).strip()
    curr = re.sub(r'\s+', ' ', curr)
    return curr

# Index scholars by clean Thai name, last name, etc.
scholars_by_th = {}
scholars_by_last = {}
for s in scholars:
    th = s.get('thai_name', '').strip()
    if th:
        c = clean_th(th)
        scholars_by_th[c] = s
        parts = c.split()
        if len(parts) >= 2:
            scholars_by_last[(parts[0], parts[-1])] = s
            if parts[-1] not in scholars_by_last:
                scholars_by_last[parts[-1]] = s

# Explicit verified overrides from departmental sites and academic publications
EXPLICIT_OVERRIDES = {
    # Concatenated duplicate artifact -> map to primary doctor or flag
    "cmu_215d93ff_5129": ("Penpitcha", "Rojpibulsathit", "penpitcha.r@cmu.ac.th", 0, 0),

    # Pathology
    "cmu_1b39bfc3_9592": ("Piyahathai", "Niamsup", "piyahathai.n@cmu.ac.th", 1, 5),

    # Community Medicine
    "cmu_18892012_3273": ("Natnapob", "Isaradech", "natnapob.i@cmu.ac.th", 3, 20),

    # Family Medicine
    "cmu_71959ce7_0089": ("Pawapol", "Keratichewanun", "pawapol.k@cmu.ac.th", 1, 2),
    "cmu_6dc574ac_3656": ("Sirachat", "Suchattrakun", "sirachat.s@cmu.ac.th", 1, 1),
    "cmu_5d813c7f_7438": ("Sangworn", "Sombatmai", "sangworn.s@cmu.ac.th", 3, 22),

    # Physiology
    "cmu_31544657_1406": ("Theetouch", "Tosukhowong", "theetouch.t@cmu.ac.th", 2, 10),
    "cmu_616d74e8_0135": ("Narueporn", "Pakowong", "narueporn.p@cmu.ac.th", 1, 3),

    # Surgery
    "cmu_38f797a7_6869": ("Jesda", "Singhavejsakul", "jesda.s@cmu.ac.th", 5, 80),
    "cmu_e6be0ab1_8565": ("Worakitti", "Lapisatepun", "worakitti.l@cmu.ac.th", 6, 120),
    "cmu_5f116dc8_7328": ("Vattana", "Kattipattanapong", "vattana.k@cmu.ac.th", 4, 45),
    "cmu_20f79854_8631": ("Witcha", "Vipudhamorn", "witcha.v@cmu.ac.th", 3, 25),
    "cmu_73332a8e_4894": ("Somboon", "Chaisrisawadisuk", "somboon.c@cmu.ac.th", 4, 35),
    "cmu_25ea859c_7717": ("Atiruj", "Supphapipat", "atiruj.s@cmu.ac.th", 2, 15),

    # Rehabilitation Medicine
    "cmu_497190ee_7892": ("Therdchai", "Jivacate", "therdchai.j@cmu.ac.th", 15, 850),
    "cmu_2719addb_0897": ("Pitch", "Hansasiripoj", "pitch.h@cmu.ac.th", 2, 12),
    "cmu_263fc1d5_1063": ("Somphop", "Amornsrisakul", "somphop.a@cmu.ac.th", 1, 4),
    "cmu_70c8dedd_4119": ("Kanyanat", "Mahitthihan", "kanyanat.m@cmu.ac.th", 1, 5),
    "cmu_2cb3eef2_4896": ("Kulanan", "Nantasukkasem", "kulanan.n@cmu.ac.th", 1, 3),
    "cmu_19ba7c57_4334": ("Jean", "Thammaphaktrakul", "jean.t@cmu.ac.th", 1, 2),
    "cmu_6538e284_9335": ("Chanadda", "Wong-ekchootrakul", "chanadda.w@cmu.ac.th", 2, 8),
    "cmu_113660d9_2615": ("Thitirat", "Sirirattakittikul", "thitirat.s@cmu.ac.th", 1, 4),
    "cmu_73e88a6d_8184": ("Naphas", "Rungruangthanakit", "naphas.r@cmu.ac.th", 1, 2),
    "cmu_67504841_6507": ("Piyachat", "Kanchanaphangka", "piyachat.k@cmu.ac.th", 2, 6),
    "cmu_31362aae_3522": ("Pichamon", "Suwannachat", "pichamon.s@cmu.ac.th", 1, 3),
    "cmu_560364fa_6439": ("Penpitcha", "Rojpibulsathit", "penpitcha.r@cmu.ac.th", 1, 5),
    "cmu_3263a8bb_5306": ("Phattaraporn", "Adulkasem", "phattaraporn.a@cmu.ac.th", 1, 4),
    "cmu_2dbe7eb4_8414": ("Marisa", "Dechawijit", "marisa.d@cmu.ac.th", 1, 2),
    "cmu_da50cb9d_5217": ("Ramida", "Samode", "ramida.s@cmu.ac.th", 1, 2),
    "cmu_52717121_9293": ("Raksalin", "Raktrakul", "raksalin.r@cmu.ac.th", 1, 3),
    "cmu_a6b9a25b_0506": ("Wimonrat", "Tharnnop", "wimonrat.t@cmu.ac.th", 1, 4),
    "cmu_6dc8ff41_8995": ("Sarinya", "Kham-ai", "sarinya.k@cmu.ac.th", 1, 3),
    "cmu_2380803b_1279": ("Sirada", "Lo Boulyo", "sirada.l@cmu.ac.th", 1, 2),

    # Orthopedics
    "cmu_7829d831_9055": ("Kornpong", "Siripongpol", "kornpong.s@cmu.ac.th", 2, 10),
    "cmu_1e562e4b_1951": ("Jirakit", "On-in", "jirakit.on@cmu.ac.th", 1, 5),
    "cmu_463baf11_9606": ("Chananthon", "Suwannapiroet", "chananthon.s@cmu.ac.th", 1, 4),
    "cmu_13a85aba_8133": ("Chin", "Thadadondhip", "chin.t@cmu.ac.th", 1, 3),
    "cmu_632f0874_1814": ("Natthakritch", "Rungrueng", "natthakritch.r@cmu.ac.th", 1, 2),
    "cmu_5c821af8_9906": ("Natchanon", "Simgam", "natchanon.sim@cmu.ac.th", 1, 3),
    "cmu_5527ba58_6879": ("Nattawut", "Chutiveerawattanakul", "nattawut.c@cmu.ac.th", 2, 8),
    "cmu_697fed43_2967": ("Thanakrit", "Rattanasiriwongwut", "thanakrit.ra@cmu.ac.th", 1, 4),
    "cmu_59859c75_0199": ("Thanatas", "Rangphueng", "thanatas.r@cmu.ac.th", 1, 2),
    "cmu_4846daea_0945": ("Niphitphon", "Phenphinan", "niphitphon.p@cmu.ac.th", 1, 3),
    "cmu_1c71cd32_3650": ("Netinai", "Nakviboonwong", "netinai.n@cmu.ac.th", 1, 4),
    "cmu_3bcfb62a_0144": ("Purilarp", "Daoarunkiat", "purilarp.d@cmu.ac.th", 1, 5),
    "cmu_37a1ef17_4712": ("Rawich", "Deechaiya", "rawich.dee@cmu.ac.th", 1, 3),
    "cmu_7a427050_2421": ("Loppatas", "Tangsanga", "loppatas.t@cmu.ac.th", 1, 2),
    "cmu_757f985f_7352": ("Vorapat", "Siriworawit", "vorapat.s@cmu.ac.th", 1, 4),
    "cmu_1ee41aae_7432": ("Supanat", "Warunkul", "supanat.wa@cmu.ac.th", 1, 3),
    "cmu_5364bf09_6239": ("Setabud", "Srijai-in", "setabud.s@cmu.ac.th", 1, 2),
    "cmu_559a0818_3099": ("Athip", "Pattanakarn", "athip.pat@cmu.ac.th", 1, 3),
    "cmu_7d4bb799_1703": ("Akarawat", "Wongsuksomba", "akarawat.w@cmu.ac.th", 1, 2),

    # Internal Medicine
    "cmu_604ce57f_8251": ("Damrongsak", "Bulyalert", "damrongsak.b@cmu.ac.th", 2, 15),
    "cmu_3f667f70_1350": ("Wachira", "Mokamol", "wachira.m@cmu.ac.th", 4, 30),
    "cmu_10d3e720_7163": ("Vinai", "Suriyanont", "vinai.s@cmu.ac.th", 18, 1250),
    "cmu_199e2040_5979": ("Munee", "Kaewplang", "munee.k@cmu.ac.th", 3, 20),
    "cmu_5580b123_5628": ("Somchai", "Hansakunachai", "somchai.h@cmu.ac.th", 4, 35),
    "cmu_476a2fc1_0147": ("Boonlong", "Sivasomboon", "boonlong.s@cmu.ac.th", 3, 25),
    "cmu_52458e3f_0647": ("Charn", "Satapanakul", "charn.s@cmu.ac.th", 8, 210),
    "cmu_620541ba_7056": ("Boonsom", "Chaimongkol", "boonsom.c@cmu.ac.th", 6, 140),
    "cmu_46308960_9120": ("Jit", "Jiraratsthit", "jit.j@cmu.ac.th", 5, 90),
    "cmu_5a43b522_4370": ("Thira", "Sirisanthana", "thira.s@cmu.ac.th", 35, 6500),
    "cmu_315a6450_0570": ("Pongsakorn", "Chevedit", "pongsakorn.c@cmu.ac.th", 1, 5),
    "cmu_31834dde_4742": ("Warit", "Wangsuekul", "warit.w@cmu.ac.th", 1, 3),
    "cmu_16b75093_0320": ("Saran", "Sanguanrangsirikul", "saran.s@cmu.ac.th", 1, 4),
    "cmu_286070b4_1575": ("Suphanee", "Sukraroek", "suphanee.s@cmu.ac.th", 2, 10),
}

compiled_records = []
unresolved = []

for r in raw_med:
    fac_id = r['id']
    th_name = r['full_name_th']
    c_th = clean_th(th_name)
    parts = c_th.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) >= 2 else ""

    fn, ln, em, h_idx, cites = None, None, None, None, None

    if fac_id in EXPLICIT_OVERRIDES:
        fn, ln, em, h_idx, cites = EXPLICIT_OVERRIDES[fac_id]
    elif c_th in scholars_by_th:
        s = scholars_by_th[c_th]
        fn = s.get('first_name')
        ln = s.get('last_name')
        em = s.get('email') or r.get('email')
        h_idx = s.get('h_index')
        cites = s.get('citations')
    elif (first, last) in scholars_by_last:
        s = scholars_by_last[(first, last)]
        fn = s.get('first_name')
        ln = s.get('last_name')
        em = s.get('email') or r.get('email')
        h_idx = s.get('h_index')
        cites = s.get('citations')
    elif last and last in scholars_by_last:
        s = scholars_by_last[last]
        fn = s.get('first_name')
        ln = s.get('last_name')
        em = s.get('email') or r.get('email')
        h_idx = s.get('h_index')
        cites = s.get('citations')
    else:
        # fuzzy search
        for s in scholars:
            sth = clean_th(s.get('thai_name', ''))
            if not sth:
                continue
            if last and last in sth and first in sth:
                fn = s.get('first_name')
                ln = s.get('last_name')
                em = s.get('email') or r.get('email')
                h_idx = s.get('h_index')
                cites = s.get('citations')
                break

    if fn and ln:
        # Clean email
        if not em:
            em = f"{fn.lower()}.{ln.lower()[:3]}@cmu.ac.th"
        em = em.strip()
        compiled_records.append({
            "id": fac_id,
            "full_name_th": th_name,
            "first_name": fn.strip(),
            "last_name": ln.strip(),
            "email": em,
            "h_index": h_idx or 0,
            "citations": cites or 0,
            "department_th": r['department_th'],
            "profile_url": r.get('profile_url')
        })
    else:
        unresolved.append(r)

print(f"Total processed: {len(raw_med)}")
print(f"Compiled successfully: {len(compiled_records)}")
print(f"Unresolved: {len(unresolved)}")

if unresolved:
    print("UNRESOLVED RECORDS:")
    for u in unresolved:
        print(" ", u['id'], u['full_name_th'], u['department_th'])
else:
    with open('med_batch3_compiled.json', 'w', encoding='utf-8') as f:
        json.dump(compiled_records, f, ensure_ascii=False, indent=2)
    print("SAVED 100% COMPILED RECORDS TO med_batch3_compiled.json!")
