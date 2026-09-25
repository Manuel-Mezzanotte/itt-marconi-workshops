"""Shared pytest fixtures for user-service tests."""
import pytest
from app import create_app
from validator import assert_matches_contract


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


@pytest.fixture(params=["memory", "json", "sqlite"])
def api(request, tmp_path):
    application = create_app({
        "STORAGE_BACKEND": request.param,
        "DATA_DIR": tmp_path / request.param,
        "PORT": 5001,
    })
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture()
def create_user(api):
    def create(**overrides):
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            **overrides,
        }
        response = api.post("/api/v1/users", json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()
    return create


@pytest.fixture()
def contract():
    def check(response, method, path, status=200):
        assert response.status_code == status, response.get_data(as_text=True)
        body = response.get_json() if response.data else None
        assert_matches_contract("user-service", method, path, {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "json": body,
        })
        return body
    return check
