"""REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05, REQ-EVT-05, REQ-EVT-06."""
from uuid import uuid4

import pytest


pytestmark = [pytest.mark.req("REQ-EVT-06"), pytest.mark.event]
BASE = "/api/v1/events"


def organizer(http, user, role="organizer"):
    response = http(user, "POST", "/api/v1/users", json={
        "first_name": "Ada", "last_name": "Lovelace", "email": f"{uuid4()}@example.com",
        "role": role,
    })
    assert response.status_code == 201
    return response.json()


def payload(user_id):
    return {
        "title": "Real HTTP conference", "organizer_id": user_id, "venue": "Auditorium",
        "city": "Trento", "start_date": "2026-11-10", "end_date": "2026-11-11",
        "capacity": 10, "price": 49.0,
    }


def test_event_crud_with_real_organizer(event_platform, http):
    user, event = event_platform
    owner = organizer(http, user)
    data = payload(owner["id"])
    created = http(event, "POST", BASE, json=data)
    assert created.status_code == 201 and created.json()["status"] == "draft"
    path = created.headers["Location"]
    assert http(event, "GET", path).json() == created.json()
    replaced = http(event, "PUT", path, json={**data, "capacity": 20})
    assert replaced.status_code == 200 and replaced.json()["capacity"] == 20
    published = http(event, "PATCH", path, json={"status": "published"})
    assert published.status_code == 200
    listed = http(event, "GET", BASE, params={"status": "published", "city": "Trento"}).json()
    assert listed["items"] == [published.json()] and listed["total"] == 1
    cancelled = http(event, "PATCH", path, json={"status": "cancelled"})
    assert cancelled.status_code == 200
    assert http(event, "DELETE", path).status_code == 204
    assert http(event, "GET", path).status_code == 404


def test_missing_reference_and_wrong_role(event_platform, http):
    user, event = event_platform
    missing = http(event, "POST", BASE, json=payload(str(uuid4())))
    assert missing.status_code == 422 and missing.json()["error"]["code"] == "REFERENCE_NOT_FOUND"
    attendee = organizer(http, user, role="attendee")
    wrong_role = http(event, "POST", BASE, json=payload(attendee["id"]))
    assert wrong_role.status_code == 422 and wrong_role.json()["error"]["code"] == "INVALID_ORGANIZER"
    assert http(event, "GET", BASE).json()["total"] == 0


def test_dependency_stopped_preserves_data(event_platform, http):
    user, event = event_platform
    data = payload(organizer(http, user)["id"])
    response = http(event, "POST", BASE, json=data)
    before, path = response.json(), response.headers["Location"]
    user.stop()
    assert http(event, "GET", "/health").status_code == 200
    assert http(event, "GET", path).json() == before
    for method, target, body in [
        ("POST", BASE, data), ("PUT", path, {**data, "title": "Changed"}),
        ("PATCH", path, {"organizer_id": data["organizer_id"]}),
    ]:
        failed = http(event, method, target, json=body)
        assert failed.status_code == 503 and failed.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
        assert http(event, "GET", path).json() == before
    assert http(event, "GET", BASE).json()["total"] == 1
    assert http(event, "PATCH", path, json={"city": "Roma"}).status_code == 200
    assert http(event, "DELETE", path).status_code == 204


def test_event_restart_persistence(event_platform, start_service, backend, http):
    user, event = event_platform
    data = {**payload(organizer(http, user)["id"]), "status": "published", "price": 1.005}
    response = http(event, "POST", BASE, json=data)
    before, path = response.json(), response.headers["Location"]
    event.stop()
    restarted = start_service(
        "event-service", urls={"USER_SERVICE_URL": user.url},
        data_dir=event.data_dir, port=event.port,
    )
    recovered = http(restarted, "GET", path)
    if backend == "memory":
        assert recovered.status_code == 404
    else:
        assert recovered.status_code == 200 and recovered.json() == before
        assert recovered.json()["price"] == 1.01
