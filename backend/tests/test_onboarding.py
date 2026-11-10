"""
Trainer Onboarding Test Suite
Verifies starter catalog retrieval, registration validation, and profile creation.
"""

from fastapi.testclient import TestClient
from src.main import app

# Initialize test client connected to the FastAPI factory app
stadium_test_client = TestClient(app)


def test_get_available_starters_returns_three_monsters() -> None:
    """
    Verifies that the GET /api/v1/onboarding/starters endpoint delivers exactly 3 valid starters.
    """
    response = stadium_test_client.get("/api/v1/onboarding/starters")
    assert response.status_code == 200

    starters_payload = response.json()
    assert len(starters_payload) == 3

    # Verify that Bulbasaur, Charmander, and Squirtle are present
    starter_names = [starter["monster_name"] for starter in starters_payload]
    assert "Bulbasaur" in starter_names
    assert "Charmander" in starter_names
    assert "Squirtle" in starter_names


def test_register_trainer_profile_success() -> None:
    """
    Verifies successful registration of a new trainer profile with Charmander.
    """
    registration_payload = {
        "trainer_name": "Ash_Ketchum",
        "selected_starter_id": 4,
    }

    response = stadium_test_client.post(
        "/api/v1/onboarding/register",
        json=registration_payload,
    )
    assert response.status_code == 201

    profile_payload = response.json()
    assert profile_payload["trainer_name"] == "Ash_Ketchum"
    assert profile_payload["selected_starter_monster"]["monster_name"] == "Charmander"
    assert profile_payload["victories_count"] == 0
    assert profile_payload["stat_progression_multiplier"] == 1.0
    assert "trainer_registration_id" in profile_payload


def test_register_trainer_fails_on_invalid_starter_id() -> None:
    """
    Verifies that selecting an unapproved starter (e.g., ID 999) is rejected with HTTP 400.
    """
    invalid_payload = {
        "trainer_name": "Gary_Oak",
        "selected_starter_id": 999,
    }

    response = stadium_test_client.post(
        "/api/v1/onboarding/register",
        json=invalid_payload,
    )
    assert response.status_code == 400


def test_register_trainer_fails_on_short_name() -> None:
    """
    Verifies that a name with less than 2 characters is rejected with HTTP 422 by Pydantic validation.
    """
    invalid_name_payload = {
        "trainer_name": "A",
        "selected_starter_id": 1,
    }

    response = stadium_test_client.post(
        "/api/v1/onboarding/register",
        json=invalid_name_payload,
    )
    assert response.status_code == 422