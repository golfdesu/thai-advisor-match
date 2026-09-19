"""Wave31 KMUTNB automotive/energy staff (headless, SKILL.state compliant).

Scope: kmutnb.ac.th hosts ONLY (cit.kmutnb.ac.th + dept /about/ pages).
Checkpoint-only, NO DB commit, NO invented names (only FacultyExtractionAgent
extractions), NO in-chat HTML. Python-only run.

Method: static probe -> BrowserScraper render each seed (thin-JS pages need
render) -> FacultyExtractionAgent.step_with_html per page -> 2-token Thai
prune in Python -> checkpoint -> export
backend/data/agent_states/wave31_kmutnb_auto_export.py.

Covers wave30 gap: wave30 got 17 (INET/welding/mech); this wave targets
automotive/energy lists via cit `/`, `/en/`, `/en/department/` plus
MM/electrical/powereng/civil/ascs/automotive/energy `/about/` pages.

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave31_kmutnb_auto_headless.py
"""
import os
import re
import sys
import json
import time
import ssl
import urllib.request

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

KEY = "wave31_kmutnb_auto"
TARGET = {
    "univ_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "univ_en": "King Mongkut's University of Technology North Bangkok",
    "faculty_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม",
    "faculty_en": "College of Industrial Technology",
    "sitemaps": [
        "https://cit.kmutnb.ac.th/sitemap.xml",
    ],
    "seeds": [
        "https://cit.kmutnb.ac.th/",
        "https://cit.kmutnb.ac.th/en/",
        "https://cit.kmutnb.ac.th/en/department/",
        "https://cit.kmutnb.ac.th/mm/about/",
        "https://cit.kmutnb.ac.th/electrical/about/",
        "https://cit.kmutnb.ac.th/powereng/about/",
        "https://cit.kmutnb.ac.th/civil/about/",
        "https://cit.kmutnb.ac.th/ascs/about/",
        "https://cit.kmutnb.ac.th/automotive/about/",
        "https://cit.kmutnb.ac.th/energy/about/",
    ],
}

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020",
    "ERR_CONNECTION", "getaddrinfo failed",
]
STAFF_HINTS = ("staff", "faculty", "personnel", "lecturer", "teacher",
               "executive", "about", "school", "academics", "people", "member",
               "department", "program", "branch", "division")

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

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def is_scope_host(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower().endswith("kmutnb.ac.th")
    except Exception:
        return False


def fetch_static(url: str, timeout: int = 20):
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


def fetch_sitemap_locs(sitemap_url: str):
    xml_text, status = fetch_static(sitemap_url)
    if not xml_text or "<loc>" not in xml_text:
        return [], f"http_{status}_no_locs" if status else "fetch_failed_or_empty"
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml_text)
    kept = [u.strip() for u in locs
            if is_scope_host(u.strip())
            and any(h in u.lower() for h in STAFF_HINTS)][:6]
    return kept, f"http_{status}_locs={len(locs)}_kept={len(kept)}"


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


def run_unit(key: str, t: dict, scraper: BrowserScraper) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=15,
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,
    )
    sitemap_findings = []
    discovered = []
    for sm in t["sitemaps"]:
        locs, note = fetch_sitemap_locs(sm)
        sitemap_findings.append({"sitemap": sm, "note": note, "kept": locs})
        for u in locs:
            if u not in discovered:
                discovered.append(u)
        time.sleep(0.5)

    queue = list(dict.fromkeys(list(t["seeds"]) + discovered))[:15]
    per_url = []
    for url in queue:
        if not is_scope_host(url):
            per_url.append({"url": url, "ok": False, "reason": "non_scope_host_skipped"})
            continue
        static_html, status = fetch_static(url)
        s_chars, s_dens = len(static_html), academic_density(static_html)
        html = None
        outcome = {"url": url, "attempts": 0, "ok": False, "reason": "",
                   "static_chars": s_chars, "static_density": s_dens,
                   "static_http": status, "rendered_chars": 0,
                   "rendered_density": 0, "added": 0, "pruned": 0}
        for attempt in range(2):
            outcome["attempts"] = attempt + 1
            try:
                html = scraper.scroll_and_render_all(
                    url, scroll_pause=1.2, max_scrolls=3, extra_wait=2.0)
            except Exception as e:  # noqa: BLE001
                outcome["reason"] = f"browser_exception:{type(e).__name__}"
                html = None
            blocked, reason = looks_blocked(html)
            if blocked:
                outcome["reason"] = reason
                time.sleep(2.0)
                continue
            break
        if html:
            outcome["rendered_chars"] = len(html)
            outcome["rendered_density"] = academic_density(html)
            if s_dens > outcome["rendered_density"] and s_dens >= 5:
                html = static_html
                outcome["reason"] = (outcome.get("reason") or "") + "|used_static_denser"
        # Follow same-site discovered staff links (one hop, capped)
        extra_links = []
        blocked, reason = looks_blocked(html)
        if blocked:
            agent.state.failed_urls.append(url)
            outcome["reason"] = outcome.get("reason") or reason
            per_url.append(outcome)
            print(f"  STOP {url} -> {outcome['reason']} "
                  f"(static={s_chars}c/d{s_dens} render={outcome['rendered_chars']}c/"
                  f"d{outcome['rendered_density']})", flush=True)
            continue
        try:
            before = len(agent.state.faculties)
            patch = agent.step_with_html(html, current_url=url)
            pruned = prune_invalid(agent)
            added = len(agent.state.faculties) - before
            outcome.update(ok=True, added=added, pruned=pruned,
                           reason=f"render_ok_html_chars={len(html or '')}|"
                                  f"patch_new={len(patch.new_profiles)}|pruned={pruned}")
            print(f"  OK {url} +{len(patch.new_profiles)} patch / +{added} net "
                  f"(pruned {pruned}) | unit total {len(agent.state.faculties)}",
                  flush=True)
            try:
                for u in (patch.discovered_urls or []):
                    if (is_scope_host(u) and u not in queue and u not in extra_links
                            and any(h in u.lower() for h in STAFF_HINTS)
                            and len(queue) + len(extra_links) < 15):
                        extra_links.append(u)
            except Exception:
                pass
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            outcome["reason"] = f"extraction_failed:{type(e).__name__}"
            print(f"  FAIL {url} extraction failed: {str(e)[:120]}", flush=True)
        per_url.append(outcome)
        time.sleep(1.0)
        # drain one-hop discovered links inline (same agent, still checkpoint-only)
        for u in extra_links:
            if not is_scope_host(u):
                continue
            s_html, s_status = fetch_static(u)
            s_c, s_d = len(s_html), academic_density(s_html)
            sub = {"url": u, "attempts": 1, "ok": False, "reason": "",
                   "static_chars": s_c, "static_density": s_d,
                   "static_http": s_status, "rendered_chars": 0,
                   "rendered_density": 0, "added": 0, "pruned": 0}
            try:
                r_html = scraper.scroll_and_render_all(
                    u, scroll_pause=1.2, max_scrolls=3, extra_wait=2.0)
            except Exception as e:  # noqa: BLE001
                sub["reason"] = f"browser_exception:{type(e).__name__}"
                per_url.append(sub)
                continue
            if r_html:
                sub["rendered_chars"] = len(r_html)
                sub["rendered_density"] = academic_density(r_html)
                if s_d > sub["rendered_density"] and s_d >= 5:
                    r_html = s_html
            blocked, reason = looks_blocked(r_html)
            if blocked:
                agent.state.failed_urls.append(u)
                sub["reason"] = reason
                per_url.append(sub)
                continue
            try:
                before = len(agent.state.faculties)
                patch = agent.step_with_html(r_html, current_url=u)
                pruned = prune_invalid(agent)
                added = len(agent.state.faculties) - before
                sub.update(ok=True, added=added, pruned=pruned,
                           reason=f"render_ok_html_chars={len(r_html or '')}|"
                                  f"patch_new={len(patch.new_profiles)}|pruned={pruned}")
                print(f"  OK (hop) {u} +{len(patch.new_profiles)} patch / +{added} net",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                agent.state.failed_urls.append(u)
                sub["reason"] = f"extraction_failed:{type(e).__name__}"
            per_url.append(sub)
            time.sleep(1.0)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    oks = [u for u in per_url if u["ok"]]
    status = ("bypassed" if oks and all(u["ok"] for u in per_url)
              else ("partial" if oks else "blocked"))
    print(f"DONE {key}: {n} verified -> {os.path.basename(export_path)} [{status}]",
          flush=True)
    return {
        "key": key, "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
        "verified_count": n, "export_path": export_path, "checkpoint": ckpt,
        "status": status, "sitemap_findings": sitemap_findings,
        "per_url": per_url, "failed_urls": list(agent.state.failed_urls),
        "serp_needed": (n == 0),
    }


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    scraper = BrowserScraper(headless=True, page_load_timeout=30)
    try:
        print(f"\n=== {KEY} :: {TARGET['faculty_th']} ===", flush=True)
        result = run_unit(KEY, TARGET, scraper)
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave31_kmutnb_auto_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave31_kmutnb_auto_headless", "db_commit": False,
                   "univ_scope": "kmutnb.ac.th only", "units": [result]},
                  f, ensure_ascii=False, indent=2)
    print(f"\nBATCH DONE: {result.get('verified_count', 0)} verified -> {summary_path}",
          flush=True)


if __name__ == "__main__":
    main()
