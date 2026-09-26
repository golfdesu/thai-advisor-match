# -*- coding: utf-8 -*-
import re

def clean_academic_title_th(raw):
    raw = raw.strip()
    raw = re.sub(r'\s+', ' ', raw)

    # Ordered longest first
    patterns = [
        (r'^(?:ศาสตราจารย์\s+ดร\.|ศ\.\s*ดร\.)\s*', 'ศ.ดร. '),
        (r'^(?:รองศาสตราจารย์\s+ดร\.|รศ\.\s*ดร\.)\s*', 'รศ.ดร. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์\s+ดร\.|ผศ\.\s*ดร\.)\s*', 'ผศ.ดร. '),
        (r'^(?:อาจารย์\s+ดร\.|อ\.\s*ดร\.)\s*', 'อ.ดร. '),
        (r'^(?:ศาสตราจารย์|ศ\.)\s*', 'ศ. '),
        (r'^(?:รองศาสตราจารย์|รศ\.)\s*', 'รศ. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*', 'ผศ. '),
        (r'^(?:อาจารย์|อ\.)\s*', 'อ. '),
    ]

    title_th = ""
    rest = raw
    for pat, norm in patterns:
        m = re.match(pat, rest)
        if m:
            title_th = norm.strip()
            rest = rest[m.end():].strip()
            break

    # split rest into first and last name
    parts = rest.split()
    first_th = parts[0] if parts else ""
    last_th = " ".join(parts[1:]) if len(parts) > 1 else ""

    full_th = f"{title_th} {first_th} {last_th}".strip() if title_th else f"{first_th} {last_th}".strip()
    return title_th, first_th, last_th, full_th

def clean_name_en(raw, first_th="", last_th=""):
    raw = raw.strip()
    # Strip credential suffixes
    raw = re.sub(r',\s*(?:Ph\.?D\.?|M\.?D\.?|D\.?Phil\.?|Ed\.?D\.?|D\.?B\.?A\.?|M\.?A\.?|M\.?Sc\.?|B\.?A\.?|B\.?Sc\.?).*$', '', raw, flags=re.I)
    raw = re.sub(r'\s+(?:Ph\.?D\.?|D\.?Phil\.?|Ed\.?D\.?)\b.*$', '', raw, flags=re.I)

    # Strip prefixes
    prefixes = [
        r'^(?:Assistant\s+Professor\s+Dr\.|Asst\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor\s+Dr\.|Assoc\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Professor\s+Dr\.|Prof\.\s*Dr\.)\s*',
        r'^(?:Lecturer\s+Dr\.|Instructor\s+Dr\.)\s*',
        r'^(?:Assistant\s+Professor|Asst\.\s*Prof\.)\s*',
        r'^(?:Associate\s+Professor|Assoc\.\s*Prof\.)\s*',
        r'^(?:Professor|Prof\.)\s*',
        r'^(?:Lecturer|Instructor)\s*',
        r'^(?:Dr\.)\s*',
    ]

    title_en = ""
    rest = raw
    for pat in prefixes:
        m = re.match(pat, rest, re.I)
        if m:
            rest = rest[m.end():].strip()
            break

    parts = rest.split()
    if len(parts) >= 2:
        first_en = parts[0].strip().capitalize()
        last_en = " ".join(p.capitalize() for p in parts[1:]).strip()
    elif len(parts) == 1:
        first_en = parts[0].strip().capitalize()
        last_en = ""
    else:
        first_en, last_en = "", ""

    return first_en, last_en

# Test cases
samples = [
    ("อาจารย์ ดร. สิริชญา คอนกรีต", "Instructor SIRICHAYA CORNGREAT, Ph.D."),
    ("ผู้ช่วยศาสตราจารย์ ดร.บารมี เขียววิชัย", "Assistant Professor BARAMEE KHEOVICHAI, Ph.D."),
    ("รองศาสตราจารย์ ดร.วรางคณา นิพัทธ์สุขกิจ", "Associate Professor Warangkana Nibhatsukit, Ph.D."),
    ("อาจารย์สกนธ์ ม่วงสุน", "Instructor Sakon Muangsun"),
    ("ผู้ช่วยศาสตราจารย์ตะวัน วรรณรัตน์", "Assistant Professor Tawan Wanarat"),
]

for th, en in samples:
    t_th, f_th, l_th, full_th = clean_academic_title_th(th)
    f_en, l_en = clean_name_en(en)
    print(f"TH: [{t_th}] [{f_th}] [{l_th}] -> '{full_th}'")
    print(f"EN: [{f_en}] [{l_en}]")
    print("---")
