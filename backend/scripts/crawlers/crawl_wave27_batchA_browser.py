"""Wave27 Batch A (browser-only): NIDA EN top-up x3 + SU ICT Elementor retry.

SKILL.state compliant: Python-only headless run, NO in-chat HTML, NO invented
names (only FacultyExtractionAgent-extracted profiles), checkpoint-only,
NO DB commit. Official *.ac.th seeds only. Max 2 browser attempts per URL.

Pattern: Wave26 breakthrough GSPA/Bus EN faculty pages
(gspa.nida.ac.th/en/faculty-member/ +22, mba.nida.ac.th/en/about/professor/ +20).

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave27_batchA_browser.py
"""
import os
import sys
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.scrapers.browser_scraper import BrowserScraper  # noqa: E402
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent  # noqa: E402
from scripts.agentic_pipeline.state_reducer import save_state_checkpoint  # noqa: E402

AGENT_STATES_DIR = os.path.join(ROOT, "backend", "data", "agent_states")

NIDA_TH = "สถาบันบัณฑิตพัฒนบริหารศาสตร์"
NIDA_EN = "National Institute of Development Administration"
SU_TH = "มหาวิทยาลัยศิลปากร"
SU_EN = "Silpakorn University"

# Official *.ac.th seeds only.
TARGETS = {
    "wave27_nida_econ": {
        "univ_th": NIDA_TH, "univ_en": NIDA_EN,
        "faculty_th": "คณะพัฒนาเศรษฐกิจ",
        "faculty_en": "Graduate School of Development Economics",
        "seeds": [
            "https://econ.nida.ac.th/en/faculty-member/",
            "https://econ.nida.ac.th/en/",
        ],
    },
    "wave27_nida_env": {
        "univ_th": NIDA_TH, "univ_en": NIDA_EN,
        "faculty_th": "คณะบริหารการพัฒนาสิ่งแวดล้อม",
        "faculty_en": "Graduate School of Environmental Development Administration",
        "seeds": [
            "https://edm.nida.ac.th/en/faculty-member/",
            "https://nida.ac.th/en/",
        ],
    },
    "wave27_nida_bus": {
        "univ_th": NIDA_TH, "univ_en": NIDA_EN,
        "faculty_th": "คณะบริหารธุรกิจ (NIDA Business School)",
        "faculty_en": "NIDA Business School",
        "seeds": [
            "https://mba.nida.ac.th/en/about/professor/",
            "https://mba.nida.ac.th/en/faculty-member/",
        ],
    },
    "wave27_su_ict": {
        "univ_th": SU_TH, "univ_en": SU_EN,
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "faculty_en": "Faculty of Information and Communication Technology",
        "seeds": [
            "https://ict.su.ac.th/?page_id=58",
            "https://ict.su.ac.th/",
        ],
    },
}

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020", "This site can",
    "ERR_CONNECTION", "getaddrinfo failed",
]


def academic_density(text: str) -> int:
    return sum((text or "").count(m) for m in ACADEMIC_MARKERS)


def looks_blocked(html: str | None) -> tuple[bool, str]:
    if not html:
        return True, "browser_empty_or_exception"
    low = html.lower()
    for m in BLOCK_MARKERS:
        if m.lower() in low and academic_density(html) < 5:
            return True, f"browser_block_marker:{m}"
    if len(html) < 1500 and academic_density(html) < 3:
        return True, "browser_thin_or_block_page"
    return False, ""


def run_unit(key: str, t: dict, scraper: BrowserScraper) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=12,
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,
    )
    per_url = []
    for url in t["seeds"]:
        outcome = {"url": url, "attempts": 0, "ok": False, "reason": "", "added": 0}
        html = None
        for attempt in range(2):  # max twice per URL
            outcome["attempts"] = attempt + 1
            try:
                html = scraper.scroll_and_render_all(
                    url, scroll_pause=1.2, max_scrolls=3, extra_wait=2.0
                )
            except Exception as e:  # noqa: BLE001
                outcome["reason"] = f"browser_exception:{type(e).__name__}"
                html = None
            blocked, reason = looks_blocked(html)
            if blocked:
                outcome["reason"] = reason
                time.sleep(2.0)
                continue
            break
        blocked, reason = looks_blocked(html)
        if blocked:
            agent.state.failed_urls.append(url)
            outcome["reason"] = outcome.get("reason") or reason
            per_url.append(outcome)
            print(f"  ⛔ {url} -> {outcome['reason']} (attempts={outcome['attempts']})", flush=True)
            continue
        try:
            before = len(agent.state.faculties)
            patch = agent.step_with_html(html, current_url=url)
            added = len(agent.state.faculties) - before
            outcome.update(ok=True, added=added,
                           reason=f"render_ok_html_chars={len(html or '')}")
            print(f"  ✅ {url} +{len(patch.new_profiles)} new | unit total {len(agent.state.faculties)}", flush=True)
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            outcome["reason"] = f"extraction_failed:{type(e).__name__}"
            print(f"  ❌ {url} extraction failed: {str(e)[:120]}", flush=True)
        per_url.append(outcome)
        time.sleep(1.0)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    bypassed = [u for u in per_url if u["ok"]]
    status = "bypassed" if bypassed and all(u["ok"] for u in per_url) else (
        "partial" if bypassed else "blocked")
    print(f"✨ DONE {key}: {n} verified -> {os.path.basename(export_path)} [{status}]", flush=True)
    return {
        "key": key, "faculty_th": t["faculty_th"], "seeds": t["seeds"],
        "verified_count": n, "export_path": export_path, "checkpoint": ckpt,
        "status": status, "per_url": per_url,
        "failed_urls": list(agent.state.failed_urls),
    }


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    scraper = BrowserScraper(headless=True, page_load_timeout=30)
    results = []
    try:
        for key, t in TARGETS.items():
            print(f"\n=== {key} :: {t['faculty_th']} ===", flush=True)
            try:
                results.append(run_unit(key, t, scraper))
            except Exception as e:  # noqa: BLE001
                print(f"❌ unit {key} fatal: {e}", flush=True)
                results.append({"key": key, "verified_count": 0,
                                "export_path": "", "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave27_batchA_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave27_batchA_browser_only", "db_commit": False,
                   "units": results}, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}", flush=True)


if __name__ == "__main__":
    main()
