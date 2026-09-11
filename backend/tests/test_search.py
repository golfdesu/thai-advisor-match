import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "online"

def test_faculty_endpoints():
    # 1. List faculty
    res = client.get("/api/v1/faculty/?limit=10")
    assert res.status_code == 200
    faculties = res.json()
    assert isinstance(faculties, list)
    assert len(faculties) > 0
    first_id = faculties[0]["id"]

    # 2. Get specific faculty profile
    res_detail = client.get(f"/api/v1/faculty/{first_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == first_id
    assert "university" in detail

def test_course_endpoints():
    # 1. List courses with degree filter
    res = client.get("/api/v1/courses/?degree_level=bachelor&limit=5")
    assert res.status_code == 200
    courses = res.json()
    assert isinstance(courses, list)
    assert len(courses) > 0
    assert courses[0]["degree_level"] == "ปริญญาตรี"

    # 2. Search courses
    search_payload = {
        "query": "วิทยาการข้อมูล Data Science",
        "degree_level": "master",
        "top_k": 5
    }
    res_search = client.post("/api/v1/courses/search", json=search_payload)
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert "results" in search_data
    assert search_data["total_matched"] > 0

def test_advisor_semantic_and_fallback_search():
    search_payload = {
        "query": "พลังงานหมุนเวียนและไมโครกริด Renewable Energy",
        "top_k": 3
    }
    res = client.post("/api/v1/search/", json=search_payload)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert data["total_matched"] > 0
    top_result = data["results"][0]
    assert "faculty" in top_result
    assert "match_score" in top_result
    assert top_result["match_score"] >= 40.0

def test_course_search_with_university_filter():
    """Verify that Course search preserves university/degree filters during vector and keyword search."""
    payload = {
        "query": "วิศวกรรม",
        "university": "จุฬาลงกรณ์มหาวิทยาลัย",
        "top_k": 5
    }
    res = client.post("/api/v1/courses/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    for course in data.get("results", []):
        assert "จุฬา" in course["university_th"] or "Chula" in course["university"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
