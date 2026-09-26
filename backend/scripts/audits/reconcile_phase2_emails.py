# -*- coding: utf-8 -*-
"""
Phase 2 — write recovered emails from SKILL.state exports into faculties.email (2026-09-26).

Only fills rows whose email is empty; never overwrites. Guards (AGENTS.md §7, §9.9, §9.10):
  • email must pass the strict TLD regex and belong to an institutional domain (.ac.th / .edu)
  • shared / departmental inboxes are rejected (generic local parts, or an address that appears
    on more than one extracted person)
  • an email already held by another faculty row is never assigned
  • match to a DB row within the same university by exact normalized Thai name, else exact
    English name; RapidFuzz token_sort_ratio >= 92 on the Thai name only when exactly one row passes
  • no new rows are inserted here (Phase 3 handles new rosters)

Usage (local DB only):
    python scripts/audits/reconcile_phase2_emails.py --prefix swu_            # dry-run
    python scripts/audits/reconcile_phase2_emails.py --prefix swu_ --apply
"""
import os
import re
import sys
import json
import argparse
import importlib.util
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remediate_bare_openalex_ids import split_thai_name  # noqa: E402

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/advisor_match")
PHASE2_DIR = Path(os.getenv("AGENT_STATE_DIR", Path(__file__).resolve().parents[2] / "data" / "agent_states")) / "phase2"

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
INSTITUTIONAL_RE = re.compile(r"(\.ac\.th|\.edu(\.[a-z]{2})?)$", re.I)
GENERIC_LOCAL_RE = re.compile(
    r"^(info|admin|office|contact|webmaster|pr|hr|dean|secretary|faculty|dept|department|library|"
    r"service|support|saraban|registrar|student|grad|graduate|academic|research|inter|international|"
    r"[a-z]{2,6}(dept|office|fac|sci|eng|med|dent|nurse|edu))$", re.I)


def load_export(path: Path) -> list[dict]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "EXTRACTED_FACULTIES", [])


def norm_th(name: str) -> str:
    first, last = split_thai_name(name or "")
    return f"{first} {last}".strip()


def norm_en(first: str, last: str) -> str:
    return re.sub(r"[^a-z ]", "", f"{first or ''} {last or ''}".lower()).strip()


def main(prefix: str, apply: bool) -> None:
    records = []
    for p in sorted(PHASE2_DIR.glob(f"{prefix}*.py")):
        records += load_export(p)

    # emails seen on more than one distinct person are shared inboxes
    owners = {}
    for r in records:
        em = (r.get("email") or "").strip().lower()
        if em:
            owners.setdefault(em, set()).add(norm_th(r.get("full_name_th")) or norm_en(r.get("first_name"), r.get("last_name")))
    shared = {em for em, who in owners.items() if len(who) > 1}

    conn = psycopg2.connect(DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT lower(email) e FROM faculties WHERE coalesce(email,'') <> ''")
    taken = {r["e"] for r in cur.fetchall()}

    univs = sorted({r.get("university_th") for r in records if r.get("university_th")})
    # the email's base domain must be one the university already uses (>= 5 rows) — rejects
    # addresses from a mislabeled page of another university (e.g. sut.ac.th under SWU)
    cur.execute(r"""SELECT university_th, substring(lower(email) from '([a-z0-9-]+\.(?:ac\.th|edu))$') d
                    FROM faculties WHERE university_th = ANY(%s) AND email LIKE '%%@%%'
                    GROUP BY 1, 2 HAVING count(*) >= 5""", (univs,))
    univ_domains = {}
    for d in cur.fetchall():
        if d["d"]:
            univ_domains.setdefault(d["university_th"], set()).add(d["d"])
    cur.execute("""SELECT id, university_th, full_name_th, first_name, last_name, email
                   FROM faculties WHERE university_th = ANY(%s)""", (univs,))
    rows = cur.fetchall()
    by_th, by_en = {}, {}
    for row in rows:
        by_th.setdefault((row["university_th"], norm_th(row["full_name_th"])), []).append(row)
        by_en.setdefault((row["university_th"], norm_en(row["first_name"], row["last_name"])), []).append(row)

    stats = Counter()
    updates = {}
    for r in records:
        em = (r.get("email") or "").strip().lower()
        if not em:
            continue
        if not EMAIL_RE.match(em) or not INSTITUTIONAL_RE.search(em.split("@")[1]):
            stats["rejected_domain_or_format"] += 1; continue
        if GENERIC_LOCAL_RE.match(em.split("@")[0]) or em in shared:
            stats["rejected_shared_inbox"] += 1; continue
        if em in taken:
            stats["already_in_db"] += 1; continue
        u = r.get("university_th")
        host = em.split("@")[1]
        if not any(host == d or host.endswith("." + d) for d in univ_domains.get(u, ())):
            stats["rejected_foreign_domain"] += 1; continue
        th = norm_th(r.get("full_name_th"))
        cands = by_th.get((u, th), []) if th else []
        if not cands:
            en = norm_en(r.get("first_name"), r.get("last_name"))
            cands = by_en.get((u, en), []) if en and " " in en else []
        if not cands and th:
            cands = [row for row in rows if row["university_th"] == u and
                     fuzz.token_sort_ratio(th, norm_th(row["full_name_th"])) >= 92]
        if len(cands) != 1:
            stats["no_match" if not cands else "ambiguous"] += 1; continue
        row = cands[0]
        if (row["email"] or "").strip():
            stats["row_has_email"] += 1; continue
        if row["id"] in updates and updates[row["id"]] != em:
            stats["conflict"] += 1; updates.pop(row["id"]); continue
        updates[row["id"]] = em
    stats["to_update"] = len(updates)
    print(dict(stats))

    out = PHASE2_DIR / f"reconcile_{prefix.strip('_')}_plan.json"
    out.write_text(json.dumps(updates, ensure_ascii=False, indent=1), encoding="utf-8")
    if not apply:
        print("DRY-RUN only — re-run with --apply to execute.")
        return
    for rid, em in updates.items():
        cur.execute("UPDATE faculties SET email = %s WHERE id = %s AND coalesce(email,'') = ''", (em, rid))
    conn.commit()
    cur.close(); conn.close()
    print(f"APPLIED {len(updates)} emails.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reconcile Phase 2 recovered emails into faculties")
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    main(a.prefix, a.apply)
