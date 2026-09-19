# Good and Bad Tests

These examples use the Thai EduCenter backend seams. Keep assertions independent of implementation details and use the smallest fixture that demonstrates user-visible behavior.

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```python
# GOOD: Tests observable search behavior through the HTTP boundary.
def test_search_returns_ranked_advisors_for_thai_query(client):
    response = client.post(
        "/api/v1/search/",
        json={"query": "ปัญญาประดิษฐ์", "top_k": 5},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert results[0]["match_score"] >= results[-1]["match_score"]
```

```python
# GOOD: Tests the public normalization behavior at the regression seam.
def test_clean_display_name_preserves_names_starting_with_dr():
    from app.models.schema import _clean_display_name

    # A Thai name beginning with ดร must not be stripped as a title.
    assert _clean_display_name("ดร.", "ดร. ดรุณี สถิตถาวร") == "ดรุณี สถิตถาวร"
```

Characteristics:

- Tests behavior users or callers care about
- Uses a public API or an agreed behavioral seam
- Survives internal refactors
- Describes WHAT, not HOW
- Uses known-good literals or independently sourced expectations

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```python
# BAD: Verifies that an internal collaborator was called rather than
# verifying the search result a user receives.
def test_search_calls_embedding_service(mocker, client):
    mock_embed = mocker.patch("app.core.embedding_service.embedding_service.get_embedding")
    client.post("/api/v1/search/", json={"query": "AI", "top_k": 5})
    mock_embed.assert_called_once()  # Tests HOW, not WHAT.
```

Red flags:

- Mocking internal collaborators
- Testing private methods without a real behavioral reason
- Asserting on call counts or call order
- A test breaks when refactoring without a behavior change
- The test name describes HOW rather than WHAT
- Verifying through a side channel instead of the interface

```python
# BAD: Bypasses the application interface and reaches directly into storage.
def test_faculty_is_saved(db_session):
    create_faculty(db_session, {"full_name_th": "อ. สมชาย"})
    row = db_session.execute(
        text("SELECT * FROM faculties WHERE full_name_th = :name"),
        {"name": "อ. สมชาย"},
    ).first()
    assert row is not None

# GOOD: Verifies the behavior through the API that callers use.
def test_faculty_is_retrievable(client):
    created = client.post("/api/v1/faculty/", json={"full_name_th": "อ. สมชาย"})
    faculty_id = created.json()["id"]

    retrieved = client.get(f"/api/v1/faculty/{faculty_id}")

    assert retrieved.status_code == 200
    assert retrieved.json()["full_name_th"] == "อ. สมชาย"
```

**Tautological tests**: Expected values restate the implementation, so the test passes by construction.

```python
# BAD: Recomputes the expected result with another sorting algorithm.
def test_top_k_heap_selects_top_results():
    from app.core.dsa_utils import TopKHeap

    heap = TopKHeap(k=2)
    for score, faculty_id in [(0.9, "a"), (0.5, "b"), (0.7, "c")]:
        heap.push(score, faculty_id)

    expected = sorted([(0.9, "a"), (0.5, "b"), (0.7, "c")], reverse=True)[:2]
    assert heap.top_k() == expected
```

```python
# GOOD: Expected ordering comes from the worked example, not from the
# implementation being tested.
def test_top_k_heap_selects_top_results():
    from app.core.dsa_utils import TopKHeap

    heap = TopKHeap(k=2)
    for score, faculty_id in [(0.9, "a"), (0.5, "b"), (0.7, "c")]:
        heap.push(score, faculty_id)

    top = heap.top_k()
    assert [faculty_id for _, faculty_id in top] == ["a", "c"]
```

For the same reason, do not build a BM25 expected value by calling `tokenize_mixed()` and the scorer in the assertion setup. Use a fixed fixture whose expected top document is known independently, as in `backend/tests/test_audited_bug_regressions.py`.
