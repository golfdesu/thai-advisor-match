"""Wave 20 recon #3 — quantify the FREE local tiers before touching the network.

Tiers (all derived from data already in Postgres, zero egress):
  T1  trailing Latin name glued inside full_name_th   ("กฤษฎา สังขนันท์Assoc. Prof. Dr. Krisada ...")
  T2  email local part as first.last                  ("anusorn.lungka@cmu.ac.th")
  T3  person-slug URL                                 ("/teams/kanoknadda-tavedhikul/")
  T4  first_name/last_name already Latin (just never probed / too short surname)

Confidence = how many independent tiers agree on the same (first, last).
Writes a report + a candidate JSON checkpoint under data/agent_states/.
"""

import json
import re
import sys
from collections import Counter
from urllib.parse import unquote, urlparse

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

OUT = r"C:\Users\chaya\AppData\Local\Temp\w20_tiers.txt"
CKPT = "data/agent_states/wave20_enames_candidates.json"

THAI = re.compile(r"[\u0E00-\u0E7F]")
RANK_EN = re.compile(
    r"\b(ass(?:ociate)?\.?|asst\.?|prof\.?|dr\.?|mr\.?|ms\.?|mrs\.?|assoc\.?|"
    r"lecturer|instructor|researcher|emeritus|adjunct)\b", re.I)
PHONE_NOISE = re.compile(r"\+?\d[\d\s\-\.]{5,}")
EMAIL_LOCAL = re.compile(r"^([a-z]{2,}[._][a-z]{2,})(?:\d+)?@", re.I)
STOPWORDS = {"publications", "publication", "email", "tel", "fax", "position",
             "department", "faculty", "university", "research", "interest",
             "profile", "homepage", "google", "scholar", "scopus", "detail",
             "uri", "index", "personnel", "teacher", "faculty", "member",
             "members", "directory", "academic", "staff", "people", "personal",
             "search", "head", "of", "the", "and", "office", "administration"}


def clean_latin(s):
    s = PHONE_NOISE.sub(" ", s)
    s = re.sub(r"[email|tel|fax|@]+\s*[:\-]", " ", s, flags=re.I)
    s = re.sub(r"[<>\"'()/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.-:")
    return s


def name_from_latin_blob(blob):
    """('Assoc. Prof. Dr. Krisada Sangkhanan', ...) -> ('Krisada','Sangkhanan')"""
    blob = clean_latin(blob)
    blob = re.sub(r"^(Faculty|School|Department|Program)\b.*$", "", blob)
    toks = [t for t in blob.split(" ") if t]
    # drop leading abbreviations / rank words / initials
    while toks and (RANK_EN.match(toks[0]) or len(toks[0]) <= 2 or toks[0].lower() in STOPWORDS):
        toks.pop(0)
    # trailing noise words (Publication, Email, ...) and initials
    toks = [t for t in toks if t.lower().strip(".") not in STOPWORDS]
    toks = [t for t in toks if not re.match(r"^[A-Z]\.$", t)]
    if len(toks) < 2:
        return None
    first, last = toks[0], toks[-1]
    if len(last) < 3 or len(first) < 2 or THAI.search(first + last):
        return None
    # must look like a name: mostly letters
    if not re.match(r"^[A-Za-zÀ-ɏ'\-]+$", first) or not re.match(r"^[A-Za-zÀ-ɏ'\-]+$", last):
        return None
    return first, " ".join(toks[1:]) if len(toks) > 2 else last


def t1_from_full_name(full_name_th):
    """Split Thai prefix from glued Latin suffix, keep the Latin person name."""
    if not full_name_th:
        return None
    # Latin runs anywhere in the string; take the longest run that has >=2 words
    runs = re.findall(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ.'\- ]{4,}", unquote(full_name_th))
    best = None
    for r in runs:
        r = r.strip()
        if PHONE_NOISE.search(r):
            # keep the part after the phone digits — emails/initials often follow
            r = clean_latin(r)
        words = [w for w in r.split() if len(w) >= 2]
        if len(words) < 2:
            continue
        score = len(words)
        if best is None or score > best[0]:
            best = (score, r)
    if not best:
        return None
    return name_from_latin_blob(best[1])


def t2_from_email(email):
    if not email or "@" not in email:
        return None
    m = EMAIL_LOCAL.match(email.strip())
    if not m:
        return None
    parts = re.split(r"[._\-]", m.group(1))
    parts = [p for p in parts if len(p) >= 2]
    if len(parts) < 2:
        return None
    first, last = parts[0].title(), " ".join(parts[1:]).title()
    if len(last.replace(" ", "")) < 3:
        return None
    return first, last


PERSON_SLUG_HOSTS = re.compile(
    r"(dent\.chula\.ac\.th|psy\.chula\.ac\.th|ahs\.chula\.ac\.th|tbs\.tu\.ac\.th|"
    r"law\.tu\.ac\.th|eng\.buu\.ac\.th|kmutt\.ac\.th|su\.ac\.th|ssru\.ac\.th|"
    r"fish\.ku\.ac\.th|msu\.ac\.th|psu\.ac\.th|kku\.ac\.th|cmu\.ac\.th|web\.pu\.ac\.th)", re.I)


def t3_from_slug(url):
    if not url or THAI.search(url):
        return None
    host = urlparse(url).netloc.lower()
    if not PERSON_SLUG_HOSTS.search(host):
        return None
    seg = unquote(urlparse(url).path).rstrip("/").rsplit("/", 1)[-1]
    if not seg or "." in seg:          # person.aspx / teacher.php are NOT people
        return None
    seg = re.sub(r"\d+$", "", seg)
    seg = re.sub(r"^(dr|prof|assoc|asst)[\-.]+", "", seg, flags=re.I)
    parts = [p for p in re.split(r"[-_.]", seg) if len(p) >= 2]
    if len(parts) < 2:
        return None
    parts = [p for p in parts if p.lower() not in STOPWORDS]
    if len(parts) < 2:
        return None
    first = parts[0].title()
    last = " ".join(parts[1:]).title()
    if len(last.replace(" ", "")) < 4:  # slug surnames are long; short = page word
        return None
    return first, last


def norm(p):
    if not p:
        return None
    return (re.sub(r"\s+", " ", p[0]).lower().strip(), re.sub(r"\s+", " ", p[1]).lower().strip())


def main():
    db = SessionLocal()
    rows = db.query(
        FacultyDB.id, FacultyDB.university, FacultyDB.full_name_th,
        FacultyDB.first_name, FacultyDB.last_name, FacultyDB.email,
        FacultyDB.profile_url, FacultyDB.openalex_id, FacultyDB.h_index,
    ).filter(FacultyDB.openalex_id.is_(None)).all()
    db.close()

    report = [f"NULL-openalex rows = {len(rows)}"]
    tiers = Counter()
    combo = Counter()
    cands = {}
    for rid, uni, fth, fn, ln, email, purl, oid, h in rows:
        t1 = t1_from_full_name(fth)
        t2 = t2_from_email(email)
        t3 = t3_from_slug(purl)
        t4 = None
        if fn and ln and not THAI.search(fn) and not THAI.search(ln) and len(ln) >= 3:
            t4 = (fn.strip(), ln.strip())
        hits = {"T1_fullname_latin": t1, "T2_email": t2, "T3_slug": t3, "T4_existing": t4}
        got = {k: v for k, v in hits.items() if v}
        for k in got:
            tiers[k] += 1
        combo[tuple(sorted(got))] += 1
        if not got:
            continue
        # agreement
        normed = {k: norm(v) for k, v in got.items()}
        agree = sum(1 for a in normed.values() for b in normed.values() if a == b) // 2
        # pick the most trusted tier: T1 (institution's own romanization) > T4 > T2 > T3
        pick_key = next((k for k in ("T1_fullname_latin", "T4_existing", "T2_email", "T3_slug") if k in got), None)
        cands[rid] = {
            "university": uni, "full_name_th": fth, "email": email,
            "profile_url": purl, "chosen": pick_key, "english": got[pick_key],
            "tiers": {k: v for k, v in got.items()}, "agreement": agree,
        }

    report.append("\n--- per-tier availability ---")
    for k, v in tiers.most_common():
        report.append(f"  {k}: {v}")
    report.append(f"\n--- tier combinations (top 20) ---")
    for k, v in combo.most_common(20):
        report.append(f"  {'+'.join(k) or 'NONE'}: {v}")
    multi = [c for c in cands.values() if c["agreement"] >= 1]
    report.append(f"\ncandidates total = {len(cands)}; with >=2 tiers agreeing = {len(multi)}")
    report.append("\n--- 25 samples per chosen tier ---")
    by_pick = {}
    for rid, c in cands.items():
        by_pick.setdefault(c["chosen"], []).append((rid, c))
    for pick, lst in sorted(by_pick.items()):
        report.append(f"\n  ### {pick} ({len(lst)})")
        for rid, c in lst[:25]:
            report.append(f"    {rid} | {str(c['full_name_th'])[:34]!r} -> {c['english']!r} | email={c['email']}")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(str(x) for x in report) + "\n")

    import os
    os.makedirs("data/agent_states", exist_ok=True)
    with open(CKPT, "w", encoding="utf-8") as fh:
        json.dump(cands, fh, ensure_ascii=False, indent=1)
    print("wrote", OUT, "and", CKPT, len(cands))


if __name__ == "__main__":
    main()
