# แผนงานการขยายฐานข้อมูลในอนาคต (Future Data Acquisition & Expansion Roadmap)

> **บันทึกเมื่อ:** 8 กันยายน 2026  
> **ฐานข้อมูลหลักปัจจุบัน:** Local Docker PostgreSQL 17 (`localhost:5432 / advisor_match`)

เอกสารในโฟลเดอร์นี้รวบรวมรายการข้อมูลที่ยังขาด ความสำคัญ แนวทาง และสคริปต์/คำสั่งสำหรับกลับมาทำงานต่อในครั้งถัดไป แบ่งออกเป็น **5 ภารกิจหลัก**ตามลำดับความสำคัญ (Priority):

> **อัปเดต 10 ก.ย. 2569:** เพิ่มภารกิจที่ 5 (อาจารย์เก่ง/ตัวท็อปงานวิจัย) และฐานข้อมูลโตแล้ว — faculties 3,901 → **5,587 คน** (24 มหาลัย)
> **อัปเดตภารกิจ 5 (10 ก.ย. 2569, รอบเย็น):** ทำขั้นที่ 2–3 ของภารกิจ 5 เสร็จ — acquisition 4 คณะ (SWU ครุศึกษา 107, SSRU ครุศาสตร์ 53, TU นิติฯ 32 พร้อมผลงานคัดสรร 188, TBS พาณิชยฯ 102) + ThaiJO OJS3 fix/enrichment หลาย wave + เครื่องมือ dedup ใหม่มือชื่อ `merge_duplicate_faculties.py --by-name` → **5,685 คน, มีผลงาน 42.4%, h>0 35.7%** (รายละเอียดใน `05_find_expert_researchers.md`)

---

## สรุปภาพรวมและสถานะปัจจุบัน (Database Audit Baseline)

| ประเภทข้อมูล | จำนวนปัจจุบัน | ความสมบูรณ์ของข้อมูล (Completeness) | ความสำคัญในการขยาย |
| :--- | :---: | :--- | :---: |
| **1. Research Labs (`research_labs`)** | **30 แห่ง** | มีข้อมูลครบทุกฟิลด์ แต่จำนวนน้อยมาก (เฉลี่ย 2-4 แล็บ/มหาลัย) | 🔥 **ระดับ 1 (Critical)** |
| **2. Faculty Coverage (`faculties`)** | **3,901 ท่าน** | กระจุกตัวที่ Top 5 มหาลัย ขาด มศว, บูรพา, แม่ฟ้าหลวง, ศิลปากร | 🔥 **ระดับ 2 (High)** |
| **3. Faculty Enrichment (`faculties`)** | **3,901 ท่าน** | ขาด Email (29.9%), Avatar (63.6%), Interests (42.8%) | ⚡ **ระดับ 3 (Medium)** |
| **4. Regional Courses (`courses`)** | **4,162 หลักสูตร** | ครบฟิลด์ 100% แต่เน้นไปที่ Top 6 มหาลัย ยังขาด ป.โท/เอก ภูมิภาค | 📌 **ระดับ 4 (Normal)** |
| **5. Elite Researchers (`faculties`)** | **2,030/5,685 มี h-index** | h>0 = 35.7%, มีผลงานวิจัย = 42.4%; การตลาด/บริหารปิด gap แล้ว (TBS h≥20 = 4), ศึกษาฯ/นิติฯ ครอบคลุม roster แล้วแต่ตัวท็อปไทยไม่อยู่ใน OpenAlex (ดูภารกิจ 5) | 🏆 **ระดับ 1–2 (ใหม่)** |

---

## สารบัญเอกสารภารกิจย่อย (Task Breakdown)

1. **[`01_research_labs_expansion.md`](./01_research_labs_expansion.md)**
   - **เป้าหมาย:** เพิ่มห้องปฏิบัติการวิจัยจาก 30 แห่ง ให้เป็น 70–100 แห่ง
   - **โฟกัส:** AI, Robotics, Smart Energy, BioMed, HealthTech, Materials
   - **แหล่งข้อมูล:** จุฬาฯ, มหิดล (ศิริราช/รามา), มช., มจธ. (FIBO), สจล., สวทช. (NECTEC/MTEC/BIOTEC/NANOTEC)

2. **[`02_faculty_coverage_expansion.md`](./02_faculty_coverage_expansion.md)**
   - **เป้าหมาย:** เก็บข้อมูลอาจารย์ในมหาวิทยาลัยที่ยังมีน้อยมาก (< 30 คน)
   - **โฟกัส:** ม.ศรีนครินทรวิโรฒ (13 ท่าน), ม.บูรพา (14 ท่าน), ม.แม่ฟ้าหลวง (25 ท่าน), ม.ศิลปากร (29 ท่าน), ม.สงขลานครินทร์ (129 ท่าน)
   - **วิธีทำ:** ใช้ Autonomous Pipeline Runner + WikiSkill

3. **[`03_faculty_profile_enrichment.md`](./03_faculty_profile_enrichment.md)**
   - **เป้าหมาย:** เติมเต็มข้อมูลอาจารย์เดิม 3,901 ท่านให้สมบูรณ์
   - **โฟกัส:**
     - เติม Email ที่ขาด 1,165 ท่าน (เพื่อให้ระบบ AI Cold Email ใช้งานได้จริง)
     - เติม Image URL ที่ขาด 2,482 ท่าน (เพื่อ UI สวยงาม ลด Fallback Avatar)
     - เติม Research Interests ที่ขาด 1,670 ท่าน (เพื่อ Semantic Match ที่แม่นยำ)

4. **[`04_regional_curriculum_expansion.md`](./04_regional_curriculum_expansion.md)**
   - **เป้าหมาย:** เสริมหลักสูตรบัณฑิตศึกษา (ป.โท และ ป.เอก) ในมหาวิทยาลัยภูมิภาค
   - **โฟกัส:** ม.สงขลานครินทร์, ม.นเรศวร, ม.อุบลราชธานี, ม.พะเยา, ม.ทักษิณ

5. **[`05_find_expert_researchers.md`](./05_find_expert_researchers.md)** ⭐ (ใหม่)
   - **เป้าหมาย:** หาอาจารย์ที่เก่ง/ผลงานวิจัยดีให้ครบทุกสาขา + แก้ data quality
   - **โฟกัส:** Enrich h-index/citations อีก 3,675 คน (65.8%), เก็บตัวท็อปสาขา ศึกษาศาสตร์/นิติฯ/รป.ม./ท่องเที่ยว/ไซเบอร์, แก้ `_fetch_distinguished_advisors` ให้ใช้ h_index, แก้ยศซ้ำ 5,409 แถว, dedup ข้ามมหาลัย
   - **Audit scripts ที่เตรียมไว้:** `backend/scripts/audits/field_taxonomy.py`, `field_coverage_gap_analysis.py`, `elite_researcher_gap.py`

---

## กฎสำคัญในการเริ่มทำต่อ (Zero-Bypass & Local-First)
1. **รันบน Local เสมอ:** ตรวจสอบว่า Docker Postgres รันอยู่ (`docker compose up -d`) ทุกคำสั่งต้องต่อที่ `localhost:5432` เพื่อหลีกเลี่ยง Egress ของ Supabase
2. **ไม่สังเคราะห์ข้อมูลเอง:** รันผ่าน Autonomous Pipeline / Established Crawlers เท่านั้นตามกฎ `AGENTS.md`
3. **เมื่อได้ข้อมูลสมบูรณ์:** ใช้ `python backend/scripts/sync_local_to_supabase.py` เพื่อซิงค์ขึ้น Cloud Production
