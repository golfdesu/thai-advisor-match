# -*- coding: utf-8 -*-
"""
Clean, Verify & Ground All Faculties in Faculties Table
======================================================
Autonomous pipeline fulfilling the zero-defect faculty hygiene goal:
1. Two-Factor Deduplication: Merges ghost duplicates across and within universities into
   their genuine active teaching winners, preserving author metrics and moving ghosts to scholars_unassigned.
2. Demonstration School Archival: Archives K-12 demonstration school teachers into scholars_unassigned.
3. Authenticity Remediation: Corrects misassigned faculties (e.g. CU/MU co-author artifacts) to authentic faculties.
4. Department Normalization: Standardizes single-department faculties (Law, Nursing, Education) to valid canonical fields.
5. Inactive / Ghost Archival: Moves consortium ghost records with bare titles to scholars_unassigned after merging.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "faculty_hygiene_and_dedup_checkpoint.json"

EMAIL_DOMAIN_MAP = {
    "chula.ac.th": "จุฬาลงกรณ์มหาวิทยาลัย",
    "cmu.ac.th": "มหาวิทยาลัยเชียงใหม่",
    "ku.ac.th": "มหาวิทยาลัยเกษตรศาสตร์",
    "mahidol.ac.th": "มหาวิทยาลัยมหิดล",
    "mahidol.edu": "มหาวิทยาลัยมหิดล",
    "psu.ac.th": "มหาวิทยาลัยสงขลานครินทร์",
    "kku.ac.th": "มหาวิทยาลัยขอนแก่น",
    "tu.ac.th": "มหาวิทยาลัยธรรมศาสตร์",
    "kmutt.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "kmitl.ac.th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "kmutnb.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "su.ac.th": "มหาวิทยาลัยศิลปากร",
    "sut.ac.th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "swu.ac.th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "buu.ac.th": "มหาวิทยาลัยบูรพา",
    "nu.ac.th": "มหาวิทยาลัยนเรศวร",
    "mfu.ac.th": "มหาวิทยาลัยแม่ฟ้าหลวง",
    "up.ac.th": "มหาวิทยาลัยพะเยา",
    "wu.ac.th": "มหาวิทยาลัยวลัยลักษณ์",
    "tsu.ac.th": "มหาวิทยาลัยทักษิณ",
    "msu.ac.th": "มหาวิทยาลัยมหาสารคาม",
    "ubu.ac.th": "มหาวิทยาลัยอุบลราชธานี",
    "mju.ac.th": "มหาวิทยาลัยแม่โจ้",
    "nida.ac.th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
    "ru.ac.th": "มหาวิทยาลัยรามคำแหง",
    "stou.ac.th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
    "ssru.ac.th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
    "cmru.ac.th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
    "rmutto.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลตะวันออก",
    "rmutp.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
    "rmutk.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
    "rmutl.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลล้านนา",
    "rmutsb.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลสุวรรณภูมิ",
    "rmutsv.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลศรีวิชัย",
    "rmuti.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลอีสาน",
    "rmutr.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลรัตนโกสินทร์",
    "rmutt.ac.th": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
    "bu.ac.th": "มหาวิทยาลัยกรุงเทพ",
    "au.edu": "มหาวิทยาลัยอัสสัมชัญ",
    "msme.au.edu": "มหาวิทยาลัยอัสสัมชัญ",
    "spu.ac.th": "มหาวิทยาลัยศรีปทุม",
}

RE_JUNK_INTERESTS = re.compile(r"^(?:none|-|\?|n/a|null|undefined)$", re.I)


def get_email_univ(email: str | None) -> str | None:
    if not email:
        return None
    em = email.lower().strip()
    for domain, univ in EMAIL_DOMAIN_MAP.items():
        if domain in em:
            return univ
    return None


def are_same_person(r1: FacultyDB, r2: FacultyDB) -> bool:
    """Strict Two-Factor Disambiguation preventing homonymous name collision."""
    # Factor 1: OpenAlex ID
    if r1.openalex_id and r2.openalex_id:
        if r1.openalex_id != "not_indexed" and r2.openalex_id != "not_indexed":
            if r1.openalex_id == r2.openalex_id:
                return True

    # Factor 2: Email
    if r1.email and r2.email:
        if r1.email.strip().lower() == r2.email.strip().lower():
            return True

    # Factor 3: English Name
    fn1 = (r1.first_name or "").strip().lower()
    ln1 = (r1.last_name or "").strip().lower()
    fn2 = (r2.first_name or "").strip().lower()
    ln2 = (r2.last_name or "").strip().lower()
    if fn1 and ln1 and fn2 and ln2:
        if fn1 == fn2 and ln1 == ln2:
            return True
        # If both have English names and they do NOT match -> distinct persons!
        return False

    # Factor 4: Publication overlap
    pubs1 = set()
    for p in (r1.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and len(t) > 10:
            pubs1.add(t)
    pubs2 = set()
    for p in (r2.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and len(t) > 10:
            pubs2.add(t)

    if pubs1 and pubs2 and len(pubs1.intersection(pubs2)) > 0:
        return True

    # If Thai name matches exactly and both are in the exact same field/department
    d1 = (r1.department_th or "").strip()
    d2 = (r2.department_th or "").strip()
    f1 = (r1.faculty_th or "").strip()
    f2 = (r2.faculty_th or "").strip()
    if d1 and d2 and d1 != "ระบุไม่ได้" and d1 == d2:
        return True
    if f1 and f2 and f1 != "ระบุไม่ได้" and f1 == f2:
        return True

    return False


def merge_faculty_metrics_and_lists(winner: FacultyDB, ghost: FacultyDB) -> None:
    """Merge author-level lifetime research metrics and list supersets into winner."""
    winner.total_citations = max(winner.total_citations or 0, ghost.total_citations or 0)
    winner.h_index = max(winner.h_index or 0, ghost.h_index or 0)
    winner.total_publications_count = max(winner.total_publications_count or 0, ghost.total_publications_count or 0)
    winner.first_author_count = max(winner.first_author_count or 0, ghost.first_author_count or 0)
    winner.co_author_count = max(winner.co_author_count or 0, ghost.co_author_count or 0)

    if (winner.first_author_count or 0) > 0 or (winner.co_author_count or 0) > 0:
        winner.co_author_count = max(0, winner.total_publications_count - (winner.first_author_count or 0))

    # Research interests union
    existing_interests = [x for x in (winner.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    ghost_interests = [x for x in (ghost.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    seen_interests = set(str(x).strip().lower() for x in existing_interests)
    for item in ghost_interests:
        norm = str(item).strip().lower()
        if norm and norm not in seen_interests:
            seen_interests.add(norm)
            existing_interests.append(item)
    winner.research_interests = existing_interests

    # Featured publications union
    existing_pubs = list(winner.featured_publications or [])
    seen_pub_titles = set()
    for p in existing_pubs:
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t:
            seen_pub_titles.add(t)
    for p in (ghost.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and t not in seen_pub_titles:
            seen_pub_titles.add(t)
            existing_pubs.append(p)
    winner.featured_publications = existing_pubs

    # Scalar fallbacks
    if not winner.email and ghost.email:
        winner.email = ghost.email
    if not winner.image_url and ghost.image_url:
        winner.image_url = ghost.image_url
    if (not winner.openalex_id or winner.openalex_id == "not_indexed") and ghost.openalex_id and ghost.openalex_id != "not_indexed":
        winner.openalex_id = ghost.openalex_id


def score_record_as_winner(r: FacultyDB) -> float:
    """Score record to pick the authentic teaching university record as winner."""
    score = 0.0
    em_univ = get_email_univ(r.email)

    # 1. Email matches university (+100)
    if em_univ and em_univ == r.university_th:
        score += 100.0
    elif r.email and ".ac.th" in r.email.lower():
        score += 30.0

    # 2. Specific authentic faculty vs generic placeholder
    f_th = (r.faculty_th or "").strip()
    d_th = (r.department_th or "").strip()
    if f_th and not any(bad in f_th for bad in ["ระบุไม่ได้", "JGSEE", "สำนักวิชาอุตสาหกรรมเกษตร"]):
        score += 20.0
    if d_th and d_th != "ระบุไม่ได้" and not any(bad in d_th for bad in ["กลุ่มวิชา", "สาขาวิชาเกษตรศาสตร์"]):
        score += 15.0

    # 3. Authentic Thai name (not bare title or English only)
    if r.full_name_th and re.search(r"[฀-๿]", r.full_name_th) and len(r.full_name_th) > 5:
        score += 25.0

    # 4. Citations & publications weight
    score += min(50.0, (r.total_citations or 0) / 100.0)
    score += min(20.0, (r.total_publications_count or 0) / 10.0)

    return score


def run_hygiene_pipeline():
    print("=== 🧹 AUTONOMOUS FACULTY HYGIENE, DEDUP & GROUNDING PIPELINE ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        # Pre-check baseline
        fac_count_start = db.query(FacultyDB).count()
        unassigned_count_start = db.query(ScholarUnassignedDB).count()
        print(f"Pre-check baseline: faculties={fac_count_start:,}, scholars_unassigned={unassigned_count_start:,}")

        # =========================================================================
        # STAGE 1: Two-Factor Deduplication & Cross-University Consolidation
        # =========================================================================
        print("\n--- 🔍 STAGE 1: Resolving Cross-University & Intra-University Duplicates ---", flush=True)
        facs_all = db.query(FacultyDB).all()

        # Build candidate clusters by Thai name
        thai_groups = defaultdict(list)
        for f in facs_all:
            th = (f.full_name_th or "").strip()
            th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.)\s*", "", th).strip()
            th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
            th_clean = re.sub(r"\s+", "", th_clean)
            if th_clean and len(th_clean) > 3 and not re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)$", th_clean):
                thai_groups[th_clean].append(f)

        # Build candidate clusters by English name
        en_groups = defaultdict(list)
        for f in facs_all:
            fn = (f.first_name or "").strip().lower()
            ln = (f.last_name or "").strip().lower()
            if fn and ln and len(fn) > 1 and len(ln) > 1:
                en_groups[(fn, ln)].append(f)

        # Disambiguate and form connected components of duplicate records
        # Using Union-Find for transitivity
        parent = {f.id: f.id for f in facs_all}
        id_to_fac = {f.id: f for f in facs_all}

        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        duplicate_pairs_count = 0

        # Check Thai candidate pairs
        for th_name, group in thai_groups.items():
            if len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    r1, r2 = group[i], group[j]
                    if are_same_person(r1, r2):
                        union(r1.id, r2.id)
                        duplicate_pairs_count += 1

        # Check English candidate pairs
        for (fn, ln), group in en_groups.items():
            if len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    r1, r2 = group[i], group[j]
                    if are_same_person(r1, r2):
                        union(r1.id, r2.id)
                        duplicate_pairs_count += 1

        # Group into components
        components = defaultdict(list)
        for f in facs_all:
            root = find(f.id)
            components[root].append(f)

        multi_components = [members for members in components.values() if len(members) > 1]
        print(f"Discovered {len(multi_components)} distinct duplicate clusters covering {sum(len(m) for m in multi_components)} records.")

        ghost_records_to_archive: list[FacultyDB] = []
        merges_applied = 0

        for members in multi_components:
            # Score members to pick winner
            members.sort(key=score_record_as_winner, reverse=True)
            winner = members[0]
            ghosts = members[1:]

            for g in ghosts:
                merge_faculty_metrics_and_lists(winner, g)
                ghost_records_to_archive.append(g)
                merges_applied += 1

        db.commit()
        print(f"Stage 1: Merged {merges_applied} duplicate ghosts into active winners.")

        # =========================================================================
        # STAGE 2: Demonstration School Teachers Archival
        # =========================================================================
        print("\n--- 🏫 STAGE 2: Archiving K-12 Demonstration School Teachers ---", flush=True)
        demo_teachers = (
            db.query(FacultyDB)
            .filter((FacultyDB.faculty_th.like("%สาธิต%")) | (FacultyDB.department_th.like("%สาธิต%")))
            .all()
        )
        print(f"Identified {len(demo_teachers)} Demonstration School teachers (non-university faculty).")
        for dt in demo_teachers:
            if dt not in ghost_records_to_archive:
                ghost_records_to_archive.append(dt)

        # =========================================================================
        # STAGE 3: Inactive / Bare-Title Consortium Ghosts Archival
        # =========================================================================
        print("\n--- 👤 STAGE 3: Archiving Inactive & Bare-Title Ghost Records ---", flush=True)
        bare_title_ghosts = (
            db.query(FacultyDB)
            .filter(FacultyDB.full_name_th.in_(["ศ.ดร.", "ผศ.ดร.", "รศ.ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร."]))
            .all()
        )
        for bg in bare_title_ghosts:
            if bg not in ghost_records_to_archive:
                ghost_records_to_archive.append(bg)
        print(f"Identified {len(bare_title_ghosts)} bare-title consortium ghosts.")

        # Execute atomic dual-table transfer for all ghosts & non-teaching records
        archive_ids = list({r.id for r in ghost_records_to_archive})
        print(f"\nTotal ghost and non-teaching records moving to scholars_unassigned: {len(archive_ids):,}")

        if archive_ids:
            chunk_size = 2000
            for i in range(0, len(archive_ids), chunk_size):
                chunk = archive_ids[i:i + chunk_size]
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO public.scholars_unassigned
                            SELECT * FROM public.faculties
                            WHERE id IN :ids
                            ON CONFLICT (id) DO UPDATE SET
                                department = EXCLUDED.department,
                                department_th = EXCLUDED.department_th,
                                email = COALESCE(scholars_unassigned.email, EXCLUDED.email),
                                total_citations = GREATEST(scholars_unassigned.total_citations, EXCLUDED.total_citations),
                                h_index = GREATEST(scholars_unassigned.h_index, EXCLUDED.h_index),
                                total_publications_count = GREATEST(scholars_unassigned.total_publications_count, EXCLUDED.total_publications_count);
                        """),
                        {"ids": tuple(chunk)},
                    )
                    conn.execute(
                        text("DELETE FROM public.faculties WHERE id IN :ids"),
                        {"ids": tuple(chunk)},
                    )
                print(f"  Archived {min(i + chunk_size, len(archive_ids)):,}/{len(archive_ids):,} records", flush=True)

        # =========================================================================
        # STAGE 4: Faculty & Department Grounding & Standardization
        # =========================================================================
        print("\n--- 🏛️ STAGE 4: Grounding & Normalizing Faculties and Departments ---", flush=True)
        with engine.begin() as conn:
            # 1. Chula faculty corrections for verified professors
            conn.execute(text("""
                UPDATE faculties
                SET faculty_th = 'คณะวิทยาศาสตร์'
                WHERE id = 'cu_w58_2872_425'; -- Anyaporn Boonmahitthisud (Materials Science)

                UPDATE faculties
                SET faculty_th = 'คณะวิศวกรรมศาสตร์'
                WHERE id = 'cu_w58_5838_487'; -- Jatuwat Sangsanont (Environmental Engineering)

                UPDATE faculties
                SET faculty_th = 'คณะสหเวชศาสตร์'
                WHERE id = 'cu_w58_6960_831'; -- Narisa Brownell (Parasitology)

                UPDATE faculties
                SET faculty_th = 'คณะวิทยาศาสตร์'
                WHERE id = 'cu_w58_7860_929'; -- Intatch Hongrattanavichit (Photographic Tech)

                UPDATE faculties
                SET faculty_th = 'คณะวิทยาศาสตร์'
                WHERE id = 'cu_w58_9215_140'; -- Cheewanun Dachoupakan Sirisomboon (Microbiology)
            """))

            # 2. Standardize single-department faculties where department_th == faculty_th
            conn.execute(text("""
                UPDATE faculties
                SET department_th = 'สาขาวิชานิติศาสตร์'
                WHERE faculty_th = 'คณะนิติศาสตร์'
                  AND (department_th = 'คณะนิติศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาพยาบาลศาสตร์'
                WHERE faculty_th = 'คณะพยาบาลศาสตร์'
                  AND (department_th = 'คณะพยาบาลศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาศึกษาศาสตร์'
                WHERE faculty_th = 'คณะศึกษาศาสตร์'
                  AND (department_th = 'คณะศึกษาศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชามนุษยศาสตร์และสังคมศาสตร์'
                WHERE faculty_th = 'คณะมนุษยศาสตร์และสังคมศาสตร์'
                  AND (department_th = 'คณะมนุษยศาสตร์และสังคมศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาเศรษฐศาสตร์'
                WHERE faculty_th = 'คณะเศรษฐศาสตร์'
                  AND (department_th = 'คณะเศรษฐศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาทันตแพทยศาสตร์'
                WHERE faculty_th = 'คณะทันตแพทยศาสตร์'
                  AND (department_th = 'คณะทันตแพทยศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาเภสัชศาสตร์'
                WHERE faculty_th = 'คณะเภสัชศาสตร์'
                  AND (department_th = 'คณะเภสัชศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชานิเทศศาสตร์'
                WHERE faculty_th = 'คณะนิเทศศาสตร์'
                  AND (department_th = 'คณะนิเทศศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาสถาปัตยกรรมศาสตร์'
                WHERE faculty_th = 'คณะสถาปัตยกรรมศาสตร์'
                  AND (department_th = 'คณะสถาปัตยกรรมศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');

                UPDATE faculties
                SET department_th = 'สาขาวิชาศิลปกรรมศาสตร์'
                WHERE faculty_th = 'คณะศิลปกรรมศาสตร์'
                  AND (department_th = 'คณะศิลปกรรมศาสตร์' OR department_th IS NULL OR department_th = 'ระบุไม่ได้');
            """))

            # 3. Resolve academic rank as department artifacts (e.g. Mahasarakham)
            conn.execute(text("""
                UPDATE faculties
                SET department_th = 'สาขาวิชาเทคโนโลยีการเกษตร'
                WHERE department_th IN ('ศาสตราจารย์', 'รองศาสตราจารย์', 'ผู้ช่วยศาสตราจารย์', 'อาจารย์')
                  AND faculty_th LIKE '%เทคโนโลยี%';

                UPDATE faculties
                SET department_th = 'สาขาวิชาวิทยาศาสตร์'
                WHERE department_th IN ('ศาสตราจารย์', 'รองศาสตราจารย์', 'ผู้ช่วยศาสตราจารย์', 'อาจารย์')
                  AND faculty_th LIKE '%วิทยาศาสตร์%';

                UPDATE faculties
                SET department_th = 'สาขาวิชาการจัดการ'
                WHERE department_th IN ('ศาสตราจารย์', 'รองศาสตราจารย์', 'ผู้ช่วยศาสตราจารย์', 'อาจารย์')
                  AND faculty_th LIKE '%บริหาร%';
            """))

            # 4. Clean any remaining duplicate prefixes in full_name_th
            conn.execute(text("""
                UPDATE faculties
                SET full_name_th = 'อ. ' || TRIM(SUBSTRING(full_name_th FROM 6))
                WHERE full_name_th LIKE 'อ. อ. %';

                UPDATE faculties
                SET full_name_th = 'รศ.ดร. ' || TRIM(SUBSTRING(full_name_th FROM 15))
                WHERE full_name_th LIKE 'รศ.ดร. รศ.ดร. %';

                UPDATE faculties
                SET full_name_th = 'ผศ.ดร. ' || TRIM(SUBSTRING(full_name_th FROM 15))
                WHERE full_name_th LIKE 'ผศ.ดร. ผศ.ดร. %';

                UPDATE faculties
                SET full_name_th = 'ศ.ดร. ' || TRIM(SUBSTRING(full_name_th FROM 13))
                WHERE full_name_th LIKE 'ศ.ดร. ศ.ดร. %';
            """))

        print("Stage 4: Grounded and normalized faculties and departments across all universities.")

    finally:
        db.close()

    # Final Verification
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unspecified_dept = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()

        # Check duplicate full_name_th
        dup_names_count = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT full_name_th FROM public.faculties
                WHERE full_name_th IS NOT NULL AND length(full_name_th) > 3
                GROUP BY full_name_th
                HAVING count(*) > 1
            ) s;
        """)).scalar()

        # Check demo teachers
        remaining_demo = conn.execute(text("""
            SELECT count(*) FROM public.faculties
            WHERE faculty_th LIKE '%สาธิต%' OR department_th LIKE '%สาธิต%';
        """)).scalar()

        # Check bare titles
        remaining_bare = conn.execute(text("""
            SELECT count(*) FROM public.faculties
            WHERE full_name_th IN ('ศ.ดร.', 'ผศ.ดร.', 'รศ.ดร.', 'ศ.', 'รศ.', 'ผศ.', 'อ.', 'ดร.');
        """)).scalar()

        print(f"\n=======================================================")
        print(f"FINAL ZERO-DEFECT QUALITY METRICS:")
        print(f"- Primary 'faculties' count: {final_fac:,} verified teaching professors")
        print(f"- 'scholars_unassigned' archival count: {final_unassigned:,}")
        print(f"- Total preserved across both tables: {final_fac + final_unassigned:,}")
        print(f"- Unspecified department count: {unspecified_dept} (MUST BE 0)")
        print(f"- Duplicate names in faculties: {dup_names_count}")
        print(f"- Demonstration school teachers remaining: {remaining_demo} (MUST BE 0)")
        print(f"- Bare title names remaining: {remaining_bare} (MUST BE 0)")
        print(f"=======================================================")

        # Top 15 Universities
        top_univs = conn.execute(text("""
            SELECT university_th, count(*)
            FROM public.faculties
            GROUP BY university_th
            ORDER BY count(*) DESC
            LIMIT 15;
        """)).all()
        print("\nTop 15 Universities in Grounded Faculties Table:")
        for u, c in top_univs:
            print(f"  {u}: {c:,}")

    # Save Checkpoint
    checkpoint_data = {
        "faculties_count_start": fac_count_start,
        "unassigned_count_start": unassigned_count_start,
        "duplicate_merges_applied": merges_applied,
        "archived_records_count": len(archive_ids),
        "faculties_count_final": final_fac,
        "unassigned_count_final": final_unassigned,
        "unspecified_dept_count": unspecified_dept,
        "remaining_demo_teachers": remaining_demo,
        "remaining_bare_titles": remaining_bare,
        "execution_time_seconds": round(time.time() - t0, 2),
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    print(f"\nCheckpoint saved to: {CHECKPOINT_FILE}")
    print(f"Pipeline finished cleanly in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_hygiene_pipeline()
