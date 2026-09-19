# -*- coding: utf-8 -*-
"""Wave 23 — English-tree harvest (no synthesis).

Diagnosis (2026-09-19): TH directory pages hold Thai rosters with NO Latin
(UP ICT one pager lists all 69 anchors, zero Latin pairs), while the sites'
EN trees are huge (science.wu.ac.th/?lang=en = 345KB, ict.up.ac.th/?lang=en
= 137KB). So harvest the EN tree instead and attribute pairs WITHOUT Thai
anchors: the row's OWN institutional email corroborates the pair
(WU/UP/MFU/MJU emails follow first.last / first.last-initial conventions).

Attribution rule (per EN page):
  E1 high:   pair's first AND last agree with email parts (full or >=4 prefix)
  E2 medium: first-full + last-initial agree (kumpol.k <-> Kumpol Klunklin)
  same pair claimed by 2+ rows on any page -> drop everywhere (uniqueness)

TH-URL staff links are re-fetched in EN form (?lang=en, /en/ path insert)
plus staff-link discovery on the EN roots. Bilingual cards (Thai+Latin on
the EN tree) also go through the W22 Thai-anchor pairing as a bonus tier.

Journalled apply -> wave23_english_tree_apply_log.json (reversible).

Usage (from repo root):
  python backend/scripts/enrich_wave23_english_tree_harvest.py            # dry-run
  python backend/scripts/enrich_wave23_english_tree_harvest.py --apply    # E1 + anchor-high + xconf-medium
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("backend/scripts"))

from app.core.database import SessionLocal  # noqa: E402
from app.models.db_models import FacultyDB  # noqa: E402
from enrich_wave20_english_names import THAI  # noqa: E402
from enrich_wave21_listing_english_names import (  # noqa: E402
    probe_keyable, latin_pair_from_text, looks_like_person_name, valid_pair,
)
from enrich_wave22_faculty_directory_harvest import (  # noqa: E402
    SEEDS, fetch, fetch_host_root, same_host_links, pair_anchors_in_page,
    thai_anchor,
)
from agentic_pipeline.content_pruner import ContentPruner  # noqa: E402
from agentic_pipeline.state_reducer import redact_pdpa_and_sanitize  # noqa: E402

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
CAND_PATH = os.path.join(CHECKPOINT_DIR, "wave23_english_tree_candidates.json")
APPLY_PATH = os.path.join(CHECKPOINT_DIR, "wave23_english_tree_apply_log.json")


def en_variants(url: str):
    """Yield EN forms of a TH URL (WordPress Polylang + ?lang=en patterns)."""
    p = urllib.parse.urlparse(url)
    yield url
    q = dict(urllib.parse.parse_qsl(p.query))
    if "lang" not in {k.lower() for k in q}:
        sep = "&" if p.query else "?"
        yield f"{url}{sep}lang=en"
    if not p.path.startswith("/en/"):
        yield urllib.parse.urlunparse(
            (p.scheme, p.netloc, "/en" + (p.path or "/"), p.params, p.query, p.fragment))


def email_tier(pair, email: str) -> str:
    """E1 (both names agree) / E2 (first-full + last-initial) / '' (no agree)."""
    if not pair or not email or "@" not in email:
        return ""
    local = email.split("@")[0].lower()
    parts = [x for x in re.split(r"[\._\-]+", local) if x.isalpha()]
    if not parts:
        return ""
    first = pair[0].lower().split()
    last = pair[1].lower().split()
    if not first or not last:
        return ""

    def agrees(token, emailside_min4=True):
        for e in parts:
            if token == e:
                return True
            if emailside_min4 and len(token) >= 4 and len(e) >= 4 and (
                    e.startswith(token) or token.startswith(e)):
                return True
        return False

    first_ok = any(agrees(t) for t in first)
    last_ok = any(agrees(t) for t in last)
    if first_ok and last_ok:
        return "E1"
    if first_ok and any(len(e) == 1 and last[-1].startswith(e) for e in parts):
        return "E2"
    return ""


def pairs_on_page(html: str):
    """All Latin pairs block-by-block on an EN page (verbatim strings only)."""
    pruned = ContentPruner.prune_html(html or "", max_output_chars=60000)
    pruned = redact_pdpa_and_sanitize(pruned) or ""
    out = []
    for b in (x.strip() for x in re.split(r"\n\s*\n|\n", pruned) if x.strip()):
        pair = latin_pair_from_text(b)
        if pair:
            out.append(pair)
    # dedupe preserving order
    seen, uniq = set(), []
    for p in out:
        if tuple(p) not in seen:
            seen.add(tuple(p))
            uniq.append(p)
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--high-only", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
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

    cands, stats = {}, defaultdict(int)
    for fk in sorted(SEEDS):
        fac_rows = [r for r in targets if (r.university_th, r.faculty_th) == fk]
        if not fac_rows:
            continue
        by_email = defaultdict(list)
        for r in fac_rows:
            if r.email:
                by_email[r.email.split("@")[0].lower()].append(r.id)
        anchors = {r.id: thai_anchor(r.full_name_th) for r in fac_rows}
        emails = {r.id: (r.email or "") for r in fac_rows}

        # EN roots + TH staff links in EN form
        en_pages = []
        th_links = []
        for host in SEEDS[fk]:
            base, home = fetch_host_root(host)
            if home:
                th_links += [u for u, _ in same_host_links(base, home)]
            for root in (f"https://{host}/en/", f"https://{host}/?lang=en",
                         f"http://{host}/en/"):
                h = fetch(root)
                if h and len(h) > 2000:
                    en_pages.append(root)
                    en_pages += [u for u, _ in same_host_links(root, h)]
        for u in list(th_links):
            en_pages += [v for v in en_variants(u) if v != u]
        # dedupe, cap
        seen, todo_urls = set(), []
        for u in en_pages:
            if u not in seen:
                seen.add(u)
                todo_urls.append(u)
        todo_urls = todo_urls[:80]
        stats["en_pages"] += len(todo_urls)

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            pages = dict(zip(todo_urls, ex.map(fetch, todo_urls)))
        ok = {u: h for u, h in pages.items() if h and len(h) > 2000}
        stats["en_pages_ok"] += len(ok)
        # one deeper level: staff pages' own same-host links (EN rosters often
        # sit one click below the staff landing page)
        sub_urls = []
        for url, html in ok.items():
            for u2, _t in same_host_links(url, html):
                if u2 not in ok and u2 not in sub_urls:
                    sub_urls.append(u2)
        sub_urls = sub_urls[:80]
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            sub_pages = dict(zip(sub_urls, ex.map(fetch, sub_urls)))
        for u, h in sub_pages.items():
            if h and len(h) > 2000 and u not in ok:
                ok[u] = h
        stats["en_pages_ok_deep"] = len(ok)

        # Tier A: Thai-anchor pairing (bilingual cards on the EN tree)
        for url, html in ok.items():
            found = pair_anchors_in_page(html, anchors, emails)
            for rid, (pair, conf, strict, xconf) in found.items():
                if rid in cands:
                    continue
                cands[rid] = {"en": list(pair), "conf": conf, "strict": strict,
                              "xconf": xconf, "method": "EN-anchor", "url": url}
                stats[f"ENa_{conf}"] += 1

        # Tier B: email attribution of every Latin pair on EN pages
        claims = defaultdict(list)  # pair -> [(rid, tier)]
        pair_page = {}
        for url, html in ok.items():
            for pair in pairs_on_page(html):
                for r in fac_rows:
                    t = email_tier(pair, r.email or "")
                    if t:
                        claims[tuple(pair)].append((r.id, t))
                        pair_page.setdefault(tuple(pair), url)
        for pair, lst in claims.items():
            rids = {i for i, _ in lst}
            if len(rids) != 1:
                stats["E_dup_claim"] += 1
                continue
            rid, tier = lst[0]
            if rid in cands:
                continue
            conf = "high" if tier == "E1" else "medium"
            cands[rid] = {"en": list(pair), "conf": conf, "tier": tier,
                          "method": "EN-email", "url": pair_page[pair]}
            stats[f"ENe_{tier}"] += 1

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    json.dump(cands, open(CAND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    safe_stats = {str(k).encode("ascii", "replace").decode(): v for k, v in stats.items()}
    print(f"candidates={len(cands)} {safe_stats}", flush=True)
    print(f"checkpoint -> {CAND_PATH}", flush=True)

    if not args.apply:
        print("(dry-run - nothing written. Re-run with --apply.)", flush=True)
        return
    # EN-anchor hits on translated pages are weak: an exact Thai anchor may be
    # a news/sidebar mention, not a person card (observed: "ASAIHL AWARD",
    # "Read Voucher"). So EN-anchor applies ONLY with xconf/strict backing;
    # EN-email (E1/E2) is self-attributing by construction.
    def wanted(rid, c):
        if c["method"] == "EN-email":
            return c["conf"] == "high" or not args.high_only
        if c.get("xconf") is True or c.get("strict") is True:
            return c["conf"] == "high" or not args.high_only
        return False
    keep = {rid: c for rid, c in cands.items() if wanted(rid, c)}
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
