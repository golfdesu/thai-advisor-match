import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.core.database import engine
from app.models.db_models import FacultyDB
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

def check_advisors_data():
    with Session(engine) as session:
        advisors = session.query(FacultyDB).all()
        total_advisors = len(advisors)
        
        missing_research = 0
        missing_publications = 0
        
        for adv in advisors:
            if not adv.research_interests or len(adv.research_interests) == 0:
                missing_research += 1
            if not adv.featured_publications or len(adv.featured_publications) == 0:
                missing_publications += 1
                
        print(f"Total Advisors in DB: {total_advisors}")
        print(f"Advisors with MISSING research_interests: {missing_research}")
        print(f"Advisors with MISSING featured_publications: {missing_publications}")

if __name__ == '__main__':
    check_advisors_data()
