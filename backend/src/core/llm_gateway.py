"""
Resilient LLM Gateway Module
High-level stadium arena referee coordinating prompt templates,
telemetry callback tracking, and Game Guide dynamic greetings using llm_provider.
"""

import logging
import time
from typing import Any
import httpx
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult

from src.core import config
from src.core.llm_provider import (
    create_resilient_ai_brain,
    extract_clean_text_response,
)
from src.prompts.guide_prompts import build_game_guide_greeting_prompt
from src.schemas.ai_gateway_schema import (
    GatewayHealthResponse,
    GameGuideGreetingRequest,
    LLMMessageItem,
    LLMMessageRole,
    LLMResponseEnvelope,
    ProviderHealthStatus,
)

referee_logger = logging.getLogger("pokeai.llm_gateway")
referee_logger.setLevel(logging.INFO)


class ResilientGatewayCallbackHandler(AsyncCallbackHandler):
    """Monitors LangChain model invocations and records telemetry metadata."""

    def __init__(self) -> None:
        super().__init__()
        self.active_provider_name: str = "offline_fallback"
        self.model_identifier: str = "unknown"
        self.fallback_triggered: bool = False
        self.attempt_count: int = 0

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        self.attempt_count += 1
        model_name = kwargs.get("invocation_params", {}).get("model_name") or kwargs.get(
            "invocation_params", {}
        ).get("model", "")
        class_name = serialized.get("name", "") if serialized else ""

        if "Ollama" in class_name or "ollama" in str(model_name).lower():
            self.active_provider_name = "ollama"
            self.model_identifier = model_name or config.OLLAMA_MODEL
        elif "Groq" in class_name or "qwen" in str(model_name).lower():
            self.active_provider_name = "groq"
            self.model_identifier = model_name or config.GROQ_MODEL
        elif "Gemini" in class_name or "gemini" in str(model_name).lower():
            self.active_provider_name = "gemini"
            self.model_identifier = model_name or config.GEMINI_MODEL

        if self.attempt_count > 1:
            self.fallback_triggered = True

    async def on_llm_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        self.fallback_triggered = True
        referee_logger.warning("Channel #%d failed: %s", self.attempt_count, str(error))


class ResilientLLMGateway:
    """High-level gateway orchestrating battle prompts and returning typed envelopes."""

    def _convert_schema_messages(
        self,
        messages: list[LLMMessageItem],
    ) -> list[BaseMessage]:
        return [
            SystemMessage(content=msg.content)
            if msg.role == LLMMessageRole.SYSTEM
            else HumanMessage(content=msg.content)
            for msg in messages
        ]

    async def generate_chat_completion(
        self,
        conversation_messages: list[LLMMessageItem],
        sampling_temperature: float = config.TEMPERATURE,
        maximum_output_tokens: int = config.MAX_OUTPUT_TOKENS,
    ) -> LLMResponseEnvelope:
        start_timestamp = time.perf_counter()
        callback_handler = ResilientGatewayCallbackHandler()

        try:
            ai_brain = create_resilient_ai_brain(
                temperature=sampling_temperature,
                max_output_tokens=maximum_output_tokens,
            )
            langchain_messages = self._convert_schema_messages(conversation_messages)

            completion_result = await ai_brain.ainvoke(
                langchain_messages,
                config={"callbacks": [callback_handler]},
            )
            elapsed_ms = (time.perf_counter() - start_timestamp) * 1000.0
            generated_text = extract_clean_text_response(completion_result).strip()

            return LLMResponseEnvelope(
                active_provider_name=callback_handler.active_provider_name,
                model_identifier=callback_handler.model_identifier,
                execution_latency_milliseconds=round(elapsed_ms, 2),
                fallback_triggered=callback_handler.fallback_triggered,
                generated_message_content=generated_text,
            )
        except Exception as error:
            referee_logger.error("Gateway completion failed: %s", str(error))
            elapsed_ms = (time.perf_counter() - start_timestamp) * 1000.0
            return LLMResponseEnvelope(
                active_provider_name="offline_fallback",
                model_identifier="offline-rules-engine",
                execution_latency_milliseconds=round(elapsed_ms, 2),
                fallback_triggered=True,
                generated_message_content=(
                    f"Welcome to the PokeAI Stadium! I'm {config.GAME_GUIDE}. "
                    f"Our radio towers are currently offline, but the stadium referee stands ready!"
                ),
            )

    async def generate_game_guide_greeting(
        self,
        greeting_request: GameGuideGreetingRequest,
    ) -> LLMResponseEnvelope:
        start_timestamp = time.perf_counter()
        callback_handler = ResilientGatewayCallbackHandler()

        prompt_template = build_game_guide_greeting_prompt()
        formatted_messages = prompt_template.format_messages(
            game_guide_name=config.GAME_GUIDE,
            trainer_name=greeting_request.trainer_name,
            starter_monster_name=greeting_request.starter_monster_name,
            selected_starter_id=greeting_request.selected_starter_id,
            starter_elemental_type=greeting_request.starter_elemental_type,
        )

        try:
            ai_brain = create_resilient_ai_brain(
                temperature=config.TEMPERATURE,
                max_output_tokens=config.MAX_OUTPUT_TOKENS,
            )
            completion_result = await ai_brain.ainvoke(
                formatted_messages,
                config={"callbacks": [callback_handler]},
            )
            elapsed_ms = (time.perf_counter() - start_timestamp) * 1000.0
            generated_text = extract_clean_text_response(completion_result).strip()

            return LLMResponseEnvelope(
                active_provider_name=callback_handler.active_provider_name,
                model_identifier=callback_handler.model_identifier,
                execution_latency_milliseconds=round(elapsed_ms, 2),
                fallback_triggered=callback_handler.fallback_triggered,
                generated_message_content=generated_text,
            )
        except Exception as error:
            referee_logger.error("Game Guide greeting failed: %s", str(error))
            elapsed_ms = (time.perf_counter() - start_timestamp) * 1000.0
            return LLMResponseEnvelope(
                active_provider_name="offline_fallback",
                model_identifier="offline-rules-engine",
                execution_latency_milliseconds=round(elapsed_ms, 2),
                fallback_triggered=True,
                generated_message_content=(
                    f"Welcome to the PokeAI Academy, {greeting_request.trainer_name}! "
                    f"I'm {config.GAME_GUIDE}, your tournament guide! You and {greeting_request.starter_monster_name} "
                    f"make a formidable team. Our training begins right now!"
                ),
            )

    async def check_gateway_health(self) -> GatewayHealthResponse:
        channel_reports = []

        # 1. Ollama probe
        ollama_available = False
        ollama_msg = "Unreachable"
        try:
            async with httpx.AsyncClient(timeout=1.0) as probe_client:
                res = await probe_client.get(f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
                if res.status_code == 200:
                    ollama_available = True
                    ollama_msg = "Operational"
        except Exception as err:
            ollama_msg = f"Offline ({type(err).__name__})"

        channel_reports.append(
            ProviderHealthStatus(
                provider_name="ollama",
                is_available=ollama_available,
                configured_model=config.OLLAMA_MODEL,
                status_message=ollama_msg,
            )
        )

        # 2. Groq probe
        groq_configured = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
        channel_reports.append(
            ProviderHealthStatus(
                provider_name="groq",
                is_available=groq_configured,
                configured_model=config.GROQ_MODEL,
                status_message="Configured with API Key" if groq_configured else "Missing GROQ_API_KEY in .env",
            )
        )

        # 3. Gemini probe
        gemini_configured = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY.strip())
        channel_reports.append(
            ProviderHealthStatus(
                provider_name="gemini",
                is_available=gemini_configured,
                configured_model=config.GEMINI_MODEL,
                status_message="Configured with API Key" if gemini_configured else "Missing GEMINI_API_KEY in .env",
            )
        )

        recommended = "ollama" if ollama_available else ("groq" if groq_configured else ("gemini" if gemini_configured else "offline_fallback"))
        return GatewayHealthResponse(
            channels=channel_reports,
            recommended_active_channel=recommended,
        )


default_resilient_llm_gateway = ResilientLLMGateway()