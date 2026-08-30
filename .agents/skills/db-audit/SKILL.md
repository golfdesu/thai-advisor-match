---
name: db-audit
description: Audits the health and cleanliness of the Supabase database and detects missing embeddings, duplicates, and PDPA compliance issues.
---

# Database & Vector Hygiene Audit Skill

When the user triggers `/audit-db` or requests a database health check, proceed as follows:

1. Run the database audit script:
   ```bash
   python backend/scripts/audit_database_hygiene.py
   ```

2. Report the results to the user across 5 key dimensions:
   - **Inventory Status:** Total number of Courses and Faculties in the system.
   - **Vector Integrity (768-dim):** Missing embeddings count (must be 0).
   - **Redundancy & Duplicates:** Check for duplicate courses or faculty members.
   - **Mandatory Fields Hygiene:** Verify missing descriptions, URLs, and department fields.
   - **PDPA & Privacy:** Confirm no personal phone numbers are exposed and 100% of contact channels are official.


