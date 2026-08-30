---
name: ui-seo-metadata
description: Guidelines and scripts for generating robust SEO metadata, Open Graph tags, and JSON-LD structured data for Next.js 16 dynamic pages.
---

# SEO Metadata Generation

This skill is used to ensure all public-facing pages (Courses and Faculty Profiles) in the Next.js 16 frontend are highly discoverable on search engines like Google.

## Metadata Requirements
1. **Dynamic Metadata (`generateMetadata`):** 
   - Implement standard Next.js 16 `generateMetadata` in `frontend/src/app/advisor/[id]/page.tsx` and course pages.
   - **Title:** e.g., "Asst. Prof. Dr. Name - Faculty of Engineering | Thai EduCenter"
   - **Description:** A concise 150-160 character summary of their research interests and academic focus in Thai.
2. **Open Graph & Twitter Cards:**
   - Include `og:title`, `og:description`, `og:image` (using the faculty's `image_url` with fallback).
3. **JSON-LD Structured Data:**
   - Inject `<script type="application/ld+json">` into the DOM.
   - For Advisors: Use `Person` schema, linking their `jobTitle`, `worksFor` (University), and `alumniOf` (Education).
   - For Courses: Use `Course` schema, detailing `coursePrerequisites`, `educationalCredentialAwarded`, and `provider`.

## Execution Steps
- When updating UI components, ensure that metadata generation does NOT block the initial page render.
- Fetch SEO data concurrently with page hydration.
- Validate the generated JSON-LD using the Google Rich Results Test format conventions.

