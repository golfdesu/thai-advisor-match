# When to Mock

Mock at **system boundaries** only. In this project, the default is local-first: use the local PostgreSQL container for database integration tests rather than replacing SQLAlchemy with a mock.

## Thai EduCenter boundaries

Mock only these boundaries when a test would otherwise make a network call, spend quota, or depend on nondeterministic state:

- **Gemini API**: `embedding_service.get_embedding()` and `genai.Client.models.generate_content()`
- **External HTTP**: university directory crawlers and OpenAlex requests
- **Time and randomness**: cache expiry, retry backoff, and generated identifiers
- **Checkpoint filesystem**: `backend/data/agent_states/` reads and writes in pipeline tests

Do not mock:

- SQLAlchemy ORM behavior when a local test database is available
- `tokenize_mixed()` or `FACULTY_LEXICAL_INDEX`; test tokenizer/index symmetry directly
- Pydantic models; validate real payloads, including LLM `null` list fields
- `dsa_utils.LRUCache` and `TopKHeap`; they are deterministic internal algorithms
- `sanitize_for_prompt`; test the actual redaction and injection-neutralization behavior

## Designing for Mockability

At a system boundary, pass the dependency in rather than constructing it inside the function.

**1. Use dependency injection**

```python
# EASY TO MOCK: the embedding boundary is injectable.
async def get_query_vector(text: str, embed_fn):
    return await embed_fn(text)

# HARD TO MOCK: the function creates a network client internally.
async def get_query_vector(text: str):
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return await client.models.embed_content(model="gemini-embedding-2", contents=text)
```

In production, pass the real `embedding_service.get_embedding` function. In a focused test, pass a deterministic 768-value fixture or a fake boundary object. Never place a fake inside `tokenize_mixed`, the BM25 scorer, or SQLAlchemy query construction.

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```python
# GOOD: Each operation has one shape and one mockable boundary.
class GeminiClient:
    async def embed_text(self, text: str) -> list[float]: ...
    async def extract_faculty_profile(self, html: str) -> "FacultyProfile": ...
    async def generate_thesis_explanation(self, query: str, advisor: "FacultyMember") -> str: ...

# BAD: Every test must understand operation-specific branching.
class GeminiClient:
    async def call(self, operation: str, payload: dict) -> dict: ...
```

The SDK-style approach means:

- Each fake returns one specific shape
- Test setup contains no operation-dispatch conditionals
- A test makes clear which external operation it exercises
- Type checking can validate each operation's input and output

## Test-boundary invariants

- Keep embedding fixtures exactly 768-dimensional, matching the `Vector(768)` columns.
- Do not send real Thai National IDs, API keys, phone numbers, or other PII to external services from tests.
- Use `sanitize_for_prompt` before any test value is passed to a prompt builder.
- Keep crawler and OpenAlex fixtures local; never point bulk or high-throughput tests at Supabase.
