"""Wave36 retry2b: KKU HUSO 2nd-hop only (hardened driver).

Scope: official *.ac.th ONLY (kku.ac.th). Headless selenium only.
Checkpoint-only, NO DB commit. Base https://huso.kku.ac.th/en/staff/
(107K chars dens 16 patch 0) -> collect individual profile/person links
(cap 15), driver.get each with per-hop TimeoutException recovery
(driver restart), feed page_source to FacultyExtractionAgent
(--univ-th "มหาวิทยาลัยขอนแก่น", --faculty-th
"คณะมนุษยศาสตร์และสังคมศาสตร์", --no-wiki).
Export: backend/data/agent_states/wave36_kku_huso_export.py
Usage (repo root): python backend/scripts/crawlers/crawl_wave36_kkuhuso_hops_retry2b.py
"""
import hashlib
import os
import re
import sys
import time
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
T = {"univ_th": "มหาวิทยาลัยขอนแก่น", "univ_en": "Khon Kaen University",
     "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
     "faculty_en": "Faculty of Humanities and Social Sciences"}
BASE = "https://huso.kku.ac.th/en/staff/"
ALLOWED = (".kku.ac.th", "kku.ac.th")
MAX_HOPS, MAX_STEPS = 15, 60
MARKERS = ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร.", "Prof", "Lecturer", "Asst"]
BOIL = ("สถานที่ติดต่อ", "ติดต่อ", "สำนักวิชา", "สาขาวิชา", "ภาควิชา",
        "มหาวิทยาลัย", "คณะ", "หลักสูตร", "สำนักงาน", "ฝ่าย",
        "computer", "science group", "research group", "breadcrumb",
        "menu", "home", "download", "sidebar", "office")
_STRIP = re.compile(
    r"^(?:ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
    r"ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์\s*ดร\.|อาจารย์|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|"
    r"Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lecturer|Professor)\s*",
    re.IGNORECASE)
HOP_HINT = re.compile(r"profil|person|staff|people|member|lecturer|teacher|faculty|advisor|researcher", re.I)


def is_official(u: str) -> bool:
    try:
        return urlparse(u).netloc.lower().split(":")[0].endswith(ALLOWED)
    except Exception:
        return False


def dens(t: str) -> int:
    return sum((t or "").count(m) for m in MARKERS)


def valid(n) -> bool:
    if not n:
        return False
    if any(b in n.lower() for b in BOIL):
        return False
    base = _STRIP.sub("", n.strip()).strip(" .")
    toks = [x for x in re.split(r"\s+", base) if x]
    if len(toks) < 2 or any(len(x) < 2 for x in toks):
        return False
    if re.search(r"@|http|www\.|\.ac\.th|\d{3,}", base):
        return False
    return True


def prune(agent) -> int:
    bad = [fid for fid, f in agent.state.faculties.items()
           if not valid(f.get("full_name_th", ""))]
    for fid in bad:
        agent.state.faculties.pop(fid, None)
    if bad:
        agent.state.dedup_thai_names = {
            k: v for k, v in agent.state.dedup_thai_names.items() if v not in bad}
    return len(bad)


def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--disable-gpu")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--window-size=1280,1600")
    o.add_argument("--disable-extensions")
    o.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/128.0.0.0 Safari/537.36")
    o.set_capability("acceptInsecureCerts", True)
    o.page_load_strategy = "eager"
    d = webdriver.Chrome(options=o)
    d.set_page_load_timeout(25)
    return d


def safe_get(driver_box, url: str, sleep: float = 2.0):
    """GET with one driver-restart recovery. Returns (html, note)."""
    d = driver_box[0]
    try:
        d.get(url)
        time.sleep(sleep)
        return d.page_source or "", ""
    except Exception as e1:  # noqa: BLE001
        note = f"{type(e1).__name__}"
        try:
            d.quit()
        except Exception:
            pass
        time.sleep(1.5)
        try:
            d = make_driver()
            driver_box[0] = d
            d.get(url)
            time.sleep(sleep)
            return d.page_source or "", f"{note}+restart_ok"
        except Exception as e2:  # noqa: BLE001
            return "", f"{note}+restart_{type(e2).__name__}"


def main():
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)
    agent = FacultyExtractionAgent(
        target_university_th=T["univ_th"], target_university_en=T["univ_en"],
        target_faculty_th=T["faculty_th"], target_faculty_en=T["faculty_en"],
        session_id="wave36_kku_huso", max_steps=MAX_STEPS,
        checkpoint_dir=AGENT_STATES_DIR, auto_lookup_wiki=False)
    box = [make_driver()]
    steps = 0
    try:
        html0, note0 = safe_get(box, BASE, 3.0)
        d = box[0]
        before = len(agent.state.faculties)
        try:
            patch = agent.step_with_html(html0, current_url=BASE)
            pruned = prune(agent)
            a0, p0, e0 = len(agent.state.faculties) - before, len(patch.new_profiles), ""
        except Exception as e:  # noqa: BLE001
            a0, p0, pruned, e0 = 0, 0, 0, f"extraction_failed:{type(e).__name__}"
        steps += 1
        from selenium.webdriver.common.by import By
        try:
            anchors = d.find_elements(By.XPATH, "//a[@href]")
        except Exception:
            anchors = []
        hops, seen = [], set()
        for a in anchors:
            try:
                href = (a.get_attribute("href") or "").strip()
                txt = (a.text or "").strip()
                if not href or href.startswith(("javascript:", "mailto:", "#")):
                    continue
                absu = urljoin(BASE, href).split("#")[0]
                if not is_official(absu) or absu.rstrip("/") == BASE.rstrip("/") or absu in seen:
                    continue
                if HOP_HINT.search(absu) or HOP_HINT.search(txt) or len(txt.split()) >= 2:
                    seen.add(absu)
                    hops.append((absu, txt[:40]))
            except Exception:
                continue
        hops.sort(key=lambda x: (-x[0].count("/"), x[0]))
        hops = hops[:MAX_HOPS]
        det = [f"base_chars={len(html0)} dens={dens(html0)} patch={p0} "
               f"err={e0 or '-'} get={note0 or 'ok'} hops_found={len(hops)}"]
        ok = 0
        for absu, txt in hops:
            if steps >= MAX_STEPS:
                det.append("budget_stop")
                break
            html_c, note = safe_get(box, absu, 2.0)
            if not html_c or (len(html_c) < 1500 and dens(html_c) < 3):
                det.append(f"hop_thin:{absu}:chars={len(html_c)}:get={note or 'ok'}")
                continue
            b = len(agent.state.faculties)
            try:
                p = agent.step_with_html(html_c, current_url=absu)
                prune(agent)
                new, pn, er = len(agent.state.faculties) - b, len(p.new_profiles), ""
            except Exception as e:  # noqa: BLE001
                new, pn, er = 0, 0, f"extraction_failed:{type(e).__name__}"
            steps += 1
            ok += 1
            det.append(f"hop:{absu}:chars={len(html_c)}:dens={dens(html_c)}:"
                       f"patch={pn}:err={er or '-'}:get={note or 'ok'}:linktext={txt!r}")
        agent.state.status = "completed"
        ckpt = save_state_checkpoint(agent.state, output_dir=AGENT_STATES_DIR)
        n = len(agent.state.faculties)
        export_path = os.path.join(AGENT_STATES_DIR, "wave36_kku_huso_export.py")
        header = (f'"""Wave36 retry2b selenium checkpoint-only export (wave36_kku_huso).\n'
                  f"Univ={T['univ_th']} Faculty={T['faculty_th']}.\n"
                  f"Method: headless selenium (eager) direct; base {BASE} + "
                  f"2nd-hop individual profile/person links (cap {MAX_HOPS}, "
                  f"driver-restart recovery); every page_source fed to "
                  f"FacultyExtractionAgent.step_with_html (step_calls={steps}).\n"
                  f"Verified count in body: {n}. Official *.ac.th only, NO DB commit.\n"
                  f"Interaction: {BASE} hops={ok}/{len(hops)} "
                  f"[{' ; '.join(det[:5])}]\n\"\"\"\n")
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(agent.export_as_dataset_python())
        print(f"DONE wave36_kku_huso: {n} verified, hops {ok}/{len(hops)} "
              f"steps={steps} -> {os.path.basename(export_path)}", flush=True)
        # merge summary preserving SU unit
        import json as _j
        sp = os.path.join(AGENT_STATES_DIR, "wave36_selenium_summary.json")
        try:
            s = _j.load(open(sp, encoding="utf-8"))
            units = [u for u in s.get("units", []) if u.get("key") != "wave36_kku_huso"]
        except Exception:
            units, s = [], {"batch": "wave36_selenium_interaction_retry2", "db_commit": False,
                            "univ_scope": "su.ac.th + kku.ac.th only"}
        units.append({"key": "wave36_kku_huso", "faculty_th": T["faculty_th"],
                      "faculty_en": T["faculty_en"], "verified_count": n,
                      "export_path": export_path, "checkpoint": ckpt, "status": "verified",
                      "per_url": [{"url": BASE, "ok": True,
                                   "reason": f"render_ok_html_chars={len(html0)}|patch_new={p0}|"
                                             f"pruned={pruned}|hops={ok}/{len(hops)}",
                                   "rendered_chars": len(html0),
                                   "rendered_density": dens(html0), "clicks": ok,
                                   "click_detail": det, "added": n, "pruned": pruned}],
                      "failed_urls": list(agent.state.failed_urls),
                      "total_clicks": ok, "step_calls": steps})
        s["units"] = units
        _j.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"SUMMARY merged -> {sp}", flush=True)
    finally:
        try:
            box[0].quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
