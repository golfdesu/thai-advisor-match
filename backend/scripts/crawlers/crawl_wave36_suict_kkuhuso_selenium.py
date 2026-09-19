"""Wave36 selenium-interaction (headless, SKILL.state compliant).

Scope: official *.ac.th ONLY (su.ac.th / kku.ac.th). Checkpoint-only,
NO DB commit, NO invented names (only FacultyExtractionAgent extractions),
NO in-chat HTML. Single shared headless Selenium driver (selenium only,
NO Playwright), used DIRECTLY (driver.get + CLICK expandables, cap N/page).

Units:
  wave36_su_ict  :: SU ICT (ict.su.ac.th/?page_id=58, 227K-char Elementor
                    page, agent extracts ~1/pass). Click elementor
                    tabs/accordions/toggles to expand hidden staff sections,
                    collect page_source per state, feed EACH to
                    FacultyExtractionAgent.step_with_html. No expandables ->
                    record 0 + reason.
  wave36_kku_huso :: KKU HUSO (huso.kku.ac.th JS-shell; roster suspected
                    behind personnel-system pages). BrowserScraper-render
                    sitemap-adjacent paths (/personnel/ /staff/ /people/
                    /en/staff/) + click any staff-directory tabs via
                    selenium. Feed rendered HTML to agent.

Exports: backend/data/agent_states/wave36_<key>_export.py.

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave36_suict_kkuhuso_selenium.py
"""
import hashlib
import os
import re
import ssl
import sys
import time
import urllib.request
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent  # noqa: E402
from scripts.agentic_pipeline.state_reducer import save_state_checkpoint  # noqa: E402

AGENT_STATES_DIR = os.path.join(ROOT, "backend", "data", "agent_states")

TARGETS = {
    "wave36_su_ict": {
        "univ_th": "มหาวิทยาลัยศิลปากร",
        "univ_en": "Silpakorn University",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "faculty_en": "Faculty of Information and Communication Technology",
        "seeds": [
            "https://ict.su.ac.th/?page_id=58",
            "https://ict.su.ac.th/",
            "https://ict.su.ac.th/personnel/",
            "https://ict.su.ac.th/staff/",
            "https://ict.su.ac.th/people/",
        ],
    },
    "wave36_kku_huso": {
        "univ_th": "มหาวิทยาลัยขอนแก่น",
        "univ_en": "Khon Kaen University",
        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        "faculty_en": "Faculty of Humanities and Social Sciences",
        "seeds": [
            "https://huso.kku.ac.th/",
            "https://huso.kku.ac.th/en/",
            "https://huso.kku.ac.th/personnel/",
            "https://huso.kku.ac.th/staff/",
            "https://huso.kku.ac.th/people/",
            "https://huso.kku.ac.th/en/staff/",
        ],
    },
}

ALLOWED_SUFFIXES = (".su.ac.th", ".kku.ac.th", "su.ac.th", "kku.ac.th")
MAX_CLICKS_PER_PAGE = 6
MAX_STEP_CALLS_PER_UNIT = 60

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = ["403 Forbidden", "Access Denied", "Just a moment",
                 "Attention Required", "cf-challenge", "Error code 1020"]
BOILERPLATE = ("สถานที่ติดต่อ", "ติดต่อ", "สำนักวิชา", "สาขาวิชา", "ภาควิชา",
               "มหาวิทยาลัย", "คณะ", "หลักสูตร", "สำนักงาน", "ฝ่าย",
               "computer", "science group", "research group", "breadcrumb",
               "menu", "home", "download", "sidebar", "office")
_TITLE_STRIP = re.compile(
    r"^(?:ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์\s*ดร\.|อาจารย์|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|"
    r"Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lecturer|Professor)\s*",
    re.IGNORECASE,
)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

NEXT_TEXTS = {"next", "ถัดไป", "หน้าถัดไป", "»", "›", ">", "more"}


def is_official(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().split(":")[0]
        return host.endswith(ALLOWED_SUFFIXES)
    except Exception:
        return False


def fetch_static(url: str, timeout: int = 15):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/128.0.0.0 Safari/537.36",
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


def valid_person_name(full_name_th) -> bool:
    if not full_name_th:
        return False
    low = full_name_th.lower()
    if any(b in low for b in BOILERPLATE):
        return False
    base = _TITLE_STRIP.sub("", full_name_th.strip()).strip(" .")
    tokens = [t for t in re.split(r"\s+", base) if t]
    if len(tokens) < 2:
        return False
    if any(len(t) < 2 for t in tokens):
        return False
    if re.search(r"@|http|www\.|\.ac\.th|\d{3,}", base):
        return False
    return True


def prune_invalid(agent) -> int:
    bad_ids = [fid for fid, f in agent.state.faculties.items()
               if not valid_person_name(f.get("full_name_th", ""))]
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


def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2400")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
    opts.set_capability("acceptInsecureCerts", True)
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def snapshot_hash(html: str) -> str:
    return hashlib.md5((html or "").encode("utf-8", errors="ignore")).hexdigest()


EXPANDABLE_XPATHS = [
    "//*[contains(@class,'elementor-tab-title')]",
    "//*[contains(@class,'elementor-toggle-title')]",
    "//*[contains(@class,'elementor-accordion-title')]",
    "//*[@role='tab']",
    "//*[contains(@class,'nav-tabs')]//a",
    "//*[contains(@class,'vc_tta-panel-heading')]",
    "//*[contains(@class,'elementor-tabs-wrapper')]//*[self::a or self::div]",
]


def find_expandable_clickables(driver):
    """Return up to MAX_CLICKS_PER_PAGE expandable/tab/pagination elements.

    Priority: elementor tabs/accordions/toggles + role=tab first,
    then numbered pagination + next controls.
    Only displayed + enabled elements are returned.
    """
    try:
        from selenium.webdriver.common.by import By
    except Exception:
        return [], "no_selenium_by"
    expandables, numbered, nexts = [], [], []
    seen = set()
    try:
        cand = []
        for xp in EXPANDABLE_XPATHS:
            try:
                cand.extend(driver.find_elements(By.XPATH, xp))
            except Exception:
                continue
        try:
            cand.extend(driver.find_elements(By.XPATH, "//a | //button"))
        except Exception as e:  # noqa: BLE001
            return [], f"find_elements_failed:{type(e).__name__}"
    except Exception as e:  # noqa: BLE001
        return [], f"find_elements_failed:{type(e).__name__}"
    for el in cand:
        try:
            if not (el.is_displayed() and el.is_enabled()):
                continue
            text = (el.text or "").strip()
            href = (el.get_attribute("href") or "")
            cls = (el.get_attribute("class") or "") + " " + (
                el.get_attribute("id") or "")
            key = (text[:28], href[-80:], cls[:60])
            if key in seen:
                continue
            seen.add(key)
            is_elementor = bool(re.search(
                r"elementor|vc_tta|nav-tabs|accordion|toggle",
                cls, re.IGNORECASE))
            is_tab_role = False
            try:
                is_tab_role = (el.get_attribute("role") or "") == "tab"
            except Exception:
                pass
            is_numbered = bool(re.fullmatch(r"\d{1,3}", text))
            href_paged = bool(re.search(r"page|paged|paging",
                                        href + " " + cls, re.IGNORECASE))
            if is_elementor or is_tab_role:
                expandables.append(el)
            elif is_numbered and href_paged:
                numbered.append(el)
            elif text in NEXT_TEXTS:
                nexts.append(el)
        except Exception:
            continue
    # De-dup expandables that are actually pagination numbers already covered.
    ordered = expandables + numbered + nexts
    if not ordered:
        return [], (f"no_expandable_elements:elementor_tabs=0 "
                    f"accordions=0 toggles=0 role_tab=0 pagination=0")
    detail = (f"expandable={len(expandables)} "
              f"numbered={len(numbered)} next={len(nexts)}")
    return ordered[:MAX_CLICKS_PER_PAGE], detail


def describe_el(el) -> str:
    try:
        cls = (el.get_attribute("class") or "")[:28]
        return f"<{el.tag_name} cls={cls!r} text={(el.text or '').strip()[:16]!r}>"
    except Exception:
        return "<el?>"


def feed(agent, html: str, url: str):
    """Feed one page_source to SKILL.state agent; return (added, patch_new, err)."""
    before = len(agent.state.faculties)
    try:
        patch = agent.step_with_html(html, current_url=url)
        pruned = prune_invalid(agent)
        added = len(agent.state.faculties) - before
        return added, len(patch.new_profiles), pruned, ""
    except Exception as e:  # noqa: BLE001
        return 0, 0, 0, f"extraction_failed:{type(e).__name__}:{str(e)[:100]}"


def run_unit(key: str, t: dict, driver) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=MAX_STEP_CALLS_PER_UNIT,
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,  # strict faculty-scoped run
    )
    seeds = [u for u in dict.fromkeys(t["seeds"]) if is_official(u)]
    per_url = []
    step_calls = 0

    for url in seeds:
        if step_calls >= MAX_STEP_CALLS_PER_UNIT:
            per_url.append({"url": url, "ok": False,
                            "reason": "skipped_step_budget_exhausted"})
            continue
        static_html, status = fetch_static(url)
        s_chars, s_dens = len(static_html), academic_density(static_html)
        try:
            driver.get(url)
            time.sleep(3.0)
            try:
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2)
            except Exception:
                pass
            html0 = driver.page_source or ""
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False,
                            "reason": f"selenium_get_failed:{type(e).__name__}",
                            "static_chars": s_chars, "static_density": s_dens,
                            "static_http": status, "clicks": 0, "added": 0})
            print(f"  GET-FAIL {url} [{type(e).__name__}]", flush=True)
            continue
        blocked, b_reason = looks_blocked(html0)
        entry = {"url": url, "ok": False, "reason": "",
                 "static_chars": s_chars, "static_density": s_dens,
                 "static_http": status,
                 "rendered_chars": len(html0),
                 "rendered_density": academic_density(html0),
                 "clicks": 0, "click_detail": [], "added": 0, "pruned": 0}
        if blocked:
            agent.state.failed_urls.append(url)
            entry["reason"] = b_reason
            per_url.append(entry)
            print(f"  STOP {url} -> {b_reason} "
                  f"(static={s_chars}c/d{s_dens} render={len(html0)}c/"
                  f"d{entry['rendered_density']})", flush=True)
            continue
        added, patch_new, pruned, err = feed(agent, html0, url)
        step_calls += 1
        entry["added"] = added
        entry["pruned"] = pruned
        if err:
            agent.state.failed_urls.append(url)
            entry["reason"] = err
            per_url.append(entry)
            print(f"  FAIL {url} {err}", flush=True)
            continue
        seen_hashes = {snapshot_hash(html0)}
        clicks = 0
        click_detail = []
        for _ in range(MAX_CLICKS_PER_PAGE):
            clickables, finder_reason = find_expandable_clickables(driver)
            if not clickables:
                click_detail.append(f"stop:{finder_reason}")
                break
            el = clickables[0]
            label = describe_el(el)
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.5)
                el.click()
            except Exception as e:  # noqa: BLE001
                click_detail.append(f"click_failed:{label}:{type(e).__name__}")
                break
            time.sleep(2.5)
            try:
                html_c = driver.page_source or ""
            except Exception:
                click_detail.append(f"pagesource_failed_after:{label}")
                break
            h = snapshot_hash(html_c)
            clicks += 1
            if h in seen_hashes:
                click_detail.append(f"dup_content_stop:{label}")
                break
            seen_hashes.add(h)
            if step_calls >= MAX_STEP_CALLS_PER_UNIT:
                click_detail.append(f"budget_stop_after:{label}")
                break
            a2, p2, _, e2 = feed(agent, html_c, f"{url}#click{clicks}")
            step_calls += 1
            entry["added"] += a2
            click_detail.append(
                f"clicked:{label}:chars={len(html_c)}:patch={p2}:err={e2 or '-'}")
            if e2:
                break
        entry["clicks"] = clicks
        entry["click_detail"] = click_detail
        entry["ok"] = True
        entry["reason"] = (
            f"render_ok_html_chars={len(html0)}|patch_new={patch_new}|"
            f"pruned={pruned}|clicks={clicks}")
        per_url.append(entry)
        print(f"  OK {url} patch={patch_new} net+{entry['added']} "
              f"clicks={clicks} | unit total {len(agent.state.faculties)}",
              flush=True)
        time.sleep(1.0)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    n = len(agent.state.faculties)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    interaction_lines = [
        f"{p['url']} clicks={p.get('clicks', 0)} "
        f"[{'; '.join(p.get('click_detail', [])[:3])}]" if p.get("ok")
        else f"{p['url']} FAILED {p.get('reason', '')}"
        for p in per_url
    ]
    header = (f'"""Wave36 selenium-interaction checkpoint-only export ({key}).\n'
              f"Univ={t['univ_th']} Faculty={t['faculty_th']}.\n"
              f"Method: selenium webdriver direct (driver.get + CLICK "
              f"elementor tabs/accordions/toggles + staff-directory tabs + "
              f"pagination, cap {MAX_CLICKS_PER_PAGE}/page); every collected "
              f"page_source fed to "
              f"FacultyExtractionAgent.step_with_html (step_calls={step_calls}).\n"
              f"Verified count in body: {n}. Official *.ac.th only, NO DB commit.\n"
              f"Interaction: {' | '.join(interaction_lines[:8])}\n\"\"\"\n")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(agent.export_as_dataset_python())
    oks = [u for u in per_url if u.get("ok")]
    status = "verified" if oks else "blocked"
    total_clicks = sum(p.get("clicks", 0) for p in per_url)
    print(f"DONE {key}: {n} verified, {total_clicks} clicks -> "
          f"{os.path.basename(export_path)} [{status}]", flush=True)
    return {"key": key, "faculty_th": t["faculty_th"],
            "faculty_en": t["faculty_en"], "verified_count": n,
            "export_path": export_path, "checkpoint": ckpt,
            "status": status, "per_url": per_url,
            "failed_urls": list(agent.state.failed_urls),
            "total_clicks": total_clicks, "step_calls": step_calls}


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    driver = make_driver()
    results = []
    try:
        for key, t in TARGETS.items():
            print(f"\n=== {key} :: {t['faculty_th']} ===", flush=True)
            try:
                results.append(run_unit(key, t, driver))
            except Exception as e:  # noqa: BLE001
                print(f"UNIT {key} fatal: {e}", flush=True)
                results.append({"key": key, "verified_count": 0,
                                "export_path": "", "total_clicks": 0,
                                "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave36_selenium_summary.json")
    import json as _json
    with open(summary_path, "w", encoding="utf-8") as f:
        _json.dump({"batch": "wave36_selenium_interaction", "db_commit": False,
                    "univ_scope": "su.ac.th + kku.ac.th only",
                    "units": results}, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> "
          f"{summary_path}", flush=True)


if __name__ == "__main__":
    main()
