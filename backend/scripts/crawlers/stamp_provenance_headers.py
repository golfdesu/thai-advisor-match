"""Stamp exact source URLs into dataset file headers."""
import io
import os

DS = r"C:\Users\chaya\Documents\Program\Project\Teacher\backend\scripts\data_sources"

HEADERS = {
    "sparse_cu_commarts_skill_state_extracted.py":
        "# Sources: commarts.chula.ac.th/th/about/units-personnel/, /th/department-jr/, / (SPA) — SKILL.state wave 1 Batch 84",
    "sparse_cu_arts_skill_state_extracted.py":
        "# Sources: arts.chula.ac.th/th/team/, /th/deans/ — SKILL.state wave 1 Batch 85 (arts.chula = Faculty of ARTS)",
    "sparse_mu_pt_skill_state_extracted.py":
        "# Source: pt.mahidol.ac.th/thai/staff/staff_lecturer/ — SKILL.state wave 1 Batch 86",
    "sparse_mu_music_skill_state_extracted.py":
        "# Sources: music.mahidol.ac.th/people/ + /yamp/faculty-list/ — SKILL.state wave 1 Batch 87 (mojibake-cleaned)",
    "sparse_cu_vet_skill_state_extracted.py":
        "# Sources: www.vet.chula.ac.th/department/<slug> x11 (anatomy, microbiology, Thai slugs) — wave 2 Batch 88",
    "sparse_tu_pharmacy_skill_state_extracted.py":
        "# Source: pharm.tu.ac.th/academicstaff — SKILL.state wave 2 Batch 89",
    "sparse_cmu_vet_api_extracted.py":
        "# Source: vmcmu.vet.cmu.ac.th/pages/person/api/fetchDataPerson_api.php (vet_subject-1,2 JSON API via CDP capture) — wave 2 Batch 90, zero-LLM pipeline",
    "sparse_ku_sportsci_skill_state_extracted.py":
        "# Source: sportsscience.kps.ku.ac.th/lecturer/ (page found via WP REST enumeration) — wave 3 Batch 91",
    "sparse_cu_ias_skill_state_extracted.py":
        "# Source: ias.chula.ac.th/personnel/ — SKILL.state wave 3 Batch 92",
    "sparse_kku_arch_skill_state_extracted.py":
        "# Source: arch.kku.ac.th/org-staff-academic — SKILL.state wave 3 Batch 93",
    "sparse_cmu_agro_skill_state_extracted.py":
        "# Source: agro.cmu.ac.th/mis2/personnel/pages/personal_new.php — SKILL.state wave 3 Batch 94",
    "sparse_cmu_finearts_skill_state_extracted.py":
        "# Source: finearts.cmu.ac.th staff roster (partial; sub-pages TODO) — wave 3 Batch 95",
    "sparse_ku_vettech_skill_state_extracted.py":
        "# Sources: vettech.ku.ac.th/vettech + /vetnurse — wave 3 Batch 96",
    "sparse_mu_inmu_skill_state_extracted.py":
        "# Sources: inmu.mahidol.ac.th/th/advisors/ + /th/executive/ — SKILL.state wave 3 Batch 97",
}

for fname, hdr in HEADERS.items():
    p = os.path.join(DS, fname)
    if not os.path.exists(p):
        print("missing:", fname)
        continue
    lines = io.open(p, encoding="utf-8").read().split("\n")
    if lines[0].startswith("# Source"):
        lines[0] = hdr
    else:
        lines.insert(0, hdr)
    io.open(p, "w", encoding="utf-8").write("\n".join(lines))
    print("stamped:", fname)
