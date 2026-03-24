import copy

import pytest
from fastapi.testclient import TestClient

import src.app

# Snapshot of the pristine activities state taken at import time,
# before any test mutates the in-memory database.
INITIAL_ACTIVITIES = copy.deepcopy(src.app.activities)

client = TestClient(src.app.app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its initial state before each test."""
    src.app.activities.clear()
    src.app.activities.update(copy.deepcopy(INITIAL_ACTIVITIES))


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects():
    # Arrange – no setup required; client is module-level

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    # Arrange
    expected_activities = list(INITIAL_ACTIVITIES.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert sorted(data.keys()) == sorted(expected_activities)


def test_activity_has_required_fields():
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    for activity in data.values():
        assert required_fields.issubset(activity.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    # Arrange
    activity_name = "Chess Club"
    new_email = "new_student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in src.app.activities[activity_name]["participants"]


def test_signup_activity_not_found():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_signup_already_registered():
    # Arrange
    activity_name = "Chess Club"
    existing_email = INITIAL_ACTIVITIES[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/participants
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Arrange
    activity_name = "Chess Club"
    existing_email = INITIAL_ACTIVITIES[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {existing_email} from {activity_name}"}
    assert existing_email not in src.app.activities[activity_name]["participants"]


def test_unregister_activity_not_found():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_unregister_participant_not_found():
    # Arrange
    activity_name = "Chess Club"
    nonexistent_email = "ghost@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": nonexistent_email},
    )

    # Assert
    assert response.status_code == 404
