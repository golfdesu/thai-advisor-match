# ภารกิจที่ 3: การเติมเต็มข้อมูลโปรไฟล์อาจารย์เดิม (Faculty Profile Enrichment)

> **ความสำคัญ:** ⚡ ระดับ 3 (Data Quality & UX Enhancement)  
> **เป้าหมาย:** ซ่อมแซมและเติมเต็มฟิลด์สำคัญที่ยังขาดในอาจารย์ 3,901 ท่านเดิม

---

## 1. ปัญหาและสถิติฟิลด์ที่ขาดหาย (Data Incompleteness)

จากการตรวจสอบฐานข้อมูล `faculties` (3,901 รายการ):

| ฟิลด์ที่ขาด | จำนวนที่ขาด | คิดเป็นเปอร์เซ็นต์ | ผลกระทบต่อระบบ |
| :--- | :---: | :---: | :--- |
| **Image URL (`image_url`)** | **2,482 ท่าน** | **63.6%** | หน้าเว็บต้องแสดง Avatar สำรอง (ตัวย่อ) แทนรูปจริง ส่งผลต่อความน่าเชื่อถือ |
| **Research Interests (`research_interests`)** | **1,670 ท่าน** | **42.8%** | การแสดงผล Synergy Badges และการจับคู่ Thesis Abstract มีความแม่นยำลดลง |
| **Publications (`featured_publications`)** | **745 ท่าน** | **19.1%** | ขาดข้อมูลผลงานวิจัยอ้างอิงล่าสุด |

---

## 2. กลยุทธ์การเติมเต็มข้อมูล (Enrichment Strategy)

### แนวทางที่ 1: เติมเต็ม Image URL จาก OpenAlex & Google Scholar / Scopus
- ค้นหาด้วยชื่อภาษาอังกฤษ (`full_name_en`) และชื่อมหาวิทยาลัยผ่าน OpenAlex API (มี API Keys อยู่ใน `backend/.env`)
- ดึงรูปภาพโปรไฟล์จากหน้า Directory ของคณะเดิมผ่าน URL ที่เคยบันทึกไว้ใน `profile_url`
- หากพบรูปภาพ ให้ตรวจสอบว่า URL นั้นสามารถเข้าถึงได้ (HTTP 200) และไม่ใช่รูป Broken Link

### แนวทางที่ 2: เติมเต็ม Research Interests จาก Featured Publications
สำหรับอาจารย์ที่มีผลงานวิจัย (`featured_publications`) แต่ยังไม่มี `research_interests` (ประมาณ 900+ ท่าน):
- สามารถสกัดคีย์เวิร์ดงานวิจัยจากชื่อบทความวิจัย (Paper Titles) ด้วย TF-IDF / KeyBERT หรือ LLM Summarization
- อัปเดตฟิลด์ `research_interests` (JSON Array)
- สังเคราะห์ข้อความ Embedding ใหม่และ Re-calculate 768-dim Vector เพื่อให้อัปเดตกับ pgvector

---

## 3. สคริปต์ตัวอย่างในการรัน Enrichment (บน Local Docker)
สร้างสคริปต์เฉพาะกิจ เช่น `backend/scripts/enrichment/enrich_faculty_missing_fields.py`:
```python
# 1. Query faculties where email is null or research_interests is null
# 2. Enrich via OpenAlex / Official Directory scrape
# 3. Update local postgres in batches of 100 with commit
```
*คำเตือน: ต้องรันบน Local Docker (`localhost:5432`) เท่านั้น เพื่อ Zero-Egress*
