import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy import or_

def check_candidates():
    db = SessionLocal()

    candidates = [
        "ยง ภู่วรวรรณ",             # CU - ไวรัสวิทยา
        "นวดล เหล่าศิริพจน์",          # KMUTT - พลังงาน (JGSEE)
        "บรรจบ ศรีภา",              # KKU - พยาธิวิทยา (พยาธิใบไม้ตับ)
        "ฤดีกร วิวัฒนปฐพี",          # PSU - เภสัชศาสตร์
        "สุพจน์ หารหนองบัว",         # CU - เคมีคอมพิวเตอร์
        "ชาติเฉลิม อิศรางกูร",        # MU - เทคนิคการแพทย์
        "ธีระวัฒน์ เหมะจุฑา",         # CU - ประสาทวิทยาโรคอุบัติใหม่
        "ประมวล ตั้งบริบูรณ์รัตน์",     # MU - เคมีพอลิเมอร์
        "สุทธวัฒน์ เบญจกุล",          # PSU - อุตสาหกรรมเกษตร
        "สายสมร ลำยอง",             # CMU - จุลชีววิทยา (เห็ดรา)
        "สุเทพ สวนใต้",              # CMU - คณิตศาสตร์
        "เพทาย เย็นจิตโสมนัส",       # MU - อณูพันธุศาสตร์ทางการแพทย์
        "วิวัฒน์ รุจิรวณิช",            # CU - วัสดุศาสตร์และปิโตรเคมี
        "พรศักดิ์ ศรีอมรศักดิ์",         # SU - เภสัชกรรมเทคโนโลยี
        "ศิริพร ดำรงค์ศิริ",           # CU - สิ่งแวดล้อม
    ]

    print("=== ตรวจสอบรายชื่ออาจารย์ดีเด่นชุดใหม่ใน Database (ป้องกันการซ้ำซ้อน) ===\n")

    found_count = 0
    not_found = []

    for name in candidates:
        # Search by checking if name is in full_name_th
        existing = db.query(FacultyDB).filter(FacultyDB.full_name_th.like(f"%{name}%")).first()
        if existing:
            print(f"❌ พบแล้วในระบบ: {name} -> ID: {existing.id} ({existing.university_th})")
            found_count += 1
        else:
            print(f"✅ ไม่ซ้ำ (พร้อมเพิ่ม): {name}")
            not_found.append(name)

    print(f"\nสรุป: ซ้ำ {found_count} ท่าน | สามารถเพิ่มได้ใหม่ {len(not_found)} ท่าน")
    db.close()

if __name__ == "__main__":
    check_candidates()