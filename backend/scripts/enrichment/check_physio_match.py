# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('cmu_med_raw.json', 'r', encoding='utf-8') as f:
    raw_med = json.load(f)

physio = [r for r in raw_med if r['department_th'] == 'ภาควิชาสรีรวิทยา']
print(f"Physiology DB records: {len(physio)}")

PHYSIO_MAP = {
    "จันทิมา ปลื้มสำราญ": ("Juntima", "Pleumsamran", "juntima.p@cmu.ac.th"),
    "จิรภาส ศรีเพชรวรรณดี": ("Jirapas", "Sripetchwandee", "jirapas.sripetch@cmu.ac.th"),
    "จิราภรณ์ โตจรัส": ("Jiraporn", "Tocharus", "jiraporn.tocharus@cmu.ac.th"),
    "ชนิศา โทนุสิน": ("Chanisa", "Thonusin", "chanisa.t@cmu.ac.th"),
    "ชุติมา ศรีมะเริง วรรธนะภูติ": ("Chutima", "Srimaroeng Vaddhanaphuti", "chutima.srimaroeng@cmu.ac.th"),
    "ณัฐยาภรณ์ อภัยใจ": ("Nattayaporn", "Apaijai", "nattayaporn.a@cmu.ac.th"),
    "นริศรา ไล้เลิศ": ("Narissara", "Lailerd", "narissara.lailerd@cmu.ac.th"),
    "พงศ์สันติ์ ใยเจริญ": ("Pongson", "Yaicharoen", "pongson.y@cmu.ac.th"),
    "ภูเนตร วีรธีรางกูร": ("Punate", "Weerateerangkul", "punate.w@cmu.ac.th"),
    "รัฐพงศ์ สังข์หนุน": ("Rattapong", "Sungnoon", "rattapong.s@cmu.ac.th"),
    "วาสนา ปรัชญาสกุล": ("Wasana", "Pratchayasakul", "wasana.pratcha@cmu.ac.th"),
    "ศิรินาฎ คำฟู": ("Sirinart", "Kumfu", "sirinart.kum@cmu.ac.th"),
    "สลิล มิ่งมาลัยรักษ์": ("Salin", "Mingmalairak", "salin.mingmalairak@cmu.ac.th"),
    "อนุสรณ์ พรสินธุเศรษฐ์": ("Anusorn", "Pornsinthusate", "anusorn.lungka@cmu.ac.th"),
}

TITLE_REGEX = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.)\s*'
    r'(?:ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.)*\s*'
    r'(?:ดร\.)*\s*'
)

for p in physio:
    clean = TITLE_REGEX.sub('', p['full_name_th']).strip()
    if clean in PHYSIO_MAP:
        fn, ln, em = PHYSIO_MAP[clean]
        print(f"  [OK] {p['full_name_th']} -> {fn} {ln} ({em})")
    else:
        print(f"  [MISSING] {p['full_name_th']} (clean='{clean}')")
