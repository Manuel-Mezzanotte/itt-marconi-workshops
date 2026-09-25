"""Shared pytest fixtures for user-service tests."""
import pytest
from app import create_app


@pytest.fixture()
def app():
    """Create a test Flask application with in-memory backend."""
    application = create_app({"STORAGE_BACKEND": "memory", "PORT": 5001})
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    """Flask test client bound to the test application."""
    return app.test_client()
