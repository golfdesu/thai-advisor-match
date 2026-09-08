# ภารกิจที่ 1: การขยายฐานข้อมูลห้องปฏิบัติการวิจัย (Research Labs Expansion)

> **ความสำคัญ:** 🔥 ระดับ 1 (Critical Gap)  
> **เป้าหมาย:** เพิ่มจำนวนห้องปฏิบัติการวิจัยจาก 30 แห่ง ให้ได้ 70–100 แห่ง

---

## 1. ปัญหาและสถานะปัจจุบัน
ในตาราง `research_labs` ปัจจุบันมีข้อมูลเพียง **30 แห่ง** ทั้งประเทศ ทำให้หน้ารวมห้องปฏิบัติการวิจัยและการค้นหา Research Lab ตามความสนใจของนักศึกษา ป.โท/ป.เอก แสดงผลได้น้อยมาก:
- จุฬาลงกรณ์มหาวิทยาลัย: 4 แห่ง
- มหาวิทยาลัยมหิดล: 3 แห่ง
- มหาวิทยาลัยเชียงใหม่: 3 แห่ง
- สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง: 3 แห่ง
- มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี: 3 แห่ง
- ม.แม่ฟ้าหลวง: 2 แห่ง
- ม.ขอนแก่น: 2 แห่ง
- มจพ.: 2 แห่ง
- ม.ธรรมศาสตร์: 2 แห่ง
- ม.สงขลานครินทร์: 2 แห่ง
- มทส.: 2 แห่ง
- ม.เกษตรศาสตร์: 2 แห่ง

---

## 2. โดเมนวิจัยเป้าหมายที่ต้องการเพิ่ม (Key Research Domains)

### กลุ่มที่ 1: AI, Data Science, Cyber Security & Robotics
- **FIBO (มจธ.):** สถาบันวิทยาการหุ่นยนต์ภาคสนาม (Field Robotics, Industrial Automation, Service Robots)
- **VISTEC:** School of Information Science and Technology (IST) - NLP, Vision, Big Data Labs
- **KMITL Robotics & AI:** ศูนย์นวัตกรรมหุ่นยนต์และระบบปัญญาประดิษฐ์ คณะวิศวกรรมศาสตร์ สจล.
- **Chula AI / Data Science:** Smart Mobility Lab, Computational Intelligence Lab
- **CMU Center of Excellence in AI:** ศูนย์วิจัยปัญญาประดิษฐ์ มหาวิทยาลัยเชียงใหม่

### กลุ่มที่ 2: HealthTech, Medicine, Genomics & Drug Discovery
- **คณะแพทยศาสตร์ศิริราชพยาบาล (ม.มหิดล):** SiCORE (Siriraj Center of Research Excellence) เช่น SiCORE-Allergy, SiCORE-Genomics, SiCORE-Dengue
- **คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี (ม.มหิดล):** ศูนย์วิจัยการแพทย์จีโนมิกส์และเวชศาสตร์แม่นยำ (Genomics & Precision Medicine)
- **คณะเภสัชศาสตร์ จุฬาฯ / มช. / มหิดล:** ศูนย์วิจัยพัฒนาชีววัตถุและยาสมุนไพรล้านนา
- **ทันตกรรมขั้นสูง:** จุฬาฯ, มหิดล (ศูนย์วิจัยทันตนวัตกรรมและวิศวกรรมเนื้อเยื่อ)

### กลุ่มที่ 3: Energy, EV, Batteries & Clean Tech
- **มทส. (SUT):** ศูนย์วิจัยพลังงานทดแทนและยานยนต์ไฟฟ้า (Synchrotron-related energy research)
- **มจธ. (KMUTT):** Clean Energy & Fuel Cell Laboratory, JGSEE (บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม)
- **จุฬาฯ:** Energy Research Institute (ERI), Advanced Battery & Supercapacitor Lab

### กลุ่มที่ 4: Agriculture, Food Innovation & Biotechnology
- **ม.เกษตรศาสตร์:** ศูนย์วิจัยพันธุวิศวกรรมและเทคโนโลยีชีวภาพข้าว, ศูนย์นวัตกรรมอาหารแห่งชาติ
- **ม.แม่ฟ้าหลวง:** ศูนย์วิจัยนวัตกรรมชาและกาแฟ (Tea & Coffee Institute), สารสกัดเครื่องสำอาง
- **ม.สงขลานครินทร์:** สถาบันวิจัยและพัฒนานวัตกรรมยางพารา, Marine Biotechnology Lab

---

## 3. โครงสร้าง Schema สำหรับ `research_labs`
ตาราง `research_labs` ในฐานข้อมูลประกอบด้วยฟิลด์ดังนี้:
```sql
CREATE TABLE public.research_labs (
    id serial PRIMARY KEY,
    name_th varchar(255) NOT NULL,
    name_en varchar(255),
    university_th varchar(255) NOT NULL,
    faculty_th varchar(255),
    department_th varchar(255),
    lead_advisor_id integer REFERENCES faculties(id),
    research_domains json,       -- e.g. ["AI", "Computer Vision", "Medical Imaging"]
    flagship_equipment json,     -- e.g. ["NVIDIA DGX H100", "Micro-CT Scanner", "Confocal Microscope"]
    open_positions json,         -- e.g. ["Master RA (ทุนเต็มจำนวน)", "PhD Candidate (1 ตำแหน่ง)"]
    contact_email varchar(255),
    website_url text,
    image_url text,
    embedding vector(768)
);
```

---

## 4. แผนการดำเนินการเมื่อกลับมาทำต่อ
1. **จัดทำข้อมูลแล็บเป้าหมาย:** รวบรวมข้อมูลแล็บจากสถาบัน/ศูนย์ความเป็นเลิศ พร้อมแมป `lead_advisor_id` เข้ากับรายชื่ออาจารย์ที่มีอยู่ในตาราง `faculties` (เพื่อให้สามารถคลิกเชื่อมโยงไปยังหน้าโปรไฟล์อาจารย์ที่ปรึกษาได้)
2. **สร้าง Embedding (768-dim):** สังเคราะห์ข้อความค้นหา:
   ```python
   text_to_embed = f"{name_th} {name_en} {university_th} {faculty_th} {' '.join(research_domains)} {' '.join(flagship_equipment)}"
   ```
3. **Commit สู่ Local Postgres:** Ingest ตรงเข้า `research_labs` ใน Docker (`localhost:5432`)
4. **ตรวจสอบความสมบูรณ์และทดสอบ Semantic Lab Search:** ทดสอบการค้นหาผ่าน API `/api/labs`
