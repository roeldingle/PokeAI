"""
Educational Module Docstring:
This module defines the Pydantic v2 data contracts for our asynchronous PokéAPI client.
In production AI engineering, external APIs return deeply-nested, unpredictable JSON.
These schemas act as a stadium security gate: ensuring all data is validated, typed,
and normalized before passing downstream to our ChromaDB vector store in Lesson 04.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PokemonCombatStats(BaseModel):
    """
    Standardized combat metrics extracted from raw PokéAPI combat data.
    Ensures that battle calculations in Lesson 05 always receive integers.
    """
    # Restricts extra unknown fields while allowing standard attribute access
    model_config = ConfigDict(extra="ignore")

    # Base hit points representing monster vitality
    hit_points: int = Field(
        ...,
        description="The base health points of the monster before stat multipliers"
    )
    # Base physical attack power
    attack: int = Field(
        ...,
        description="Base physical attack damage output"
    )
    # Base physical armor and damage mitigation
    defense: int = Field(
        ...,
        description="Base physical damage reduction"
    )
    # Special elemental attack output
    special_attack: int = Field(
        ...,
        description="Base special attack power for elemental strikes"
    )
    # Special elemental defense mitigation
    special_defense: int = Field(
        ...,
        description="Base special defense resistance against elemental strikes"
    )
    # Agility metric determining turn order in the battle arena
    speed: int = Field(
        ...,
        description="Speed metric deciding which combatant strikes first in each turn"
    )


class PokemonSpeciesLoreRecord(BaseModel):
    """
    Unified domain model combining combat parameters and natural language lore.
    This is the exact contract stored in ChromaDB vector memory in Lesson 04.
    """
    model_config = ConfigDict(extra="ignore")

    # Official National Pokédex serial number
    pokemon_id: int = Field(
        ...,
        description="Canonical National Pokédex integer identifier"
    )
    # Lowercase canonical monster name (e.g., 'charmander', 'bulbasaur')
    pokemon_name: str = Field(
        ...,
        description="Lowercase canonical monster identifier name"
    )
    # List of primary and secondary elemental affinities (e.g., ['fire'], ['grass', 'poison'])
    elemental_types: List[str] = Field(
        default_factory=list,
        description="List of elemental type categories assigned to this monster"
    )
    # Flattened dictionary of base combat statistics for fast lookup
    base_stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Dictionary mapping stat names to baseline integer values"
    )
    # Passive combat traits and special characteristics
    abilities: List[str] = Field(
        default_factory=list,
        description="List of passive battle capabilities and traits"
    )
    # Cleaned, single-line English Pokédex description used for vector embeddings
    lore_flavor_text: str = Field(
        ...,
        description="Sanitized English species lore description for vector embeddings"
    )
    # Official front-facing sprite image URL for UI rendering
    front_default_sprite_url: Optional[str] = Field(
        default=None,
        description="Direct HTTP URL pointing to the monster's front pixel sprite"
    )