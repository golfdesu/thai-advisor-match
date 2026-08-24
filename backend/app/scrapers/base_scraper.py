import urllib3
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.schema import FacultyMember

# Suppress insecure SSL warnings for university departmental servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BaseScraper(ABC):
    """Abstract Base Class for all University and Department Scrapers."""
    
    university_name: str = ""
    university_name_th: str = ""
    faculty_name: str = ""
    faculty_name_th: str = ""
    department_name: str = ""
    department_name_th: str = ""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    @abstractmethod
    def scrape(self) -> List[FacultyMember]:
        """Execute scraping logic and return a list of standardized FacultyMember objects."""
        pass
