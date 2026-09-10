"""
XHR/Fetch Network Capture Tool (Selenium CDP Performance Logging)
Captures all XHR/fetch/subdocument responses while a page loads/interacts,
returning {url: response_text} for analysis by the SKILL.state extraction agent.
"""
import json
import time
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class NetworkCaptureScraper:
    """Headless Chrome with network capture via CDP."""

    def __init__(self, page_load_timeout: int = 40):
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1400,2400")
        opts.set_capability("acceptInsecureCerts", True)
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(page_load_timeout)

    def _get_responses(self) -> List[dict]:
        logs = self.driver.get_log("performance")
        responses = []
        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
            except Exception:
                continue
            if msg["method"] in ("Network.responseReceived",):
                r = msg["params"]["response"]
                responses.append({
                    "requestId": msg["params"]["requestId"],
                    "url": r["url"],
                    "status": r["status"],
                    "mime": r.get("mimeType", ""),
                })
        return responses

    def _get_body(self, request_id: str) -> str:
        try:
            result = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return result.get("body", "")
        except Exception:
            return ""

    def capture(
        self,
        url: str,
        wait: float = 6.0,
        click_selectors: List[str] = None,
        scroll_rounds: int = 3,
        mime_filter: tuple = ("json", "javascript", "html", "xml", "text"),
    ) -> Dict[str, str]:
        """Loads page, optionally clicks selectors, returns captured response bodies."""
        out: Dict[str, str] = {}
        self.driver.get(url)
        time.sleep(wait)

        if scroll_rounds:
            for _ in range(scroll_rounds):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)

        for sel in (click_selectors or []):
            try:
                els = self.driver.find_elements("css selector", sel)
                for el in els[:20]:
                    try:
                        self.driver.execute_script("arguments[0].click();", el)
                        time.sleep(1.2)
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(1.5)

        for resp in self._get_responses():
            if resp["status"] != 200:
                continue
            mime = resp["mime"].lower()
            if mime and not any(m in mime for m in mime_filter):
                continue
            body = self._get_body(resp["requestId"])
            if body:
                key = f"{resp['url']}||{resp['mime']}"
                if key not in out or len(body) > len(out[key]):
                    out[key] = body
        return out

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass
