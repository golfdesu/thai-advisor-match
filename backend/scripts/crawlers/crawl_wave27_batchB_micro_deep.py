"""Wave27 Batch B (deep-path): MU micro x6 staff-link follow via BrowserScraper.

SKILL.state compliant: headless Python-only, NO in-chat HTML, NO invented names
(only FacultyExtractionAgent-extracted profiles), checkpoint-only, NO DB commit.
mahidol.ac.th only. Landing -> same-site staff-keyword links (cap 10/unit) ->
render each -> step_with_html -> checkpoint -> export.

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave27_batchB_micro_deep.py
"""
import os
import re
import sys
import json
import time
from urllib.parse import urljoin, urlparse

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
MU_TH = "มหาวิทยาลัยมหิดล"
MU_EN = "Mahidol University"

TARGETS = {
    "wave27_mu_rilca": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย (RILCA)",
        "faculty_en": "Research Institute for Languages and Cultures of Asia",
        "seeds": ["https://rilca.mahidol.ac.th/"],
    },
    "wave27_mu_mb": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "สถาบันชีววิทยาศาสตร์โมเลกุล",
        "faculty_en": "Institute of Molecular Biosciences",
        "seeds": ["https://mb.mahidol.ac.th/"],
    },
    "wave27_mu_ss": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
        "faculty_en": "College of Sports Science and Technology",
        "seeds": ["https://ss.mahidol.ac.th/"],
    },
    "wave27_mu_la": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "คณะศิลปศาสตร์",
        "faculty_en": "Faculty of Liberal Arts",
        "seeds": ["https://la.mahidol.ac.th/"],
    },
    "wave27_mu_bart": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "คณะวิศวกรรมศาสตร์ ภาควิชาวิศวกรรมชีวการแพทย์ (BART LAB)",
        "faculty_en": "Faculty of Engineering, Dept. of Biomedical Engineering (BART LAB)",
        "seeds": ["https://eg.mahidol.ac.th/"],
    },
    "wave27_mu_ipsr": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "สถาบันวิจัยประชากรและสังคม (IPSR)",
        "faculty_en": "Institute for Population and Social Research",
        "seeds": ["https://ipsr.mahidol.ac.th/"],
    },
}

STAFF_KW = re.compile(
    r"(personnel|staff|faculty|researcher|people|about|department)",
    re.IGNORECASE,
)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020",
]
CAP_DEEP = 10


def academic_density(text):
    return sum((text or "").count(m) for m in ACADEMIC_MARKERS)


def looks_blocked(html):
    if not html:
        return True, "browser_empty_or_exception"
    low = html.lower()
    for m in BLOCK_MARKERS:
        if m.lower() in low and academic_density(html) < 5:
            return True, f"browser_block_marker:{m}"
    if len(html) < 1500 and academic_density(html) < 3:
        return True, "browser_thin_or_block_page"
    return False, ""


def render(url, scraper):
    html = None
    reason = ""
    for attempt in range(2):
        try:
            html = scraper.scroll_and_render_all(
                url, scroll_pause=1.0, max_scrolls=2, extra_wait=1.5
            )
        except Exception as e:  # noqa: BLE001
            reason = f"browser_exception:{type(e).__name__}"
            html = None
        blocked, b_reason = looks_blocked(html)
        if blocked:
            reason = b_reason
            time.sleep(1.5)
            continue
        reason = f"render_ok_html_chars={len(html or '')}"
        return html, False, reason, attempt + 1
    return html, True, reason, 2


def same_site(url, seed_host):
    try:
        h = urlparse(url).netloc.lower()
    except Exception:
        return False
    return h == seed_host or h.endswith(".mahidol.ac.th") or h == "mahidol.ac.th"


def collect_staff_links(html, base_url, seed_host):
    found = []
    seen = set()
    for m in HREF_RE.finditer(html or ""):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, raw).split("#")[0].strip()
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https"):
            continue
        if not same_site(abs_url, seed_host):
            continue
        path_q = (p.path or "") + "?" + (p.query or "")
        if not STAFF_KW.search(path_q):
            continue
        if abs_url not in seen:
            seen.add(abs_url)
            found.append(abs_url)
    # prioritize most staff-like paths first
    prio = re.compile(r"(personnel|staff|researcher|faculty|people)", re.IGNORECASE)
    found.sort(key=lambda u: (0 if prio.search(urlparse(u).path or "") else 1, len(u)))
    return found[:CAP_DEEP]


def run_unit(key, t, scraper):
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=24,
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,
    )
    per_url = []
    dept_paths = []
    for seed in t["seeds"]:
        seed_host = urlparse(seed).netloc.lower()
        html, blocked, reason, attempts = render(seed, scraper)
        if blocked:
            agent.state.failed_urls.append(seed)
            per_url.append({"url": seed, "ok": False, "reason": reason,
                            "added": 0, "role": "landing"})
            print(f"  landing-blocked {seed} -> {reason}", flush=True)
            continue
        # extract landing itself (may hold staff)
        try:
            before = len(agent.state.faculties)
            agent.step_with_html(html, current_url=seed)
            added = len(agent.state.faculties) - before
        except Exception as e:  # noqa: BLE001
            added = 0
            reason = f"extraction_failed:{type(e).__name__}"
            agent.state.failed_urls.append(seed)
        per_url.append({"url": seed, "ok": True, "reason": reason,
                        "added": added, "role": "landing"})
        print(f"  landing OK {seed} +{added} chars={len(html or '')}", flush=True)
        # follow same-site staff links
        staff_links = collect_staff_links(html, seed, seed_host)
        dept_paths = [urlparse(u).path or "/" for u in staff_links]
        print(f"  staff_links[{len(staff_links)}]: {dept_paths}", flush=True)
        if not staff_links:
            per_url.append({"url": "(no-staff-links)", "ok": False,
                            "reason": "no_staff_links_on_landing", "added": 0,
                            "role": "follow"})
        for url in staff_links:
            dhtml, dblocked, dreason, _ = render(url, scraper)
            if dblocked:
                agent.state.failed_urls.append(url)
                per_url.append({"url": url, "ok": False, "reason": dreason,
                                "added": 0, "role": "deep"})
                print(f"  deep-blocked {url} -> {dreason}", flush=True)
                continue
            try:
                b2 = len(agent.state.faculties)
                patch = agent.step_with_html(dhtml, current_url=url)
                added2 = len(agent.state.faculties) - b2
                per_url.append({"url": url, "ok": True,
                                "reason": f"render_ok_html_chars={len(dhtml or '')}",
                                "added": added2, "role": "deep"})
                print(f"  deep OK {url} +{len(patch.new_profiles)} "
                      f"unit_total={len(agent.state.faculties)}", flush=True)
            except Exception as e:  # noqa: BLE001
                agent.state.failed_urls.append(url)
                per_url.append({"url": url, "ok": False,
                                "reason": f"extraction_failed:{type(e).__name__}",
                                "added": 0, "role": "deep"})
                print(f"  deep-extract-fail {url}: {str(e)[:100]}", flush=True)
            time.sleep(0.8)
        time.sleep(0.5)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    print(f"DONE {key}: {n} verified -> {os.path.basename(export_path)}", flush=True)
    return {
        "key": key, "faculty_th": t["faculty_th"], "seeds": t["seeds"],
        "verified_count": n, "export_path": export_path, "checkpoint": ckpt,
        "dept_paths": dept_paths, "per_url": per_url,
        "failed_urls": list(agent.state.failed_urls),
    }


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    scraper = BrowserScraper(headless=True, page_load_timeout=25)
    results = []
    try:
        for key, t in TARGETS.items():
            print(f"\n=== {key} :: {t['faculty_th']} ===", flush=True)
            try:
                results.append(run_unit(key, t, scraper))
            except Exception as e:  # noqa: BLE001
                print(f"unit {key} fatal: {e}", flush=True)
                results.append({"key": key, "verified_count": 0,
                                "export_path": "", "dept_paths": [],
                                "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave27_batchB_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave27_batchB_micro_deep", "db_commit": False,
                   "units": results}, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}",
          flush=True)


if __name__ == "__main__":
    main()
