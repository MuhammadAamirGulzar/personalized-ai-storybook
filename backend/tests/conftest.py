# Pytest configuration and shared fixtures for MyAIStorybook testing

import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
import subprocess

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.auth.database import Base, get_db
from backend.auth.models import User
from backend.auth.security import get_password_hash
from backend.main import app




# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for testing
    Each test gets a fresh database
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Provide a database session for tests
    """
    session = test_db()
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# FASTAPI TEST CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden database dependency
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user in the database
    """
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """
    Get authentication headers with valid JWT token
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# MOCK FIXTURES FOR EXTERNAL SERVICES
# ============================================================================

@pytest.fixture(scope="function")
def mock_ollama():
    """
    Mock Ollama subprocess calls to avoid external dependencies
    """
    with patch('subprocess.run') as mock_run:
        # Default mock response for Ollama
        mock_result = Mock()
        mock_result.stdout = b'{"type": "normal", "enhanced": "A wonderful story about friendship"}'
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture(scope="function")
def mock_webui_api():
    """
    Mock WebUI API calls for image generation
    """
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": ["base64_encoded_image_data"]
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture(scope="function")
def mock_ollama_manager():
    """
    Mock OllamaManager to avoid GPU operations
    """
    with patch('backend.utils.ollama_manager.OllamaManager') as mock_manager:
        mock_manager.pause_ollama.return_value = True
        mock_manager.resume_ollama.return_value = None
        yield mock_manager


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_story_data():
    """
    Sample story data for testing
    """
    return {
        "title": "The Brave Little Mouse",
        "characters": ["brave mouse", "wise owl", "friendly rabbit"],
        "scenes": [
            {
                "scene_number": 1,
                "text": "Once upon a time, a brave little mouse lived in a cozy hole.",
                "image_description": "A small mouse in a comfortable burrow with soft bedding"
            },
            {
                "scene_number": 2,
                "text": "One day, the mouse decided to explore the big forest.",
                "image_description": "A tiny mouse standing at the edge of a vast, colorful forest"
            },
            {
                "scene_number": 3,
                "text": "The mouse made many friends and learned to be courageous.",
                "image_description": "The mouse surrounded by forest animal friends, smiling happily"
            }
        ]
    }


@pytest.fixture
def sample_user_photo():
    """
    Sample base64 encoded user photo (1x1 pixel PNG)
    """
    # Minimal valid PNG (1x1 transparent pixel)
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
