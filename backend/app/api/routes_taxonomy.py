# -*- coding: utf-8 -*-
"""
Hierarchical Academic Taxonomy API for Thai EduCenter.
Serves cascading metadata (Region -> University -> Faculty -> Department)
with O(1) in-memory LRU caching for instant (sub-millisecond) UI filter updates.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, or_

from app.core.database import get_db
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
from app.core.taxonomy import UNIVERSITY_TAXONOMY, REGIONS_CONFIG, get_unis_for_region, get_university_info
from app.core.dsa_utils import LRUCache

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])

# In-memory DSA LRU Cache for taxonomy endpoints (0.01ms response time)
_TAXONOMY_CACHE = LRUCache[str, Any](capacity=1024)


@router.get("/regions")
def get_regions(db: Session = Depends(get_db)):
    """Return all geographical regions with university, advisor, course, and lab counts."""
    cache_key = "regions_overview"
    cached = _TAXONOMY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    # Compute overall counts in one pass
    f_total = db.query(func.count(FacultyDB.id)).scalar() or 0
    c_total = db.query(func.count(CourseDB.id)).scalar() or 0
    l_total = db.query(func.count(ResearchLabDB.id)).scalar() or 0

    results = []
    for r in REGIONS_CONFIG:
        rid = r["id"]
        unis = get_unis_for_region(rid)
        if not unis:
            results.append({
                "id": rid,
                "label_th": r["label_th"],
                "label_en": r["label_en"],
                "icon": r["icon"],
                "university_count": len(UNIVERSITY_TAXONOMY),
                "advisor_count": f_total,
                "course_count": c_total,
                "lab_count": l_total
            })
        else:
            f_count = db.query(func.count(FacultyDB.id)).filter(FacultyDB.university_th.in_(unis)).scalar() or 0
            c_count = db.query(func.count(CourseDB.id)).filter(CourseDB.university_th.in_(unis)).scalar() or 0
            l_count = db.query(func.count(ResearchLabDB.id)).filter(ResearchLabDB.university_th.in_(unis)).scalar() or 0
            results.append({
                "id": rid,
                "label_th": r["label_th"],
                "label_en": r["label_en"],
                "icon": r["icon"],
                "university_count": len(unis),
                "advisor_count": f_count,
                "course_count": c_count,
                "lab_count": l_count
            })

    _TAXONOMY_CACHE.put(cache_key, results)
    return results


@router.get("/universities")
def get_universities(
    region: Optional[str] = Query(None, description="Filter universities by region slug (e.g. north, south)"),
    db: Session = Depends(get_db)
):
    """
    Return universities filtered by region with academic counts.
    If region is omitted or 'all', returns all 37 institutions.
    """
    cache_key = f"unis:{region or 'all'}"
    cached = _TAXONOMY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    allowed_unis = get_unis_for_region(region)
    target_unis = allowed_unis if allowed_unis else list(UNIVERSITY_TAXONOMY.keys())

    # Pre-aggregate advisor, course, and lab counts per university
    f_counts = dict(
        db.query(FacultyDB.university_th, func.count(FacultyDB.id))
        .filter(FacultyDB.university_th.in_(target_unis))
        .group_by(FacultyDB.university_th)
        .all()
    )
    c_counts = dict(
        db.query(CourseDB.university_th, func.count(CourseDB.id))
        .filter(CourseDB.university_th.in_(target_unis))
        .group_by(CourseDB.university_th)
        .all()
    )
    l_counts = dict(
        db.query(ResearchLabDB.university_th, func.count(ResearchLabDB.id))
        .filter(ResearchLabDB.university_th.in_(target_unis))
        .group_by(ResearchLabDB.university_th)
        .all()
    )

    results = []
    for uname in target_unis:
        info = get_university_info(uname)
        adv_count = f_counts.get(uname, 0)
        crs_count = c_counts.get(uname, 0)
        lab_count = l_counts.get(uname, 0)
        results.append({
            "name_th": uname,
            "name_en": info.get("en", uname),
            "abbr": info.get("abbr", ""),
            "region": info.get("region", "central"),
            "advisor_count": adv_count,
            "course_count": crs_count,
            "lab_count": lab_count,
            "total_items": adv_count + crs_count + lab_count
        })

    # Sort universities by total items (most comprehensive first)
    results.sort(key=lambda x: x["total_items"], reverse=True)
    _TAXONOMY_CACHE.put(cache_key, results)
    return results


@router.get("/faculties")
def get_faculties(
    university: Optional[str] = Query(None, description="University name in Thai or English"),
    region: Optional[str] = Query(None, description="Region slug"),
    db: Session = Depends(get_db)
):
    """
    Return distinct faculties under a university (or region).
    Includes counts of advisors and courses available in each faculty.
    """
    cache_key = f"faculties:{university or 'any'}:{region or 'any'}"
    cached = _TAXONOMY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    f_query = db.query(FacultyDB.faculty_th, func.count(FacultyDB.id)).filter(FacultyDB.faculty_th.isnot(None), FacultyDB.faculty_th != "")
    c_query = db.query(CourseDB.faculty_th, func.count(CourseDB.id)).filter(CourseDB.faculty_th.isnot(None), CourseDB.faculty_th != "")

    if university and university.strip().lower() != "all":
        u_clean = university.strip()
        u_cond_f = or_(FacultyDB.university_th == u_clean, FacultyDB.university == u_clean)
        u_cond_c = or_(CourseDB.university_th == u_clean, CourseDB.university == u_clean)
        f_query = f_query.filter(u_cond_f)
        c_query = c_query.filter(u_cond_c)
    elif region and region.strip().lower() != "all":
        unis = get_unis_for_region(region)
        if unis:
            f_query = f_query.filter(FacultyDB.university_th.in_(unis))
            c_query = c_query.filter(CourseDB.university_th.in_(unis))

    adv_counts = dict(f_query.group_by(FacultyDB.faculty_th).all())
    crs_counts = dict(c_query.group_by(CourseDB.faculty_th).all())

    all_fac_names = sorted(list(set(list(adv_counts.keys()) + list(crs_counts.keys()))))
    results = []
    for fname in all_fac_names:
        adv = adv_counts.get(fname, 0)
        crs = crs_counts.get(fname, 0)
        results.append({
            "faculty_th": fname,
            "advisor_count": adv,
            "course_count": crs,
            "total_items": adv + crs
        })

    results.sort(key=lambda x: x["total_items"], reverse=True)
    _TAXONOMY_CACHE.put(cache_key, results)
    return results


@router.get("/departments")
def get_departments(
    university: str = Query(..., description="University name in Thai"),
    faculty: str = Query(..., description="Faculty name in Thai"),
    db: Session = Depends(get_db)
):
    """
    Return distinct departments / disciplines within a specific university and faculty.
    """
    cache_key = f"departments:{university}:{faculty}"
    cached = _TAXONOMY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    u_clean = university.strip()
    f_clean = faculty.strip()

    adv_query = (
        db.query(FacultyDB.department_th, func.count(FacultyDB.id))
        .filter(
            or_(FacultyDB.university_th == u_clean, FacultyDB.university == u_clean),
            FacultyDB.faculty_th == f_clean,
            FacultyDB.department_th.isnot(None),
            FacultyDB.department_th != ""
        )
        .group_by(FacultyDB.department_th)
        .all()
    )

    crs_query = (
        db.query(CourseDB.department_th, func.count(CourseDB.id))
        .filter(
            or_(CourseDB.university_th == u_clean, CourseDB.university == u_clean),
            CourseDB.faculty_th == f_clean,
            CourseDB.department_th.isnot(None),
            CourseDB.department_th != ""
        )
        .group_by(CourseDB.department_th)
        .all()
    )

    adv_counts = dict(adv_query)
    crs_counts = dict(crs_query)

    all_dept_names = sorted(list(set(list(adv_counts.keys()) + list(crs_counts.keys()))))
    results = []
    for dname in all_dept_names:
        adv = adv_counts.get(dname, 0)
        crs = crs_counts.get(dname, 0)
        results.append({
            "department_th": dname,
            "advisor_count": adv,
            "course_count": crs,
            "total_items": adv + crs
        })

    results.sort(key=lambda x: x["total_items"], reverse=True)
    _TAXONOMY_CACHE.put(cache_key, results)
    return results
