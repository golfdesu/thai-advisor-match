# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Physics (5)
PHYSICS_MAPPING = {
    "cmu_1c152406_5414": ("Waraporn", "Nuntiyakul", "waraporn.n@cmu.ac.th"),
    "cmu_66c849bd_0403": ("Chatdanai", "Boonrueng", "chatdanai.b@cmu.ac.th"),
    "cmu_2485e39d_2496": ("Pornrat", "Wattanakasiwich", "pornrat.w@cmu.ac.th"),
    "cmu_10384457_1171": ("Wiradej", "Thongsuwan", "wiradej.t@cmu.ac.th"),
    "cmu_4dd8180d_3847": ("Supab", "Choopun", "supab.c@cmu.ac.th"),
}

# 2. Biology (26)
BIOLOGY_MAPPING = {
    "cmu_1bd3935f_5239": ("Jarunee", "Jungklang", "jarunee.j@cmu.ac.th"),
    "cmu_37bc1206_6908": ("Chitchol", "Phalaraksh", "chitchol.p@cmu.ac.th"),
    "cmu_6d9af7f5_6031": ("Decha", "Thapanya", "decha.th@cmu.ac.th"),
    "cmu_16c8981f_9609": ("Dia", "Shannon", "dia.shannon@cmu.ac.th"),
    "cmu_4ca2dfe3_2607": ("Thaneeya", "Chetiyanukornkul", "thaneeya.c@cmu.ac.th"),
    "cmu_44c0e7a0_2174": ("Nada", "Arayasakul", "nada.a@cmu.ac.th"),
    "cmu_20f06b68_5382": ("Narin", "Printarakul", "narin.pr@cmu.ac.th"),
    "cmu_34732e43_8275": ("Pimonrat", "Tiansawat", "pimonrat.t@cmu.ac.th"),
    "cmu_7388334b_2017": ("Sitthisak", "Intasit", "sitthisak.inta@cmu.ac.th"),
    "cmu_3c861083_3909": ("Siriphorn", "Jangsutthivorawat", "siriphorn.jang@cmu.ac.th"),
    "cmu_351a8e1b_0968": ("Suttathorn", "Chairuangsri", "suttathorn.c@cmu.ac.th"),
    "cmu_3600809e_2760": ("Hataichanok", "Pandith", "hataichanok.p@cmu.ac.th"),
    "cmu_1fc403b3_5937": ("Issara", "Patawang", "isara.p@cmu.ac.th"),
    "cmu_1e629b8e_1464": ("Jatupol", "Kampuansai", "jatupol.k@cmu.ac.th"),
    "cmu_60e63b54_8938": ("Tanawat", "Chaowasku", "tanawat.ch@cmu.ac.th"),
    "cmu_4610e0bb_2017": ("Prasit", "Wangpakapattanawong", "prasit.wang@cmu.ac.th"),
    "cmu_5d6edcd4_8304": ("Pathrapol", "Lithanatudom", "pathrapol.l@cmu.ac.th"),
    "cmu_52e94dfa_7029": ("Stephen", "Elliott", "stephen.e@cmu.ac.th"),
    "cmu_35dd9b9b_8639": ("Arunothai", "Jampeetong", "arunothai.j@cmu.ac.th"),
    "cmu_2f1b8e42_0426": ("Alice", "Sharp", "alice.sharp@cmu.ac.th"),
    "cmu_2315d15a_2364": ("Aussara", "Panya", "aussara.pan@cmu.ac.th"),
    "cmu_355cf068_4330": ("Usawadee", "Chanasut", "usawadee.ch@cmu.ac.th"),
    "cmu_702352ff_7153": ("Maslin", "Osathanunkul", "maslin.o@cmu.ac.th"),
    "cmu_6aea0aec_3979": ("Jutarat", "Panjakhan", "jutarat.pan@cmu.ac.th"),
    "cmu_b01e79b8_0604": ("Nilita", "Mookjaeng", "nilita.m@cmu.ac.th"),
    "cmu_2bcdb80b_8854": ("Phattrasuda", "Chayaphakdee", "phattrasuda.c@cmu.ac.th"),
}

# 3. Chemistry (54)
CHEM_MAPPING = {
    "cmu_2e6a7981_7631": ("Kornthach", "Ounnunkad", "kornthach.o@cmu.ac.th"),
    "cmu_40a62142_8785": ("Kritsana", "Jitmanee", "kritsana.j@cmu.ac.th"),
    "cmu_16f82415_7802": ("Kongkiat", "Trisuwan", "kongkiat.t@cmu.ac.th"),
    "cmu_701ab247_6985": ("Kanlayawat", "Wangkawong", "kanlayawat.w@cmu.ac.th"),
    "cmu_4b06c396_0374": ("Kanchana", "Damri", "kanchana.d@cmu.ac.th"),
    "cmu_7a577000_1451": ("Kittipan", "Sivawannapong", "kittipan.s@cmu.ac.th"),
    "cmu_5f340589_7775": ("Kullapa", "Chanawanno", "kullapa.c@cmu.ac.th"),
    "cmu_58266b28_7728": ("Kiattikhun", "Manokruang", "kiattikhun.m@cmu.ac.th"),
    "cmu_4e479ced_9227": ("Kanarat", "Nalampang", "kanarat.n@cmu.ac.th"),
    "cmu_6c1907a2_2428": ("Jidapa", "Thinoi", "jidapa.t@cmu.ac.th"),
    "cmu_582916ed_2886": ("Chanida", "Puangpila", "chanida.pu@cmu.ac.th"),
    "cmu_32a07516_3905": ("Chomanad", "Swasdimitr", "chomanad.s@cmu.ac.th"),
    "cmu_50a908ac_2745": ("Chamnan", "Randorn", "chamnan.r@cmu.ac.th"),
    "cmu_724fad24_0225": ("Thapanee", "Sarakonsri", "thapanee.s@cmu.ac.th"),
    "cmu_26c7e153_8919": ("Napapa", "Promsawan", "napapa.p@cmu.ac.th"),
    "cmu_4e834cc1_4725": ("Tinnakorn", "Kanyanee", "tinnakorn.k@cmu.ac.th"),
    "cmu_6ad70009_3416": ("Thanwadee", "Limtrakul", "thanwadee.l@cmu.ac.th"),
    "cmu_f6960165_6965": ("Thiti", "Chanphirom", "thiti.c@cmu.ac.th"),
    "cmu_d5ea9798_3957": ("Theeraboon", "Pojankarun", "theeraboon.p@cmu.ac.th"),
    "cmu_782826aa_1619": ("Nopakarn", "Chandet", "nopakarn.c@cmu.ac.th"),
    "cmu_16a4f0d3_6040": ("Nuttee", "Suree", "nuttee.s@cmu.ac.th"),
    "cmu_13b506f6_4009": ("Nawee", "Kangwan", "nawee.k@cmu.ac.th"),
    "cmu_314912f9_9422": ("Nuchnipa", "Nanthawong", "nuchnipa.n@cmu.ac.th"),
    "cmu_1719b49c_7684": ("Burapat", "Inceesungvorn", "burapat.i@cmu.ac.th"),
    "cmu_689f7995_3064": ("Praput", "Thavornyutikarn", "praput.th@cmu.ac.th"),
    "cmu_77a4ef23_8680": ("Paralee", "Waenkaew", "paralee.w@cmu.ac.th"),
    "cmu_22866f68_0268": ("Panchika", "Prangkio", "panchika.p@cmu.ac.th"),
    "cmu_5ce8e3a6_5016": ("Piyarat", "Nimmanpipak", "piyarat.n@cmu.ac.th"),
    "cmu_50b29aad_0710": ("Pattanapong", "Thangsunan", "pattanapong.t@cmu.ac.th"),
    "cmu_6a6d1838_8962": ("Pitchaya", "Mungkornasawakul", "pitchaya.m@cmu.ac.th"),
    "cmu_7a77a2e2_8013": ("Puttinan", "Meepowpan", "puttinan.m@cmu.ac.th"),
    "cmu_73085631_9589": ("Pakawan", "Puangsombat", "pakawan.p@cmu.ac.th"),
    "cmu_1cb08288_1441": ("Patnarin", "Worajittiphon", "patnarin.w@cmu.ac.th"),
    "cmu_22825acc_4319": ("Phumon", "Sookwong", "phumon.s@cmu.ac.th"),
    "cmu_72714b2e_5332": ("Pumis", "Thaptimdang", "pumis.th@cmu.ac.th"),
    "cmu_218803e4_6616": ("Mookda", "Pattarawarapan", "mookda.p@cmu.ac.th"),
    "cmu_5ffd5eaf_3834": ("Runglawan", "Somsunan", "runglawan.s@cmu.ac.th"),
    "cmu_66c5ca0b_9872": ("Laongnuan", "Srisombat", "laongnuan.sri@cmu.ac.th"),
    "cmu_7427ab26_3134": ("Wong", "Phakhodee", "wong.p@cmu.ac.th"),
    "cmu_2943756f_5566": ("Woranong", "Leewattana-phasuk", "woranong.l@cmu.ac.th"),
    "cmu_179c18fd_9460": ("Wasin", "Sombut", "wasin.s@cmu.ac.th"),
    "cmu_c217e6b5_5884": ("Wan", "Wiriya", "wan.w@cmu.ac.th"),
    "cmu_3a54a038_3756": ("Wimon", "Naksata", "wimon.n@cmu.ac.th"),
    "cmu_2b801c28_3114": ("Veasarach", "Jonjaroen", "veasarach.j@cmu.ac.th"),
    "cmu_643992d7_9545": ("Sila", "Kittiwachana", "sila.k@cmu.ac.th"),
    "cmu_5a4e874d_9643": ("Sorapong", "Chanhom", "sorapong.c@cmu.ac.th"),
    "cmu_23122f89_2559": ("Sittichai", "Wirojanupatump", "sittichai.w@cmu.ac.th"),
    "cmu_3d00ad57_5599": ("Surin", "Saipanya", "surin.s@cmu.ac.th"),
    "cmu_473ee563_1548": ("Sulawan", "Kaowphong", "sulawan.k@cmu.ac.th"),
    "cmu_3f37144d_1874": ("Saengrawee", "Sriwichai", "saengrawee.s@cmu.ac.th"),
    "cmu_368603d1_8292": ("Hataichanoke", "Niamsup", "hataichanoke.n@cmu.ac.th"),
    "cmu_67350322_0485": ("Aphinan", "Kanpiengjai", "aphinan.k@cmu.ac.th"),
    "cmu_7645de8c_5935": ("Apiwat", "Teerawutgulrag", "apiwat.t@cmu.ac.th"),
    "cmu_f692e80b_2491": ("Aroonchai", "Saiai", "aroonchai.s@cmu.ac.th"),
}

combined = {}
combined.update(PHYSICS_MAPPING)
combined.update(BIOLOGY_MAPPING)
combined.update(CHEM_MAPPING)

with open('cmu_science_raw.json', 'r', encoding='utf-8') as f:
    raw_science = json.load(f)

print(f"Total raw Science records: {len(raw_science)}")
print(f"Total compiled mappings: {len(combined)}")

final_list = []
missing = []
for r in raw_science:
    fid = r['id']
    if fid in combined:
        fn, ln, em = combined[fid]
        final_list.append({
            "id": fid,
            "full_name_th": r['full_name_th'],
            "first_name": fn,
            "last_name": ln,
            "email": em,
            "department_th": r['department_th']
        })
    else:
        missing.append(r)

print(f"Successfully mapped: {len(final_list)}/{len(raw_science)}")
if missing:
    print(f"Missing ({len(missing)}): {[m['full_name_th'] for m in missing]}")

with open('science_batch2_compiled.json', 'w', encoding='utf-8') as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)
