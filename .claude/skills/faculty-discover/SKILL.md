---
name: faculty-discover
description: Discover unlisted and newly appointed high-impact faculty members using 2024-2026 OpenAlex publication footprints, with strict confidence scoring (>= 0.85) and quarantine state management.
---

# Stage 6: Unlisted Faculty Discovery & Confidence Quarantine Skill

This skill overcomes central university directory lag (6–24 months) by mining recent affiliated publication footprints on OpenAlex (2024–2026) to identify active, high-impact scholars who are missing from central faculty portals.

## Operational Standards
1. **Selection Over Generation:** Query authoritative academic indices (OpenAlex Works & Authors APIs) for verified metrics (`h_index >= 3`, `works_count >= 8`, recent peer-reviewed publications).
2. **Confidence Threshold (< 0.85 Quarantine):** 
   - Every candidate is evaluated on academic credentials, department affiliation clarity, Thai nomenclature authenticity, and LLM resolution confidence.
   - Candidates scoring `< 0.85` or exhibiting flags are quarantined to `backend/data/agent_states/skill_state_unresolved_quarantine.json`.
   - Only candidates scoring `>= 0.85` are vectorized and committed to local PostgreSQL.
3. **Local-First Zero-Egress Invariant:** Embeddings (768-dim) and database commits apply strictly to local PostgreSQL (`localhost:5432/advisor_match`). Zero remote Supabase sync.

---

## Discovery Workflow (5-Step Footprint Mining)

1. **Institutional Recent Works Harvest (Footprint 3):**
   - Query OpenAlex Works API for target university ROR / OpenAlex ID (e.g., Chulalongkorn `I158708052`, Chiang Mai `I48076826`).
   - Filter `publication_year:2024|2025|2026` sorted by citation count.
2. **Symmetric Set Difference ($S_{\text{harvested}} \setminus S_{\text{db}}$):**
   - Clean Latin author names and check against existing verified faculty database.
   - Retain only authors not present in the current database.
3. **Institutional Affiliation & Qualification Verification:**
   - Verify active affiliation with the target university and extract department string.
   - Filter for proven academic track record (`h_index >= 3`, `works_count >= 8`).
4. **Thai Academic Nomenclature Resolution:**
   - Resolve authentic Thai academic title (`ศ.ดร.`, `รศ.ดร.`, `ผศ.ดร.`, `อ.ดร.`, `ศ.นพ.`, etc.), full name, faculty, and department via `gemini-3.5-flash-lite`.
5. **Confidence Evaluation & Quarantine Checkpointing:**
   - Evaluate objective confidence score ($0.0 \dots 1.0$).
   - If `score < 0.85`: Route to `skill_state_unresolved_quarantine.json`.
   - If `score >= 0.85`: Checkpoint to `skill_state_unlisted_discovery.json`, compute 768-dim Gemini vector embedding, and insert into `faculties` table.

---

## Execution Command

Run the discovery pipeline:
```bash
python backend/scripts/enrichment/discover_unlisted_faculty.py
```

Inspect discovery and quarantine checkpoints:
```bash
python -c "
import json

with open('backend/data/agent_states/skill_state_unlisted_discovery.json', 'r', encoding='utf-8') as f:
    qualified = json.load(f)
print(f'Qualified Records: {len(qualified)}')

try:
    with open('backend/data/agent_states/skill_state_unresolved_quarantine.json', 'r', encoding='utf-8') as f:
        quarantined = json.load(f)
    print(f'Quarantined Records: {len(quarantined)}')
except FileNotFoundError:
    print('Quarantine file not created yet.')
"
```
