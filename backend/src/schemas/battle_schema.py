"""
Battle Schema Module
Defines rigorous Pydantic v2 data models for turn-based GBA combat.
These models enforce strict data validation for moves, battle participants, and turn resolutions.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PokemonMoveSlot(BaseModel):
    """
    Represents an attack or status move mapped to one of the 4 classic GBA move slots.
    Tracks power, accuracy, current/max power points (PP), and unlock milestones.
    """
    # Unique numerical identifier for the move
    move_id: int = Field(description="Unique identifier for the attack move")
    # Human-readable name of the move (e.g. Scratch, Ember)
    move_name: str = Field(description="Display name of the move")
    # Elemental classification (e.g. fire, water, grass, normal)
    elemental_type: str = Field(description="Elemental type classification for advantage calculations")
    # Base attack power used in physical damage calculation (0 for status moves)
    base_power: int = Field(ge=0, description="Base attack power value")
    # Percentage chance that the move connects with the target
    accuracy_percentage: int = Field(ge=1, le=100, description="Hit accuracy percentage between 1 and 100")
    # Remaining power points available for this battle
    current_power_points: int = Field(ge=0, description="Remaining uses of this move")
    # Maximum power points when fully refreshed
    maximum_power_points: int = Field(ge=1, description="Maximum total uses of this move")
    # Flag indicating whether this slot is currently unlocked for the player
    is_unlocked: bool = Field(default=True, description="True if unlocked, false if locked behind victory count")
    # Number of victories required to unlock this move slot (0 for starters, 10 for slot 3, 20 for slot 4)
    unlock_victory_threshold: int = Field(default=0, description="Victories required to unlock this slot")


class ActiveBattleEntity(BaseModel):
    """
    Represents an active combatant on the battlefield (Player Monster or Opponent Monster).
    Encapsulates core stats, real-time health points, and active move slots.
    """
    # National Pokédex number
    pokemon_id: int = Field(description="National Pokédex ID")
    # Species display name
    pokemon_name: str = Field(description="Species name of the monster")
    # Current combat level
    level: int = Field(ge=1, le=100, description="Combat level of the monster")
    # List of elemental types assigned to this monster (e.g. ['fire'], ['normal', 'flying'])
    elemental_types: List[str] = Field(description="Elemental typing for calculating incoming damage")
    # Current active health points (hit points)
    current_health_points: int = Field(ge=0, description="Current health points remaining")
    # Total maximum health points at full vitality
    maximum_health_points: int = Field(ge=1, description="Maximum total health capacity")
    # Attack statistic determining outgoing physical damage
    attack_stat: int = Field(ge=1, description="Base attack statistic")
    # Defense statistic mitigating incoming physical damage
    defense_stat: int = Field(ge=1, description="Base defense statistic")
    # Speed statistic determining turn priority (who strikes first)
    speed_stat: int = Field(ge=1, description="Speed stat for turn initiative priority")
    # URL pointing to front-facing sprite image (used for opponent display)
    sprite_front_url: str = Field(description="Front-facing sprite image URL")
    # URL pointing to back-facing sprite image (used for player display)
    sprite_back_url: str = Field(description="Back-facing sprite image URL")
    # Exactly 4 move slots representing the classic GBA attack palette
    move_slots: List[PokemonMoveSlot] = Field(description="Up to 4 move slots for the combatant")


class BattleInitiationRequest(BaseModel):
    """
    Payload dispatched by the frontend to start an authentic GBA battle.
    """
    # Name of the trainer starting the battle
    trainer_name: str = Field(min_length=1, max_length=50, description="Name of the player trainer")
    # ID of the player's selected monster
    selected_pokemon_id: int = Field(description="Pokédex ID of the active starter or party monster")
    # Optional opponent ID (defaults to Pidgey ID 16 if omitted)
    opponent_pokemon_id: Optional[int] = Field(default=16, description="Opponent Pokédex ID (default Pidgey)")


class TurnActionRequest(BaseModel):
    """
    Payload dispatched when the player selects a move from the 2x2 move grid.
    """
    # Unique identifier of the battle session
    battle_session_id: str = Field(description="Unique UUID string tracking the active match")
    # Numerical ID of the move selected by the player
    selected_move_id: int = Field(description="ID of the move selected by the player")


class SingleMoveResolution(BaseModel):
    """
    The calculated outcome of a single attack action taken by either combatant.
    """
    # Name of the monster initiating the attack
    attacker_name: str = Field(description="Name of the attacking monster")
    # Name of the monster receiving the attack
    defender_name: str = Field(description="Name of the defending monster")
    # Display name of the move performed
    move_name: str = Field(description="Name of the move used")
    # Whether the move successfully hit or missed based on accuracy
    is_hit_successful: bool = Field(description="True if attack connected, False if missed")
    # Exact numerical damage subtracted from defender's HP
    calculated_damage: int = Field(ge=0, description="Exact damage inflicted")
    # Elemental effectiveness multiplier (2.0 = Super Effective, 0.5 = Resisted, 1.0 = Neutral, 0.0 = Immune)
    type_effectiveness_multiplier: float = Field(description="Type matchup multiplier")
    # Indicates whether the attack scored a critical strike
    is_critical_hit: bool = Field(description="True if critical hit landed")
    # Remaining health points of the defender after damage calculation
    defender_remaining_health_points: int = Field(ge=0, description="Defender HP after resolution")
    # Maximum health points of the defender for UI ratio calculations
    defender_maximum_health_points: int = Field(ge=1, description="Defender max HP")
    # GBA style narration string (e.g. 'Charmander used Scratch! It dealt 5 damage.')
    narrative_announcement: str = Field(description="Battle log narrative message")


class BattleTurnResolutionResponse(BaseModel):
    """
    Comprehensive response returned after resolving a round of combat.
    Contains both actions in initiative order, updated combatant states, and match status.
    """
    # Unique identifier for the battle session
    battle_session_id: str = Field(description="Session ID of the battle")
    # Current turn number (e.g. 1 of 5)
    current_turn_number: int = Field(ge=1, description="Current turn index")
    # First action executed in the turn based on speed initiative
    first_action_resolution: SingleMoveResolution = Field(description="First attack executed")
    # Second action executed (optional if defender was knocked out by the first strike)
    second_action_resolution: Optional[SingleMoveResolution] = Field(default=None, description="Retaliation attack if defender survived")
    # Updated state of the player monster
    player_monster: ActiveBattleEntity = Field(description="Updated player combatant state")
    # Updated state of the opponent monster
    opponent_monster: ActiveBattleEntity = Field(description="Updated opponent combatant state")
    # Whether the battle has concluded (either by knockout or completion)
    is_battle_concluded: bool = Field(description="True if match has ended")
    # Name of the winning monster if battle is concluded
    victorious_monster_name: Optional[str] = Field(default=None, description="Name of winner if resolved")
    # Maximum turns allowed per battle match (Lesson 6 5-Turn Battle Clock)
    maximum_turns_allowed: int = Field(default=5, ge=1, description="Maximum turns permitted per match")
    # True when Turn 5 finishes and both combatants are still standing (triggers Catch Roulette in Lesson 7)
    is_turn_limit_reached: bool = Field(default=False, description="True if Turn 5 expired without a knockout")
    # Post-battle progression summary (+1% stat scaling, move slot unlocks, and KO auto-recruitment)
    progression_update: Optional[dict] = Field(
        default=None,
        description="Progression reward details when the player wins by knockout",
    )
    # Lesson 9 Autonomous Gym Leader AI decision telemetry (Perceive -> Remember -> Decide -> Act)
    gym_leader_decision: Optional[dict] = Field(
        default=None,
        description="Autonomous Gym Leader AI turn decision and dynamic threat telemetry",
    )
