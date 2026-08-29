from app.core.database import SessionLocal, engine
from app.models.db_models import CourseDB

session = SessionLocal()
print("MU Total:", session.query(CourseDB).filter(CourseDB.university == "Mahidol University").count())
