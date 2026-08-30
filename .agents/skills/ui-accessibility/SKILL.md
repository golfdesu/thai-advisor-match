---
name: ui-accessibility
description: Guidelines and checklists for ensuring the Next.js 16 frontend meets WCAG accessibility standards for educational platforms.
---

# UI Accessibility (a11y) Validation

As an educational platform, Thai EduCenter must be accessible to all students, including those relying on screen readers or navigating via keyboard. Apply these checks when modifying UI components in `frontend/src/`.

## 1. Semantic HTML & ARIA
- Use semantic tags (`<header>`, `<main>`, `<nav>`, `<article>`, `<section>`) instead of nested `<div>` wrappers.
- For non-text interactables (like icon buttons from `lucide-react`), always include `aria-label` or visually hidden text (`sr-only` class).
- Maintain logical heading structures (`<h1>` down to `<h4>`). Never skip heading levels.

## 2. Keyboard Navigation
- Ensure all interactive elements (buttons, links, search inputs, custom dropdowns) are accessible via the `Tab` key.
- Custom interactive components must implement `onKeyDown` handlers (specifically for `Enter` and `Space`) if they mimic button behavior.
- Ensure the focus state is visible (using Tailwind's `focus:ring` or `focus:outline` utilities). Do NOT use `focus:outline-none` unless replacing it with a custom visible focus state.

## 3. Visual & Color Contrast (Tailwind v4)
- Ensure text elements have a minimum contrast ratio of 4.5:1 against their backgrounds.
- When configuring `@theme` variables or using `dark:*` variants, test the contrast in both Light and Dark modes.
- Do not convey essential information by color alone (e.g., add icons or text labels to error states, not just red borders).

## 4. Image Fallbacks
- All `<img>` and Next.js `<Image>` tags must have descriptive `alt` attributes.
- If an image is purely decorative (e.g., a background pattern), explicitly set `alt=""` so screen readers ignore it.

