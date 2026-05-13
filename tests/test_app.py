import copy
from urllib.parse import quote

import pytest
from httpx import AsyncClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


def activity_path(activity_name: str, action: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/{action}"


@pytest.mark.asyncio
async def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activities = {
        "Basketball Team",
        "Soccer Team",
        "Chess Club",
        "Programming Class",
        "Gym Class",
    }

    # Act
    response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == expected_activities
    assert isinstance(data["Chess Club"]["participants"], list)


@pytest.mark.asyncio
async def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student1@mergington.edu"

    # Act
    response = await client.post(
        activity_path(activity_name, "signup"),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


@pytest.mark.asyncio
async def test_signup_duplicate_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = await client.post(
        activity_path(activity_name, "signup"),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


@pytest.mark.asyncio
async def test_signup_for_nonexistent_activity_returns_404(client):
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student2@mergington.edu"

    # Act
    response = await client.post(
        activity_path(activity_name, "signup"),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.asyncio
async def test_unregister_participant_removes_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = activities[activity_name]["participants"][0]
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = await client.delete(
        activity_path(activity_name, "participants"),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert len(activities[activity_name]["participants"]) == initial_count - 1
    assert email not in activities[activity_name]["participants"]


@pytest.mark.asyncio
async def test_unregister_nonexistent_participant_returns_404(client):
    # Arrange
    activity_name = "Programming Class"
    email = "notregistered@mergington.edu"

    # Act
    response = await client.delete(
        activity_path(activity_name, "participants"),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
