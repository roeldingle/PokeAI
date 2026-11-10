"""
Configuration and Metadata Test Suite
Verifies that environment variables, centralized settings, and the metadata API endpoint function correctly.
"""

from fastapi.testclient import TestClient
from src.core import config
from src.main import app

# Initialize the test client connected directly to our FastAPI application factory
stadium_test_client = TestClient(app)


def test_configuration_values_loaded() -> None:
    """
    Validates that core configuration parameters are successfully read from the environment or default fallbacks.
    Ensures that the application never boots in a state of missing vital stadium metadata.
    """
    # Verify that the environment classification is non-empty and set as expected
    assert config.application_environment == "local"

    # Verify that the semantic version follows standard numbering
    assert config.game_version == "0.1.0"

    # Verify that the title matches our canonical project title
    assert config.game_title == "PokeAI"

    # Verify that our Game Guide name is properly loaded and non-empty
    assert config.game_guide_name in ["Shaneil", "Athena"]

    # Verify that CORS origins list contains the expected frontend development server URL
    assert "http://localhost:5173" in config.backend_cors_origins


def test_get_metadata_endpoint_success() -> None:
    """
    Tests the GET /api/v1/metadata endpoint to ensure accurate payload serialization against our Pydantic schema.
    """
    # Send a GET request to the metadata endpoint
    response = stadium_test_client.get("/api/v1/metadata")

    # Assert that the referee responds with a 200 OK status code
    assert response.status_code == 200

    # Parse response JSON payload
    response_payload = response.json()

    # Validate that each expected key is present and strictly matches the configuration state
    assert response_payload["application_environment"] == "local"
    assert response_payload["game_version"] == "0.1.0"
    assert response_payload["game_title"] == "PokeAI"
    assert response_payload["game_guide_name"] == config.game_guide_name
    assert "monster battler" in response_payload["game_description"]
    assert "AI Engineering" in response_payload["project_learning_goal"]


def test_root_status_endpoint() -> None:
    """
    Tests the root GET / endpoint to verify application health and welcome message.
    """
    # Send a GET request to the stadium root
    response = stadium_test_client.get("/")

    # Check for HTTP 200 OK
    assert response.status_code == 200

    # Verify that the status flag indicates 'online'
    response_payload = response.json()
    assert response_payload["status"] == "online"
    assert "Welcome to the PokeAI Stadium" in response_payload["message"]
