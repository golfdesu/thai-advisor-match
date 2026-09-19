---
name: phase-35-email-recovery-roadmap
description: Complete specification and context for Phase 35 official email recovery across PostgreSQL faculty clusters
metadata: 
  node_type: memory
  type: project
---

# Phase 35 Official Email Recovery Roadmap

**Status (Completed on 2026-09-16):**
- **Phase 35 Completed & Committed**: 22 authentic official academic emails recovered into local PostgreSQL (`faculties` table in `advisor_match`).
- **Comprehensive Audit of 937 Unexamined Faculty**: 100% of the unexamined faculty pool systematically investigated via headless HTTP probing and checkpointed into `SKILL.state`.
- **Section 9 Invariants & Quality Guardrails**:
  - Rejection of personal freemails (@gmail.com, @hotmail.com, @yahoo.com, @outlook.com, @live.com, @icloud.com).
  - Rejection of generic departmental inboxes (info@, contact@, saraban@, admin@, support@, dean@, pr@, fibo@, ieadmin@).
  - Strict anti-alignment guard: prevented false-positive attribution of emails from multi-faculty directory index pages (153 records safeguarded).
  - Preserved unresolvable faculty strictly as SQL NULL rather than synthesized.
  - Zero personal telephone numbers collected.
  - Rebuilt pgvector deterministic lexical `embedding_text` via `build_faculty_embedding_text(f)` for all updated records.
- **Checkpoints & Artifacts**:
  - `backend/data/agent_states/recoverable_official_emails_phase35.json`
  - `backend/data/agent_states/skill_state_phase35.json`
  - `backend/data/agent_states/skill_state_comprehensive_investigation_937.json`
  - `backend/data/agent_states/comprehensive_investigation_937_faculty.json`
- **Database counts**:
  - Total faculties: 13,409
  - Authentic official emails: 11,272 (+22 increase across Phase 35, 0 cross-university domain mismatches, 0 freemails, 0 personal phone numbers)
  - Missing/Unresolvable: 2,137
- **Regression tests**: 71/71 passing (`pytest backend/tests/test_audited_bug_regressions.py`).

## Recovered in Phase 35 (22 Records):
1. **KMUTT – Department of Microbiology (`mic.kmutt.ac.th`) (9 records)**:
   - HTML entity de-obfuscation of Joomla CMS spambot cloaked JavaScript variables:
     - `kmutt_4bf8615a_9065` | ผศ.ดร. ดวงทิพย์ มูลมั่งมี -> `duangtip.moo@kmutt.ac.th`
     - `kmutt_3b0ec732_2197` | ผศ.ดร. นิยม กำลังดี -> `niyom.kam@kmutt.ac.th`
     - `kmutt_5482c64f_9833` | ผศ.ดร. วิทยา เขาหนองบัว -> `wittaya.kao@kmutt.ac.th`
     - `kmutt_44a91424_9581` | ผศ.ดร. สุกัญญา พึ่งจะแย้ม -> `sukanya.phu@kmutt.ac.th`
     - `kmutt_295b713f_1735` | ผศ.ดร. กรรณิการ์ กุลยะณี -> `kannika.kuny@kmutt.ac.th`
     - `kmutt_79b26f7e_5520` | ดร. จริญญา เชาวน์ปรีชา -> `arinya.chao@kmutt.ac.th`
     - `kmutt_381fedf1_8538` | ดร. อานนท์ ชูกำเนิด -> `arnon.chuk@kmutt.ac.th`
     - `kmutt_13ee518d_7562` | ผศ.ดร. นุจริน จงรุจา -> `nujarin.jon@kmutt.ac.th`
     - `kmutt_411aa867_0808` | ดร. พฤทธิ์ กฤษณะพันธ์ -> `prit.khr@kmutt.ac.th`
2. **KMUTT – School of Information Technology (SIT) (`sit.kmutt.ac.th`) (7 records)**:
   - Individual profile endpoint resolution (`/showprofile?empid=...`):
     - `kmutt_sit_narongrit_waraporn` | ผศ.ดร. ณรงค์ฤทธิ์ วราภรณ์ -> `narongrit@sit.kmutt.ac.th`
     - `kmutt_sit_siam_yamsangsung` | ดร. สยาม แย้มแสงสังข์ -> `siam@sit.kmutt.ac.th`
     - `kmutt_sit_tul` | ผศ.ดร. ตุลย์ ไตรยสรรค์ -> `tuul.tri@sit.kmutt.ac.th`
     - `kmutt_sit_tuul_t` | ดร. ตุลย์ ตรียะซอน -> `tuul.tri@sit.kmutt.ac.th`
     - `kmutt_sit_wichian_chutimaskul` | รศ.ดร. วิเชียร ชุติมาสกุล -> `wichian@sit.kmutt.ac.th`
     - `kmutt_sit_vajirasak_vanijja` | รศ.ดร. วชิรศักดิ์ วณิชชา -> `vachee@sit.kmutt.ac.th`
     - `kmutt_sit_umaporn_supasitthimethee` | ผศ.ดร. อุมาพร สุภสิทธิเมธี -> `umaporn@sit.kmutt.ac.th`
3. **Unexamined Faculty Pool Verified Recoveries (6 records)**:
   - Recovered authentic institutional faculty emails with two-factor name token verification:
     - `sut_apinun_buritatum_6141` | อ.ดร. อภินันท์ บูริตธรรม -> `apinun_ce@sut.ac.th` (SUT Engineering)
     - `regionalun_facultymem_sreenorchan_068` | ผศ. สุรชัย ศรีนรจันทร์ -> `surachai-s@mju.ac.th` (MJU Agriculture)
     - `nida_as_001` | รศ.ดร. สุรพงษ์ อังคสกุลเกียรติ -> `surapong@as.nida.ac.th` (NIDA Applied Statistics)
     - `sut_nikom_klomkliang_0415` | รศ.ดร. นิคม กลมเกลี้ยง -> `nikom.klo@sut.ac.th` (SUT Engineering)
     - `nida_tanasai_sucontphunt_1133` | ผศ.ดร. ธนาสัย สุคนธ์พันธุ์ -> `tanasai@as.nida.ac.th` (NIDA Applied Statistics)
     - `nu_kumropr__8257` | รศ.ดร. คำรพ รัตนสุต -> `kumropr@nu.ac.th` (Naresuan Agriculture)

## Systematic Audit Classification across all 937 Unexamined Records:
- 473: `NO_PROFILE_URL_PUBLISHED` (No web profile URL available in database; curriculum/thesis advisor ingestions)
- 153: `DIRECTORY_PAGE_MULTI_FACULTY_NO_INDIVIDUAL_MATCH` (Multi-faculty directory pages; adjacent emails strictly rejected per Section 9)
- 72: `EMPTY_PROFILE_NO_EMAIL` (Profile page exists and successfully loaded, but publishes no email address)
- 62: `PROFILE_PROBE_HTTP_ERROR_404` (Profile link returns HTTP 404 not found on university web server)
- 52: `VISITING_INTERNATIONAL_ARTIST` (Mahidol College of Music visiting guest artists; no institutional university email)
- 33: `GENERIC_INBOX_EXCLUSION_SECTION_9` (Faculty published only generic department/secretary inboxes; e.g. `ed.swu@g.swu.ac.th`, `tls@tu.ac.th`)
- 21: `PROFILE_PROBE_TIMEOUT` (University web server timed out)
- 19: `VISITING_ADJUNCT_PROFESSOR` (Chula Sasin international visiting adjunct professors)
- 17: `PROFILE_PROBE_HTTP_ERROR_403` (Profile page blocked by university firewall)
- 16: `FREEMAIL_EXCLUSION_SECTION_9` (Only personal freemails published; `@gmail.com`, `@yahoo.com`)
- 8: `PROFILE_PROBE_DNS_LOOKUP_FAILED` (Dead departmental subdomains)
- 5: `DEAD_DOMAIN_UNREACHABLE` (Dead domain connection failed)
- 6: `AUTHENTIC_ACADEMIC_EMAIL_FOUND` (Two-factor verified individual academic institutional email)

## Known Policy Omission Clusters (1,206 records):
- Clinical Medical & Dental Hospital Doctors (~639 records)
- Chula CBS Inactive / Emeritus (~233 records)
- Personal Freemail Exclusion Clusters (KMITL Architecture, Silpakorn Engineering, Chula Pharmacy, CMU Engineering) (~334 records)
