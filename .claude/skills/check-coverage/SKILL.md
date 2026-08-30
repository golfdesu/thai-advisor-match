---
name: check-coverage
description: Checks the completeness of course counts in the Supabase database against the official targets of each university in Thailand.
---

# University Course Coverage Checker Skill

When the user triggers `/check-coverage` or wants to check which university is missing course data:

1. Run the coverage check script:
   ```bash
   python backend/scripts/check_completeness.py
   ```

2. Summarize the coverage per university (Current vs Official Target).
3. Identify the universities that have significantly lower counts than their targets to prioritize data scraping in the next iteration.

