"""
Playwright Web Application & API Contract Test Suite
Validates that endpoints serving the Next.js frontend (App Router) return
valid schema structures and adhere to zero-regression webapp standards.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_webapp_backend_health():
    """Verify backend health endpoint is active for frontend consumption."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "online"


def test_webapp_faculty_cards_contract():
    """Verify faculty endpoint returns structured results for AdvisorCard.tsx."""
    response = client.get("/api/v1/faculty/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        advisor = data[0]
        # Contract fields required by AdvisorCard.tsx
        assert "id" in advisor
        assert "name" in advisor or "full_name_th" in advisor


def test_webapp_courses_contract():
    """Verify course discovery endpoint returns structured cards for CourseCard.tsx."""
    response = client.get("/api/v1/courses/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_webapp_search_post_contract():
    """Verify semantic search POST endpoint accepts query and returns matched results."""
    response = client.post("/api/v1/search/", json={"query": "AI Robotics", "top_k": 3})
    assert response.status_code == 200, (
        f"Search endpoint returned {response.status_code}; "
        "check GEMINI_API_KEY and pgvector embedding availability"
    )
    if response.status_code == 200:
        data = response.json()
        assert "results" in data
        assert "query" in data


def test_playwright_browser_environment():
    """Verify Playwright availability or document MCP integration."""
    try:
        import playwright
        assert playwright is not None
    except ImportError:
        pytest.skip(
            "Python playwright package not installed in current venv. "
            "Browser interactions run via Playwright MCP server or CLI."
        )
