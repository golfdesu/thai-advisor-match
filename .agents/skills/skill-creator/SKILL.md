---
name: skill-creator
description: Methodology for authoring, evaluating, and iteratively refining agent skills. Enforces progressive disclosure (<500 lines), A/B subagent testing (with-skill vs baseline), quantitative assertion drafting, and timing/token telemetry.
---

# Skill Creator & Optimization Guide

This skill standardizes the creation, audit, and empirical evaluation of autonomous agent skills across the workspace.

## 1. Anatomy of a High-Quality Skill

Every skill must reside in its own self-contained directory:

```text
skill-name/
├── SKILL.md            # (Required) YAML frontmatter + concise operational instructions
├── scripts/            # (Optional) Deterministic CLI utilities & automation scripts
├── references/         # (Optional) In-depth domain docs, schemas, or API references
└── assets/             # (Optional) Templates, seeds, or mock fixtures
```

### Progressive Disclosure Rules
- **Metadata (Frontmatter):** `name` and `description` must clearly articulate *what* the skill does and *when* it should trigger.
- **Body (< 500 Lines):** The main `SKILL.md` body should contain actionable decision trees, hard invariants, and core workflows. Offload large reference tables (>300 lines) or specialized variants to `references/`.
- **Imperative Voice:** Instructions must use concise, imperative language ("Extract...", "Validate...", "Enforce...") without filler explanations.

---

## 2. The 4-Stage Iterative Skill Lifecycle

```text
1. Capture Intent & Invariants
   └─ Identify the exact trigger conditions, inputs, outputs, and non-negotiable rules.

2. Draft Concise SKILL.md
   └─ Structure with high-priority rules first, step-by-step workflow, and error recovery.

3. Empirical A/B Evaluation
   ├─ Run Test Case WITH skill
   ├─ Run Test Case WITHOUT skill (or old skill version as baseline)
   └─ Record timing, token consumption, and failure modes.

4. Formulate Quantitative Assertions & Refine
   └─ Measure success rate against concrete assertions. Tighten instructions where agents deviate.
```

---

## 3. A/B Evaluation Pattern

To test whether a skill meaningfully improves task performance:
1. **Define Test Prompts:** Select 2-3 representative user requests covering both standard and edge-case scenarios.
2. **Execute Dual Runs:**
   - Run A: Subagent equipped with the candidate skill.
   - Run B: Baseline subagent without the skill.
3. **Draft Objective Assertions:**
   - *Format Validity:* Output conforms to required JSON schema or markdown structure.
   - *Constraint Adherence:* Zero prohibited actions (e.g. no deprecated models, no forbidden imports).
   - *Accuracy:* Expected entities, formulas, or metadata are fully present.
4. **Capture Metrics:** Compare total execution time, total tokens, and assertion pass rate.
