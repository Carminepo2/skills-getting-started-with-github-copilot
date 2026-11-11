import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Basketball Team"]["participants"] == []


def test_signup_adds_participant(client):
    email = "student@example.com"

    response = client.post("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Basketball Team"
    assert client.get("/activities").json()["Basketball Team"]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client):
    email = "student@example.com"
    client.post("/activities/Basketball Team/signup", params={"email": email})

    response = client.post("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Basketball Team"]["participants"] == [email]


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_removes_participant(client):
    email = "student@example.com"
    client.post("/activities/Basketball Team/signup", params={"email": email})

    response = client.delete("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Basketball Team"
    assert client.get("/activities").json()["Basketball Team"]["participants"] == []


def test_delete_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_participant_not_signed_up(client):
    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"