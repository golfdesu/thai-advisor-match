# -*- coding: utf-8 -*-
"""Orphan check 3 (DIRECT official-site only, NO SERPAPI).
Verifies grad (โท/เอก) programs for SWU COSCI + MFU IT via urllib + BrowserScraper.
NO DB writes. Output: backend/data/agent_states/orphan_program_check3.json
"""
import os, sys, re, json, ssl, urllib.request, urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
OUT = os.path.join(ROOT, "backend", "data", "agent_states", "orphan_program_check3.json")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

GRAD_RE = re.compile(r"(ปริญญาโท|ปริญญาเอก|มหาบัณฑิต|ดุษฎีบัณฑิต|วท\.ม\.|ศศ\.ม\.|นศ\.ม\.|ปร\.ด\.|Ph\.?D\.?|Master|Doctoral|Graduate)", re.I)
COSCI_RE = re.compile(r"(นวัตกรรมสื่อสารสังคม|Social Communication Innovation|COSCI|cosci)", re.I)
IT_RE = re.compile(r"(เทคโนโลยีสารสนเทศ|Information Technology|\bIT\b|School of Information Technology|สำนักวิชาเทคโนโลยีสารสนเทศ)", re.I)
LINK_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")

def fetch_static(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            raw = r.read()
            html = raw.decode("utf-8", errors="replace")
            return {"url": url, "final_url": r.geturl(), "status": r.getcode(), "html": html, "method": "urllib"}
    except Exception as e:
        return {"url": url, "final_url": url, "status": -1, "html": "", "method": "urllib", "error": str(e)[:200]}

def fetch_render(url):
    try:
        from app.scrapers.browser_scraper import BrowserScraper
        s = BrowserScraper(headless=True, page_load_timeout=30)
        try:
            html = s.scroll_and_render_all(url, scroll_pause=1.0, max_scrolls=3, extra_wait=2.0)
        finally:
            s.close()
        if html:
            return {"url": url, "final_url": url, "status": 200, "html": html, "method": "render"}
        return {"url": url, "final_url": url, "status": -1, "html": "", "method": "render", "error": "empty_render"}
    except Exception as e:
        return {"url": url, "final_url": url, "status": -1, "html": "", "method": "render", "error": str(e)[:200]}

def clean(t):
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", t or "")).strip()[:160]

def extract_grad_links(html, base, scope_re):
    out = []
    seen = set()
    for href, inner in LINK_RE.findall(html or ""):
        txt = clean(inner)
        if not txt or len(txt) < 4:
            continue
        if GRAD_RE.search(txt) or GRAD_RE.search(href):
            if scope_re and not (scope_re.search(txt) or scope_re.search(href)):
                # keep grad links anyway if page itself is scope-filtered; mark scope=False
                scope = False
            else:
                scope = True
            full = urllib.parse.urljoin(base, href.strip())
            if full in seen:
                continue
            seen.add(full)
            out.append({"title": txt, "link": full, "scope_match": scope})
    return out

def page_has_grad(html):
    return bool(GRAD_RE.search(html or ""))

def check_unit(key, seeds, scope_re, scope_names):
    pages = []
    links = []
    for u in seeds:
        r = fetch_static(u)
        # render fallback when static thin/empty or no grad keywords
        if (not r["html"] or len(r["html"]) < 5000 or not page_has_grad(r["html"])) and r["status"] != -1:
            rr = fetch_render(u)
            if rr["html"] and len(rr["html"]) > len(r["html"]):
                r = rr
        elif r["status"] == -1 or not r["html"]:
            rr = fetch_render(u)
            if rr["html"]:
                r = rr
        txt = clean(r["html"])[:2000]
        has_grad = page_has_grad(r["html"])
        has_scope = bool(scope_re.search(r["html"]))
        gl = extract_grad_links(r["html"], r["final_url"], scope_re)
        links.extend(gl)
        pages.append({"seed": u, "final_url": r["final_url"], "status": r["status"],
                      "method": r["method"], "bytes": len(r["html"]),
                      "has_grad_kw": has_grad, "has_scope_kw": has_scope,
                      "error": r.get("error", ""), "snippet": txt[:600]})
    scoped = [l for l in links if l["scope_match"]]
    # verdict: EXISTS only if >=1 scoped grad program link/name, else ABSENT if pages fetched OK, else UNCLEAR
    ok_pages = [p for p in pages if p["status"] == 200 and p["bytes"] > 1000]
    if scoped:
        verdict = "EXISTS"
    elif not ok_pages:
        verdict = "UNCLEAR"
    else:
        verdict = "ABSENT"
    return {"faculty": key, "scope": scope_names, "verdict": verdict,
            "scoped_programs": scoped[:20], "all_grad_links": links[:20], "pages": pages}

def main():
    swu_seeds = [
        "https://cosci.swu.ac.th/",
        "http://cosci.swu.ac.th/",
        "https://cosci.swu.ac.th/courses/",
        "https://cosci.swu.ac.th/programs/",
        "https://grad.swu.ac.th/",
        "https://grad.swu.ac.th/programs/",
    ]
    mfu_seeds = [
        "https://www.mfu.ac.th/en/academics.html",
        "https://www.mfu.ac.th/en/academics/school-of-information-technology.html",
        "https://its.mfu.ac.th/",
        "https://it.mfu.ac.th/",
        "https://www.mfu.ac.th/",
    ]
    swu = check_unit("swu_cosci", swu_seeds, COSCI_RE,
                     ["วิทยาลัยนวัตกรรมสื่อสารสังคม", "College of Social Communication Innovation"])
    mfu = check_unit("mfu_it", mfu_seeds, IT_RE,
                     ["สำนักวิชาเทคโนโลยีสารสนเทศ", "School of Information Technology"])
    data = {"swu_cosci": swu, "mfu_it": mfu,
            "_meta": {"method": "direct-official-only", "serpapi": False, "db_writes": False}}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for k in ("swu_cosci", "mfu_it"):
        u = data[k]
        print(f"{k}: {u['verdict']} scoped={len(u['scoped_programs'])} gradlinks={len(u['all_grad_links'])}")
        for p in u["pages"]:
            print(f"  {p['status']} {p['method']} {p['bytes']}b grad={p['has_grad_kw']} scope={p['has_scope_kw']} {p['seed']} -> {p['final_url']} {p['error']}")
        for s in u["scoped_programs"][:10]:
            print(f"  * {s['title'][:100]} | {s['link']}")
    print(f"WROTE {OUT}")

if __name__ == "__main__":
    main()
