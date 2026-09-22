# -*- coding: utf-8 -*-
"""
Test Simulation of Cross-University and Intra-University Deduplication
====================================================================
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

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
    "nida.ac.th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์",
    "ru.ac.th": "มหาวิทยาลัยรามคำแหง",
    "stou.ac.th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
}


def get_email_univ(email: str | None) -> str | None:
    if not email:
        return None
    em = email.lower().strip()
    for domain, univ in EMAIL_DOMAIN_MAP.items():
        if domain in em:
            return univ
    return None


db = SessionLocal()
try:
    facs = db.query(FacultyDB).all()
    print(f"Total faculties: {len(facs):,}")

    # Group by normalized Thai name AND English name
    clusters = defaultdict(list)
    for f in facs:
        th = (f.full_name_th or "").strip()
        th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.)\s*", "", th).strip()
        th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
        th_clean = re.sub(r"\s+", "", th_clean)

        fn = (f.first_name or "").strip().lower()
        ln = (f.last_name or "").strip().lower()

        # Primary key: clean Thai name if available
        if th_clean and len(th_clean) > 3 and not re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)$", th_clean):
            clusters[f"th:{th_clean}"].append(f)
        elif fn and ln and len(fn) > 1 and len(ln) > 1:
            clusters[f"en:{fn}_{ln}"].append(f)

    multi_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
    print(f"Total multi-row clusters: {len(multi_clusters)}")

    resolved_winners = {}
    ghosts_to_archive = []

    for ckey, rows in multi_clusters.items():
        # Score each row to determine the authentic winner
        scored_rows = []
        for r in rows:
            score = 0
            em_univ = get_email_univ(r.email)

            # 1. Email matches university (+100)
            if em_univ and em_univ == r.university_th:
                score += 100
            elif r.email and ".ac.th" in r.email.lower():
                score += 30

            # 2. Specific authentic faculty vs generic placeholder
            f_th = (r.faculty_th or "").strip()
            d_th = (r.department_th or "").strip()
            if f_th and not any(bad in f_th for bad in ["ระบุไม่ได้", "JGSEE", "สำนักวิชาอุตสาหกรรมเกษตร"]):
                score += 20
            if d_th and d_th != "ระบุไม่ได้" and not any(bad in d_th for bad in ["กลุ่มวิชา", "สาขาวิชาเกษตรศาสตร์"]):
                score += 15

            # 3. Authentic Thai name (not bare title or English only)
            if r.full_name_th and re.search(r"[฀-๿]", r.full_name_th) and len(r.full_name_th) > 5:
                score += 25

            # 4. Citations & publications weight
            score += min(50, (r.total_citations or 0) / 100)
            score += min(20, (r.total_publications_count or 0) / 10)

            scored_rows.append((score, r))

        scored_rows.sort(key=lambda x: x[0], reverse=True)
        winner = scored_rows[0][1]
        resolved_winners[ckey] = winner

        for sc, r in scored_rows[1:]:
            ghosts_to_archive.append((winner, r))

    print(f"Simulation result:")
    print(f"- Winners retained: {len(resolved_winners)}")
    print(f"- Ghost rows to archive into scholars_unassigned: {len(ghosts_to_archive)}")

    # Show first 15 examples
    print("\nSample Winner vs Ghost resolutions:")
    for w, g in ghosts_to_archive[:15]:
        print(f"WINNER: {w.id} | {w.full_name_th} ({w.first_name} {w.last_name}) @ {w.university_th} ({w.faculty_th} - {w.department_th}) [Email: {w.email}]")
        print(f" GHOST: {g.id} | {g.full_name_th} ({g.first_name} {g.last_name}) @ {g.university_th} ({g.faculty_th} - {g.department_th}) [Email: {g.email}]")
        print("-" * 80)

finally:
    db.close()
