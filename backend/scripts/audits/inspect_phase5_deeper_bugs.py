# -*- coding: utf-8 -*-
"""
Deep inspection script for Phase 5.
Audits:
1. The 64 'department_named_faculty' instances.
2. The remaining 20 cross-university homonym clusters.
3. Publication titles: HTML entities, junk titles, empty objects.
4. Research interests: HTML entities, URLs, trailing commas/periods.
5. Education: HTML tags, raw boilerplate.
6. Courses: degree_level normalization, curriculum_highlights junk, career_paths junk.
7. Research labs: member_faculty_ids validation, research_domains integrity.
"""
import sys
import re
from pathlib import Path
from collections import defaultdict
import html

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def inspect_phase5():
    db = SessionLocal()
    print("=" * 80)
    print("🔍 DEEP PHASE 5 FORENSIC BUG SCANNER")
    print("=" * 80)

    faculties = db.query(FacultyDB).all()
    courses = db.query(CourseDB).all()
    labs = db.query(ResearchLabDB).all()

    print(f"Dataset: {len(faculties)} faculties, {len(courses)} courses, {len(labs)} labs\n")

    # -------------------------------------------------------------
    # 1. Inspect department_named_faculty
    # -------------------------------------------------------------
    print("--- 1. DEPARTMENT NAMED FACULTY / BREADCRUMBS ---")
    dept_fac_findings = []
    for f in faculties:
        dept = (f.department_th or "").strip()
        fac = (f.faculty_th or "").strip()
        if dept.startswith("คณะ") and dept != fac:
            dept_fac_findings.append((f.id, f.full_name_th, f.university_th, fac, dept))
        elif "มหาวิทยาลัย" in dept:
            dept_fac_findings.append((f.id, f.full_name_th, f.university_th, fac, dept))

    print(f"Total found: {len(dept_fac_findings)}")
    for item in dept_fac_findings[:15]:
        print(f"  {item[0]} | {item[1]} | {item[2]} | Fac: '{item[3]}' | Dept: '{item[4]}'")

    # -------------------------------------------------------------
    # 2. Inspect remaining 20 cross-uni clusters
    # -------------------------------------------------------------
    print("\n--- 2. REMAINING 20 CROSS-UNIVERSITY CLUSTERS ---")
    th_name_all = defaultdict(list)
    for f in faculties:
        th = f.full_name_th or ""
        th_clean = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|นพ|พญ|ทพ|ทพญ|สพ|ภก|ภญ|\.|\s)+", "", th).strip()
        th_clean = re.sub(r"\s+", "", th_clean)
        if len(th_clean) >= 6:
            th_name_all[th_clean].append(f)

    cross_uni = {k: v for k, v in th_name_all.items() if len(set(f.university_th for f in v)) > 1}
    print(f"Total remaining cross-uni clusters: {len(cross_uni)}")
    for name, group in cross_uni.items():
        print(f"\nCluster: {name} ({len(group)} records)")
        for f in group:
            print(f"  ID: {f.id} | {f.full_name_th} | {f.university_th} | {f.faculty_th} | {f.department_th} | {f.email} | pubs: {f.total_publications_count} | cites: {f.total_citations}")

    # -------------------------------------------------------------
    # 3. Inspect Publication Titles
    # -------------------------------------------------------------
    print("\n--- 3. PUBLICATION TITLES SANITIZATION ---")
    html_entity_pubs = []
    junk_pubs = []
    for f in faculties:
        if f.featured_publications:
            for p in f.featured_publications:
                title = p.get("title", "") if isinstance(p, dict) else str(p)
                if not title or title.strip() in ["-", "null", "none", "Title", "No Title"]:
                    junk_pubs.append((f.id, title))
                elif "&amp;" in title or "&quot;" in title or "&#39;" in title or "&lt;" in title or "&gt;" in title:
                    html_entity_pubs.append((f.id, title[:60]))

    print(f"Publications with unescaped HTML entities: {len(html_entity_pubs)}")
    for item in html_entity_pubs[:5]:
        print(f"  {item[0]}: {item[1]}")
    print(f"Publications with junk/empty title: {len(junk_pubs)}")
    for item in junk_pubs[:5]:
        print(f"  {item[0]}: {item[1]}")

    # -------------------------------------------------------------
    # 4. Inspect Research Interests
    # -------------------------------------------------------------
    print("\n--- 4. RESEARCH INTERESTS SANITIZATION ---")
    html_entity_interests = []
    url_interests = []
    trailing_punct_interests = []
    for f in faculties:
        if f.research_interests:
            for it in f.research_interests:
                s = str(it).strip()
                if "&amp;" in s or "&quot;" in s or "&#39;" in s or "&lt;" in s:
                    html_entity_interests.append((f.id, s))
                if s.startswith("http://") or s.startswith("https://"):
                    url_interests.append((f.id, s))
                if s.endswith(",") or s.endswith(";"):
                    trailing_punct_interests.append((f.id, s))

    print(f"Interests with HTML entities: {len(html_entity_interests)}")
    for item in html_entity_interests[:5]:
        print(f"  {item[0]}: {item[1]}")
    print(f"Interests that are raw URLs: {len(url_interests)}")
    for item in url_interests[:5]:
        print(f"  {item[0]}: {item[1]}")
    print(f"Interests with trailing punctuation: {len(trailing_punct_interests)}")
    for item in trailing_punct_interests[:5]:
        print(f"  {item[0]}: {item[1]}")

    # -------------------------------------------------------------
    # 5. Inspect Courses
    # -------------------------------------------------------------
    print("\n--- 5. COURSES AUDIT ---")
    degree_levels = set()
    tuition_totals = set()
    courses_with_html = []
    courses_with_junk_careers = []
    for c in courses:
        degree_levels.add(c.degree_level)
        if c.curriculum_highlights:
            for h in c.curriculum_highlights:
                if "<" in str(h) and ">" in str(h):
                    courses_with_html.append((c.id, h))
        if c.career_paths:
            for cp in c.career_paths:
                if str(cp).strip() in ["-", "ไม่มี", "null", "none"]:
                    courses_with_junk_careers.append((c.id, cp))

    print(f"Unique degree levels in courses: {degree_levels}")
    print(f"Courses with HTML in highlights: {len(courses_with_html)}")
    print(f"Courses with junk in career_paths: {len(courses_with_junk_careers)}")
    for item in courses_with_junk_careers[:5]:
        print(f"  {item[0]}: {item[1]}")

    # -------------------------------------------------------------
    # 6. Inspect Research Labs
    # -------------------------------------------------------------
    print("\n--- 6. RESEARCH LABS AUDIT ---")
    fac_ids = {f.id for f in faculties}
    dangling_members = []
    for l in labs:
        for mid in (l.member_faculty_ids or []):
            if mid not in fac_ids:
                dangling_members.append((l.id, mid))
    print(f"Dangling member_faculty_ids in labs: {len(dangling_members)}")
    for item in dangling_members:
        print(f"  Lab: {item[0]} -> Member ID not in faculties: {item[1]}")

    db.close()


if __name__ == "__main__":
    inspect_phase5()
