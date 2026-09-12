"""Wave 20 recon (READ-ONLY): which NULL-name domains carry a harvestable English name?

For each domain with the most openalex_id-NULL rows, pull a few profile URLs straight
out of the DB, fetch them, and report where an English name shows up (if anywhere):
  - og:title / <title> in latin script
  - an explicit "Name (English)" / "ชื่อ-นามสกุล (ภาษาอังกฤษ)" label
  - a discoverable /en/ path variant of the same profile
  - list pages that carry EN names next to the Thai one (CMU dept pages)

Nothing is written to the DB. Results go to a text file so the Thai console
encoding (cp1252) cannot eat them.
"""

import re
import ssl
import sys
import urllib.request
from collections import Counter
from urllib.parse import urljoin, urlparse

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

OUT = r"C:\Users\chaya\AppData\Local\Temp\w20_probeE.txt"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

THAI = re.compile(r"[\u0E00-\u0E7F]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z.'\-]{2,}")


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                raw = r.read()
            enc = "utf-8"
            m = re.search(rb'charset=["\']?([\w\-]+)', raw[:4096], re.I)
            if m:
                enc = m.group(1).decode("ascii", "ignore")
            return raw.decode(enc, "replace")
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                return f"__ERROR__ {type(exc).__name__}: {exc}"
    return "__ERROR__"


def title_of(html):
    out = []
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        out.append(("title", re.sub(r"\s+", " ", m.group(1)).strip()[:120]))
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)"[^>]+property=["\']og:title["\']', html, re.I)
    if m:
        out.append(("og:title", m.group(1).strip()[:120]))
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S | re.I)
    if m:
        h1 = re.sub(r"<[^>]+>", " ", m.group(1))
        out.append(("h1", re.sub(r"\s+", " ", h1).strip()[:120]))
    return out


def en_name_markers(html):
    """Explicit English-name labels, whatever the language of the page."""
    pats = [
        r"Name\s*\(([Ee]nglish|[Ee]ng\.?)\)\s*[:\-]?\s*([^<\n]{3,80})",
        r"\(([Ee]nglish|[Ee]ng\.?)\)\s*[:\-]\s*([^<\n]{3,80})",
        r"ชื่อ[-\s]*(?:นามสกุล)?\s*\((?:ภาษาอังกฤษ|อังกฤษ|English)\)\s*[:\-]?\s*([^<\n]{3,80})",
        r"英文名\s*[:\-]?\s*([^<\n]{3,80})",
        r'itemprop="name"\s+content="([^"]{3,80})"',
        r'<span[^>]*class="[^"]*(?:name-en|english-name|en-name)[^"]*"[^>]*>([^<]{3,80})',
    ]
    hits = []
    for p in pats:
        for m in re.finditer(p, html):
            val = (m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)).strip()
            if val and not THAI.search(val) and len(LATIN_WORD.findall(val)) >= 2:
                hits.append((p[:24], val[:80]))
    return hits[:6]


def probe_domain(out, name, urls, sample):
    out.append(f"\n{'=' * 78}\n### {name}  (sample {min(sample, len(urls))} of {len(urls)})")
    for u in urls[:sample]:
        html = fetch(u)
        if html.startswith("__ERROR__"):
            out.append(f"  FETCH-FAIL {u}\n      {html[:150]}")
            continue
        out.append(f"  {u}  len={len(html)}")
        for kind, val in title_of(html):
            tag = "EN?" if not THAI.search(val) else "th"
            out.append(f"      {kind:8s}[{tag:3s}] {val}")
        for pat, val in en_name_markers(html):
            out.append(f"      MARKER {pat}... -> {val}")
        # does an /en/ sibling exist?
        low = u.lower()
        cands = []
        if "/en/" in low:
            cands.append(low.replace("/en/", "/th/"))
        else:
            cands.append(low.replace("/th/", "/en/"))
            parsed = urlparse(u)
            cands.append(f"{parsed.scheme}://en.{parsed.netloc}{parsed.path}" + (f"?{parsed.query}" if parsed.query else ""))
            cands.append(urljoin(u.rstrip("/") + "/", "../en/"))
        for c in cands:
            if c == low:
                continue
            h2 = fetch(c, timeout=25)
            if h2.startswith("__ERROR__"):
                continue
            ts = title_of(h2)
            good = [v for _, v in ts if v and not THAI.search(v)]
            if good:
                out.append(f"      EN-VARIANT OK {c} -> {good[0][:90]}  len={len(h2)}")
            else:
                out.append(f"      en-variant {c} -> no latin title (len={len(h2)})")


def main():
    db = SessionLocal()
    rows = (
        db.query(FacultyDB.profile_url, FacultyDB.full_name_th, FacultyDB.university)
        .filter(FacultyDB.openalex_id.is_(None), FacultyDB.profile_url.isnot(None))
        .all()
    )
    by_host = {}
    for url, th, uni in rows:
        host = urlparse(url).netloc.lower()
        by_host.setdefault(host, []).append(url)

    out = ["NULL-openalex rows WITH profile_url, by host:"]
    for host, urls in sorted(by_host.items(), key=lambda kv: -len(kv[1]))[:24]:
        out.append(f"  {host} = {len(urls)}")
    db.close()

    targets = [
        ("www.pharm.chula.ac.th", 3),
        ("eng.buu.ac.th", 3),
        ("new.agro.ku.ac.th", 3),
        ("www.aad.kmitl.ac.th", 3),
        ("www.dent.cmu.ac.th", 3),
        ("w1.med.cmu.ac.th", 4),
        ("ag.kku.ac.th", 3),
        ("edu.swu.ac.th", 3),
        ("www.eng.su.ac.th", 3),
        ("www.dent.chula.ac.th", 2),
    ]
    for host, n in targets:
        urls = by_host.get(host, [])
        if not urls:
            near = [h for h in by_host if host.split(".")[0] in h]
            out.append(f"\n### {host}: NO ROWS (near: {near[:4]})")
            continue
        probe_domain(out, host, urls, n)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote", OUT, len(out), "lines")


if __name__ == "__main__":
    main()
