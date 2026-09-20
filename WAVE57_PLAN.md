# Wave 57 Execution Plan
**Drafted:** 2026-09-20  
**Status:** Ready to execute (waiting for OpenAlex quota reset overnight)

---

## 1. Context

After Waves 53–56 (RMUT, MJU, NIDA, Rajabhat), DB stands at:

- **Grand Total:** 59,960 faculty records
- **OpenAlex coverage:** 45,622 / 59,960 = **76%**
- **Email coverage:** 17,330 / 59,960 = **28%**

Wave 57 targets major universities that were acquired in earlier waves but remain under-indexed in OpenAlex, meaning their full academic rosters were never fully pulled.

---

## 2. Coverage Gaps (DB snapshot 2026-09-20)

| University | Total | OPX | OPX% | Email | Email% | Priority |
|---|---|---|---|---|---|---|
| Srinakharinwirot (SWU) | 1,612 | 71 | **4%** | 214 | 13% | 🔴 CRITICAL |
| Burapha (BUU) | 930 | 42 | **4%** | 579 | 62% | 🔴 CRITICAL |
| Silpakorn (SU) | 696 | 65 | **9%** | 315 | 45% | 🔴 CRITICAL |
| Thaksin (TSU) | 2,128 | 483 | **22%** | 1,703 | 80% | 🔴 CRITICAL |
| KMUTT | 537 | 131 | **24%** | 423 | 78% | 🔴 CRITICAL |
| Prince of Songkla (PSU) | 754 | 249 | **33%** | 584 | 77% | 🟠 HIGH |
| KMITL | 909 | 310 | **34%** | 526 | 57% | 🟠 HIGH |
| Thammasat (TU) | 1,105 | 440 | **39%** | 689 | 62% | 🟠 HIGH |
| KMUTNB | 528 | 265 | **50%** | 321 | 60% | 🟠 HIGH |
| Walailak (WU) | 2,417 | 1,266 | **52%** | 1,195 | 49% | 🟠 HIGH |
| Chiang Mai (CMU) | 1,767 | 983 | **55%** | 1,632 | 92% | 🟡 MED |
| Kasetsart (KU) | 3,229 | 1,918 | **59%** | 3,162 | 97% | 🟡 MED |
| Chulalongkorn (CU) | 2,346 | 1,399 | **59%** | 1,509 | 64% | 🟡 MED |
| NIDA | 1,625 | 1,614 | 99% | 36 | **2%** | 🟡 EMAIL ONLY |
| Mae Fah Luang (MFU) | 2,454 | 2,022 | 82% | 549 | **22%** | 🟡 EMAIL ONLY |
| Mahasarakham (MSU) | 1,413 | 1,260 | 89% | 129 | **9%** | 🟡 EMAIL ONLY |
| University of Phayao (UP) | 1,300 | 884 | 68% | 415 | **31%** | 🟡 EMAIL ONLY |
| Ubon Ratchathani (UBU) | 987 | 679 | 68% | 252 | **25%** | 🟡 EMAIL ONLY |

---

## 3. Wave 57A — OpenAlex Roster Expansion

**Script (already exists, backoff fixed):**
```
backend/scripts/crawlers/run_wave57_top_universities_enrichment.py
```

### 3.1 OpenAlex Institution IDs

| University | ID | Verified? | Notes |
|---|---|---|---|
| SWU (Srinakharinwirot) | `I76920116` | ✅ **Confirmed** | 5,150 authors confirmed via test request 2026-09-20 |
| KMUTT | `I60837268` | ✅ Confirmed via DB reverse-lookup |  |
| CMU | `I48076826` | ✅ Confirmed via DB reverse-lookup |  |
| KU | `I198105771` | ✅ Confirmed via DB reverse-lookup |  |
| CU | `I75009780` | ✅ Confirmed via DB reverse-lookup |  |
| MU | `I25399158` | ✅ Confirmed via DB reverse-lookup |  |
| TU | `I110458564` | ⚠️ Unverified — verify before run |  |
| BUU | `I129488602` | ⚠️ Unverified — verify before run |  |
| SU | `I102985835` | ⚠️ Unverified — verify before run |  |
| PSU | `I183412441` | ⚠️ Unverified — verify before run |  |
| KMITL | `I16426522` | ⚠️ Unverified — verify before run |  |
| KMUTNB | `I4210090662` | ⚠️ Unverified — verify before run |  |
| KKU | `I196701617` | ⚠️ Unverified — verify before run |  |
| TSU (Thaksin) | ❌ Unknown | ❌ **Must lookup** | `display_name.search:Thaksin` |
| WU (Walailak) | ❌ Unknown | ❌ **Must lookup** | `display_name.search:Walailak` |

### 3.2 ID Lookup Command (for TSU and WU)
```
https://api.openalex.org/institutions?filter=country_code:TH,display_name.search:Thaksin&select=id,display_name,works_count
https://api.openalex.org/institutions?filter=country_code:TH,display_name.search:Walailak&select=id,display_name,works_count
```

### 3.3 Rate-Limit Parameters (tuned in current script)
- **Per-page:** 200 authors
- **Inter-page delay:** 0.12s
- **429 backoff:** 30 / 60 / 90 / 120 / 150 / 180s (exponential, max 6 retries)
- **DNS error handling:** 60s wait, max 3 retries
- **Inter-university delay:** 3s (normal), 45s (after zero-result university)
- **Max pages per university:** 60 (= up to 12,000 authors/university)

### 3.4 Expected Yield

| University | OpenAlex authors | Est. new records |
|---|---|---|
| SWU | ~5,150 | ~3,500 |
| BUU | ~3,000 | ~2,100 |
| SU | ~2,000 | ~1,400 |
| TSU | ~4,000 | ~1,500 |
| KMUTT | ~2,500 | ~2,000 |
| PSU | ~4,500 | ~3,800 |
| KMITL | ~3,000 | ~2,100 |
| TU | ~3,500 | ~2,100 |
| KMUTNB | ~2,000 | ~1,700 |
| WU | ~3,000 | ~1,800 |
| CMU, KU, CU (expand) | ~10,000 | ~3,000 |
| **TOTAL** | — | **~25,000 new** |

Grand Total after Wave 57A: **~85,000 records**

---

## 4. Wave 57B — Email Enrichment (HTML crawl)

Run **after** 57A commits cleanly. These universities have good OpenAlex coverage but near-zero emails.

**Method:** SKILL.state pipeline via `run_acquire.py` (HTML, not OpenAlex — OpenAlex has no emails)

| University | Records | Email% | Target URL |
|---|---|---|---|
| NIDA | 1,625 | 2% | `https://www.nida.ac.th/th/faculty/` |
| MSU (Mahasarakham) | 1,413 | 9% | `https://personnel.msu.ac.th/` |
| MFU | 2,454 | 22% | `https://personnel.mfu.ac.th/` |
| UBU (Ubon Ratchathani) | 987 | 25% | `https://www.ubu.ac.th/` (faculty pages) |
| UP (Phayao) | 1,300 | 31% | `https://www.up.ac.th/` (faculty pages) |

---

## 5. Step-by-Step Execution Order (Tomorrow)

```
Step 1  Verify OpenAlex quota reset
        → python -c "import urllib.request, json; ..."
        → Test SWU: should return count ~5,150

Step 2  Verify unconfirmed IDs (one request each, 0.5s gap)
        → BUU I129488602, SU I102985835, PSU I183412441,
          KMITL I16426522, KMUTNB I4210090662, TU I110458564

Step 3  Lookup missing IDs for TSU and WU via institution search

Step 4  Update TARGET_UNIVERSITIES in run_wave57_top_universities_enrichment.py
        if any IDs are wrong (replace with correct ones from Step 2–3)

Step 5  Run Wave 57A
        → python backend/scripts/crawlers/run_wave57_top_universities_enrichment.py
        → Monitor until complete (~30–60 min depending on rate limits)

Step 6  Verify DB totals per university

Step 7  Run pytest
        → cd backend && pytest tests/ -x -q

Step 8  Run Wave 57B email enrichment (SKILL.state, NIDA first)
        → python backend/scripts/agentic_pipeline/run_acquire.py --url ... --univ NIDA

Step 9  Update CHANGELOG.md

Step 10 Run sync_system_status.py to update PROJECT_STRUCTURE_AND_WORKFLOW.md
```

---

## 6. Files Reference

| File | Purpose |
|---|---|
| `backend/scripts/crawlers/run_wave57_top_universities_enrichment.py` | Main Wave 57A script (ready, backoff fixed) |
| `backend/data/agent_states/wave57_*.json` | Per-university checkpoints (auto-created) |
| `CHANGELOG.md` | Add entry after Wave 57 completes |
| `PROJECT_STRUCTURE_AND_WORKFLOW.md` | Update via `sync_system_status.py` |

---

## 7. Notes & Risks

- **OpenAlex rate limit:** Daily quota resets overnight (UTC). Test with 1 request before full run. If still blocked, wait another hour.
- **RMUTT (Thanyaburi):** Only 1 record in DB. OpenAlex does not have a separate institution ID — needs dedicated HTML crawl in a future wave.
- **MU (Mahidol):** Already 98% OpenAlex — skip 57A, not worth the quota.
- **SUT:** Already 89% OpenAlex — skip 57A.
- **Pre-existing pytest failure:** `test_phase2_bibliometric_monotonicity_invariants` fails with `ModuleNotFoundError` for `clean_and_deduplicate_database_2026_09_13` (archived in prior session). Not caused by Wave 57 — ignore or skip that test.
