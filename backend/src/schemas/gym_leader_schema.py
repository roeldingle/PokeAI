"""
Gym Leader Schema Module
Defines Pydantic v2 data contracts for the Lesson 9 Autonomous Gym Leader AI Agent.
Models the Perceive -> Remember -> Decide -> Act decision loop, persona conditioning,
and dynamic threat calibration against the player's +1% stat progression multiplier.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class GymLeaderPersona(str, Enum):
    """
    Distinct opponent personas conditioning tactical priorities and in-character taunts.
    """
    WILD_INSTINCT = "WILD_INSTINCT"  # Wild Pidgey (#16) - instinctual territorial fighter
    BROCK = "BROCK"                  # Pewter City Gym Leader (#95 Onix) - rock-solid strategist
    MISTY = "MISTY"                  # Cerulean City Gym Leader (#121 Starmie) - all-out water offensive


class AgentMoodState(str, Enum):
    """
    Dynamic emotional/tactical state of the opponent agent calculated during the Perceive step.
    """
    CALCULATING = "CALCULATING"            # Early battle probing & balanced move selection
    AGGRESSIVE = "AGGRESSIVE"              # Pressing elemental advantage or countering scaled player threat
    DEFENSIVE = "DEFENSIVE"                # Cautious posture when facing type disadvantage
    DESPERATE_CLUTCH = "DESPERATE_CLUTCH"  # Low HP (<= 30%) all-out high-power finishing mode


class GymLeaderTurnDecisionRequest(BaseModel):
    """
    Request payload for querying the Autonomous Gym Leader Agent's decision loop.
    """
    # Active battle session identifier
    battle_session_id: str = Field(
        ...,
        min_length=1,
        description="Active battle session ID to evaluate.",
    )
    # Optional explicit persona override (auto-detected from opponent species if omitted)
    gym_leader_persona: Optional[GymLeaderPersona] = Field(
        default=None,
        description="Opponent persona (WILD_INSTINCT, BROCK, or MISTY).",
    )
    # Whether to query live LLM providers for taunt generation or use deterministic agent loop
    use_llm_gateway: bool = Field(
        default=False,
        description="True to invoke ResilientLLMGateway for dynamic taunt phrasing.",
    )


class GymLeaderTurnDecision(BaseModel):
    """
    Structured output of the Autonomous Gym Leader Agent's Perceive -> Remember -> Decide -> Act loop.
    """
    # Numerical ID of the chosen opponent move slot
    selected_move_id: int = Field(
        ...,
        description="Move ID chosen by the autonomous opponent agent.",
    )
    # Display name of the chosen opponent move
    selected_move_name: str = Field(
        ...,
        description="Display name of the move chosen by the agent.",
    )
    # Chain-of-thought tactical reasoning explaining why this move maximizes expected utility
    internal_tactical_reasoning: str = Field(
        ...,
        description="Internal Perceive-Remember-Decide reasoning trace.",
    )
    # In-character stadium taunt delivered by Brock, Misty, or the wild monster
    in_character_dialogue_taunt: str = Field(
        ...,
        description="In-character battle taunt conditioned on persona and mood.",
    )
    # Current mood state of the autonomous agent
    agent_mood: AgentMoodState = Field(
        ...,
        description="Calculated tactical mood state of the agent.",
    )
    # Calibrated threat score on a 0.0 to 10.0 scale factoring in player's +1% stat multiplier
    calibrated_threat_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Dynamic threat score (0.0 to 10.0) of the player's active monster.",
    )
    # The player's current +1% victory stat progression multiplier detected by the agent
    detected_player_stat_multiplier: float = Field(
        default=1.0,
        ge=1.0,
        description="Player stat progression multiplier (1.0 + victories * 0.01) perceived by the agent.",
    )
    # Active persona identity of the opponent
    gym_leader_persona: GymLeaderPersona = Field(
        default=GymLeaderPersona.WILD_INSTINCT,
        description="Active opponent persona.",
    )
    # Provider channel used
    active_provider_name: str = Field(
        default="autonomous_agent_engine",
        description="Execution engine or LLM provider channel.",
    )
    # Execution latency in milliseconds
    execution_latency_milliseconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Decision loop execution time in milliseconds.",
    )
