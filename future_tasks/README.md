# แผนงานการขยายฐานข้อมูลในอนาคต (Future Data Acquisition & Expansion Roadmap)

> **บันทึกเมื่อ:** 8 กันยายน 2026  
> **ฐานข้อมูลหลักปัจจุบัน:** Local Docker PostgreSQL 17 (`localhost:5432 / advisor_match`)

เอกสารในโฟลเดอร์นี้รวบรวมรายการข้อมูลที่ยังขาด ความสำคัญ แนวทาง และสคริปต์/คำสั่งสำหรับกลับมาทำงานต่อในครั้งถัดไป แบ่งออกเป็น 4 ภารกิจหลักตามลำดับความสำคัญ (Priority):

---

## สรุปภาพรวมและสถานะปัจจุบัน (Database Audit Baseline)

| ประเภทข้อมูล | จำนวนปัจจุบัน | ความสมบูรณ์ของข้อมูล (Completeness) | ความสำคัญในการขยาย |
| :--- | :---: | :--- | :---: |
| **1. Research Labs (`research_labs`)** | **30 แห่ง** | มีข้อมูลครบทุกฟิลด์ แต่จำนวนน้อยมาก (เฉลี่ย 2-4 แล็บ/มหาลัย) | 🔥 **ระดับ 1 (Critical)** |
| **2. Faculty Coverage (`faculties`)** | **3,901 ท่าน** | กระจุกตัวที่ Top 5 มหาลัย ขาด มศว, บูรพา, แม่ฟ้าหลวง, ศิลปากร | 🔥 **ระดับ 2 (High)** |
| **3. Faculty Enrichment (`faculties`)** | **3,901 ท่าน** | ขาด Email (29.9%), Avatar (63.6%), Interests (42.8%) | ⚡ **ระดับ 3 (Medium)** |
| **4. Regional Courses (`courses`)** | **4,162 หลักสูตร** | ครบฟิลด์ 100% แต่เน้นไปที่ Top 6 มหาลัย ยังขาด ป.โท/เอก ภูมิภาค | 📌 **ระดับ 4 (Normal)** |

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

---

## กฎสำคัญในการเริ่มทำต่อ (Zero-Bypass & Local-First)
1. **รันบน Local เสมอ:** ตรวจสอบว่า Docker Postgres รันอยู่ (`docker compose up -d`) ทุกคำสั่งต้องต่อที่ `localhost:5432` เพื่อหลีกเลี่ยง Egress ของ Supabase
2. **ไม่สังเคราะห์ข้อมูลเอง:** รันผ่าน Autonomous Pipeline / Established Crawlers เท่านั้นตามกฎ `AGENTS.md`
3. **เมื่อได้ข้อมูลสมบูรณ์:** ใช้ `python backend/scripts/sync_local_to_supabase.py` เพื่อซิงค์ขึ้น Cloud Production
