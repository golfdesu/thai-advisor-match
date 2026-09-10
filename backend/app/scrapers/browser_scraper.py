"""
Headless Browser Scraper for SPA / Client-Side Rendered University Pages
Follows the data-scrape-spa skill contract (Selenium-based rendering).
"""
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BrowserScraper:
    """Renders JavaScript-heavy university pages and returns final HTML."""

    def __init__(self, headless: bool = True, page_load_timeout: int = 30):
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1400,2400")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        opts.set_capability("acceptInsecureCerts", True)
        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(page_load_timeout)

    def scroll_and_render_all(
        self,
        url: str,
        scroll_pause: float = 1.5,
        max_scrolls: int = 5,
        extra_wait: float = 2.0,
    ) -> Optional[str]:
        """Navigates, scrolls to trigger lazy-loading, and returns final page HTML."""
        try:
            self.driver.get(url)
            time.sleep(extra_wait)
            for _ in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
            return self.driver.page_source
        except Exception as e:
            print(f"  BrowserScraper error on {url}: {e}")
            return None

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass
