# -*- coding: utf-8 -*-
"""
Phase 5 research lab ingestion from SKILL.state lab crawls (2026-09-26).

Source: backend/data/agent_states/phase5/<key>.py (agentic_pipeline/lab_cli_runner.py exports)

Rules:
- A lab is inserted only when its lead advisor resolves to exactly ONE faculties row of the same
  university: exact normalized Thai name, else exact English first+last name, else RapidFuzz
  token_sort_ratio >= 92 on the Thai name with a single passing row. Unresolved or ambiguous
  leads are quarantined (the zero-defect audit counts a NULL lead_advisor_id as an orphan).
- Members are kept only when they resolve the same way; unresolved member names are dropped.
- The lab name must name a lab / unit / center / group; administrative offices, funds and
  journals are quarantined.
- Dedup against existing research_labs of the same university: RapidFuzz >= 90 on name_th or
  name_en, or identical website_url. Duplicates are skipped (existing rows are not modified).
- faculty_th: as stated on the page, else the resolved lead advisor's faculty_th (grounded in the
  faculties row, never guessed).
- Local Docker DB ONLY.

Usage:
    python scripts/ingest_phase5_research_labs.py            # dry-run
    python scripts/ingest_phase5_research_labs.py --apply
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts" / "audits"))

from rapidfuzz import fuzz

from app.core.database import SessionLocal
from app.models.db_models import ResearchLabDB, FacultyDB
from remediate_bare_openalex_ids import split_thai_name  # noqa: E402

PHASE5_DIR = Path(os.getenv("AGENT_STATE_DIR", BACKEND_DIR / "data" / "agent_states")) / "phase5"
KEYS = ["cu", "kmutt", "kmitl", "cmu", "kku", "ku", "psu", "tu", "sut"]

LAB_NAME_RE = re.compile(
    r"(ห้องปฏิบัติการ|ห้องวิจัย|หน่วยวิจัย|หน่วยปฏิบัติการ|ศูนย์วิจัย|ศูนย์ความเป็นเลิศ|ศูนย์|กลุ่มวิจัย|สถาบันวิจัย|"
    r"lab\b|laborator|research (center|centre|unit|group)|center of excellence|centre of excellence|"
    r"excellence center|research institute)", re.I)
ADMIN_NAME_RE = re.compile(
    r"(สำนักงาน|กองทุน|วารสาร|ฝ่าย|งานบริการ|ทุนวิจัย|office|fund|journal|grant|administration)", re.I)
EN_TITLE_RE = re.compile(
    r"^((assoc\.?|asst\.?|assistant|associate|prof\.?|professor|dr\.?|mr\.?|mrs\.?|ms\.?|miss)\s*)+", re.I)


# the LLM sometimes prepends a page-section category ("กลุ่มวิจัยGlocal Lab",
# "ห้องปฏิบัติการวิจัยห้องปฏิบัติการ...") — drop it when another name starts right after it
_SECTION_PREFIX_RE = re.compile(
    r"^(กลุ่มวิจัย|ห้องปฏิบัติการวิจัย|ศูนย์วิจัย)\s*(?=[A-Za-z]|ห้องปฏิบัติการ|หน่วย|กลุ่ม|ศูนย์)")


def clean_lab_name(name):
    return _SECTION_PREFIX_RE.sub("", re.sub(r"\s+", " ", (name or "").strip())) or None


def load_export(path: Path) -> list[dict]:
    # lab_cli_runner writes the list with json.dumps (null/true), so parse it as JSON, not Python
    text = path.read_text(encoding="utf-8")
    return list(json.loads(text.split("EXTRACTED_LABS = ", 1)[1]))


def norm_th(name: str) -> str:
    first, last = split_thai_name(name or "")
    return f"{first} {last}".strip()


def norm_en(name: str) -> str:
    return re.sub(r"[^a-z ]", "", EN_TITLE_RE.sub("", (name or "").strip()).lower()).strip()


def has_thai(s: str) -> bool:
    return bool(re.search(r"[฀-๿]", s or ""))


class FacultyResolver:
    def __init__(self, rows):
        self.by_th, self.by_en, self.by_univ = {}, {}, {}
        for r in rows:
            self.by_univ.setdefault(r.university_th, []).append(r)
            if r.full_name_th:
                self.by_th.setdefault((r.university_th, norm_th(r.full_name_th)), []).append(r)
            en = re.sub(r"[^a-z ]", "", f"{r.first_name or ''} {r.last_name or ''}".lower()).strip()
            if " " in en:
                self.by_en.setdefault((r.university_th, en), []).append(r)

    def resolve(self, univ: str, name: str):
        """Return the single matching faculties row, or None (no match / ambiguous)."""
        if not name or len(name.strip()) < 4:
            return None
        if has_thai(name):
            key = norm_th(name)
            if not key or " " not in key:
                return None
            cands = self.by_th.get((univ, key), [])
            if not cands:
                cands = [r for r in self.by_univ.get(univ, [])
                         if r.full_name_th and fuzz.token_sort_ratio(key, norm_th(r.full_name_th)) >= 92]
        else:
            key = norm_en(name)
            cands = self.by_en.get((univ, key), []) if " " in key else []
        ids = {c.id for c in cands}
        return cands[0] if len(ids) == 1 else None


def build_embedding_text(lab: dict) -> str:
    return (
        f"{lab['name_th'] or ''} {lab.get('name_en') or ''}. "
        f"University: {lab['university']} {lab['university_th']}. "
        f"Faculty: {lab.get('faculty') or ''} {lab.get('faculty_th') or ''}. "
        f"Department: {lab.get('department') or ''} {lab.get('department_th') or ''}. "
        f"Description: {lab.get('description') or ''}. "
        f"Research domains: {', '.join(lab.get('research_domains') or [])}. "
        f"Equipment: {', '.join(lab.get('flagship_equipment') or [])}."
    )


def main(apply: bool) -> None:
    session = SessionLocal()
    try:
        existing = session.query(ResearchLabDB.id, ResearchLabDB.name_th, ResearchLabDB.name_en,
                                 ResearchLabDB.university_th, ResearchLabDB.website_url).all()
        existing_ids = {e.id for e in existing}
        univs = set()
        exports = {}
        for key in KEYS:
            p = PHASE5_DIR / f"{key}.py"
            if p.exists():
                exports[key] = load_export(p)
                univs.update(l["university_th"] for l in exports[key] if l.get("university_th"))
        fac_rows = (session.query(FacultyDB.id, FacultyDB.university_th, FacultyDB.full_name_th,
                                  FacultyDB.first_name, FacultyDB.last_name, FacultyDB.faculty_th,
                                  FacultyDB.faculty)
                    .filter(FacultyDB.university_th.in_(univs)).all())
        resolver = FacultyResolver(fac_rows)

        to_insert, quarantine, stats = [], [], {}
        for key, labs in exports.items():
            s = {"extracted": len(labs), "new": 0, "dup_existing": 0, "q_not_lab": 0,
                 "q_no_lead_name": 0, "q_lead_unresolved": 0}
            for lab in labs:
                u = lab["university_th"]
                lab["name_th"] = clean_lab_name(lab.get("name_th"))
                name =(lab.get("name_th") or "").strip() or (lab.get("name_en") or "").strip()
                label = f"{name} {lab.get('name_en') or ''}"
                if (not LAB_NAME_RE.search(label) or ADMIN_NAME_RE.search(label)
                        or len(LAB_NAME_RE.sub("", name).strip()) < 4):  # bare "ศูนย์วิจัย" names nothing
                    quarantine.append({**lab, "reason": "not a named lab/unit/center"}); s["q_not_lab"] += 1
                    continue
                if any(e.university_th == u and (
                        (lab.get("name_th") and e.name_th and fuzz.token_sort_ratio(lab["name_th"], e.name_th) >= 90) or
                        (lab.get("name_en") and e.name_en and fuzz.token_sort_ratio(lab["name_en"].lower(), e.name_en.lower()) >= 90) or
                        (lab.get("website_url") and e.website_url and lab["website_url"].rstrip("/") == e.website_url.rstrip("/")))
                       for e in existing):
                    s["dup_existing"] += 1
                    continue
                lead_name = (lab.get("lead_advisor_name") or "").strip()
                if not lead_name:
                    quarantine.append({**lab, "reason": "no lead advisor named on page"}); s["q_no_lead_name"] += 1
                    continue
                lead = resolver.resolve(u, lead_name)
                if not lead:
                    quarantine.append({**lab, "reason": "lead advisor not uniquely in faculties"})
                    s["q_lead_unresolved"] += 1
                    continue
                if not has_thai(lab.get("name_th") or ""):
                    # English-only row (EN mirror page): a planned row with the same resolved lead is
                    # treated as the same lab under its English name (conservative: never a 2nd insert)
                    twin = next((t for t in to_insert if t["lead_advisor_id"] == lead.id), None)
                    if twin:
                        if not twin["name_en"]:
                            twin["name_en"] = (lab.get("name_en") or lab.get("name_th") or "").strip() or None
                        s["dup_existing"] += 1
                        continue
                members = []
                for m in lab.get("member_names") or []:
                    r = resolver.resolve(u, m)
                    if r and r.id != lead.id and r.id not in members:
                        members.append(r.id)
                n = 1
                while f"phase5_{key}_{n:03d}" in existing_ids:
                    n += 1
                lab_id = f"phase5_{key}_{n:03d}"
                existing_ids.add(lab_id)
                row = {
                    "id": lab_id,
                    "name_th": lab.get("name_th") if has_thai(lab.get("name_th") or "") else None,
                    "name_en": (lab.get("name_en") or "").strip() or name,
                    "university": lab["university"], "university_th": u,
                    "faculty_th": lab.get("faculty_th") or lead.faculty_th,
                    "faculty": lab.get("faculty_en") or (lead.faculty if not lab.get("faculty_th") else None),
                    "department_th": lab.get("department_th"), "department": lab.get("department_en"),
                    "lead_advisor_id": lead.id, "lead_advisor_name_source": lead_name,
                    "member_faculty_ids": members,
                    "description": lab.get("description"),
                    "research_domains": lab.get("research_domains") or [],
                    "flagship_equipment": lab.get("flagship_equipment") or [],
                    "website_url": lab.get("website_url") or lab.get("source_url"),
                    "source_url": lab.get("source_url"),
                }
                if not row["name_th"]:
                    row["name_th"] = row["name_en"]
                to_insert.append(row)
                # also guards against the same lab extracted twice across exports
                existing.append(type("E", (), {"university_th": u, "name_th": row["name_th"],
                                               "name_en": row["name_en"], "website_url": row["website_url"],
                                               "id": lab_id})())
                s["new"] += 1
            stats[key] = s

        print(json.dumps(stats, ensure_ascii=False))
        (PHASE5_DIR / "ingest_plan.json").write_text(json.dumps(to_insert, ensure_ascii=False, indent=1),
                                                     encoding="utf-8")
        (PHASE5_DIR / "quarantine.json").write_text(json.dumps(quarantine, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
        print(f"insert={len(to_insert)} quarantine={len(quarantine)}")
        if not apply:
            print("DRY-RUN only — re-run with --apply to execute.")
            return

        from app.core.embedding_service import embedding_service

        def embed(lab):
            try:
                vec = embedding_service.get_embedding(build_embedding_text(lab))
                return vec if isinstance(vec, list) and len(vec) == 768 else None
            except Exception as e:
                print(f"embed fail {lab['id']}: {str(e)[:120]}")
                return None

        with ThreadPoolExecutor(max_workers=6) as ex:
            vecs = list(ex.map(embed, to_insert))
        for lab, vec in zip(to_insert, vecs):
            session.add(ResearchLabDB(
                id=lab["id"], name_th=lab["name_th"], name_en=lab["name_en"],
                university=lab["university"], university_th=lab["university_th"],
                faculty=lab["faculty"], faculty_th=lab["faculty_th"],
                department=lab["department"], department_th=lab["department_th"],
                lead_advisor_id=lab["lead_advisor_id"], member_faculty_ids=lab["member_faculty_ids"],
                description=lab["description"], research_domains=lab["research_domains"],
                flagship_equipment=lab["flagship_equipment"], industry_partners=[], open_positions=[],
                website_url=lab["website_url"],
                embedding_text=build_embedding_text(lab), embedding=vec,
            ))
        session.commit()
        print(f"APPLIED insert={len(to_insert)} null_emb={sum(v is None for v in vecs)}")
    finally:
        session.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase 5 research lab ingestion")
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
