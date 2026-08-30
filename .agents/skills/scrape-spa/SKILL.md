---
name: scrape-spa
description: Extracts course and faculty data from university websites that are Single Page Applications (SPA) or use Client-side JavaScript Rendering.
---

# University SPA Scraper Skill

When the user triggers `/scrape-spa [URL]` or wants to extract data from modern university websites rendered with JavaScript/React:

1. Use the Headless Browser module (`backend/app/scrapers/browser_scraper.py`):
   ```python
   from app.scrapers.browser_scraper import BrowserScraper
   
   scraper = BrowserScraper(headless=True)
   html = scraper.scroll_and_render_all(url, scroll_pause=1.5, max_scrolls=5)
   scraper.close()
   ```

2. Parse the rendered HTML to extract course information or faculty lists using BeautifulSoup.
3. Verify that the extracted data complies with the project standards:
   - Do not collect personal phone numbers (PDPA Compliance).
   - Always calculate 768-dim Vector Embeddings before saving to the Supabase database.

