# Prince of Songkla University (มหาวิทยาลัยสงขลานครินทร์) — Verified Directory Knowledge
<!-- Reference: WikiSkill (arXiv:2608.27454v1) -->

### 🟢 Verified Active Directory URLs

_(none — faculty directory URLs at PSU are faculty-specific; see scoped list below. Do NOT auto-seed across faculties.)_

### Faculty-Scoped Endpoints (for matching faculty runs ONLY — never auto-seed into other faculties)

- Faculty of Management Sciences (คณะวิทยาการจัดการ): `https://www.fms.psu.ac.th/professor/professor-dpa/professor-pa/` (7 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-fin/` (4 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-mkt/` (5 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-hrm/` (7 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-bis/` (6 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-bba/` (4 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-lgm/` (7 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dba/professor-mice/` (4 profiles verified 2026-09-06)
- Faculty of Management Sciences: `https://www.fms.psu.ac.th/professor/professor-dacc/professor-acc/` (3 profiles verified 2026-09-06)
- Faculty of Law (คณะนิติศาสตร์): `https://law.psu.ac.th/index.php/about/personnel/lecturer.html` (25 profiles verified 2026-09-06)
- Faculty of Science (คณะวิทยาศาสตร์) — Physical Science dept: `https://www.sci.psu.ac.th/personnel-lists/?id=01` (67 profiles extracted 2026-09-09)
- Faculty of Science — Biological Science dept: `https://www.sci.psu.ac.th/personnel-lists/?id=02` (50 profiles extracted 2026-09-09)
- Faculty of Science — Computational Science dept: `https://www.sci.psu.ac.th/personnel-lists/?id=03` (50 profiles extracted 2026-09-09)
- Faculty of Science — dept group 04: `https://www.sci.psu.ac.th/personnel-lists/?id=04` (52 profiles extracted 2026-09-09, batch 71 ingested)

### ⚠️ Operational Notes
- **Wiki auto-seed pitfall (fixed 2026-09-09):** `lookup_university_endpoints` seeds ALL URLs under "Verified Active Directory URLs" regardless of `--faculty-th`. Keep faculty-specific URLs strictly under "Faculty-Scoped Endpoints" and use `--no-wiki` on `cli_runner.py` for strict faculty-scoped runs. Contaminated exports (FMS/Law profiles mislabeled as Science) were deleted before ingestion.

### 🚫 Blocked / No HTML Directory
- Faculty of Medicine: `med.psu.ac.th` & variants — DNS does not resolve; physician rosters at `hospital.psu.ac.th` link out to a Google Sites org chart.
- Faculty of Engineering: `eng.psu.ac.th` — SPA-style site (`/staff` landing page is JS-driven); department subdomains (chem/ee/me/mining) do not resolve; `ce.eng.psu.ac.th` uses a JS redirect to `index.php`.
