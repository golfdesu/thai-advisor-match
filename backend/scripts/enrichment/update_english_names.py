import sys
import time
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scholarly import scholarly
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENGLISH_NAMES = {
    "ธราดล": ("Tharadol", "Komolmis"),
    "วัชริน": ("Watcharin", "Srirattanawichaikul"),
    "กสิณ": ("Kasin", "Prakobwaityakit"),
    "เกษมศักดิ์": ("Kasemsak", "Uthaichana"),
    "ดลเดช": ("Dhonded", "Tantrawiwat"),
    "นิพนธ์": ("Nipon", "Theera-Umpon"),
    "อุกฤษฏ์": ("Ukrit", "Mankong"),
    "บุญศรี": ("Boonsri", "Kaewkam-ai"),
    "ปารเมศ": ("Paramet", "Wirasanti"),
    "พีรพล": ("Peerapol", "Jirapong"),
    "สมบูรณ์": ("Somboon", "Nuchprayoon"),
    "สิโรตม์": ("Sirote", "Khunkitti"),
    "เสริมศักดิ์": ("Sermsak", "Uatrongjit"),
    "พีรพนธ์": ("Peerapon", "Anusarnsunthorn"),
    "ธนะพงษ์": ("Thanapong", "Thanasaksiri"),
    "ปณิดา": ("Panida", "Thararak"),
    "วิศรุต": ("Wisarut", "Atchariyawiriya"),
    "สรพล": ("Sorapon", "Kitsirisin"),
    "ยุทธนา": ("Yuttana", "Khamsuwan")
}

def fix_english_names():
    with SessionLocal() as db:
        faculties = db.query(FacultyDB).all()
        for faculty in faculties:
            for th_first, (en_first, en_last) in ENGLISH_NAMES.items():
                if th_first in faculty.full_name_th:
                    faculty.first_name = en_first
                    faculty.last_name = en_last
                    
                    # Update embedding text
                    if en_first not in (faculty.embedding_text or ""):
                        faculty.embedding_text = f"{en_first} {en_last} {faculty.embedding_text}"
                    break
        db.commit()
        logger.info("Updated English names in database!")

def fetch_scholar_for_yuttana():
    with SessionLocal() as db:
        yuttana = db.query(FacultyDB).filter(FacultyDB.first_name == "Yuttana").first()
        if not yuttana:
            return
            
        logger.info("Searching Google Scholar for Yuttana Khamsuwan...")
        try:
            search_query = scholarly.search_author("Yuttana Khamsuwan")
            author = next(search_query)
            author = scholarly.fill(author, sections=['publications'])
            
            top_pubs = []
            for p in author.get('publications', [])[:5]:
                pub_title = p.get('bib', {}).get('title', '')
                pub_year = p.get('bib', {}).get('pub_year', '')
                if pub_title:
                    top_pubs.append({"title": f"{pub_title} ({pub_year})" if pub_year else pub_title})
            
            if top_pubs:
                # Merge unique
                existing = yuttana.featured_publications or []
                existing_titles = [e.get("title").lower() for e in existing]
                for p in top_pubs:
                    if p["title"].lower() not in existing_titles:
                        existing.append(p)
                yuttana.featured_publications = existing
                db.commit()
                logger.info(f"Successfully added publications for Yuttana: {top_pubs}")
        except Exception as e:
            logger.error(f"Error fetching Yuttana's scholar: {e}")

if __name__ == "__main__":
    fix_english_names()
    fetch_scholar_for_yuttana()
