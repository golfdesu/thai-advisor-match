"""Wave 56: Rajabhat Universities Comprehensive Autonomous Pipeline
Harvests faculty data from all major Rajabhat (มหาวิทยาลัยราชภัฏ) universities via OpenAlex.
Covers 23 Rajabhat campuses across Thailand.
"""

import sys
import json
import time
import re
import random
import threading
import urllib.request
import urllib.parse
import urllib.error
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

RAJABHAT_UNIVERSITIES = [
    {"en": "Suan Sunandha Rajabhat University", "th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
     "prefix": "ssru", "openalex_id": "I4210105946"},
    {"en": "Bansomdejchaopraya Rajabhat University", "th": "มหาวิทยาลัยราชภัฏบ้านสมเด็จเจ้าพระยา",
     "prefix": "bsru", "openalex_id": "I4210134513"},
    {"en": "Chiang Mai Rajabhat University", "th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
     "prefix": "cmru", "openalex_id": "I9340882"},
    {"en": "Nakhon Ratchasima Rajabhat University", "th": "มหาวิทยาลัยราชภัฏนครราชสีมา",
     "prefix": "nrru", "openalex_id": "I4210151714"},
    {"en": "Udon Thani Rajabhat University", "th": "มหาวิทยาลัยราชภัฏอุดรธานี",
     "prefix": "udru", "openalex_id": "I3132704155"},
    {"en": "Rajabhat Maha Sarakham University", "th": "มหาวิทยาลัยราชภัฏมหาสารคาม",
     "prefix": "rmu", "openalex_id": "I4210135781"},
    {"en": "Phetchaburi Rajabhat University", "th": "มหาวิทยาลัยราชภัฏเพชรบุรี",
     "prefix": "pbru", "openalex_id": "I4210106727"},
    {"en": "Nakhon Si Thammarat Rajabhat University", "th": "มหาวิทยาลัยราชภัฏนครศรีธรรมราช",
     "prefix": "nstru", "openalex_id": "I4210160017"},
    {"en": "Songkhla Rajabhat University", "th": "มหาวิทยาลัยราชภัฏสงขลา",
     "prefix": "skru", "openalex_id": "I194118695"},
    {"en": "Roi et Rajabhat University", "th": "มหาวิทยาลัยราชภัฏร้อยเอ็ด",
     "prefix": "reru", "openalex_id": "I4210087403"},
    {"en": "Loei Rajabhat University", "th": "มหาวิทยาลัยราชภัฏเลย",
     "prefix": "lru", "openalex_id": "I4210150485"},
    {"en": "Nakhon Pathom Rajabhat University", "th": "มหาวิทยาลัยราชภัฏนครปฐม",
     "prefix": "npru", "openalex_id": "I4210139698"},
    {"en": "Phranakhon Si Ayutthaya Rajabhat University", "th": "มหาวิทยาลัยราชภัฏพระนครศรีอยุธยา",
     "prefix": "aru", "openalex_id": "I4210130090"},
    {"en": "Buriram Rajabhat University", "th": "มหาวิทยาลัยราชภัฏบุรีรัมย์",
     "prefix": "bru", "openalex_id": "I4210091243"},
    {"en": "Sakon Nakhon Rajabhat University", "th": "มหาวิทยาลัยราชภัฏสกลนคร",
     "prefix": "snru", "openalex_id": "I4210159985"},
    {"en": "Uttaradit Rajabhat University", "th": "มหาวิทยาลัยราชภัฏอุตรดิตถ์",
     "prefix": "uru", "openalex_id": "I176205391"},
    {"en": "Rambhai Barni Rajabhat University", "th": "มหาวิทยาลัยราชภัฏรำไพพรรณี",
     "prefix": "rbru", "openalex_id": "I4210141957"},
    {"en": "Phetchabun Rajabhat University", "th": "มหาวิทยาลัยราชภัฏเพชรบูรณ์",
     "prefix": "pcru", "openalex_id": "I4210088548"},
    {"en": "Lampang Rajabhat University", "th": "มหาวิทยาลัยราชภัฏลำปาง",
     "prefix": "lpru", "openalex_id": "I4210096430"},
    {"en": "Chandrakasem Rajabhat University", "th": "มหาวิทยาลัยราชภัฏจันทรเกษม",
     "prefix": "cru", "openalex_id": "I95579309"},
    {"en": "Phranakhon Rajabhat University", "th": "มหาวิทยาลัยราชภัฏพระนคร",
     "prefix": "pnru", "openalex_id": "I4210096456"},
    {"en": "Sisaket Rajabhat University", "th": "มหาวิทยาลัยราชภัฏศรีสะเกษ",
     "prefix": "sskru", "openalex_id": "I4210128712"},
]

RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|สาขาวิชา|หน่วยงาน|คณะ|สาขา|โทร|เบอร์|ห้อง|center|department|faculty)",
    re.I,
)

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


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
                config=types.EmbedContentConfig(output_dimensionality=768),
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


def fetch_openalex(univ: dict) -> list[dict]:
    inst_id = univ["openalex_id"]
    results = []
    cursor = "*"
    pages = 0

    while cursor:
        try:
            params = urllib.parse.urlencode({
                "filter": f"affiliations.institution.id:{inst_id}",
                "select": "id,display_name,topics,cited_by_count,works_count,summary_stats",
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
                    "profile_url": f"https://openalex.org/{(a.get('id') or '').split('/')[-1]}",
                    "research_interests": topics,
                    "featured_publications": [],
                    "total_citations": a.get("cited_by_count", 0) or 0,
                    "h_index": h_index,
                    "works_count": a.get("works_count", 0) or 0,
                    "openalex_id": (a.get("id") or "").split("/")[-1],
                })

            if pages >= 50 or not cursor:
                break
            time.sleep(0.15)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5)
            else:
                print(f"    HTTP {e.code}")
                break
        except Exception as e:
            print(f"    Error: {e}")
            break

    return results, pages


def process_university(univ: dict, db, have_ids_global: set) -> tuple[int, int]:
    inst_id = univ["openalex_id"]
    print(f"\n  {univ['en']}: fetching OpenAlex ({inst_id})...")

    raw_records, pages = fetch_openalex(univ)
    print(f"    -> {len(raw_records)} authors ({pages} pages)")

    if not raw_records:
        return 0, 0

    # Checkpoint
    ckpt = CHECKPOINT_DIR / f"wave56_{univ['prefix']}_extraction.json"
    with open(ckpt, "w", encoding="utf-8") as f:
        json.dump(raw_records, f, ensure_ascii=False, indent=2)

    # Load existing from DB for this university
    existing = db.query(
        FacultyDB.id,
        FacultyDB.full_name_th,
        FacultyDB.first_name,
        FacultyDB.last_name,
        FacultyDB.openalex_id,
        FacultyDB.total_citations,
        FacultyDB.h_index,
        FacultyDB.total_publications_count,
    ).filter(FacultyDB.university == univ["en"]).all()

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

    to_insert = []
    enrichment = []
    seen_batch: set[str] = set()

    for rec in raw_records:
        opx = (rec.get("openalex_id") or "").strip()
        name_th = (rec.get("full_name_th") or "").strip()
        name_en = (rec.get("full_name_en") or "").strip()
        name_key = (name_th or name_en).lower().strip()

        if RE_BAD_NAME.search(name_th) or RE_BAD_NAME.search(name_en):
            continue

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

    # Enrichment
    for upd in enrichment:
        fac = db.query(FacultyDB).filter(FacultyDB.id == upd["id"]).first()
        if not fac:
            continue
        if (upd["total_citations"] or 0) > (fac.total_citations or 0):
            fac.total_citations = upd["total_citations"]
            fac.h_index = max(fac.h_index or 0, upd["h_index"] or 0)
            fac.total_publications_count = max(
                fac.total_publications_count or 0, upd["total_publications_count"] or 0
            )
        if upd["openalex_id"] and not fac.openalex_id:
            fac.openalex_id = upd["openalex_id"]
        if upd["research_interests"]:
            fac.research_interests = list(set(fac.research_interests or []) | set(upd["research_interests"]))
    if enrichment:
        db.commit()

    if not to_insert:
        print(f"    -> {univ['en']}: 0 new, {len(enrichment)} enriched")
        return 0, len(enrichment)

    # Embeddings
    embed_texts = []
    for r in to_insert:
        name = (r.get("full_name_th") or r.get("full_name_en") or "").strip()
        interests = " | ".join((r.get("research_interests") or [])[:5])
        embed_texts.append(f"{name} {univ['th']} {interests}".strip())

    with ThreadPoolExecutor(max_workers=min(4, len(clients) or 1)) as ex:
        embs = list(ex.map(get_embedding, embed_texts))

    # DB commit
    seq = 0
    new_objs = []

    for i, r in enumerate(to_insert):
        seq += 1
        uid = f"{univ['prefix']}_w56_{seq:04d}_{random.randint(100, 999)}"
        while uid in have_ids_global:
            seq += 1
            uid = f"{univ['prefix']}_w56_{seq:04d}_{random.randint(100, 999)}"
        have_ids_global.add(uid)

        emb = embs[i] if i < len(embs) else [0.0] * 768
        fn_th = r.get("full_name_th") or r.get("full_name_en") or "อาจารย์"

        interests = [RE_PHONE.sub("", x).strip() for x in (r.get("research_interests") or [])]
        interests = [x for x in interests if x and len(x) > 2]

        new_objs.append(FacultyDB(
            id=uid,
            first_name=r.get("first_name") or "",
            last_name=r.get("last_name") or "",
            full_name_th=fn_th,
            academic_title_th=r.get("academic_title_th") or "",
            university=univ["en"],
            university_th=univ["th"],
            faculty="",
            faculty_th="",
            department="",
            department_th="",
            email="",
            image_url="",
            profile_url=r.get("profile_url") or "",
            research_interests=interests,
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

    print(f"    -> +{len(new_objs)} new, {len(enrichment)} enriched | {len(new_objs)+len(existing)} total")
    return len(new_objs), len(enrichment)


def main():
    print("=" * 70)
    print("Wave 56: Rajabhat Universities Comprehensive Pipeline")
    print(f"         {len(RAJABHAT_UNIVERSITIES)} universities")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Pre-load all IDs globally to prevent collisions across universities
        have_ids_global = {r[0] for r in db.query(FacultyDB.id).all()}
        print(f"Existing records in DB: {len(have_ids_global):,}")

        total_inserted = 0
        total_enriched = 0

        for univ in RAJABHAT_UNIVERSITIES:
            inserted, enriched = process_university(univ, db, have_ids_global)
            total_inserted += inserted
            total_enriched += enriched

        # Final stats
        from sqlalchemy import text
        total_all = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()
        rajabhat_total = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajabhat%'"
        )).scalar()
        rajabhat_opx = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajabhat%' "
            "AND openalex_id != '' AND openalex_id IS NOT NULL"
        )).scalar()

        # Per-university summary
        rows = db.execute(text(
            "SELECT university, COUNT(*) FROM faculties WHERE university LIKE '%Rajabhat%' "
            "GROUP BY university ORDER BY COUNT(*) DESC"
        )).fetchall()

        print(f"\n{'='*70}")
        print("Wave 56 Final Results:")
        for r in rows:
            print(f"  {r[0]}: {r[1]:,}")
        print(f"\n  Rajabhat Total: {rajabhat_total:,}")
        print(f"  Rajabhat with OpenAlex: {rajabhat_opx:,} ({100*rajabhat_opx//max(1,rajabhat_total)}%)")
        print(f"  Grand Total: {total_all:,}")
        print(f"\n  Wave 56 Summary: +{total_inserted:,} new, {total_enriched:,} enriched")

    finally:
        db.close()

    print("\nWave 56 Rajabhat Pipeline Complete!")


if __name__ == "__main__":
    main()
