# -*- coding: utf-8 -*-
"""
Test Suite for Hierarchical Taxonomy & Regional Cascading Filters.
Verifies taxonomy metadata endpoints, region mappings, and regional search filtering
across courses, faculty directories, and advisor semantic matching.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.taxonomy import REGIONS_CONFIG, UNIVERSITY_TAXONOMY, get_unis_for_region

client = TestClient(app)


def test_taxonomy_core_mappings():
    """Verify taxonomy mappings and helper functions."""
    assert len(REGIONS_CONFIG) >= 6
    assert len(UNIVERSITY_TAXONOMY) >= 37

    # Check northern universities
    north_unis = get_unis_for_region("north")
    assert "มหาวิทยาลัยเชียงใหม่" in north_unis
    assert "มหาวิทยาลัยนเรศวร" in north_unis

    # Check southern universities
    south_unis = get_unis_for_region("south")
    assert "มหาวิทยาลัยสงขลานครินทร์" in south_unis

    # Check empty or "all"
    assert get_unis_for_region("all") == []
    assert get_unis_for_region(None) == []


def test_taxonomy_regions_endpoint():
    """Verify GET /api/v1/taxonomy/regions returns all configured regions with counts."""
    response = client.get("/api/v1/taxonomy/regions")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) == len(REGIONS_CONFIG)

    region_ids = [r["id"] for r in regions]
    assert "all" in region_ids
    assert "central" in region_ids
    assert "north" in region_ids
    assert "northeast" in region_ids
    assert "south" in region_ids
    assert "east" in region_ids

    # Check structure
    for r in regions:
        assert "label_th" in r
        assert "icon" in r
        assert "university_count" in r
        assert "advisor_count" in r
        assert "course_count" in r
        assert "lab_count" in r
        assert r["university_count"] >= 0
        assert r["lab_count"] >= 0


def test_taxonomy_universities_endpoint():
    """Verify GET /api/v1/taxonomy/universities with and without region filter."""
    # All universities
    all_res = client.get("/api/v1/taxonomy/universities")
    assert all_res.status_code == 200
    all_unis = all_res.json()
    assert len(all_unis) == len(UNIVERSITY_TAXONOMY)

    # Filter by north
    north_res = client.get("/api/v1/taxonomy/universities?region=north")
    assert north_res.status_code == 200
    north_unis = north_res.json()
    assert len(north_unis) == 6
    north_names = [u["name_th"] for u in north_unis]
    assert "มหาวิทยาลัยเชียงใหม่" in north_names

    # Check university object structure
    u0 = north_unis[0]
    assert "name_th" in u0
    assert "abbr" in u0
    assert "region" in u0
    assert "advisor_count" in u0
    assert "course_count" in u0
    assert "lab_count" in u0


def test_taxonomy_faculties_and_departments_cascade():
    """Verify cascading queries from university to faculties and departments."""
    # 1. Get faculties in CMU
    fac_res = client.get("/api/v1/taxonomy/faculties?university=มหาวิทยาลัยเชียงใหม่")
    assert fac_res.status_code == 200
    facs = fac_res.json()
    assert len(facs) > 0
    fac_names = [f["faculty_th"] for f in facs]
    assert "คณะวิศวกรรมศาสตร์" in fac_names

    # 2. Get departments in CMU Engineering
    dept_res = client.get(
        "/api/v1/taxonomy/departments?university=มหาวิทยาลัยเชียงใหม่&faculty=คณะวิศวกรรมศาสตร์"
    )
    assert dept_res.status_code == 200
    depts = dept_res.json()
    assert len(depts) > 0
    dept_names = [d["department_th"] for d in depts]
    assert any("วิศวกรรม" in d for d in dept_names)


def test_regional_faculty_filtering():
    """Verify GET /api/v1/faculty/?region=north filters by regional universities."""
    response = client.get("/api/v1/faculty/?region=north&limit=10")
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) > 0

    north_unis = set(get_unis_for_region("north"))
    for card in cards:
        assert card["university_th"] in north_unis


def test_regional_courses_filtering():
    """Verify GET /api/v1/courses/?region=south filters by southern universities."""
    response = client.get("/api/v1/courses/?region=south&limit=10")
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) > 0

    south_unis = set(get_unis_for_region("south"))
    for card in cards:
        assert card["university_th"] in south_unis


def test_regional_course_search():
    """Verify POST /api/v1/courses/search respects region parameter."""
    payload = {
        "query": "วิศวกรรม",
        "region": "north",
        "top_k": 5
    }
    response = client.post("/api/v1/courses/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    north_unis = set(get_unis_for_region("north"))
    for course in data["results"]:
        assert course["university_th"] in north_unis


def test_regional_labs_filtering():
    """Verify GET /api/v1/labs/?region=east and region=north filters by regional universities."""
    # Eastern region (e.g. Burapha University)
    response_east = client.get("/api/v1/labs/?region=east&limit=10")
    assert response_east.status_code == 200
    labs_east = response_east.json()
    assert len(labs_east) > 0
    east_unis = set(get_unis_for_region("east"))
    for lab in labs_east:
        assert lab["university_th"] in east_unis

    # Northern region
    response_north = client.get("/api/v1/labs/?region=north&limit=10")
    assert response_north.status_code == 200
    labs_north = response_north.json()
    assert len(labs_north) > 0
    north_unis = set(get_unis_for_region("north"))
    for lab in labs_north:
        assert lab["university_th"] in north_unis


def test_regional_lab_search():
    """Verify POST /api/v1/labs/search respects region parameter."""
    payload = {
        "query": "ปัญญาประดิษฐ์",
        "region": "central",
        "top_k": 5
    }
    response = client.post("/api/v1/labs/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    central_unis = set(get_unis_for_region("central"))
    for lab in data["results"]:
        assert lab["university_th"] in central_unis

