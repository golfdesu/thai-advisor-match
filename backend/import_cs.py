import json
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def import_cs():
    with open('cmu_cs_faculty.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    db = SessionLocal()
    for item in data:
        # Check if exists
        existing = db.query(FacultyDB).filter_by(id=item["id"]).first()
        if existing:
            continue
            
        fac = FacultyDB(
            id=item["id"],
            university=item["university"],
            university_th=item["university_th"],
            faculty=item["faculty"],
            faculty_th=item["faculty_th"],
            department=item["department"],
            department_th=item["department_th"],
            academic_title_th=item["academic_title_th"],
            first_name=item["first_name"],
            last_name=item["last_name"],
            full_name_th=item["full_name_th"],
            role=item["role"],
            email=item["email"],
            image_url=item["image_url"],
            profile_url=item["profile_url"],
            education=item["education"],
            research_interests=item["research_interests"],
            taught_courses=item["taught_courses"],
            scholar_url=item["scholar_url"]
        )
        db.add(fac)
    db.commit()
    db.close()
    print("CS Faculty imported successfully.")

if __name__ == "__main__":
    import_cs()
