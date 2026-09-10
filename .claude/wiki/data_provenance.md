# Faculty Data Provenance — Sparse-Famous-Faculty Waves 1–3
<!-- Reference: WikiSkill (arXiv:2608.27454v1) & SKILL.state (arXiv:2608.26263v2) -->
<!-- All extractions: 2026-09-10 → local DB `advisor_match` (Docker pgvector, localhost:5432) -->

## Executive Summary

| Wave | Batches | New Records | Method Highlight |
|---|---|---|---|
| 1 | 84–87 | +329 | SERPAPI discovery + static/SPA hybrid crawl |
| 2 | 88–90 | +298 | CDP network capture → hidden JSON API + legacy-site revival |
| 3 | 91–97 | +228 | DNS probing + WP REST API enumeration + MIS systems |
| **Total** | **14 batches** | **+855** | DB: 4,732 → **5,587** (0 missing embeddings) |

## Extraction Pipeline (applies to every source)

```
Discovery (SERPAPI / DNS probe / main-site nav parse)
  → Candidate probing (static HTTP + academic-density scoring: ศ./รศ./ผศ./Prof)
  → [SPA fallback] Selenium headless render (app/scrapers/browser_scraper.py)
  → [XHR hidden] CDP network capture (app/scrapers/network_capture.py, tab click-through)
  → SKILL.state agent (FacultyExtractionAgent: Gemini structured output →
     FacultyStateReducer: title normalization + RapidFuzz dedup + PDPA phone redaction
     → checkpoint JSON in data/agent_states/)
  → Deterministic cleaning (clean_sparse_wave{1,2,3}.py: mojibake strip,
     EN-name fallback, @-preservation, email/name dedup)
  → Dataset files → scripts/data_sources/sparse_*_skill_state_extracted.py
  → faculty_massive_ingestion_runner.py (id upsert + batch commit
     + 768-dim gemini embedding, multi-threaded, key rotation)
```

Tools added: `scripts/crawlers/discover_sparse_faculty_seeds.py` (SERPAPI,
candidates checkpointed to `data/agent_states/seed_discovery_results.json`),
`scripts/crawlers/spa_skill_state_runner.py` (density-gated Selenium hybrid),
`scripts/crawlers/cmu_vet_api_pipeline.py` (JSON API → Reducer),
`app/scrapers/network_capture.py` (CDP), `scripts/crawlers/clean_sparse_wave{1,2,3}.py`.

---

## Wave 1 (Batches 84–87) — จุฬาฯ + มหิดล

### Batch 84 — คณะวารสารศาสตร์และสื่อสารมวลชน จุฬาฯ (2 → 28)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.commarts.chula.ac.th/th/about/units-personnel/` | 22 | static, unit staff + @chula emails |
| `https://www.commarts.chula.ac.th/th/department-jr/` | 7 | dept page (found via SERP); sibling `department-*` pages follow same pattern |
| `https://www.commarts.chula.ac.th/th/` (Selenium-rendered) | +2 | homepage lazy-loads faculty |

Discovery: SERPAPI query `"คณะวารสารศาสตร์และสื่อสารมวลชน จุฬาลงกรณ์มหาวิทยาลัย ทำเนียบอาจารย์"`.

### Batch 85 — คณะอักษรศาสตร์ จุฬาฯ (21 → 47)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.arts.chula.ac.th/th/team/` | 18 | **arts.chula.ac.th = Faculty of ARTS (อักษรศาสตร์), NOT ศิลปกรรมศาสตร์** — initial mislabel corrected before ingest |
| `https://www.arts.chula.ac.th/th/deans/` | 8 | deans page |

### Batch 86 — คณะกายภาพบำบัด มหิดล (3 → 77)
| Source URL | Yield | Notes |
|---|---|---|
| `https://pt.mahidol.ac.th/thai/staff/staff_lecturer/` | 74 | static, Thai research interests + @mahidol emails |

Discovery: SERPAPI. Sister page `https://pt.mahidol.ac.th/thai/staff/` = 0 yield.

### Batch 87 — วิทยาลัยดุริยางคศิลป์ มหิดล (3 → 206)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.music.mahidol.ac.th/people/` | 195 | EN names; deterministic cleaner strips Cyrillic/Arabic transliteration mojibake (215→203) |
| `https://www.music.mahidol.ac.th/yamp/faculty-list/` | 20 | YAMP program faculty |

---

## Wave 2 (Batches 88–90) — XHR API breakthroughs

### Batch 90 — คณะสัตวแพทยศาสตร์ มช. (3 → 83)
| Source | Yield | Notes |
|---|---|---|
| `https://vmcmu.vet.cmu.ac.th/pages/person/api/fetchDataPerson_api.php?typeData[type]=vet_subject-1` | 23 | คณาจารย์ปรีคลินิก — JSON: name TH/EN, email, research, branch, scopus/scholar/orcid |
| `...vet_subject-2` | 59 | คณาจารย์คลินิก |

**How found:** page `main_person-2` has zero names in raw+rendered HTML → CDP network capture
(`app/scrapers/network_capture.py`) while clicking `vetSubject('vet-1'/'vet-2')` buttons → captured
the XHR to `fetchDataPerson_api.php`. Full category switch-map read from
`https://vmcmu.vet.cmu.ac.th/pages/person/js/person.js` (`office-*`, `hotpital_*`, `center_*` =
non-faculty, skipped). Pipeline: `cmu_vet_api_pipeline.py` (API → RawFacultyProfile → StateReducer,
zero-LLM hallucination).

### Batch 88 — คณะสัตวแพทยศาสตร์ จุฬาฯ (4 → 178)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.vet.chula.ac.th/department/anatomy` | 28 | **legacy site** renders full rosters as static HTML |
| `.../department/microbiology` | 10 | |
| `.../department/ศัลยศาสตร์` | 17 | URL-encoded Thai slugs |
| `.../department/สรีรวิทยา-ftpi` | 41 | |
| `.../department/สัตวแพทยสาธารณสุข` | 10 | |
| `.../department/สูติศาสตร์-เธนุเวชวิทยา-และวิทยาการสืบพันธุ์` | 11 | |
| `.../department/หน่วยชีวเคมี` | 16 | |
| `.../department/หน่วยปรสิตวิทยา` | 6 | |
| `.../department/หน่วยพยาธิวิทยา` | 19 | |
| `.../department/อายุรศาสตร์-ukzh` | 24 | |
| `.../department/เภสัชวิทยา-lvew` | 26 | |

**How found:** new site `vet.chula.ac.th/academic_team` = support staff only, lecturer roster
XHR-invisible (CDP capture confirmed no API) → 12 department slugs enumerated from
`www.vet.chula.ac.th/th/` homepage nav (`/department/…`). Dead auto-discovered links
(facebook, 500-error slugs `หน่วยพยาธิวิทยาุตยา`, `www.pharmaco.vet…`) failed safely.

### Batch 89 — คณะเภสัชศาสตร์ ม.ธรรมศาสตร์ (1 → 43)
| Source URL | Yield | Notes |
|---|---|---|
| `https://pharm.tu.ac.th/academicstaff` | 42 | nav link on homepage `/`; static. Note: domain is `pharm.tu.ac.th` (NOT `pharmacy.tu.ac.th` — DNS dead) |

---

## Wave 3 (Batches 91–97) — 5 universities, 7 faculties

### Batch 94 — คณะเกษตรศาสตร์ มช. (4 → 84)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.agro.cmu.ac.th/mis2/personnel/pages/personal_new.php` | 80 | CMU MIS personnel system, static HTML |

### Batch 93 — คณะสถาปัตยกรรมศาสตร์ มข. (2 → 61)
| Source URL | Yield | Notes |
|---|---|---|
| `https://arch.kku.ac.th/org-staff-academic` | 59 | static; `/org-staff-support` = non-academic (skipped) |

### Batch 92 — สถาบันเอเชียศึกษา จุฬาฯ (1 → 28)
| Source URL | Yield | Notes |
|---|---|---|
| `http://www.ias.chula.ac.th/personnel/` | 27 | "ทำเนียบบุคลากร" — found via SERP (subdomain is `ias.`, not `asia.`) |

### Batch 91 — คณะวิทยาศาสตร์การกีฬาและสุขภาพ มก. (1 → 25)
| Source URL | Yield | Notes |
|---|---|---|
| `https://sportsscience.kps.ku.ac.th/lecturer/` | 24 | **page hidden from nav** — revealed by WP REST API enumeration (`wp-json/wp/v2/pages?per_page=100` → page_id 359 "อาจารย์", 521 "บุคลากร"); staff page = 0 yield |

Discovery: SERPAPI → `sportsscience.kps.ku.ac.th` (Khamphaengsaen campus subdomain).

### Batch 97 — สถาบันโภชนาการ มหิดล (3 → 26)
| Source URL | Yield | Notes |
|---|---|---|
| `https://inmu.mahidol.ac.th/th/advisors/` | 18 | faculty grad advisors |
| `https://inmu.mahidol.ac.th/th/executive/` | 5 | executives |
| `/th/organization/`, `/th/research/` | 0 | JS-rendered, confirmed via browser render |

### Batch 96 — คณะเทคนิคการสัตวแพทย์ มก. (2 → 11)
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.vettech.ku.ac.th/vettech` | 4 | dept microsite |
| `https://www.vettech.ku.ac.th/vetnurse` | 5 | dept microsite |

Full rosters behind logins (`vettech-dev.ku.ac.th/vtperson`, `ku-work.ku.ac.th`).

### Batch 95 — คณะวิจิตรศิลป์ มช. (5 → 11) — partial
| Source URL | Yield | Notes |
|---|---|---|
| `https://www.finearts.cmu.ac.th/เกี่ยวกับเรา/บุคลากร/บุคลากร-new/รายนามบุคลากรภาควิชาทั…/` | 6 | Elementor; full roster split across sub-pages per ภาควิชา (TODO wave 4) |

---

## Data Quality Passes (applied before ingestion)

1. **Transliteration mojibake** (wave 1 Music): LLM EN→TH transliteration produced Cyrillic/Arabic
   contamination (`อภิชาติ Аsavamongkolkul`, `องค์أنونต์`) — deterministic regex strip
   `[^\u0E00-\u0E7F A-Za-z0-9 .,\-()'&:@]`, EN-fallback names when Thai unusable (215 → 203).
2. **@-strip email bug** (wave 1 files): contamination regex originally excluded `@`, corrupting
   emails (`sayamon.schula.ac.th`). Regex extended with `:@`; all 6 wave-1 datasets regenerated and
   re-ingested (rows updated in place, no duplicate inserts). Stray 4-char emails in DB zeroed.
3. **Faculty relabeling** (Batch 85): `arts.chula.ac.th` correctly = คณะอักษรศาสตร์ (was initially
   mislabeled ศิลปกรรมศาสตร์ by seed guess) — corrected pre-ingest, 0 contamination.
4. **Missing-embedding repair**: 22 + 3 + 23 residual NULL embeddings rebuilt
   (`build_faculty_embedding_text` + `embedding_service`) after each ingest → final 0 missing.

## Confirmed Blocked (do NOT retry without new strategy)

- **CU Faculty of Fine & Applied Arts** `faa.chula.ac.th` — Imperva Incapsula JS challenge
  (212-byte page; Selenium headless bypass failed).
- **MU Veterinary Science** `vs.mahidol.ac.th/new/facultyprofiles.aspx` — only 3 lead profiles in
  DOM; no XHR roster (CDP-verified).
- **KU Architecture** `arch.ku.ac.th` — no staff page; rosters behind `ku-work.ku.ac.th` login.
- **DNS-dead subdomains** (~20, see `leading_thai_universities.md`): cu `sscience/sport/dss/mmri/
  asia/cups/ptc/agsa`, ku `sport/agri/envs/educ`, kku `medtech/techno`, mu `rilca/ili/hrid/csts/
  liter/lan`, cmu `medtech/commarts/econ/psy`.
- **SERPAPI**: key[0] exhausted (429) 2026-09-10; key[1] remaining — prefer direct subdomain probing.
- **Tourism/Hospitality rosters** (probed 2026-09-10 eve, all ConnectError from this host — may be
  network-local, not server-dead): `tht.msu.ac.th`, SU `htcl.su.ac.th`, PSU `hti.psu.ac.th`,
  BUU `tourism.buu.ac.th`, RU `htii.ru.ac.th`, KMUTT `tsrit.kmutt.ac.th`, MU `comarts.mahidol.ac.th`,
  TU `cits.tu.ac.th`; NIDA tourism page = Cloudflare 403. `stic.ac.th` resolves but is "St Teresa
  International University" (private, not a public tourism faculty). **Retry only from a clean network.**
- **Cyber/HCI elite sources**: SIT `sit.kmutt.ac.th` & KMUTT FIBO ConnectError (same evening); the
  previously-verified SIT/CI/FIBO staff rosters were tiny and are already ingested — no new feed available.
- **OpenAlex key pool**: all 3 keys daily-exhausted 2026-09-10 (~15:00 ICT); canary gate aborted wave 2
  with 0 writes. Re-runnable any time after the daily reset.
