"""Wave27 Batch C (headless, checkpoint-only, NO DB commit).

Targets:
 1. PSU Dent (n=1): direct dept-subpage guesses under www.dent.psu.ac.th
    (/endo/ /ortho/ /prostho/ /pedo/ /surgery/ /radio/ /perio/ /operative/)
    + sitemap.xml re-check, urllib static first + browser fallback.
    Feed rendered rosters to SKILL.state agent. Image-only -> 0, no OCR.
 2. NU Sci (n=7): enumerate ?page=department&id=1..20 via BrowserScraper,
    plus faculty/faculty2 + math/chem/physics subsites. Banned: ldsc/nurse.
 3. UBU Sci (n=6): micro/it.sci.ubu.ac.th depts + www.ubu.ac.th portal roster
    links (static first, browser if 0).
 4. MFU Law (n=2): law.mfu.ac.th EN faculty pages top-up (/en/ staff).

Invariants: official *.ac.th only; 2-token Thai person-name rule in Python;
no invented names (agent-extracted only); NO DB commit.

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave27_batchC_headless.py
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
from scripts.agentic_pipeline.state_reducer import (  # noqa: E402
    save_state_checkpoint,
    normalize_thai_title_and_name,
)

AGENT_STATES_DIR = os.path.join(ROOT, "backend", "data", "agent_states")

PSU_TH = "มหาวิทยาลัยสงขลานครินทร์"
PSU_EN = "Prince of Songkla University"
PSU_FAC_TH = "คณะทันตแพทยศาสตร์"
PSU_FAC_EN = "Faculty of Dentistry"

NU_TH = "มหาวิทยาลัยนเรศวร"
NU_EN = "Naresuan University"
NU_FAC_TH = "คณะวิทยาศาสตร์"
NU_FAC_EN = "Faculty of Science"

UBU_TH = "มหาวิทยาลัยอุบลราชธานี"
UBU_EN = "Ubon Ratchathani University"
UBU_FAC_TH = "คณะวิทยาศาสตร์"
UBU_FAC_EN = "Faculty of Science"

MFU_TH = "มหาวิทยาลัยแม่ฟ้าหลวง"
MFU_EN = "Mae Fah Luang University"
MFU_FAC_TH = "สำนักวิชานิติศาสตร์"
MFU_FAC_EN = "School of Law"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer",
                    "Asst", "ทพ.", "ภาควิชา", "สาขาวิชา"]
BLOCK_MARKERS = ["403 Forbidden", "Access Denied", "Just a moment",
                 "Attention Required", "cf-challenge", "cf-error",
                 "Error code 1020"]
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
STAFF_KW = re.compile(r"(personnel|staff|faculty|researcher|people|department|"
                      r"about|personal|teacher|lecturer)", re.IGNORECASE)
BANNED_NU = re.compile(r"(ldsc|nurse|พยาบาล)", re.IGNORECASE)


def is_official_ac_th(url: str) -> bool:
    try:
        h = urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return False
    return h.endswith(".ac.th")


def academic_density(text: str) -> int:
    return sum((text or "").count(m) for m in ACADEMIC_MARKERS)


def looks_blocked(html) -> tuple:
    if not html:
        return True, "empty_or_exception"
    low = html.lower()
    for m in BLOCK_MARKERS:
        if m.lower() in low and academic_density(html) < 5:
            return True, f"block_marker:{m}"
    if len(html) < 1500 and academic_density(html) < 3:
        return True, "thin_or_block_page"
    return False, ""


def fetch_static(url: str, timeout: int = 20) -> tuple:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX,
                                    timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), resp.getcode()
    except Exception as e:  # noqa: BLE001
        return "", f"static_fail:{type(e).__name__}"


def render_url(url: str, scraper, max_scrolls=2):
    html = None
    reason = ""
    for _ in range(2):
        try:
            html = scraper.scroll_and_render_all(
                url, scroll_pause=1.0, max_scrolls=max_scrolls, extra_wait=1.5)
        except Exception as e:  # noqa: BLE001
            reason = f"browser_exception:{type(e).__name__}"
            html = None
        blocked, b_reason = looks_blocked(html)
        if blocked:
            reason = b_reason
            time.sleep(1.5)
            continue
        reason = f"render_ok_chars={len(html or '')}"
        return html, False, reason
    return html, True, reason


def feed(agent, html: str, url: str) -> tuple:
    before = len(agent.state.faculties)
    try:
        patch = agent.step_with_html(html, current_url=url)
        return len(agent.state.faculties) - before, len(patch.new_profiles), ""
    except Exception as e:  # noqa: BLE001
        agent.state.failed_urls.append(url)
        return 0, 0, f"extraction_failed:{type(e).__name__}"


def apply_two_token_rule(agent) -> int:
    """Drop single-token person names in Python. Returns discarded count."""
    dropped = 0
    for fid in list(agent.state.faculties.keys()):
        f = agent.state.faculties[fid]
        try:
            _, _, base = normalize_thai_title_and_name(
                f.get("full_name_th") or "", f.get("academic_title_th"))
        except Exception:
            base = (f.get("full_name_th") or "").strip()
        toks = [t for t in base.split() if t.strip(" .")]
        if len(toks) < 2:
            del agent.state.faculties[fid]
            dropped += 1
    return dropped


def drop_banned_nu(agent) -> int:
    dropped = 0
    for fid in list(agent.state.faculties.keys()):
        f = agent.state.faculties[fid]
        blob = " ".join([f.get("department_th") or "", f.get("department") or "",
                         f.get("profile_url") or "", f.get("faculty_th") or ""])
        if BANNED_NU.search(blob):
            del agent.state.faculties[fid]
            dropped += 1
    return dropped


def collect_staff_links(html, base_url, cap=10):
    try:
        seed_host = urlparse(base_url).netloc.lower()
    except Exception:
        return []
    found, seen = [], set()
    for m in HREF_RE.finditer(html or ""):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, raw).split("#")[0].strip()
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https") or not is_official_ac_th(abs_url):
            continue
        if (p.netloc.lower() != seed_host
                and not p.netloc.lower().endswith(".ac.th")):
            continue
        if not STAFF_KW.search((p.path or "") + "?" + (p.query or "")):
            continue
        if abs_url not in seen:
            seen.add(abs_url)
            found.append(abs_url)
    prio = re.compile(r"(personnel|staff|researcher|faculty|people)",
                      re.IGNORECASE)
    found.sort(key=lambda u: (0 if prio.search(urlparse(u).path or "")
                              else 1, len(u)))
    return found[:cap]


def sitemap_locs(base: str) -> list:
    locs = []
    for name in ("sitemap.xml", "wp-sitemap.xml", "sitemap_index.xml"):
        html, _ = fetch_static(urljoin(base, "/" + name), timeout=15)
        if not html or "<loc>" not in html:
            continue
        for m in re.finditer(r"<loc>([^<]+)</loc>", html):
            u = m.group(1).strip()
            if is_official_ac_th(u) and STAFF_KW.search(u):
                locs.append(u)
    return locs[:8]


def new_agent(key, univ_th, univ_en, fac_th, fac_en, max_steps=30):
    return FacultyExtractionAgent(
        target_university_th=univ_th, target_university_en=univ_en,
        target_faculty_th=fac_th, target_faculty_en=fac_en,
        session_id=key, max_steps=max_steps,
        checkpoint_dir=AGENT_STATES_DIR, auto_lookup_wiki=False)


def finalize(key, agent, header_note, per_url, extra: dict) -> dict:
    dropped = apply_two_token_rule(agent)
    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(header_note + "\n" + agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    print(f"DONE {key}: {n} verified (dropped_single_token={dropped}) -> "
          f"{os.path.basename(export_path)}", flush=True)
    out = {"key": key, "verified_count": n,
           "single_token_dropped": dropped, "export_path": export_path,
           "checkpoint": ckpt, "per_url": per_url,
           "failed_urls": list(agent.state.failed_urls)}
    out.update(extra)
    return out


# ------------------------------- target units -------------------------------

def run_psu_dent(scraper):
    key = "wave27_psu_dent"
    agent = new_agent(key, PSU_TH, PSU_EN, PSU_FAC_TH, PSU_FAC_EN)
    base = "https://www.dent.psu.ac.th"
    guesses = [base + "/"] + [f"{base}/{d}/" for d in
                              ("endo", "ortho", "prostho", "pedo", "surgery",
                               "radio", "perio", "operative")]
    sm = []
    try:
        sm = sitemap_locs(base)
    except Exception:
        sm = []
    per_url, dept_found, static_hits = [], [], []
    for url in guesses:
        if not is_official_ac_th(url):
            continue
        html, st = fetch_static(url)
        dens = academic_density(html)
        if html and dens >= 3 and len(html) > 2000:
            static_hits.append(url)
        per_url.append({"url": url, "role": "guess",
                        "static_len": len(html or ""), "static_dens": dens,
                        "static_status": st if isinstance(st, str) else "ok"})
        time.sleep(0.4)
    cands = static_hits + [u for u in sm if u not in static_hits]
    if not cands:  # browser fallback on base + first 5 dept guesses
        cands = guesses[:6]
    cands = cands[:8]
    for url in cands:
        html, blocked, reason = render_url(url, scraper)
        if blocked:
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "role": "render", "ok": False,
                            "reason": reason})
            print(f"  psu render-blocked {url} -> {reason}", flush=True)
            continue
        dept_found.append(url)
        added, _, err = feed(agent, html, url)
        per_url.append({"url": url, "role": "render", "ok": True,
                        "reason": reason, "added": added, "err": err})
        print(f"  psu render OK {url} +{added}", flush=True)
        time.sleep(0.8)
    header = (f'"""Wave27 Batch C checkpoint-only export (psu_dent). '
              f"Guesses={len(guesses)} static_hits={len(static_hits)} "
              f"sitemap_locs={len(sm)} rendered_ok={dept_found}. "
              f"Image-only -> 0, no OCR, NO DB commit.\"\"\"")
    return finalize(key, agent, header, per_url,
                    {"dept_urls_found": dept_found,
                     "guesses": guesses, "sitemap_locs": sm})


def run_nu_sci(scraper):
    key = "wave27_nu_sci"
    agent = new_agent(key, NU_TH, NU_EN, NU_FAC_TH, NU_FAC_EN, max_steps=40)
    seeds = ["https://www.sci.nu.ac.th/",
             "https://www.sci.nu.ac.th/faculty/",
             "https://www.sci.nu.ac.th/faculty2/",
             "https://math.sci.nu.ac.th/",
             "https://chemistry.sci.nu.ac.th/",
             "https://physics.sci.nu.ac.th/"]
    seeds = [u for u in seeds if is_official_ac_th(u)]
    dept_urls = [f"https://www.sci.nu.ac.th/?page=department&id={i}"
                 for i in range(1, 21)]
    per_url, dept_found, skipped = [], [], []
    for url in seeds + dept_urls:
        if BANNED_NU.search(url):
            skipped.append(url)
            continue
        html, blocked, reason = render_url(url, scraper)
        if blocked:
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False, "reason": reason})
            continue
        if BANNED_NU.search(html[:2000]):
            skipped.append(url)
            per_url.append({"url": url, "ok": False,
                            "reason": "skipped_banned_ldsc_nurse"})
            continue
        dept_found.append(url)
        added, _, err = feed(agent, html, url)
        per_url.append({"url": url, "ok": True, "reason": reason,
                        "added": added, "err": err})
        print(f"  nu render {url} +{added}", flush=True)
        time.sleep(0.6)
    banned_dropped = drop_banned_nu(agent)
    header = (f'"""Wave27 Batch C checkpoint-only export (nu_sci). '
              f"dept_ids=1..20 rendered_ok={len(dept_found)} "
              f"banned_skipped={len(skipped)} banned_dropped={banned_dropped}. "
              f"Official *.ac.th only, NO DB commit.\"\"\"")
    return finalize(key, agent, header, per_url,
                    {"dept_urls_found": dept_found, "banned_skipped": skipped,
                     "banned_dropped": banned_dropped})


def run_static_then_browser(key, univ_th, univ_en, fac_th, fac_en, seeds,
                            scraper, cap_links=10, cap_render=8):
    agent = new_agent(key, univ_th, univ_en, fac_th, fac_en)
    per_url, links_found, rendered = [], [], []
    # CLI static first
    for url in seeds:
        html, st = fetch_static(url)
        blocked, reason = looks_blocked(html)
        if blocked:
            per_url.append({"url": url, "role": "static", "ok": False,
                            "reason": f"{st}:{reason}"})
            continue
        added, _, err = feed(agent, html, url)
        per_url.append({"url": url, "role": "static", "ok": True,
                        "reason": f"static_len={len(html)}", "added": added,
                        "err": err})
        for lk in collect_staff_links(html, url, cap=cap_links):
            if lk not in links_found:
                links_found.append(lk)
        time.sleep(0.4)
    static_verified = len(agent.state.faculties)
    # browser fallback if 0
    if static_verified == 0:
        todo = (seeds + links_found)[:cap_render]
        for url in todo:
            html, blocked, reason = render_url(url, scraper)
            if blocked:
                agent.state.failed_urls.append(url)
                per_url.append({"url": url, "role": "render", "ok": False,
                                "reason": reason})
                continue
            rendered.append(url)
            added, _, err = feed(agent, html, url)
            per_url.append({"url": url, "role": "render", "ok": True,
                            "reason": reason, "added": added, "err": err})
            for lk in collect_staff_links(html, url, cap=cap_links):
                if lk not in links_found and len(links_found) < cap_links:
                    links_found.append(lk)
            print(f"  {key} render {url} +{added}", flush=True)
            time.sleep(0.6)
    return agent, per_url, links_found, rendered, static_verified


def run_ubu_sci(scraper):
    key = "wave27_ubu_sci"
    seeds = ["https://micro.sci.ubu.ac.th/", "https://it.sci.ubu.ac.th/",
             "https://www.sci.ubu.ac.th/", "https://www.ubu.ac.th/",
             "https://www.ubu.ac.th/personnel/", "https://sci.ubu.ac.th/"]
    seeds = [u for u in seeds if is_official_ac_th(u)]
    agent, per_url, links, rendered, static_n = run_static_then_browser(
        key, UBU_TH, UBU_EN, UBU_FAC_TH, UBU_FAC_EN, seeds, scraper)
    header = (f'"""Wave27 Batch C checkpoint-only export (ubu_sci). '
              f"static_verified={static_n} roster_links={len(links)} "
              f"browser_rendered={len(rendered)}. Official *.ac.th only, "
              f"NO DB commit.\"\"\"")
    return finalize(key, agent, header, per_url,
                    {"dept_urls_found": rendered, "roster_links": links,
                     "static_verified": static_n})


def run_mfu_law(scraper):
    key = "wave27_mfu_law"
    seeds = ["https://law.mfu.ac.th/", "https://law.mfu.ac.th/en/",
             "https://law.mfu.ac.th/en/faculty-member/",
             "https://law.mfu.ac.th/en/staff/",
             "https://law.mfu.ac.th/staff/"]
    seeds = [u for u in seeds if is_official_ac_th(u)]
    agent, per_url, links, rendered, static_n = run_static_then_browser(
        key, MFU_TH, MFU_EN, MFU_FAC_TH, MFU_FAC_EN, seeds, scraper)
    header = (f'"""Wave27 Batch C checkpoint-only export (mfu_law). '
              f"static_verified={static_n} en_links={len(links)} "
              f"browser_rendered={len(rendered)}. Official *.ac.th only, "
              f"NO DB commit.\"\"\"")
    return finalize(key, agent, header, per_url,
                    {"dept_urls_found": rendered, "roster_links": links,
                     "static_verified": static_n})


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    scraper = BrowserScraper(headless=True, page_load_timeout=30)
    results = {}
    try:
        print("=== wave27_psu_dent ===", flush=True)
        results["psu_dent"] = run_psu_dent(scraper)
        print("=== wave27_nu_sci ===", flush=True)
        results["nu_sci"] = run_nu_sci(scraper)
        print("=== wave27_ubu_sci ===", flush=True)
        results["ubu_sci"] = run_ubu_sci(scraper)
        print("=== wave27_mfu_law ===", flush=True)
        results["mfu_law"] = run_mfu_law(scraper)
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave27_batchC_summary.json")
    compact = {}
    for k, r in results.items():
        compact[k] = {
            "verified": r.get("verified_count", 0),
            "export": r.get("export_path", ""),
            "dept_urls_found": r.get("dept_urls_found", []),
            "roster_links": r.get("roster_links", r.get("sitemap_locs", [])),
            "failed_urls": r.get("failed_urls", [])[:12],
            "single_token_dropped": r.get("single_token_dropped", 0),
            "note": f"per_url_n={len(r.get('per_url', []))}",
        }
    compact["_meta"] = {"batch": "wave27_batchC", "mode": "checkpoint-only, "
                        "NO DB commit", "official_ac_th_only": True}
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(compact, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results.values())
    print(f"BATCH DONE: {total} verified across {len(results)} units -> "
          f"{summary_path}", flush=True)


if __name__ == "__main__":
    main()
