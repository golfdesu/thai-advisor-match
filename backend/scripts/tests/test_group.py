from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from sqlalchemy import func

session = SessionLocal()
results = session.query(CourseDB.university, func.count(CourseDB.id)).group_by(CourseDB.university).all()
for u, c in sorted(results, key=lambda x: x[1], reverse=True):
    print(f"{u}: {c}")
