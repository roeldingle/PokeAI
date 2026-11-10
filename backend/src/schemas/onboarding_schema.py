"""
Onboarding Schema Module
Defines Pydantic v2 data models for starter monster catalogs and trainer registration contracts.
"""

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StarterMonsterInfo(BaseModel):
    """
    Structured data representation of a starter monster available for selection.
    Guarantees consistent base combat metrics across frontend UI cards and backend battle engines.
    """

    # Enforce strict validation without arbitrary unmapped fields
    model_config = ConfigDict(
        # Prevent undeclared fields from slipping into our battle roster
        extra="forbid",
        # Provide OpenAPI documentation sample payload
        json_schema_extra={
            "example": {
                "starter_pokemon_id": 4,
                "monster_name": "Charmander",
                "elemental_types": ["Fire"],
                "starter_description": "Obviously prefers hot places. When it rains, steam is said to spout from the tip of its tail.",
                "base_hit_points": 39,
                "base_attack_power": 52,
                "base_defense_rating": 43,
                "base_speed_velocity": 65,
                "front_sprite_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png",
            }
        },
    )

    # Official National Pokédex identifier (1 for Bulbasaur, 4 for Charmander, 7 for Squirtle)
    starter_pokemon_id: int = Field(
        ...,
        description="Official Pokédex numerical identifier for this starter monster",
    )

    # Canonical monster name displayed across stadium screens
    monster_name: str = Field(
        ...,
        description="Display name of the starter monster",
    )

    # List of elemental types determining combat strengths and weaknesses
    elemental_types: list[str] = Field(
        ...,
        description="Elemental types (e.g., Grass, Poison, Fire, Water)",
    )

    # Narrative lore description used by Shaneil and AI prompts
    starter_description: str = Field(
        ...,
        description="Pokédex lore entry explaining the monster's biology and temperament",
    )

    # Fundamental base hit points determining monster vitality
    base_hit_points: int = Field(
        ...,
        gt=0,
        description="Initial base health capacity of the monster",
    )

    # Base physical and special combat striking power
    base_attack_power: int = Field(
        ...,
        gt=0,
        description="Base offensive combat rating",
    )

    # Base defensive resistance against incoming damage
    base_defense_rating: int = Field(
        ...,
        gt=0,
        description="Base damage reduction metric",
    )

    # Base speed determining action priority order in battle turns
    base_speed_velocity: int = Field(
        ...,
        gt=0,
        description="Speed metric governing turn order in combat",
    )

    # Public web asset URL for the pixelated front battle sprite
    front_sprite_url: str = Field(
        ...,
        description="Direct web URL to the pixelated front battle sprite",
    )


class TrainerRegistrationRequest(BaseModel):
    """
    Intake payload submitted by the player when locking in their name and starter choice.
    """

    model_config = ConfigDict(
        # Disallow extra fields to keep the intake strictly bounded
        extra="forbid",
        json_schema_extra={
            "example": {
                "trainer_name": "Red_Champion",
                "selected_starter_id": 4,
            }
        },
    )

    # Trainer name validated between 2 and 20 characters
    trainer_name: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Chosen trainer name for the current player",
    )

    # Starter ID selection (1 = Bulbasaur, 4 = Charmander, 7 = Squirtle, or index 1, 2, 3)
    selected_starter_id: int = Field(
        ...,
        description="ID of the chosen starter monster (1, 4, 7 or 1, 2, 3)",
    )


class TrainerProfileResponse(BaseModel):
    """
    Confirmed tournament registration card returned after successful onboarding.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "trainer_registration_id": "trainer-9b1deb4d",
                "trainer_name": "Red_Champion",
                "victories_count": 0,
                "stat_progression_multiplier": 1.0,
                "created_at_timestamp": "2026-11-10T06:00:00Z",
            }
        },
    )

    # Unique registration ticket identifier
    trainer_registration_id: str = Field(
        ...,
        description="System-generated unique identifier for this registered trainer",
    )

    # Confirmed trainer display name
    trainer_name: str = Field(
        ...,
        description="Confirmed player trainer name",
    )

    # Full data contract of the selected starter partner
    selected_starter_monster: StarterMonsterInfo = Field(
        ...,
        description="Complete details and stats of the chosen starter monster",
    )

    # Battle track record initialized to 0
    victories_count: int = Field(
        default=0,
        ge=0,
        description="Count of battles won in the arena",
    )

    # Initial baseline stat multiplier (progresses +1% per win)
    stat_progression_multiplier: float = Field(
        default=1.0,
        ge=1.0,
        description="Active stat progression multiplier for battle calculations",
    )

    # ISO timestamp when registration was established
    created_at_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of registration",
    )