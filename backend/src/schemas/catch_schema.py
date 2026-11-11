"""
Catch Schema Module
Defines the Pydantic data contracts for Lesson 7 Catch Pokémon Roulette Phase:
- PokeballTier: Enum representing the 4 wheel tiers (GOLD, SILVER, BRONZE, NORMAL)
- CatchRouletteSpinRequest: Request to spin the overtime capture wheel
- CatchRouletteOutcome: Full outcome of the spin, capture probability check, and party recruitment
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from src.schemas.progression_schema import TrainerPartyPoolState


class PokeballTier(str, Enum):
    """
    The four canonical Pokéball tiers available on the retro roulette wheel.
    Each tier maps to an explicit, calibrated capture probability.
    """
    GOLD = "GOLD"        # 90% capture rate (Legendary gold tier)
    SILVER = "SILVER"    # 75% capture rate (High-grade silver tier)
    BRONZE = "BRONZE"    # 60% capture rate (Sturdy bronze tier)
    NORMAL = "NORMAL"    # 50% capture rate (Standard red-and-white Pokéball)


class CatchRouletteSpinRequest(BaseModel):
    """
    Request envelope sent from the frontend when the trainer spins the roulette wheel
    after Turn 5 expires without a knockout.
    """
    # Registered trainer profile name
    trainer_name: str = Field(
        ...,
        min_length=1,
        description="Registered trainer profile identifier."
    )
    # Target wild monster information
    opponent_pokemon_id: int = Field(
        ...,
        gt=0,
        description="PokéAPI species ID of the targeted wild monster."
    )
    opponent_pokemon_name: str = Field(
        ...,
        min_length=1,
        description="Display name of the targeted wild monster."
    )
    opponent_pokemon_sprite_url: str = Field(
        default="",
        description="Front sprite image URL of the target monster."
    )
    opponent_level: int = Field(
        default=5,
        ge=1,
        description="Level of the targeted wild monster."
    )
    # Optional injected deterministic test rolls (0.0 to 1.0)
    injected_tier_roll: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional deterministic roll for selecting pokeball tier (used in unit tests)."
    )
    injected_catch_roll: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional deterministic roll for catch success verification (used in unit tests)."
    )


class CatchRouletteOutcome(BaseModel):
    """
    Comprehensive outcome returned after the roulette wheel spins and the capture roll resolves.
    """
    # The tier landed on by the wheel
    selected_pokeball_tier: PokeballTier = Field(
        ...,
        description="The Pokéball tier landed on the roulette wheel."
    )
    # The exact capture probability for this tier (0.50, 0.60, 0.75, or 0.90)
    capture_probability: float = Field(
        ...,
        description="Calibrated probability of capturing the wild monster (0.50 to 0.90)."
    )
    # Whether the capture roll succeeded
    capture_successful: bool = Field(
        ...,
        description="True if the capture succeeded; False if the monster broke free."
    )
    # Name of the monster targeted
    captured_monster_name: str = Field(
        ...,
        description="The display name of the target monster."
    )
    # Authentic stadium commentator play-by-play narrative
    narrative_outcome: str = Field(
        ...,
        description="Stadium announcement describing the roulette spin and catch result."
    )
    # Updated trainer party pool if recruitment occurred
    updated_party_pool: Optional[TrainerPartyPoolState] = Field(
        default=None,
        description="Updated party pool state reflecting the newly recruited monster if captured."
    )
