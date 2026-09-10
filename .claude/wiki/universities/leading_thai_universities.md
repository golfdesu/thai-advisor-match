# Leading Thai Universities (มหาวิทยาลัยวิจัยชั้นนำทั่วประเทศ) — Verified Directory Knowledge
<!-- Reference: WikiSkill (arXiv:2608.27454v1) -->

### 🟢 Verified Active Directory URLs

- `https://multi-university-robotics-centers` (General - 11 profiles verified 2026-09-06)

### Faculty-Scoped Endpoints (wave 3 additions, 2026-09-10)

- KU Sports Science & Health (คณะวิทยาศาสตร์การกีฬาและสุขภาพ): `https://sportsscience.kps.ku.ac.th/lecturer/` (24 profiles; WP REST API enumeration reveals pages — `wp-json/wp/v2/pages?per_page=100`)
- KKU Architecture (คณะสถาปัตยกรรมศาสตร์): `https://arch.kku.ac.th/org-staff-academic` (59 profiles, static)
- CMU Agriculture (คณะเกษตรศาสตร์): `https://www.agro.cmu.ac.th/mis2/personnel/pages/personal_new.php` (80 profiles, MIS personnel system static)
- CMU Fine Arts (คณะวิจิตรศิลป์): `https://www.finearts.cmu.ac.th/เกี่ยวกับเรา/บุคลากร/บุคลากร-new/รายนามบุคลากรภาควิชาทั*` (6 via Elementor-rendered page; full roster needs sub-page enumeration)
- KU Veterinary Technology (คณะเทคนิคการสัตวแพทย์): `https://www.vettech.ku.ac.th/vettech` + `/vetnurse` (9; deeper rosters behind login systems `vtperson` / `ku-work.ku.ac.th`)

### 🔴 Blocked / Dead Ends (wave 3)

- KU Architecture (คณะสถาปัตยกรรมศาสตร์): main site nav has no staff page; lecturer data behind `ku-work.ku.ac.th` (login). Land/BiD dept sites don't publish rosters (2026-09-10).
- MU Veterinary Science (คณะสัตวแพทยศาสตร์): `facultyprofiles.aspx` shows only 3 leads; full roster not in DOM/XHR (2026-09-10).
- CU Faculty of Fine & Applied Arts (ศิลปกรรมศาสตร์): `faa.chula.ac.th` Imperva Incapsula challenge persists (2026-09-10).
- DNS-dead subdomains probed: cu `sscience/sport/dss/mmri/asia/cups/ptc/agsa.chula.ac.th`, ku `sport/agri/envs/educ.ku.ac.th`, kku `medtech/techno.kku.ac.th`, mu `rilca/ili/hrid/csts/liter/lan.mahidol.ac.th`, cmu `medtech/commarts/econ/psy.cmu.ac.th` (2026-09-10).
