"""Wave31 pass 2: extract staff from CIT dept subsite personnel pages (headless).

Scope: kmutnb.ac.th only. Checkpoint-only, NO DB commit, NO invented names.
Seeds are the discovered /บุคลากร/ (personnel) pages + subsite homepages.
Static-first (pages are static-dense); browser fallback if thin.
Exports backend/data/agent_states/wave31_kmutnb_auto_export.py.

Usage (repo root):
  python backend/scripts/crawlers/crawl_wave31_kmutnb_auto_pass2.py
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

SEEDS = [
    "https://mm.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "https://ascs.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "https://electrical.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "https://civil.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "https://powereng.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "https://mm.cit.kmutnb.ac.th/",
    "https://ascs.cit.kmutnb.ac.th/",
    "https://electrical.cit.kmutnb.ac.th/",
    "https://civil.cit.kmutnb.ac.th/",
    "https://powereng.cit.kmutnb.ac.th/",
]

ACADEMIC_MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
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


def fetch_static(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.7"})
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore"), r.getcode()
    except Exception:
        return "", 0


def density(t):
    return sum((t or "").count(m) for m in ACADEMIC_MARKERS)


def valid_person_name(full_name_th) -> bool:
    if not full_name_th:
        return False
    low = full_name_th.lower()
    if any(b in low for b in BOILERPLATE):
        return False
    base = _TITLE_STRIP.sub("", full_name_th.strip()).strip(" .")
    tokens = [t for t in re.split(r"\s+", base) if t]
    if len(tokens) < 2 or any(len(t) < 2 for t in tokens):
        return False
    if re.search(r"@|http|www\.|\.ac\.th|\d{3,}", base):
        return False
    return True


def main():
    agent = FacultyExtractionAgent(
        target_university_th="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        target_university_en="King Mongkut's University of Technology North Bangkok",
        target_faculty_th="วิทยาลัยเทคโนโลยีอุตสาหกรรม",
        target_faculty_en="College of Industrial Technology",
        session_id=KEY, max_steps=15,
        checkpoint_dir=AGENT_STATES_DIR, auto_lookup_wiki=False)
    scraper = BrowserScraper(headless=True, page_load_timeout=30)
    per_url = []
    try:
        for url in SEEDS:
            if ".kmutnb.ac.th" not in url:
                continue
            html, code = fetch_static(url)
            sd = density(html)
            use, src = html, f"static_{code}"
            if sd < 5:
                try:
                    rend = scraper.scroll_and_render_all(
                        url, scroll_pause=1.2, max_scrolls=3, extra_wait=2.0)
                except Exception as e:  # noqa: BLE001
                    rend = None
                    print(f"  BROWSER EXC {url}: {type(e).__name__}", flush=True)
                if rend and density(rend) > sd:
                    use, src = rend, "browser"
            if not use or code == 404 and not use:
                agent.state.failed_urls.append(url)
                per_url.append({"url": url, "ok": False,
                                "reason": f"empty_{src}"})
                print(f"  STOP {url} empty ({src})", flush=True)
                continue
            try:
                before = len(agent.state.faculties)
                patch = agent.step_with_html(use, current_url=url)
                bad = [fid for fid, f in agent.state.faculties.items()
                       if not valid_person_name(f.get("full_name_th", ""))]
                for fid in bad:
                    agent.state.faculties.pop(fid, None)
                added = len(agent.state.faculties) - before
                per_url.append({"url": url, "ok": True,
                                "reason": f"{src}_chars={len(use)}|"
                                f"patch_new={len(patch.new_profiles)}|"
                                f"pruned={len(bad)}",
                                "added": added})
                print(f"  OK {url} +{len(patch.new_profiles)} patch / +{added} net "
                      f"(pruned {len(bad)}) | total {len(agent.state.faculties)}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                agent.state.failed_urls.append(url)
                per_url.append({"url": url, "ok": False,
                                "reason": f"extraction_failed:{type(e).__name__}"})
                print(f"  FAIL {url}: {str(e)[:120]}", flush=True)
            time.sleep(1.0)
    finally:
        try:
            scraper.close()
        except Exception:
            pass
    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{KEY}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    summary = {"batch": "wave31_kmutnb_auto_headless", "db_commit": False,
               "univ_scope": "kmutnb.ac.th only",
               "units": [{"key": KEY, "verified_count": n,
                          "export_path": export_path, "checkpoint": ckpt,
                          "per_url": per_url,
                          "failed_urls": list(agent.state.failed_urls),
                          "serp_needed": (n == 0)}]}
    with open(os.path.join(AGENT_STATES_DIR, "wave31_kmutnb_auto_summary.json"),
              "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"DONE {KEY}: {n} verified -> {export_path}", flush=True)


if __name__ == "__main__":
    main()
