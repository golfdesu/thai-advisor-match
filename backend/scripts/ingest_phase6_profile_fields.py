# -*- coding: utf-8 -*-
"""
Phase 6 faculty profile fields (image_url / education / taught_courses) ingestion (2026-09-26).

Source: agentic_pipeline/profile_enrich_runner.py results (backend/data/agent_states/phase6/).

Rules:
- Targets are faculty whose profile_url is a personal page (used by exactly one row, not openalex.org)
  and who miss at least one of the three fields.
- Fill only EMPTY fields; existing values are never overwritten.
- Pages the LLM did not confirm as this person's profile are quarantined.
- image_url: must be picked by the LLM from the page's own <img> list, on an allowed Next.js image
  host (*.ac.th / *.edu), and not shared by 2+ people in the results (default avatars / logos).
- education / taught_courses: phone numbers and emails are stripped (PDPA); items outside
  4..300 chars are dropped.
- Rows whose text changed are re-embedded (existing embedding_text + the new fields).
- Local Docker DB ONLY.

Usage:
    python scripts/ingest_phase6_profile_fields.py --export-targets phase6/targets_pilot.json \
        --hosts research.tsu.ac.th intranet.wu.ac.th www.cmu.ac.th
    python scripts/ingest_phase6_profile_fields.py --results phase6/results_pilot.json            # dry-run
    python scripts/ingest_phase6_profile_fields.py --results phase6/results_pilot.json --apply
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, or_, cast, String

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

STATE_DIR = Path(os.getenv("AGENT_STATE_DIR", BACKEND_DIR / "data" / "agent_states"))
IMG_HOST_RE = re.compile(r"(^|\.)([a-z0-9-]+\.)*(ac\.th|edu)$", re.I)
PHONE_RE = re.compile(r"(\+?66[\s-]?|0)\d{1,2}[\s-]?\d{3}[\s-]?\d{3,4}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def empty(v) -> bool:
    return v is None or v == [] or v == "" or v == "null"


def clean_items(items) -> list[str]:
    out = []
    for x in items or []:
        x = EMAIL_RE.sub("", PHONE_RE.sub("", str(x)))
        x = re.sub(r"\s+", " ", x).strip(" ,;:-|")
        if 4 <= len(x) <= 300 and x not in out:
            out.append(x)
    return out


def valid_image(url) -> bool:
    if not url:
        return False
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(IMG_HOST_RE.search(p.hostname or ""))


def resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else STATE_DIR / path


def export_targets(out: str, hosts: list[str]) -> None:
    session = SessionLocal()
    try:
        single = (session.query(FacultyDB.profile_url).filter(FacultyDB.profile_url.isnot(None),
                                                              FacultyDB.profile_url != "")
                  .group_by(FacultyDB.profile_url).having(func.count() == 1).subquery())
        missing = or_(func.coalesce(FacultyDB.image_url, "") == "",
                      FacultyDB.education.is_(None), cast(FacultyDB.education, String).in_(["[]", "null"]),
                      FacultyDB.taught_courses.is_(None), cast(FacultyDB.taught_courses, String).in_(["[]", "null"]))
        rows = (session.query(FacultyDB.id, FacultyDB.full_name_th, FacultyDB.first_name, FacultyDB.last_name,
                              FacultyDB.profile_url)
                .join(single, single.c.profile_url == FacultyDB.profile_url)
                .filter(missing, ~FacultyDB.profile_url.like("%openalex.org%")).all())
        targets = [{"id": r.id, "name_th": r.full_name_th, "name_en": f"{r.first_name or ''} {r.last_name or ''}".strip(),
                    "profile_url": r.profile_url}
                   for r in rows if not hosts or urlparse(r.profile_url).netloc in hosts]
        resolve(out).parent.mkdir(parents=True, exist_ok=True)
        resolve(out).write_text(json.dumps(targets, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"exported targets={len(targets)} -> {out}")
    finally:
        session.close()


def main(results_path: str, apply: bool) -> None:
    results = json.loads(resolve(results_path).read_text(encoding="utf-8"))
    img_count = Counter(r.get("image_url") for r in results.values() if r.get("image_url"))
    session = SessionLocal()
    try:
        rows = {r.id: r for r in session.query(FacultyDB.id, FacultyDB.image_url, FacultyDB.education,
                                               FacultyDB.taught_courses, FacultyDB.embedding_text)
                .filter(FacultyDB.id.in_(list(results))).all()}
        plan, quarantine = {}, []
        stats = Counter()
        for fid, r in results.items():
            stats[r["status"]] += 1
            if r["status"] != "ok" or fid not in rows:
                continue
            if not r.get("is_person_profile"):
                quarantine.append({"id": fid, "reason": "not confirmed as this person's profile", **r})
                stats["q_not_profile"] += 1
                continue
            row, patch = rows[fid], {}
            img = r.get("image_url")
            if empty(row.image_url) and valid_image(img):
                if img_count[img] == 1:
                    patch["image_url"] = img
                else:
                    stats["img_shared_dropped"] += 1
            edu = clean_items(r.get("education"))
            if empty(row.education) and edu:
                patch["education"] = edu
            courses = clean_items(r.get("taught_courses"))
            if empty(row.taught_courses) and courses:
                patch["taught_courses"] = courses
            if patch:
                plan[fid] = patch
                for k in patch:
                    stats[f"fill_{k}"] += 1
        print(json.dumps(dict(stats), ensure_ascii=False))
        stem = resolve(results_path).stem
        (resolve(results_path).parent / f"{stem}_plan.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        (resolve(results_path).parent / f"{stem}_quarantine.json").write_text(
            json.dumps(quarantine, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"update={len(plan)} quarantine={len(quarantine)}")
        if not apply:
            print("DRY-RUN only — re-run with --apply to execute.")
            return

        from app.core.embedding_service import embedding_service

        def new_text(fid):
            p, base = plan[fid], rows[fid].embedding_text or ""
            extra = ""
            if p.get("education"):
                extra += f" Education: {'; '.join(p['education'])}."
            if p.get("taught_courses"):
                extra += f" Taught Courses: {', '.join(p['taught_courses'])}."
            return (base + extra)[:6000] if extra else None

        def embed(fid):
            text = new_text(fid)
            if not text:
                return fid, None, None
            try:
                vec = embedding_service.get_embedding(text)
                return fid, text, vec if isinstance(vec, list) and len(vec) == 768 else None
            except Exception as e:
                print(f"embed fail {fid}: {str(e)[:120]}")
                return fid, text, None

        with ThreadPoolExecutor(max_workers=6) as ex:
            embeds = {fid: (t, v) for fid, t, v in ex.map(embed, list(plan))}
        reembedded = kept_old = 0
        for fid, patch in plan.items():
            text, vec = embeds[fid]
            if text and vec:
                patch = {**patch, "embedding_text": text, "embedding": vec}
                reembedded += 1
            elif text:
                kept_old += 1  # keep the old vector rather than write a dummy one
            session.query(FacultyDB).filter(FacultyDB.id == fid).update(patch, synchronize_session=False)
        session.commit()
        print(f"APPLIED update={len(plan)} reembedded={reembedded} embed_failed_kept_old={kept_old}")
    finally:
        session.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase 6 profile field ingestion")
    ap.add_argument("--export-targets")
    ap.add_argument("--hosts", nargs="*", default=[])
    ap.add_argument("--results")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.export_targets:
        export_targets(a.export_targets, a.hosts)
    elif a.results:
        main(a.results, a.apply)
    else:
        ap.error("use --export-targets or --results")
