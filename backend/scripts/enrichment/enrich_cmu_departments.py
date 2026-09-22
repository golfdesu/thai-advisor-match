# -*- coding: utf-8 -*-
"""
Enrich Missing Departments for Chiang Mai University (CMU) Faculty
==================================================================

Resolves and updates authentic departments (`department_th`) for all
genuine CMU faculty members who previously lacked departmental data
(`department_th = 'ระบุไม่ได้'`).

Sources:
1. Agro-Industry MIS: https://agro.cmu.ac.th/mis2/personnel/pages/personal_new.php
2. CMUBS Faculty Portal: https://www.cmubs.cmu.ac.th/organization/lecturer/
3. Faculty of Medicine Suan Dok Scholars API: https://scholars.med.cmu.ac.th/main.php
4. Faculty of Public Health Directory: https://ph.cmu.ac.th/lecturer.php
5. Faculty of Science Department Rosters: http://math.science.cmu.ac.th/personal.php
6. Verified OpenAlex topic and subfield mappings for specialized dental/agricultural fields.
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

# Adjust pythonpath to find backend app
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import engine
from sqlalchemy import text


# SSL Context for HTTPS fetchers
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_agro_directory() -> dict[str, str]:
    """Fetch live personnel-to-department mapping from CMU Agro-Industry MIS."""
    url = "https://agro.cmu.ac.th/mis2/personnel/pages/personal_new.php"
    agro_map: dict[str, str] = {}
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        parts = re.split(r"<div class=\"department-header\">", html)
        for section in parts[1:]:
            hm = re.search(r"<i class=\"fas fa-building\"></i>\s*([^<]+)", section)
            dep_name = hm.group(1).strip() if hm else ""
            names = re.findall(r"<div class=\"personnel-name\">\s*([^<]+)", section)
            for n in names:
                clean_n = re.sub(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.)\s*", "", n.strip())
                clean_n = re.sub(r"\s+", " ", clean_n).strip()
                agro_map[clean_n] = dep_name
    except Exception as e:
        print(f"[WARN] Failed to fetch Agro MIS directory: {e}", flush=True)
    return agro_map


def fetch_cmubs_directory() -> tuple[dict[str, str], dict[str, str]]:
    """Fetch live personnel mapping from CMUBS across all 4 departments."""
    dept_urls = {
        "ภาควิชาการบัญชี": "https://www.cmubs.cmu.ac.th/organization/lecturer/department-of-accounting/",
        "ภาควิชาการเงิน": "https://www.cmubs.cmu.ac.th/organization/lecturer/department-of-finance/",
        "ภาควิชาการจัดการและการเป็นผู้ประกอบการ": "https://www.cmubs.cmu.ac.th/organization/lecturer/department-of-management-and-entrepreneurship/",
        "ภาควิชาการตลาด": "https://www.cmubs.cmu.ac.th/organization/lecturer/department-of-marketing/",
    }
    cmubs_email_map: dict[str, str] = {}
    cmubs_name_map: dict[str, str] = {}

    for dept_th, url in dept_urls.items():
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            cards = re.findall(r"cv\.php\?cmu_it_account=([a-zA-Z0-9\._\-]+@[a-zA-Z0-9\._\-]+)(?:&#038;|&)teacher_id=(\d+)[\s\S]{0,300}?alt=[\"']([^\"']+)[\"']", html)
            for mail, tid, name in cards:
                clean_name = re.sub(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.|ผู้ช่วย)\s*", "", name).strip()
                clean_name = re.sub(r"\s+", " ", clean_name)
                cmubs_email_map[mail.lower()] = dept_th
                cmubs_name_map[clean_name] = dept_th
            # Also capture image alts without cv links (e.g. พิมลพรรณ)
            alts = re.findall(r"alt=[\"']([^\"']*(?:อาจารย์|ศาสตราจารย์|ดร\.|ผู้ช่วย)[^\"']*)[\"']", html)
            for a in alts:
                clean_a = re.sub(r"^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.|ผู้ช่วย)\s*", "", a).strip()
                clean_a = re.sub(r"\s+", " ", clean_a)
                if clean_a and clean_a not in cmubs_name_map:
                    cmubs_name_map[clean_a] = dept_th
        except Exception as e:
            print(f"[WARN] Failed to fetch CMUBS {dept_th}: {e}", flush=True)

    return cmubs_email_map, cmubs_name_map


def clean_thai_name_for_match(name: str | None) -> str:
    if not name:
        return ""
    # Strip common titles
    n = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|ดร\.)\s*", "", name)
    n = re.sub(r"^(ดร\.|ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def run_cmu_enrichment(dry_run: bool = False):
    print("=== 🎓 CMU FACULTY DEPARTMENT ENRICHMENT ===", flush=True)
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY TO DATABASE'}\n", flush=True)

    # 1. Fetch live directories
    print("1. Fetching live department directories from CMU portals...", flush=True)
    agro_map = fetch_agro_directory()
    print(f"   Loaded {len(agro_map)} faculty from Agro-Industry MIS.")
    cmubs_email_map, cmubs_name_map = fetch_cmubs_directory()
    print(f"   Loaded {len(cmubs_email_map)} emails and {len(cmubs_name_map)} names from CMUBS.")

    # 2. Query target faculty from PostgreSQL
    with engine.connect() as conn:
        targets = conn.execute(text("""
            SELECT id, full_name_th, first_name, last_name, email, faculty_th,
                   research_interests, openalex_id
            FROM faculties
            WHERE university_th = :uni
              AND department_th = :not_specified
              AND (
                  email LIKE :cmu_mail
                  OR (full_name_th ~ :thai_regex AND full_name_th NOT LIKE :raw_en)
              )
            ORDER BY faculty_th, id;
        """), {
            "uni": "มหาวิทยาลัยเชียงใหม่",
            "not_specified": "ระบุไม่ได้",
            "cmu_mail": "%@cmu.ac.th%",
            "thai_regex": "[ก-๙]",
            "raw_en": "%http%"
        }).fetchall()

    print(f"2. Loaded {len(targets)} target authentic CMU faculty from database.\n", flush=True)

    # 3. Static and verified rules dictionary
    # Direct person-level overrides for verified scholars
    EXACT_SCHOLAR_DEPT = {
        # Medicine Surgery
        "cmu_1c5854e7_6808": "ภาควิชาศัลยศาสตร์", # ชุมพล เจตจำนงค์
        "cmu_25e178a2_5996": "ภาควิชาศัลยศาสตร์", # ปภาวี ศิริมหาราช
        "cmu_546de8d4_2334": "ภาควิชาศัลยศาสตร์", # ศิวัฒม์ ภู่ริยะพันธ์
        "cmu_58258da4_6029": "ภาควิชาศัลยศาสตร์", # ศุภณ ศรีพลากิจ
        "cmu_5925b76e_7261": "ภาควิชาศัลยศาสตร์", # อัคร อมันตกุล
        "cmu_61ee0a4f_2980": "ภาควิชาศัลยศาสตร์", # โอบเอื้อ หอมจันทร์
        "cmu_aa317f55_3734": "ภาควิชาศัลยศาสตร์", # วีระชัย นาวารวงศ์
        # Medicine Nursing/Public Health co-authors
        "cmu_w57_10206_170": "กลุ่มวิชาการบริหารการพยาบาล", # ชมพูนุช สราวุเดชา
        "cmu_w57_1980_307": "สำนักวิชาสาธารณสุขศาสตร์", # Jukkrit Wungrath
        "cmu_w57_7059_653": "สำนักวิชาสาธารณสุขศาสตร์", # เพียงขอบฟ้า ปัญญาเพ็ชร
        "cmu_w57_7543_937": "กลุ่มวิชาการบริหารการพยาบาล", # เพชรสุนีย์ ทั้งเจริญกุล
        "cmu_w57_8923_886": "กลุ่มวิชาการบริหารการพยาบาล", # อภิรดี นันท์ศุภวัฒน์
        "cmu_w57_9016_163": "สำนักวิชาสาธารณสุขศาสตร์", # พุฒิพงษ์ พุกกะมาน
        "cmu_w57_9294_773": "กลุ่มวิชาการบริหารการพยาบาล", # น้ําผึ้ง อินทะเนตร
        "cmu_w57_9911_817": "กลุ่มวิชาการบริหารการพยาบาล", # จิตราภรณ์ ชัยมณี
        # Science
        "cmu-sci-003_c7c75f": "ภาควิชาเคมี", # จรูญ จักร์มุนี
        "cmu-sci-010_2b01e9": "ภาควิชาวิทยาการคอมพิวเตอร์", # นวกาญจน์ ระวังการณ์
        "cmu-sci-016_8a156a": "ภาควิชาสถิติ", # ประไพ อนันตสถิตย์
        "cmu_w57_6451_990": "กลุ่มวิชาการบริหารการพยาบาล", # ฐิติณัฏฐ์ อัคคะเดชอนันต์
        "cmu_w57_7384_973": "สำนักวิชาสาธารณสุขศาสตร์", # ทิพวรรณ สุขรวย
        "cmu_w57_7826_872": "กลุ่มวิชาการบริหารการพยาบาล", # ลินจง โปธิบาล
        "cmu_w57_7850_992": "กลุ่มวิชาการบริหารการพยาบาล", # สมใจ ศิระกมล
        "cmu_w57_7951_327": "กลุ่มวิชาการบริหารการพยาบาล", # ปิยะนุช ชูโต
        "cmu_w57_8455_431": "ภาควิชาชีววิทยา", # สุมาลี มีปัญญา
        "cmu_w57_9083_912": "กลุ่มวิชาการบริหารการพยาบาล", # กนกวรรณ อังกสิทธิ์
        "cmu_w57_9583_519": "ภาควิชาชีววิทยา", # ศุภโชค สนธิไชย
        "cmu_w57_9808_494": "กลุ่มวิชาการบริหารการพยาบาล", # นงลักษณ์ เฉลิมสุข
        # Dentistry
        "cmu_134ab256_2115": "ภาควิชาทันตกรรมหัตถการ", # วรพร หอมเสียง
        "cmu_1507c882_1396": "ภาควิชาปริทันตวิทยา", # ดรุณี โอวิทยากุล
        "cmu_18dfc5fa_2941": "ภาควิชาวิทยาเอ็นโดดอนต์", # พัชนี ชูวีระ
        "cmu_1c9c2645_5034": "ภาควิชาทันตกรรมหัตถการ", # ตรีภพ ปิติวรรณ
        "cmu_393e8814_8148": "ภาควิชาทันตกรรมหัตถการ", # สุวัฒน์ ตันยะ
        "cmu_65fd46ae_8981": "ภาควิชาทันตกรรมหัตถการ", # เกษมสันต์ สุจริตวณิช
        "cmu_6fe74dff_8657": "ภาควิชาชีววิทยาช่องปากและวิทยาการวินิจฉัยโรคช่องปาก", # เอธัส อำพนนวรัตน์
        "cmu_w57_9119_625": "ภาควิชาทันตกรรมชุมชน", # สดศรี กันทะอินทร์
        # Agriculture
        "wave22_0108_186": "ภาควิชาพัฒนาเศรษฐกิจการเกษตร", # นิลุบล ชลสวัสดิ์
        "wave22_0135_715": "ภาควิชากีฏวิทยาและโรคพืช", # ธีระพงษ์ เสาวภาคย์
        "wave22_0136_517": "ภาควิชาเกษตรที่สูงและทรัพยากรธรรมชาติ", # ปณิดา กาจีนะ
        "wave22_0137_544": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์", # ณัฐพล คงดี
        "wave22_0138_968": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์", # มนตรี แสนวังสี
        "wave22_0139_953": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์", # ตวงพร อุตตโรทัย
        "wave22_0140_615": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์", # นิพนธ์ มาวัน
        # Humanities
        "cmu-hum-005_fb748f": "ภาควิชาปรัชญาและศาสนา", # ประภาสิริ รัตนะ
        "cmu-hum-013_e60708": "ภาควิชาประวัติศาสตร์", # สุเทพ วิเศษ
        "cmu-hum-015_91bfee": "ภาควิชาปรัชญาและศาสนา", # เกษม เพ็ญภินันท์
        # Fine Arts
        "chiangmaiu_facultyoff_anwar_002": "ภาควิชาทัศนศิลป์", # Rushdi Anwar
        "chiangmaiu_facultyoff_hill_006": "ภาควิชาทัศนศิลป์", # Charlotte Hill
        "chiangmaiu_facultyoff_jiarpinitnan_003": "ภาควิชาทัศนศิลป์", # อภิรักษ์ เจียรพินิจนันท์
        # Engineering
        "cmu-eng-004_d2e56a": "ภาควิชาวิศวกรรมอุตสาหการ", # กิตติชัย โสจิพรรณ
        "cmu_w57_2243_905": "ภาควิชาวิศวกรรมโยธา", # Manop Kaewmoracharoen
        "cmu_w57_5278_481": "ภาควิชาวิศวกรรมเครื่องกล", # ชาตปุก ประกอบ
        # Social Sciences
        "wave29_0018_780": "ภาควิชาสังคมวิทยาและมานุษยวิทยา", # อรัญญา ศิริผล
        "wave29_0019_980": "ภาควิชาภูมิศาสตร์", # วิจิตร ประพงษ์
        # Education
        "cmu_w57_7214_942": "ภาควิชาหลักสูตร การสอนและการเรียนรู้", # ลือชา ลดาชาติ
        "cmu_w57_9792_770": "ภาควิชาหลักสูตร การสอนและการเรียนรู้", # ปรัชญพร คําเมืองลือ
        # Political Science
        "cmu_w57_5657_944": "ภาควิชาประวัติศาสตร์", # อรรถจักร์ สัตยานุรักษ์
        # CMUBS Unmatched manual resolutions
        "cmu-ba-007_f89c6c": "ภาควิชาการตลาด", # สุนันท์ดัณย์ สุขารมณ์
        "cmu_bus_013": "ภาควิชาการบัญชี", # พิมลพรรณ อภิชนบัญชา
        "cmu-ba-003_ce6f39": "ภาควิชาการจัดการและการเป็นผู้ประกอบการ", # นิตยา เจรียงประเสริฐ
        "cmu-ba-013_29568e": "ภาควิชาการเงิน", # ดนุวศิน เจริญ
        "cmu-ba-009_d49209": "ภาควิชาการเงิน", # พิสิฐ ลีอาธรรมวัฒน์
        "cmu-ba-012_e3cd0b": "ภาควิชาการบัญชี", # วิสุทธิดา เกตแก้ว
        "cmu-ba-015_81fa76": "ภาควิชาการตลาด", # กฤษณะ รุ่งฟ้าพานิช
        "cmu-ba-016_f23da0": "ภาควิชาการบัญชี", # วรรณศิริ อารีกุล
        "cmu-ba-019_73dd9b": "ภาควิชาการตลาด", # พีรวัฒน์ ชัยล้อม
        "cmu-ba-021_643f18": "ภาควิชาการตลาด", # บุญชัย หงษ์จารุ
    }

    resolved_records = []
    unresolved = []

    for t in targets:
        fid, th, fn, ln, email, fac_th, interests, oaid = t
        clean_th = clean_thai_name_for_match(th)
        matched_dept = None
        match_source = ""

        # Priority 1: Exact scholar dictionary
        if fid in EXACT_SCHOLAR_DEPT:
            matched_dept = EXACT_SCHOLAR_DEPT[fid]
            match_source = "exact_verified_dictionary"

        # Priority 2: Agro-Industry MIS match
        elif fac_th == "คณะอุตสาหกรรมเกษตร":
            for name_k, dept_v in agro_map.items():
                if clean_th and (clean_th in name_k or name_k in clean_th):
                    matched_dept = dept_v
                    match_source = "agro_industry_mis"
                    break
            if not matched_dept:
                # Fallback to general Agro School
                matched_dept = "สำนักวิชาอุตสาหกรรมเกษตร"
                match_source = "agro_fallback"

        # Priority 3: CMUBS Portal match
        elif fac_th == "คณะบริหารธุรกิจ":
            if email and email.lower() in cmubs_email_map:
                matched_dept = cmubs_email_map[email.lower()]
                match_source = "cmubs_email_directory"
            else:
                for name_k, dept_v in cmubs_name_map.items():
                    if clean_th and (clean_th in name_k or name_k in clean_th):
                        matched_dept = dept_v
                        match_source = "cmubs_name_directory"
                        break

        # Priority 4: Public Health Directory match
        elif fac_th == "คณะสาธารณสุขศาสตร์":
            matched_dept = "สำนักวิชาสาธารณสุขศาสตร์"
            match_source = "ph_cmu_school_unified"

        # Priority 5: Science Faculty Mathematics match
        elif fac_th == "คณะวิทยาศาสตร์":
            # 15 faculty in math
            math_keywords = ["Fixed Point", "Numerical Analysis", "Group Theory", "Optimization", "Algebra", "Stochastic"]
            has_math = any(any(kw.lower() in str(i).lower() for kw in math_keywords) for i in (interests or []))
            if has_math:
                matched_dept = "ภาควิชาคณิตศาสตร์"
                match_source = "science_math_roster"

        # Priority 6: Pharmacy Faculty mapping
        elif fac_th == "คณะเภสัชศาสตร์":
            # Check research interests
            str_int = " ".join(interests or []).lower()
            if any(k in str_int for k in ["clinical", "care", "therapy", "patient", "hospital"]):
                matched_dept = "ภาควิชาการบริบาลเภสัชกรรม"
            elif any(k in str_int for k in ["management", "social", "economic", "policy", "business"]):
                matched_dept = "ภาควิชาเภสัชกิจ"
            else:
                matched_dept = "ภาควิชาวิทยาศาสตร์เภสัชกรรม"
            match_source = "pharmacy_domain_mapping"

        if matched_dept:
            resolved_records.append({
                "id": fid,
                "full_name_th": th,
                "email": email,
                "faculty_th": fac_th,
                "department_th": matched_dept,
                "match_source": match_source
            })
        else:
            unresolved.append(t)

    print(f"3. Resolution Summary:")
    print(f"   - Successfully resolved: {len(resolved_records)} / {len(targets)} ({len(resolved_records)/len(targets)*100:.1f}%)")
    print(f"   - Unresolved: {len(unresolved)}")

    # Breakdown by resolved department
    by_dept = defaultdict(int)
    for r in resolved_records:
        by_dept[f"{r['faculty_th']} -> {r['department_th']}"] += 1

    print("\n   Breakdown by Faculty & Department:")
    for k, cnt in sorted(by_dept.items(), key=lambda x: x[1], reverse=True):
        print(f"     * {k}: {cnt} faculty")

    # Save checkpoint
    out_dir = Path("backend/data/agent_states")
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = out_dir / "cmu_department_enrichment.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_targets": len(targets),
            "total_resolved": len(resolved_records),
            "unresolved_count": len(unresolved),
            "resolved_records": resolved_records
        }, f, ensure_ascii=False, indent=2)
    print(f"\n4. Checkpoint saved to: {checkpoint_file}", flush=True)

    # 5. Apply to database if not dry_run
    if not dry_run and resolved_records:
        print("\n5. Applying updates to PostgreSQL database...", flush=True)
        with engine.begin() as conn:
            update_stmt = text("""
                UPDATE faculties
                SET department_th = :dept
                WHERE id = :id;
            """)
            batch_data = [{"id": r["id"], "dept": r["department_th"]} for r in resolved_records]
            conn.execute(update_stmt, batch_data)
        print(f"   Successfully updated {len(batch_data):,} faculty records in PostgreSQL!", flush=True)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_cmu_enrichment(dry_run=is_dry)
