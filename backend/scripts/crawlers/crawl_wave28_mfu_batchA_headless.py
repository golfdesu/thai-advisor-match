"""Wave28 MFU Batch A (headless, SKILL.state compliant).

Scope: Mae Fah Luang University ONLY (mfu.ac.th hosts only).
Checkpoint-only, NO DB commit, NO invented names (only FacultyExtractionAgent
extractions), NO in-chat HTML. Python-only run.

Method per school: sitemap.xml probe -> staff-path probe -> BrowserScraper
render (MFU www is JS shell; static alone gives ~0) -> step_with_html ->
checkpoint -> export backend/data/agent_states/wave28_mfu_<key>_export.py.

2-token Thai rule enforced in Python (post-extraction prune).

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave28_mfu_batchA_headless.py
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

MFU_TH = "มหาวิทยาลัยแม่ฟ้าหลวง"
MFU_EN = "Mae Fah Luang University"

# mfu.ac.th hosts ONLY.
TARGETS = {
    "wave28_mfu_liberalarts": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาศิลปศาสตร์",
        "faculty_en": "School of Liberal Arts",
        "sitemaps": [
            "https://www.mfu.ac.th/sitemap.xml",
            "https://liberal-arts.mfu.ac.th/sitemap.xml",
            "https://sla.mfu.ac.th/sitemap.xml",
        ],
        "seeds": [
            "https://www.mfu.ac.th/en/academics.html",
            "https://www.mfu.ac.th/en/academics/school-of-liberal-arts.html",
            "https://www.mfu.ac.th/th/academics/school-of-liberal-arts.html",
            "https://liberal-arts.mfu.ac.th/",
            "https://liberal-arts.mfu.ac.th/en/",
            "https://sla.mfu.ac.th/",
        ],
    },
    "wave28_mfu_sinology": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาจีนวิทยา",
        "faculty_en": "School of Sinology",
        "sitemaps": [
            "https://www.mfu.ac.th/sitemap.xml",
            "https://sinology.mfu.ac.th/sitemap.xml",
            "https://chinese.mfu.ac.th/sitemap.xml",
        ],
        "seeds": [
            "https://www.mfu.ac.th/en/academics.html",
            "https://www.mfu.ac.th/en/academics/school-of-sinology.html",
            "https://sinology.mfu.ac.th/",
            "https://sinology.mfu.ac.th/en/",
            "https://chinese.mfu.ac.th/",
        ],
    },
    "wave28_mfu_law": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชานิติศาสตร์",
        "faculty_en": "School of Law",
        "sitemaps": [
            "https://law.mfu.ac.th/sitemap.xml",
            "https://www.mfu.ac.th/sitemap.xml",
        ],
        "seeds": [
            "https://law.mfu.ac.th/",
            "https://law.mfu.ac.th/en/law-staff/law-lecturers.html",
            "https://law.mfu.ac.th/en/law-staff/law-executives.html",
            "https://law.mfu.ac.th/en/",
        ],
    },
    "wave28_mfu_management": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาการจัดการ",
        "faculty_en": "School of Management",
        "sitemaps": [
            "https://mbs.mfu.ac.th/sitemap.xml",
            "https://management.mfu.ac.th/sitemap.xml",
            "https://www.mfu.ac.th/sitemap.xml",
        ],
        "seeds": [
            "https://mbs.mfu.ac.th/",
            "https://mbs.mfu.ac.th/en/",
            "https://management.mfu.ac.th/",
            "https://www.mfu.ac.th/en/academics/school-of-management.html",
            "https://www.mfu.ac.th/en/academics.html",
        ],
    },
    "wave28_mfu_antiaging": {
        "univ_th": MFU_TH, "univ_en": MFU_EN,
        "faculty_th": "สำนักวิชาการแพทย์ชะลอวัย",
        "faculty_en": "School of Anti-Aging Medicine",
        "sitemaps": [
            "https://www.mfu.ac.th/sitemap.xml",
            "https://longevity.mfu.ac.th/sitemap.xml",
            "https://anti-aging.mfu.ac.th/sitemap.xml",
        ],
        "seeds": [
            "https://www.mfu.ac.th/en/academics.html",
            "https://www.mfu.ac.th/en/academics/school-of-anti-aging-medicine.html",
            "https://longevity.mfu.ac.th/",
            "https://anti-aging.mfu.ac.th/",
        ],
    },
}

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020",
    "ERR_CONNECTION", "getaddrinfo failed",
]
STAFF_HINTS = ("staff", "faculty", "personnel", "lecturer", "teacher",
               "executive", "about", "school", "academics", "people", "member")

# Boilerplate / breadcrumb fragments that are NEVER person names (Invariant 9).
BOILERPLATE = (
    "สถานที่ติดต่อ", "ติดต่อ", "สำนักวิชา", "สาขาวิชา", "ภาควิชา",
    "มหาวิทยาลัย", "คณะ", "หลักสูตร", "สำนักงาน", "ฝ่าย",
    "computer", "science group", "research group", "breadcrumb",
    "menu", "home", "download", "sidebar", "office",
)

# Title prefixes stripped with explicit period/whitespace delimiter
# (Invariant 1: never r"ดร\.?" — Thai has no word boundaries).
_TITLE_STRIP = re.compile(
    r"^(?:ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์\s*ดร\.|อาจารย์|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|"
    r"Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lecturer|Professor)\s*",
    re.IGNORECASE,
)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def is_mfu_host(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower().endswith("mfu.ac.th")
    except Exception:
        return False


def fetch_static(url: str, timeout: int = 20) -> tuple[str, int]:
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


def fetch_sitemap_locs(sitemap_url: str) -> tuple[list, str]:
    xml_text, status = fetch_static(sitemap_url)
    if not xml_text or "<loc>" not in xml_text:
        return [], f"http_{status}_no_locs" if status else "fetch_failed_or_empty"
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml_text)
    kept = [u.strip() for u in locs
            if is_mfu_host(u.strip())
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


def valid_person_name(full_name_th: str | None) -> bool:
    """2-token Thai rule in Python: strip titles (explicit delimiter), require
    >=2 tokens, reject breadcrumbs/boilerplate. No invented names."""
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
        max_steps=14,
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

    queue = list(dict.fromkeys(list(t["seeds"]) + discovered))
    per_url = []
    for url in queue:
        if not is_mfu_host(url):
            per_url.append({"url": url, "ok": False, "reason": "non_mfu_host_skipped"})
            continue
        static_html, status = fetch_static(url)
        s_chars, s_dens = len(static_html), academic_density(static_html)
        html = None
        # MFU www is JS shell: always browser-render (max 2 attempts).
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
            # Prefer rendered when denser; fall back to static if render thin.
            if s_dens > outcome["rendered_density"] and s_dens >= 5:
                html = static_html
                outcome["reason"] = (outcome.get("reason") or "") + "|used_static_denser"
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
    summary_path = os.path.join(AGENT_STATES_DIR, "wave28_mfu_batchA_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave28_mfu_batchA_headless", "db_commit": False,
                   "univ_scope": "mfu.ac.th only", "units": results},
                  f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}",
          flush=True)


if __name__ == "__main__":
    main()
