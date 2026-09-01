# WikiSkill Knowledge Index
<!-- Reference: WikiSkill - Compiling Agent Experience into Persistent Knowledge (arXiv:2608.27454v1) -->

Master index of compiled agent experience, verified university directory patterns, and scraping/cleaning strategies across Thai Higher Education.

---

## 🏛️ Universities Directory Knowledge (`wiki/universities/`)
- [Chiang Mai University (CMU)](universities/cmu.md) — ME (`/staff/professor`), CPE (`/lecturer-thai.php`), EE endpoints.
- [King Mongkut's Institute of Technology Ladkrabang (KMITL)](universities/kmitl.md) — School of Engineering directories.
- [Chulalongkorn University (CU)](universities/chula.md) — Faculty of Engineering & Science directory structures.

---

## 🧩 Extraction & Cleaning Patterns (`wiki/patterns/`)
- [Thai Academic Title Edge Cases](patterns/thai_title_rules.md) — Normalization rules for complex/double titles (`ศ.(พิเศษ)`, `รศ.ดร.`, `พญ.ดร.`).
- [SPA & Dynamic Page Scraping](patterns/spa_scraping.md) — Client-side rendered university directory bypass strategies.
- [Anti-Bot & Rate-Limit Policies](patterns/rate_limiting.md) — Request intervals and retry mechanisms.

---

## 📜 Evolution Log (`wiki/evolution_log.md`)
- [Evolution History](evolution_log.md) — Audit trail of compiled traces and proposed/accepted skill patches.
