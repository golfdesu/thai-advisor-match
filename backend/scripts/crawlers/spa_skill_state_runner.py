"""
SPA-aware SKILL.state Faculty Extraction Runner
Crawls university faculty pages (static fetch first; Selenium fallback for JS pages)
and feeds rendered HTML into the SKILL.state FacultyExtractionAgent (RapidFuzz dedup,
checkpointing) then exports the verified dataset for ingestion.

Usage:
  python -X utf8 scripts/crawlers/spa_skill_state_runner.py --key mu_vet --steps 12
Targets are defined in scripts/crawlers/spa_targets.py (populated from SERP discovery).
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.scrapers.browser_scraper import BrowserScraper
from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from scripts.agentic_pipeline.state_reducer import save_state_checkpoint

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS_PATH = os.path.join(BACKEND_DIR, "scripts", "crawlers", "spa_targets.json")
DISCOVERY_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "seed_discovery_results.json")

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]


def academic_density(text: str) -> int:
    return sum(text.count(m) for m in ACADEMIC_MARKERS)


def fetch_static(url: str, timeout: int = 20) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "th-TH,th;q=0.9,en;q=0.7",
            },
        )
        return urllib.request.urlopen(req, context=ctx, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return ""


def same_site(url: str, base: str) -> bool:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.endswith(urlparse(base).netloc.split(".")[-3:] if False else urlparse(base).netloc) or urlparse(url).netloc.endswith("." + urlparse(base).netloc)
    except Exception:
        return False


def run_target(key: str, max_steps: int = 12, use_browser_always: bool = False):
    targets = json.load(open(TARGETS_PATH, encoding="utf-8"))
    if key not in targets:
        print(f"❌ Unknown target key: {key}")
        return
    t = targets[key]
    seeds = t["seeds"]

    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        max_steps=max_steps,
        checkpoint_dir="data/agent_states",
        auto_lookup_wiki=False,
    )
    scraper = None
    queue = list(dict.fromkeys(seeds))
    visited = set()
    steps = 0

    while queue and steps < max_steps:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        steps += 1
        print(f"\n[Step {steps}] 🌐 {url}")

        html = fetch_static(url)
        if use_browser_always or academic_density(html) < 5:
            if scraper is None:
                print("  🖥️ Rendering with headless browser (SPA detected)...")
                scraper = BrowserScraper()
            rendered = scraper.scroll_and_render_all(url, scroll_pause=1.2, max_scrolls=4)
            if rendered and academic_density(rendered) > academic_density(html):
                html = rendered

        if not html:
            agent.state.failed_urls.append(url)
            continue

        try:
            patch = agent.step_with_html(html, current_url=url)
            print(f"  ✅ +{len(patch.new_profiles)} profiles | total {len(agent.state.faculties)}")
            print(f"  📊 {patch.summary_of_changes[:150]}")
            base = seeds[0]
            for u in patch.discovered_urls:
                if u not in visited and same_site(u, base):
                    queue.append(u)
        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
        time.sleep(1.0)

    if scraper:
        scraper.close()

    agent.state.status = "completed"
    save_state_checkpoint(agent.state, output_dir=agent.checkpoint_dir)

    out_file = os.path.join("data", "agent_states", f"spa_{key}_export.py")
    code = agent.export_as_dataset_python()
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"\n✨ DONE {key}: {len(agent.state.faculties)} verified faculties -> {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--browser", action="store_true", help="Always render with headless browser")
    args = parser.parse_args()
    run_target(args.key, max_steps=args.steps, use_browser_always=args.browser)
