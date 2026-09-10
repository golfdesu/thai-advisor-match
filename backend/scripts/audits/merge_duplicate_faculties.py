# -*- coding: utf-8 -*-
"""
Merge duplicate faculty rows — two matching bases:
  default:    same REAL OpenAlex author ID
  --by-name:  same normalized Thai name within the SAME university+faculty
              (catches legacy dataset rows vs fresh SKILL.state acquisitions where
              the old rows lack emails, so the reducer's email pre-check can't see them)

Scope & safety:
- OpenAlex mode excludes sentinels ('' / 'not_indexed').
- --by-name merges ONLY inside one university_th+faculty_th group; the canonical
  display name is the title-stripped form, titles live in academic_title_th.
- Groups where all rows belong to the SAME university_th are merged into a
  single canonical row (the one carrying the most profile information).
- Groups spanning MULTIPLE universities are kept as-is (likely legitimate
  dual affiliations); metrics are identical via OpenAlex anyway.
- Merge = UNION of list fields + first-non-null of scalar fields, then the
  losing rows are deleted after all references (research_labs lead/member)
  are re-pointed to the surviving id.
- Embedding is preserved: kept row's embedding wins; if null, inherits the
  first non-null donor embedding (and is rebuilt from merged embedding_text
  in --by-name mode, where the surviving profile data changes).

Usage (Local Docker DB only — never Supabase):
    python scripts/audits/merge_duplicate_faculties.py                     # dry-run
    python scripts/audits/merge_duplicate_faculties.py --apply
    python scripts/audits/merge_duplicate_faculties.py --by-name [--apply]
"""
import sys
import io
import os
import json
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import psycopg2
import psycopg2.extras

DSN = "postgresql://postgres:postgres@localhost:5432/advisor_match"

LIST_FIELDS = ["research_interests", "featured_publications", "education", "taught_courses"]
SCALAR_FIELDS = [
    "email", "image_url", "profile_url", "scholar_url",
    "academic_title_th", "first_name", "last_name", "role",
    "department", "department_th", "faculty", "faculty_th",
    "embedding_text", "university", "full_name_th",
    # research metrics & identity — first-non-null: same person, kept row inherits
    # the donor's enrichment (without these, deleting an h-index donor loses the metric)
    "h_index", "total_citations", "openalex_id",
]
# rank signal for choosing the canonical row: richer profile wins
RICHNESS_LEN_FIELDS = ["research_interests", "featured_publications", "education"]


def richness(row) -> int:
    score = 0
    for f in RICHNESS_LEN_FIELDS:
        try:
            score += len(json.dumps(row[f], ensure_ascii=False) or "")
        except (TypeError, ValueError):
            pass
    for f in ("email", "image_url", "profile_url", "scholar_url"):
        if row.get(f):
            score += 50
    if row.get("embedding") is not None:
        score += 30
    return score


def merge_lists(values):
    """Union of JSON list fields, order-preserving, dict items deduped by title."""
    out, seen_str, seen_title = [], set(), set()
    for v in values:
        if v is None:
            continue
        items = v if isinstance(v, list) else [v]
        for item in items:
            if isinstance(item, str):
                key = item.strip().lower()
                if key and key not in seen_str:
                    seen_str.add(key)
                    out.append(item)
            elif isinstance(item, dict):
                key = str(item.get("title") or item.get("name") or json.dumps(item, sort_keys=True)).strip().lower()
                if key and key not in seen_title:
                    seen_title.add(key)
                    out.append(item)
            elif item is not None:
                out.append(item)
    return out or []


def norm_display_name(name: str) -> str:
    """Strip leading academic/courtesy rank tokens so 'ศ.ดร. สมคิด' == 'สมคิด เลิศไพฑูรย์'."""
    import re
    n = re.sub(r"\s+", " ", (name or "").strip())
    for _ in range(3):
        n = re.sub(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.|ศ\.|รศ\.|ผศ\.|อ\."
                   r"|นาย|นางสาว|นาง)\s*", "", n).strip()
    return n


SELECT_COLS = """
        id, university_th, faculty_th, full_name_th, openalex_id,
        email, image_url, profile_url, scholar_url,
        academic_title_th, first_name, last_name, role,
        department, department_th, faculty, faculty_th,
        research_interests, featured_publications, education, taught_courses,
        embedding_text, university, embedding IS NOT NULL AS has_emb,
        (coalesce(research_interests::text,'') <> '[]' AND research_interests::text IS NOT NULL)
          OR (coalesce(featured_publications::text,'') <> '[]' AND featured_publications::text IS NOT NULL)
          OR coalesce(email,'') <> '' OR coalesce(image_url,'') <> ''
          OR coalesce(profile_url,'') <> '' OR coalesce(scholar_url,'') <> ''
          OR coalesce(education::text,'') NOT IN ('[]','null','')
        AS has_unique_info
"""


def plan_by_openalex(cur):
    cur.execute("""
        SELECT openalex_id
        FROM faculties
        WHERE openalex_id IS NOT NULL
          AND openalex_id NOT IN ('', 'not_indexed')
        GROUP BY openalex_id
        HAVING count(*) > 1
    """)
    dup_ids = [r["openalex_id"] for r in cur.fetchall()]
    print(f"duplicate openalex_id groups (real IDs only): {len(dup_ids)}")
    if not dup_ids:
        return []

    cur.execute(f"SELECT {SELECT_COLS} FROM faculties WHERE openalex_id = ANY(%s) ORDER BY openalex_id, id",
                (dup_ids,))
    rows = cur.fetchall()

    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["openalex_id"], []).append(r)

    plan, cross_uni_skipped = [], 0
    for oid, members in groups.items():
        by_uni: dict[str, list] = {}
        for m in members:
            by_uni.setdefault(m["university_th"] or "", []).append(m)
        if len(by_uni) > 1:
            cross_uni_skipped += 1
            continue  # dual affiliation — keep all
        for uni, uni_members in by_uni.items():
            if len(uni_members) < 2:
                continue
            all_sparse = all(not m["has_unique_info"] for m in uni_members)
            if all_sparse:
                keep = sorted(uni_members, key=lambda m: m["id"])[0]
                donors = [m for m in uni_members if m["id"] != keep["id"]]
            else:
                ranked = sorted(uni_members, key=richness, reverse=True)
                keep, donors = ranked[0], ranked[1:]
            plan.append((oid, uni, keep, donors))
    print(f"merge groups planned (same-university only): {len(plan)}")
    print(f"cross-university groups skipped (kept as dual affiliations): {cross_uni_skipped}")
    return plan


def plan_by_name(cur):
    """Same normalized Thai name within one university_th + faculty_th."""
    cur.execute(f"SELECT {SELECT_COLS} FROM faculties WHERE full_name_th IS NOT NULL ORDER BY id")
    rows = cur.fetchall()
    groups: dict[tuple, list] = {}
    for r in rows:
        nm = norm_display_name(r["full_name_th"])
        if len(nm) < 4:
            continue
        groups.setdefault((r["university_th"] or "", r["faculty_th"] or "", nm), []).append(r)

    plan = []
    for (uni, fac, nm), members in groups.items():
        if len(members) < 2:
            continue
        ranked = sorted(members, key=richness, reverse=True)
        keep, donors = ranked[0], ranked[1:]
        keep = dict(keep)
        keep["full_name_th"] = nm          # canonical display = title-stripped
        plan.append((nm, uni or fac, keep, donors))
    plan.sort(key=lambda p: (p[1], p[0]))
    print(f"name-collision groups within same uni+faculty: {len(plan)}")
    total_delete = sum(len(d) for _, _, _, d in plan)
    print(f"rows to delete after merge: {total_delete}")
    for nm, uni, keep, donors in plan[:15]:
        print(f"  ▸ [{uni}] {nm[:30]:32} keep={keep['id']:34} ← {[d['id'] for d in donors]}")
    return plan


def execute_merge(cur, plan, rebuild_embeddings: bool) -> None:
    if rebuild_embeddings:
        sys.path.insert(0, os.path.abspath("backend"))
        from app.core.database import SessionLocal
        from app.models.db_models import FacultyDB
        from app.core.embedding_service import embedding_service
        from scripts.faculty_massive_ingestion_runner import build_faculty_embedding_text
        from sqlalchemy import update as sa_update

    kept_ids, deleted_ids, need_reembed = [], [], []
    for oid, uni, keep, donors in plan:
        updates, params = [], []

        for f in LIST_FIELDS:
            merged = merge_lists([keep[f]] + [d[f] for d in donors])
            updates.append(f"{f} = %s")
            params.append(json.dumps(merged, ensure_ascii=False))

        for f in SCALAR_FIELDS:
            if not keep.get(f):
                for d in donors:
                    if d.get(f):
                        updates.append(f"{f} = %s")
                        params.append(d[f])
                        break

        # openalex_id special case: a kept 'not_indexed' sentinel (truthy) must not
        # block a donor's REAL id — prefer the real one.
        if keep.get("openalex_id") in (None, "", "not_indexed"):
            for d in donors:
                oid = d.get("openalex_id")
                if oid and oid != "not_indexed":
                    updates.append("openalex_id = %s")
                    params.append(oid)
                    break

        if keep.get("full_name_th"):
            updates.append("full_name_th = %s")
            params.append(keep["full_name_th"])

        if not keep["has_emb"]:
            for d in donors:
                if d["has_emb"]:
                    updates.append("embedding = (SELECT embedding FROM faculties WHERE id = %s)")
                    params.append(d["id"])
                    break

        if updates:
            params.append(keep["id"])
            cur.execute(f"UPDATE faculties SET {', '.join(updates)} WHERE id = %s", params)

        for d in donors:
            cur.execute(
                "UPDATE research_labs SET lead_advisor_id = %s WHERE lead_advisor_id = %s",
                (keep["id"], d["id"]),
            )
            cur.execute("""
                UPDATE research_labs
                SET member_faculty_ids = (
                    SELECT jsonb_agg(DISTINCT x) FROM jsonb_array_elements_text(
                        to_jsonb(member_faculty_ids)::jsonb
                    ) AS t(x) WHERE x <> %s
                )
                WHERE member_faculty_ids::jsonb @> to_jsonb(ARRAY[%s]::text[])::jsonb
            """, (d["id"], d["id"]))
            cur.execute("DELETE FROM faculties WHERE id = %s", (d["id"],))
            deleted_ids.append(d["id"])

        kept_ids.append(keep["id"])
        if rebuild_embeddings:
            need_reembed.append(keep["id"])

    conn = cur.connection
    conn.commit()
    print(f"\nAPPLIED: merged {len(kept_ids)} canonical rows, deleted {len(deleted_ids)} duplicates.")

    if rebuild_embeddings and need_reembed:
        db = SessionLocal()
        ok = fail = 0
        for i, rid in enumerate(need_reembed, 1):
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
                fail += 1
                db.execute(sa_update(FacultyDB).where(FacultyDB.id == rid).values(embedding=None))
            if i % 25 == 0:
                db.commit()
                print(f"  re-embedded {i}/{len(need_reembed)}")
        db.commit()
        db.close()
        print(f"embedding rebuild: ok={ok} failed={fail} (run backfill_embeddings.py if failed>0)")

    cur.execute("SELECT count(*) AS n FROM faculties")
    print(f"faculties total now: {cur.fetchone()['n']:,}")


def main(apply: bool, by_name: bool) -> None:
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    plan = plan_by_name(cur) if by_name else plan_by_openalex(cur)
    if not plan:
        print("nothing to merge.")
        cur.close(); conn.close()
        return

    total_delete = sum(len(d) for _, _, _, d in plan)
    print(f"rows to delete after merge: {total_delete}\n")
    if not by_name:
        for oid, uni, keep, donors in plan[:12]:
            print(f"  ▸ [{uni}] keep={keep['id']}  ←  delete={[d['id'] for d in donors]}")

    if not apply:
        print("\nDRY-RUN only — re-run with --apply to execute.")
        cur.close(); conn.close()
        return

    execute_merge(cur, plan, rebuild_embeddings=by_name)
    cur.close(); conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge duplicate faculties (by OpenAlex ID or by Thai name)")
    parser.add_argument("--apply", action="store_true", help="Execute the merge (default: dry-run)")
    parser.add_argument("--by-name", action="store_true",
                        help="Match on normalized Thai name within the same university+faculty")
    args = parser.parse_args()
    main(apply=args.apply, by_name=args.by_name)
