"""REQ-REG-B01..B09, REQ-REG-04, REQ-REG-05: real processes, no HTTP mocks."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest


pytestmark = [pytest.mark.req("REQ-REG-05"), pytest.mark.registration]
BASE = "/api/v1/registrations"


def user_record(http, service, role="attendee"):
    response = http(service, "POST", "/api/v1/users", json={
        "first_name": "Test", "last_name": "User", "email": f"{uuid4()}@example.com", "role": role,
    })
    assert response.status_code == 201
    return response.json()


def event_record(http, user, event, capacity=2, status="published"):
    owner = user_record(http, user, "organizer")
    response = http(event, "POST", "/api/v1/events", json={
        "title": "Registration integration", "organizer_id": owner["id"],
        "venue": "Auditorium", "city": "Trento", "start_date": "2026-11-10",
        "end_date": "2026-11-11", "capacity": capacity, "price": 149.0,
    })
    assert response.status_code == 201
    if status != "draft":
        response = http(event, "PATCH", response.headers["Location"], json={"status": status})
        assert response.status_code == 200
    return response.json()


def register(http, service, user_id, event_id):
    return http(service, "POST", BASE, json={"user_id": user_id, "event_id": event_id})


def test_full_capacity_journey_and_historical_price(registration_platform, http):
    user, event, registration = registration_platform
    conference = event_record(http, user, event)
    attendees = [user_record(http, user) for _ in range(3)]
    first = register(http, registration, attendees[0]["id"], conference["id"])
    second = register(http, registration, attendees[1]["id"], conference["id"])
    assert first.status_code == second.status_code == 201
    full = register(http, registration, attendees[2]["id"], conference["id"])
    assert full.status_code == 409 and full.json()["error"]["code"] == "EVENT_FULL"
    duplicate = register(http, registration, attendees[0]["id"], conference["id"])
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "ALREADY_REGISTERED"
    first_path = first.headers["Location"]
    assert http(registration, "PUT", first_path).status_code == 405
    assert http(registration, "PATCH", first_path, json={"status": "cancelled"}).status_code == 200
    third = register(http, registration, attendees[2]["id"], conference["id"])
    assert third.status_code == 201
    stats = http(registration, "GET", BASE + "/stats", params={"event_id": conference["id"]}).json()
    assert stats == {"event_id": conference["id"], "capacity": 2, "confirmed": 2, "available": 0}
    changed = http(event, "PATCH", f"/api/v1/events/{conference['id']}", json={"price": 199.99})
    assert changed.status_code == 200
    assert http(registration, "GET", first_path).json()["amount"] == 149.0
    assert http(registration, "PATCH", second.headers["Location"], json={"status": "cancelled"}).status_code == 200
    again = register(http, registration, attendees[0]["id"], conference["id"])
    assert again.status_code == 201 and again.json()["amount"] == 199.99
    assert again.json()["id"] != first.json()["id"]
    assert http(registration, "DELETE", again.headers["Location"]).status_code == 204
    stats = http(registration, "GET", BASE + "/stats", params={"event_id": conference["id"]}).json()
    assert stats["confirmed"] == 1 and stats["available"] == 1
    assert http(registration, "GET", BASE, params={"status": "confirmed"}).json()["items"] == [third.json()]


def test_reference_errors_and_closed_event(registration_platform, http):
    user, event, registration = registration_platform
    attendee = user_record(http, user)
    conference = event_record(http, user, event, status="draft")
    for user_id, event_id in [(str(uuid4()), conference["id"]), (attendee["id"], str(uuid4()))]:
        failed = register(http, registration, user_id, event_id)
        assert failed.status_code == 422 and failed.json()["error"]["code"] == "REFERENCE_NOT_FOUND"
    for status in ("draft", "cancelled"):
        if status == "cancelled":
            assert http(event, "PATCH", f"/api/v1/events/{conference['id']}", json={"status": status}).status_code == 200
        closed = register(http, registration, attendee["id"], conference["id"])
        assert closed.status_code == 422 and closed.json()["error"]["code"] == "EVENT_NOT_OPEN"
    missing = http(registration, "GET", BASE + "/stats", params={"event_id": str(uuid4())})
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
    assert http(registration, "GET", BASE).json()["total"] == 0


@pytest.mark.parametrize("dependency", ["user", "event"])
def test_each_dependency_stopped_separately(registration_platform, http, dependency):
    user, event, registration = registration_platform
    attendees = [user_record(http, user) for _ in range(2)]
    conference = event_record(http, user, event)
    original = register(http, registration, attendees[0]["id"], conference["id"])
    assert original.status_code == 201
    path = original.headers["Location"]
    (user if dependency == "user" else event).stop()
    failed = register(http, registration, attendees[1]["id"], conference["id"])
    assert failed.status_code == 503 and failed.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert http(registration, "GET", "/health").status_code == 200
    assert http(registration, "GET", path).json() == original.json()
    assert http(registration, "GET", BASE).json()["total"] == 1
    stats = http(registration, "GET", BASE + "/stats", params={"event_id": conference["id"]})
    assert stats.status_code == (200 if dependency == "user" else 503)
    assert http(registration, "PATCH", path, json={"status": "cancelled"}).status_code == 200
    assert http(registration, "DELETE", path).status_code == 204


@pytest.mark.parametrize("same_user", [False, True])
def test_concurrent_http_reservations_have_one_winner(registration_platform, http, same_user):
    user, event, registration = registration_platform
    conference = event_record(http, user, event, capacity=1)
    attendees = [user_record(http, user) for _ in range(1 if same_user else 8)]
    identifiers = [attendees[0]["id"]] * 8 if same_user else [item["id"] for item in attendees]
    barrier = Barrier(8)

    def attempt(user_id):
        barrier.wait(timeout=5)
        return register(http, registration, user_id, conference["id"])

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, identifiers))
    assert sum(result.status_code == 201 for result in results) == 1
    failures = [result for result in results if result.status_code != 201]
    assert all(result.status_code == 409 for result in failures)
    assert all(result.json()["error"]["code"] == (
        "ALREADY_REGISTERED" if same_user else "EVENT_FULL"
    ) for result in failures)
    stats = http(registration, "GET", BASE + "/stats", params={"event_id": conference["id"]}).json()
    assert stats["confirmed"] == 1 and stats["available"] == 0


def test_registration_restart_persistence(registration_platform, start_service, backend, http):
    user, event, registration = registration_platform
    attendee = user_record(http, user)
    conference = event_record(http, user, event, capacity=1)
    first = register(http, registration, attendee["id"], conference["id"])
    assert first.status_code == 201
    http(registration, "PATCH", first.headers["Location"], json={"status": "cancelled"})
    second = register(http, registration, attendee["id"], conference["id"])
    assert second.status_code == 201
    path = second.headers["Location"]
    registration.stop()
    restarted = start_service("registration-service", urls={
        "USER_SERVICE_URL": user.url, "EVENT_SERVICE_URL": event.url,
    }, data_dir=registration.data_dir, port=registration.port)
    recovered = http(restarted, "GET", path)
    stats = http(restarted, "GET", BASE + "/stats", params={"event_id": conference["id"]}).json()
    if backend == "memory":
        assert recovered.status_code == 404 and stats["confirmed"] == 0
    else:
        assert recovered.status_code == 200 and recovered.json() == second.json()
        assert stats["confirmed"] == 1
        assert http(restarted, "GET", BASE, params={"status": "cancelled"}).json()["total"] == 1
