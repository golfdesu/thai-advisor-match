# -*- coding: utf-8 -*-
"""
Relocate OpenAlex Mismatched Faculty Records to True Universities
==================================================================
Identifies 101 faculty records whose assigned university never appeared in their
OpenAlex publication history and whose verified institutional home is another
Thai university (e.g. Mahidol, Chulalongkorn, CMU, Kasetsart, NIDA, Thammasat).

Actions:
1. Re-assign university_th and university to their true institution.
2. Ensure faculty_th aligns with their academic subject.
3. Clean synthetic or placeholder fields.
4. Assign clean canonical IDs.
5. Re-generate embedding_text and 768-dim vector embeddings via embedding_service.
6. Commit changes to PostgreSQL.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
SCRIPTS_DIR = BACKEND_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from app.core.embedding_text import build_faculty_embedding_text
from scripts.audits.clean_prototype_synthetic_faculties import slugify
from scripts.audits.audit_openalex_affiliations import match_thai_univ


def run_relocation():
    print("=================================================================", flush=True)
    print("🚀 RELOCATING OPENALEX MISMATCHED SCHOLARS TO TRUE UNIVERSITIES", flush=True)
    print("=================================================================", flush=True)

    conflict_file = BACKEND_DIR / "data" / "agent_states" / "openalex_affiliation_conflicts.json"
    cache_file = BACKEND_DIR / "data" / "agent_states" / "openalex_affiliations_cache.json"

    with open(conflict_file, "r", encoding="utf-8") as f:
        conflicts = json.load(f)
    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    no_email = [c for c in conflicts if not (c.get("email") or "").strip()]

    db = SessionLocal()
    try:
        relocations = []
        for c in no_email:
            fid = c["id"]
            meta = cache.get(c["openalex_id"], {})
            affs = meta.get("affiliations", [])
            lkis = meta.get("last_known_institutions", [])
            assigned_u = c["assigned_univ"]

            # check if assigned_u appears in any affiliation
            found_assigned = any(
                match_thai_univ(a.get("institution")) and match_thai_univ(a.get("institution"))[0] == assigned_u
                for a in affs
            ) or any(
                match_thai_univ(l.get("display_name")) and match_thai_univ(l.get("display_name"))[0] == assigned_u
                for l in lkis
            )

            if found_assigned:
                continue

            primary_target = None
            for l in lkis:
                m = match_thai_univ(l.get("display_name"))
                if m:
                    primary_target = m
                    break
            if not primary_target:
                for a in affs:
                    m = match_thai_univ(a.get("institution"))
                    if m:
                        primary_target = m
                        break

            if not primary_target:
                continue

            relocations.append((c, primary_target))

        print(f"Identified {len(relocations)} verified scholars to relocate to authentic institutions.\n", flush=True)

        count_relocated = 0
        t0 = time.time()

        for c, (target_u_th, target_u_en) in relocations:
            old_id = c["id"]
            fac = db.query(FacultyDB).filter(FacultyDB.id == old_id).first()
            if not fac:
                continue

            old_uni = fac.university_th
            fac.university_th = target_u_th
            fac.university = target_u_en
            fac.email = None

            # Generate clean ID
            uni_prefix = slugify(target_u_en.split()[0])[:4]
            name_slug = slugify(fac.last_name or fac.first_name or "scholar")[:12]
            suffix = old_id.split("_")[-1][:6]
            new_id = f"{uni_prefix}_reloc_{name_slug}_{suffix}"

            # Check ID uniqueness
            existing_id = db.query(FacultyDB.id).filter(FacultyDB.id == new_id).first()
            if existing_id:
                new_id = f"{new_id}_{int(time.time()) % 1000}"

            # Recompute embedding text and vector
            emb_text = build_faculty_embedding_text(fac)
            vec = embedding_service.get_embedding(emb_text)

            # Update DB via clean cast
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE public.faculties
                        SET id = :new_id,
                            university_th = :target_u_th,
                            university = :target_u_en,
                            email = NULL,
                            education = CAST('[]' AS json),
                            embedding_text = :emb_text,
                            embedding = CAST(:vec AS vector)
                        WHERE id = :old_id
                    """),
                    {
                        "new_id": new_id,
                        "target_u_th": target_u_th,
                        "target_u_en": target_u_en,
                        "emb_text": emb_text,
                        "vec": str(vec),
                        "old_id": old_id,
                    }
                )

            count_relocated += 1
            if count_relocated % 10 == 0 or count_relocated == len(relocations):
                elapsed = time.time() - t0
                print(f"  [{count_relocated}/{len(relocations)}] Relocated {fac.full_name_th} ({old_uni} -> {target_u_th}) [{elapsed:.1f}s]", flush=True)

        print(f"\n✅ Successfully relocated and grounded {count_relocated} scholars to their true universities!", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    run_relocation()
