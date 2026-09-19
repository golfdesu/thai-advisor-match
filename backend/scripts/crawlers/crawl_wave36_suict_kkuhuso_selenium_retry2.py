"""Wave36 retry2: SU ICT JS-click overlay bypass + KKU HUSO 2nd-hop profiles.

Scope: official *.ac.th ONLY. Headless selenium only (no Playwright).
Checkpoint-only, NO DB commit, NO invented names, NO in-chat HTML.

1. SU ICT (https://ict.su.ac.th/?page_id=58): prior el.click() hit
   ElementClickInterceptedException (overlay). Retry with JS clicks:
   driver.execute_script("arguments[0].click();", el) on nav candidates
   (nav/header/elementor-item) + elementor tab/toggle/accordion widgets;
   fallback el.send_keys(Keys.ENTER). page_source per state -> agent.
2. KKU HUSO (https://huso.kku.ac.th/en/staff/ 107K chars dens 16 patch 0):
   follow 2ND-HOP individual profile/person links on that page (cap 15):
   driver.get each, feed page_source to agent.

Faculty scope (--no-wiki equivalent auto_lookup_wiki=False):
  SU  --univ-th "มหาวิทยาลัยศิลปากร" --faculty-th "คณะเทคโนโลยีสารสนเทศและการสื่อสาร"
  KKU --univ-th "มหาวิทยาลัยขอนแก่น" --faculty-th "คณะมนุษยศาสตร์และสังคมศาสตร์"
Exports: backend/data/agent_states/wave36_<key>_export.py
Usage (repo root): python backend/scripts/crawlers/crawl_wave36_suict_kkuhuso_selenium_retry2.py
"""
import hashlib
import os
import re
import ssl
import sys
import time
import urllib.request
from urllib.parse import urljoin, urlparse

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
        "seeds": ["https://ict.su.ac.th/?page_id=58"],
    },
    "wave36_kku_huso": {
        "univ_th": "มหาวิทยาลัยขอนแก่น",
        "univ_en": "Khon Kaen University",
        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        "faculty_en": "Faculty of Humanities and Social Sciences",
        "seeds": ["https://huso.kku.ac.th/en/staff/"],
    },
}
ALLOWED_SUFFIXES = (".su.ac.th", ".kku.ac.th", "su.ac.th", "kku.ac.th")
MAX_JS_CLICKS = 8
MAX_HOPS = 15
MAX_STEPS = 60

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
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


def is_official(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().split(":")[0]
        return host.endswith(ALLOWED_SUFFIXES)
    except Exception:
        return False


def academic_density(text: str) -> int:
    return sum((text or "").count(m) for m in ACADEMIC_MARKERS)


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
    bad = [fid for fid, f in agent.state.faculties.items()
           if not valid_person_name(f.get("full_name_th", ""))]
    for fid in bad:
        agent.state.faculties.pop(fid, None)
    if bad:
        agent.state.dedup_thai_names = {
            k: v for k, v in agent.state.dedup_thai_names.items() if v not in bad}
        agent.state.dedup_emails = {
            k: v for k, v in agent.state.dedup_emails.items() if v not in bad}
    return len(bad)


def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2400")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/128.0.0.0 Safari/537.36")
    opts.set_capability("acceptInsecureCerts", True)
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(30)
    return d


def h(html: str) -> str:
    return hashlib.md5((html or "").encode("utf-8", errors="ignore")).hexdigest()


def feed(agent, html: str, url: str):
    before = len(agent.state.faculties)
    try:
        patch = agent.step_with_html(html, current_url=url)
        pruned = prune_invalid(agent)
        return len(agent.state.faculties) - before, len(patch.new_profiles), pruned, ""
    except Exception as e:  # noqa: BLE001
        return 0, 0, 0, f"extraction_failed:{type(e).__name__}:{str(e)[:100]}"


def describe(el) -> str:
    try:
        return (f"<{el.tag_name} cls={(el.get_attribute('class') or '')[:26]!r} "
                f"text={(el.text or '').strip()[:18]!r}>")
    except Exception:
        return "<el?>"


SU_JS_XPATHS = [
    "//nav//a", "//header//a",
    "//*[contains(@class,'elementor-nav')]//a",
    "//*[contains(@class,'elementor-item')]",
    "//*[contains(@class,'elementor-tab-title')]",
    "//*[contains(@class,'elementor-toggle-title')]",
    "//*[contains(@class,'elementor-accordion-title')]",
    "//*[@role='tab']",
]


def collect_su_candidates(driver):
    from selenium.webdriver.common.by import By
    els, seen = [], set()
    for xp in SU_JS_XPATHS:
        try:
            els.extend(driver.find_elements(By.XPATH, xp))
        except Exception:
            continue
    out = []
    for el in els:
        try:
            if not (el.is_displayed() and el.is_enabled()):
                continue
            key = ((el.text or "")[:24], (el.get_attribute("class") or "")[:40])
            if key in seen:
                continue
            seen.add(key)
            out.append(el)
        except Exception:
            continue
    return out[:MAX_JS_CLICKS * 2]


def js_click(driver, el) -> str:
    """JS click primary, ENTER-key fallback. Returns method or raises."""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.4)
        driver.execute_script("arguments[0].click();", el)
        return "js"
    except Exception as e1:  # noqa: BLE001
        try:
            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.ENTER)
            return "enter"
        except Exception:
            raise e1


def run_su(key, t, driver) -> dict:
    from selenium.webdriver.common.by import By  # noqa: F401
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"], target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"], target_faculty_en=t["faculty_en"],
        session_id=key, max_steps=MAX_STEPS, checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False)
    url = t["seeds"][0]
    per_url, step_calls, clicks, details = [], 0, 0, []
    driver.get(url)
    time.sleep(3.0)
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)
    except Exception:
        pass
    html0 = driver.page_source or ""
    a0, p0, pr0, e0 = feed(agent, html0, url)
    step_calls += 1
    seen = {h(html0)}
    cands = collect_su_candidates(driver)
    details.append(f"nav_candidates={len(cands)} base_chars={len(html0)} "
                   f"dens={academic_density(html0)} patch={p0} err={e0 or '-'}")
    for el in cands[:MAX_JS_CLICKS]:
        if step_calls >= MAX_STEPS:
            details.append("budget_stop")
            break
        label = describe(el)
        try:
            method = js_click(driver, el)
        except Exception as e:  # noqa: BLE001
            details.append(f"click_failed:{label}:{type(e).__name__}")
            continue
        time.sleep(2.5)
        try:
            html_c = driver.page_source or ""
        except Exception:
            details.append(f"pagesource_failed_after:{label}")
            break
        if h(html_c) in seen:
            details.append(f"dup_content:{method}:{label}")
            continue
        seen.add(h(html_c))
        a2, p2, _, e2 = feed(agent, html_c, f"{url}#js{clicks + 1}")
        step_calls += 1
        clicks += 1
        details.append(f"{method}_clicked:{label}:chars={len(html_c)}:patch={p2}:err={e2 or '-'}")
        if e2:
            break
    return finish(key, t, agent, per_url=[{
        "url": url, "ok": True,
        "reason": f"render_ok_html_chars={len(html0)}|patch_new={p0}|pruned={pr0}|js_clicks={clicks}",
        "rendered_chars": len(html0), "rendered_density": academic_density(html0),
        "clicks": clicks, "click_detail": details, "added": len(agent.state.faculties),
        "pruned": pr0}], step_calls=step_calls)


HOP_HINT = re.compile(r"profil|person|staff|people|member|lecturer|teacher|faculty|advisor|researcher", re.I)


def collect_hops(driver, base_url):
    from selenium.webdriver.common.by import By
    try:
        anchors = driver.find_elements(By.XPATH, "//a[@href]")
    except Exception:
        return []
    out, seen = [], set()
    for a in anchors:
        try:
            href = (a.get_attribute("href") or "").strip()
            text = (a.text or "").strip()
            if not href or href.startswith(("javascript:", "mailto:", "#")):
                continue
            absu = urljoin(base_url, href).split("#")[0]
            if not is_official(absu):
                continue
            if absu.rstrip("/") == base_url.rstrip("/"):
                continue
            if absu in seen:
                continue
            if HOP_HINT.search(absu) or HOP_HINT.search(text) or len(text.split()) >= 2:
                # prefer deeper paths (likely individual pages)
                seen.add(absu)
                out.append((absu, text[:40]))
        except Exception:
            continue
    # deepest paths first (individual profiles), index/section pages last
    out.sort(key=lambda x: (-x[0].count("/"), x[0]))
    return out[:MAX_HOPS]


def run_kku(key, t, driver) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"], target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"], target_faculty_en=t["faculty_en"],
        session_id=key, max_steps=MAX_STEPS, checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False)
    base = t["seeds"][0]
    driver.get(base)
    time.sleep(3.0)
    html0 = driver.page_source or ""
    a0, p0, pr0, e0 = feed(agent, html0, base)
    step_calls = 1
    hops = collect_hops(driver, base)
    details = [f"base_chars={len(html0)} dens={academic_density(html0)} "
               f"patch={p0} err={e0 or '-'} hops_found={len(hops)}"]
    ok_hops = 0
    for absu, txt in hops:
        if step_calls >= MAX_STEPS:
            details.append("budget_stop")
            break
        try:
            driver.get(absu)
            time.sleep(2.5)
            html_c = driver.page_source or ""
        except Exception as e:  # noqa: BLE001
            details.append(f"hop_get_failed:{absu}:{type(e).__name__}")
            continue
        if len(html_c) < 1500 and academic_density(html_c) < 3:
            details.append(f"hop_thin:{absu}:chars={len(html_c)}")
            continue
        a2, p2, _, e2 = feed(agent, html_c, absu)
        step_calls += 1
        ok_hops += 1
        details.append(f"hop:{absu}:chars={len(html_c)}:dens={academic_density(html_c)}:patch={p2}:err={e2 or '-'}:linktext={txt!r}")
    return finish(key, t, agent, per_url=[{
        "url": base, "ok": True,
        "reason": f"render_ok_html_chars={len(html0)}|patch_new={p0}|pruned={pr0}|hops={ok_hops}/{len(hops)}",
        "rendered_chars": len(html0), "rendered_density": academic_density(html0),
        "clicks": ok_hops, "click_detail": details, "added": len(agent.state.faculties),
        "pruned": pr0}], step_calls=step_calls)


def finish(key, t, agent, per_url, step_calls) -> dict:
    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    n = len(agent.state.faculties)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    lines = []
    for p in per_url:
        if p.get("ok"):
            lines.append(f"{p['url']} clicks={p.get('clicks', 0)} "
                         f"[{'; '.join(p.get('click_detail', [])[:4])}]")
        else:
            lines.append(f"{p['url']} FAILED {p.get('reason', '')}")
    header = (f'"""Wave36 retry2 selenium checkpoint-only export ({key}).\n'
              f"Univ={t['univ_th']} Faculty={t['faculty_th']}.\n"
              f"Method: headless selenium webdriver direct; SU=JS "
              f"arguments[0].click()+ENTER fallback on nav+elementor "
              f"widgets; KKU=2nd-hop profile links (cap {MAX_HOPS}); every "
              f"page_source fed to FacultyExtractionAgent.step_with_html "
              f"(step_calls={step_calls}).\n"
              f"Verified count in body: {n}. Official *.ac.th only, NO DB commit.\n"
              f"Interaction: {' | '.join(lines[:8])}\n\"\"\"\n")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(agent.export_as_dataset_python())
    total_clicks = sum(p.get("clicks", 0) for p in per_url)
    oks = [u for u in per_url if u.get("ok")]
    status = "verified" if oks else "blocked"
    print(f"DONE {key}: {n} verified, {total_clicks} interactions -> "
          f"{os.path.basename(export_path)} [{status}]", flush=True)
    return {"key": key, "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
            "verified_count": n, "export_path": export_path, "checkpoint": ckpt,
            "status": status, "per_url": per_url,
            "failed_urls": list(agent.state.failed_urls),
            "total_clicks": total_clicks, "step_calls": step_calls}


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    driver = make_driver()
    results = []
    try:
        print("\n=== wave36_su_ict :: SU JS-click retry ===", flush=True)
        try:
            results.append(run_su("wave36_su_ict", TARGETS["wave36_su_ict"], driver))
        except Exception as e:  # noqa: BLE001
            print(f"UNIT wave36_su_ict fatal: {e}", flush=True)
            results.append({"key": "wave36_su_ict", "verified_count": 0,
                            "export_path": "", "total_clicks": 0,
                            "status": f"fatal:{type(e).__name__}"})
        print("\n=== wave36_kku_huso :: KKU 2nd-hop ===", flush=True)
        try:
            results.append(run_kku("wave36_kku_huso", TARGETS["wave36_kku_huso"], driver))
        except Exception as e:  # noqa: BLE001
            print(f"UNIT wave36_kku_huso fatal: {e}", flush=True)
            results.append({"key": "wave36_kku_huso", "verified_count": 0,
                            "export_path": "", "total_clicks": 0,
                            "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    import json as _json
    summary_path = os.path.join(AGENT_STATES_DIR, "wave36_selenium_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        _json.dump({"batch": "wave36_selenium_interaction_retry2", "db_commit": False,
                    "univ_scope": "su.ac.th + kku.ac.th only",
                    "units": results}, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}", flush=True)


if __name__ == "__main__":
    main()
