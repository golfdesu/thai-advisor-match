# ภารกิจที่ 4: การขยายหลักสูตรมหาวิทยาลัยภูมิภาค (Regional Curriculum Expansion)

> **ความสำคัญ:** 📌 ระดับ 4 (Coverage Optimization)  
> **เป้าหมาย:** เพิ่มหลักสูตรระดับบัณฑิตศึกษา (ป.โท / ป.เอก) ในมหาวิทยาลัยภูมิภาค

---

## 1. สถานะปัจจุบัน
ในตาราง `courses` (4,162 หลักสูตร):
- ม.เชียงใหม่, ม.ขอนแก่น, ม.เกษตรศาสตร์, จุฬาฯ, มหิดล รวมกันมีมากกว่า 2,800 หลักสูตร (ครอบคลุมครบถ้วน)
- แต่มหาวิทยาลัยภูมิภาคและสถาบันชั้นนำบางแห่งยังมีหลักสูตรในระบบค่อนข้างน้อย:
  - ม.สงขลานครินทร์ (มอ.): 74 หลักสูตร
  - ม.สุโขทัยธรรมาธิราช: 70 หลักสูตร
  - ม.ศิลปากร: 61 หลักสูตร
  - ม.ศรีนครินทรวิโรฒ: 56 หลักสูตร
  - ม.พะเยา: 54 หลักสูตร
  - ม.แม่ฟ้าหลวง: 54 หลักสูตร
  - ม.นเรศวร: 53 หลักสูตร
  - ม.บูรพา: 41 หลักสูตร
  - ม.ทักษิณ: 36 หลักสูตร
  - ม.อุบลราชธานี: 74 หลักสูตร
  - ม.วลัยลักษณ์: มีน้อยมาก

---

## 2. วิธีการดำเนินงานตาม SKILL: `data-curriculum-tuition-discovery`
รันกระบวนการ 3-Tier Discovery ตามที่บันทึกไว้ใน `.agents/skills/data-curriculum-tuition-discovery/SKILL.md`:
1. **Tier 1 (TQF-2 MIS):** เจาะ MIS หรือเว็บไซต์บัณฑิตวิทยาลัยเพื่อเก็บชื่อปริญญา หน่วยกิต และโครงสร้างหลักสูตร
2. **Tier 2 (TCAS & Registrar Fees):** ดึงข้อมูลค่าเทอมรายภาคการศึกษา (`tuition_per_semester`) และโอกาสทางวิชาชีพ (`career_paths`)
3. **Tier 3 (Fuzzy Reconciliation & Embedding):** แมปข้อมูลด้วย RapidFuzz และยิงสร้าง Embedding 768-dim ก่อน Commit ลง Local Postgres

### คำสั่ง CLI ที่พร้อมใช้งาน:
```bash
python backend/scripts/agentic_pipeline/course_cli_runner.py \
  --univ-th "มหาวิทยาลัยสงขลานครินทร์" \
  --univ-en "Prince of Songkla University" \
  --faculty-th "บัณฑิตวิทยาลัย" \
  --faculty-en "Graduate School" \
  --url "https://grad.psu.ac.th/curriculum" \
  --export-file "backend/scripts/data_sources/psu_grad_courses.py"
```
