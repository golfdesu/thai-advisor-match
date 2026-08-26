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

def test_cold_email_generator():
    # Fetch a faculty member
    res_fac = client.get("/api/v1/faculty/?limit=1")
    assert res_fac.status_code == 200
    faculty_id = res_fac.json()[0]["id"]

    cold_email_payload = {
        "faculty_id": faculty_id,
        "student_name": "Somchai Jaidee",
        "intended_degree": "Master of Science",
        "student_background": "B.Eng. Computer Engineering, GPA 3.75",
        "research_topic": "AI for Medical Image Analysis",
        "language": "th"
    }
    res_email = client.post("/api/v1/search/cold-email", json=cold_email_payload)
    assert res_email.status_code == 200
    email_data = res_email.json()
    assert "subject" in email_data
    assert "body" in email_data
    assert len(email_data["subject"]) > 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])

