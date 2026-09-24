"""Wave 57: Top Thai Universities OpenAlex Enrichment Pipeline
Targets universities with low OpenAlex / email coverage:
- SWU (Srinakharinwirot): 1,612 total, 9% openalex → expand
- BUU (Burapha): 930 total, 19% openalex → expand
- KMUTT: 537 total, 32% openalex → expand
- SU (Silpakorn): 696 total, 39% openalex → expand
- PSU (Prince of Songkla): 754 total, 61% openalex → expand
- KMITL: 909 total, 60% openalex → expand
- KMUTNB: 528 total, 71% openalex → expand
- KKU (Khon Kaen): 946 total, 80% openalex → expand
- CMU (Chiang Mai): 1,767 total, 80% openalex → expand
- CU (Chulalongkorn): 2,346 total, 90% openalex → enrich email (64%)
- MU (Mahidol): 1,354 total, 98% openalex → enrich email (81%)

Strategy: Use confirmed OpenAlex institution IDs to fetch full author rosters,
deduplicate against existing DB, insert new + enrich existing.
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
from concurrent.futures import ThreadPoolExecutor

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

# ─────────────────────────────────────────────────────────────
# Confirmed OpenAlex Institution IDs (verified via author lookup)
# ─────────────────────────────────────────────────────────────
TARGET_UNIVERSITIES = [
    # Priority 1: Very low OpenAlex coverage
    {"en": "Srinakharinwirot University",        "th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
     "prefix": "swu",   "openalex_id": "I76920116",   "current_total": 1612, "current_opx_pct": 9},
    {"en": "Burapha University",                  "th": "มหาวิทยาลัยบูรพา",
     "prefix": "buu",   "openalex_id": "I129488602",  "current_total": 930,  "current_opx_pct": 19},
    {"en": "King Mongkut's University of Technology Thonburi", "th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
     "prefix": "kmutt", "openalex_id": "I60837268",   "current_total": 537,  "current_opx_pct": 32},
    {"en": "Suranaree University of Technology",  "th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
     "prefix": "sut",   "openalex_id": "I82475049",   "current_total": 1369, "current_opx_pct": 97},
    {"en": "Naresuan University",                 "th": "มหาวิทยาลัยนเรศวร",
     "prefix": "nu",    "openalex_id": "I4210136448", "current_total": 1530, "current_opx_pct": 85},

    # Priority 2: Medium coverage — expand roster
    {"en": "Silpakorn University",                "th": "มหาวิทยาลัยศิลปากร",
     "prefix": "su",    "openalex_id": "I102985835",  "current_total": 696,  "current_opx_pct": 39},
    {"en": "Prince of Songkla University",        "th": "มหาวิทยาลัยสงขลานครินทร์",
     "prefix": "psu",   "openalex_id": "I183412441",  "current_total": 754,  "current_opx_pct": 61},
    {"en": "King Mongkut's Institute of Technology Ladkrabang", "th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
     "prefix": "kmitl", "openalex_id": "I16426522",   "current_total": 909,  "current_opx_pct": 60},
    {"en": "King Mongkut's University of Technology North Bangkok", "th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
     "prefix": "kmutnb","openalex_id": "I4210090662", "current_total": 528,  "current_opx_pct": 71},
    {"en": "Khon Kaen University",                "th": "มหาวิทยาลัยขอนแก่น",
     "prefix": "kku",   "openalex_id": "I196701617",  "current_total": 946,  "current_opx_pct": 80},

    # Priority 3: Good coverage, but roster likely incomplete
    {"en": "Chiang Mai University",               "th": "มหาวิทยาลัยเชียงใหม่",
     "prefix": "cmu",   "openalex_id": "I48076826",   "current_total": 1767, "current_opx_pct": 80},
    {"en": "Thammasat University",                "th": "มหาวิทยาลัยธรรมศาสตร์",
     "prefix": "tu",    "openalex_id": "I110458564",  "current_total": 1105, "current_opx_pct": 86},
    {"en": "Kasetsart University",                "th": "มหาวิทยาลัยเกษตรศาสตร์",
     "prefix": "ku",    "openalex_id": "I198105771",  "current_total": 3229, "current_opx_pct": 86},
    {"en": "Chulalongkorn University",            "th": "จุฬาลงกรณ์มหาวิทยาลัย",
     "prefix": "cu",    "openalex_id": "I75009780",   "current_total": 2346, "current_opx_pct": 90},
    {"en": "Mahidol University",                  "th": "มหาวิทยาลัยมหิดล",
     "prefix": "mu",    "openalex_id": "I25399158",   "current_total": 1354, "current_opx_pct": 98},
]

RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|สาขาวิชา|หน่วยงาน|คณะ|department|faculty|center|school)", re.I
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
        return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
    for _ in range(2):
        with key_lock:
            if not quota_available:
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
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
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
            time.sleep(0.3)
    return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search


def fetch_openalex_authors(univ: dict) -> tuple[list[dict], int]:
    """Fetch all authors affiliated with this institution from OpenAlex."""
    inst_id = univ["openalex_id"]
    results = []
    cursor = "*"
    pages = 0
    consecutive_errors = 0

    while cursor:
        try:
            params = urllib.parse.urlencode({
                "filter": f"affiliations.institution.id:{inst_id}",
                "select": "id,display_name,last_known_institutions,topics,"
                          "cited_by_count,works_count,summary_stats",
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
            consecutive_errors = 0

            for a in authors:
                display_name = (a.get("display_name") or "").strip()
                if not display_name or RE_BAD_NAME.search(display_name):
                    continue

                topics = [(t.get("display_name") or "") for t in (a.get("topics") or [])[:8]
                          if t.get("display_name")]
                h_index = (a.get("summary_stats") or {}).get("h_index", 0) or 0
                has_thai = any("฀" <= c <= "๿" for c in display_name)

                # Get verified faculty email from last_known_institutions
                email = ""
                for inst in (a.get("last_known_institutions") or []):
                    raw_email = ""
                    # OpenAlex doesn't return individual emails, skip

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

            if pages >= 60 or not cursor:
                break

            time.sleep(0.12)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Exponential backoff: 30, 60, 90, 120, 180s
                wait = min(180, 30 * (consecutive_errors + 1))
                print(f"    Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                consecutive_errors += 1
                if consecutive_errors >= 6:
                    print(f"    Persistent 429 — stopping {univ['prefix']}")
                    break
            else:
                print(f"    HTTP {e.code}")
                break
        except Exception as e:
            if "getaddrinfo" in str(e) or "11001" in str(e):
                print(f"    DNS error (likely post-429 cooldown). Waiting 60s...")
                time.sleep(60)
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    break
            else:
                print(f"    Error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    break
                time.sleep(2)

    return results, pages


def process_university(univ: dict, db, have_ids_global: set) -> tuple[int, int]:
    """Full enrichment pipeline for one university."""
    print(f"\n  {univ['prefix'].upper()} — {univ['en']}")
    print(f"    OpenAlex ID: {univ['openalex_id']} | Current DB: {univ['current_total']:,} | OPX: {univ['current_opx_pct']}%")

    raw_records, pages = fetch_openalex_authors(univ)
    print(f"    Fetched: {len(raw_records):,} authors ({pages} pages)")

    if not raw_records:
        return 0, 0

    # Checkpoint
    ckpt = CHECKPOINT_DIR / f"wave57_{univ['prefix']}_extraction.json"
    with open(ckpt, "w", encoding="utf-8") as f:
        json.dump(raw_records, f, ensure_ascii=False, indent=2)

    # Load existing DB records for this university
    existing = db.query(
        FacultyDB.id,
        FacultyDB.full_name_th,
        FacultyDB.first_name,
        FacultyDB.last_name,
        FacultyDB.email,
        FacultyDB.openalex_id,
        FacultyDB.total_citations,
        FacultyDB.h_index,
        FacultyDB.total_publications_count,
        FacultyDB.research_interests,
    ).filter(FacultyDB.university == univ["en"]).all()

    existing_by_openalex: dict[str, str] = {}
    existing_by_name_th: dict[str, str] = {}
    existing_by_name_en: dict[str, str] = {}
    existing_metrics: dict[str, dict] = {}

    for row in existing:
        eid, nth, fn, ln, email, opx, cit, h, pubs, ri = row
        name_en = f"{fn or ''} {ln or ''}".strip()
        if opx and opx not in ("not_indexed", "none", "null", ""):
            existing_by_openalex[opx] = eid
        if nth and len(nth) > 2:
            existing_by_name_th[nth.lower()] = eid
        if name_en and len(name_en) > 2:
            existing_by_name_en[name_en.lower()] = eid
        existing_metrics[eid] = {
            "c": cit or 0, "h": h or 0, "w": pubs or 0,
            "ri": set(ri or []),
        }

    to_insert = []
    enrichment = []
    seen_batch: set[str] = set()

    for rec in raw_records:
        opx = (rec.get("openalex_id") or "").strip()
        name_th = (rec.get("full_name_th") or "").strip()
        name_en = (rec.get("full_name_en") or "").strip()
        name_key = (name_th or name_en).lower().strip()

        matched = None
        if opx and opx in existing_by_openalex:
            matched = existing_by_openalex[opx]
        if not matched and name_th and name_th.lower() in existing_by_name_th:
            matched = existing_by_name_th[name_th.lower()]
        if not matched and name_en and name_en.lower() in existing_by_name_en:
            matched = existing_by_name_en[name_en.lower()]
        if not matched and name_key and len(name_key) > 3:
            for en, eid in existing_by_name_th.items():
                if fuzz.token_set_ratio(name_key, en) >= 90:
                    matched = eid
                    break
        if not matched and name_key and len(name_key) > 3:
            for en, eid in existing_by_name_en.items():
                if fuzz.token_set_ratio(name_key, en) >= 90:
                    matched = eid
                    break

        if matched:
            old = existing_metrics.get(matched, {})
            new_cit = rec.get("total_citations", 0) or 0
            new_topics = set(rec.get("research_interests") or [])
            if new_cit > old.get("c", 0) or (opx and opx not in existing_by_openalex) or (new_topics - old.get("ri", set())):
                enrichment.append({
                    "id": matched,
                    "total_citations": new_cit,
                    "h_index": rec.get("h_index", 0) or 0,
                    "total_publications_count": rec.get("works_count", 0) or 0,
                    "openalex_id": opx,
                    "research_interests": list(new_topics),
                })
        else:
            dedup_key = (opx or name_key or "").strip()
            if dedup_key in seen_batch:
                continue
            seen_batch.add(dedup_key)
            to_insert.append(rec)

    # Apply enrichment updates
    enriched_count = 0
    for upd in enrichment:
        fac = db.query(FacultyDB).filter(FacultyDB.id == upd["id"]).first()
        if not fac:
            continue
        changed = False
        if (upd["total_citations"] or 0) > (fac.total_citations or 0):
            fac.total_citations = upd["total_citations"]
            fac.h_index = max(fac.h_index or 0, upd["h_index"] or 0)
            fac.total_publications_count = max(
                fac.total_publications_count or 0,
                upd["total_publications_count"] or 0
            )
            changed = True
        if upd["openalex_id"] and not (fac.openalex_id and fac.openalex_id not in ("not_indexed", "")):
            fac.openalex_id = upd["openalex_id"]
            changed = True
        if upd["research_interests"]:
            merged = list(set(fac.research_interests or []) | set(upd["research_interests"]))
            if merged != (fac.research_interests or []):
                fac.research_interests = merged
                changed = True
        if changed:
            enriched_count += 1
    if enriched_count:
        db.commit()

    print(f"    -> New: {len(to_insert):,} | Enrich: {enriched_count:,}")

    if not to_insert:
        return 0, enriched_count

    # Generate embeddings
    embed_texts = []
    for r in to_insert:
        name = (r.get("full_name_th") or r.get("full_name_en") or "").strip()
        interests = " | ".join((r.get("research_interests") or [])[:5])
        embed_texts.append(f"{name} {univ['th']} {interests}".strip())

    with ThreadPoolExecutor(max_workers=min(4, len(clients) or 1)) as ex:
        embs = list(ex.map(get_embedding, embed_texts))

    # Commit to DB
    seq = 0
    new_objs = []

    for i, r in enumerate(to_insert):
        seq += 1
        uid = f"{univ['prefix']}_w57_{seq:04d}_{random.randint(100, 999)}"
        while uid in have_ids_global:
            seq += 1
            uid = f"{univ['prefix']}_w57_{seq:04d}_{random.randint(100, 999)}"
        have_ids_global.add(uid)

        emb = embs[i] if i < len(embs) else None  # NULL: re-embed via embed_missing.py
        fn_th = r.get("full_name_th") or r.get("full_name_en") or "อาจารย์"
        interests = [RE_PHONE.sub("", x).strip() for x in (r.get("research_interests") or [])]
        interests = [x for x in interests if x and len(x) > 2]

        new_objs.append(FacultyDB(
            id=uid,
            first_name=r.get("first_name") or "",
            last_name=r.get("last_name") or "",
            full_name_th=fn_th,
            academic_title_th="",
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

    return len(new_objs), enriched_count


def main():
    print("=" * 70)
    print("Wave 57: Top Thai Universities OpenAlex Enrichment Pipeline")
    print(f"         {len(TARGET_UNIVERSITIES)} universities")
    print("=" * 70)

    db = SessionLocal()
    try:
        have_ids_global = {r[0] for r in db.query(FacultyDB.id).all()}
        print(f"Starting DB size: {len(have_ids_global):,}")

        total_inserted = 0
        total_enriched = 0
        results_summary = []

        for idx, univ in enumerate(TARGET_UNIVERSITIES):
            inserted, enriched = process_university(univ, db, have_ids_global)
            total_inserted += inserted
            total_enriched += enriched
            results_summary.append((univ["prefix"].upper(), inserted, enriched))
            # Inter-university cooldown to prevent sustained 429 burst
            if idx < len(TARGET_UNIVERSITIES) - 1 and inserted == 0 and enriched == 0:
                # If we got nothing (likely rate-limited), wait longer before next
                print(f"  [cooldown] No data from {univ['prefix'].upper()}, waiting 45s before next university...")
                time.sleep(45)
            elif idx < len(TARGET_UNIVERSITIES) - 1:
                time.sleep(3)  # Normal inter-university gap

        # Final per-university verification
        from sqlalchemy import text
        print(f"\n{'='*70}")
        print("Wave 57 Final Results:")
        print(f"{'University':<50} {'Total':>7} {'OPX':>7} {'OPX%':>6}")
        print("-" * 72)
        for univ in TARGET_UNIVERSITIES:
            row = db.execute(text(
                "SELECT COUNT(*), "
                "COUNT(CASE WHEN openalex_id != '' AND openalex_id IS NOT NULL AND openalex_id != 'not_indexed' THEN 1 END) "
                "FROM faculties WHERE university = :u"
            ), {"u": univ["en"]}).fetchone()
            total, opx = row[0], row[1]
            pct = 100 * opx // max(1, total)
            delta = total - univ["current_total"]
            print(f"  {univ['prefix'].upper()+' '+univ['en'][:42]:<50} {total:>7,} {opx:>7,} {pct:>5}%  (+{delta:,})")

        grand_total = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()
        total_opx = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE openalex_id != '' AND openalex_id IS NOT NULL AND openalex_id != 'not_indexed'"
        )).scalar()
        print(f"\n  Grand Total: {grand_total:,} | OpenAlex: {total_opx:,} ({100*total_opx//max(1,grand_total)}%)")
        print(f"  Wave 57: +{total_inserted:,} new, {total_enriched:,} enriched")

    finally:
        db.close()

    print("\nWave 57 Pipeline Complete!")


if __name__ == "__main__":
    main()
