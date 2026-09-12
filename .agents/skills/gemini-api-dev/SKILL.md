---
name: gemini-api-dev
description: Guidelines, SDK conventions, and model selection for developing applications powered by the Gemini API within Thai EduCenter. Covers current models (gemini-3.8-flash, gemini-3.5-flash-lite, gemini-3.1-pro-preview), structured output extraction, client pooling, and deprecation guardrails.
---

# Gemini API Development Guide & Standards

This skill codifies the best practices and conventions for integrating the Google Gemini API into the Thai EduCenter backend, crawler pipelines, and agent systems.

## 1. Active Models & Hierarchy

### Production Models
- **`gemini-3.8-flash`**: Primary balanced model (1M tokens) for web extraction, unstructured content parsing, and multi-turn agentic workflows.
- **`gemini-3.5-flash-lite`**: High-speed, cost-efficient model for sub-2.5s interactive search refinement, psychometric quiz analysis, and prompt generation.
- **`gemini-3.1-pro-preview`**: Deep reasoning and research model for complex schema synthesis, disambiguation, and cross-source reconciliation.
- **`gemini-embedding-2-preview` / `gemini-embedding-001`**: 768-dimensional text embedding models used for pgvector semantic search (`dim=768`).

### Deprecation Guardrails
> [!WARNING]
> Models such as `gemini-2.0-*` and `gemini-1.5-*` are **legacy and deprecated**.
> Prefer the Gemini 3.x series for new generation code; `gemini-2.5-*` models remain available.
> Use the documented embedding ID `gemini-embedding-2-preview` rather than `gemini-embedding-2`.

---

## 2. SDK Usage Standards (`google-genai`)

Always use the modern `google-genai` SDK (`from google import genai`). The legacy `google-generativeai` package is deprecated.

### Client Pooling & Key Rotation Pattern
```python
import os
from google import genai
from google.genai import types

# Client pooling helper
_client_cache: dict[str, genai.Client] = {}

def get_gemini_client(api_key: str | None = None) -> genai.Client:
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if key not in _client_cache:
        _client_cache[key] = genai.Client(api_key=key)
    return _client_cache[key]
```

### Structured Output with Pydantic v2
When extracting structured data (curriculum, faculty profiles, research tags), always pass `response_schema` and `response_mime_type='application/json'`:

```python
from pydantic import BaseModel, Field

class FacultyProfile(BaseModel):
    full_name_th: str
    academic_title_th: str | None = None
    research_interests: list[str] = Field(default_factory=list)

client = get_gemini_client()
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Extract faculty data...",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=FacultyProfile,
        temperature=0.1,
    ),
)
data = FacultyProfile.model_validate_json(response.text)
```

---

## 3. High-Performance & DSA Rules
1. **No Sequential LLM Calls in Search Loops:** Never execute Gemini API calls inside per-result iteration loops.
2. **Deterministic Pruning Before Calling LLM:** Always strip HTML boilerplate using `ContentPruner` (trafilatura) before prompt injection to save 80%+ input tokens.
3. **Embedding Caching:** All query embeddings must check the in-memory `LRUCache` (`_embedding_cache`) before calling `embed_content`.
4. **Prompt Injection Sanitization:** Sanitize user input using `sanitize_for_prompt` to neutralize instruction overrides and strip null bytes (`\x00`).
