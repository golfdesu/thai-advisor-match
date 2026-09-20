# -*- coding: utf-8 -*-
import urllib.request
import json
import ssl
import urllib.parse
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 mailto:admin@advisor-match.th'}

CHEM_NAMES = [
    ("กรธัช อุ่นนันกาศ", "Kornthach", "Ounnunkad", "kornthach.o@cmu.ac.th"),
    ("กฤษณะ จิตมณี", "Kritsana", "Jitmanee", "kritsana.j@cmu.ac.th"),
    ("ก้องเกียรติ ไตรสุวรรณ", "Kongkiat", "Trisuwan", "kongkiat.t@cmu.ac.th"),
    ("กัลยาวัสถ์ วังคะวงษ์", "Kanlayawat", "Wangkawong", "kanlayawat.w@cmu.ac.th"),
    ("กาญจนา ดำริห์", "Kanchana", "Damri", "kanchana.d@cmu.ac.th"),
    ("กิตติพันธ์ ศิวะวรรณพงศ์", "Kittipan", "Sivawannapong", "kittipan.s@cmu.ac.th"),
    ("กุลภา ชนะวรรโณ", "Kullapa", "Chanawanno", "kullapa.c@cmu.ac.th"),
    ("เกียรติคุณ มะโนเครื่อง", "Kiattikhun", "Manokruang", "kiattikhun.m@cmu.ac.th"),
    ("คณารัฐ ณ ลำปาง", "Kanarat", "Nalampang", "kanarat.n@cmu.ac.th"),
    ("จิดาภา ทิน้อย", "Jidapa", "Thinoi", "jidapa.t@cmu.ac.th"),
    ("ชนิดา พวงพิลา", "Chanida", "Puangpila", "chanida.pu@cmu.ac.th"),
    ("ชมนาด สวาสดิ์มิตร", "Chomanad", "Swasdimitr", "chomanad.s@cmu.ac.th"),
    ("ชำนาญ ราญฎร", "Chamnan", "Randorn", "chamnan.r@cmu.ac.th"),
    ("ฐปนีย์ สารครศรี", "Thapanee", "Sarakonsri", "thapanee.s@cmu.ac.th"),
    ("ณปภา พรหมสวรรค์", "Napapa", "Promsawan", "napapa.p@cmu.ac.th"),
    ("ทินกร กันยานี", "Tinnakorn", "Kanyanee", "tinnakorn.k@cmu.ac.th"),
    ("ธัญวดี ลิ้มธรากุล", "Thanwadee", "Limtrakul", "thanwadee.l@cmu.ac.th"),
    ("ธิติ จันทร์ภิรมย์", "Thiti", "Chanphirom", "thiti.c@cmu.ac.th"),
    ("ธีรบุญ พจนการุณ", "Theeraboon", "Pojankarun", "theeraboon.p@cmu.ac.th"),
    ("นพกาญจน์ จันทร์เดช", "Nopakarn", "Chandet", "nopakarn.c@cmu.ac.th"),
    ("นัทธี สุรีย์", "Natthee", "Suree", "natthee.s@cmu.ac.th"),
    ("นาวี กังวาลย์", "Nawee", "Kangwan", "nawee.k@cmu.ac.th"),
    ("นุชนิภา นันทะวงศ์", "Nuchnipa", "Nanthawong", "nuchnipa.n@cmu.ac.th"),
    ("บูรภัทร์ อินทรีย์สังวร", "Burapat", "Inceesungvorn", "burapat.i@cmu.ac.th"),
    ("ประพุทธ์ ถาวรยุติการต์", "Praput", "Thavornyutikarn", "praput.th@cmu.ac.th"),
    ("ปะราลี แว่นแก้ว", "Paralee", "Waenkaew", "paralee.w@cmu.ac.th"),
    ("ปัญชิกา ปรังเขียว", "Panchika", "Prangkio", "panchika.p@cmu.ac.th"),
    ("ปิยรัตน์ นิมมานพิภักดิ์", "Piyarat", "Nimmanpipak", "piyarat.n@cmu.ac.th"),
    ("พัฒนพงศ์ ทังสุนันท์", "Pattanapong", "Thangsunan", "pattanapong.t@cmu.ac.th"),
    ("พิชญา มังกรอัศวกุล", "Pitchaya", "Mungkornasawakul", "pitchaya.m@cmu.ac.th"),
    ("พุฒินันท์ มีเผ่าพันธ์", "Puttinan", "Meepowpan", "puttinan.m@cmu.ac.th"),
    ("ภควรรณ พวงสมบัติ", "Pakawan", "Puangsombat", "pakawan.p@cmu.ac.th"),
    ("ภัทร์นฤน วรจิตติพล", "Patnarin", "Worajittiphon", "patnarin.w@cmu.ac.th"),
    ("ภูมน สุขวงศ์", "Phumon", "Sookwong", "phumon.s@cmu.ac.th"),
    ("ภูมิศร์ ทับทิมแดง", "Pumis", "Thaptimdang", "pumis.th@cmu.ac.th"),
    ("มุกดา ภัทราวราพันธ์", "Mookda", "Pattarawarapan", "mookda.p@cmu.ac.th"),
    ("รุ้งลาวัลย์ สมสุนันท์", "Runglawan", "Somsunan", "runglawan.s@cmu.ac.th"),
    ("ละอองนวล ศรีสมบัติ", "Laongnuan", "Srisombat", "laongnuan.sri@cmu.ac.th"),
    ("วงศ์ พะโคดี", "Wong", "Phakhodee", "wong.p@cmu.ac.th"),
    ("วรอนงค์ ลี้วัฒนาผาสุข", "Woranong", "Leewattana-phasuk", "woranong.l@cmu.ac.th"),
    ("วศิน สมบุตร", "Wasin", "Sombut", "wasin.s@cmu.ac.th"),
    ("ว่าน วิริยา", "Wan", "Wiriya", "wan.w@cmu.ac.th"),
    ("วิมล นาคสาทา", "Wimon", "Naksata", "wimon.n@cmu.ac.th"),
    ("เวสารัช จรเจริญ", "Veasarach", "Jorncharoen", "veasarach.j@cmu.ac.th"),
    ("ศิลา กิตติวัชนะ", "Sila", "Kittiwachana", "sila.k@cmu.ac.th"),
    ("สรพงษ์ จันทร์หอม", "Sorapong", "Chanhom", "sorapong.c@cmu.ac.th"),
    ("สิทธิชัย วิโรจนุปถัมภ์", "Sittichai", "Wirojanupatump", "sittichai.w@cmu.ac.th"),
    ("สุรินทร์ สายปัญญา", "Surin", "Saipanya", "surin.s@cmu.ac.th"),
    ("สุลาวัลย์ ขาวผ่อง", "Sulawan", "Khaophong", "sulawan.k@cmu.ac.th"),
    ("แสงรวี ศรีวิชัย", "Saengrawee", "Sriwichai", "saengrawee.s@cmu.ac.th"),
    ("หทัยชนก เนียมทรัพย์", "Hataichanoke", "Niamsup", "hataichanoke.n@cmu.ac.th"),
    ("อภินันท์ กันเปียงใจ", "Aphinan", "Kanpiengjai", "aphinan.k@cmu.ac.th"),
    ("อภิวัฒน์ ธีรวุฒิกุลรักษ์", "Apiwat", "Teerawutgulrag", "apiwat.t@cmu.ac.th"),
    ("อรุณฉาย สายอ้าย", "Aroonchai", "Saiai", "aroonchai.s@cmu.ac.th"),
]

verified_chem = []
for th_name, fn, ln, em in CHEM_NAMES:
    query = f"{fn} {ln}"
    url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(query)}&rows=5"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        items = data.get('message', {}).get('items', [])
        found = False
        top_title = "None"
        cites = 0
        for it in items:
            authors = [a.get('family', '').lower() for a in it.get('author', [])]
            if ln.lower() in authors:
                found = True
                top_title = it.get('title', [''])[0]
                cites = it.get('is-referenced-by-count', 0)
                break
        print(f"[{'OK' if found else '??'}] {th_name} -> {fn} {ln} | match={found} | '{top_title[:45]}' (cites={cites})")
        verified_chem.append({'th_name': th_name, 'first_name': fn, 'last_name': ln, 'email': em, 'found': found, 'cites': cites})
    except Exception as e:
        print(f"[ERR] {th_name} -> {e}")

print(f"\nChemistry Summary: {sum(1 for v in verified_chem if v['found'])}/{len(verified_chem)} verified with Crossref publications")
with open('chem_verified.json', 'w', encoding='utf-8') as f:
    json.dump(verified_chem, f, ensure_ascii=False, indent=2)
