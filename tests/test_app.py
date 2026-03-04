from copy import deepcopy
import copy
from urllib.parse import quote
import pytest
from fastapi.testclient import TestClient
from src import app as app_module
from src.app import app


@pytest.fixture(autouse=True)
def client_and_reset():
    # Arrange: snapshot activities and provide TestClient
    original = copy.deepcopy(app_module.activities)
    client = TestClient(app)
    try:
        yield client
    finally:
        # Teardown: restore activities to original state
        app_module.activities = copy.deepcopy(original)


def test_root_redirect(client_and_reset):
    # Arrange
    client = client_and_reset

    # Act
    resp = client.get("/")

    # Assert
    # TestClient may follow redirects, so accept 200 (final) or redirect codes.
    assert resp.status_code in (200, 307, 308)
    if resp.status_code == 200:
        # If redirects were followed, ensure final URL is the index page
        assert str(resp.url).endswith("/static/index.html")
    else:
        assert resp.headers.get("location", "").endswith("/static/index.html")


def test_get_activities(client_and_reset):
    # Arrange
    client = client_and_reset

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_success_and_duplicate(client_and_reset):
    # Arrange
    client = client_and_reset
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    quoted = quote(activity, safe="")

    # Act: successful signup
    resp = client.post(f"/activities/{quoted}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # Act: duplicate signup
    resp2 = client.post(f"/activities/{quoted}/signup", params={"email": email})

    # Assert duplicate rejected
    assert resp2.status_code == 400


def test_signup_nonexistent_activity(client_and_reset):
    # Arrange
    client = client_and_reset
    activity = "NoSuchActivity"
    quoted = quote(activity, safe="")

    # Act
    resp = client.post(f"/activities/{quoted}/signup", params={"email": "x@x.com"})

    # Assert
    assert resp.status_code == 404


def test_unregister_success_and_errors(client_and_reset):
    # Arrange
    client = client_and_reset
    activity = "Programming Class"
    email = "toremove@mergington.edu"
    quoted = quote(activity, safe="")

    # Ensure participant is present
    resp = client.post(f"/activities/{quoted}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # Act: unregister
    resp2 = client.delete(f"/activities/{quoted}/signup/{quote(email, safe='')}" )

    # Assert
    assert resp2.status_code == 200
    assert email not in app_module.activities[activity]["participants"]

    # Act: unregister non-existent email
    resp3 = client.delete(f"/activities/{quoted}/signup/{quote('noone@x.com', safe='')}" )
    assert resp3.status_code == 404

    # Act: unregister from non-existent activity
    resp4 = client.delete(f"/activities/{quote('NotAnActivity', safe='')}/signup/{quote(email, safe='')}")
    assert resp4.status_code == 404
