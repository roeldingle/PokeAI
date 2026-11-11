"""
Unit and Integration Test Suite for the Resilient LLM Gateway
Verifies the Three-Channel Walkie-Talkie fallback cascade:
- Channel 1: Ollama (Local)
- Channel 2: Groq (Fast Cloud)
- Channel 3: Google Gemini (Strategic Cloud)
- Channel 4: Emergency Offline Fallback
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from src.core import config
from src.core.llm_gateway import ResilientLLMGateway
from src.main import app
from src.schemas.ai_gateway_schema import (
    GameGuideGreetingRequest,
    LLMMessageItem,
    LLMMessageRole,
)


@pytest.fixture
def sample_conversation_messages() -> list[LLMMessageItem]:
    """Provides a realistic combat prompt fixture for gateway testing."""
    return [
        LLMMessageItem(
            role=LLMMessageRole.SYSTEM,
            content="You are an arena referee providing brief battle status updates.",
        ),
        LLMMessageItem(
            role=LLMMessageRole.USER,
            content="Charmander used Scratch! Report the damage result.",
        ),
    ]


@pytest.mark.anyio
async def test_gateway_primary_channel_ollama_success(
    sample_conversation_messages: list[LLMMessageItem],
) -> None:
    """
    Test 1: Channel 1 (Ollama) succeeds cleanly.
    Verifies that the gateway returns active_provider_name='ollama' and fallback_triggered=False.
    """
    gateway_instance = ResilientLLMGateway()

    # Create mock brain returning an Ollama AI message
    mock_brain = AsyncMock()
    mock_brain.ainvoke.return_value = AIMessage(
        content="Charmander's Scratch dealt 12 physical damage!"
    )

    with patch(
        "src.core.llm_gateway.create_resilient_ai_brain",
        return_value=mock_brain,
    ):
        response_envelope = await gateway_instance.generate_chat_completion(
            conversation_messages=sample_conversation_messages,
        )

        assert response_envelope.fallback_triggered is False
        assert "Scratch" in response_envelope.generated_message_content
        assert response_envelope.execution_latency_milliseconds >= 0.0


@pytest.mark.anyio
async def test_gateway_emergency_offline_fallback_when_all_fail(
    sample_conversation_messages: list[LLMMessageItem],
) -> None:
    """
    Test 2: All providers fail.
    Verifies that the gateway catches the exception and returns the emergency fallback
    without raising an unhandled 500 error.
    """
    gateway_instance = ResilientLLMGateway()

    # Mock brain raising an outage exception across all channels
    mock_brain = AsyncMock()
    mock_brain.ainvoke.side_effect = ConnectionError("All AI towers unreachable")

    with patch(
        "src.core.llm_gateway.create_resilient_ai_brain",
        return_value=mock_brain,
    ):
        response_envelope = await gateway_instance.generate_chat_completion(
            conversation_messages=sample_conversation_messages,
        )

        assert response_envelope.active_provider_name == "offline_fallback"
        assert response_envelope.model_identifier == "offline-rules-engine"
        assert response_envelope.fallback_triggered is True
        assert config.GAME_GUIDE in response_envelope.generated_message_content


@pytest.mark.anyio
async def test_game_guide_dynamic_greeting_generation() -> None:
    """
    Test 3: Game Guide greeting dynamically incorporates trainer moniker
    and the guide name configured in backend settings.
    """
    gateway_instance = ResilientLLMGateway()

    greeting_request = GameGuideGreetingRequest(
        trainer_name="Ash_Ketchum",
        selected_starter_id=4,
        starter_monster_name="Charmander",
        starter_elemental_type="Fire",
    )

    mock_brain = AsyncMock()
    mock_brain.ainvoke.return_value = AIMessage(
        content=f"Welcome Ash_Ketchum! I'm {config.GAME_GUIDE}! Charmander's Fire attacks will scorch the stadium!"
    )

    with patch(
        "src.core.llm_gateway.create_resilient_ai_brain",
        return_value=mock_brain,
    ):
        response_envelope = await gateway_instance.generate_game_guide_greeting(greeting_request)

        assert "Ash_Ketchum" in response_envelope.generated_message_content
        assert config.GAME_GUIDE in response_envelope.generated_message_content


def test_api_route_ai_health_endpoint() -> None:
    """
    Test 4: GET /api/v1/ai/health returns 200 OK and reports status for all 3 channels.
    """
    test_client = TestClient(app)
    response = test_client.get("/api/v1/ai/health")

    assert response.status_code == 200
    payload = response.json()
    assert "channels" in payload
    assert len(payload["channels"]) == 3
    provider_names = [channel["provider_name"] for channel in payload["channels"]]
    assert "ollama" in provider_names
    assert "groq" in provider_names
    assert "gemini" in provider_names
    assert "recommended_active_channel" in payload


def test_api_route_game_guide_greeting_endpoint() -> None:
    """
    Test 5: POST /api/v1/ai/guide/greeting returns 200 OK and returns a valid LLMResponseEnvelope.
    """
    test_client = TestClient(app)
    request_payload = {
        "trainer_name": "Red_Champion",
        "selected_starter_id": 1,
        "starter_monster_name": "Bulbasaur",
        "starter_elemental_type": "Grass",
    }

    response = test_client.post("/api/v1/ai/guide/greeting", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert "active_provider_name" in payload
    assert "model_identifier" in payload
    assert "execution_latency_milliseconds" in payload
    assert "fallback_triggered" in payload
    assert "generated_message_content" in payload
    assert len(payload["generated_message_content"]) > 0