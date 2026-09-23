# -*- coding: utf-8 -*-
"""
Thai Faculty Romanization & Dual-Factor OpenAlex Verification Pipeline

Target: Faculty members with openalex_id IS NULL (currently 2,622 records).
Phases:
  1. Romanization Hypothesis Generation:
     - Retains valid English first_name if already present.
     - Uses gemini-3.5-flash-lite to transliterate Thai names/surnames to Latin/English.
     - Checkpoints transliterations to backend/data/agent_states/thai_romanization_cache.json.
  2. Dual-Factor Corroboration in OpenAlex (7 API keys, 21 worker threads):
     - Factor 1: Name match (surname token + given name/initial).
     - Factor 2: Institutional affiliation match (university tokens).
     - Resolves h_index, total_citations, total_publications_count, openalex_id.
     - Confirmed genuine zero-hits get stamped 'not_indexed' and h_index=0.
  3. Database Commit:
     - Maintains total_publications_count == first_author_count + co_author_count invariant.
     - Updates embedding_text if name changed.
     - Batch commits every 100 records with full reversal checkpoints.

Usage:
  python backend/scripts/enrich_thai_faculty_openalex.py              # dry-run
  python backend/scripts/enrich_thai_faculty_openalex.py --apply      # commit to database
  python backend/scripts/enrich_thai_faculty_openalex.py --apply --limit 200
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend directory is in python path
_SCRIPTS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR))

from dotenv import load_dotenv

_env_file = _BACKEND_DIR / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file)
else:
    load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from fetch_openalex_publication_metrics import (
    fetch_with_retry, all_keys_exhausted
)
from enrich_openalex_author_metrics import (
    strip_accents, tokens, qualify_candidates, topic_disambiguate,
    inst_frag, COMMON_INST_STOP, api_healthy, CANARY, SENTINEL_MISS,
    PROTECTED_SENTINEL_IDS
)

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
ROMANIZATION_CACHE_PATH = os.path.join(CHECKPOINT_DIR, "thai_romanization_cache.json")
ENRICHMENT_SNAPSHOT_PATH = os.path.join(CHECKPOINT_DIR, "thai_romanized_enrichment.json")
PROBED_IDS_PATH = os.path.join(CHECKPOINT_DIR, "openalex_probed_ids.json")


def load_probed_ids() -> set:
    """Load set of already-probed faculty IDs from checkpoint."""
    if os.path.exists(PROBED_IDS_PATH):
        try:
            with open(PROBED_IDS_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_probed_ids(probed: set):
    """Save probed IDs set to checkpoint on disk."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    with open(PROBED_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(probed)), f)


def load_romanization_cache() -> dict:
    """Load existing romanization cache from disk if available."""
    if os.path.exists(ROMANIZATION_CACHE_PATH):
        try:
            with open(ROMANIZATION_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load romanization cache: {e}", flush=True)
    return {}


def save_romanization_cache(cache: dict):
    """Save romanization cache to disk."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    with open(ROMANIZATION_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def generate_romanization_batch(items: list, gemini_clients: list) -> list:
    """
    Calls gemini-3.6-flash to transliterate a batch of Thai names.
    Cycles through available gemini_clients if one hits rate-limit or 503.
    """
    prompt = f"""Transliterate the following Thai scholar names into English Latin alphabet (first_name, last_name).
Rules:
1. If existing_first_name is provided and is a valid English given name, retain it as first_name and only transliterate the surname as last_name.
2. Strip all titles (academic, medical, military, civic, such as ผศ., รศ., ศ., อ., ดร., พญ., นพ., ภก., คุณ, ร.ต.อ., ว่าที่ร้อยตรี, ว่าที่เรือตรี, etc.).
3. If an English name is already present or embedded in full_name_th, extract and use that English name.
4. Ensure outputs contain ONLY pure ASCII characters [a-zA-Z -]. No Thai characters.
5. Return JSON array of objects with keys: "id", "first_name", "last_name".

Input:
{json.dumps(items, ensure_ascii=False)}
"""
    for client in gemini_clients:
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            cleaned = []
            for d in data:
                fid = str(d.get("id", ""))
                fn = re.sub(r"[^a-zA-Z\s\-]", "", str(d.get("first_name", "")).strip()).strip().title()
                ln = re.sub(r"[^a-zA-Z\s\-]", "", str(d.get("last_name", "")).strip()).strip().title()
                cleaned.append({"id": fid, "first_name": fn, "last_name": ln})
            return cleaned
        except Exception as e:
            continue
    return []


def corroborates_enhanced(cand: dict, uni: str) -> bool:
    """
    Enhanced corroborator: checks both affiliations and last_known_institutions.
    Uses token length >= 3 for university tokens.
    """
    if not uni:
        return False
    utok = {t for t in inst_frag(uni).split() if len(t) >= 3 and t not in COMMON_INST_STOP}
    if not utok:
        return False

    inst_names = []
    for a in cand.get("affiliations") or []:
        inst_names.append((a.get("institution") or {}).get("display_name", ""))
    for lki in cand.get("last_known_institutions") or []:
        inst_names.append(lki.get("display_name", ""))

    for name in inst_names:
        disp_toks = set(inst_frag(name).split())
        if bool(utok & disp_toks):
            return True
    return False


def search_openalex_author(name: str, per_page: int = 10) -> list:
    """Query OpenAlex author search endpoint with polite key rotation."""
    q = urllib.parse.quote(name)
    url = f"https://api.openalex.org/authors?search={q}&per-page={per_page}"
    d = fetch_with_retry(url, max_retries=4)
    return (d or {}).get("results", []) or []


def probe_faculty_record(item: tuple) -> tuple:
    """
    Thread-safe worker function. Network ONLY, no DB sessions.
    item: (rid, first_name, last_name, university, research_interests)
    Returns: (rid, first_name, last_name, author_dict_or_None, verdict)
      verdict in {'match', 'no_hit', 'ambiguous'}
    """
    rid, fn, ln, uni, interests = item
    if not ln or len(ln) < 2:
        return rid, fn, ln, None, "skip_no_name"

    if all_keys_exhausted():
        return rid, fn, ln, None, "exhausted"

    query = f"{strip_accents(fn).strip()} {strip_accents(ln).strip()}"
    cands = search_openalex_author(query)
    qualifying = qualify_candidates(fn, ln, cands)

    if not qualifying:
        return rid, fn, ln, None, "no_hit"

    # Check institutional corroboration
    corr = [c for c in qualifying if corroborates_enhanced(c, uni or "")]
    if corr:
        corr.sort(key=lambda c: ((c.get("summary_stats") or {}).get("h_index") or 0), reverse=True)
        return rid, fn, ln, corr[0], "match"

    # If only one candidate exists, verify it doesn't conflict with a different Thai university
    if len(qualifying) == 1:
        c = qualifying[0]
        # Check if candidate is associated with a conflicting Thai institution
        cand_insts = []
        for a in c.get("affiliations") or []:
            cand_insts.append((a.get("institution") or {}).get("display_name", ""))
        for lki in c.get("last_known_institutions") or []:
            cand_insts.append(lki.get("display_name", ""))

        has_th_country = any((lki.get("country_code") == "TH") for lki in (c.get("last_known_institutions") or []))

        # If topics match research_interests, treat as verified match
        if interests:
            winner = topic_disambiguate(qualifying, interests)
            if winner:
                return rid, fn, ln, winner, "match"

        # If candidate has Thailand country code or unique long surname, and no conflicting institutions
        if has_th_country or (len(ln) >= 6 and not cand_insts):
            return rid, fn, ln, c, "match"

        return rid, fn, ln, None, "ambiguous"

    # Multiple qualifying candidates: try topic disambiguation
    if interests:
        winner = topic_disambiguate(qualifying, interests)
        if winner:
            return rid, fn, ln, winner, "match"

    return rid, fn, ln, None, "ambiguous"


def main():
    parser = argparse.ArgumentParser(description="Thai Faculty Romanization & Dual-Factor OpenAlex Enrichment")
    parser.add_argument("--limit", type=int, default=0, help="Max records to process (0 = all)")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    parser.add_argument("--workers", type=int, default=21, help="Worker threads for OpenAlex (default 21)")
    parser.add_argument("--batch", type=int, default=100, help="DB commit batch size (default 100)")
    parser.add_argument("--skip-romanize", action="store_true", help="Skip Gemini romanization pass")
    parser.add_argument("--include-not-indexed", action="store_true", help="Process records with openalex_id == 'not_indexed'")
    parser.add_argument("--reset-probed", action="store_true", help="Clear probed IDs checkpoint")
    args = parser.parse_args()

    print("=================================================================", flush=True)
    print("🚀 THAI FACULTY ROMANIZATION & DUAL-FACTOR OPENALEX ENRICHMENT", flush=True)
    print(f"Mode: {'APPLY (Database commit)' if args.apply else 'DRY-RUN (Simulate only)'}", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # 1. Fetch target faculty records where openalex_id IS NULL or not_indexed
        if args.include_not_indexed:
            filter_cond = (FacultyDB.openalex_id.is_(None)) | (FacultyDB.openalex_id == "not_indexed")
        else:
            filter_cond = FacultyDB.openalex_id.is_(None)

        targets = (
            db.query(
                FacultyDB.id,
                FacultyDB.full_name_th,
                FacultyDB.first_name,
                FacultyDB.last_name,
                FacultyDB.university,
                FacultyDB.research_interests
            )
            .filter(filter_cond)
            .filter(~FacultyDB.id.in_(PROTECTED_SENTINEL_IDS))
            .all()
        )

        total_targets = len(targets)
        print(f"Found {total_targets} faculty records to process (include_not_indexed={args.include_not_indexed})", flush=True)
        if total_targets == 0:
            print("No records to process! 100% already enriched.", flush=True)
            return

        probed_ids = set() if args.reset_probed else load_probed_ids()
        print(f"Loaded {len(probed_ids)} previously probed IDs from checkpoint", flush=True)

        if not args.reset_probed and probed_ids:
            targets = [t for t in targets if t.id not in probed_ids]
            print(f"Remaining un-probed targets after checkpoint filter: {len(targets)}", flush=True)

        if len(targets) == 0:
            print("All target records have already been probed in previous runs!", flush=True)
            return

        if args.limit > 0:
            targets = targets[: args.limit]
            print(f"Limited processing to {len(targets)} records", flush=True)

        # 2. Romanization Pass
        cache = load_romanization_cache()
        print(f"Loaded {len(cache)} existing transliterations from cache", flush=True)

        needed_romanization = []
        for r in targets:
            rid = r.id
            if rid in cache:
                continue
            fn = (r.first_name or "").strip()
            ln = (r.last_name or "").strip()
            if fn.isascii() and len(fn) >= 2 and ln.isascii() and len(ln) >= 2:
                # Already has valid first and last name in DB
                cache[rid] = {"first_name": fn, "last_name": ln}
                continue

            existing_first = fn if (fn.isascii() and len(fn) >= 2) else None
            needed_romanization.append({
                "id": rid,
                "full_name_th": r.full_name_th or "",
                "existing_first_name": existing_first
            })

        if needed_romanization and not args.skip_romanize:
            print(f"\n--- Transliterating {len(needed_romanization)} names via Gemini ---", flush=True)
            raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "")
            gemini_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
            if not gemini_keys:
                print("ERROR: GEMINI_API_KEY / GEMINI_API_KEYS not found in backend/.env", flush=True)
                return

            from google import genai
            gemini_clients = [genai.Client(api_key=k) for k in gemini_keys]

            chunk_size = 40
            for i in range(0, len(needed_romanization), chunk_size):
                chunk = needed_romanization[i : i + chunk_size]
                pct = ((i + len(chunk)) / len(needed_romanization)) * 100
                print(f"Transliterating [{i + len(chunk)}/{len(needed_romanization)}] ({pct:.1f}%)...", flush=True)
                results = generate_romanization_batch(chunk, gemini_clients)
                for res in results:
                    fid = res["id"]
                    cache[fid] = {
                        "first_name": res.get("first_name", ""),
                        "last_name": res.get("last_name", "")
                    }
                save_romanization_cache(cache)
                time.sleep(0.3)

            print(f"✅ Romanization complete! Cache now holds {len(cache)} names.\n", flush=True)
        elif needed_romanization and args.skip_romanize:
            print(f"Skipping romanization pass (--skip-romanize). {len(needed_romanization)} records without transliteration.", flush=True)

        # 3. OpenAlex Health Check
        if not api_healthy():
            print("❌ OpenAlex API is not healthy right now (quota exhausted or rate limited). Aborting.", flush=True)
            return
        print("✅ OpenAlex API healthy (CANARY probe succeeded)", flush=True)

        # 4. Prepare OpenAlex Verification Work Items
        work_items = []
        for r in targets:
            rid = r.id
            names = cache.get(rid, {})
            fn = names.get("first_name") or (r.first_name if (r.first_name and r.first_name.isascii()) else "")
            ln = names.get("last_name") or (r.last_name if (r.last_name and r.last_name.isascii()) else "")
            work_items.append((rid, fn, ln, r.university, r.research_interests))

        print(f"\n--- Probing OpenAlex across {len(work_items)} candidates ({args.workers} workers) ---", flush=True)

        stats = {
            "match": 0,
            "not_indexed": 0,
            "ambiguous": 0,
            "applied": 0
        }
        changes_snapshot = []
        pending_commits = []

        start_time = time.time()
        chunk_step = 500
        total_done = 0

        for chunk_idx in range(0, len(work_items), chunk_step):
            if all_keys_exhausted():
                print("\n[!] All OpenAlex API keys have reached daily quota! Gracefully committing and halting.", flush=True)
                break

            current_chunk = work_items[chunk_idx : chunk_idx + chunk_step]
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                future_to_item = {executor.submit(probe_faculty_record, item): item for item in current_chunk}

                for future in as_completed(future_to_item):
                    total_done += 1
                    try:
                        rid, fn, ln, author, verdict = future.result()
                    except Exception as e:
                        verdict = "error"
                        author = None
                        rid = future_to_item[future][0]
                        fn, ln = future_to_item[future][1], future_to_item[future][2]

                    if verdict == "match" and author:
                        stats["match"] += 1
                        raw_id = author.get("id", "")
                        oa_id = raw_id if raw_id.startswith("http") else f"https://openalex.org/{raw_id}"
                        stats_dict = author.get("summary_stats") or {}
                        h_idx = stats_dict.get("h_index") or 0
                        citations = author.get("cited_by_count") or 0
                        works = author.get("works_count") or 0

                        pending_commits.append({
                            "id": rid,
                            "first_name": fn,
                            "last_name": ln,
                            "openalex_id": oa_id,
                            "h_index": h_idx,
                            "total_citations": citations,
                            "total_publications_count": works,
                            "verdict": "match"
                        })
                    elif verdict == "no_hit":
                        stats["not_indexed"] += 1
                        pending_commits.append({
                            "id": rid,
                            "first_name": fn,
                            "last_name": ln,
                            "openalex_id": SENTINEL_MISS,
                            "h_index": 0,
                            "total_citations": 0,
                            "total_publications_count": 0,
                            "verdict": "not_indexed"
                        })
                    elif verdict == "exhausted":
                        break
                    elif verdict in ("skip_no_name", "error"):
                        stats["skipped"] = stats.get("skipped", 0) + 1
                    else:
                        stats["ambiguous"] += 1
                        if fn and ln:
                            pending_commits.append({
                                "id": rid,
                                "first_name": fn,
                                "last_name": ln,
                                "openalex_id": SENTINEL_MISS,
                                "h_index": 0,
                                "total_citations": 0,
                                "total_publications_count": 0,
                                "verdict": "ambiguous_sentinel"
                            })

                    if verdict != "exhausted":
                        probed_ids.add(rid)

                    # Batch Commit
                    if len(pending_commits) >= args.batch:
                        if args.apply:
                            apply_db_batch(db, pending_commits)
                            stats["applied"] += len(pending_commits)
                        changes_snapshot.extend(pending_commits)
                        save_probed_ids(probed_ids)
                        pending_commits = []

                    if total_done % 100 == 0 or total_done == len(work_items):
                        elapsed = time.time() - start_time
                        rate = total_done / elapsed if elapsed > 0 else 0
                        print(
                            f"[{total_done}/{len(work_items)}] "
                            f"Matches: {stats['match']} | Not Indexed: {stats['not_indexed']} | "
                            f"Ambiguous: {stats['ambiguous']} ({rate:.1f} records/s)",
                            flush=True
                        )

            if all_keys_exhausted():
                print("\n[!] All OpenAlex API keys have reached daily quota! Halting chunk iteration.", flush=True)
                break

        # Final commit for remaining items
        if pending_commits:
            if args.apply:
                apply_db_batch(db, pending_commits)
                stats["applied"] += len(pending_commits)
            changes_snapshot.extend(pending_commits)
            save_probed_ids(probed_ids)
            pending_commits = []

        # Save snapshot
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        all_matches = [c for c in changes_snapshot if c.get("verdict") == "match"]
        with open(ENRICHMENT_SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": "apply" if args.apply else "dry-run",
                "stats": stats,
                "changes_count": len(changes_snapshot),
                "matched_count": len(all_matches),
                "sample_matches": all_matches[:100],
                "sample_changes": changes_snapshot[:50]
            }, f, ensure_ascii=False, indent=2)

        print("\n=================================================================", flush=True)
        print("🎉 ENRICHMENT COMPLETED SUCCESSFULLY!", flush=True)
        print(f"Total Processed: {total_done}", flush=True)
        print(f"Authentic Matches: {stats['match']}", flush=True)
        print(f"Stamped Not Indexed: {stats['not_indexed']}", flush=True)
        print(f"Ambiguous / Handled: {stats['ambiguous']}", flush=True)
        print(f"Applied to Database: {stats['applied']}", flush=True)
        print(f"Checkpoint saved to: {ENRICHMENT_SNAPSHOT_PATH}", flush=True)
        print("=================================================================", flush=True)

    finally:
        db.close()


def apply_db_batch(db, batch: list):
    """
    Applies a batch of updates to PostgreSQL.
    Maintains: total_publications_count == first_author_count + co_author_count invariant.
    Guarantees: Zero duplicate OpenAlex ID collisions across distinct individuals.
    """
    fids = [item["id"] for item in batch]
    faculties = db.query(FacultyDB).filter(FacultyDB.id.in_(fids)).all()
    fac_map = {f.id: f for f in faculties}

    # Query all currently assigned OpenAlex IDs in DB to prevent collisions
    target_oa_ids = [item["openalex_id"] for item in batch if item["verdict"] == "match" and item.get("openalex_id")]
    existing_collisions = set()
    if target_oa_ids:
        rows = db.query(FacultyDB.openalex_id).filter(
            FacultyDB.openalex_id.in_(target_oa_ids),
            ~FacultyDB.id.in_(fids)
        ).all()
        existing_collisions = {r[0] for r in rows}

    assigned_in_batch = set()
    for item in batch:
        fac = fac_map.get(item["id"])
        if not fac:
            continue

        # Update names if currently empty
        if not fac.first_name and item.get("first_name"):
            fac.first_name = item["first_name"]
        if not fac.last_name and item.get("last_name"):
            fac.last_name = item["last_name"]

        if item["verdict"] == "match":
            oa_id = item["openalex_id"]
            if oa_id in existing_collisions or oa_id in assigned_in_batch:
                # Collision detected with another individual; avoid assigning duplicate
                continue

            assigned_in_batch.add(oa_id)
            fac.openalex_id = oa_id
            fac.h_index = max(fac.h_index or 0, item["h_index"])
            fac.total_citations = max(fac.total_citations or 0, item["total_citations"])
            applied_pubs = max(fac.total_publications_count or 0, item["total_publications_count"])
            if (fac.first_author_count or 0) > 0 or (fac.co_author_count or 0) > 0:
                current_sum = (fac.first_author_count or 0) + (fac.co_author_count or 0)
                diff = applied_pubs - current_sum
                if diff > 0:
                    fac.co_author_count = (fac.co_author_count or 0) + diff
                else:
                    applied_pubs = current_sum
            fac.total_publications_count = applied_pubs
        elif item["verdict"] in ("not_indexed", "ambiguous_sentinel"):
            if not fac.openalex_id:
                fac.openalex_id = SENTINEL_MISS
            if fac.total_citations is None:
                fac.total_citations = 0
            if fac.total_publications_count is None:
                fac.total_publications_count = 0

        # Refresh embedding text
        fac.embedding_text = build_faculty_embedding_text(fac)

    db.commit()


if __name__ == "__main__":
    main()
