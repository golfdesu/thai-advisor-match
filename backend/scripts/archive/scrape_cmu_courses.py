"""
Scraper for Chiang Mai University central curriculum database (CMU MIS TQF2).
Source: https://www.mis.cmu.ac.th/TQF/TQF2/CurriculumPublicList.aspx
Collects all curricula (Bachelor -> Ph.D.) across every faculty/college.

Usage:
    python scrape_cmu_courses.py --phase list                # step 1: enumerate all curricula
    python scrape_cmu_courses.py --phase details             # step 2: fetch THA/ENG detail per curriculum
    python scrape_cmu_courses.py --phase list --faculties 05,06 --levels 4,6
Outputs:
    data/cmu_tqf_list.json     - flat list of curricula from the search grid
    data/cmu_tqf_details.json  - per-curriculum THA/ENG details (credits, degrees, structure, study plan)
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mis.cmu.ac.th/TQF/TQF2/CurriculumPublicList.aspx"
DATA_DIR = Path(__file__).resolve().parent / "data"
LIST_FILE = DATA_DIR / "cmu_tqf_list.json"
DETAILS_FILE = DATA_DIR / "cmu_tqf_details.json"

ACADEMIC_YEAR = "2568"
ACADEMIC_TERM = "1"

FACULTIES = {
    "01": ("Faculty of Humanities", "คณะมนุษยศาสตร์"),
    "02": ("Faculty of Education", "คณะศึกษาศาสตร์"),
    "03": ("Faculty of Fine Arts", "คณะวิจิตรศิลป์"),
    "04": ("Faculty of Social Sciences", "คณะสังคมศาสตร์"),
    "05": ("Faculty of Science", "คณะวิทยาศาสตร์"),
    "06": ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์"),
    "07": ("Faculty of Medicine", "คณะแพทยศาสตร์"),
    "08": ("Faculty of Agriculture", "คณะเกษตรศาสตร์"),
    "09": ("Faculty of Dentistry", "คณะทันตแพทยศาสตร์"),
    "10": ("Faculty of Pharmacy", "คณะเภสัชศาสตร์"),
    "11": ("Faculty of Associated Medical Sciences", "คณะเทคนิคการแพทย์"),
    "12": ("Faculty of Nursing", "คณะพยาบาลศาสตร์"),
    "13": ("Faculty of Agro-Industry", "คณะอุตสาหกรรมเกษตร"),
    "14": ("Faculty of Veterinary Medicine", "คณะสัตวแพทยศาสตร์"),
    "15": ("Faculty of Business Administration", "คณะบริหารธุรกิจ"),
    "16": ("Faculty of Economics", "คณะเศรษฐศาสตร์"),
    "17": ("Faculty of Architecture", "คณะสถาปัตยกรรมศาสตร์"),
    "18": ("Faculty of Mass Communication", "คณะการสื่อสารมวลชน"),
    "19": ("Faculty of Political Science and Public Administration", "คณะรัฐศาสตร์และรัฐประศาสนศาสตร์"),
    "20": ("Faculty of Law", "คณะนิติศาสตร์"),
    "21": ("College of Arts, Media and Technology", "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี"),
    "26": ("Biomedical Engineering Institute", "สถาบันวิศวกรรมชีวการแพทย์"),
    "30": ("Multidisciplinary and Interdisciplinary School", "วิทยาลัยพหุวิทยาการและสหวิทยาการ"),
    "37": ("Research Institute for Health Sciences", "สถาบันวิจัยวิทยาศาสตร์สุขภาพ"),
    "49": ("School of Public Policy", "วิทยาลัยนโยบายสาธารณะ"),
    "60": ("Faculty of Public Health", "คณะสาธารณสุขศาสตร์"),
    "61": ("International College of Digital Innovation", "วิทยาลัยนวัตกรรมดิจิทัล (นานาชาติ)"),
    "62": ("College of Marine Studies and Management", "วิทยาลัยการจัดการและการศึกษาทางทะเล"),
}

LEVELS = {
    "2": ("bachelor", "ปริญญาตรี"),
    "3": ("graduate_certificate", "ประกาศนียบัตรบัณฑิต"),
    "4": ("master", "ปริญญาโท"),
    "5": ("higher_graduate_certificate", "ประกาศนียบัตรบัณฑิตชั้นสูง"),
    "6": ("doctor", "ปริญญาเอก"),
    "7": ("bachelor_master", "ปริญญาตรี-โท (หลักสูตรบูรณาการ)"),
    "8": ("master_doctor", "ปริญญาโท-เอก (หลักสูตรบูรณาการ)"),
}

DELAY = 0.35
log = logging.getLogger("cmu_scraper")


def new_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; ThaiEduCenter/1.0)"
    return s


def form_fields(soup: BeautifulSoup) -> dict:
    data = {}
    for inp in soup.find_all("input"):
        name = inp.get("name")
        if not name or inp.get("type") in ("submit", "button", "image"):
            continue
        data[name] = inp.get("value", "")
    for sel in soup.find_all("select"):
        name = sel.get("name")
        if not name:
            continue
        opt = sel.find("option", selected=True) or sel.find("option")
        data[name] = opt["value"] if opt else ""
    return data


def post_with_retry(s: requests.Session, data: dict, tries: int = 3):
    for attempt in range(tries):
        try:
            r = s.post(BASE_URL, data=data, timeout=90)
            if r.status_code == 200:
                return r
        except requests.RequestException as exc:
            log.warning("POST failed (attempt %d): %s", attempt + 1, exc)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"POST failed after {tries} attempts")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_grid_rows(soup: BeautifulSoup, faculty_code: str, level_code: str) -> list:
    grid = soup.find(id="GVCuriculumList")
    if grid is None:
        return []
    entries = []
    seen_ctls = set()
    level_en, level_th = LEVELS[level_code]
    fac_en, fac_th = FACULTIES[faculty_code]
    for anchor in grid.find_all("a"):
        href = anchor.get("href", "")
        m = re.search(r"__doPostBack\('(GVCuriculumList\$(ctl\d+)\$btnCurriculumName(Tha|Eng))'", href)
        if not m:
            continue
        target, ctl, lang = m.group(1), m.group(2), m.group(3)
        if ctl in seen_ctls:
            continue
        seen_ctls.add(ctl)
        tr = anchor.find_parent("tr")

        thai_name, eng_name = "", ""
        for a in tr.find_all("a"):
            h = a.get("href", "")
            t = clean(a.get_text())
            if "btnCurriculumNameTha" in h:
                thai_name = t
            elif "btnCurriculumNameEng" in h:
                eng_name = t

        plans = []
        plan_grid = tr.find("table", id=re.compile(r"GVPlanInCurr$"))
        if plan_grid:
            for ptr in plan_grid.find_all("tr"):
                spans = [clean(td.get_text()) for td in ptr.find_all("td") if clean(td.get_text())]
                if spans:
                    plans.append(spans)

        level_label = ""
        lbl = tr.find("span", id=re.compile(r"Label1$"))
        if lbl:
            level_label = clean(lbl.get_text())

        entries.append({
            "faculty_code": faculty_code,
            "faculty_en": fac_en,
            "faculty_th": fac_th,
            "level_code": level_code,
            "level_en": level_en,
            "level_th": level_th or level_label,
            "grid_ctl": ctl,
            "postback_target": target,
            "title_th": thai_name,
            "title_en": eng_name,
            "plans": plans,
        })
    return entries


def phase_list(faculties, levels, year, term):
    s = new_session()
    all_entries = []
    for fac in faculties:
        for lvl in levels:
            r = s.get(BASE_URL, timeout=60)
            soup = BeautifulSoup(r.text, "lxml")
            data = form_fields(soup)
            data.update({
                "ddlAcademicYear": year,
                "ddlAcademicTerm": term,
                "ddlListFaculty": fac,
                "ddlStudentLevelID": lvl,
                "btnSearch": "Search",
            })
            r2 = post_with_retry(s, data)
            soup2 = BeautifulSoup(r2.text, "lxml")
            count_el = soup2.find(id="lblCountCourse")
            count = int(clean(count_el.get_text())) if count_el else 0
            entries = parse_grid_rows(soup2, fac, lvl)
            log.info("%s / level %s -> count=%s parsed=%d", FACULTIES[fac][0], lvl, count, len(entries))
            all_entries.extend(entries)
            time.sleep(DELAY)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text(json.dumps(all_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Saved %d curricula to %s", len(all_entries), LIST_FILE)


def parse_detail_page(soup: BeautifulSoup):
    result = {}
    code_el = soup.find(id="lblCurriculumTQF2ID")
    if code_el:
        m = re.search(r"Code\s*:\s*(\S+)", clean(code_el.get_text()))
        result["curriculum_code"] = m.group(1) if m else ""

    hdf = soup.find(id="hdfTQF2ID")
    result["tqf2_id"] = hdf["value"] if hdf and hdf.has_attr("value") else ""

    name_el = soup.find(id="CurriculumName")
    result["name"] = re.sub(r"\s+", "\n", name_el.get_text()).strip() if name_el else ""

    for key, sid in (("degree_full", "lblFullDegree"), ("degree_abbrev", "lblShortDegree")):
        el = soup.find(id=sid)
        if el:
            txt = clean(el.get_text())
            parts = txt.split(":", 1)
            result[key] = parts[1].strip() if len(parts) > 1 else txt
        else:
            result[key] = ""

    structure = []
    grid = soup.find(id="GVCurriculumList")
    current_section = None
    if grid is not None:
        for tr in grid.find_all("tr"):
            tds = tr.find_all("td")
            texts = [clean(td.get_text()) for td in tds]
            nonempty = [t for t in texts if t]
            if not nonempty:
                continue
            course_match = None
            if len(tds) >= 5 and re.fullmatch(r"\d{5,}", texts[1] if len(texts) > 1 else ""):
                credit_txt = next((t for t in reversed(nonempty) if re.search(r"\d\s*\(\d+-\d+-\d+\)", t)), "")
                course_match = {
                    "course_ref": texts[1],
                    "course_abbr": texts[2] if len(texts) > 2 else "",
                    "course_number": texts[3] if len(texts) > 3 else "",
                    "course_title": texts[4] if len(texts) > 4 else "",
                    "credit": credit_txt,
                }
            if course_match:
                if current_section is not None:
                    structure.append({"section": current_section, **course_match})
                continue
            label = nonempty[0]
            value = nonempty[1] if len(nonempty) > 1 else ""
            if re.fullmatch(r"[\d.]+", value or "") or value == "-":
                structure.append({"section": label, "credits": value})
                current_section = label
            elif len(label) < 120:
                current_section = label

    result["structure"] = structure

    study_plan = []
    sp = soup.find(id="GVStudyPlan")
    if sp is not None:
        plan_name, year_lbl, term_lbl = "", "", ""
        for tr in sp.find_all("tr"):
            head = tr.find("span", id=re.compile(r"dvStdYearHeadPlan"))
            if head:
                p = tr.find("span", id=re.compile(r"lblCurriculumPlanName$"))
                y = tr.find("span", id=re.compile(r"lblStudyYear$"))
                t = tr.find("span", id=re.compile(r"lblStudyTerm$"))
                plan_name = clean(p.get_text()) if p else plan_name
                year_lbl = clean(y.get_text()) if y else year_lbl
                term_lbl = clean(t.get_text()) if t else term_lbl
                continue
            is_sum = tr.find(id=re.compile(r"dvStdYearSum")) is not None
            tds = [td for td in tr.find_all("td")]
            texts = [clean(td.get_text()) for td in tds]
            nonempty = [t for t in texts if t]
            if not nonempty:
                continue
            if len(tds) >= 5 and re.fullmatch(r"\d{5,}", texts[1] or ""):
                item = {
                    "course_ref": texts[1],
                    "course_title": texts[4] if len(texts) > 4 else "",
                    "credit": texts[5] if len(texts) > 5 else "",
                }
                study_plan.append({
                    "plan": plan_name,
                    "year": year_lbl,
                    "term": term_lbl,
                    **item,
                })
            elif is_sum:
                study_plan.append({
                    "plan": plan_name,
                    "year": year_lbl,
                    "term": term_lbl,
                    "summary": nonempty[-1],
                })
    result["study_plan"] = study_plan
    return result


def fetch_detail_for_entry(s: requests.Session, entry: dict, year, term):
    r = s.get(BASE_URL, timeout=60)
    soup = BeautifulSoup(r.text, "lxml")
    data = form_fields(soup)
    data.update({
        "ddlAcademicYear": year,
        "ddlAcademicTerm": term,
        "ddlListFaculty": entry["faculty_code"],
        "ddlStudentLevelID": entry["level_code"],
        "btnSearch": "Search",
    })
    r2 = post_with_retry(s, data)
    soup2 = BeautifulSoup(r2.text, "lxml")

    data2 = form_fields(soup2)
    data2["__EVENTTARGET"] = entry["postback_target"]
    data2.pop("btnSearch", None)
    r3 = post_with_retry(s, data2)
    soup3 = BeautifulSoup(r3.text, "lxml")

    parsed = parse_detail_page(soup3)
    # The detail page renders in the default language (English); official Thai
    # title/plan names already come from the list grid entry.
    if not parsed.get("curriculum_code"):
        raise RuntimeError("detail page did not render (no curriculum code)")
    return parsed


def phase_details(year, term, limit=None, resume=True):
    entries = json.loads(LIST_FILE.read_text(encoding="utf-8"))
    existing = {}
    if resume and DETAILS_FILE.exists():
        existing = {d["key"]: d for d in json.loads(DETAILS_FILE.read_text(encoding="utf-8"))}

    results = dict(existing)
    s = new_session()
    done = 0
    for entry in entries:
        key = f"{entry['faculty_code']}|{entry['level_code']}|{entry['grid_ctl']}|{entry['title_th'][:80]}"
        if key in results:
            continue
        try:
            detail = fetch_detail_for_entry(s, entry, year, term)
        except Exception as exc:
            log.error("FAILED %s: %s", key, exc)
            continue
        record = {"key": key, **entry,
                  "name_en": detail.pop("name", ""),
                  "curriculum_code": detail.get("curriculum_code"),
                  "tqf2_id": detail.get("tqf2_id"),
                  "degree_full_en": detail.get("degree_full"),
                  "degree_abbrev_en": detail.get("degree_abbrev"),
                  "structure": detail.get("structure"),
                  "study_plan": detail.get("study_plan")}
        results[key] = record
        done += 1
        total = len(results)
        log.info("[%d/%d] %s | code=%s", total, len(entries), entry["title_th"][:60], record["curriculum_code"])
        if done % 10 == 0:
            DETAILS_FILE.write_text(json.dumps(list(results.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        if limit and done >= limit:
            break
        time.sleep(DELAY)

    DETAILS_FILE.write_text(json.dumps(list(results.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Saved %d detailed records to %s", len(results), DETAILS_FILE)


def main():
    parser = argparse.ArgumentParser(description="Scrape CMU TQF2 curriculum database")
    parser.add_argument("--phase", choices=["list", "details"], required=True)
    parser.add_argument("--faculties", help="comma-separated faculty codes, e.g. 05,06 (default: all)")
    parser.add_argument("--levels", help="comma-separated level codes 2,4,6 (default: all)")
    parser.add_argument("--year", default=ACADEMIC_YEAR)
    parser.add_argument("--term", default=ACADEMIC_TERM)
    parser.add_argument("--limit", type=int, help="max details to fetch (testing)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    faculties = args.faculties.split(",") if args.faculties else list(FACULTIES)
    levels = args.levels.split(",") if args.levels else list(LEVELS)

    if args.phase == "list":
        phase_list(faculties, levels, args.year, args.term)
    else:
        phase_details(args.year, args.term, limit=args.limit)


if __name__ == "__main__":
    main()
