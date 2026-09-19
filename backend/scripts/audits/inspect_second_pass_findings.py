"""Inspect all irregularities found in the second-pass exhaustive scan:
1. English university name mismatches vs canonical mapping
2. Cross-university profile URLs and image URLs
3. Thaksin University MUSE ("Faculty of Music" / "คณะดุริยางคศาสตร์") faculty and duplicate records
4. Cross-university duplicate faculty records (same Thai name across different universities)
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer
from urllib.parse import urlparse
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

TH_TO_EN_CANONICAL = {
    "จุฬาลงกรณ์มหาวิทยาลัย": "Chulalongkorn University",
    "มหาวิทยาลัยเกษตรศาสตร์": "Kasetsart University",
    "มหาวิทยาลัยเชียงใหม่": "Chiang Mai University",
    "มหาวิทยาลัยมหิดล": "Mahidol University",
    "มหาวิทยาลัยธรรมศาสตร์": "Thammasat University",
    "มหาวิทยาลัยขอนแก่น": "Khon Kaen University",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": "King Mongkut's Institute of Technology Ladkrabang",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": "King Mongkut's University of Technology Thonburi",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": "King Mongkut's University of Technology North Bangkok",
    "มหาวิทยาลัยศิลปากร": "Silpakorn University",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "Srinakharinwirot University",
    "มหาวิทยาลัยอุบลราชธานี": "Ubon Ratchathani University",
    "มหาวิทยาลัยนเรศวร": "Naresuan University",
    "มหาวิทยาลัยบูรพา": "Burapha University",
    "มหาวิทยาลัยแม่ฟ้าหลวง": "Mae Fah Luang University",
    "มหาวิทยาลัยแม่โจ้": "Maejo University",
    "มหาวิทยาลัยวลัยลักษณ์": "Walailak University",
    "มหาวิทยาลัยพะเยา": "University of Phayao",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": "Suranaree University of Technology",
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": "National Institute of Development Administration",
    "มหาวิทยาลัยทักษิณ": "Thaksin University",
    "มหาวิทยาลัยรามคำแหง": "Ramkhamhaeng University",
    "มหาวิทยาลัยมหาสารคาม": "Mahasarakham University",
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": "Suan Sunandha Rajabhat University",
    "ราชวิทยาลัยจุฬาภรณ์": "Chulabhorn Royal Academy",
}

UNI_DOMAIN_MAP = {
    "จุฬาลงกรณ์มหาวิทยาลัย": ["chula.ac.th", "sasin.edu", "chulavrc.org", "chula.md"],
    "มหาวิทยาลัยเกษตรศาสตร์": ["ku.th", "ku.ac.th"],
    "มหาวิทยาลัยเชียงใหม่": ["cmu.ac.th", "chiangmai.ac.th"],
    "มหาวิทยาลัยมหิดล": ["mahidol.ac.th", "mahidol.edu"],
    "มหาวิทยาลัยธรรมศาสตร์": ["tu.ac.th", "siit.tu.ac.th"],
    "มหาวิทยาลัยขอนแก่น": ["kku.ac.th"],
    "มหาวิทยาลัยสงขลานครินทร์": ["psu.ac.th"],
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": ["kmitl.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ["kmutt.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ["kmutnb.ac.th", "tggs-bangkok.org"],
    "มหาวิทยาลัยศิลปากร": ["su.ac.th"],
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": ["swu.ac.th", "g.swu.ac.th"],
    "มหาวิทยาลัยอุบลราชธานี": ["ubu.ac.th"],
    "มหาวิทยาลัยนเรศวร": ["nu.ac.th"],
    "มหาวิทยาลัยบูรพา": ["buu.ac.th"],
    "มหาวิทยาลัยแม่ฟ้าหลวง": ["mfu.ac.th"],
    "มหาวิทยาลัยแม่โจ้": ["mju.ac.th"],
    "มหาวิทยาลัยวลัยลักษณ์": ["wu.ac.th"],
    "มหาวิทยาลัยพะเยา": ["up.ac.th"],
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": ["sut.ac.th"],
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": ["nida.ac.th"],
    "มหาวิทยาลัยทักษิณ": ["tsu.ac.th"],
    "มหาวิทยาลัยสงฆ์": ["mcu.ac.th", "mbu.ac.th"],
    "มหาวิทยาลัยมหาสารคาม": ["msu.ac.th"],
    "มหาวิทยาลัยรามคำแหง": ["ru.ac.th"],
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": ["ssru.ac.th"],
    "ราชวิทยาลัยจุฬาภรณ์": ["cra.ac.th"],
}


def main():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        print(f"Total faculty records: {len(faculties)}")

        # 1. English university mismatches
        en_mismatches = []
        for f in faculties:
            exp_en = TH_TO_EN_CANONICAL.get(f.university_th)
            if exp_en and f.university != exp_en:
                en_mismatches.append(f)

        print(f"\n1. English University Desynchronizations: {len(en_mismatches)}")
        breakdown = Counter((f.university_th, f.university) for f in en_mismatches)
        for (th, en), count in breakdown.most_common():
            print(f"   - {count} records: '{th}' -> currently '{en}' (expected: '{TH_TO_EN_CANONICAL[th]}')")

        # 2. Cross-University Profile URLs and Image URLs
        print("\n2. Cross-University URLs:")
        cross_profiles = []
        cross_images = []
        for f in faculties:
            uni = f.university_th or ""
            expected_domains = None
            for k, doms in UNI_DOMAIN_MAP.items():
                if k in uni:
                    expected_domains = doms
                    break

            if not expected_domains:
                continue

            # check profile_url
            p_url = f.profile_url or ""
            if p_url:
                try:
                    host = (urlparse(p_url).hostname or "").lower()
                    if host:
                        # check if host matches any other university's domain
                        for other_u, other_doms in UNI_DOMAIN_MAP.items():
                            if other_u != uni:
                                if any(host == d or host.endswith("." + d) for d in other_doms):
                                    # verify it doesn't match current uni's domains
                                    if not any(host == d or host.endswith("." + d) for d in expected_domains):
                                        cross_profiles.append((f.id, f.full_name_th, uni, f.faculty_th, p_url, other_u, host))
                                        break
                except Exception:
                    pass

            # check image_url
            img_url = f.image_url or ""
            if img_url:
                try:
                    host = (urlparse(img_url).hostname or "").lower()
                    if host:
                        for other_u, other_doms in UNI_DOMAIN_MAP.items():
                            if other_u != uni:
                                if any(host == d or host.endswith("." + d) for d in other_doms):
                                    if not any(host == d or host.endswith("." + d) for d in expected_domains):
                                        cross_images.append((f.id, f.full_name_th, uni, f.faculty_th, img_url, other_u, host))
                                        break
                except Exception:
                    pass

        print(f"   - Cross-University Profile URLs: {len(cross_profiles)}")
        for r in cross_profiles:
            print(f"     * {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")

        print(f"   - Cross-University Image URLs: {len(cross_images)}")
        for r in cross_images:
            print(f"     * {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")

        # 3. Thaksin University MUSE ("Faculty of Music" / "คณะดุริยางคศาสตร์")
        print("\n3. Thaksin University 'คณะดุริยางคศาสตร์':")
        tsu_music = [f for f in faculties if f.university_th == "มหาวิทยาลัยทักษิณ" and f.faculty_th == "คณะดุริยางคศาสตร์"]
        print(f"   - Total records labeled 'คณะดุริยางคศาสตร์': {len(tsu_music)}")
        for f in tsu_music:
            print(f"     * {f.id} | {f.full_name_th} | email={f.email} | dept={f.department_th} | interests={f.research_interests}")

        # Check duplicate pairs between tsu_music and other Thaksin records
        tsu_all = [f for f in faculties if f.university_th == "มหาวิทยาลัยทักษิณ"]
        name_map = {}
        for f in tsu_all:
            norm_name = (f.full_name_th or "").strip()
            name_map.setdefault(norm_name, []).append(f)

        duplicates = {name: recs for name, recs in name_map.items() if len(recs) > 1}
        print(f"\n   - Duplicate Thai Names within Thaksin University: {len(duplicates)}")
        for name, recs in duplicates.items():
            print(f"     * {name} ({len(recs)} records):")
            for r in recs:
                print(f"       - ID: {r.id} | Fac: {r.faculty_th} | Email: {r.email} | Citations: {r.total_citations} | H-index: {r.h_index}")

        # 4. Cross-University Duplicate Faculty Check (same person appearing in multiple universities)
        print("\n4. Cross-University Duplicate Persons (same full_name_th across different universities):")
        all_name_map = {}
        for f in faculties:
            # normalize name: remove titles if needed, or exact full_name_th
            raw_name = (f.full_name_th or "").strip()
            if raw_name:
                all_name_map.setdefault(raw_name, []).append(f)

        cross_uni_dups = []
        for name, recs in all_name_map.items():
            unis = set(r.university_th for r in recs)
            if len(unis) > 1:
                cross_uni_dups.append((name, recs))

        print(f"   - Total cross-university name duplicates: {len(cross_uni_dups)}")
        for name, recs in cross_uni_dups:
            print(f"     * {name} ({len(recs)} records):")
            for r in recs:
                print(f"       - ID: {r.id} | Uni: {r.university_th} | Fac: {r.faculty_th} | Email: {r.email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
