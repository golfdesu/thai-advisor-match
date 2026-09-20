"""Wave 53 Fix: Fetch missing RMUT campuses with corrected OpenAlex IDs
Fixes RMUTL, RMUTK, RMUTR, RMUTSV, RMUTS, RMUTTO with correct IDs
and adds RMUTT via generic RMUT + Thailand affiliation filter.
"""

import os
import sys
import json
import time
import re
import random
import threading
import urllib.request
import urllib.parse
import urllib.error
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from app.core.config import settings
    from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB
    from backend.app.core.config import settings
    from backend.scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

from google import genai
from google.genai import types
from rapidfuzz import fuzz

# Corrected RMUT campus OpenAlex IDs from OpenAlex search
RMUT_FIX_CAMPUSES = [
    {
        "en": "Rajamangala University of Technology Thanyaburi",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
        "short": "RMUTT",
        "prefix": "rmutt",
        # RMUTT is merged under general RMUT; use Thailand filter
        "openalex_id": "I10245363",   # generic RMUT -- filter by TH affiliation string
        "filter_name": "Thanyaburi",
    },
    {
        "en": "Rajamangala University of Technology Lanna",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลล้านนา",
        "short": "RMUTL",
        "prefix": "rmutl",
        "openalex_id": "I73683852",
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Krungthep",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
        "short": "RMUTK",
        "prefix": "rmutk",
        "openalex_id": "I4210094798",
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Rattanakosin",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลรัตนโกสินทร์",
        "short": "RMUTR",
        "prefix": "rmutr",
        "openalex_id": "I4210088080",   # corrected from I4210107090
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Srivijaya",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลศรีวิชัย",
        "short": "RMUTSV",
        "prefix": "rmutsv",
        "openalex_id": "I73668669",     # corrected from I4210090296
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Suvanabhumi",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลสุวรรณภูมิ",
        "short": "RMUTS",
        "prefix": "rmuts",
        "openalex_id": "I4210106845",   # corrected from I4210146567
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Tawan-ok",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลตะวันออก",
        "short": "RMUTTO",
        "prefix": "rmutto",
        "openalex_id": "I4210130811",   # corrected from I4210106200
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Isan",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลอีสาน",
        "short": "RMUTI",
        "prefix": "rmuti",
        "openalex_id": "I1285782058",   # corrected from I4210116416
        "filter_name": None,
    },
    {
        "en": "Rajamangala University of Technology Phra Nakhon",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
        "short": "RMUTP",
        "prefix": "rmutp",
        "openalex_id": "I4210118263",   # corrected from I4210134987
        "filter_name": None,
    },
]

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# Embedding setup
def setup_clients():
    keys_raw = getattr(settings, "GEMINI_API_KEYS", None) or getattr(settings, "GEMINI_API_KEY", None)
    if isinstance(keys_raw, str):
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    elif isinstance(keys_raw, list):
        keys = [k.strip() for k in keys_raw if k and k.strip()]
    else:
        keys = []
    return [genai.Client(api_key=k) for k in keys]

clients = setup_clients()
key_box = [0]
key_lock = threading.Lock()
quota_available = len(clients) > 0
consecutive_429 = [0]


def get_embedding(text: str) -> list[float]:
    global quota_available
    if not quota_available or not clients:
        return [0.0] * 768
    for _ in range(2):
        with key_lock:
            if not quota_available:
                return [0.0] * 768
            c = clients[key_box[0] % len(clients)]
            key_box[0] += 1
        try:
            res = c.models.embed_content(
                model="gemini-embedding-001",
                contents=text[:2000],
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            with key_lock:
                consecutive_429[0] = 0
            return res.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                with key_lock:
                    consecutive_429[0] += 1
                    if consecutive_429[0] >= 3:
                        quota_available = False
                        print("  WARN: Gemini quota exhausted. Baseline embeddings.")
                return [0.0] * 768
            time.sleep(0.3)
    return [0.0] * 768


def fetch_openalex_campus(campus: dict) -> list[dict]:
    """Fetch authors for a RMUT campus from OpenAlex."""
    inst_id = campus["openalex_id"]
    filter_name = campus.get("filter_name")
    print(f"  [OpenAlex] {campus['short']} ({inst_id}): fetching...")
    results = []
    cursor = "*"
    pages = 0

    while cursor:
        try:
            filter_str = f"affiliations.institution.id:{inst_id}"
            params = urllib.parse.urlencode({
                "filter": filter_str,
                "select": "id,display_name,last_known_institutions,topics,cited_by_count,works_count,summary_stats",
                "per-page": "200",
                "cursor": cursor,
                "mailto": "research@example.com",
            })
            url = f"https://api.openalex.org/authors?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "AdvisorMatchBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            authors = data.get("results", [])
            cursor = data.get("meta", {}).get("next_cursor")
            pages += 1

            for a in authors:
                display_name = (a.get("display_name") or "").strip()
                if not display_name:
                    continue

                # For generic RMUT, verify by last_known_institutions display_name
                if filter_name:
                    last_insts = a.get("last_known_institutions") or []
                    ok = any(filter_name.lower() in (i.get("display_name") or "").lower()
                             for i in last_insts)
                    if not ok:
                        continue

                topics = [(t.get("display_name") or "") for t in (a.get("topics") or [])[:8]
                          if (t.get("display_name") or "")]
                h_index = (a.get("summary_stats") or {}).get("h_index", 0) or 0
                has_thai = any("฀" <= c <= "๿" for c in display_name)

                results.append({
                    "full_name_th": display_name if has_thai else "",
                    "full_name_en": "" if has_thai else display_name,
                    "first_name": "", "last_name": "",
                    "academic_title_th": "", "academic_title_en": "",
                    "faculty": "", "faculty_th": "",
                    "department": "", "department_th": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": f"https://openalex.org/{(a.get('id','') or '').split('/')[-1]}",
                    "research_interests": topics,
                    "featured_publications": [],
                    "total_citations": a.get("cited_by_count", 0) or 0,
                    "h_index": h_index,
                    "works_count": a.get("works_count", 0) or 0,
                    "openalex_id": (a.get("id") or "").split("/")[-1],
                    "_campus_prefix": campus["prefix"],
                })

            if pages >= 40 or not cursor:
                break
            time.sleep(0.15)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5)
            else:
                print(f"    HTTP {e.code}: {e}")
                break
        except Exception as e:
            print(f"    Error: {e}")
            break

    print(f"    -> {campus['short']}: {len(results)} authors ({pages} pages)")
    return results


def main():
    print("=" * 70)
    print("Wave 53 Fix: RMUT Corrected OpenAlex IDs Pipeline")
    print("=" * 70)

    db = SessionLocal()
    try:
        total_inserted = 0
        total_enriched = 0

        for campus in RMUT_FIX_CAMPUSES:
            print(f"\n{'─'*60}")
            print(f"  {campus['en']}")

            records = fetch_openalex_campus(campus)
            if not records:
                print(f"  -> No records, skip")
                continue

            # Load existing from DB
            existing = db.query(
                FacultyDB.id,
                FacultyDB.full_name_th,
                FacultyDB.first_name,
                FacultyDB.last_name,
                FacultyDB.openalex_id,
                FacultyDB.total_citations,
                FacultyDB.h_index,
                FacultyDB.total_publications_count,
            ).filter(FacultyDB.university == campus["en"]).all()

            existing_by_openalex: dict[str, str] = {}
            existing_by_name: dict[str, str] = {}
            existing_metrics: dict[str, dict] = {}

            for row in existing:
                eid, nth, fn, ln, opx, cit, h, pubs = row
                if opx:
                    existing_by_openalex[opx] = eid
                name = (nth or f"{fn} {ln}".strip() or "").lower().strip()
                if name and len(name) > 2:
                    existing_by_name[name] = eid
                existing_metrics[eid] = {"c": cit or 0, "h": h or 0, "w": pubs or 0}

            print(f"  Existing in DB: {len(existing)}")

            to_insert = []
            enrichment = []
            seen_batch: set[str] = set()

            for rec in records:
                opx = (rec.get("openalex_id") or "").strip()
                name_th = (rec.get("full_name_th") or "").strip()
                name_en = (rec.get("full_name_en") or "").strip()
                name_key = (name_th or name_en).lower().strip()

                matched = None
                if opx and opx in existing_by_openalex:
                    matched = existing_by_openalex[opx]
                if not matched and name_key and name_key in existing_by_name:
                    matched = existing_by_name[name_key]
                if not matched and name_key and len(name_key) > 3:
                    for en, eid in existing_by_name.items():
                        if fuzz.token_set_ratio(name_key, en) >= 90:
                            matched = eid
                            break

                if matched:
                    old = existing_metrics.get(matched, {})
                    if (rec.get("total_citations", 0) or 0) > old.get("c", 0):
                        enrichment.append({
                            "id": matched,
                            "total_citations": rec["total_citations"],
                            "h_index": rec["h_index"],
                            "total_publications_count": rec["works_count"],
                            "openalex_id": opx,
                            "research_interests": rec.get("research_interests") or [],
                        })
                else:
                    dedup_key = (opx or name_key or "").strip()
                    if dedup_key in seen_batch:
                        continue
                    seen_batch.add(dedup_key)
                    to_insert.append(rec)

            print(f"  New: {len(to_insert)}, Enrich: {len(enrichment)}")

            # Enrichment
            for upd in enrichment:
                fac = db.query(FacultyDB).filter(FacultyDB.id == upd["id"]).first()
                if not fac:
                    continue
                if (upd["total_citations"] or 0) > (fac.total_citations or 0):
                    fac.total_citations = upd["total_citations"]
                    fac.h_index = max(fac.h_index or 0, upd["h_index"] or 0)
                    fac.total_publications_count = max(
                        fac.total_publications_count or 0,
                        upd["total_publications_count"] or 0
                    )
                if upd["openalex_id"] and not fac.openalex_id:
                    fac.openalex_id = upd["openalex_id"]
                if upd["research_interests"]:
                    merged = list(set(fac.research_interests or []) | set(upd["research_interests"]))
                    fac.research_interests = merged
            if enrichment:
                db.commit()
                total_enriched += len(enrichment)

            if not to_insert:
                continue

            # Embeddings
            print(f"  Generating {len(to_insert)} embeddings...")
            embed_texts = []
            for r in to_insert:
                name = (r.get("full_name_th") or r.get("full_name_en") or "").strip()
                interests = " | ".join((r.get("research_interests") or [])[:5])
                embed_texts.append(f"{name} {campus['th']} {interests}".strip())

            with ThreadPoolExecutor(max_workers=min(4, len(clients) or 1)) as ex:
                embs = list(ex.map(get_embedding, embed_texts))

            # DB commit
            have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
            seq = 0
            new_objs = []
            for i, r in enumerate(to_insert):
                seq += 1
                uid = f"{campus['prefix']}_w53b_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"{campus['prefix']}_w53b_{seq:04d}_{random.randint(100, 999)}"
                have_ids.add(uid)

                emb = embs[i] if i < len(embs) else [0.0] * 768
                fn_th = r.get("full_name_th") or r.get("full_name_en") or "อาจารย์"

                new_objs.append(FacultyDB(
                    id=uid,
                    first_name=r.get("first_name") or "",
                    last_name=r.get("last_name") or "",
                    full_name_th=fn_th,
                    academic_title_th=r.get("academic_title_th") or "",
                    university=campus["en"],
                    university_th=campus["th"],
                    faculty=r.get("faculty") or "",
                    faculty_th=r.get("faculty_th") or "",
                    department=r.get("department") or "",
                    department_th=r.get("department_th") or "",
                    email=r.get("email") or "",
                    image_url=r.get("image_url") or "",
                    profile_url=r.get("profile_url") or "",
                    research_interests=r.get("research_interests") or [],
                    featured_publications=[],
                    total_citations=r.get("total_citations") or 0,
                    h_index=r.get("h_index") or 0,
                    total_publications_count=r.get("works_count") or 0,
                    openalex_id=r.get("openalex_id") or "",
                    embedding=emb,
                ))

            batch_size = 300
            for i in range(0, len(new_objs), batch_size):
                db.add_all(new_objs[i:i + batch_size])
                db.commit()
                print(f"    Batch committed: {len(new_objs[i:i+batch_size])}")

            total_inserted += len(new_objs)
            print(f"  {campus['short']} done: +{len(new_objs)} inserted")

        # Final stats
        from sqlalchemy import text
        total_rmut = db.execute(text("SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%'")).scalar()
        total_all = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()
        rmut_opx = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%' "
            "AND openalex_id != '' AND openalex_id IS NOT NULL"
        )).scalar()

        # Per-campus breakdown
        rows = db.execute(text(
            "SELECT university, COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%' GROUP BY university ORDER BY COUNT(*) DESC"
        )).fetchall()

        print(f"\n{'='*70}")
        print("Wave 53 Fix Final Results:")
        for r in rows:
            print(f"  {r[0]}: {r[1]}")
        print(f"\n  RMUT Total: {total_rmut:,}")
        print(f"  RMUT with OpenAlex: {rmut_opx:,} ({100*rmut_opx//max(1,total_rmut)}%)")
        print(f"  Grand Total: {total_all:,}")
        print(f"\n  +{total_inserted} new, {total_enriched} enriched")

    finally:
        db.close()

    print("\nWave 53 Fix Complete!")


if __name__ == "__main__":
    main()
