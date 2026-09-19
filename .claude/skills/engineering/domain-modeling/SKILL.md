---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a CONTEXT.md, or recording or editing an ADR.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily: only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed. For this project, the system-wide glossary belongs at the repository root as `CONTEXT.md`; keep implementation rules in `AGENTS.md` and skills, not in the glossary.

## Thai EduCenter domain

Use these canonical terms when updating the glossary:

| Thai term | English | Definition |
|---|---|---|
| อาจารย์ที่ปรึกษา | Advisor | A faculty member who supervises graduate research. This is a role, not automatically every person in the faculty directory. |
| หลักสูตร | Program | A degree program. It is not a single course or subject. |
| รายวิชา | Course | A single subject within a program, represented by course data in the application. |
| ห้องปฏิบัติการ | Research Lab | A research group or center with research domains, members, and optionally one lead advisor. |
| มหาวิทยาลัย | Institution | A university represented by its canonical Thai and English names. |
| คะแนนความเหมาะสม | Match Score | The 0–100 composite percentage returned to a student; distinguish it from raw cosine similarity and BM25 score. |
| ความสนใจวิจัย | Research Interest | A faculty member's declared research topic, represented as a list of terms or phrases. |
| ชุดทดสอบ RIASEC | Career Quiz | The project's career-discovery assessment and its RIASEC breakdown. |

Challenge these overloaded terms immediately:

- **ค้นหา / search**: clarify advisor search, course search, lab search, vector retrieval, or BM25 retrieval.
- **score**: clarify `match_score` percentage, cosine similarity, or BM25 score.
- **database**: clarify local Docker PostgreSQL versus Supabase production; the local-first invariant applies by default.
- **embedding**: clarify a request-time query vector versus a stored 768-dimensional entity vector.
- **advisor / faculty**: clarify whether the person is merely listed faculty or is acting as a thesis advisor.
- **program / course**: clarify a degree program versus an individual subject.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up: capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
