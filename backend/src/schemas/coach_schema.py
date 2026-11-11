"""
Coach Schema Module
Defines Pydantic v2 data contracts for the Lesson 8 'ASK GUIDE' Tactical RAG Coach.
Enforces strict typing for incoming tactical queries and outgoing RAG-grounded battle advice.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CoachTacticalAdviceRequest(BaseModel):
    """
    Request payload dispatched when a trainer selects 'ASK GUIDE' in the GBA Battle Arena.
    """
    # Unique UUID string identifying the active battle session
    battle_session_id: str = Field(
        ...,
        min_length=1,
        description="Active battle session identifier to inspect combat state.",
    )
    # Optional custom question from the trainer (e.g., 'Should I use Scratch or Ember?')
    custom_trainer_question: Optional[str] = Field(
        default=None,
        description="Optional natural language question from the trainer.",
    )
    # Whether to query live LLM providers or use instant deterministic RAG synthesis
    use_llm_gateway: bool = Field(
        default=True,
        description="True to query ResilientLLMGateway, False for instant deterministic RAG synthesis.",
    )


class CoachTacticalAdviceResponse(BaseModel):
    """
    Comprehensive tactical advice envelope returned by the Game Guide RAG Coach.
    Combines deterministic elemental math, ChromaDB retrieved opponent lore, and LLM reasoning.
    """
    # Unique battle session ID that was analyzed
    battle_session_id: str = Field(
        ...,
        description="Battle session identifier analyzed by the coach.",
    )
    # Dynamic name of the Game Guide loaded from .env / config.py
    game_guide_name: str = Field(
        ...,
        description="Name of the Game Guide delivering the tactical whisper.",
    )
    # Exact display name of the optimal unlocked move (e.g., 'Ember', 'Scratch')
    recommended_action_name: str = Field(
        ...,
        description="Name of the recommended move or tactical action.",
    )
    # Numerical move ID corresponding to the recommended move slot
    recommended_move_id: Optional[int] = Field(
        default=None,
        description="Move slot ID of the recommended attack for one-click execution.",
    )
    # In-character tactical explanation grounded in vector lore and type math
    tactical_justification: str = Field(
        ...,
        description="Concise, encouraging tactical whisper from the Game Guide.",
    )
    # Calibrated confidence score between 0.0 and 1.0
    confidence_rating: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) in the recommended counter-move.",
    )
    # Snippet of opponent species lore retrieved from ChromaDB vector memory
    retrieved_lore_context: str = Field(
        ...,
        description="Vector-retrieved opponent Pokédex lore grounding the advice.",
    )
    # Summary of elemental effectiveness multipliers across unlocked moves
    elemental_matchup_summary: str = Field(
        ...,
        description="Human-readable summary of move effectiveness multipliers.",
    )
    # Active AI provider channel that synthesized the justification
    active_provider_name: str = Field(
        default="offline_fallback",
        description="LLM provider channel used (ollama, groq, gemini, or offline_fallback).",
    )
    # Specific model identifier used for generation
    model_identifier: str = Field(
        default="tactical-rag- synthesizer",
        description="Model identifier that generated the tactical advice.",
    )
    # Round-trip execution latency in milliseconds
    execution_latency_milliseconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total RAG retrieval and LLM generation latency in milliseconds.",
    )
