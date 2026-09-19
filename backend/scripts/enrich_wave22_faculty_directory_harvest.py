# -*- coding: utf-8 -*-
"""Wave 22 — Faculty directory discovery harvest (no synthesis).

Targets the 367 no-URL rows clustered in a few faculties (WU Science 88,
UP ICT 69, MJU AgriProd 44, MFU Law 32, ...). These rows have NO profile_url,
so W21 could never fetch a page for them. This runner starts from the
faculty's OWN homepage (host already proven by sibling DB rows — never
guessed) and follows same-host personnel/staff links one level:

  homepage -> personnel|staff|teacher links -> directory pages
           -> person pages (capped) -> Thai-anchor pairing (W21 gates)

Every candidate is a verbatim Latin string from the institution's HTML.
Same anti-synthesis gates as W21 (valid_pair, person-name gate, degree
strip, cross-row uniqueness, PDPA redaction). Journalled apply to
wave22_directory_en_apply_log.json (reversible).

Faculties whose DB rows contain ZERO hosts (WU Eng, WU Informatics) are NOT
seeded here — their domains would have to be guessed. They ride the next
round via university-site school-link crawling.

Usage (from repo root):
  python backend/scripts/enrich_wave22_faculty_directory_harvest.py            # dry-run
  python backend/scripts/enrich_wave22_faculty_directory_harvest.py --apply    # high + xconf-medium
  python backend/scripts/enrich_wave22_faculty_directory_harvest.py --apply --high-only
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("backend/scripts"))

from rapidfuzz import fuzz  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.db_models import FacultyDB  # noqa: E402
from enrich_wave20_english_names import THAI  # noqa: E402
from enrich_wave21_listing_english_names import (  # noqa: E402
    probe_keyable, thai_anchor, latin_pair_from_text,
    email_corroborates,
)
from agentic_pipeline.content_pruner import ContentPruner  # noqa: E402
from agentic_pipeline.state_reducer import redact_pdpa_and_sanitize  # noqa: E402

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
CAND_PATH = os.path.join(CHECKPOINT_DIR, "wave22_directory_en_candidates.json")
APPLY_PATH = os.path.join(CHECKPOINT_DIR, "wave22_directory_en_apply_log.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Seeds: (university_th, faculty_th) -> homepage host PROVEN by sibling DB rows.
# Never add a host here that does not already appear in faculties.profile_url.
SEEDS = {
    ("มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาวิทยาศาสตร์"): ["science.wu.ac.th"],
    ("มหาวิทยาลัยพะเยา", "คณะเทคโนโลยีสารสนเทศและการสื่อสาร"): ["ict.up.ac.th"],
    ("มหาวิทยาลัยแม่โจ้", "คณะผลิตกรรมการเกษตร"): ["agri.mju.ac.th", "ap.mju.ac.th"],
    ("มหาวิทยาลัยแม่ฟ้าหลวง", "สำนักวิชานิติศาสตร์"): ["law.mfu.ac.th"],
}

STAFF_LINK_RE = re.compile(
    r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.S | re.I)
STAFF_ANCHOR_PAT = re.compile(
    r"personnel|staff|teacher|lecturer|faculty.?member|directory|people|"
    r"บุคลากร|คณาจารย์|อาจารย์|สายวิชาการ|ทำเนียบ|สมาชิก",
    re.I)
TAG_RE = re.compile(r"<[^>]+>")
PERSON_HREF_PAT = re.compile(
    r"(\?|&)(id|pid|username|user|staff_id)=\w+|"
    r"/(person|people|staff|profile|teams|faculty|member|portfolio)[^\"']*",
    re.I)
MAX_PERSON_PAGES_PER_FACULTY = 150


def clean_text(blob: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", blob or ""))).strip()


def fetch(url: str, timeout: int = 30) -> "str | None":
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                html = r.read().decode("utf-8", "replace")
                time.sleep(0.3)
                return html
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None


def fetch_host_root(host: str) -> "tuple[str, str] | tuple[None, None]":
    for scheme in ("https", "http"):
        html = fetch(f"{scheme}://{host}/")
        if html and len(html) > 2000:
            return f"{scheme}://{host}", html
    return None, None


def same_host_links(base: str, html: str):
    host = urllib.parse.urlparse(base).netloc.lower()
    links = []
    seen = set()
    for href, inner in STAFF_LINK_RE.findall(html or ""):
        text = clean_text(inner)
        if not text or not STAFF_ANCHOR_PAT.search(text):
            continue
        absu = urllib.parse.urljoin(base + "/", href.strip())
        p = urllib.parse.urlparse(absu)
        if p.netloc.lower() != host or p.scheme not in ("http", "https"):
            continue
        if absu in seen:
            continue
        seen.add(absu)
        links.append((absu, text[:60]))
    return links


def pair_anchors_in_page(html: str, anchors: "dict[str, str]", emails: "dict[str, str]"):
    """Same pairing core as W21 L-block (exact anchor=high, fuzzy92=medium),
    plus strict (pair inside matched block) and xconf (email agreement)."""
    pruned = ContentPruner.prune_html(html or "", max_output_chars=60000)
    pruned = redact_pdpa_and_sanitize(pruned) or ""
    blocks = [b.strip() for b in re.split(r"\n\s*\n|\n", pruned) if b.strip()]
    out = {}
    for rid, anchor in anchors.items():
        if not anchor or len(anchor) < 4:
            continue
        hits = []
        for i, b in enumerate(blocks):
            exact = anchor in b
            fuzzy = (not exact) and fuzz.partial_ratio(anchor, b) >= 92
            if not (exact or fuzzy):
                continue
            window = " ".join(blocks[max(0, i - 1): i + 2])
            pair = latin_pair_from_text(window)
            if pair:
                solo = latin_pair_from_text(b)
                hits.append((pair, "high" if exact else "medium",
                             solo is not None and tuple(solo) == tuple(pair)))
        uniq = {p for p, _, _ in hits}
        if len(uniq) == 1:
            pair = next(iter(uniq))
            conf = "high" if any(c == "high" for p, c, _ in hits if p == pair) else "medium"
            strict = any(s for p, _, s in hits if p == pair)
            xconf = email_corroborates(pair, emails.get(rid, ""))
            out[rid] = (pair, conf, strict, xconf)
    # cross-row uniqueness per page
    claim = defaultdict(list)
    for rid, (pair, _, _, _) in out.items():
        claim[tuple(pair)].append(rid)
    return {rid: v for rid, v in out.items() if len(claim[tuple(v[0])]) == 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--high-only", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--faculties", type=int, default=0,
                    help="pilot limit: first N seeded faculties (0 = all)")
    args = ap.parse_args()

    db = SessionLocal()
    rows = (db.query(FacultyDB.id, FacultyDB.first_name, FacultyDB.last_name,
                     FacultyDB.full_name_th, FacultyDB.university_th,
                     FacultyDB.faculty_th, FacultyDB.profile_url, FacultyDB.email)
            .filter(FacultyDB.openalex_id.is_(None)).all())
    db.close()
    targets = [r for r in rows
               if not probe_keyable(r.first_name, r.last_name, r.profile_url, r.email)]
    print(f"NULL={len(rows)} harvest-targets={len(targets)}", flush=True)

    fac_keys = sorted(SEEDS)
    if args.faculties:
        fac_keys = fac_keys[: args.faculties]
    fac_rows = {k: [r for r in targets
                    if (r.university_th, r.faculty_th) == k] for k in fac_keys}
    for k in fac_keys:
        safe = f"{k[0][:20]}.. | {k[1][:30]}..".encode("ascii", "replace").decode()
        print(f"  {safe} rows={len(fac_rows[k])}", flush=True)

    cands = {}
    stats = defaultdict(int)
    for fk in fac_keys:
        anchors = {r.id: thai_anchor(r.full_name_th) for r in fac_rows[fk]}
        emails = {r.id: (r.email or "") for r in fac_rows[fk]}
        if not anchors:
            continue
        dir_pages, person_pages = [], []
        for host in SEEDS[fk]:
            base, home = fetch_host_root(host)
            if not home:
                stats[f"root_fail:{host}"] += 1
                continue
            links = same_host_links(base, home)
            stats[f"staff_links:{host}"] = len(links)
            for url, _text in links:
                (person_pages if PERSON_HREF_PAT.search(url) else dir_pages).append(url)
        # also treat staff links found ON directory pages (one more level, same host)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            dir_html = dict(zip(dir_pages, ex.map(fetch, dir_pages)))
        for url, html in list(dir_html.items()):
            if not html:
                continue
            for url2, _t in same_host_links(url, html):
                if PERSON_HREF_PAT.search(url2):
                    if url2 not in person_pages:
                        person_pages.append(url2)
                elif url2 not in dir_pages and url2 not in dir_html:
                    dir_pages.append(url2)
        person_pages = person_pages[:MAX_PERSON_PAGES_PER_FACULTY]
        todo = [(u, h) for u, h in dir_html.items() if h]
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            extra = dict(zip([u for u in dir_pages if u not in dir_html],
                             ex.map(fetch, [u for u in dir_pages if u not in dir_html])))
        todo += [(u, h) for u, h in extra.items() if h]
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            ph = dict(zip(person_pages, ex.map(fetch, person_pages)))
        todo += [(u, h) for u, h in ph.items() if h]
        stats[f"pages_ok:{fk[1][:12]}"] = len(todo)
        for url, html in todo:
            found = pair_anchors_in_page(html, anchors, emails)
            for rid, (pair, conf, strict, xconf) in found.items():
                if rid in cands:
                    continue  # first page wins (directory before person pages)
                cands[rid] = {"en": list(pair), "conf": conf, "strict": strict,
                              "xconf": xconf, "method": "D-block",
                              "url": url, "faculty": list(fk)}
                stats[f"D_{conf}{'_strict' if strict else ''}{'_xconf' if xconf else ''}"] += 1

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    json.dump(cands, open(CAND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    safe_stats = {str(k).encode("ascii", "replace").decode(): v for k, v in stats.items()}
    print(f"candidates={len(cands)} {safe_stats}", flush=True)
    print(f"checkpoint -> {CAND_PATH}", flush=True)

    if not args.apply:
        print("(dry-run - nothing written. Re-run with --apply.)", flush=True)
        return

    def wanted(c):
        if c["conf"] == "high":
            return True
        return not args.high_only and c["conf"] == "medium" and (
            c.get("strict") is True or c.get("xconf") is True)
    keep = {rid: c for rid, c in cands.items() if wanted(c)}
    journal = json.load(open(APPLY_PATH, encoding="utf-8")) if os.path.exists(APPLY_PATH) else []
    journalled = {j["id"] for j in journal}
    db = SessionLocal()
    n = 0
    for rid, c in keep.items():
        r = db.get(FacultyDB, rid)
        if r is None or probe_keyable(r.first_name, r.last_name, r.profile_url, r.email):
            continue
        th_cur = (r.first_name or "") + (r.last_name or "")
        if (not th_cur.strip()) or THAI.search(th_cur):
            if rid not in journalled:
                journal.append({"id": rid, "first_name": r.first_name,
                                "last_name": r.last_name, "full_name_th": r.full_name_th})
                journalled.add(rid)
            r.first_name, r.last_name = c["en"][0], c["en"][1]
            n += 1
    db.commit()
    json.dump(journal, open(APPLY_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    db.close()
    print(f"APPLY: names written={n}/{len(keep)} journal={len(journal)} -> {APPLY_PATH}", flush=True)


if __name__ == "__main__":
    main()
