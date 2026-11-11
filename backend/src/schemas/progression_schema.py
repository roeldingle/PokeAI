"""
Progression Schema Module
Defines Pydantic v2 data contracts for Lesson 6:
- 5-Turn Battle Clock state tracking
- Pre-Turn 1 TEAM party swapping rules
- +1% incremental stat mastery progression per victory
- Move Slot 3 (10 wins) and Move Slot 4 (20 wins) unlock milestones
- Automatic opponent recruitment into the trainer's party pool upon knockout
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot


class RecruitedPartyMonster(BaseModel):
    """
    Represents an individual monster in the trainer's party pool.
    Stores both immutable baseline species stats and dynamically scaled effective stats
    computed from the monster's cumulative victory count.
    """
    # National Pokédex identifier for the species
    pokemon_id: int = Field(description="National Pokédex ID of the monster")
    # Display name of the monster species
    pokemon_name: str = Field(description="Species name of the monster")
    # Current combat level
    level: int = Field(ge=1, le=100, description="Combat level of the monster")
    # Elemental typing list (e.g. ['fire'], ['normal', 'flying'])
    elemental_types: List[str] = Field(description="Elemental types assigned to this species")
    # Total number of tournament victories achieved by this monster
    victories_count: int = Field(default=0, ge=0, description="Cumulative victories earned by this monster")
    # Calculated progression multiplier: 1.0 + (victories_count * 0.01)
    stat_progression_multiplier: float = Field(
        default=1.0,
        ge=1.0,
        description="Stat multiplier scaling factor (+1% per victory)",
    )
    # Unscaled baseline health points at Lv 6 / Lv 5
    base_health_points: int = Field(ge=1, description="Unscaled base maximum health points")
    # Unscaled baseline physical attack stat
    base_attack_stat: int = Field(ge=1, description="Unscaled base attack stat")
    # Unscaled baseline physical defense stat
    base_defense_stat: int = Field(ge=1, description="Unscaled base defense stat")
    # Unscaled baseline speed priority stat
    base_speed_stat: int = Field(ge=1, description="Unscaled base speed stat")
    # Scaled effective maximum health points: round(base_hp * multiplier)
    effective_health_points: int = Field(ge=1, description="Progression-scaled maximum health points")
    # Scaled effective attack stat: round(base_attack * multiplier)
    effective_attack_stat: int = Field(ge=1, description="Progression-scaled attack stat")
    # Scaled effective defense stat: round(base_defense * multiplier)
    effective_defense_stat: int = Field(ge=1, description="Progression-scaled defense stat")
    # Scaled effective speed stat: round(base_speed * multiplier)
    effective_speed_stat: int = Field(ge=1, description="Progression-scaled speed stat")
    # URL for the front-facing animated sprite
    sprite_front_url: str = Field(description="Front-facing sprite image URL")
    # URL for the back-facing animated sprite
    sprite_back_url: str = Field(description="Back-facing sprite image URL")
    # Up to 4 move slots with dynamic unlock states based on victories_count
    move_slots: List[PokemonMoveSlot] = Field(description="Move palette with milestone unlock flags")


class TrainerPartyPoolState(BaseModel):
    """
    Represents the complete roster of monsters recruited by a trainer,
    along with pre-turn TEAM swap eligibility flags.
    """
    # Name of the player trainer
    trainer_name: str = Field(description="Name of the trainer owning this party pool")
    # Pokédex ID of the monster currently assigned as the active lead combatant
    active_pokemon_id: int = Field(description="Pokédex ID of the currently active monster")
    # Total count of monsters in the trainer's pool
    total_party_count: int = Field(ge=1, description="Total number of monsters in the trainer's party pool")
    # Flag indicating whether the TEAM button should be enabled (requires > 1 monster)
    is_team_swap_enabled: bool = Field(
        description="True when the trainer owns 2 or more monsters, False when only 1 monster is owned"
    )
    # Ordered list of all monsters recruited into the trainer's pool
    party_monsters: List[RecruitedPartyMonster] = Field(description="Roster of recruited monsters")


class TeamSwapRequest(BaseModel):
    """
    Payload sent by the frontend when the trainer clicks TEAM and selects a different
    party monster before Turn 1 combat begins.
    """
    # Unique battle session UUID string
    battle_session_id: str = Field(description="Active battle session identifier")
    # Pokédex ID of the party monster to bring into the arena
    target_pokemon_id: int = Field(description="Pokédex ID of the monster to swap in as active")


class TeamSwapResponse(BaseModel):
    """
    Response returned after validating and executing a pre-Turn 1 party swap.
    """
    # Unique battle session UUID string
    battle_session_id: str = Field(description="Active battle session identifier")
    # Name of the monster that was recalled to the bench
    previous_pokemon_name: str = Field(description="Name of the monster swapped out")
    # Updated active battle entity now standing on the player's grass pedestal
    new_active_monster: ActiveBattleEntity = Field(description="Newly swapped-in active combatant entity")
    # Updated party pool state reflecting the new active lead
    party_pool_state: TrainerPartyPoolState = Field(description="Updated trainer party pool state")
    # Retro GBA narration line announcing the switch
    narrative_announcement: str = Field(description="Stadium narration announcing the partner switch")


class VictoryProgressionUpdateResponse(BaseModel):
    """
    Comprehensive summary of post-battle progression rewards when a trainer wins by knockout:
    - +1% stat boost calculation
    - Move Slot 3 (10 wins) or Move Slot 4 (20 wins) unlock notifications
    - Auto-recruitment of the defeated opponent into the trainer's party pool
    """
    # Name of the victorious trainer
    trainer_name: str = Field(description="Name of the victorious trainer")
    # Pokédex ID of the monster that earned the victory
    victorious_pokemon_id: int = Field(description="Pokédex ID of the winning monster")
    # Name of the monster that earned the victory
    victorious_pokemon_name: str = Field(description="Name of the winning monster")
    # Experience points awarded for the victory
    experience_points_gained: int = Field(default=45, ge=0, description="EXP awarded for winning the match")
    # New cumulative victory count after adding this win
    updated_victories_count: int = Field(ge=1, description="Updated total victories for this monster")
    # New stat progression multiplier: 1.0 + (updated_victories_count * 0.01)
    stat_progression_multiplier: float = Field(ge=1.0, description="Updated +1% per win stat multiplier")
    # List of move names unlocked on this exact victory milestone (e.g. ['Ember'] at 10 wins)
    newly_unlocked_move_names: List[str] = Field(
        default_factory=list,
        description="Move names unlocked at this exact victory milestone",
    )
    # Whether the defeated opponent was newly added to the trainer's party pool
    was_opponent_auto_recruited: bool = Field(
        description="True if the knocked-out opponent was newly added to the party pool"
    )
    # Species name of the opponent that was knocked out and recruited
    recruited_opponent_pokemon_name: Optional[str] = Field(
        default=None,
        description="Name of the defeated monster recruited into the party pool",
    )
    # Updated ActiveBattleEntity reflecting the new scaled stats and unlocked moves
    updated_monster_entity: ActiveBattleEntity = Field(
        description="Updated combat entity with +1% stat scaling and unlocked moves applied"
    )
    # Updated trainer party pool state including any newly recruited monster
    updated_party_pool: TrainerPartyPoolState = Field(
        description="Complete updated party pool for the trainer"
    )
