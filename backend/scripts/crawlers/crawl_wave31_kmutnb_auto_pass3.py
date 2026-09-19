"""Wave31 pass 3: civil + powereng personnel pages, static-only with retry.

Loads existing wave31 checkpoint, appends extractions, re-exports.
Scope: kmutnb.ac.th only. Checkpoint-only, NO DB commit.
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

from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent  # noqa: E402
from scripts.agentic_pipeline.state_reducer import (  # noqa: E402
    save_state_checkpoint, load_state_checkpoint)

AGENT_STATES_DIR = os.path.join(ROOT, "backend", "data", "agent_states")
KEY = "wave31_kmutnb_auto"
SEEDS = [
    "http://civil.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
    "http://powereng.cit.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/",
]
MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
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


def fetch_retry(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36",
                "Accept-Language": "th-TH,th;q=0.9,en;q=0.7"})
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=25) as r:
                return r.read().decode("utf-8", errors="ignore"), r.getcode()
        except Exception as e:  # noqa: BLE001
            print(f"  fetch try{i + 1} {url}: {type(e).__name__}", flush=True)
            time.sleep(3.0)
    return "", 0


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
    ckpt_file = os.path.join(AGENT_STATES_DIR, f"{KEY}.json")
    agent.state = load_state_checkpoint(ckpt_file)
    print(f"LOADED {len(agent.state.faculties)} existing", flush=True)
    per_url = []
    for url in SEEDS:
        html, code = fetch_retry(url)
        d = sum(html.count(m) for m in MARKERS)
        print(f"FETCH {url} http={code} chars={len(html)} density={d}", flush=True)
        if not html or d < 5:
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False,
                            "reason": f"static thin http={code} d={d}"})
            continue
        try:
            before = len(agent.state.faculties)
            patch = agent.step_with_html(html, current_url=url)
            bad = [fid for fid, f in agent.state.faculties.items()
                   if not valid_person_name(f.get("full_name_th", ""))]
            for fid in bad:
                agent.state.faculties.pop(fid, None)
            added = len(agent.state.faculties) - before
            per_url.append({"url": url, "ok": True,
                            "reason": f"static_chars={len(html)}|"
                            f"patch_new={len(patch.new_profiles)}|pruned={len(bad)}",
                            "added": added})
            print(f"  OK +{len(patch.new_profiles)} patch / +{added} net "
                  f"| total {len(agent.state.faculties)}", flush=True)
        except Exception as e:  # noqa: BLE001
            agent.state.failed_urls.append(url)
            per_url.append({"url": url, "ok": False,
                            "reason": f"extraction_failed:{type(e).__name__}"})
        time.sleep(2.0)
    agent.state.status = "completed"
    ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
    export_path = os.path.join(AGENT_STATES_DIR, f"{KEY}_export.py")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(agent.export_as_dataset_python())
    n = len(agent.state.faculties)
    summ_file = os.path.join(AGENT_STATES_DIR, "wave31_kmutnb_auto_summary.json")
    with open(summ_file, encoding="utf-8") as f:
        summary = json.load(f)
    summary["units"][0]["verified_count"] = n
    summary["units"][0]["per_url"] = summary["units"][0].get("per_url", []) + per_url
    summary["units"][0]["failed_urls"] = list(agent.state.failed_urls)
    summary["units"][0]["serp_needed"] = (n == 0)
    with open(summ_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"DONE {KEY}: {n} verified -> {export_path}", flush=True)


if __name__ == "__main__":
    main()
