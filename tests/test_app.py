import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    # Make a deep copy of the in-memory activities and restore after test
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect some known activity to exist
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_and_prevent_duplicate(client):
    email = "test_user@example.com"
    activity = "Chess Club"
    encoded_activity = urllib.parse.quote(activity, safe="")

    # Signup should succeed first time
    resp = client.post(f"/activities/{encoded_activity}/signup?email={urllib.parse.quote(email)}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Second signup should be rejected with 400
    resp2 = client.post(f"/activities/{encoded_activity}/signup?email={urllib.parse.quote(email)}")
    assert resp2.status_code == 400
    assert "already" in resp2.json().get("detail", "").lower()


def test_remove_participant(client):
    email = "to_remove@example.com"
    activity = "Tennis Club"
    encoded_activity = urllib.parse.quote(activity, safe="")

    # Ensure participant is present by signing up
    resp = client.post(f"/activities/{encoded_activity}/signup?email={urllib.parse.quote(email)}")
    assert resp.status_code == 200

    # Now remove the participant
    resp_del = client.delete(f"/activities/{encoded_activity}/participants?email={urllib.parse.quote(email)}")
    assert resp_del.status_code == 200
    assert "Removed" in resp_del.json().get("message", "")

    # Confirm participant no longer present
    resp_get = client.get("/activities")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert email not in data[activity]["participants"]
