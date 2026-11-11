"""
AI Routes Module
Exposes FastAPI endpoints for the Three-Channel Resilient LLM Gateway,
providing health diagnostic probes, general text completions, and Game Guide dynamic greetings.
"""

from fastapi import APIRouter, status
from src.core.llm_gateway import (
    ResilientLLMGateway,
    default_resilient_llm_gateway,
)
from src.schemas.ai_gateway_schema import (
    GatewayHealthResponse,
    GameGuideGreetingRequest,
    LLMCompletionRequest,
    LLMResponseEnvelope,
)

# Instantiate dedicated APIRouter for AI operations
ai_router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Gateway"],
)


@ai_router.get(
    "/health",
    response_model=GatewayHealthResponse,
    summary="Check Three-Channel Gateway Health",
)
async def check_ai_gateway_health() -> GatewayHealthResponse:
    """
    Probes the operational readiness of Channel 1 (Ollama), Channel 2 (Groq), and Channel 3 (Gemini).
    Returns availability status and the recommended primary frequency.
    """
    return await default_resilient_llm_gateway.check_gateway_health()


@ai_router.post(
    "/generate",
    response_model=LLMResponseEnvelope,
    summary="Generate Resilient Chat Completion",
)
async def generate_chat_completion(
    completion_request: LLMCompletionRequest,
) -> LLMResponseEnvelope:
    """
    Dispatches a prompt payload through our Resilient Three-Channel Gateway cascade.
    Tries Ollama first -> failover to Groq -> failover to Gemini -> offline emergency response.
    Returns the generated dialogue along with provider telemetry and latency in milliseconds.
    """
    return await default_resilient_llm_gateway.generate_chat_completion(
        conversation_messages=completion_request.messages,
        sampling_temperature=completion_request.temperature,
        maximum_output_tokens=completion_request.max_tokens,
    )


@ai_router.post(
    "/guide/greeting",
    response_model=LLMResponseEnvelope,
    status_code=status.HTTP_200_OK,
    summary="Awaken Game Guide Dynamic Greeting",
)
async def generate_game_guide_greeting(
    greeting_request: GameGuideGreetingRequest,
) -> LLMResponseEnvelope:
    """
    Constructs an authentic Game Guide coach persona prompt, injecting the trainer's name
    and chosen starter monster details, then passes it through the Resilient Gateway.
    """
    return await default_resilient_llm_gateway.generate_game_guide_greeting(
        greeting_request=greeting_request,
    )