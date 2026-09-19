"""Wave37 MFU sinology + science (headless, SKILL.state compliant).

Scope: Mae Fah Luang University ONLY (mfu.ac.th hosts only).
Checkpoint-only, NO DB commit, NO invented names (only FacultyExtractionAgent
extractions), NO in-chat HTML. Python-only run, single shared headless browser.

Method per unit: static probe -> BrowserScraper.render each seed ->
same-site staff-keyword link follow incl. lecturer-category subpages
(liberalarts hub + 4 categories pattern) -> FacultyExtractionAgent
step_with_html per page -> name prune -> checkpoint ->
export backend/data/agent_states/wave37_mfu_<key>_export.py.

cli_runner.py equivalents: --univ-th "มหาวิทยาลัยแม่ฟ้าหลวง"
--faculty-th "สำนักวิชาจีนวิทยา" / "สำนักวิชาวิทยาศาสตร์"
--max-steps 12 --no-wiki.

Sinology uses EN-name-accepting extraction: keep real 2-token person names
Thai OR EN with title; drop script-mixed (Thai+Latin / Thai+CJK / Thai+Arabic
contamination such as wave35-style mojibake).

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave37_mfu_sinology_science_headless.py
"""
import os
import re
import sys
import json
import time
import ssl
import urllib.request
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

MFU_TH = "มหาวิทยาลัยแม่ฟ้าหลวง"
MFU_EN = "Mae Fah Luang University"
PORTAL = "https://www.mfu.ac.th/en/academics.html"

TARGETS = {
    "wave37_mfu_sinology": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาจีนวิทยา",
        "faculty_en": "School of Sinology",
        "en_accepting": True,
        "seeds": [
            "https://sinology.mfu.ac.th/",
            "https://sinology.mfu.ac.th/en/",
            "https://www.mfu.ac.th/en/academics/school-of-sinology.html",
            "https://schooldirectory.mfu.ac.th/school/school-of-sinology.html",
            PORTAL,
        ],
    },
    "wave37_mfu_science": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "faculty_en": "School of Science",
        "en_accepting": False,
        "seeds": [
            "https://science.mfu.ac.th/",
            "https://science.mfu.ac.th/en/",
            "https://scis.mfu.ac.th/",
            "https://scis.mfu.ac.th/en/",
            "https://www.mfu.ac.th/en/academics/school-of-science.html",
            PORTAL,
        ],
    },
}

MAX_URLS_PER_UNIT = 12  # --max-steps 12 equivalent

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020",
]
STAFF_HINTS = ("staff", "faculty", "personnel", "lecturer", "teacher",
               "academic", "about", "people", "member", "directory",
               "executive", "school", "department", "division", "program")
BOILERPLATE = (
    "สถานที่ติดต่อ", "ติดต่อ", "สำนักวิชา", "สาขาวิชา", "ภาควิชา",
    "มหาวิทยาลัย", "คณะ", "หลักสูตร", "สำนักงาน", "ฝ่าย",
    "computer", "science group", "research group", "breadcrumb",
    "menu", "home", "download", "sidebar", "office",
)
_TITLE_STRIP = re.compile(
    r"^(?:ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์\s*ดร\.|อาจารย์|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|"
    r"Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lecturer|Professor)\s*",
    re.IGNORECASE,
)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def is_mfu_host(url: str) -> bool:
    try:
        return urlparse(url).netloc.lower().endswith("mfu.ac.th")
    except Exception:
        return False


def fetch_static(url: str, timeout: int = 15):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), resp.getcode()
    except Exception:
        return "", 0


def academic_density(text: str) -> int:
    return sum((text or "").count(m) for m in ACADEMIC_MARKERS)


def looks_blocked(html) -> tuple:
    if not html:
        return True, "browser_empty_or_exception"
    low = html.lower()
    for m in BLOCK_MARKERS:
        if m.lower() in low and academic_density(html) < 5:
            return True, f"browser_block_marker:{m}"
    if len(html) < 1500 and academic_density(html) < 3:
        return True, "browser_thin_or_block_page"
    return False, ""


def _scripts_present(base: str) -> set:
    scripts = set()
    if re.search(r"[ก-๙]", base):
        scripts.add("thai")
    if re.search(r"[A-Za-z]", base):
        scripts.add("latin")
    if re.search(r"[一-鿿぀-ヿ가-힣]", base):
        scripts.add("cjk")
    if re.search(r"[؀-ۿЀ-џހ-޿]", base):
        scripts.add("other")
    return scripts


def valid_person_name(full_name_th, en_accepting: bool = False) -> bool:
    """2-token person-name rule in Python. EN-accepting mode (sinology): keep
    real 2-token Thai OR EN names with title; drop script-mixed. Standard mode
    (science): same hygiene incl. script-mixed drop. No invented names."""
    if not full_name_th:
        return False
    low = full_name_th.lower()
    if any(b in low for b in BOILERPLATE):
        return False
    base = _TITLE_STRIP.sub("", full_name_th.strip()).strip(" .")
    # Iteratively strip stacked titles (e.g. double-title normalizer residue).
    prev = None
    while prev != base:
        prev = base
        base = _TITLE_STRIP.sub("", base).strip(" .")
    tokens = [t for t in re.split(r"\s+", base) if t]
    if len(tokens) < 2:
        return False
    if any(len(t) < 2 for t in tokens):
        return False
    if re.search(r"@|http|www\.|\.ac\.th|\d{3,}", base):
        return False
    scripts = _scripts_present(base)
    if len(scripts) > 1:
        return False  # drop script-mixed contamination
    if "other" in scripts:
        return False
    if scripts == {"cjk"}:
        return False  # keep Thai OR EN only per spec
    if not en_accepting and scripts == {"latin"}:
        # Standard mode still accepts clean EN transliterations (agent emits
        # EN first/last with Thai-title full names); script-mixed already out.
        pass
    return True


def prune_invalid(agent, en_accepting: bool) -> int:
    bad_ids = [fid for fid, f in agent.state.faculties.items()
               if not valid_person_name(f.get("full_name_th", ""),
                                        en_accepting=en_accepting)]
    for fid in bad_ids:
        agent.state.faculties.pop(fid, None)
    if bad_ids:
        agent.state.dedup_thai_names = {
            k: v for k, v in agent.state.dedup_thai_names.items() if v not in bad_ids
        }
        agent.state.dedup_emails = {
            k: v for k, v in agent.state.dedup_emails.items() if v not in bad_ids
        }
    return len(bad_ids)


def collect_staff_links(html, base_url):
    found, seen = [], set()
    for m in HREF_RE.finditer(html or ""):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, raw).split("#")[0].strip()
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https") or not is_mfu_host(abs_url):
            continue
        path_q = (p.path or "") + "?" + (p.query or "")
        if not any(h in path_q.lower() for h in STAFF_HINTS):
            continue
        if abs_url not in seen:
            seen.add(abs_url)
            found.append(abs_url)
    prio = re.compile(r"(personnel|staff|faculty|people|academic|lecturer)",
                       re.IGNORECASE)
    found.sort(key=lambda u: (0 if prio.search(urlparse(u).path or "") else 1,
                              len(u)))
    return found


def render(url, scraper):
    html, reason = None, ""
    for _ in range(2):
        try:
            html = scraper.scroll_and_render_all(
                url, scroll_pause=1.2, max_scrolls=3, extra_wait=2.0)
        except Exception as e:  # noqa: BLE001
            reason = f"browser_exception:{type(e).__name__}"
            html = None
        blocked, b_reason = looks_blocked(html)
        if blocked:
            reason = b_reason
            time.sleep(2.0)
            continue
        reason = f"render_ok_html_chars={len(html or '')}"
        return html, False, reason
    return html, True, reason


def run_unit(key: str, t: dict, scraper: BrowserScraper) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=MAX_URLS_PER_UNIT,
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,  # --no-wiki: strict faculty-scoped run
    )
    queue = [u for u in dict.fromkeys(t["seeds"]) if is_mfu_host(u)]
    queue = queue[:MAX_URLS_PER_UNIT]
    visited, per_url = set(), []
    while queue and len(visited) < MAX_URLS_PER_UNIT:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        static_html, status = fetch_static(url)
        s_chars, s_dens = len(static_html), academic_density(static_html)
        html, blocked, reason = render(url, scraper)
        outcome = {"url": url, "attempts": 1, "ok": False, "reason": reason,
                   "static_chars": s_chars, "static_density": s_dens,
                   "static_http": status, "rendered_chars": len(html or ""),
                   "rendered_density": academic_density(html or ""),
                   "added": 0, "pruned": 0}
        if html and s_dens > outcome["rendered_density"] and s_dens >= 5:
            html = static_html
            reason += "|used_static_denser"
        blocked, b_reason = looks_blocked(html)
        if blocked:
            agent.state.failed_urls.append(url)
            outcome["reason"] = reason or b_reason
            per_url.append(outcome)
            print(f"  STOP {url} -> {outcome['reason']} "
                  f"(static={s_chars}c/d{s_dens} render={outcome['rendered_chars']}c/"
                  f"d{outcome['rendered_density']})", flush=True)
            continue
        try:
            before = len(agent.state.faculties)
            patch = agent.step_with_html(html, current_url=url)
            pruned = prune_invalid(agent, t["en_accepting"])
            added = len(agent.state.faculties) - before
            outcome.update(ok=True, added=added, pruned=pruned,
                           reason=f"{reason}|patch_new={len(patch.new_profiles)}|"
                                  f"pruned={pruned}")
            print(f"  OK {url} +{len(patch.new_profiles)} patch / +{added} net "
                  f"(pruned {pruned}) | unit total {len(agent.state.faculties)}",
                  flush=True)
            for u in collect_staff_links(html, url):
                if u not in visited and u not in queue \
                        and len(visited) + len(queue) < MAX_URLS_PER_UNIT:
                    queue.append(u)
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            outcome["reason"] = f"extraction_failed:{type(e).__name__}"
            print(f"  FAIL {url} extraction failed: {str(e)[:120]}", flush=True)
        per_url.append(outcome)
        time.sleep(1.0)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    oks = [u for u in per_url if u["ok"]]
    status = ("verified" if oks else "blocked")
    print(f"DONE {key}: {n} verified -> {os.path.basename(export_path)} [{status}]",
          flush=True)
    return {
        "key": key, "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
        "verified_count": n, "export_path": export_path, "checkpoint": ckpt,
        "status": status, "per_url": per_url,
        "failed_urls": list(agent.state.failed_urls),
        "serp_needed": (n == 0),
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
                print(f"UNIT {key} fatal: {e}", flush=True)
                results.append({"key": key, "verified_count": 0,
                                "export_path": "", "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave37_mfu_sinology_science_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave37_mfu_sinology_science_headless", "db_commit": False,
                   "univ_scope": "mfu.ac.th only", "units": results},
                  f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}",
          flush=True)


if __name__ == "__main__":
    main()
