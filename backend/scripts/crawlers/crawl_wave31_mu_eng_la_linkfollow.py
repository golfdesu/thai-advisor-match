"""Wave31 MU shortage x2 link-follow (headless, SKILL.state compliant).

Scope: mahidol.ac.th hosts ONLY. Checkpoint-only, NO DB commit,
NO invented names (only FacultyExtractionAgent extractions),
NO in-chat HTML. Python-only run.

Pattern (RILCA/mb/IPSR breakthrough): BrowserScraper-render landing +
/departments/ (eng) or /en/ (la) index, collect SAME-SITE links matching
staff-keywords (personnel/staff/faculty/researcher/people/about/department/
lab/center), render each (cap 12 deep), FacultyExtractionAgent.step_with_html
per page. Do NOT guess slugs -- only follow discovered links. LA fallback:
if landing yields no staff hrefs, 2nd-hop via discovered dept-like
intermediate links (thai/english/linguistics/history/program/division/branch)
found on landing, then staff-link follow from those.

cli_runner-equivalent: --univ-th "มหาวิทยาลัยมหิดล" --max-steps 15 --no-wiki.
Exports: backend/data/agent_states/wave31_mu_<key>_export.py
2-token Thai rule enforced in Python (post-extraction prune).

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave31_mu_eng_la_linkfollow.py
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
    "wave31_mu_eng": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "seeds": [
            "https://eg.mahidol.ac.th/",
            "https://eg.mahidol.ac.th/departments/",
        ],
    },
    "wave31_mu_la": {
        "univ_th": MU_TH, "univ_en": MU_EN,
        "faculty_th": "คณะศิลปศาสตร์",
        "faculty_en": "Faculty of Liberal Arts",
        "seeds": [
            "https://la.mahidol.ac.th/",
            "https://la.mahidol.ac.th/en/",
        ],
    },
}

STAFF_KW = re.compile(
    r"(personnel|staff|faculty|researcher|people|about|department|lab|center)",
    re.IGNORECASE,
)
DEPT_KW = re.compile(
    r"(thai|english|linguistic|history|department|program|division|branch|sาขา|ภาควิชา|center|lab)",
    re.IGNORECASE,
)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BLOCK_MARKERS = [
    "403 Forbidden", "Access Denied", "Just a moment", "Attention Required",
    "cf-challenge", "cf-error", "Error code 1020",
]
CAP_DEEP = 12
MAX_STEPS = 15  # cli_runner-equivalent --max-steps 15

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


def is_mu_host(url: str) -> bool:
    try:
        return urlparse(url).netloc.lower().endswith("mahidol.ac.th")
    except Exception:
        return False


def academic_density(text) -> int:
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
    """2-token Thai rule in Python: strip titles, require >=2 tokens."""
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


def render(url, scraper):
    html = None
    reason = ""
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
            time.sleep(1.5)
            continue
        reason = f"render_ok_html_chars={len(html or '')}"
        return html, False, reason
    return html, True, reason


def collect_links(html, base_url, pattern):
    found, seen = [], set()
    for m in HREF_RE.finditer(html or ""):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, raw).split("#")[0].strip()
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https"):
            continue
        if not is_mu_host(abs_url):
            continue
        if not pattern.search((p.path or "") + "?" + (p.query or "")):
            continue
        if abs_url not in seen:
            seen.add(abs_url)
            found.append(abs_url)
    prio = re.compile(r"(personnel|staff|researcher|faculty|people)", re.IGNORECASE)
    found.sort(key=lambda u: (0 if prio.search(urlparse(u).path or "") else 1, len(u)))
    return found


def run_unit(key: str, t: dict, scraper: BrowserScraper) -> dict:
    agent = FacultyExtractionAgent(
        target_university_th=t["univ_th"],  # --univ-th "มหาวิทยาลัยมหิดล"
        target_university_en=t["univ_en"],
        target_faculty_th=t["faculty_th"],
        target_faculty_en=t["faculty_en"],
        session_id=key,
        max_steps=MAX_STEPS,  # --max-steps 15
        checkpoint_dir=AGENT_STATES_DIR,
        auto_lookup_wiki=False,  # --no-wiki
    )
    per_url = []
    landing_htmls = {}
    staff_links_all: list = []
    # Level 0: render seeds (landing + index), extract each, collect staff links
    for seed in t["seeds"]:
        if agent.state.step_count >= MAX_STEPS:
            per_url.append({"url": seed, "ok": False, "reason": "max_steps_reached",
                            "added": 0, "role": "landing-skipped"})
            continue
        html, blocked, reason = render(seed, scraper)
        if blocked:
            agent.state.failed_urls.append(seed)
            per_url.append({"url": seed, "ok": False, "reason": reason,
                            "added": 0, "role": "landing"})
            print(f"  landing-blocked {seed} -> {reason}", flush=True)
            continue
        landing_htmls[seed] = html
        try:
            before = len(agent.state.faculties)
            patch = agent.step_with_html(html, current_url=seed)
            pruned = prune_invalid(agent)
            added = len(agent.state.faculties) - before
            per_url.append({"url": seed, "ok": True,
                            "reason": f"{reason}|patch_new={len(patch.new_profiles)}|pruned={pruned}",
                            "added": added, "role": "landing"})
            print(f"  landing OK {seed} +{added} net (patch {len(patch.new_profiles)}, pruned {pruned})",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(seed)
            per_url.append({"url": seed, "ok": False,
                            "reason": f"extraction_failed:{type(e).__name__}",
                            "added": 0, "role": "landing"})
            print(f"  landing-extract-fail {seed}: {str(e)[:120]}", flush=True)
        for u in collect_links(html, seed, STAFF_KW):
            if u not in staff_links_all:
                staff_links_all.append(u)
        time.sleep(0.8)

    dept_paths = [urlparse(u).path or "/" for u in staff_links_all]
    print(f"  staff_links[{len(staff_links_all)}]: {dept_paths[:12]}", flush=True)

    # LA fallback 2nd-hop: if few/no staff links, render discovered dept-like
    # intermediate links from landing, then harvest staff links from those.
    second_hop_staff: list = []
    intermediates: list = []
    if len(staff_links_all) < 3:
        for seed, html in landing_htmls.items():
            for u in collect_links(html, seed, DEPT_KW):
                if u not in staff_links_all and u not in intermediates and u != seed:
                    intermediates.append(u)
        intermediates = intermediates[:4]
        print(f"  fallback intermediates[{len(intermediates)}]: "
              f"{[urlparse(u).path for u in intermediates]}", flush=True)
        for inter in intermediates:
            if len(staff_links_all) + len(second_hop_staff) >= CAP_DEEP:
                break
            ihtml, blocked, reason = render(inter, scraper)
            if blocked:
                per_url.append({"url": inter, "ok": False, "reason": reason,
                                "added": 0, "role": "intermediate"})
                print(f"  inter-blocked {inter} -> {reason}", flush=True)
                continue
            for u in collect_links(ihtml, inter, STAFF_KW):
                if u not in staff_links_all and u not in second_hop_staff:
                    second_hop_staff.append(u)
            per_url.append({"url": inter, "ok": True, "reason": reason,
                            "added": 0, "role": "intermediate-harvest-only"})
            print(f"  inter-harvest {inter} -> +{len(second_hop_staff)} staff total",
                  flush=True)
            time.sleep(0.8)

    deep_queue = (staff_links_all + second_hop_staff)[:CAP_DEEP]
    if not deep_queue:
        per_url.append({"url": "(no-staff-links)", "ok": False,
                        "reason": "no_staff_links_on_landing_nor_intermediates",
                        "added": 0, "role": "follow"})

    for url in deep_queue:
        if agent.state.step_count >= MAX_STEPS:
            per_url.append({"url": url, "ok": False, "reason": "max_steps_reached",
                            "added": 0, "role": "deep-skipped"})
            print(f"  deep-skipped(max_steps) {url}", flush=True)
            continue
        dhtml, dblocked, dreason = render(url, scraper)
        if dblocked:
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False, "reason": dreason,
                            "added": 0, "role": "deep"})
            print(f"  deep-blocked {url} -> {dreason}", flush=True)
            continue
        try:
            b2 = len(agent.state.faculties)
            patch = agent.step_with_html(dhtml, current_url=url)
            pruned = prune_invalid(agent)
            added2 = len(agent.state.faculties) - b2
            per_url.append({"url": url, "ok": True,
                            "reason": f"{dreason}|patch_new={len(patch.new_profiles)}|pruned={pruned}",
                            "added": added2, "role": "deep"})
            print(f"  deep OK {url} +{len(patch.new_profiles)} patch / +{added2} net "
                  f"(pruned {pruned}) unit_total={len(agent.state.faculties)}", flush=True)
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False,
                            "reason": f"extraction_failed:{type(e).__name__}",
                            "added": 0, "role": "deep"})
            print(f"  deep-extract-fail {url}: {str(e)[:100]}", flush=True)
        time.sleep(0.8)

    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{key}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    print(f"DONE {key}: {n} verified -> {os.path.basename(export_path)}", flush=True)
    return {
        "key": key, "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
        "seeds": t["seeds"], "verified_count": n, "export_path": export_path,
        "checkpoint": ckpt, "staff_links": staff_links_all + second_hop_staff,
        "dept_paths": [urlparse(u).path or "/" for u in staff_links_all + second_hop_staff],
        "intermediates": intermediates, "per_url": per_url,
        "failed_urls": list(agent.state.failed_urls),
        "steps_used": agent.state.step_count,
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
                results.append({"key": key, "verified_count": 0, "export_path": "",
                                "status": f"fatal:{type(e).__name__}"})
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    summary_path = os.path.join(AGENT_STATES_DIR, "wave31_mu_linkfollow_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"batch": "wave31_mu_eng_la_linkfollow", "db_commit": False,
                   "univ_scope": "mahidol.ac.th only", "max_steps": MAX_STEPS,
                   "no_wiki": True, "units": results}, f, ensure_ascii=False, indent=2)
    total = sum(r.get("verified_count", 0) for r in results)
    print(f"\nBATCH DONE: {total} verified across {len(results)} units -> {summary_path}",
          flush=True)


if __name__ == "__main__":
    main()
