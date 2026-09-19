"""Repair email hygiene, publication URLs, and duplicate stubs in local PostgreSQL.

Default mode is read-only dry-run. ``--apply`` commits:
1. Normalizes shared departmental inboxes (36 addresses across 752 records) to SQL NULL.
2. Normalizes personal/free-mail addresses (gmail, yahoo, hotmail, etc. across 333 records) to SQL NULL.
3. Cleans empty string URLs ('url': '') in featured_publications to None across 92 records.
4. Purges 2 verified duplicate stubs ('tu_law_021', 'chulalongk_facultyofa_siriprikphong_026').
5. Rebuilds deterministic embedding_text for every mutated faculty record.

Zero external AI API calls, zero egress to Supabase.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB, ResearchLabDB


SHARED_DEPARTMENTAL_EMAILS = {
    "fish@ku.ac.th",
    "allied@allied.tu.ac.th",
    "fac-en@silpakorn.edu",
    "agro@psu.ac.th",
    "engineering@kku.ac.th",
    "chemy@ku.ac.th",
    "math@cmu.ac.th",
    "attm@med.tu.ac.th",
    "biology@cmu.ac.th",
    "intmed@cmu.ac.th",
    "ams@cmu.ac.th",
    "dsc@cmu.ac.th",
    "cpe@ku.ac.th",
    "chemistry@kmutt.ac.th",
    "stat@sci.kmutnb.ac.th",
    "ie@eng.chula.ac.th",
    "microbiology@kmutt.ac.th",
    "cs@sci.kmutnb.ac.th",
    "ase@eng.ku.ac.th",
    "anatomy.med@g.swu.ac.th",
    "ortho.med@g.swu.ac.th",
    "survey@eng.chula.ac.th",
    "mining@eng.chula.ac.th",
    "radiology.med@g.swu.ac.th",
    "eye.med@g.swu.ac.th",
    "ic@sci.kmutnb.ac.th",
    "water@eng.chula.ac.th",
    "physiology.med@g.swu.ac.th",
    "microbiology.med@g.swu.ac.th",
    "cpe@eng.cmu.ac.th",
    "biochemistry.med@g.swu.ac.th",
    "forensic.med@g.swu.ac.th",
    "webadmin@sit.kmutt.ac.th",
    "pediatrics@cmu.ac.th",
    "cpe@kku.ac.th",
    "commarts@chula.ac.th",
}

PERSONAL_FREEMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "windowslive.com",
    "ymail.com",
}

DUPLICATE_STUB_IDS_TO_DELETE = {
    "tu_law_021",  # duplicate of thammasatu_facultyofl_limpaowart_005
    "chulalongk_facultyofa_siriprikphong_026",  # duplicate of tu_37991aa4_4542
}


def main(*, apply: bool) -> None:
    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "deleted_stubs": [],
        "shared_department_emails_nulled": [],
        "personal_emails_nulled": [],
        "publication_urls_cleaned": 0,
        "faculty_publications_modified": 0,
        "embedding_texts_rebuilt": 0,
    }

    try:
        # 1. DELETE DUPLICATE STUBS
        for stub_id in sorted(DUPLICATE_STUB_IDS_TO_DELETE):
            f = db.query(FacultyDB).filter(FacultyDB.id == stub_id).first()
            if f:
                lab = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == stub_id).first()
                if lab:
                    print(f"Skipping deletion of {stub_id}: referenced by lab {lab.id}")
                    continue
                report["deleted_stubs"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                })
                if apply:
                    db.delete(f)

        # 2. SCAN AND NORMALIZE EMAILS & PUBLICATION URLS ACROSS ALL FACULTIES
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for f in faculties:
            if f.id in DUPLICATE_STUB_IDS_TO_DELETE:
                continue

            changed = False

            # Check email
            if f.email:
                em_lower = f.email.lower().strip()
                dom = em_lower.split("@")[-1].strip() if "@" in em_lower else ""

                if em_lower in SHARED_DEPARTMENTAL_EMAILS:
                    report["shared_department_emails_nulled"].append({
                        "id": f.id,
                        "full_name_th": f.full_name_th,
                        "old_email": f.email,
                    })
                    f.email = None
                    changed = True
                elif dom in PERSONAL_FREEMAIL_DOMAINS:
                    report["personal_emails_nulled"].append({
                        "id": f.id,
                        "full_name_th": f.full_name_th,
                        "old_email": f.email,
                    })
                    f.email = None
                    changed = True

            # Check featured_publications
            if isinstance(f.featured_publications, list):
                pubs_changed = False
                cleaned_pubs = []
                for p in f.featured_publications:
                    if isinstance(p, dict):
                        new_p = dict(p)
                        if new_p.get("url") == "":
                            new_p["url"] = None
                            pubs_changed = True
                            report["publication_urls_cleaned"] = int(report["publication_urls_cleaned"]) + 1
                        cleaned_pubs.append(new_p)
                    else:
                        cleaned_pubs.append(p)

                if pubs_changed:
                    f.featured_publications = cleaned_pubs
                    flag_modified(f, "featured_publications")
                    report["faculty_publications_modified"] = int(report["faculty_publications_modified"]) + 1
                    changed = True

            if changed:
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        out_filename = (
            "email_hygiene_and_duplicates_apply.json"
            if apply
            else "email_hygiene_and_duplicates_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Deleted duplicate stubs: {len(report['deleted_stubs'])}")
        print(f"Shared departmental emails nulled: {len(report['shared_department_emails_nulled'])}")
        print(f"Personal/freemail emails nulled: {len(report['personal_emails_nulled'])}")
        print(f"Publication empty URLs cleaned: {report['publication_urls_cleaned']}")
        print(f"Faculty records with publications modified: {report['faculty_publications_modified']}")
        print(f"Embedding texts rebuilt: {report['embedding_texts_rebuilt']}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all changes to local PostgreSQL.")
        else:
            db.rollback()
            print("Dry-run complete. No changes were committed.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply mutations to local PostgreSQL")
    args = parser.parse_args()
    main(apply=args.apply)
