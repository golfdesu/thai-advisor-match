---
name: qa-evaluate-search
description: Methodology for systematically benchmarking and evaluating the semantic search and retrieval quality of pgvector and Gemini embeddings.
---

# Evaluate Search Quality (Semantic RAG Testing)

This skill is used to evaluate the accuracy of the Semantic Advisor Matching engine.

## Evaluation Process
1. **Define Test Queries:** Create a set of diverse Thai research proposals or topics (e.g., "อยากทำวิจัย AI ประยุกต์ใช้ในการวินิจฉัยโรคมะเร็ง", "ระบบ Microgrid พลังงานแสงอาทิตย์").
2. **Execute Vector Search:** Use the `backend/app/api/routes_search.py` endpoints or directly query the database using the 768-dim `gemini-embedding-2` vector against `pgvector` with HNSW indexes.
3. **Analyze Re-ranking (Hybrid Multi-Evidence):**
   - Verify that the Cosine Similarity score is correct.
   - Ensure the 4-tier composite score is properly applied (Semantic, Core Interests, Publication Synergy, Academic Track Record).
4. **Generate Evaluation Report:** Create a markdown artifact comparing the expected top advisors vs the actual returned advisors, highlighting any hallucinations or missing semantic links.
5. **Prompt/Ontology Tuning:** If results are poor, recommend updates to the `THAI_EN_SYNONYMS` regex ontology in `embedding_service.py`.

## Rules
- Do NOT test on production user data. Use synthetic or pre-defined benchmark queries.
- Ensure all queries test the latency requirement (< 500ms).

