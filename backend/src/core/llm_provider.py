"""
LLM Provider Module
Configures resilient chat models with provider fallbacks (Ollama -> Groq -> Gemini)
and exposes clean text extraction, synchronous token streaming, and asynchronous execution.
"""

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from src.core.config import (
    APP_ENV,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_OUTPUT_TOKENS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE,
)


def extract_clean_text_response(ai_response_object: Any) -> str:
    """Extract readable text from a LangChain response, chunk, or content block list."""
    response_text = getattr(ai_response_object, "text", None)
    if response_text:
        return str(response_text)

    response_content = getattr(ai_response_object, "content", ai_response_object)
    if isinstance(response_content, str):
        return response_content

    if isinstance(response_content, list):
        text_parts = []
        for content_part in response_content:
            if isinstance(content_part, str):
                text_parts.append(content_part)
            elif isinstance(content_part, dict):
                part_text = content_part.get("text", "")
                if isinstance(part_text, str):
                    text_parts.append(part_text)
        return "".join(text_parts)

    return str(response_content)


def create_resilient_ai_brain(
    temperature: float = TEMPERATURE,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
):
    """
    Build the configured chat model with provider fallbacks.
    Tries Local Ollama first in local environments; routes straight to Groq -> Gemini in staging/prod.
    """
    # Channel 1: Local Ollama (tactical belt radio)
    local_ollama_model = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_predict=max_output_tokens,
        timeout=2.0,  # 2s bounded timeout to prevent game engine freezes if Ollama is offline
    )

    # Channel 2: Groq Cloud (ultra-fast satellite relay)
    groq_cloud_model = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_output_tokens,
        max_retries=1,
    )

    # Channel 3: Google Gemini (grandmaster reasoning hotline)
    gemini_cloud_model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        max_retries=1,
    )

    # Assemble candidate fallback list based on credentials present
    backup_models = []
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        backup_models.append(gemini_cloud_model)
    if GROQ_API_KEY and GROQ_API_KEY.strip():
        backup_models.append(groq_cloud_model)
    

    # Use local Ollama first only in local mode
    if APP_ENV == "local":
        if backup_models:
            return local_ollama_model.with_fallbacks(backup_models)
        return local_ollama_model

    # Staging / Production mode: start with Groq, fallback to Gemini
    if backup_models:
        return backup_models[0].with_fallbacks(backup_models[1:]) if len(backup_models) > 1 else backup_models[0]

    # Fallback to local Ollama if no cloud keys configured
    return local_ollama_model


def get_streaming_provider(
    messages: Sequence[Any],
) -> tuple[Iterator[str], str]:
    """Return a synchronous text-token iterator and the configured provider fallback order."""
    resilient_ai_brain = create_resilient_ai_brain()
    provider_order = (
        "Ollama -> Groq -> Gemini"
        if APP_ENV == "local"
        else "Groq -> Gemini"
    )

    def stream_text_tokens() -> Iterator[str]:
        for response_chunk in resilient_ai_brain.stream(messages):
            text_token = extract_clean_text_response(response_chunk)
            if text_token:
                yield text_token

    return stream_text_tokens(), provider_order


async def get_async_streaming_provider(
    messages: Sequence[Any],
) -> tuple[AsyncIterator[str], str]:
    """Return an asynchronous text-token iterator for non-blocking FastAPI streaming."""
    resilient_ai_brain = create_resilient_ai_brain()
    provider_order = (
        "Ollama -> Groq -> Gemini"
        if APP_ENV == "local"
        else "Groq -> Gemini"
    )

    async def astream_text_tokens() -> AsyncIterator[str]:
        async for response_chunk in resilient_ai_brain.astream(messages):
            text_token = extract_clean_text_response(response_chunk)
            if text_token:
                yield text_token

    return astream_text_tokens(), provider_order