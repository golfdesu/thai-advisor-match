"""Curated faculty_th merges (parenthetical/campus-suffix aliases only). DRY-RUN first."""
import sys
from pathlib import Path
from sqlalchemy import func

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

# (university_th, alias_label, canonical_label) — alias rows get canonical label
MERGES = [
 ("มหาวิทยาลัยธรรมศาสตร์", "คณะสถาปัตยกรรมศาสตร์และการผังเมือง (TDS)", "คณะสถาปัตยกรรมศาสตร์และการผังเมือง"),
 ("มหาวิทยาลัยมหิดล", "สถาบันวิจัยประชากรและสังคม (IPSR)", "สถาบันวิจัยประชากรและสังคม"),
 ("มหาวิทยาลัยมหิดล", "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT)", "คณะเทคโนโลยีสารสนเทศและการสื่อสาร"),
 ("มหาวิทยาลัยมหิดล", "คณะวิศวกรรมศาสตร์ ภาควิชาวิศวกรรมชีวการแพทย์ (BART LAB)", "คณะวิศวกรรมศาสตร์"),
 ("มหาวิทยาลัยศรีนครินทรวิโรฒ", "วิทยาลัยนวัตกรรมสื่อสารสังคม (COSCI)", "วิทยาลัยนวัตกรรมสื่อสารสังคม"),
 ("มหาวิทยาลัยศิลปากร", "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT)", "คณะเทคโนโลยีสารสนเทศและการสื่อสาร"),
 ("มหาวิทยาลัยเกษตรศาสตร์", "สถาบันค้นคว้าและพัฒนาผลิตภัณฑ์อาหาร (IFRPD)", "สถาบันค้นคว้าและพัฒนาผลิตภัณฑ์อาหาร"),
 ("มหาวิทยาลัยเกษตรศาสตร์", "สถาบัน KAPI", "สถาบันค้นคว้าและพัฒนาผลิตผลทางการเกษตรและอุตสาหกรรมเกษตร (KAPI)"),
 ("สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)", "คณะบริหารธุรกิจ (NIDA Business School)", "คณะบริหารธุรกิจ"),
 ("จุฬาลงกรณ์มหาวิทยาลัย", "คณะวารสารศาสตร์และสื่อสารมวลชน", "คณะนิเทศศาสตร์"),
]

DRY = "--apply" not in sys.argv

db = SessionLocal()
try:
    total = 0
    for u, alias, canon in MERGES:
        n = db.query(func.count()).select_from(FacultyDB).filter(
            FacultyDB.university_th == u, FacultyDB.faculty_th == alias).scalar()
        n_canon = db.query(func.count()).select_from(FacultyDB).filter(
            FacultyDB.university_th == u, FacultyDB.faculty_th == canon).scalar()
        _log(f"{'[DRY] ' if DRY else ''}{u} :: {alias} ({n}) -> {canon} ({n_canon})")
        if n and not DRY:
            db.query(FacultyDB).filter(
                FacultyDB.university_th == u, FacultyDB.faculty_th == alias).update(
                {FacultyDB.faculty_th: canon}, synchronize_session=False)
            total += n
    if not DRY:
        db.commit()
        _log(f"merged {total} rows")
    else:
        _log("dry run — pass --apply to commit")
finally:
    db.close()
