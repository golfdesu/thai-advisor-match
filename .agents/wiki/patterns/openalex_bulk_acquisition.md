# OpenAlex Bulk Faculty Acquisition Runbook

> **อ่านก่อนทำงาน:** เอกสารนี้บันทึกวิธีดึงข้อมูลอาจารย์ไทยปริมาณมากด้วย OpenAlex API
> ผลจริง: Wave 58 ดึง 6 มหาลัย ได้ **58,439 records ใน ~45 นาที**

---

## ทำไมต้องใช้ OpenAlex (ไม่ใช่ Crawl เว็บมหาลัย)

| | Crawl เว็บมหาลัย | OpenAlex API |
|---|---|---|
| ความเร็ว | ช้า (1–5 records/วินาที) | เร็วมาก (200 records/request) |
| ปริมาณ | ไม่กี่ร้อย–ไม่กี่พัน | หลายพัน–หลายหมื่น/มหาลัย |
| ความเสถียร | เปลี่ยน HTML บ่อย | API มี versioning |
| email | มี | ไม่มี (ต้อง crawl เพิ่ม) |
| ข้อมูล research | ไม่มี | มี: citation, h-index, topics |

ข้อจำกัด OpenAlex: มีแค่คนที่เคย **publish งานวิจัย** เท่านั้น อาจารย์ที่สอนอย่างเดียวจะไม่มีใน OpenAlex

---

## ขั้นตอนที่ 1 — หา Institution ID

OpenAlex ระบุมหาวิทยาลัยด้วย Institution ID รูปแบบ `I<number>` ต้องหาก่อนทุกครั้ง **ห้ามเดา**

ค้นหาผ่าน endpoint:
```
GET https://api.openalex.org/institutions?search=Chulalongkorn+University
```

ทดสอบ ID ก่อนใช้งานจริง (`per-page=1` ดูว่ามี authors ไหม):
```
GET https://api.openalex.org/authors?filter=affiliations.institution.id:I158708052&per-page=1
```
ถ้า `meta.count = 0` แปลว่า ID ผิด — ต้องหาใหม่

### Institution IDs ที่ตรวจสอบแล้ว (2026-09)

```python
THAI_UNIVERSITIES = [
    {"en": "Chulalongkorn University",                              "openalex_id": "I158708052"},
    {"en": "Mahidol University",                                    "openalex_id": "I114027177"},
    {"en": "Chiang Mai University",                                 "openalex_id": "I110747655"},
    {"en": "Kasetsart University",                                  "openalex_id": "I168746847"},
    {"en": "Khon Kaen University",                                  "openalex_id": "I179193067"},
    {"en": "Thammasat University",                                  "openalex_id": "I108108428"},
    {"en": "Prince of Songkla University",                          "openalex_id": "I131868736"},
    {"en": "King Mongkut's Institute of Technology Ladkrabang",     "openalex_id": "I91538806"},
    {"en": "King Mongkut's University of Technology Thonburi",      "openalex_id": "I116101508"},
    {"en": "King Mongkut's University of Technology North Bangkok", "openalex_id": "I62343571"},
    {"en": "Silpakorn University",                                  "openalex_id": "I86677382"},
    {"en": "Naresuan University",                                   "openalex_id": "I120651893"},
    {"en": "Suranaree University of Technology",                    "openalex_id": "I96915999"},
    {"en": "Srinakharinwirot University",                           "openalex_id": "I154478539"},
    {"en": "Burapha University",                                    "openalex_id": "I129488602"},
    {"en": "Walailak University",                                   "openalex_id": "I96916377"},
    {"en": "Ubon Ratchathani University",                           "openalex_id": "I72091625"},
    {"en": "University of Phayao",                                  "openalex_id": "I4210090662"},
    {"en": "Mahasarakham University",                               "openalex_id": "I173726621"},
    {"en": "Ramkhamhaeng University",                               "openalex_id": "I58196637"},
    {"en": "Maejo University",                                      "openalex_id": "I4210168903"},
    {"en": "Thaksin University",                                    "openalex_id": "I79246082"},
    {"en": "Mae Fah Luang University",                              "openalex_id": "I4210116829"},
    # CRU: umbrella ID I4405255716 คือ 0 authors — ใช้ sub-institution แทน
    {"en": "Chulabhorn Research Institute",                         "openalex_id": "I39737112"},
    {"en": "Chulabhorn Graduate Institute",                         "openalex_id": "I2799959951"},
    {"en": "Chulabhorn Hospital",                                   "openalex_id": "I4210106686"},
]
```

> **ข้อควรระวัง:** บางมหาลัยมีหลาย ID (umbrella + sub-institutions) เช่น ราชวิทยาลัยจุฬาภรณ์
> umbrella ID `I4405255716` ให้ผล 0 authors ต้องใช้ 3 sub-institution ID แทน
> ตรวจสอบด้วย `per-page=1` ก่อนเสมอ

---

## ขั้นตอนที่ 2 — ดึง Authors ด้วย Cursor Pagination

OpenAlex ใช้ cursor-based pagination รองรับสูงสุด 200 records/request, cap 10,000 records/institution

```python
import urllib.request
import urllib.parse
import json
import time

def fetch_openalex_authors(institution_id: str) -> list[dict]:
    results = []
    cursor = "*"          # เริ่มต้นด้วย * เสมอ
    pages = 0

    while cursor:
        params = urllib.parse.urlencode({
            "filter": f"affiliations.institution.id:{institution_id}",
            "select": (
                "id,display_name,last_known_institutions,topics,"
                "cited_by_count,works_count,summary_stats"
            ),
            "per-page": "200",
            "cursor": cursor,
            "mailto": "your@email.com",   # ใส่เพื่อเข้า polite pool (~100k req/day)
        })
        url = f"https://api.openalex.org/authors?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "YourBot/1.0"})

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())

        results.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")   # None = หมดแล้ว
        pages += 1

        time.sleep(0.3)   # polite delay — ป้องกัน rate limit

        if pages >= 60 or not cursor:   # 60 pages x 200 = 12,000 max
            break

    return results
```

**fields ที่ได้:**

| field | ความหมาย |
|---|---|
| `id` | URL เช่น `https://openalex.org/A123456` — ตัดเอา `A123456` เป็น openalex_id |
| `display_name` | ชื่อเต็ม (อังกฤษเป็นหลัก) |
| `topics[].display_name` | สาขาวิจัย เช่น `["Machine Learning", "Bioinformatics"]` |
| `cited_by_count` | citation ตลอดชีพ |
| `works_count` | จำนวนงานวิจัยทั้งหมด |
| `summary_stats.h_index` | h-index |

---

## ขั้นตอนที่ 3 — Circuit Breaker สำหรับ Rate Limit

```python
import urllib.error

def fetch_with_circuit_breaker(url: str) -> dict | None:
    consecutive_429 = 0

    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "YourBot/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = min(180, 30 * (consecutive_429 + 1))  # 30→60→90→max 180s
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                consecutive_429 += 1
                if consecutive_429 >= 6:
                    print("Persistent rate limit — skipping university")
                    return None
            else:
                return None

        except Exception as e:
            time.sleep(2)

    return None
```

---

## ขั้นตอนที่ 4 — Parallel Embedding Generation

ดึง OpenAlex sequential ทีละมหาลัย แต่ generate embedding แบบ parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def generate_embedding(text: str) -> list[float]:
    # ใช้ Gemini / OpenAI / sentence-transformers
    # ถ้า quota หมด: return [0.0] * 768
    ...

texts = [f"{r['display_name']} {topics}" for r in records]

with ThreadPoolExecutor(max_workers=5) as executor:
    embeddings = list(executor.map(generate_embedding, texts))
```

**Embedding circuit breaker:** ถ้า Gemini ตอบ 429 ติดกัน 3 ครั้ง ให้ fallback เป็น `[0.0] * 768` ทันที อย่าให้ block pipeline

---

## ขั้นตอนที่ 5 — Deduplication 5-Pass (ก่อน Insert)

```python
from rapidfuzz import fuzz

def deduplicate(new_records: list[dict], existing: list[dict]) -> list[dict]:
    # สร้าง lookup จาก existing records
    by_openalex = {r["openalex_id"]: True for r in existing if r.get("openalex_id")}
    by_name_th  = {r["full_name_th"].lower(): True for r in existing if r.get("full_name_th")}
    by_name_en  = {r["full_name_en"].lower(): True for r in existing if r.get("full_name_en")}

    to_insert = []
    seen_batch: set[str] = set()

    for rec in new_records:
        opx     = rec.get("openalex_id", "")
        name_th = rec.get("full_name_th", "").lower()
        name_en = rec.get("full_name_en", "").lower()
        key     = opx or name_th or name_en

        # Pass 1: OpenAlex ID ตรง
        if opx and opx in by_openalex:
            continue
        # Pass 2: ชื่อไทยตรง
        if name_th and name_th in by_name_th:
            continue
        # Pass 3: ชื่ออังกฤษตรง
        if name_en and name_en in by_name_en:
            continue
        # Pass 4: RapidFuzz fuzzy (threshold 90)
        matched = any(fuzz.token_set_ratio(name_en, n) >= 90 for n in by_name_en)
        if matched:
            continue
        # Pass 5: ซ้ำใน batch ปัจจุบัน
        if key in seen_batch:
            continue

        seen_batch.add(key)
        to_insert.append(rec)

    return to_insert
```

---

## ขั้นตอนที่ 6 — Checkpoint + Commit DB

```python
import json
from pathlib import Path

CHECKPOINT_DIR = Path("backend/data/agent_states")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# 1. บันทึก raw records ก่อนทุกครั้ง
ckpt = CHECKPOINT_DIR / "waveXX_<prefix>_extraction.json"
with open(ckpt, "w", encoding="utf-8") as f:
    json.dump(raw_records, f, ensure_ascii=False, indent=2)

# 2. commit DB เป็น batch 300 records
for i in range(0, len(new_objects), 300):
    db.add_all(new_objects[i : i + 300])
    db.commit()
```

ถ้า script crash ให้ load checkpoint แล้ว resume จาก `to_insert` ที่ยังไม่ได้ commit โดยไม่ต้อง re-fetch

---

## ข้อมูลที่ OpenAlex ไม่มี — ต้อง Crawl เว็บมหาลัยเพิ่ม

| ข้อมูล | วิธีดึงเพิ่ม |
|---|---|
| Email | Crawl หน้า faculty directory ของมหาลัย |
| รูปภาพ | Crawl หน้า profile ของอาจารย์แต่ละคน |
| ชื่อภาษาไทย | Crawl หน้า profile หรือ match จาก directory |
| ภาควิชา | Crawl จาก URL structure ของ faculty directory |

**Email**: ใช้ regex `[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}` แล้ว validate domain ให้ตรงกับมหาลัย เช่น `@chula.ac.th`, `@kku.ac.th` เท่านั้น อย่า accept freemail (gmail, hotmail)

---

## สรุป Full Pipeline

```
สำหรับแต่ละมหาวิทยาลัย:
1. หา institution_id → ทดสอบด้วย per-page=1
2. fetch_openalex_authors() → cursor pagination 200/req, max 60 pages
3. circuit breaker → 429 backoff 30s→60s→90s→180s
4. checkpoint raw records → disk (waveXX_<prefix>_extraction.json)
5. deduplicate 5-pass → กรองซ้ำกับ existing DB
6. generate embeddings → ThreadPoolExecutor parallel, fallback [0.0]*768
7. commit DB → batch 300/commit
8. inter-university cooldown → 10s (90s ถ้าได้ 0 authors)

ขั้นตอนแยก (ทำหลัง):
9. crawl faculty directory → ดึง email, รูป, ชื่อไทย, ภาควิชา
```

---

## ผลจริงจากโปรเจกต์ (Wave 58, 2026-09)

| มหาวิทยาลัย | OpenAlex ID | ก่อน | หลัง | เพิ่ม |
|---|---|---|---|---|
| Khon Kaen University | I179193067 | 942 | 12,130 | +11,188 |
| Thammasat University | I108108428 | 1,101 | 11,427 | +10,326 |
| Chulalongkorn University | I158708052 | 2,355 | 13,147 | +10,792 |
| Silpakorn University | I86677382 | 678 | 4,862 | +4,184 |
| Prince of Songkla University | I131868736 | 742 | 12,385 | +11,643 |
| KMITL | I91538806 | 856 | 9,734 | +8,878 |
| **รวม Wave 58** | | **6,674** | **63,685** | **+58,439** |

เวลารวม: ~45 นาที
