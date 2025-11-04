import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import os

# Set mock mode for testing
os.environ["USE_MOCK"] = "1"

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_ingest_no_files():
    """Test ingest with no files."""
    response = client.post("/ingest", files=[])
    assert response.status_code == 400


def test_generate_outline():
    """Test outline generation."""
    response = client.post(
        "/generate_outline",
        json={
            "premise": "A shy barista can pause time for 10 seconds",
            "genre": "urban fantasy",
            "length": "short"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "outline" in data
    assert "logline" in data["outline"]
    assert "beats" in data["outline"]
    assert "consistency" in data


def test_generate_outline_validation():
    """Test outline generation with invalid input."""
    # Too short premise
    response = client.post(
        "/generate_outline",
        json={"premise": "short", "genre": "sci-fi", "length": "short"}
    )
    assert response.status_code == 422  # Validation error


def test_expand_scene():
    """Test scene expansion."""
    outline = {
        "logline": "Test story",
        "beats": [
            {"title": "Hook", "goal": "Test", "conflict": "Test", "outcome": "Test"}
        ]
    }
    response = client.post(
        "/expand_scene",
        json={
            "outline": outline,
            "scene_index": 0,
            "protagonist": "Test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "scene_text" in data
    assert "continuity" in data


def test_expand_scene_invalid_index():
    """Test scene expansion with invalid index."""
    outline = {
        "logline": "Test",
        "beats": [{"title": "Hook", "goal": "", "conflict": "", "outcome": ""}]
    }
    response = client.post(
        "/expand_scene",
        json={
            "outline": outline,
            "scene_index": 999,  # Out of bounds
            "protagonist": "Test"
        }
    )
    # Should still work (clamped)
    assert response.status_code == 200


def test_export_story():
    """Test story export."""
    outline = {
        "logline": "Test story",
        "beats": [
            {"title": "Hook", "goal": "Goal", "conflict": "Conflict", "outcome": "Outcome"}
        ]
    }
    scenes = ["Scene 1 text"]
    
    response = client.post(
        "/export",
        json={
            "outline": outline,
            "scenes": scenes,
            "save_to_db": False
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "Test story" in response.text


def test_ask_no_index():
    """Test ask endpoint without index."""
    response = client.get("/ask?q=test")
    # Should return 400 if no index
    assert response.status_code in [400, 500]


def test_list_stories():
    """Test listing stories."""
    response = client.get("/stories")
    assert response.status_code == 200
    data = response.json()
    assert "stories" in data
    assert "count" in data

