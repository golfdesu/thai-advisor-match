# ภารกิจที่ 5: ค้นหาอาจารย์ที่เก่งและเติมเต็มสาขาที่ขาด "ตัวท็อปงานวิจัย" (Elite Researcher Discovery & Gap Fix)

> **ความสำคัญ:** 🔥 ระดับ 1–2 (เชื่อมโยงกับภารกิจ 2 และ 3)
> **บันทึกเมื่อ:** 10 กันยายน 2569
> **ฐานข้อมูลที่ใช้ตรวจ:** Local Docker PostgreSQL (`localhost:5432 / advisor_match`) — อาจารย์ 5,587 คน (ณ วันเปิดภารกิจ; **ปัจจุบัน 5,685 คน** หลัง Batches 98–101 + dedup)
> **สคริปต์ audit ที่สร้างไว้:**
> - `backend/scripts/audits/field_coverage_gap_analysis.py` (สาขาไหนอาจารย์น้อย)
> - `backend/scripts/audits/field_taxonomy.py` (taxonomy 57 สาขา — shared)
> - `backend/scripts/audits/elite_researcher_gap.py` (สาขาไหนขาดตัวท็อป)

---

## 1. สรุปสถานะข้อมูลวิจัยในปัจจุบัน (อัปเดตหลัง dedup 10 ก.ย.)

| เมตริก | ค่า |
| :--- | :---: |
| อาจารย์ทั้งหมด | เดิม **5,497** → ปัจจุบัน **5,685 คน** (Batches 98–101 +322 academic ใหม่, dedup --by-name ลบซ้ำ 283 แถว) |
| มี `h_index` > 0 | **2,030 คน (35.7%)** — wave 1 ได้ +227 แต่ dedup ด้วยชื่อกลบบางแถวที่ donor มี h เล็กน้อย (2,050 → 2,030); OpenAlex wave 2 คิวรอ quota → เป้า 50%+ ยังต้องทำต่อ |
| มี `total_citations` | ~2,000 คน |
| มี `featured_publications` | 1,750 → **2,413 คน (42.4%)** — ThaiJO waves 1–4 (+~900) และ TU Law curated (+188 รายการ) |
| **ไม่มีข้อมูลวิจัยเลย** | `openalex_id IS NULL` เหลือ **2,093 แถว** (ยังไม่ attempt — resume ได้) |
| h-index เฉลี่ย (ที่มีข้อมูล) | 14.1 |
| h-index สูงสุด | 121 (Michael Doyle, จุฬาฯ เคมี) |

**Bias สำคัญ:** OpenAlex enrichment ที่ทำไปมัก match ได้แค่ STEM/วิทย์สุขภาพ (ชื่ออังกฤษ) ส่วนสายสังคมฯ/มนุษยศาสตร์ที่ publish ใน ThaiJO ยังไม่ถูกเชื่อม citation — ดูสคริปต์ `enrich_thaijo_publications.py` ว่ารันถึงไหน

## 2. 🏆 อาจารย์ตัวท็อปปัจจุบัน (จะใช้ทำ "Distinguished Advisors" ได้ทันที)

| อาจารย์ | มหาลัย | h-index | Citations | สาขา |
| :--- | :--- | ---: | ---: | :--- |
| Michael Doyle | จุฬาฯ | 121 | 88,361 | เคมี/เภสัช |
| ศ.ดร. สุทธวัฒน์ เบญจกุล | สงขลานครินทร์ | 117 | 61,450 | ชีวเคมี/โรคเขตร้อน |
| ผศ.ดร. ชญานิษฐ์ อัศวตั้งตระกูลดี | จุฬาฯ | 108 | 41,864 | เภสัช |
| ผศ. ภญ. เจนนิ | จุฬาฯ | 102 | 37,089 | เภสัช |
| ศ.ดร. สมชาย วงศ์วิเศษ | สจล.ลาดกระบัง | 101 | 42,309 | วัสดุ/พลังงาน |
| ผศ. วฤทธิ์ มิตรธรรมศิริ | มหิดล | 98 | 39,130 | แพทย์ |
| ศ.ดร. ปริญญา จินดาประเสริฐ | ม.ขอนแก่น | 92 | 32,737 | แพทย์ |
| ศ.ดร. Philip Hallinger | มหิดล | 86 | 31,192 | การศึกษา (หายากในสายสังคมฯ) |
| ศ.ดร. เมธา วรรณพัฒน์ | ม.ขอนแก่น | 49 | 9,558 | สัตวแพทย์ |

## 3. 🚨 สาขาที่ Demand สูงมาก แต่ "อาจารย์เก่ง" ใน DB แทบไม่มี (Priority Gap)

เทียบกับ demand จาก MHESI (นศ.ใหม่ ป.โท ปีการศึกษา 2568 ภาค 1 = 40,029 คน/ปี, แหล่ง: `info.mhesi.go.th/stat_std_new.php`)

| สาขา | Demand ป.โท/ปี | อาจารย์ใน DB | อาจารย์ h≥20 | สถานะ (อัปเดต 10 ก.ย. หลังขั้นที่ 3) |
| :--- | ---: | ---: | ---: | :--- |
| **ศึกษาศาสตร์ + ครุศาสตร์** | ~7,254 | 206 → **340** | 0 (max h=18) | 🟡 ครอบคลุม roster แล้ว (SWU+SSRU+CU) — ตัวท็อปไทยไม่มีใน OpenAlex จริง, มีผลงาน 205 คน |
| **รัฐประศาสนศาสตร์ (รป.ม.)** | ~2,830 | 70 → 67* | **1** (max h=77) | 🟡 *หลัง dedup; มีตัวท็อปแล้ว 1 |
| **นิติศาสตร์** | ~1,622 | 282 → **328** | 0 (max h=7) | 🟡 มี curated pubs **188 รายการ** (TU Law) — ตัวจริงคือ ThaiJO ไม่ใช่ h |
| **พยาบาลศาสตร์** | ~1,534 | 250 | 6 | 🟡 ขาดตัวท็อป |
| **สาธารณสุขศาสตร์** | ~1,428 | 233 | 6 | 🟡 ขาดตัวท็อป |
| **รัฐศาสตร์** | ~1,331 | 199 | 1 | 🟡 |
| **ท่องเที่ยว/โรงแรม** | สูงต่อเนื่อง | 77 | 0 | ⚫ **ข้าม** — แหล่ง tourism ทุกแห่ง ConnectError (ตรวจสอบซ้ำ 10 ก.ย.) |
| **การตลาด/บริหารธุรกิจ** | สูง (ภาคีบริหารฯ) | 95 → **149** | 0 → **4** (max h=37) | ✅ **ปิดแล้ว** — TBS 102 คน (Batch 101) มีตัวท็อป h≥20 ครั้งแรก |
| **Cybersecurity** | ตลาดแรงงานสูงมาก | 85 | 2 | ⚫ **ข้าม** — SIT/FIBO เข้าไม่ได้; รายการเดิม ingested หมดแล้ว |
| **HCI / UX** | ตลาดแรงงานสูง | 39 | 0 | ⚫ **ข้าม** — ไม่มีแหล่ง reachable |
| **Educational Technology** | ตลาดแรงงานสูง | 20 | 0 | 🔴 |
| **Logistics / Supply Chain** | ตลาดแรงงานสูง | 85 | 0 | 🔴 |
| **สถาปัตยกรรมศาสตร์** | ~202 | 82 | 0 | 🔴 h สูงสุดแค่ 4 |
| **จิตวิทยา** | — | 166 | 0 | 🔴 h สูงสุดแค่ 6 |
| **ประวัติศาสตร์/โบราณคดี** | — | 60 | 0 | 🔴 |

สาขาที่มีตัวท็อปแน่นอยู่แล้ว (ไม่ต้องเร่ง): ชีวเทค/ชีวเคมี (26 คน h≥40), แพทย์ (18), พลังงาน (13), โยธา (9), เคมี (3), วัสดุ (2)

## 4. 🐛 ปัญหา Data Quality ที่ค้นพบตอน audit (ต้องแก้ก่อนจัดอันดับ)

1. **ยศซ้ำในชื่อ (5,409 แถว = 97%!)** — `full_name_th` เก็บยศซ้ำกับ `academic_title_th`
   เช่น `academic_title_th='ศ.ดร.'` + `full_name_th='ศ.ดร. สุทธิเขตต์ นาคะเสถียร'` → ตอน render จะโชว์ "ศ.ดร.ศ.ดร. สุทธิเขตต์..."
   **ทางแก้:** ตอนแสดงผล/สร้าง card ให้ strip title ออกจาก `full_name_th` ก่อน หรือ normalize ทั้ง column
2. **อาจารย์ซ้ำข้ามมหาลัย** — เจอเคส "บิน จ้าว" (h=87, cit=22,690) ซ้ำทั้ง มธ. และ จุฬาฯ พร้อม id ต่างกัน
   **ทางแก้:** รัน dedup ด้วย OpenAlex ID + fuzzy name (RapidFuzz) — ดู `disambiguate_faculties.py`
3. **750 คน ไม่สามารถจัดสาขาได้** (จาก 5,587) เพราะไม่มี research_interests / department คลุมเครือ

## 5. 🐛 ปัญหา Backend: `_fetch_distinguished_advisors` ไม่ได้จัดอันดับด้วยความเก่ง

ไฟล์: `backend/app/api/routes_universities.py` (ฟังก์ชัน `_fetch_distinguished_advisors`)
ปัจจุบันแค่ดึง 25 คนแรกที่มี `research_interests` แล้วคัด 5 คณะแรก — **ไม่ใช้ h_index/citations เลย**
→ หน้าแรกของมหาลัยจึงโชว์ "อาจารย์โดดเด่น" ที่จริงเป็นแค่ลำดับการ insert

**Quick Win (แก้เล็ก ผลชัด):** เปลี่ยน ORDER เป็น
```python
.order_by(FacultyDB.h_index.desc().nullslast(), FacultyDB.total_citations.desc().nullslast())
```
แล้วคงกลไกกระจายหลายคณะ (seen_departments) เดิมไว้

## 6. แผนปฏิบัติการ (ทำเป็นลำดับ)

### ขั้นที่ 1 — Quick Wins (แก้โค้ด ไม่ต้อง scrape) ✅ เสร็จแล้ว 10 ก.ย. 2569
- [x] แก้ `_fetch_distinguished_advisors` ให้ ORDER BY h_index DESC NULLS LAST → `routes_universities.py` (ยืนยัน: จุฬาฯ โชว์ Doyle h=121 → ชญานิษฐ์ h=108 → เจนนิ h=102 → บิน จ้าว h=87 → อรวรรณ h=75)
- [x] แก้ render ยศซ้ำ (strip title ที่ Pydantic DTO — `schema.py` `_clean_display_name` + model_validator ทั้ง FacultyMember/FacultyCardSchema; ทดสอบ 433/500 แถวที่ยศซ้ำ → เหลือ 0)
- [x] Dedup ด้วย `openalex_id` → สร้าง `scripts/audits/merge_duplicate_faculties.py` (dry-run + --apply); รันแล้ว 5,587 → **5,497** (ลบ 90 แถวซ้ำจาก 89 กลุ่ม same-uni; เก็บ 12 กลุ่มข้ามมหาลัยไว้เป็น dual affiliation; re-point research_labs refs อัตโนมัติ; embedding ไม่มี NULL ค้าง)
- [x] 🐛 พบเพิ่ม: `/search/cold-email` พัง 100% (`req.degree_level`/`req.thesis_topic` ไม่มีใน ColdEmailRequest) — แก้เป็น `intended_degree`/`research_topic` แล้ว (test_search ผ่าน 11/11 ยกเว้นเทสต์ที่พังมาก่อน)
- [x] 🐛 พบเพิ่ม: แล็บ 5 แห่ง lead_advisor_id ชี้ id ที่ไม่มีตัวตน (`ku_agro_001` ฯลฯ) — re-point ไปอาจารย์สาขาตรง h-index สูงสุดแล้ว (cassava→สโรจน์ รอดคืน h=48, smart-agri→พีระศักดิ์ ศรีนิเวศน์ h=39, MFU cosmetic→มยุรี h=27, MFU fungal→อรวรรณ h=32, SUT quantum→สุขิต h=42); orphan เหลือ 0

> ⚠️ เทสต์ที่พังมาก่อนหน้า (ไม่เกี่ยวกับงานนี้): `tests/test_agentic_pipeline.py::test_state_reducer_dedup_and_enrichment` คาดหวัง id รูปแบบเก่า `cmu_eng_ee_001` แต่ reducer สร้าง `chiangmaiu_facultyofe_charoensuk_001` — ต้องอัปเดตเทสต์ให้ตรง scheme ปัจจุบัน

### ขั้นที่ 2 — Enrichment ข้อมูลวิจัย (ตาม AGENTS.md Zero-Bypass) — 🔄 ทำ 10 ก.ย. 2569
**🔎 ข้อค้นพบสำคัญตอน audit:** เก่าไม่เคยมีสคริปต์ไหนใน repo ที่ *เขียน h_index ใหม่* ได้เลย — ค่า h_index เดิมทั้งหมดถูกย้ายมาจาก Supabase (`migrate_supabase_to_local.py`) กลุ่ม "ไม่มีข้อมูลวิจัย" ที่แท้คือนักวิชาการ **~2,036 คนที่ `openalex_id IS NULL` (ยังไม่เคยถูก attempt)** ไม่ใช่ attempt แล้วพลาด (กลุ่ม attempt-แล้วพลาดมี sentinel `not_indexed` แยกไว้แล้ว ~1,521 คน)

- [x] สร้างเครื่องมือใหม่ `backend/scripts/enrich_openalex_author_metrics.py` (OpenAlex author search → h_index/citations/works)
  - 🛡️ **homonym gate บังคับ:** รับ candidate ก็ต่อเมื่อ *นามสกุลตรงเป็น token เต็ม* + ชื่อต้น(หรือตัวหน้า)ตรง และถ้ามีหลายคนตรงโดยไม่ confirm ด้วยสังกัดมหาลัย → ปฏิเสธ ("Pi" → "Ileana Heredia-Pi" h=31 คือเคสจริงที่ gate กันไว้ได้)
  - precision ตรวจกับ ground-truth (กลุ่มที่มี id เดิม): **100%** exact-id recovery
  - idempotent + resume ได้: เลือกจาก `openalex_id IS NULL`, commit เป็น batch, checkpoint JSON ที่ `backend/data/agent_states/openalex_author_metrics_apply.json` (มี `before` snapshot ทุกแถว → revert ได้)
  - h_index ไม่อยู่ใน `embedding_text` → **ไม่ต้อง re-embed**
- [x] **Wave 1 รัน --apply สำเร็จบางส่วน:** 2,036 → resolve เพิ่ม **+227 คนมี h_index** (1,823 → **2,050 = 37.3%**), total resolved id 1,940 → **2,175**; สาขาที่ได้เพิ่มชัด: Math 7→16, Physics 32→44, ChemEng 39→47 คนมี h
  - ⚠️ **quota ของ OpenAlex key pool (3 keys) หมดกลาง wave** → polite pool โดน 429 ต่อ; แถวที่ยังไม่ได้ attempt เหลือ **1,795** (NULL, resume ได้)
  - 🐛 แถว 501 คนถูก stamp `not_indexed` ผิดduring ช่วง API ตาย — **แก้แล้ว: clear กลับ NULL ทั้ง 501** (จาก checkpoint list) และเพิ่ม **canary health-gate** ในสคริปต์ (ตรวจด้วยชื่อ known-good ก่อน stamp sentinel; API ตายเมื่อไหร่ → หยุด clean ไม่เก็บขยะ) + flag `--include-sentinel` สำหรับ probe ซ้ำแถว sentinel เก่า
  - ▶️ **รอบหน้า (quota รีเซ็ตแล้ว):** `python backend/scripts/enrich_openalex_author_metrics.py --apply --workers 4` ต่อจาก 1,795 ที่ค้าง (รันจาก repo root)
- [ ] ~~ThaiJO ให้ citations สายสังคม~~ ❌ **เป็นไปไม่ได้** — `enrich_thaijo_publications.py` เขียนแค่ *ชื่อหัวข้อ* (`citation_count` hard-set 0) และกลุ่ม `not_indexed` 0% in OpenAlex จริง; Google Scholar route ก็ใช้ไม่ได้ (SERPAPI key แรกหมด, `google_scholar_profiles` คืนศูนย์) — ThaiJO มีค่าเฉพาะ enrichment หัวข้อผลงาน (รันแล้ว 10 ก.ย. — ดู log)
- [x] ตรวจสอบ checkpoint `backend/data/agent_states/` ก่อนรันซ้ำ — ของ enrichment เดิมไม่มี state file; ตอนนี้ checkpoint ของเราเองเขียนทุก batch

**สรุป demand-gap หลัง wave 1:** สาขา ตัวท็อปโลก (ศึกษาฯ h สูงสุด 7, นิติฯ 6, จิตวิทยา 6, ท่องเที่ยว 0) **ไม่หายจาก enrichment** เพราะคนกลุ่มนี้ตีพิมพ์ไทย/ไม่มีใน OpenAlex — ทางออกเดียวคือ **ขั้นที่ 3 (Acquisition)** และ/หรือยอมรับ gap โดยแสดง tier ตามข้อมูลจริง

### ขั้นที่ 3 — Acquisition สาขา-มหาลัยที่ขาด (ใช้ skill `data-acquire-faculty-elites`) ✅ เสร็จ 10 ก.ย. 2569
เป้าหมายเรียงตาม demand: คณะศึกษาศาสตร์/ครุศาสตร์ (มศว, จุฬาฯ, สวนสุนันทา) → นิติฯ (ธรรมศาสตร์) → การตลาด/บริหาร (TBS) → Cyber/HCI (SIT, FIBO) → ท่องเที่ยว

**ทำสำเร็จ — 4 batches ใหม่ผ่าน SKILL.state Reducer ครบวงจร (crawl → reducer → checkpoint → export → runner upsert):**

| Batch | Source / Pipeline | ได้ | จุดเด่น |
| :--- | :--- | ---: | :--- |
| 98 | `crawlers/swu_edu_api_pipeline.py` — edu.swu.ac.th WordPress `staff` API | **107** | sidebar 4-line + กรองเจ้าหน้าที่ด้วย courtesy prefix |
| 99 | `crawlers/ssru_edu_api_pipeline.py` — edu.ssru.ac.th TH/EN accordion + DLP emails | **53** | email/photo/วุฒิการศึกษา/DLP ครบ 100%, 9 ภาควิชา |
| 100 | `crawlers/tu_law_api_pipeline.py` — law.tu.ac.th WP `teacher` API (102 posts) | **32** | **ผลงานวิชาการคัดสรร 188 รายการ (dict shape + DOI)** ครั้งแรกที่นิติศาสตร์ไทยมีรายชื่อผลงานจริงใน DB |
| 101 | `crawlers/tbs_staff_api_pipeline.py` — tbs.tu.ac.th `staff-sitemap.xml` (195 คน) | **102** | email 78, วุฒิ 90, photo 570×570 ครบ, กรอง non-academic 17 |

**ผลต่อ priority gap (หลัง dedup 10 ก.ย.):**
- ศึกษาศาสตร์+ครุศาสตร์: 206 → **340 คน** (มีผลงาน 205) — h-index ยังไม่มีตัวท็อป (max 18) ตามข้อจำกัด OpenAlex จริง
- นิติศาสตร์: 282 → **328 คน** (มีผลงาน 182 — ส่วนใหญ่มาจาก curated pubs ของ TU Law)
- พาณิชยศาสตร์/การตลาด (TBS): 95 → **149 คน, h≥20 = 4 คน (max 37)** — gap "h≥20 = 0" **ปิดแล้วเป็นสาขาแรก** ของตารางขั้นที่ 3
- 🐛 พบระหว่างทาง: แถว legacy ไม่มี email → reducer pre-check มองไม่เห็น → ซ้ำข้าม id-family; **แก้ด้วย `merge_duplicate_faculties.py --by-name`** (โหมดใหม่: normalize ตัดยศ, merge ใน uni+faculty เดียว, re-embed อัตโนมัติ) — รอบแรก 98 กลุ่ม, หลัง Batch 101 อีก 185 กลุ่ม (5,872 → **5,685**)

**ข้าม (แหล่งข้อมูลเข้าถึงไม่ได้จริง — ตามคำสั่ง "หาไม่ได้จริงก็ข้าม"):**
- Cyber/HCI: SIT/FIBO/CBS ConnectError, NIDA Cloudflare 403 (ของเดิมที่ verify ไว้แล้วเป็นรายการเล็ก ingested ไปนานแล้ว)
- ท่องเที่ยว/โรงแรม: tht.msu.ac.th, SU HTCL, PSU, BUU, RU, MU, TU-CITS **ConnectError ทั้งหมด** (ปัญหาเครือข่ายจากเครื่องนี้ ไม่ใช่ 404) — probe ซ้ำ 10 ก.ย. ไม่ผ่านสักแหล่ง
- Marketing เพิ่มเติม: TBS เป็นแหล่งเดียวที่เปิด (ทำแล้ว)

### ขั้นที่ 2b — OpenAlex wave 2 (ต่อจาก 1,795 ที่ค้าง) ❌ quota หมดทั้ง 3 keys + polite pool ถูก throttle
รัน 10 ก.ย. หลัง Batch 101: targets เพิ่มเป็น **1,964** แต่ canary health-gate ทำงานถูกต้อง **abort ก่อนเขียนใดๆ (0 writes, ไม่ stamp ขยะ)** → ข้ามตามคำสั่ง; คิว daily-reset ครั้งถัดไป: `python backend/scripts/enrich_openalex_author_metrics.py --apply --workers 4` (idempotent, resume จาก `openalex_id IS NULL` — ตอนนี้ 2,093 แถว)

### ขั้นที่ 4 — ผูกเข้า UX (หลังข้อมูลครบ) ⏸️ เลื่อนไว้
- [ ] เพิ่ม filter/sort "ระดับผลงานวิจัย" (h-index tier) ในหน้าค้นหาอาจารย์
- [ ] Badge "🏆 ตัวท็อปสาขา" ใน AdvisorCard เมื่อ h_index ≥ 20 หรือ citations ≥ 1,000
> เลื่อนไปก่อน — เป็นงาน frontend ที่ทำได้ทันทีเมื่อพร้อม ไม่ต้องรอข้อมูล

---

## 📊 สรุปผลภารกิจ 5 (10 ก.ย. 2569 รอบสุดท้าย)

| | ก่อน | หลัง |
| :--- | ---: | ---: |
| อาจารย์ทั้งหมด | 5,497 | **5,685** |
| มี `featured_publications` | ~1,750 (31.8%) | **2,413 (42.4%)** |
| ThaiJO-credited (นักวิชาการไทยมีผลงานจริง) | 551 | **656** (waves 1–4, +105) |
| มี `h_index` > 0 | 2,050 (37.3%) | 2,030 (35.7%)* |
| missing embeddings | 0 | **0** |
| สาขาปิด gap ตัวท็อป (h≥20 > 0) | — | **การตลาด/บริหาร (TBS = 4 คน, max h=37)** |

\*h>0 ลดเล็กน้อยเพราะ dedup ด้วยชื่อลบแถวซ้ำที่ donor เป็น h-index เล็กน้อย — OpenAlex wave 2 (รอบ quota ถัดไป) จะ attempt แถวใหม่ทั้งหมดที่ยัง NULL (2,093) ให้กลับมา ≥37%

**เครื่องมือถาวรที่เพิ่มเข้า repo (นำกลับไปใช้ทุก batch ใหม่):**
1. `enrich_openalex_author_metrics.py` — h-index/citations จาก OpenAlex + homonym gate + canary health-gate
2. `enrich_thaijo_publications.py` (เขียนใหม่ OJS3 so01–so06) — หัวข้อผลงานสายสังคม/นิติ/ศึกษาฯ
3. `merge_duplicate_faculties.py --by-name` — dedup ข้าม id-family (ตัดยศ) + สืบทอด h_index/openalex_id จาก donor + re-embed
4. `backfill_embeddings.py` — ซ่อมแถวที่ embedding เป็น NULL
5. 4 pipelines ตัวอย่าง acquisition มาตรฐาน WordPress/sitemap (SWU/SSRU/TU-Law/TBS) → ใช้เป็น template คณะต่อไป
