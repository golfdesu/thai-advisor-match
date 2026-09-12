"""Wave 20 recon #2 — local slug harvest potential + 3 targeted page probes.

Local (zero network):
  * how many NULL rows have a romanized URL slug we can trust?
    - *.pdf whose filename is a latin name (new.agro.ku.ac.th)
    - 2-token latin slugs (dent.chula /teams/x-y/, psy /th/people/x-y/, buu)
  * email-prefix corroboration rate for each slug candidate.

Network (few requests):
  * aad.kmitl /en/personnel/ page — EN staff names?
  * one w1.med.cmu listing page — Thai<->EN pairing HTML pattern
  * forest.ku.ac.th — is it the same KUForest app (EN toggle works)?
"""

import re
import ssl
import sys
import urllib.request
from urllib.parse import unquote, urlparse

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

OUT = r"C:\Users\chaya\AppData\Local\Temp\w20_probeF.txt"
THAI = re.compile(r"[\u0E00-\u0E7F]")
LATIN_SLUG = re.compile(r"^[a-z][a-z0-9.\-]*$", re.I)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                return f"__ERROR__ {type(exc).__name__}: {exc}"
    return "__ERROR__"


def last_segment(url):
    path = unquote(urlparse(url).path)
    return path.rstrip("/").rsplit("/", 1)[-1]


def slug_name(seg):
    """Return (first, last) from a romanized slug segment, or None."""
    seg = re.sub(r"\.pdf$", "", seg, flags=re.I)
    seg = re.sub(r"^(BIOT_EN_|BIOT_|CV_|EN_)", "", seg, flags=re.I)
    seg = re.sub(r"^(assoc[.\-]?prof|asst[.\-]?prof|dr|prof)[.\-]+", "", seg, flags=re.I)
    seg = re.sub(r"\d+$", "", seg)          # akkarat-2 trailing dedupe digit
    seg = re.sub(r"[-_.]{2,}", "-", seg)
    parts = [p for p in re.split(r"[-_.]", seg) if p and LATIN_SLUG.match(p) and len(p) >= 2]
    if len(parts) < 2:
        return None
    first, last = parts[0].title(), parts[-1].title()
    if len(last) < 3:
        return None
    return first, last


def email_prefixes(email):
    if not email or "@" not in email:
        return set()
    local = email.split("@")[0].lower()
    toks = re.split(r"[._\-0-9]+", local)
    return {t for t in toks if len(t) >= 3}


def main():
    db = SessionLocal()
    rows = (
        db.query(FacultyDB.id, FacultyDB.university, FacultyDB.full_name_th,
                 FacultyDB.first_name, FacultyDB.last_name, FacultyDB.email,
                 FacultyDB.profile_url)
        .filter(FacultyDB.openalex_id.is_(None))
        .all()
    )
    db.close()

    out = []
    stats = {}
    samples = {}
    corrob = {}
    for r in rows:
        rid, uni, fth, fn, ln, email, purl = r
        if not purl or THAI.search(purl):
            key = "00 no/Thai url"
        else:
            host = urlparse(purl).netloc.lower()
            seg = last_segment(purl)
            pair = slug_name(seg) if seg else None
            if pair:
                ep = email_prefixes(email or "")
                ok = pair[0].lower() in ep or pair[1].lower() in ep
                key = f"A {host}"
                corrob.setdefault(host, [0, 0])
                corrob[host][0 if ok else 1] += 1
                samples.setdefault("A " + host, []).append((seg, pair, email, str(fth)[:40]))
            else:
                key = f"B other {host}"
                samples.setdefault(key, []).append((seg, email, str(fth)[:30]))
        stats[key] = stats.get(key, 0) + 1

    out.append("=== LOCAL SLUG HARVEST POTENTIAL (NULL rows) ===")
    for k in sorted(stats):
        if k.startswith(("A ", "00")):
            out.append(f"  {k}: {stats[k]}")
    out.append("\n=== EMAIL CORROBORATION (A buckets: matched / unmatched) ===")
    for h, (m, u) in sorted(corrob.items(), key=lambda kv: -(kv[1][0] + kv[1][1])):
        out.append(f"  {h}: {m}/{m+u}")
    out.append("\n=== SAMPLES per corroborated host ===")
    for h, s in sorted(samples.items()):
        if not h.startswith("A "):
            continue
        out.append(f"  --- {h} ({len(s)})")
        for row in s[:8]:
            out.append(f"      {row}")
    out.append("\n=== B buckets (no latin 2-token slug), counts ===")
    for k in sorted(stats):
        if k.startswith("B "):
            out.append(f"  {k}: {stats[k]}")
    # non-corroborated A samples — risk check
    out.append("\n=== A samples WITHOUT email corroboration (first 6/host) ===")
    for h, s in sorted(samples.items()):
        if not h.startswith("A "):
            continue
        host = h[2:]
        ep_all = []
        for seg, pair, email, fth in s:
            ep = email_prefixes(email or "")
            if not (pair[0].lower() in ep or pair[1].lower() in ep):
                ep_all.append((seg, pair, email, fth))
        for row in ep_all[:6]:
            out.append(f"  {host}: {row}")

    out.append("\n=== NETWORK PROBES ===")
    h = fetch("https://www.aad.kmitl.ac.th/en/personnel/")
    out.append(f"aad /en/personnel/: len={len(h) if not h.startswith('__') else h[:80]}")
    if not h.startswith("__"):
        out.append(f"   title={re.search(chr(60)+'title[^>]*>(.*?)'+chr(60)+'/title>', h, re.S).group(1).strip()[:100] if re.search(chr(60)+'title[^>]*>(.*?)'+chr(60)+'/title>', h, re.S) else '?'}")
        latin_runs = re.findall(r">([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,3})\s*<", h)
        cnt = {}
        for m in latin_runs:
            cnt[m] = cnt.get(m, 0) + 1
        out.append("   EN-name-ish strings: " + str(sorted(cnt.items(), key=lambda kv: -kv[1])[:25]))

    h = fetch("https://w1.med.cmu.ac.th/patho/about-us/medical-teacher/")
    out.append(f"\nw1.med patho listing len={len(h)}")
    # find Thai name with adjacent latin name
    zone = re.findall(r"[^<>]{0,60}[\u0E00-\u0E7F][^<>]{0,40}<[^>]+>[^<]*[A-Z][a-z]+ [A-Z][a-z]+[^<]{0,50}", h)
    out.append("   Thai+EN adjacency raw hits: %d" % len(zone))
    for z in zone[:6]:
        out.append("   > " + re.sub(r"\s+", " ", z)[:140])
    pairs = re.findall(r"[\u0E00-\u0E7F][\u0E00-\u0E7F .ฯ]*\((?:ศ\.|รศ\.|ผศ\.|อ\.)?([A-Z][a-zA-Z.\- ]{4,40}(?:[A-Z][a-zA-Z.\-]{3,}))\)", h)
    out.append("   paren-EN-after-Thai hits: %d" % len(pairs))
    for p in pairs[:10]:
        out.append("   > " + p)

    h = fetch("https://vet.ku.ac.th/", timeout=25)
    out.append(f"\nvet.ku.ac.th root: len={len(h) if not h.startswith('__') else h[:60]}")
    h2 = fetch("https://forest.ku.ac.th/", timeout=25)
    t = re.search(r"<title[^>]*>(.*?)</title>", h2, re.S)
    out.append(f"forest.ku.ac.th root title: {t.group(1).strip()[:80] if t else h2[:80]}")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(str(x) for x in out) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
