"""
Builds backend/scripts/data/cmu_courses.json (project courses schema) from
the raw CMU TQF2 scrape output (cmu_tqf_list.json / cmu_tqf_details.json).

Usage:
    python build_cmu_courses_json.py
"""

import json
import logging
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
LIST_FILE = DATA_DIR / "cmu_tqf_list.json"
DETAILS_FILE = DATA_DIR / "cmu_tqf_details.json"
OUT_FILE = DATA_DIR / "cmu_courses.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build")

DEGREE_ABBREV_TH = [
    ("ปรัชญาดุษฎีบัณฑิต", "ปร.ด."),
    ("วิศวกรรมศาสตรดุษฎีบัณฑิต", "วศ.ด."),
    ("สาธารณสุขศาสตรดุษฎีบัณฑิต", "สาธารณสุขศาสตรดุษฎีบัณฑิต"),
    ("วิทยาศาสตรมหาบัณฑิต", "วท.ม."),
    ("วิศวกรรมศาสตรมหาบัณฑิต", "วศ.ม."),
    ("บริหารธุรกิจมหาบัณฑิต", "บธ.ม."),
    ("ศิลปศาสตรมหาบัณฑิต", "ศศ.ม."),
    ("สถาปัตยกรรมศาสตรมหาบัณฑิต", "สถ.ม."),
    ("สาธารณสุขศาสตรมหาบัณฑิต", "สาธารณสุขศาสตรมหาบัณฑิต"),
    ("ศึกษาศาสตรมหาบัณฑิต", "ศษ.ม."),
    ("ศิลปมหาบัณฑิต", "ศิลปมหาบัณฑิต"),
    ("นิติศาสตรมหาบัณฑิต", "น.ม."),
    ("เภสัชศาสตรมหาบัณฑิต", "เภสัชศาสตรมหาบัณฑิต"),
    ("พยาบาลศาสตรมหาบัณฑิต", "พย.ม."),
    ("รัฐประศาสนศาสตรมหาบัณฑิต", "รป.ม."),
    ("รัฐศาสตรมหาบัณฑิต", "รศ.ม."),
    ("แพทยศาสตรมหาบัณฑิต", "แพทยศาสตรมหาบัณฑิต"),
    ("ทันตแพทยศาสตรมหาบัณฑิต", "ทันตแพทยศาสตรมหาบัณฑิต"),
    ("วิทยาศาสตรบัณฑิต", "วท.บ."),
    ("วิศวกรรมศาสตรบัณฑิต", "วศ.บ."),
    ("บริหารธุรกิจบัณฑิต", "บธ.บ."),
    ("บัญชีบัณฑิต", "บช.บ."),
    ("เศรษฐศาสตรบัณฑิต", "ศษ.บ."),
    ("สถาปัตยกรรมศาสตรบัณฑิต", "สถ.บ."),
    ("ภูมิสถาปัตยกรรมศาสตรบัณฑิต", "ภูมิสถาปัตยกรรมศาสตรบัณฑิต"),
    ("ศิลปศาสตรบัณฑิต", "ศศ.บ."),
    ("สัตวแพทยศาสตรบัณฑิต", "สต.บ."),
    ("แพทยศาสตรบัณฑิต", "แพทย์บ."),
    ("ทันตแพทยศาสตรบัณฑิต", "ทันตแพทย์บ."),
    ("เภสัชศาสตรบัณฑิต", "เภสัชศาสตรบัณฑิต"),
    ("พยาบาลศาสตรบัณฑิต", "พย.บ."),
    ("เทคนิคการแพทยบัณฑิต", "เทคนิคการแพทย์บ."),
    ("รัฐประศาสนศาสตรบัณฑิต", "รป.บ."),
    ("รัฐศาสตรบัณฑิต", "รศ.บ."),
    ("นิติศาสตรบัณฑิต", "น.บ."),
    ("การศึกษาบัณฑิต", "กศ.บ."),
    ("ประกาศนียบัตรบัณฑิตชั้นสูง", "ประกาศนียบัตรบัณฑิตชั้นสูง"),
    ("ประกาศนียบัตรบัณฑิต", "ประกาศนียบัตรบัณฑิต"),
]

YEAR_WORDS = {
    "First": 1, "Second": 2, "Third": 3, "Fourth": 4,
    "Fifth": 5, "Sixth": 6, "Seventh": 7,
}

LEVEL_DURATION_DEFAULT = {
    "2": "4 ปี",
    "3": "1 ปี",
    "4": "2 ปี",
    "5": "1 ปี",
    "6": "3 ปี",
    "7": "5 ปี",
    "8": "5 ปี",
}


def degree_name_th(title_th: str) -> str:
    for full, abbr in DEGREE_ABBREV_TH:
        if full in title_th:
            return abbr
    return ""


def total_credits_from_structure(structure) -> str:
    if not structure:
        return ""
    first = structure[0]
    if "credits" in first:
        return f"{first['credits']} หน่วยกิต"
    return ""


def highlights_from_structure(structure) -> list:
    out = []
    for row in structure or []:
        sec = row.get("section", "")
        m = re.match(r"([A-D])\.\s+(.+)", sec)
        if m:
            label = re.sub(r"\s*:\s*a\s*(minimum|maximum)\s*of$", "", m.group(2), flags=re.I).strip()
            if label and label not in out:
                out.append(label)
    return out[:8]


def duration_from_study_plan(study_plan, level_code) -> str:
    max_year = 0
    for item in study_plan or []:
        y = item.get("year") or ""
        m = re.search(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh)", y)
        if m:
            max_year = max(max_year, YEAR_WORDS[m.group(1)])
        else:
            n = re.search(r"(\d+)", y)
            if n:
                max_year = max(max_year, int(n.group(1)))
    if max_year:
        return f"{max_year} ปี"
    return LEVEL_DURATION_DEFAULT.get(level_code, "")


def program_type_from_plans(plans) -> str:
    kinds, schedules = [], []
    for plan in plans or []:
        for cell in plan:
            if cell.startswith("[Tha]") or cell.startswith("[Eng]"):
                continue
            if "หลักสูตร" in cell and cell not in kinds:
                kinds.append(cell)
            elif ("ภาค" in cell or "Weekend" in cell) and cell not in schedules:
                schedules.append(cell)
    parts = kinds + schedules
    return " / ".join(parts[:4])


def clean_title_en(raw: str) -> str:
    # drop Thai-script parentheticals that CMU appends to English titles
    cleaned = re.sub(r"\([^)]*[\u0e00-\u0e7f][^)]*\)", "", raw or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def build_record(entry: dict, detail: dict | None, seq: int) -> dict:
    code = (detail or {}).get("curriculum_code") or ""
    rec_id = f"cmu_tqf_{code}" if code else f"cmu_{entry['faculty_code']}_{entry['level_code']}_{seq:03d}"
    structure = (detail or {}).get("structure") or []
    study_plan = (detail or {}).get("study_plan") or []

    description_parts = []
    name_en = clean_title_en((detail or {}).get("name_en", ""))
    degree_full = (detail or {}).get("degree_full_en") or ""
    if degree_full:
        description_parts.append(f"{degree_full}")
    credits = total_credits_from_structure(structure)
    if credits:
        description_parts.append(f"โครงสร้างหลักสูตรรวมไม่น้อยกว่า {credits}")
    dur = duration_from_study_plan(study_plan, entry["level_code"])
    if dur:
        description_parts.append(f"ระยะเวลาศึกษาราว {dur}")

    embedding_text = " ".join(filter(None, [
        entry["title_th"], clean_title_en(entry["title_en"]),
        entry["faculty_th"], entry["faculty_en"],
        degree_full, program_type_from_plans(entry["plans"]),
    ]))

    return {
        "id": rec_id,
        "title_th": entry["title_th"],
        "title_en": clean_title_en(entry["title_en"]) or None,
        "degree_level": entry["level_th"],
        "degree_name": degree_name_th(entry["title_th"]),
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": entry["faculty_en"],
        "faculty_th": entry["faculty_th"],
        "department": None,
        "department_th": None,
        "program_type": program_type_from_plans(entry["plans"]) or None,
        "duration_years": dur or None,
        "total_credits": credits or None,
        "tuition_per_semester": None,
        "tuition_total": None,
        "description": " — ".join(description_parts) or None,
        "curriculum_highlights": highlights_from_structure(structure),
        "career_paths": [],
        "tags": [entry["level_en"].replace("_", " ")],
        "website_url": "https://www.mis.cmu.ac.th/TQF/TQF2/CurriculumPublicList.aspx",
        "curriculum_code": code or None,
        "tqf2_id": (detail or {}).get("tqf2_id"),
        "degree_full_en": degree_full or None,
        "degree_abbrev_en": (detail or {}).get("degree_abbrev_en") or None,
        "study_plan_summary": {
            "items": len(study_plan),
            "years": sorted({i.get("year") for i in study_plan if i.get("year")}),
        },
        "embedding_text": embedding_text,
    }


def main():
    entries = json.loads(LIST_FILE.read_text(encoding="utf-8"))
    details = {}
    if DETAILS_FILE.exists():
        details = {d["key"]: d for d in json.loads(DETAILS_FILE.read_text(encoding="utf-8"))}

    records = []
    detailed = 0
    counters = {}
    for e in entries:
        key = f"{e['faculty_code']}|{e['level_code']}|{e['grid_ctl']}|{e['title_th'][:80]}"
        d = details.get(key)
        if d:
            detailed += 1
        counters[e["faculty_code"]] = counters.get(e["faculty_code"], 0) + 1
        records.append(build_record(e, d, counters[e["faculty_code"]]))

    # de-duplicate ids (same curriculum listed under multiple levels/plans)
    seen = {}
    for r in records:
        if r["id"] in seen:
            r["id"] = r["id"] + "_v2"
        seen[r["id"]] = True

    OUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Built %d course records (%d with full TQF2 detail) -> %s",
             len(records), detailed, OUT_FILE)
    by_level = {}
    for r in records:
        by_level[r["degree_level"]] = by_level.get(r["degree_level"], 0) + 1
    log.info("By level: %s", by_level)


if __name__ == "__main__":
    main()
