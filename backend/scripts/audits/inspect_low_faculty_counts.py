# -*- coding: utf-8 -*-
import sys
from pathlib import Path

parents = Path(__file__).resolve().parents
BACKEND_DIR = parents[2] if len(parents) > 2 else parents[0]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

TARGET_UNIVS = [
    "จุฬาลงกรณ์มหาวิทยาลัย",
    "มหาวิทยาลัยธรรมศาสตร์",
    "มหาวิทยาลัยมหิดล",
    "มหาวิทยาลัยเกษตรศาสตร์",
    "มหาวิทยาลัยเชียงใหม่",
    "มหาวิทยาลัยขอนแก่น",
    "มหาวิทยาลัยสงขลานครินทร์",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "มหาวิทยาลัยศิลปากร"
]

query = text("""
    SELECT university_th, faculty_th, count(*) as count
    FROM faculties
    WHERE university_th = ANY(:univs)
    GROUP BY university_th, faculty_th
    ORDER BY university_th, count ASC
""")

rows = db.execute(query, {"univs": TARGET_UNIVS}).fetchall()

print("=" * 60)
print("FACULTY BREAKDOWN FOR TOP THAI UNIVERSITIES")
print("=" * 60)

by_univ = {}
for u, f, c in rows:
    if u not in by_univ:
        by_univ[u] = []
    by_univ[u].append((f, c))

for u in TARGET_UNIVS:
    if u in by_univ:
        print(f"\n>>> {u} (ทั้งหมด {sum(c for f, c in by_univ[u])} คน):")
        # Sort by count ascending
        sorted_facs = sorted(by_univ[u], key=lambda x: x[1])
        for f, c in sorted_facs:
            # Highlight small ones (< 20) or medium (< 40)
            status = "🔴 น้อยมาก (<15)" if c < 15 else ("🟡 ค่อนข้างน้อย (15-30)" if c <= 30 else "🟢 ปกติ (>30)")
            print(f"  - {f or 'ไม่ระบุคณะ'}: {c} คน  [{status}]")

db.close()
