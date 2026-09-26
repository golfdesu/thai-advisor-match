# -*- coding: utf-8 -*-
"""
Remediate faculty rows whose openalex_id is stored in the bare 'A5...' form (2026-09-26 audit).

Each bare ID is re-verified two-factor against the live OpenAlex author record:
  1. Affiliation — one of the author's institutions fuzzy-matches the row's university.
  2. Name       — the author's display name matches the row's English name AND the
                  Thai name's initial consonants are compatible with the English name
                  (catches first-name-only matches like 'ราณี ซิงห์' ↔ 'Ranee Sangsuwan').

Actions:
  NORMALIZE  verified, no other row holds the ID     → prefix https://openalex.org/
  MERGE      verified, same-university row holds the canonical ID and is the same person
             → merge into the canonical row (max metrics, union lists, re-point labs), delete bare row
  RESET      not verified → openalex_id NULL, metrics 0, featured_publications [] (they belong to
             another person); mismatched English surname cleared; embedding rebuilt
  REVIEW     verified but the canonical ID is held by a different-university row → left untouched

Usage (local Docker DB only — never Supabase):
    python scripts/audits/remediate_bare_openalex_ids.py            # dry-run, writes plan JSON
    python scripts/audits/remediate_bare_openalex_ids.py --apply
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras
from rapidfuzz import fuzz

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parent))
from fetch_openalex_publication_metrics import fetch_with_retry  # noqa: E402

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/advisor_match")
STATE_DIR = Path(os.getenv("AGENT_STATE_DIR", SCRIPTS_DIR.parent / "data" / "agent_states"))
PLAN_FILE = STATE_DIR / "remediate_bare_openalex_plan_2026-09-26.json"
OA_PREFIX = "https://openalex.org/"

UNIV_EN_FALLBACK = {
    "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี": "Rajamangala University of Technology Thanyaburi",
}

# Thai initial consonant → acceptable first Latin letters (RTGS + common personal spellings)
THAI_INITIAL = {
    **dict.fromkeys("กฃ", "kg"), **dict.fromkeys("ขคฅฆ", "kc"), "ง": "n",
    "จ": "cj", **dict.fromkeys("ฉชฌ", "c"), **dict.fromkeys("ซศษส", "sc"),
    "ญ": "yn", **dict.fromkeys("ฎด", "d"), **dict.fromkeys("ฏต", "td"),
    **dict.fromkeys("ฐฑฒถทธ", "td"), **dict.fromkeys("ณน", "n"), "บ": "bp", "ป": "pb",
    **dict.fromkeys("ผพภ", "pb"), **dict.fromkeys("ฝฟ", "fp"), "ม": "m", "ย": "yj",
    "ร": "rl", **dict.fromkeys("ลฬ", "lr"), "ว": "wv", **dict.fromkeys("หฮ", "h"),
    "อ": "aeiou", "ฤ": "r",
}
LEADING_VOWELS = "เแโใไ"
TITLE_TOKEN_RE = re.compile(
    r"^(?:[ก-๙A-Za-z]{1,6}\.)+$"
    r"|^(?:ศาสตราจารย์|รองศาสตราจารย์|รองศาตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|เกียรติคุณ|นาย|นางสาว|นาง)$")
GLUED_TITLE_RE = re.compile(r"^(?:นางสาว|นาย|นาง)(?=[ก-๙]{2,})")
THAI_RE = re.compile(r"[ก-๙]")


def thai_initials(word: str) -> str | None:
    w = word.lstrip(LEADING_VOWELS)
    if not w:
        return None
    # silent leading ห before sonorants (หน, หม, หล, หว, หย, หง, หร)
    if w[0] == "ห" and len(w) > 1 and w[1] in "นมลวยงรญ":
        w = w[1:]
    return THAI_INITIAL.get(w[0])


def split_thai_name(full_name_th: str) -> tuple[str, str]:
    tokens = [t for t in re.split(r"\s+", (full_name_th or "").strip()) if t]
    while tokens:
        if TITLE_TOKEN_RE.match(tokens[0]):
            tokens.pop(0)
            continue
        # a title glued to the next token, e.g. "อ.ดร.ราณี" or "ศ.เกียรติคุณ"
        stripped = re.sub(r"^(?:[ก-๙]{1,5}\.)+", "", tokens[0])
        # "นายชาคริต" — only when a surname follows, so a given name like "นางนวล" survives
        if len(tokens) > 1:
            stripped = GLUED_TITLE_RE.sub("", stripped)
        if stripped == tokens[0]:
            break
        tokens[0] = stripped
        if not stripped:
            tokens.pop(0)
    if not tokens:
        return "", ""
    return tokens[0], " ".join(tokens[1:])


def initial_ok(thai_word: str, latin_word: str) -> bool:
    if not thai_word or not latin_word:
        return False
    allowed = thai_initials(thai_word)
    return bool(allowed) and latin_word.strip()[0].lower() in allowed


def _truncated_match(en: str, names: list[str]) -> bool:
    """Long Thai surnames are sometimes stored cut off ('Shinlap' for 'Shinlapawittayatorn')."""
    en_tokens = en.lower().split()
    if len(en_tokens) < 2:
        return False
    for n in names:
        oa_tokens = (n or "").lower().split()
        if len(oa_tokens) == len(en_tokens) and all(
                o.startswith(e) and len(e) >= 4 for e, o in zip(en_tokens, oa_tokens)):
            return True
    return False


def name_verified(row, author) -> tuple[bool, str]:
    en = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip()
    names = [author.get("display_name") or ""] + (author.get("display_name_alternatives") or [])
    th_first, th_last = split_thai_name(row["full_name_th"])
    th_full = f"{th_first} {th_last}".strip()
    # OpenAlex sometimes carries a Thai display name, or "ไทย (Latin)" — compare against
    # both the English and the Thai name; token_set tolerates the parenthesised extra.
    oa_score = max((max(fuzz.token_sort_ratio(en.lower(), n.lower()),
                        fuzz.token_set_ratio(en.lower(), n.lower()) if en else 0,
                        fuzz.token_set_ratio(th_full, n) if THAI_RE.search(n) else 0)
                    for n in names if n), default=0)
    if oa_score < 85 and not _truncated_match(en, names):
        return False, f"EN name vs OpenAlex {oa_score:.0f}"
    if not THAI_RE.search(th_first + th_last):
        # full_name_th holds a Latin name (kmutt_sbt legacy) — compare it directly
        s = fuzz.token_sort_ratio(f"{th_first} {th_last}".lower(), en.lower())
        return s >= 85, f"latin full_name_th vs EN {s:.0f}"
    if not initial_ok(th_first, row["first_name"] or ""):
        return False, "Thai/EN first-name initial mismatch"
    if th_last and not initial_ok(th_last, row["last_name"] or ""):
        return False, "Thai/EN surname initial mismatch"
    return True, "ok"


def affiliation_verified(row, author) -> tuple[bool, str]:
    univ_en = row["university"] or UNIV_EN_FALLBACK.get(row["university_th"], "")
    if not univ_en:
        return False, "no English university name"
    insts = [i.get("display_name") or "" for i in (author.get("last_known_institutions") or [])]
    insts += [(a.get("institution") or {}).get("display_name") or "" for a in (author.get("affiliations") or [])]
    best = max((fuzz.token_set_ratio(univ_en.lower(), i.lower()) for i in insts if i), default=0)
    return best >= 90, f"affiliation {best:.0f}"


def fetch_authors(ids: list[str]) -> dict[str, dict]:
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        url = ("https://api.openalex.org/authors?per-page=50&filter=openalex:" + "|".join(chunk) +
               "&select=id,display_name,display_name_alternatives,affiliations,last_known_institutions")
        for a in (fetch_with_retry(url) or {}).get("results", []):
            out[a["id"].rsplit("/", 1)[-1]] = a
    return out


def same_person(a, b) -> bool:
    ta, tb = " ".join(split_thai_name(a["full_name_th"])), " ".join(split_thai_name(b["full_name_th"]))
    ea = f"{a['first_name'] or ''} {a['last_name'] or ''}".lower()
    eb = f"{b['first_name'] or ''} {b['last_name'] or ''}".lower()
    return fuzz.token_sort_ratio(ta, tb) >= 80 or fuzz.token_sort_ratio(ea, eb) >= 90


COLS = """id, university, university_th, faculty_th, full_name_th, first_name, last_name, openalex_id,
          email, image_url, profile_url, scholar_url, role, department, department_th,
          research_interests, featured_publications, education, taught_courses,
          total_citations, h_index, total_publications_count, first_author_count, co_author_count,
          embedding IS NOT NULL AS has_emb"""


def build_plan(cur):
    cur.execute(f"SELECT {COLS} FROM faculties WHERE openalex_id ~ '^A[0-9]+$' ORDER BY id")
    bare = cur.fetchall()
    cur.execute(f"SELECT {COLS} FROM faculties WHERE openalex_id = ANY(%s)",
                ([OA_PREFIX + r["openalex_id"] for r in bare],))
    holders = {}
    for r in cur.fetchall():
        holders.setdefault(r["openalex_id"].rsplit("/", 1)[-1], []).append(r)

    authors = fetch_authors(sorted({r["openalex_id"] for r in bare}))
    print(f"bare rows: {len(bare)} | OpenAlex authors fetched: {len(authors)}")
    if len(authors) < len({r['openalex_id'] for r in bare}) * 0.9:
        sys.exit("OpenAlex fetch incomplete (quota/network) — aborting without changes.")

    plan = []
    for r in bare:
        author = authors.get(r["openalex_id"])
        if not author:
            plan.append({"action": "RESET", "id": r["id"], "reason": "author not found in OpenAlex",
                         "clear_last_name": False})
            continue
        n_ok, n_why = name_verified(r, author)
        a_ok, a_why = affiliation_verified(r, author)
        entry = {"id": r["id"], "oa": r["openalex_id"], "oa_name": author.get("display_name"),
                 "full_name_th": r["full_name_th"], "en": f"{r['first_name']} {r['last_name']}",
                 "reason": f"{n_why}; {a_why}"}
        if not (n_ok and a_ok):
            th_first, th_last = split_thai_name(r["full_name_th"])
            entry["action"] = "RESET"
            entry["clear_last_name"] = bool(THAI_RE.search(th_last)) and not initial_ok(th_last, r["last_name"] or "")
            plan.append(entry)
            continue
        partners = holders.get(r["openalex_id"], [])
        if not partners:
            entry["action"] = "NORMALIZE"
        elif all(p["university_th"] == r["university_th"] and same_person(p, r) for p in partners):
            entry["action"] = "MERGE"
            entry["keep"] = sorted(partners, key=lambda p: p["id"])[0]["id"]
        else:
            entry["action"] = "REVIEW"
            entry["holders"] = [f"{p['id']} ({p['university_th']})" for p in partners]
        plan.append(entry)
    return plan, {r["id"]: r for r in bare}, {p["id"]: p for ps in holders.values() for p in ps}


def merge_lists(*values):
    out, seen = [], set()
    for v in values:
        for item in (v or []):
            key = (item.get("title") if isinstance(item, dict) else str(item)) or json.dumps(item, sort_keys=True)
            key = str(key).strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(item)
    return out


def apply_plan(cur, plan, bare_rows, holder_rows) -> list[str]:
    reembed = []
    for e in plan:
        rid, act = e["id"], e["action"]
        if act == "NORMALIZE":
            cur.execute("UPDATE faculties SET openalex_id = %s WHERE id = %s", (OA_PREFIX + e["oa"], rid))
        elif act == "RESET":
            cur.execute("""UPDATE faculties SET openalex_id = NULL, total_citations = 0, h_index = 0,
                           total_publications_count = 0, first_author_count = 0, co_author_count = 0,
                           featured_publications = '[]'::json
                           WHERE id = %s""", (rid,))
            if e.get("clear_last_name"):
                cur.execute("UPDATE faculties SET last_name = NULL WHERE id = %s", (rid,))
            reembed.append(rid)
        elif act == "MERGE":
            d, k = bare_rows[rid], holder_rows[e["keep"]]
            sets, params = [], []
            for f in ("research_interests", "featured_publications", "education", "taught_courses"):
                sets.append(f"{f} = %s::json")
                params.append(json.dumps(merge_lists(k[f], d[f]), ensure_ascii=False))
            for f in ("total_citations", "h_index", "total_publications_count", "first_author_count", "co_author_count"):
                sets.append(f"{f} = %s")
                params.append(max(k[f] or 0, d[f] or 0))
            for f in ("email", "image_url", "profile_url", "scholar_url", "role", "department", "department_th"):
                if not k[f] and d[f]:
                    sets.append(f"{f} = %s")
                    params.append(d[f])
            if not k["has_emb"] and d["has_emb"]:
                sets.append("embedding = (SELECT embedding FROM faculties WHERE id = %s)")
                params.append(rid)
            params.append(k["id"])
            cur.execute(f"UPDATE faculties SET {', '.join(sets)} WHERE id = %s", params)
            cur.execute("UPDATE research_labs SET lead_advisor_id = %s WHERE lead_advisor_id = %s", (k["id"], rid))
            cur.execute("""
                UPDATE research_labs SET member_faculty_ids = (
                    SELECT coalesce(jsonb_agg(DISTINCT CASE WHEN x = %s THEN %s ELSE x END), '[]'::jsonb)
                    FROM jsonb_array_elements_text(member_faculty_ids::jsonb) AS t(x))
                WHERE member_faculty_ids::jsonb ? %s""", (rid, k["id"], rid))
            cur.execute("DELETE FROM faculties WHERE id = %s", (rid,))
            reembed.append(k["id"])
    return reembed


def rebuild_embeddings(ids: list[str]) -> tuple[int, int]:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from app.core.embedding_service import embedding_service
    from faculty_massive_ingestion_runner import build_faculty_embedding_text

    ok = fail = 0
    db = SessionLocal()
    try:
        for rid in ids:
            obj = db.get(FacultyDB, rid)
            if obj is None:
                continue
            obj.embedding_text = build_faculty_embedding_text(obj)
            try:
                vec = embedding_service.get_embedding(obj.embedding_text)
            except Exception:
                vec = None
            if vec:
                obj.embedding = vec
                ok += 1
            else:
                fail += 1  # keeps previous embedding; logged for backfill
            db.commit()
    finally:
        db.close()
    return ok, fail


def main(apply: bool) -> None:
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    plan, bare_rows, holder_rows = build_plan(cur)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    counts = {}
    for e in plan:
        counts[e["action"]] = counts.get(e["action"], 0) + 1
    print(f"plan: {counts} → {PLAN_FILE.name}")

    if not apply:
        print("DRY-RUN only — re-run with --apply to execute.")
        return
    reembed = apply_plan(cur, plan, bare_rows, holder_rows)
    conn.commit()
    cur.close(); conn.close()
    print(f"APPLIED. rebuilding {len(reembed)} embeddings...")
    ok, fail = rebuild_embeddings(reembed)
    print(f"embeddings rebuilt ok={ok} failed={fail}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Verify & remediate bare-form OpenAlex IDs")
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
