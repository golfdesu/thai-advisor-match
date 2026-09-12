---
name: webapp-testing
description: Methodologies and tools for interacting with and testing the local Next.js 16 web application using Playwright. Covers UI verification, navigation flow checks, browser console error monitoring, visual screenshot inspection, and SSR hydration validation.
---

# Web Application Testing & Verification (Playwright)

This skill provides testing procedures for validating frontend routes, UI interactions, and responsive states of the Next.js 16 application (`http://localhost:3000`).

## 1. Decision Tree: Reconnaissance-then-Action

Always follow the **Reconnaissance-then-Action** approach when testing interactive web features:

```text
Target UI Feature
  │
  ├─ 1. Reconnaissance:
  │    ├─ Navigate to target route (e.g., '/', '/career-discovery', '/advisor/1')
  │    ├─ Wait for page hydration & networkidle
  │    └─ Capture rendered DOM & check browser console logs for React 19 hydration errors
  │
  ├─ 2. Action:
  │    ├─ Locate interactive elements using accessible roles or text (data-testid, button text, search inputs)
  │    ├─ Simulate user input (typing query, clicking filter tags, selecting quiz choices)
  │    └─ Wait for async state / dynamic route update
  │
  └─ 3. Verification:
       ├─ Assert expected cards, tags, or scores appear in the DOM
       ├─ Capture screenshot to verify layout, responsive wrapping, and dark mode class
       └─ Verify zero uncaught JavaScript errors or failed network requests (HTTP 4xx/5xx)
```

## 2. Invariants & Health Checks

When testing the frontend, verify compliance with these core architectural standards:
1. **Zero Hydration Mismatches:** Inspect browser logs for React 19 errors (e.g., `Encountered a script tag...` or SSR DOM discrepancies).
2. **Next.js Image Integrity:** Ensure `<Image />` components render correctly without broken image icons. Fallback avatars (`getAdvisorAvatarUrl`) must display when remote images fail.
3. **Class-based Dark Mode:** Verify that toggling dark mode adds `class="dark"` to the `<html>` element and applies proper theme styling.
4. **Instant Search on Interaction:** Clicking popular chips or suggestion tags must immediately execute the search query without requiring Enter or double-clicks.

## 3. Running Web App Tests

Playwright scripts can run in headless mode via Python:

```bash
pytest backend/tests/test_webapp_playwright.py -v
```
