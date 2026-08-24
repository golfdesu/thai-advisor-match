import os
import sys
import time
import logging
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scholarly import scholarly

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_scholar_data():
    logger.info("Starting Google Scholar Data Extraction...")
    
    with SessionLocal() as db:
        faculties = db.query(FacultyDB).all()
        
        for faculty in faculties:
            # Construct search query (English name + University is best)
            # If no first_name, try full_name_th
            search_name = ""
            if faculty.first_name and faculty.last_name:
                search_name = f"{faculty.first_name} {faculty.last_name}"
            else:
                search_name = faculty.full_name_th.split(" ")[-2:] # Try to grab name parts
                search_name = " ".join(search_name)
                
            query = f"{search_name} Chiang Mai University"
            logger.info(f"Searching Scholar for: {query}")
            
            try:
                # Search for the author
                search_query = scholarly.search_author(query)
                try:
                    author = next(search_query)
                except StopIteration:
                    logger.warning(f"Author not found on Scholar: {query}")
                    time.sleep(1.5)
                    continue
                
                # We found an author, fill in their publications
                logger.info(f"Found author: {author.get('name')}. Fetching publications...")
                author = scholarly.fill(author, sections=['publications'])
                
                # Get top 5 publications
                pubs = author.get('publications', [])
                top_pubs = []
                for p in pubs[:5]:
                    pub_title = p.get('bib', {}).get('title', '')
                    pub_year = p.get('bib', {}).get('pub_year', '')
                    num_citations = p.get('num_citations', 0)
                    
                    if pub_title:
                        title_str = f"{pub_title} ({pub_year})" if pub_year else pub_title
                        top_pubs.append({"title": title_str, "citations": num_citations})
                
                if top_pubs:
                    # Append new pubs to existing ones to not lose manual data, but avoid exact duplicates
                    existing_pubs = faculty.featured_publications or []
                    existing_titles = [ep.get("title", "").lower() for ep in existing_pubs]
                    
                    for np in top_pubs:
                        if np["title"].lower() not in existing_titles:
                            existing_pubs.append(np)
                    
                    # Update database
                    faculty.featured_publications = existing_pubs
                    # We also might want to append to embedding_text so it's matched in vector search, 
                    # but for now we just store in featured_publications which our semantic match script reads!
                    
                    db.commit()
                    logger.info(f"Successfully added {len(top_pubs)} publications for {faculty.full_name_th}")
                else:
                    logger.info(f"No publications found for {faculty.full_name_th}")
                
            except Exception as e:
                logger.error(f"Error processing {faculty.full_name_th}: {e}")
            
            # Sleep to avoid Google Scholar rate limiting (CAPTCHA)
            time.sleep(2)
            
    logger.info("Google Scholar update complete!")

if __name__ == "__main__":
    update_scholar_data()
