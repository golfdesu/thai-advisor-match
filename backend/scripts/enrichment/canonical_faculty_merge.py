# -*- coding: utf-8 -*-
"""
Canonical Faculty Label & Multi-University Disambiguation (Wave 2 Hygiene)
Fixes, from live-DB evidence (no fabrication):
  Phase 1: merged university_th strings ("X และ Y") → single university via email domain,
           else id prefix, else department_th hints (e.g. ศิริราช/รามาธิบดี → Mahidol).
  Phase 2: faculty_th variant labels → canonical per university
           ((TBS)/(KKBS)/(CBS)/FIBO/SIT/SBT/CAMT/SIIT/CMMU/TGGS duplicates, สำนักวิชาววิทยาศาสตร์ typo, SUT program-suffix labels).
  Phase 3: multi-faculty labels split by email domain
           (CU+MU สหเวช/เทคนิคการแพทย์, KU อุตสาหกรรมเกษตร+สัตวแพทย์ → department_th).
  Phase 4: NIDA university name unification.
Recomputes embedding_text for all changed rows; embeddings are re-generated afterwards via embed_missing/fast_reembed runners.
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

UNI_BY_DOMAIN = [
    ("chula.ac.th", ("จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University")),
    ("mahidol.", ("มหาวิทยาลัยมหิดล", "Mahidol University")),
    ("cmu.ac.th", ("มหาวิทยาลัยเชียงใหม่", "Chiang Mai University")),
    ("ku.ac.th", ("มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University")),
    ("ku.th", ("มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University")),
    ("tu.ac.th", ("มหาวิทยาลัยธรรมศาสตร์", "Thammasat University")),
    ("psu.ac.th", ("มหาวิทยาลัยสงขลานครินทร์", "Prince of Songkla University")),
    ("kmitl.ac.th", ("สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "King Mongkut's Institute of Technology Ladkrabang")),
    ("kmutt.ac.th", ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", "King Mongkut's University of Technology Thonburi")),
    ("kmutnb.ac.th", ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "King Mongkut's University of Technology North Bangkok")),
    ("kku.ac.th", ("มหาวิทยาลัยขอนแก่น", "Khon Kaen University")),
    ("swu.ac.th", ("มหาวิทยาลัยศรีนครินทรวิโรฒ", "Srinakharinwirot University")),
    ("nida.ac.th", ("สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)", "National Institute of Development Administration")),
    ("su.ac.th", ("มหาวิทยาลัยศิลปากร", "Silpakorn University")),
]

UNI_BY_ID_PREFIX = [
    ("chulalongk", ("จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University")),
    ("mahidol", ("มหาวิทยาลัยมหิดล", "Mahidol University")),
    ("chiangmai", ("มหาวิทยาลัยเชียงใหม่", "Chiang Mai University")),
    ("kasetsart", ("มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University")),
    ("thammasat", ("มหาวิทยาลัยธรรมศาสตร์", "Thammasat University")),
    ("princeofso", ("มหาวิทยาลัยสงขลานครินทร์", "Prince of Songkla University")),
    ("kmitl", ("สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "King Mongkut's Institute of Technology Ladkrabang")),
    ("kmutt", ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", "King Mongkut's University of Technology Thonburi")),
    ("kmutnb", ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "King Mongkut's University of Technology North Bangkok")),
    ("khonkaen", ("มหาวิทยาลัยขอนแก่น", "Khon Kaen University")),
    ("silpakornu", ("มหาวิทยาลัยศิลปากร", "Silpakorn University")),
    ("nida", ("สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)", "National Institute of Development Administration")),
]

FACULTY_CANONICAL = {
    "จุฬาลงกรณ์มหาวิทยาลัย": {
        "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ แห่งจุฬาลงกรณ์มหาวิทยาลัย": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ฯ",
        "คณะพาณิชยศาสตร์และการบัญชี (CBS จุฬาฯ)": "คณะพาณิชยศาสตร์และการบัญชี",
    },
    "มหาวิทยาลัยเกษตรศาสตร์": {
        "คณะบริหารธุรกิจ (KBS มหาวิทยาลัยเกษตรศาสตร์)": "คณะบริหารธุรกิจ",
        "คณะเกษตร กำแพงแสน": "คณะเกษตร",
        "คณะวิทยาศาสตร์การกีฬาและสุขภาพ (วิทยาเขตกำแพงแสน)": "คณะวิทยาศาสตร์การกีฬาและสุขภาพ",
    },
    "มหาวิทยาลัยขอนแก่น": {
        "คณะบริหารธุรกิจและการบัญชี (KKBS)": "คณะบริหารธุรกิจและการบัญชี",
    },
    "มหาวิทยาลัยเชียงใหม่": {
        "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี (CAMT)": "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี",
        "คณะสาธารณสุขศาสตร์ / สถาบันวิจัยวิทยาศาสตร์สุขภาพ (RIHES)": "คณะสาธารณสุขศาสตร์",
    },
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": {
        "คณะเทคโนโลยีสารสนเทศ (SIT)": "คณะเทคโนโลยีสารสนเทศ",
        "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม",
        "บัณฑิตวิทยาลัยพลังงาน สิ่งแวดล้อมและวัสดุ": "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม (JGSEE)",
        "คณะพลังงาน สิ่งแวดล้อมและวัสดุ": "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม (JGSEE)",
    },
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": {
        "วิทยาลัยเทคโนโลยีอุตสาหกรรม (CIT)": "วิทยาลัยเทคโนโลยีอุตสาหกรรม",
    },
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": {
        "สำนักวิชาววิทยาศาสตร์": "สำนักวิชาวิทยาศาสตร์",
        "สำนักวิชาวิทยาศาสตร์ (สาขาวิชาฟิสิกส์)": "สำนักวิชาวิทยาศาสตร์",
        "สำนักวิชาเทคโนโลยีการเกษตร (สาขาวิชาเทคโนโลยีชีวภาพ)": "สำนักวิชาเทคโนโลยีการเกษตร",
    },
    "มหาวิทยาลัยธรรมศาสตร์": {
        "คณะพาณิชยศาสตร์และการบัญชี (TBS)": "คณะพาณิชยศาสตร์และการบัญชี",
        "คณะวิศวกรรมศาสตร์ (TSE)": "คณะวิศวกรรมศาสตร์",
        "สถาบันเทคโนโลยีนานาชาติสิรินธร": "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)",
    },
    "มหาวิทยาลัยมหิดล": {
        "วิทยาลัยการจัดการ มหาวิทยาลัยมหิดล (CMMU)": "วิทยาลัยการจัดการ (CMMU)",
    },
    "มหาวิทยาลัยนเรศวร": {
        "วิทยาลัยพลังงานทดแทนและเทคโนโลยีสมาร์ตกริด (SGtech)": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี (SGtech)",
    },
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": {
        "คณะทรัพยากรชีวภาพและเทคโนโลยี (SBT)": "คณะทรัพยากรชีวภาพและเทคโนโลยี",
    },
    "มหาวิทยาลัยแม่ฟ้าหลวง": {
        "สำนักวิชาอุตสาหกรรมเกษตร และสถาบันชาและกาแฟ": "สำนักวิชาอุตสาหกรรมเกษตร",
    },
}

# Exact per-row faculty assignments resolved from verified department_th evidence
EXACT_ID_CANONICAL = {
    "cmu_bmei_anawat_001": ("คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    "cmu_bmei_siriporn_001": ("คณะแพทยศาสตร์", "Faculty of Medicine"),
    "cmu_plasma_dheerawan_001": ("คณะวิทยาศาสตร์", "Faculty of Science"),
}

# Rules for composite faculty labels that survived Phase 1 (department-evidence based)
COMPOSITE_DEPT_RULES = {
    "คณะอุตสาหกรรมเกษตร และ คณะสัตวแพทยศาสตร์": [
        (("คณะสัตวแพทยศาสตร์",), "คณะสัตวแพทยศาสตร์", "Faculty of Veterinary Medicine"),
        (("คณะอุตสาหกรรมเกษตร", "ภาควิชา"), "คณะอุตสาหกรรมเกษตร", "Faculty of Agro-Industry"),
    ],
    "คณะสหเวชศาสตร์ และ คณะเทคนิคการแพทย์": [
        (("เทคนิคการแพทย์",), "คณะเทคนิคการแพทย์", "Faculty of Medical Technology"),
        (("สหเวช", "เคมีคลินิก"), "คณะสหเวชศาสตร์", "Faculty of Allied Health Sciences"),
    ],
    "คณะแพทยศาสตร์ศิริราชพยาบาล และ คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี": [
        (("ศิริราช",), "คณะแพทยศาสตร์ศิริราชพยาบาล", "Faculty of Medicine Siriraj Hospital"),
        (("รามาธิบดี",), "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี", "Faculty of Medicine Ramathibodi Hospital"),
    ],
    "คณะจิตรกรรม, คณะวิจิตรศิลป์, คณะอักษรศาสตร์, คณะมนุษยศาสตร์ และ คณะสังคมศาสตร์": [
        (("ทัศนศิลป์", "ศิลปะไทย"), "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "Faculty of Painting, Sculpture and Graphic Arts"),
        (("ภาษาอังกฤษ", "ภาษาตะวันออก"), "คณะอักษรศาสตร์", "Faculty of Arts"),
        (("สังคมวิทยา", "มานุษยวิทยา"), "คณะสังคมศาสตร์", "Faculty of Social Sciences"),
    ],
}

MULTI_FACULTY_SPLIT = {
    # KU merged agro+vet: id prefix kasetsart_agro_vet_* carries faculty in the id
    "มหาวิทยาลัยเกษตรศาสตร์": {
        "คณะอุตสาหกรรมเกษตร และ คณะสัตวแพทยศาสตร์": "_BY_ID",
    },
    # CU+MU allied health: department_th carries the real faculty
    "จุฬาลงกรณ์มหาวิทยาลัย และ มหาวิทยาลัยมหิดล": {
        "คณะสหเวชศาสตร์ และ คณะเทคนิคการแพทย์": "_BY_DEPT",
    },
}

ENG_NAME = {
    "จุฬาลงกรณ์มหาวิทยาลัย": "Chulalongkorn University",
    "มหาวิทยาลัยมหิดล": "Mahidol University",
    "มหาวิทยาลัยเชียงใหม่": "Chiang Mai University",
    "มหาวิทยาลัยเกษตรศาสตร์": "Kasetsart University",
    "มหาวิทยาลัยธรรมศาสตร์": "Thammasat University",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University",
    "มหาวิทยาลัยขอนแก่น": "Khon Kaen University",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": "King Mongkut's Institute of Technology Ladkrabang",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": "King Mongkut's University of Technology Thonburi",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": "King Mongkut's University of Technology North Bangkok",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "Srinakharinwirot University",
    "มหาวิทยาลัยบูรพา": "Burapha University",
    "มหาวิทยาลัยแม่ฟ้าหลวง": "Mae Fah Luang University",
    "มหาวิทยาลัยนเรศวร": "Naresuan University",
    "มหาวิทยาลัยพะเยา": "University of Phayao",
    "มหาวิทยาลัยมหาสารคาม": "Mahasarakham University",
    "มหาวิทยาลัยแม่โจ้": "Maejo University",
    "มหาวิทยาลัยทักษิณ": "Thaksin University",
    "มหาวิทยาลัยวลัยลักษณ์": "Walailak University",
    "มหาวิทยาลัยอุบลราชธานี": "Ubon Ratchathani University",
    "มหาวิทยาลัยรามคำแหง": "Ramkhamhaeng University",
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": "National Institute of Development Administration",
    "มหาวิทยาลัยศิลปากร": "Silpakorn University",
}

KU_AGRO_VET_ID_MAP = {
    "agro": ("คณะอุตสาหกรรมเกษตร", "Faculty of Agro-Industry"),
    "vet": ("คณะสัตวแพทยศาสตร์", "Faculty of Veterinary Medicine"),
}


def resolve_uni(email: str, fid: str, dep: str) -> tuple[str, str] | None:
    e = (email or "").lower()
    for dom, pair in UNI_BY_DOMAIN:
        if dom in e:
            return pair
    lfid = (fid or "").lower()
    for pref, pair in UNI_BY_ID_PREFIX:
        if lfid.startswith(pref):
            return pair
    if "ศิริราช" in (dep or "") or "รามาธิบดี" in (dep or ""):
        return ("มหาวิทยาลัยมหิดล", "Mahidol University")
    return None


def split_multi_faculty(f: FacultyDB) -> str | None:
    cur = (f.faculty_th or "").strip()
    table = MULTI_FACULTY_SPLIT.get(f.university_th, {})
    rule = table.get(cur)
    if not rule:
        return None
    if rule == "_BY_ID":
        lfid = (f.id or "").lower()
        for key, (fac_th, fac_en) in KU_AGRO_VET_ID_MAP.items():
            if key in lfid:
                f.faculty = fac_en
                return fac_th
        return None
    if rule == "_BY_DEPT":
        dep = f.department_th or ""
        if "เทคนิคการแพทย์" in dep:
            f.university_th = "มหาวิทยาลัยมหิดล"
            f.university = ENG_NAME["มหาวิทยาลัยมหิดล"]
            return "คณะเทคนิคการแพทย์"
        if "สหเวช" in dep:
            f.university_th = "จุฬาลงกรณ์มหาวิทยาลัย"
            f.university = ENG_NAME["จุฬาลงกรณ์มหาวิทยาลัย"]
            return "คณะสหเวชศาสตร์"
        lfid = (f.id or "").lower()
        if lfid.startswith("mahidol"):
            f.university_th = "มหาวิทยาลัยมหิดล"
            f.university = ENG_NAME["มหาวิทยาลัยมหิดล"]
            return "คณะเทคนิคการแพทย์"
        if lfid.startswith("chulalongk"):
            f.university_th = "จุฬาลงกรณ์มหาวิทยาลัย"
            f.university = ENG_NAME["จุฬาลงกรณ์มหาวิทยาลัย"]
            return "คณะสหเวชศาสตร์"
    return None


def apply_composite_dept_rule(f: FacultyDB) -> str | None:
    rules = COMPOSITE_DEPT_RULES.get((f.faculty_th or "").strip())
    if not rules:
        return None
    dep = f.department_th or ""
    for needles, fac_th, fac_en in rules:
        if any(n in dep for n in needles):
            f.faculty = fac_en
            return fac_th
    return None


def build_embedding_text(f: FacultyDB) -> str:
    pubs_text = []
    for p in (f.featured_publications or []):
        if isinstance(p, dict):
            t = p.get("title") or ""
            v = p.get("venue") or ""
            pubs_text.append(f"{t} {v}".strip())
        else:
            pubs_text.append(str(p).strip())
    parts = [
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.full_name_th or "",
        f.academic_title_th or "",
        f.faculty_th or "",
        f.department_th or "",
        f.faculty or "",
        f.department or "",
        f.university_th or "",
        f.university or "",
        f.role or "",
        " ".join([str(i) for i in (f.research_interests or [])]),
        " ".join(pubs_text),
        " ".join([str(e) for e in (f.education or [])]),
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]


def main():
    db = SessionLocal()
    changed_ids: list[str] = []

    # ── Phase 1: merged university strings ──────────────────────────
    merged = db.query(FacultyDB).filter(FacultyDB.university_th.like("%และ%")).all()
    print(f"[Phase 1] merged university strings: {len(merged)}")
    unresolved = []
    for f in merged:
        pair = resolve_uni(f.email, f.id, f.department_th or "")
        if pair:
            f.university_th, f.university = pair
            changed_ids.append(f.id)
        else:
            unresolved.append(f"{f.id} | {f.university_th!r} | email={f.email!r}")

    # ── Phase 2: faculty label canonicalization ─────────────────────
    rows = db.query(FacultyDB).all()
    print(f"[Phase 2] scanning {len(rows)} rows for faculty label variants...")
    for f in rows:
        table = FACULTY_CANONICAL.get(f.university_th, {})
        cur = (f.faculty_th or "").strip()
        if cur in table and table[cur] != cur:
            f.faculty_th = table[cur]
            changed_ids.append(f.id)

    # ── Phase 3: multi-faculty label split ──────────────────────────
    print("[Phase 3] multi-faculty label split...")
    for f in rows:
        new_fac = split_multi_faculty(f) or apply_composite_dept_rule(f)
        if new_fac and new_fac != f.faculty_th:
            f.faculty_th = new_fac
            changed_ids.append(f.id)

    # ── Phase 3b: exact ID-level canonical assignments ──────────────
    for fid, (fac_th, fac_en) in EXACT_ID_CANONICAL.items():
        f = db.get(FacultyDB, fid)
        if f and f.faculty_th != fac_th:
            f.faculty_th, f.faculty = fac_th, fac_en
            changed_ids.append(f.id)

    # ── Phase 3c: CU/MedTech row correction ─────────────────────────
    # คณะเทคนิคการแพทย์ standalone exists only at Mahidol; at CU it is a
    # department under คณะสหเวชศาสตร์. So a "CU + คณะเทคนิคการแพทย์" record
    # (from the combined CU&MU allied-health batch) is really MU.
    for f in rows:
        if f.university_th == "จุฬาลงกรณ์มหาวิทยาลัย" and f.faculty_th == "คณะเทคนิคการแพทย์":
            f.university_th = "มหาวิทยาลัยมหิดล"
            f.university = ENG_NAME["มหาวิทยาลัยมหิดล"]
            changed_ids.append(f.id)
        elif f.university_th == "จุฬาลงกรณ์มหาวิทยาลัย" and f.faculty_th == "คณะสหเวชศาสตร์ และ คณะเทคนิคการแพทย์":
            # chula-prefixed batch with blank department → CU Allied Health
            f.faculty_th = "คณะสหเวชศาสตร์"
            f.faculty = "Faculty of Allied Health Sciences"
            changed_ids.append(f.id)

    # ── Phase 4: NIDA name unification ──────────────────────────────
    for f in db.query(FacultyDB).filter(FacultyDB.university_th == "สถาบันบัณฑิตพัฒนบริหารศาสตร์").all():
        f.university_th = "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)"
        f.university = ENG_NAME[f.university_th]
        changed_ids.append(f.id)

    # ── Rebuild embedding_text for all changed rows ─────────────────
    unique_ids = sorted(set(changed_ids))
    for fid in unique_ids:
        f = db.get(FacultyDB, fid)
        if f:
            f.embedding_text = build_embedding_text(f)
            f.embedding = None
    db.commit()
    print(f"✅ Canonical merge complete. Changed records: {len(unique_ids)} (embedding_text rebuilt)")
    with open(os.path.join(BACKEND_DIR, "data", "agent_states", "canonical_merge_reembed_ids.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(unique_ids))
    print(f"📝 Re-embed ID list saved to data/agent_states/canonical_merge_reembed_ids.txt")
    if unresolved:
        print(f"⚠️ Unresolved Phase-1 rows ({len(unresolved)}):")
        for u in unresolved:
            print(f"   {u}")
    db.close()


if __name__ == "__main__":
    main()
