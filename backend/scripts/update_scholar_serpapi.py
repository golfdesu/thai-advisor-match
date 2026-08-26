import os
import sys
import json
import time

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpapi import GoogleSearch
from dotenv import load_dotenv
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

load_dotenv()

from sqlalchemy import or_

def update_publications_from_serpapi():
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        print("Error: SERPAPI_KEY not found in environment variables.")
        return

    db = SessionLocal()
    # Only fetch faculties that do NOT already have publications populated
    faculties = db.query(FacultyDB).filter(
        or_(
            FacultyDB.featured_publications == None,
            FacultyDB.featured_publications == []
        )
    ).all()
    
    if not faculties:
        print("All faculties already have publications populated!")
        db.close()
        return

    print(f"Found {len(faculties)} faculties without publications. Fetching...")
    
    pending_updates = 0
    for faculty in faculties:
        # Search for the Author's Publications directly
        author_query = f"author:\"{faculty.first_name} {faculty.last_name}\""
        print(f"Searching for: {author_query}")
        
        search_params = {
            "engine": "google_scholar",
            "q": author_query,
            "api_key": serpapi_key,
            "num": 5
        }
        
        try:
            search = GoogleSearch(search_params)
            results = search.get_dict()
        except Exception as e:
            print(f"Failed to fetch SerpApi for {author_query}: {e}")
            continue
            
        organic_results = results.get("organic_results", [])
        
        # Fallback if no results with strict author: constraint
        if not organic_results:
            fallback_query = f"\"{faculty.first_name} {faculty.last_name}\""
            print(f"  -> No strict results, trying fallback: {fallback_query}")
            search_params["q"] = fallback_query
            try:
                search = GoogleSearch(search_params)
                results = search.get_dict()
                organic_results = results.get("organic_results", [])
            except Exception as e:
                print(f"  -> Fallback failed: {e}")
                
        if not organic_results:
            print(f"  -> Still no articles found for {faculty.first_name} {faculty.last_name}.")
            continue
            
        # Keep top 5 publications
        featured_pubs = []
        for article in organic_results[:5]:
            pub_title = article.get("title", "")
            pub_link = article.get("link", "")
            if pub_title:
                featured_pubs.append({
                    "title": pub_title,
                    "url": pub_link
                })
        
        # 3. Update Database in Batches
        if featured_pubs:
            faculty.featured_publications = featured_pubs
            print(f"  -> Successfully added {len(featured_pubs)} publications.")
            pending_updates += 1
            if pending_updates % 5 == 0:
                db.commit()
            
        time.sleep(0.5) # Sleep briefly to respect API rate limits

    if pending_updates > 0:
        db.commit()
    db.close()
    print("Update complete!")

if __name__ == "__main__":
    update_publications_from_serpapi()
