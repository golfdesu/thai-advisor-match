# -*- coding: utf-8 -*-
"""Wave 21 — Listing/Profile English-Name Harvester (no synthesis).

Finds romanized names for faculties the OpenAlex probe cannot key
(no direct Latin first/last, no person-slug, no first.last email) by
re-fetching their OWN institutional profile/listing pages and reading the
Latin name printed next to their Thai name. Every candidate is a verbatim
string from the institution's HTML — nothing is invented.

Methods (deterministic, zero LLM):
  P  person page (?id=, /person/, /portfolio.php?id=, ...) — <h1>/<title>
     Latin run becomes the candidate (institution's own rendering).
  L  shared listing page — the row's Thai anchor (title-stripped via the
     audited normalize_thai_title_and_name) must match a text block
     (exact substring, or RapidFuzz partial_ratio >= 92); the Latin pair in
     that block (+/-1 neighbour) becomes the candidate. The pair must be
     unique per page: claimed by 2+ rows or 2+ pairs in one block -> drop.

Gates (anti-hallucination):
  - valid_pair() from enrich_wave20_english_names (length + noise-word gates).
  - PDPA: phone numbers redacted before any text is kept (we keep no page
    text at all — only the name pair + source URL + method).
  - Journalled apply: previous values -> data/agent_states/
    wave21_listing_en_apply_log.json (reversible, like W20).

Usage (from repo root):
  python backend/scripts/enrich_wave21_listing_english_names.py            # harvest, dry-run report
  python backend/scripts/enrich_wave21_listing_english_names.py --apply    # write high+medium to DB
  python backend/scripts/enrich_wave21_listing_english_names.py --apply --high-only
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
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
from enrich_wave20_english_names import (  # noqa: E402
    THAI, NAME_TOKEN, valid_pair, latin_words, pair_from_words,
)
from agentic_pipeline.state_reducer import (  # noqa: E402
    normalize_thai_title_and_name, redact_pdpa_and_sanitize,
)
from agentic_pipeline.content_pruner import ContentPruner  # noqa: E402

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
CAND_PATH = os.path.join(CHECKPOINT_DIR, "wave21_listing_en_candidates.json")
APPLY_PATH = os.path.join(CHECKPOINT_DIR, "wave21_listing_en_apply_log.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PERSON_URL_RE = re.compile(
    r"(\?|&)(id|pid|username|user|staff_id)=\w+|/(person|people|staff|profile|teams|faculty|member|portfolio)[^?]*$", re.I)
# tokens that are org units / boilerplate, not person names (extends W20 NOISE_WORDS
# which lacks faculty/department vocabulary — without these, "prakpum Engineering"
# style username+department pairs slip through as false candidates)
EXTRA_NOISE = {
    "engineering", "engineer", "technology", "technologies", "design", "science",
    "sciences", "medicine", "medical", "nursing", "pharmacy", "pharmaceutical",
    "dentistry", "dental", "architecture", "education", "management", "business",
    "economics", "law", "arts", "industrial", "industry", "graduate", "school",
    "college", "institute", "campus", "hospital", "clinic", "laboratory", "lab",
    "project", "projects", "system", "systems", "information", "computer",
    "mechanical", "electrical", "civil", "chemical", "department", "faculty",
    "division", "program", "programme", "center", "centre", "office", "section",
    # publication-venue / date words leaking from on-page publication lists
    "proceedings", "proceeding", "journal", "journals", "conference", "symposium",
    "workshop", "seminar", "transactions", "letters", "review", "article", "paper",
    "papers", "thesis", "dissertation", "presented", "published", "international",
    "national", "annual", "research", "researcher", "volume", "vol", "issue",
    "pages", "chapter", "editor", "editors",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    # rank words in full form (W20 RANK_EN only catches abbreviations, so
    # "Assistant Aobaom" slipped through as a false candidate)
    "assistant", "assist", "associate", "assoc", "professor", "lecturer",
    "instructor", "fellow", "doctor", "physician", "surgeon", "dean",
    # research-area / department vocabulary ("Database Intui",
    # "Ophthalmology Khwanngern", "Tourism Hansapinyo", "Fisheries Kasetsart")
    "database", "databases", "data", "ophthalmology", "tourism", "hospitality",
    "fisheries", "fishery", "agriculture", "agricultural", "veterinary",
    "anatomy", "physiology", "biochemistry", "microbiology", "pathology",
    "surgery", "surgical", "pediatric", "pediatrics", "psychiatry", "radiology",
    "oncology", "cardiology", "neurology", "therapy", "clinical", "public",
    "health", "environmental", "environment", "energy", "polymer", "material",
    "materials", "textile", "food", "nutrition", "forestry", "forest", "animal",
    "plant", "soil", "water", "marine", "planning", "music", "fine", "applied",
    "social", "humanity", "humanities", "language", "linguistics", "literature",
    "history", "philosophy", "psychology", "sociology", "political",
    "communication", "journalism", "marketing", "finance", "accounting",
    "logistics", "nursing",
    # university-name tokens ("Fisheries Kasetsart University" headers)
    "kasetsart", "chulalongkorn", "mahidol", "khonkaen", "thammasat",
    "songkla", "burapha", "srinakharinwirot", "walailak", "silpakorn",
    "phayao", "maejo", "naresuan", "kmitl", "kmutt", "kmutnb",
    # clinical specialties + card-header words ("Gastroenterology Leerapun",
    # "Pramote Expertise" from column headers on listing pages)
    "expertise", "specialty", "specialist", "interests", "education",
    "qualifications", "degree", "degrees", "bachelor", "master", "doctoral",
    "phone", "room", "address",
    "gastroenterology", "nephrology", "dermatology", "urology", "orthopedics",
    "orthopaedic", "orthopedic", "radiology", "anesthesiology", "obstetrics",
    "gynecology", "otolaryngology", "hematology", "endocrinology",
    "rheumatology", "infectious", "emergency", "rehabilitation", "preventive",
    "forensic", "transfusion",
    # award/news/button junk seen on EN trees ("ASAIHL AWARD", "Read Voucher",
    # "GLOBE Scientist", "Thailand Innovation")
    "award", "awards", "voucher", "read", "more", "click", "download",
    "scientist", "globe", "innovation", "innovations", "congratulations",
    "congratulation", "welcome", "news", "events", "event", "seminar",
    "ceremony", "meeting", "contest", "competition", "scholarship", "grant",
}
USERNAME_LIKE_RE = re.compile(r"^[A-Z]{2,4}$")  # AWS, NSD, NSN ...
# trailing degree/professional suffixes ("Chanodom Piankusol MPH PH")
DEGREE_TOKENS = {
    "mph", "ph", "phd", "md", "rn", "rph", "dds", "dvm", "drph", "mba",
    "ma", "msc", "ms", "bsc", "bs", "mphil", "pharmd", "facp", "facc",
    "mphtm", "dtm", "dip", "cert", "do", "dsc", "edd", "jr", "sr",
    "ii", "iii", "iv",
}
LATIN_RUN_RE = re.compile(r"[A-Za-z][A-Za-z.'\- ]{3,}")
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
# mirror of the OpenAlex probe keyability gate (direct romanized only here;
# slug/email fallbacks are handled by the probe itself, so harvest targets
# rows the probe cannot key even with fallbacks)
SLUG_PATTERN = re.compile(r"/(?:academic-staff|people|faculty|staff|teams|profile|person)/([a-zA-Z0-9_\-]+)/?", re.I)
NOISE_SLUGS = {"index", "detail", "profile", "people", "staff", "faculty", "team", "academic-staff"}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def direct_romanized(first, last) -> bool:
    fn = strip_accents(first).strip() if first else ""
    ln = strip_accents(last).strip() if last else ""
    return bool(fn and ln and fn.isascii() and ln.isascii() and len(ln) >= 2)


def slug_fallback(profile_url, email):
    if profile_url:
        m = SLUG_PATTERN.search(profile_url)
        if m:
            raw = re.sub(r"-(?:th|en)$", "", m.group(1).strip().lower())
            parts = [p for p in raw.split("-") if p.isalpha() and len(p) >= 2 and p not in NOISE_SLUGS]
            if len(parts) >= 2:
                return True
    if email and "@" in email:
        local = email.split("@")[0].lower()
        parts = [p for p in re.split(r"[\._]", local) if p.isalpha() and len(p) >= 3]
        if len(parts) >= 2:
            return True
    return False


def probe_keyable(first, last, profile_url, email) -> bool:
    return direct_romanized(first, last) or slug_fallback(profile_url, email)


def thai_anchor(full_name_th: str) -> str:
    """Title-stripped Thai base name via the audited normalizer (never raw regex)."""
    try:
        _title, _full, base = normalize_thai_title_and_name(full_name_th or "")
    except Exception:
        base = full_name_th or ""
    base = re.sub(r"\s+", " ", base).strip()
    return base


def clean_html_text(blob: str) -> str:
    text = unescape(TAG_RE.sub(" ", blob or ""))
    return re.sub(r"\s+", " ", text).strip()


def looks_like_person_name(pair) -> bool:
    """Post-gate on top of valid_pair: reject usernames and org-unit words.

    Real Latin names on Thai university pages are Title Case (or FULL CAPS);
    lowercase single tokens (prakpum, sommas) are login usernames, 2-4 letter
    all-caps tokens (AWS, NSD) are username abbreviations, and faculty words
    (Engineering, Technology) are department boilerplate. A wrong-but-confident
    name is far worse than a miss, so reject aggressively.
    """
    if not pair:
        return False
    first, last = pair
    toks = (first.split() + last.split())
    if any(t.lower() in EXTRA_NOISE for t in toks):
        return False
    f0 = first.split()[0] if first.split() else ""
    if not f0 or not f0[0].isupper():
        return False
    if USERNAME_LIKE_RE.match(f0):
        return False
    # internal capitals are acronyms/fragments, never Thai romanizations
    # ("PEx", "eVoucher"; real surnames like McDonald don't occur here)
    if any(re.search(r"[A-Z].*[A-Z]", t) for t in toks if len(t) > 2):
        return False
    return True


def latin_pair_from_text(text: str):
    words = latin_words(text or "")
    # strip trailing degree suffixes before pairing ("... Piankusol MPH PH")
    while len(words) > 2 and words[-1].lower().rstrip(".") in DEGREE_TOKENS:
        words.pop()
    if len(words) < 2:
        return None
    pair = pair_from_words(words)
    if pair and valid_pair(pair) and looks_like_person_name(pair):
        return (pair[0].strip(), pair[1].strip())
    return None


def clean_stored_pair(en_list):
    """Post-clean a checkpointed pair (same degree-strip + gates). Returns
    cleaned [first, last] or None if it no longer validates."""
    words = [w for w in " ".join(en_list or []).split() if w]
    while len(words) > 2 and words[-1].lower().rstrip(".") in DEGREE_TOKENS:
        words.pop()
    if len(words) < 2:
        return None
    pair = pair_from_words(words)
    if pair and valid_pair(pair) and looks_like_person_name(pair):
        return [pair[0].strip(), pair[1].strip()]
    return None


def fetch_url(url: str, timeout: int = 30) -> "str | None":
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                time.sleep(0.3)  # politeness between hits on the same worker
                return raw
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None


def harvest_person_page(html: str):
    """Method P: single-person page -> (pair, 'P-h1'|'P-title') or (None, '')."""
    h1s = [clean_html_text(m) for m in H1_RE.findall(html or "")]
    for h in h1s:
        if h and not THAI.search(h):
            pair = latin_pair_from_text(h)
            if pair:
                return pair, "P-h1"
    m = TITLE_RE.search(html or "")
    if m:
        title = clean_html_text(m.group(1))
        title = re.split(r"\s*[-|–]\s*", title)[0].strip()
        if title and not THAI.search(title):
            pair = latin_pair_from_text(title)
            if pair:
                return pair, "P-title"
    return None, ""


def harvest_listing_page(html: str, anchors: "dict[str, str]"):
    """Method L: match each Thai anchor to a pruned text block, take its Latin pair.

    anchors: {row_id: thai_base_name}.
    Returns {row_id: (pair, conf, strict)} where strict=True means the pair was
    extractable from the MATCHED block alone (no +/-1 neighbour bleed), which
    removes the main wrong-person vector (adjacent card's name). Uniqueness
    across rows sharing the page is enforced by the caller.
    """
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
            out[rid] = (pair, conf, strict)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--high-only", action="store_true")
    ap.add_argument("--harvest", action="store_true",
                    help="re-fetch pages even when a candidate checkpoint exists "
                         "(default with --apply: reuse checkpoint, DB writes only)")
    ap.add_argument("--revectorize", action="store_true",
                    help="refresh 768-dim embeddings for journalled rows "
                         "(embedding_text includes first/last names)")
    ap.add_argument("--rescore", action="store_true",
                    help="stamp email-corroboration (xconf) onto checkpoint mediums "
                         "using DB emails (no network)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit-urls", type=int, default=0)
    args = ap.parse_args()

    if args.revectorize:
        revectorize_journalled()
        return
    if args.rescore:
        rescore_checkpoint()
        return
    if args.apply and not args.harvest and os.path.exists(CAND_PATH) and not args.limit_urls:
        cands = json.load(open(CAND_PATH, encoding="utf-8"))
        print(f"reusing checkpoint candidates={len(cands)} (pass --harvest to re-fetch)", flush=True)
    else:
        cands, _stats = harvest(args)

    if args.apply:
        apply_candidates(cands, args.high_only)
    else:
        print("(dry-run - nothing written. Re-run with --apply.)", flush=True)


def harvest(args):
    """Fetch + extract. Returns (cands, stats). Network-heavy; skipped by
    --apply when a checkpoint already exists (pass --harvest to force)."""
    db = SessionLocal()
    rows = (db.query(FacultyDB.id, FacultyDB.first_name, FacultyDB.last_name,
                     FacultyDB.full_name_th, FacultyDB.profile_url, FacultyDB.email)
            .filter(FacultyDB.openalex_id.is_(None)).all())
    db.close()

    targets = [r for r in rows if not probe_keyable(r.first_name, r.last_name, r.profile_url, r.email)]
    print(f"NULL total={len(rows)} probe-keyable={len(rows) - len(targets)} harvest-targets={len(targets)}", flush=True)

    by_url = defaultdict(list)
    no_url = 0
    for r in targets:
        if r.profile_url:
            by_url[r.profile_url].append(r)
        else:
            no_url += 1
    urls = sorted(by_url)
    if args.limit_urls:
        urls = urls[: args.limit_urls]
    print(f"distinct listing/profile URLs={len(by_url)} (fetching {len(urls)}) no-url rows={no_url}", flush=True)

    pages = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_url, u): u for u in urls}
        done = 0
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                html = fut.result()
            except Exception:
                html = None
            if html:
                pages[u] = html
            done += 1
            if done % 100 == 0:
                print(f"  fetched {done}/{len(urls)} ok={len(pages)}", flush=True)
    print(f"fetched ok={len(pages)}/{len(urls)}", flush=True)

    cands = {}
    stats = defaultdict(int)
    for u in urls:
        html = pages.get(u)
        if not html:
            stats["fetch_fail"] += 1
            continue
        rows_u = by_url[u]
        emails_u = {r.id: (r.email or "") for r in rows_u}
        if PERSON_URL_RE.search(u or ""):
            pair, how = harvest_person_page(html)
            if pair:
                for r in rows_u:
                    cands[r.id] = {"en": list(pair), "conf": "high", "method": how, "url": u}
                    stats["P"] += 1
                continue
            stats["P_miss"] += 1
            # fall through to listing-style anchor pairing on the same page:
            # some person pages (?username=) print Thai + Latin side by side
            anchors = {r.id: thai_anchor(r.full_name_th) for r in rows_u}
            found = harvest_listing_page(html, anchors)
            for rid, (fpair, conf, strict) in found.items():
                xconf = email_corroborates(fpair, emails_u.get(rid, ""))
                cands[rid] = {"en": list(fpair), "conf": conf, "strict": strict,
                              "xconf": xconf, "method": "P-block", "url": u}
                stats[f"P_block_{conf}{'_strict' if strict else ''}{'_xconf' if xconf else ''}"] += 1
            stats["P_rows_no_pair"] += len(rows_u) - len(found)
            continue
        anchors = {r.id: thai_anchor(r.full_name_th) for r in rows_u}
        found = harvest_listing_page(html, anchors)
        # cross-row uniqueness: one Latin pair claimed by 2+ rows -> drop all
        claim = defaultdict(list)
        for rid, (pair, conf, strict) in found.items():
            claim[tuple(pair)].append(rid)
        for rid, (pair, conf, strict) in found.items():
            if len(claim[tuple(pair)]) > 1:
                stats["L_dup_claim"] += 1
                continue
            xconf = email_corroborates(pair, emails_u.get(rid, ""))
            cands[rid] = {"en": list(pair), "conf": conf, "strict": strict,
                          "xconf": xconf, "method": "L-block", "url": u}
            stats[f"L_{conf}{'_strict' if strict else ''}{'_xconf' if xconf else ''}"] += 1
        stats["L_rows_no_pair"] += len(rows_u) - len(found)

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    json.dump(cands, open(CAND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"candidates={len(cands)} {dict(stats)}", flush=True)
    print(f"checkpoint -> {CAND_PATH}", flush=True)
    return cands, stats


def rescore_checkpoint() -> int:
    """Stamp xconf (email corroboration) onto checkpoint mediums + clean
    degree-suffixed pairs. No network."""
    cands = json.load(open(CAND_PATH, encoding="utf-8"))
    db = SessionLocal()
    rows = db.query(FacultyDB.id, FacultyDB.email).filter(
        FacultyDB.id.in_(list(cands))).all()
    db.close()
    emails = {r.id: r.email for r in rows}
    n = drop = 0
    for rid in list(cands):
        c = cands[rid]
        cleaned = clean_stored_pair(c.get("en"))
        if not cleaned:
            del cands[rid]
            drop += 1
            continue
        c["en"] = cleaned
        if c.get("conf") == "medium":
            c["xconf"] = email_corroborates(tuple(cleaned), emails.get(rid) or "")
            if c["xconf"]:
                n += 1
    json.dump(cands, open(CAND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"RESCORE: kept={len(cands)} dropped_cruft={drop} mediums_xconf_true={n}", flush=True)
    return n


def revectorize_journalled() -> int:
    """SOP Step 4: refresh embeddings for rows whose names changed.

    embedding_text embeds first_name/last_name, so W21 renames stale the
    stored vectors. Sequential (journal is small); EmbeddingService handles
    key rotation + gemini-embedding-001 fallback internally.
    """
    from app.core.embedding_service import EmbeddingService
    from enrichment.canonical_faculty_merge import build_embedding_text
    journal = []
    for path in (APPLY_PATH,
                 os.path.join(CHECKPOINT_DIR, "wave23_english_tree_apply_log.json")):
        if os.path.exists(path):
            journal += json.load(open(path, encoding="utf-8"))
    ids = list(dict.fromkeys(j["id"] for j in journal))  # de-dupe, keep order
    print(f"revectorize targets={len(ids)}", flush=True)
    svc = EmbeddingService()
    db = SessionLocal()
    n = 0
    for i, rid in enumerate(ids):
        r = db.get(FacultyDB, rid)
        if r is None:
            continue
        vec = svc.get_embedding(build_embedding_text(r))
        if vec and len(vec) == 768:
            r.embedding = vec
            n += 1
        if (i + 1) % 25 == 0:
            db.commit()
            print(f"  ...{i + 1}/{len(ids)} ok={n}", flush=True)
    db.commit()
    db.close()
    print(f"REVECTORIZE: refreshed={n}/{len(ids)}", flush=True)
    return n


def email_corroborates(pair, email) -> bool:
    """Second-tier check for medium candidates: does the institution's own
    email local-part agree with the harvested Latin pair?

    Covers full (somchai.kul ↔ Somchai Kul), prefix (kumpol.k ↔ Kumpol
    Klunklin) and initial (kumpol.k ↔ Kumpol K...) conventions. Department
    mailboxes (info@, chem@, ...) never match a person pair, so a hit is
    genuine per-person corroboration — the W20 >=2-tier rule, reused.
    """
    if not pair or not email or "@" not in email:
        return False
    local = email.split("@")[0].lower()
    parts = [p for p in re.split(r"[\._\-]+", local) if p.isalpha() and len(p) >= 1]
    if not parts:
        return False
    toks = [t.lower() for t in (pair[0].split() + pair[1].split()) if t]
    for t in toks:
        for e in parts:
            if t == e:
                return True
            if len(t) >= 4 and len(e) >= 4 and (e.startswith(t) or t.startswith(e)):
                return True
            if len(t) >= 4 and len(e) == 1 and t.startswith(e):
                return True  # first.last-initial convention
    # initial-initial: j.s ↔ Somchai Jaidee?
    if len(parts) >= 2 and all(len(p) == 1 for p in parts[:2]) and len(toks) >= 2:
        if toks[0].startswith(parts[0]) and toks[-1].startswith(parts[1]):
            return True
    return False


def apply_candidates(cands: dict, high_only: bool) -> int:
    """Journalled DB write. Only touches rows whose names are still Thai/empty.

    Without --high-only, medium candidates are applied ONLY when strict=True
    (pair inside the matched block) OR the row's own institutional email
    corroborates the pair (second-tier agreement). Plain mediums stay parked.
    Returns rows written."""
    def wanted(c):
        if c["conf"] == "high":
            return True
        return not high_only and c["conf"] == "medium" and (
            c.get("strict") is True or c.get("xconf") is True)
    keep = {rid: c for rid, c in cands.items() if wanted(c)}
    db = SessionLocal()
    journal = json.load(open(APPLY_PATH, encoding="utf-8")) if os.path.exists(APPLY_PATH) else []
    journalled = {j["id"] for j in journal}
    n = 0
    for i, (rid, c) in enumerate(keep.items()):
        r = db.get(FacultyDB, rid)
        if r is None:
            continue
        if probe_keyable(r.first_name, r.last_name, r.profile_url, r.email):
            continue  # resolved by another wave since harvest
        th_cur = (r.first_name or "") + (r.last_name or "")
        if (not th_cur.strip()) or THAI.search(th_cur):
            if rid not in journalled:
                journal.append({"id": rid, "first_name": r.first_name,
                                "last_name": r.last_name, "full_name_th": r.full_name_th})
                journalled.add(rid)
            r.first_name, r.last_name = c["en"][0], c["en"][1]
            n += 1
        if (i + 1) % 500 == 0:
            db.commit()
            json.dump(journal, open(APPLY_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    db.commit()
    json.dump(journal, open(APPLY_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    db.close()
    print(f"APPLY: names written={n}/{len(keep)} journal={len(journal)} -> {APPLY_PATH}", flush=True)
    print("NEXT: re-vectorize touched rows (embedding includes names), then re-run OpenAlex probe.", flush=True)
    return n


if __name__ == "__main__":
    main()
