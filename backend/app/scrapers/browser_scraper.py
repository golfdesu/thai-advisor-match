import time
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper
from app.models.schema import FacultyMember

logger = logging.getLogger(__name__)

class BrowserScraper(BaseScraper):
    """
    Headless Browser Scraper using Selenium (Chrome/Edge WebDriver)
    Specifically designed for Single Page Applications (SPAs) and JavaScript-heavy university portals.
    """

    def __init__(self, headless: bool = True, timeout: int = 20):
        super().__init__(timeout=timeout)
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        if self.driver is not None:
            return self.driver

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.timeout)
            return self.driver
        except Exception as e:
            logger.warning(f"Chrome WebDriver not initialized, falling back to edge/requests: {e}")
            try:
                from selenium import webdriver
                from selenium.webdriver.edge.options import Options as EdgeOptions

                edge_options = EdgeOptions()
                if self.headless:
                    edge_options.add_argument("--headless=new")
                edge_options.add_argument("--disable-gpu")
                self.driver = webdriver.Edge(options=edge_options)
                self.driver.set_page_load_timeout(self.timeout)
                return self.driver
            except Exception as e2:
                logger.error(f"Failed to initialize Browser Driver: {e2}")
                return None

    def fetch_rendered_html(self, url: str, wait_for_selector: Optional[str] = None, wait_seconds: float = 3.0) -> str:
        """
        Loads a URL, executes JavaScript, waits for dynamic content to render, and returns full HTML.
        """
        driver = self._init_driver()
        if not driver:
            # Fallback to requests if browser driver is unavailable
            r = self.session.get(url, timeout=self.timeout)
            return r.text

        try:
            driver.get(url)
            if wait_for_selector:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                except Exception:
                    pass
            else:
                time.sleep(wait_seconds)

            return driver.page_source
        except Exception as e:
            logger.error(f"Error rendering {url}: {e}")
            return ""

    def scroll_and_render_all(self, url: str, scroll_pause: float = 1.5, max_scrolls: int = 5) -> str:
        """
        Scrolls down dynamically to trigger Infinite Scroll / Lazy Loading on modern university sites.
        """
        driver = self._init_driver()
        if not driver:
            return self.fetch_rendered_html(url)

        try:
            driver.get(url)
            last_height = driver.execute_script("return document.body.scrollHeight")

            for _ in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            return driver.page_source
        except Exception as e:
            logger.error(f"Error scrolling page {url}: {e}")
            return ""

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def __del__(self):
        self.close()

    def scrape(self) -> List[FacultyMember]:
        """Override in university-specific scrapers"""
        return []
