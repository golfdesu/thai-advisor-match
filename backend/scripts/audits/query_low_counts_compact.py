from app.core.database import SessionLocal
from sqlalchemy import text

TARGET_UNIVS = [
    "จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยธรรมศาสตร์", "มหาวิทยาลัยมหิดล",
    "มหาวิทยาลัยเกษตรศาสตร์", "มหาวิทยาลัยเชียงใหม่", "มหาวิทยาลัยขอนแก่น",
    "มหาวิทยาลัยสงขลานครินทร์", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "มหาวิทยาลัยศิลปากร"
]

db = SessionLocal()
rows = db.execute(text("""
    SELECT university_th, faculty_th, count(*) AS n
    FROM faculties
    WHERE university_th = ANY(:univs)
    GROUP BY university_th, faculty_th
    HAVING count(*) <= 30
    ORDER BY n, university_th, faculty_th
"""), {"univs": TARGET_UNIVS}).fetchall()
for university, faculty, count in rows:
    print(f"{university}|{faculty}|{count}")
db.close()
