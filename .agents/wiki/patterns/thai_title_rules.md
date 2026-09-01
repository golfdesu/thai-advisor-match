# Thai Academic Title Normalization & Edge-Cases
<!-- Reference: WikiSkill - Pattern Knowledge (arXiv:2608.27454v1) -->

## Common Multi-Title Patterns

| Raw Title in Web HTML | Normalized Thai Title | Base Clean Name Pattern |
| :--- | :---: | :--- |
| `ศ.ดร. ศ.ดร. มานะ ใจดี` (Duplicate Prefix) | `ศ.ดร.` | `มานะ ใจดี` |
| `ศาสตราจารย์ ดร. สมชาย มุ่งมั่น` | `ศ.ดร.` | `สมชาย มุ่งมั่น` |
| `รองศาสตราจารย์ ดร. กิตติชัย โสจิพรรณ` | `รศ.ดร.` | `กิตติชัย โสจิพรรณ` |
| `ผู้ช่วยศาสตราจารย์ ดร. วิทยา ประเสริฐ` | `ผศ.ดร.` | `วิทยา ประเสริฐ` |
| `ศ.(พิเศษ) ดร. ...` | `ศ.(พิเศษ) ดร.` | Strip prefix before fuzzy match |
| `พญ.ดร.` / `นพ.ดร.` (Medical Doctor + Ph.D.) | `พญ.ดร.` / `นพ.ดร.` | Preserve clinical prefix |
| `สพ.ญ.ดร.` / `น.สพ.ดร.` (Veterinary + Ph.D.) | `สพ.ญ.ดร.` | Preserve clinical prefix |

---

## Strict Sanitization Rules
1. **Never retain Thai 10-digit phone numbers** (e.g. `08x-xxx-xxxx` or `053-94xxxx`) — auto-redact to `[REDACTED_PHONE]`.
2. **Strip title before running Levenshtein / RapidFuzz distance** — title variations (e.g. `ผศ.` vs `ผู้ช่วยศาสตราจารย์`) artificially lower fuzzy similarity if not removed.
