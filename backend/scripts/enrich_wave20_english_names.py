"""Wave 20 — English Name Resolver + OpenAlex unlock.

The 6,707 faculties with openalex_id IS NULL are mostly Thai-script names:
OpenAlex indexes Latin names, so they can never be keyed as-is. This script
derives each person's OWN romanization (never invented) from sources already
in the DB or on their institutional page, in tiers of decreasing trust:

  T1  Latin name glued at the tail of full_name_th by our own crawlers
      ("...กฤษฎา สังขนันท์Assoc. Prof. Dr. Krisada Sangkhanan")
  T2  institutional email local part, first.last convention
      ("anusorn.lungka@cmu.ac.th"); department mailboxes are blacklisted
  T3  personal URL slug on whitelisted person-path hosts
      (".../teams/kanoknadda-tavedhikul/" -> Kanoknadda Tavedhikul)
  T4  first_name/last_name columns already Latin (never probed, just lazy)
  T5  (network) KUForest Person.aspx English mode via the ASP.NET language
      postback — one request per profile, title becomes "First Last - KUforest"
  T6  (network) psy.chula.ac.th /en/people/<slug>/ page <h1>

Confidence: >=2 independent tiers agreeing (exact or prefix) -> "high";
single tier -> "medium". T1/T5/T6 (institution's own text) are authoritative;
T2/T3 are accepted because the surname gate in the OpenAlex resolver requires
an exact whole-token match — a wrong romanization yields no_hit, not a wrong
person.

Apply: for rows whose first_name/last_name are Thai-script (or NULL) we write
the English pair into first_name/last_name (the API exposes these as the
display English name), and clean the glued Latin suffix out of full_name_th.
The previous DB values are journalled to data/agent_states/wave20_apply_log.json
so the wave is reversible.

Usage:
  python scripts/enrich_wave20_english_names.py            # local tiers, dry-run report
  python scripts/enrich_wave20_english_names.py --network  # + T5/T6 harvesting (resumable)
  python scripts/enrich_wave20_english_names.py --apply    # write to Postgres (main thread)
"""

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from urllib.parse import unquote, urlparse

sys.path.insert(0, ".")

from sqlalchemy import or_

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

STATE_DIR = "data/agent_states"
CAND_PATH = os.path.join(STATE_DIR, "wave20_enames_candidates.json")
KU_PATH = os.path.join(STATE_DIR, "wave20_kuforest_en.json")
APPLY_PATH = os.path.join(STATE_DIR, "wave20_apply_log.json")

THAI = re.compile(r"[\u0E00-\u0E7F]")
RANK_EN = re.compile(
    r"\b(ass(?:ociate)?\.?|asst\.?|prof\.?|dr\.?|mr\.?|ms\.?|mrs\.?|assoc\.?|aph\.?|"
    r"lecturer|instructor|researcher|emeritus|adjunct|senior)\b", re.I)
PHONE_NOISE = re.compile(r"\+?\d[\d\s\-\.]{5,}")
NOISE_WORDS = {
    "publications", "publication", "email", "tel", "fax", "position", "department",
    "faculty", "university", "research", "interest", "interests", "profile",
    "homepage", "google", "scholar", "scopus", "detail", "uri", "index",
    "personnel", "teacher", "members", "member", "directory", "academic", "staff",
    "people", "personal", "search", "head", "office", "administration", "view",
    "more", "page", "curriculum", " vitae", "cv", "th", "en", "and", "the", "of",
    "division", "center", "programme", "program", "course", "page", "home",
    "md", "mr", "ms", "drs", "prof", "assoc", "asst",
}
# mailboxes that are departments/shared, never a person
MAILBOX_BLOCK = re.compile(
    r"^(info|admin|secretar|faculty|depart|office|itunit|webmail|postmaster|"
    r"chemist|chemistry|biology|biolog|math|mathema|physic|zoo|botany|microbio|"
    r"anatomy|biochem|pharmac|pathol|parasit|food|agri|agricult|vet|nursing|"
    r"educat|psy|library|regist|finance|person|general|dean|hospi|med|cmu|kku|"
    r"ku|tu|su|wu|mu|buu|psu|kmitl|kmUTT|mfu|mju|nu|swu|nida|ru|bu|nnru|mru|tru)+", re.I)

NAME_TOKEN = re.compile(r"^[A-Za-zÀ-ɏ'\-]+$")

PERSON_PATH_HOSTS = {
    "www.dent.chula.ac.th": r"^/teams/([\w\-]+)/?$",
    "www.psy.chula.ac.th": r"^/(?:en|th)?/?people/([\w\-]+)/?$",
    "www.ahs.chula.ac.th": r"/(?:people|staff|profile)/([\w\-]+)",
    "tbs.tu.ac.th": r"/staff/([\w\-]+)",
    "law.tu.ac.th": r"/(?:faculty|people|profile)/([\w\-]+)",
    "eng.buu.ac.th": r"/faculty-members/([\w\-]+)/?$",
    "www.cpe.kmutt.ac.th": r"/(?:people|faculty|staff)/([\w\-]+)",
    "chem.kmutt.ac.th": r"/(?:people|faculty|staff|profile)/([\w\-]+)",
    "www.su.ac.th": r"/(?:staff|people|profile)/([\w\-]+)",
    "ssrudlp.ssru.ac.th": r"/staff/([\w_\-]+)",
    "fish.ku.ac.th": r"/(?:people|member|staff)/([\w\-]+)",
    "www.dent.cmu.ac.th": None,   # dept listing pages, not person pages
    "www.ict.mahidol.ac.th": r"/(?:people|staff|member)/([\w_\-]+)",
    "sci.ku.ac.th": r"/(?:people|member|staff)/([\w\-]+)",
    "www.sci.psu.ac.th": r"/(?:person|people|profile)/([\w\-]+)",
}


# ---------------------------------------------------------------- helpers ---

def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def valid_pair(p):
    if not p:
        return False
    first, last = p
    firsts = first.split()
    lasts = last.split()
    if len(firsts) < 1 or len(lasts) < 1:
        return False
    if len(firsts[0]) < 2 or len("".join(lasts)) < 4:
        return False
    toks = firsts + lasts
    if all(t.lower().strip(".") in NOISE_WORDS for t in toks):
        return False
    return all(NAME_TOKEN.match(t) and not THAI.search(t) for t in toks)


def split_camel(token):
    """'AmponnawaratPublication' -> 'Amponnawarat Publication'."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", token)


def latin_words(blob):
    blob = PHONE_NOISE.sub(" ", unescape(blob or ""))
    words = []
    for raw in re.findall(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ'\.\-]*", blob):
        for w in split_camel(raw).split():
            w = w.strip(".-:' ")
            if len(w) >= 2 and w.lower() not in NOISE_WORDS and not RANK_EN.match(w) \
                    and not re.match(r"^[A-Z]\.?$", w):
                words.append(w)
    return words


def pair_from_words(words):
    if len(words) < 2:
        return None
    # last token may be a multi-part surname glued by hyphen; keep all trailing words
    first = words[0]
    last = words[-1]
    if len(words) >= 3 and len(words[-1]) < 5 and words[-2][-1].islower() is False:
        pass
    mid = words[1:-1]
    # CMU style: "Assoc. Prof. Dr. Somchai Somsuk"  -> keep trailing 2-3 words
    tail = words[-2:] if len(words) > 2 and all(len(w) > 2 for w in words[-2:]) else None
    cand = (first, " ".join(mid + [last])) if mid else (first, last)
    for c in ((first, last), cand, (words[-2], words[-1]) if len(words) >= 2 else None,
              (words[-2], " ".join(words[-1:])) if len(words) >= 2 else None):
        if valid_pair(c):
            return c
    return cand if valid_pair(cand) else None


def t1_from_full_name(full_name_th):
    """Latin person name glued inside full_name_th."""
    if not full_name_th:
        return None, None
    cleaned = unquote(full_name_th)
    runs = re.findall(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ.,'&\- ]{4,}", cleaned)
    best_words, best = None, ""
    for r in runs:
        w = latin_words(r)
        if best_words is None or len(w) > len(best_words):
            best_words, best = w, r
    if not best_words or len(best_words) < 2:
        return None, cleaned
    return pair_from_words(best_words), cleaned


def t2_from_email(email, row_first_th=""):
    if not email or "@" not in email or MAILBOX_BLOCK.match(email.split("@")[0].strip()):
        return None
    local = email.strip().split("@")[0].lower()
    # KKU-style 7+ letter concatenations are not parseable; require a delimiter
    parts = [p for p in re.split(r"[._\-]+", local) if len(p) >= 3]
    if len(parts) < 2:
        return None
    first, last = parts[0].title(), " ".join(parts[1:]).title()
    pair = (first, last)
    if not valid_pair(pair):
        return None
    return pair


def t3_from_url(url):
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    path = unquote(urlparse(url).path)
    rx = PERSON_PATH_HOSTS.get(host)
    if not rx:
        return None
    m = re.search(rx, path, re.I)
    if not m:
        return None
    seg = m.group(1)
    if "." in seg or not re.fullmatch(r"[A-Za-z][A-Za-z0-9._\-]*", seg):
        return None
    seg = re.sub(r"\d+$", "", seg)
    parts = [p for p in re.split(r"[-_.]+", seg) if len(p) >= 3]
    parts = [p for p in parts if p.lower() not in NOISE_WORDS]
    if len(parts) < 2:
        return None
    pair = (parts[0].title(), " ".join(parts[1:]).title())
    return pair if valid_pair(pair) else None


def agree(a, b):
    """exact or one-sided-prefix agreement between two tier pairs."""
    if not a or not b:
        return False
    an, bn = [norm(a[0]), norm(a[1])], [norm(b[0]), norm(b[1])]
    hits = 0
    for x, y in zip(an, bn):
        if x == y or (min(len(x), len(y)) >= 4 and (y.startswith(x) or x.startswith(y))):
            hits += 1
    return hits == 2


# ------------------------------------------------------- network: KUForest ---

KU_PAT = re.compile(r"research\.ku\.ac\.th/(?:\w+/)?Person\.aspx\?(?:pid|id)=(\d+)", re.I)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _opener(jar):
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=CTX),
        urllib.request.HTTPCookieProcessor(jar))


def kuforest_english(pid, jar=None):
    """Return 'First Last' as rendered by KUForest in English mode, or None.

    The site is ASP.NET WebForms; the language link is a __postback that flips a
    session cookie. Once flipped, plain GETs render English.
    """
    import http.cookiejar
    jar = jar or http.cookiejar.CookieJar()
    op = _opener(jar)
    base = f"https://research.ku.ac.th/forest/Person.aspx?id={pid}"
    for attempt in range(3):
        try:
            html = op.open(base, timeout=40).read().decode("utf-8", "replace")
            t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
            title = unescape(t.group(1)).strip() if t else ""
            if title and not THAI.search(title.split(" - KUforest")[0]):
                name = re.split(r"\s*[-|–]\s*", title)[0].strip()
                name = re.sub(r"^(Assoc\.?|Asst\.?|Prof\.?|Dr\.?|Mr\.?|Ms\.?|Mrs\.?)[\s.]+", "", name, flags=re.I)
                toks = [w for w in name.split() if NAME_TOKEN.match(w)]
                if len(toks) >= 2:
                    return " ".join(toks)
            # flip language via postback
            vs = re.search(r'id="__VIEWSTATE" value="([^"]*)"', html)
            vg = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]*)"', html)
            ev = re.search(r'id="__EVENTVALIDATION" value="([^"]*)"', html)
            if not vs:
                return None
            body = {
                "__VIEWSTATE": vs.group(1),
                "__VIEWSTATEGENERATOR": vg.group(1) if vg else "",
                "__EVENTVALIDATION": ev.group(1) if ev else "",
                "ctl00$LanguageLinkButton": "English",
            }
            req = urllib.request.Request(
                base, data=urllib.parse.urlencode(body).encode(),
                headers={"User-Agent": UA,
                         "Content-Type": "application/x-www-form-urlencoded"})
            html2 = op.open(req, timeout=40).read().decode("utf-8", "replace")
            t = re.search(r"<title[^>]*>(.*?)</title>", html2, re.S | re.I)
            title = unescape(t.group(1)).strip() if t else ""
            name = re.split(r"\s*[-|–]\s*", title)[0].strip()
            if not name or THAI.search(name):
                return None
            name = re.sub(r"^(Assoc\.?|Asst\.?|Prof\.?|Dr\.?|Mr\.?|Ms\.?|Mrs\.?)[\s.]+", "", name, flags=re.I)
            toks = [w for w in name.split() if NAME_TOKEN.match(w)]
            return " ".join(toks) if len(toks) >= 2 else None
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return None


PSY_PAT = re.compile(r"psy\.chula\.ac\.th/(?:en|th)/people/([\w\-]+)/?$", re.I)


def fetch_text(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            time.sleep(1.0 * (attempt + 1))
    return None


def psy_english(url):
    m = PSY_PAT.search(url or "")
    if not m:
        return None
    en_url = f"https://www.psy.chula.ac.th/en/people/{m.group(1)}/"
    html = fetch_text(en_url, timeout=30)
    if not html:
        return None
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    if not h1:
        return None
    name = re.sub(r"<[^>]+>", " ", h1.group(1))
    name = unescape(re.sub(r"\s+", " ", name)).strip()
    toks = [w for w in name.split() if NAME_TOKEN.match(w)]
    return " ".join(toks) if len(toks) >= 2 and not THAI.search(name) else None


def harvest_network(rows_by_id, report):
    """T5 + T6 — resumable; results checkpointed as pid->Name."""
    os.makedirs(STATE_DIR, exist_ok=True)
    ku_done = {}
    if os.path.exists(KU_PATH):
        ku_done = json.load(open(KU_PATH, encoding="utf-8"))

    ku_tasks, psy_tasks = [], []
    for rid, r in rows_by_id.items():
        url = r[1] if isinstance(r, tuple) else (r.profile_url or "")
        m = KU_PAT.search(url or "")
        if m and m.group(1) not in ku_done:
            ku_tasks.append((rid, m.group(1)))
        elif PSY_PAT.search(url or ""):
            psy_tasks.append((rid, url))

    report.append(f"network: KU pending pids={len(set(p for _, p in ku_tasks))} (cached {len(ku_done)}), psy pages={len(psy_tasks)}")
    done = [0]

    def ku_worker(item):
        rid, pid = item
        name = kuforest_english(pid)
        return pid, name

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(ku_worker, it) for it in sorted(set(ku_tasks), key=lambda x: x[1])]
        for fut in as_completed(futs):
            pid, name = fut.result()
            ku_done[pid] = name or ""
            done[0] += 1
            if done[0] % 100 == 0:
                json.dump(ku_done, open(KU_PATH, "w", encoding="utf-8"))
                el = time.time() - t0
                report.append(f"  KU {done[0]}/{len(futs)} ok={sum(1 for v in ku_done.values() if v)} {el/60:.1f}m")
    json.dump(ku_done, open(KU_PATH, "w", encoding="utf-8"))

    psy_done = {}
    for rid, url in psy_tasks:
        m = PSY_PAT.search(url)
        key = m.group(1)
        if key in psy_done:
            continue
        psy_done[key] = psy_english(url) or ""
    return ku_done, psy_done


# ------------------------------------------------------------------ main ---

def build_candidates():
    """Rebuild the local-tier candidate map from scratch (deterministic, offline).

    T5/T6 results are merged back in afterwards from KU_PATH if present.
    """
    db = SessionLocal()
    rows = db.query(FacultyDB).filter(
        or_(FacultyDB.openalex_id.is_(None), FacultyDB.openalex_id == "")
    ).all()
    cands = {}
    if os.path.exists(CAND_PATH):
        try:
            old = json.load(open(CAND_PATH, encoding="utf-8"))
            cands = {k: v for k, v in old.items()
                     if isinstance(v, dict) and "tiers" in v and "en" in v}
        except Exception:  # noqa: BLE001
            cands = {}
    report = []
    tiers_count = Counter()
    for r in rows:
        p1, cleaned = t1_from_full_name(r.full_name_th)
        p2 = t2_from_email(r.email or "")
        p3 = t3_from_url(r.profile_url or "")
        p4 = None
        if r.first_name and r.last_name and not THAI.search(r.first_name + r.last_name) \
                and len(r.last_name) >= 3:
            p4 = (r.first_name.strip(), r.last_name.strip())
        got = {}
        for k, v in (("T1", p1), ("T2", p2), ("T3", p3), ("T4", p4)):
            if v and valid_pair(v):
                got[k] = v
        # carry over harvested T5/T6 from a previous --network run
        prev = cands.get(r.id) or {}
        for k in ("T5", "T6"):
            if prev.get("tiers", {}).get(k):
                got[k] = tuple(prev["tiers"][k])
        if got:
            vals = list(got.values())
            conf = "high" if (any(a == b or agree(a, b)
                                  for i, a in enumerate(vals) for b in vals[i + 1:])
                              or "T5" in got or "T6" in got) else "medium"
            # authoritative tier wins (T5/T6 = page's own English rendering)
            pick = next((k for k in ("T5", "T6", "T1", "T4", "T3", "T2") if k in got))
            cands[r.id] = {
                "en": got[pick], "conf": conf, "tiers": got,
                "th_ok": bool(THAI.search((r.first_name or "") + (r.last_name or ""))),
            }
            for k in got:
                tiers_count[k] += 1
    db.close()
    report.append(f"tiers: {dict(tiers_count)} | candidates={len(cands)}")
    return cands, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cands, report = build_candidates()

    if args.network:
        db = SessionLocal()
        # column-only load: skip the 768-dim embedding vector for 6.7k rows
        missing = {r[0]: r for r in db.query(
            FacultyDB.id, FacultyDB.profile_url, FacultyDB.full_name_th).filter(
            or_(FacultyDB.openalex_id.is_(None), FacultyDB.openalex_id == "")).all()
            if r[0] not in cands or cands[r[0]]["conf"] == "medium"}
        db.close()
        ku_map, psy_map = harvest_network(missing, report)
        # fold T5/T6 in
        n5 = n6 = 0
        for rid, r in missing.items():
            m = KU_PAT.search(r[1] or "")
            if m and ku_map.get(m.group(1)):
                name = ku_map[m.group(1)]
                toks = name.split()
                pair = (toks[0], " ".join(toks[1:]))
                if valid_pair(pair):
                    c = cands.setdefault(rid, {"tiers": {}, "conf": "medium", "th_ok": True})
                    c["tiers"]["T5"] = pair
                    if "T1" not in c["tiers"] and "T4" not in c["tiers"]:
                        c["en"] = pair
                    vals = list(c["tiers"].values())
                    if any(a == b for i, a in enumerate(vals) for b in vals[i + 1:]) or len(vals) > 1:
                        c["conf"] = "high"
                    n5 += 1
            pm = PSY_PAT.search(r[1] or "")
            if pm and psy_map.get(pm.group(1)):
                toks = psy_map[pm.group(1)].split()
                pair = (toks[0], " ".join(toks[1:]))
                if valid_pair(pair):
                    c = cands.setdefault(rid, {"tiers": {}, "conf": "medium", "th_ok": True})
                    c["tiers"]["T6"] = pair
                    if "T1" not in c["tiers"]:
                        c["en"] = pair
                    c["conf"] = "high"
                    n6 += 1
        db.close()
        report.append(f"T5 KUForest names applied={n5}  T6 psy applied={n6}")

    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(cands, open(CAND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    conf = Counter(c["conf"] for c in cands.values())
    report.append(f"checkpoint: {len(cands)} candidates {dict(conf)}")

    if args.apply:
        db = SessionLocal()
        journal = json.load(open(APPLY_PATH, encoding="utf-8")) if os.path.exists(APPLY_PATH) else []
        journalled = {j["id"] for j in journal}
        n_first = n_clean = 0
        todo = [i for i in cands if cands[i]["conf"] in ("high", "medium")]
        if args.limit:
            todo = todo[: args.limit]

        def note_prev(rid, r):
            if rid not in journalled:
                journal.append({"id": rid, "first_name": r.first_name,
                                "last_name": r.last_name, "full_name_th": r.full_name_th})
                journalled.add(rid)

        for i, rid in enumerate(todo):
            r = db.query(FacultyDB).filter(FacultyDB.id == rid).first()
            if not r:
                continue
            c = cands[rid]
            first, last = c["en"]
            th_cur = (r.first_name or "") + (r.last_name or "")
            if (not th_cur.strip()) or THAI.search(th_cur):
                if (r.first_name, r.last_name) != (first, last):
                    note_prev(rid, r)
                    r.first_name, r.last_name = first, last
                    n_first += 1
            # Clean a glued Latin tail out of full_name_th, but ONLY when the tail
            # agrees with this person's own romanization — otherwise leave it
            # (it may be a genuinely-needed foreign name, e.g. "James Michael Brimson").
            m_tail = re.search(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ.,'&\- ]{4,}$", unquote(r.full_name_th or ""))
            if m_tail and THAI.search(r.full_name_th or ""):
                tail_words = latin_words(m_tail.group(0))
                en_join = norm(" ".join(c["en"]))
                tail_join = norm(" ".join(tail_words))
                agrees = bool(tail_join) and (tail_join in en_join or en_join in tail_join
                                              or norm(tail_words[-1]) in en_join)
                cleaned = r.full_name_th[:m_tail.start()].strip(" -–|/")
                if agrees and cleaned and cleaned != r.full_name_th:
                    note_prev(rid, r)
                    r.full_name_th = cleaned
                    n_clean += 1
            if (i + 1) % 500 == 0:
                db.commit()
                json.dump(journal, open(APPLY_PATH, "w", encoding="utf-8"), ensure_ascii=False)
                report.append(f"  applied {i+1}/{len(todo)}")
        db.commit()
        json.dump(journal, open(APPLY_PATH, "w", encoding="utf-8"), ensure_ascii=False)
        db.close()
        report.append(f"APPLY: names written={n_first}, full_name_th cleaned={n_clean}, journal={len(journal)}")

    with open(r"C:\Users\chaya\AppData\Local\Temp\w20_resolver.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(str(x) for x in report) + "\n")
    print("\n".join(str(x).encode("ascii", "replace").decode() for x in report[-8:]))
    print("report -> C:/Users/chaya/AppData/Local/Temp/w20_resolver.txt")


if __name__ == "__main__":
    main()
