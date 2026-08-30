---
name: qa-tdd
description: Methodologies and workflows for Test-Driven Development (TDD) across the Thai EduCenter monorepo using Pytest (Backend) and Vitest/Jest (Frontend).
---

# Test-Driven Development (TDD) Workflow

This skill enforces a strict TDD lifecycle when developing new features or modifying existing logic. The goal is to ensure high reliability for the AI Advisor matching engine and UI components.

## TDD Lifecycle (Red-Green-Refactor)
When tasked with creating or updating a feature, you MUST follow these steps in order:
1. **RED (Write the Test):** Write the unit or integration tests for the expected behavior BEFORE writing the actual implementation code. Ensure the test fails.
2. **GREEN (Implement):** Write the minimal amount of application code required to make the tests pass.
3. **REFACTOR (Optimize):** Refactor the implementation to meet the project's DSA and High-Performance Architecture standards (e.g., $O(1)$ LRU Cache, vector column deferrals) while keeping the tests passing.

## Backend Testing (Pytest)
- **Location:** `backend/tests/`
- **Scope:** 
  - Ensure API endpoints (FastAPI) return expected HTTP status codes.
  - Mock `google-genai` clients and Supabase database sessions using `pytest-mock` or dependency injection overrides.
  - Verify `TopKHeap` and `ClientLRUCache` logic behaves correctly under concurrency.

## Frontend Testing (Vitest/Jest & React Testing Library)
- **Location:** `frontend/__tests__/` or alongside components (e.g., `Component.test.tsx`).
- **Scope:**
  - Test client-side state hooks and tab switching without triggering unintended network requests.
  - Verify that `<html class="dark">` specific utility classes are present when the dark mode is toggled.

