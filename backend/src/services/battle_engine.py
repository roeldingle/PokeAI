"""
Battle Engine Service Module
Implements deterministic combat resolution, authentic Gen-1 damage arithmetic,
18-type elemental advantage matrices, and turn initiative resolution.
In production AI engineering, this deterministic engine ensures the generative AI layer
never hallucinates hit points, combat math, or rule logic.
"""

import math
import random
import uuid
from typing import Dict, List, Optional, Tuple
from src.schemas.battle_schema import (
    ActiveBattleEntity,
    BattleTurnResolutionResponse,
    PokemonMoveSlot,
    SingleMoveResolution,
)

# Complete 18-type Pokémon elemental advantage lookup matrix
# Keys represent the Attacking Move Type, nested dictionaries map Defending Types to multipliers
ELEMENTAL_TYPE_CHART_MATRIX: Dict[str, Dict[str, float]] = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "electric": {"water": 2.0, "grass": 0.5, "electric": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
    "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
    "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
    "ground": {"fire": 2.0, "grass": 0.5, "electric": 2.0, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying": {"grass": 2.0, "electric": 0.5, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5},
    "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5},
    "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0},
    "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5},
}


class BattleEngineService:
    """
    Core deterministic combat engine managing battle initialization, mathematical damage calculation,
    initiative resolution, and session state tracking.
    """

    def __init__(self) -> None:
        # In-memory storage for active battle sessions
        # Maps unique battle_session_id to active match dictionaries
        self.active_battle_sessions: Dict[str, Dict] = {}

    def calculate_elemental_effectiveness(
        self,
        attacking_move_elemental_type: str,
        defending_pokemon_elemental_types: List[str],
    ) -> float:
        """
        Calculates cumulative type effectiveness multiplier by cross-referencing
        the attacking move type against all defending elemental types.
        """
        # Normalize attacking move type to lowercase
        normalized_move_type = attacking_move_elemental_type.lower()
        # Initialize baseline neutral effectiveness multiplier
        cumulative_type_multiplier = 1.0

        # Retrieve advantage rules for this attacking type
        type_advantage_rules = ELEMENTAL_TYPE_CHART_MATRIX.get(normalized_move_type, {})

        # Iterate over each type the defending monster possesses
        for individual_defender_type in defending_pokemon_elemental_types:
            # Normalize target type
            normalized_defender_type = individual_defender_type.lower()
            # If an explicit matchup rule exists, multiply it; otherwise neutral (1.0)
            if normalized_defender_type in type_advantage_rules:
                cumulative_type_multiplier *= type_advantage_rules[normalized_defender_type]

        return cumulative_type_multiplier

    def calculate_damage_output(
        self,
        attacker_entity: ActiveBattleEntity,
        defender_entity: ActiveBattleEntity,
        move_to_execute: PokemonMoveSlot,
        enforce_deterministic_variance: bool = False,
    ) -> Tuple[int, float, bool]:
        """
        Computes damage inflicted using authentic Pokémon Gen-1 arithmetic:
        Damage = ((((2 * Level / 5 + 2) * BasePower * (Attack / Defense)) / 50) + 2) * Effectiveness * Critical
        """
        # If the move is a status move (0 base power), zero damage is inflicted
        if move_to_execute.base_power <= 0:
            return (0, 1.0, False)

        # Step 1: Calculate elemental type effectiveness multiplier
        effectiveness_multiplier = self.calculate_elemental_effectiveness(
            attacking_move_elemental_type=move_to_execute.elemental_type,
            defending_pokemon_elemental_types=defender_entity.elemental_types,
        )

        # If defender is completely immune (multiplier is 0.0), no damage is dealt
        if effectiveness_multiplier == 0.0:
            return (0, 0.0, False)

        # Step 2: Determine critical strike chance (approx 6.25% in classic Pokémon)
        # For strict deterministic testing, default to no critical hit unless rolled
        is_critical_strike = False
        critical_strike_multiplier = 1.0
        if not enforce_deterministic_variance:
            # 1 in 16 chance of landing a critical strike
            if random.random() < 0.0625:
                is_critical_strike = True
                critical_strike_multiplier = 1.5

        # Step 3: Compute core damage arithmetic
        # Step 3a: Level scaling component
        level_scaling_factor = ((2 * attacker_entity.level) / 5) + 2

        # Step 3b: Attack-to-Defense combat ratio
        combat_stat_ratio = attacker_entity.attack_stat / max(1, defender_entity.defense_stat)

        # Step 3c: Base arithmetic formula
        raw_base_damage = (
            ((level_scaling_factor * move_to_execute.base_power * combat_stat_ratio) / 50) + 2
        )

        # Step 3d: Apply type multiplier and critical strike
        scaled_damage = raw_base_damage * effectiveness_multiplier * critical_strike_multiplier

        # Step 3e: Apply standard damage variance (between 0.85 and 1.00) unless deterministic mode is enabled
        variance_multiplier = 1.00 if enforce_deterministic_variance else random.uniform(0.85, 1.00)
        final_damage_integer = math.floor(scaled_damage * variance_multiplier)

        # Ensure that any damaging move dealing > 0 effectiveness inflicts at least 1 HP of damage
        final_damage_guaranteed = max(1, final_damage_integer)

        return (final_damage_guaranteed, effectiveness_multiplier, is_critical_strike)

    def generate_action_narrative(
        self,
        attacker_name: str,
        defender_name: str,
        move_name: str,
        calculated_damage: int,
        type_multiplier: float,
        is_critical: bool,
        is_knockout: bool,
    ) -> str:
        """
        Builds retro GBA narrative announcement lines for the stadium dialogue box.
        """
        announcement_lines = [f"{attacker_name} used {move_name}!"]

        if is_critical:
            announcement_lines.append("Critical hit!")

        if type_multiplier >= 2.0:
            announcement_lines.append("It's super effective!")
        elif 0.0 < type_multiplier < 1.0:
            announcement_lines.append("It's not very effective...")
        elif type_multiplier == 0.0:
            announcement_lines.append(f"It had no effect on {defender_name}!")

        if calculated_damage > 0:
            announcement_lines.append(f"Dealt {calculated_damage} damage.")

        if is_knockout:
            announcement_lines.append(f"{defender_name} fainted!")

        return " ".join(announcement_lines)

    def create_starter_pokemon_entity(
        self,
        pokemon_id: int,
        trainer_name: str,
    ) -> ActiveBattleEntity:
        """
        Generates calibrated battle stats and 4 move slots for the player's chosen starter.
        Slots 1 and 2 are unlocked; Slots 3 and 4 are locked behind 10 and 20 victories.
        """
        # Charmander preset (Fire)
        if pokemon_id == 4:
            return ActiveBattleEntity(
                pokemon_id=4,
                pokemon_name="Charmander",
                level=6,
                elemental_types=["fire"],
                current_health_points=20,
                maximum_health_points=20,
                attack_stat=12,
                defense_stat=10,
                speed_stat=14,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/4.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/4.gif",
                move_slots=[
                    PokemonMoveSlot(move_id=1, move_name="Scratch", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=2, move_name="Growl", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=3, move_name="Ember", elemental_type="fire", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=10),
                    PokemonMoveSlot(move_id=4, move_name="Flamethrower", elemental_type="fire", base_power=90, accuracy_percentage=100, current_power_points=15, maximum_power_points=15, is_unlocked=False, unlock_victory_threshold=20),
                ],
            )
        # Bulbasaur preset (Grass/Poison)
        elif pokemon_id == 1:
            return ActiveBattleEntity(
                pokemon_id=1,
                pokemon_name="Bulbasaur",
                level=6,
                elemental_types=["grass", "poison"],
                current_health_points=21,
                maximum_health_points=21,
                attack_stat=11,
                defense_stat=11,
                speed_stat=11,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/1.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/1.gif",
                move_slots=[
                    PokemonMoveSlot(move_id=5, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=6, move_name="Growl", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=7, move_name="Vine Whip", elemental_type="grass", base_power=45, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=10),
                    PokemonMoveSlot(move_id=8, move_name="Solar Beam", elemental_type="grass", base_power=120, accuracy_percentage=100, current_power_points=10, maximum_power_points=10, is_unlocked=False, unlock_victory_threshold=20),
                ],
            )
        # Squirtle preset (Water)
        else:
            return ActiveBattleEntity(
                pokemon_id=7,
                pokemon_name="Squirtle",
                level=6,
                elemental_types=["water"],
                current_health_points=21,
                maximum_health_points=21,
                attack_stat=11,
                defense_stat=13,
                speed_stat=10,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/7.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/7.gif",
                move_slots=[
                    PokemonMoveSlot(move_id=9, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=10, move_name="Tail Whip", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=11, move_name="Water Gun", elemental_type="water", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=10),
                    PokemonMoveSlot(move_id=12, move_name="Hydro Pump", elemental_type="water", base_power=110, accuracy_percentage=80, current_power_points=5, maximum_power_points=5, is_unlocked=False, unlock_victory_threshold=20),
                ],
            )

    def create_wild_opponent_entity(self, pokemon_id: int = 16) -> ActiveBattleEntity:
        """
        Creates an authentic early-game wild opponent (Pidgey Lv 5) with animated showdown sprites.
        """
        return ActiveBattleEntity(
            pokemon_id=16,
            pokemon_name="Pidgey",
            level=5,
            elemental_types=["normal", "flying"],
            current_health_points=18,
            maximum_health_points=18,
            attack_stat=10,
            defense_stat=9,
            speed_stat=12,
            sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/16.gif",
            sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/16.gif",
            move_slots=[
                PokemonMoveSlot(move_id=13, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=14, move_name="Sand Attack", elemental_type="ground", base_power=0, accuracy_percentage=100, current_power_points=15, maximum_power_points=15, is_unlocked=True, unlock_victory_threshold=0),
            ],
        )

    def initialize_battle_session(
        self,
        trainer_name: str,
        selected_pokemon_id: int,
        opponent_pokemon_id: int = 16,
    ) -> Dict:
        """
        Instantiates a new battle session and records initial state in session storage.
        """
        # Generate unique UUID string for tracking this battle instance
        session_id = str(uuid.uuid4())

        # Construct player and opponent combatant models
        player_entity = self.create_starter_pokemon_entity(
            pokemon_id=selected_pokemon_id,
            trainer_name=trainer_name,
        )
        opponent_entity = self.create_wild_opponent_entity(
            pokemon_id=opponent_pokemon_id,
        )

        # Store session record in memory
        session_payload = {
            "battle_session_id": session_id,
            "trainer_name": trainer_name,
            "current_turn_number": 1,
            "is_battle_concluded": False,
            "victorious_monster_name": None,
            "player_monster": player_entity,
            "opponent_monster": opponent_entity,
        }
        self.active_battle_sessions[session_id] = session_payload
        return session_payload

    def resolve_combat_round(
        self,
        battle_session_id: str,
        selected_move_id: int,
        deterministic_mode: bool = False,
    ) -> BattleTurnResolutionResponse:
        """
        Executes a complete round of combat:
        1. Validates player move and decrements PP.
        2. Compares speed initiative to determine turn order.
        3. Executes first strike; knocks out defender if HP reaches 0.
        4. If defender survives, executes retaliation strike.
        5. Updates turn counter and returns structured response.
        """
        # Retrieve session state
        session_data = self.active_battle_sessions.get(battle_session_id)
        if not session_data:
            raise ValueError(f"Battle session '{battle_session_id}' not found.")

        if session_data["is_battle_concluded"]:
            raise ValueError("This battle has already concluded.")

        player_monster: ActiveBattleEntity = session_data["player_monster"]
        opponent_monster: ActiveBattleEntity = session_data["opponent_monster"]

        # Find selected player move
        chosen_player_move: Optional[PokemonMoveSlot] = next(
            (move for move in player_monster.move_slots if move.move_id == selected_move_id),
            None,
        )
        if not chosen_player_move:
            raise ValueError(f"Move with ID {selected_move_id} not available for {player_monster.pokemon_name}.")

        if not chosen_player_move.is_unlocked:
            raise ValueError(f"Move '{chosen_player_move.move_name}' is locked behind {chosen_player_move.unlock_victory_threshold} wins.")

        if chosen_player_move.current_power_points <= 0:
            raise ValueError(f"Move '{chosen_player_move.move_name}' has 0 PP remaining.")

        # Decrement player move PP
        chosen_player_move.current_power_points -= 1

        # Opponent selects a basic move (e.g. first available move with PP)
        opponent_move = next(
            (move for move in opponent_monster.move_slots if move.current_power_points > 0 and move.base_power > 0),
            opponent_monster.move_slots[0],
        )
        opponent_move.current_power_points = max(0, opponent_move.current_power_points - 1)

        # Determine speed initiative priority
        # If player speed >= opponent speed, player attacks first
        player_attacks_first = player_monster.speed_stat >= opponent_monster.speed_stat

        first_action: SingleMoveResolution
        second_action: Optional[SingleMoveResolution] = None

        if player_attacks_first:
            # Player strikes opponent first
            damage_to_opponent, type_mult_1, crit_1 = self.calculate_damage_output(
                attacker_entity=player_monster,
                defender_entity=opponent_monster,
                move_to_execute=chosen_player_move,
                enforce_deterministic_variance=deterministic_mode,
            )
            opponent_monster.current_health_points = max(0, opponent_monster.current_health_points - damage_to_opponent)
            opponent_knocked_out = opponent_monster.current_health_points == 0

            first_action = SingleMoveResolution(
                attacker_name=player_monster.pokemon_name,
                defender_name=opponent_monster.pokemon_name,
                move_name=chosen_player_move.move_name,
                is_hit_successful=True,
                calculated_damage=damage_to_opponent,
                type_effectiveness_multiplier=type_mult_1,
                is_critical_hit=crit_1,
                defender_remaining_health_points=opponent_monster.current_health_points,
                defender_maximum_health_points=opponent_monster.maximum_health_points,
                narrative_announcement=self.generate_action_narrative(
                    attacker_name=player_monster.pokemon_name,
                    defender_name=opponent_monster.pokemon_name,
                    move_name=chosen_player_move.move_name,
                    calculated_damage=damage_to_opponent,
                    type_multiplier=type_mult_1,
                    is_critical=crit_1,
                    is_knockout=opponent_knocked_out,
                ),
            )

            # If opponent survived, opponent retaliates
            if not opponent_knocked_out:
                damage_to_player, type_mult_2, crit_2 = self.calculate_damage_output(
                    attacker_entity=opponent_monster,
                    defender_entity=player_monster,
                    move_to_execute=opponent_move,
                    enforce_deterministic_variance=deterministic_mode,
                )
                player_monster.current_health_points = max(0, player_monster.current_health_points - damage_to_player)
                player_knocked_out = player_monster.current_health_points == 0

                second_action = SingleMoveResolution(
                    attacker_name=opponent_monster.pokemon_name,
                    defender_name=player_monster.pokemon_name,
                    move_name=opponent_move.move_name,
                    is_hit_successful=True,
                    calculated_damage=damage_to_player,
                    type_effectiveness_multiplier=type_mult_2,
                    is_critical_hit=crit_2,
                    defender_remaining_health_points=player_monster.current_health_points,
                    defender_maximum_health_points=player_monster.maximum_health_points,
                    narrative_announcement=self.generate_action_narrative(
                        attacker_name=opponent_monster.pokemon_name,
                        defender_name=player_monster.pokemon_name,
                        move_name=opponent_move.move_name,
                        calculated_damage=damage_to_player,
                        type_multiplier=type_mult_2,
                        is_critical=crit_2,
                        is_knockout=player_knocked_out,
                    ),
                )
        else:
            # Opponent strikes player first
            damage_to_player, type_mult_1, crit_1 = self.calculate_damage_output(
                attacker_entity=opponent_monster,
                defender_entity=player_monster,
                move_to_execute=opponent_move,
                enforce_deterministic_variance=deterministic_mode,
            )
            player_monster.current_health_points = max(0, player_monster.current_health_points - damage_to_player)
            player_knocked_out = player_monster.current_health_points == 0

            first_action = SingleMoveResolution(
                attacker_name=opponent_monster.pokemon_name,
                defender_name=player_monster.pokemon_name,
                move_name=opponent_move.move_name,
                is_hit_successful=True,
                calculated_damage=damage_to_player,
                type_effectiveness_multiplier=type_mult_1,
                is_critical_hit=crit_1,
                defender_remaining_health_points=player_monster.current_health_points,
                defender_maximum_health_points=player_monster.maximum_health_points,
                narrative_announcement=self.generate_action_narrative(
                    attacker_name=opponent_monster.pokemon_name,
                    defender_name=player_monster.pokemon_name,
                    move_name=opponent_move.move_name,
                    calculated_damage=damage_to_player,
                    type_multiplier=type_mult_1,
                    is_critical=crit_1,
                    is_knockout=player_knocked_out,
                ),
            )

            # If player survived, player retaliates
            if not player_knocked_out:
                damage_to_opponent, type_mult_2, crit_2 = self.calculate_damage_output(
                    attacker_entity=player_monster,
                    defender_entity=opponent_monster,
                    move_to_execute=chosen_player_move,
                    enforce_deterministic_variance=deterministic_mode,
                )
                opponent_monster.current_health_points = max(0, opponent_monster.current_health_points - damage_to_opponent)
                opponent_knocked_out = opponent_monster.current_health_points == 0

                second_action = SingleMoveResolution(
                    attacker_name=player_monster.pokemon_name,
                    defender_name=opponent_monster.pokemon_name,
                    move_name=chosen_player_move.move_name,
                    is_hit_successful=True,
                    calculated_damage=damage_to_opponent,
                    type_effectiveness_multiplier=type_mult_2,
                    is_critical_hit=crit_2,
                    defender_remaining_health_points=opponent_monster.current_health_points,
                    defender_maximum_health_points=opponent_monster.maximum_health_points,
                    narrative_announcement=self.generate_action_narrative(
                        attacker_name=player_monster.pokemon_name,
                        defender_name=opponent_monster.pokemon_name,
                        move_name=chosen_player_move.move_name,
                        calculated_damage=damage_to_opponent,
                        type_multiplier=type_mult_2,
                        is_critical=crit_2,
                        is_knockout=opponent_knocked_out,
                    ),
                )

        # Check match conclusion
        turn_number = session_data["current_turn_number"]
        is_concluded = (player_monster.current_health_points == 0) or (opponent_monster.current_health_points == 0)
        victor_name = None
        if opponent_monster.current_health_points == 0:
            victor_name = player_monster.pokemon_name
        elif player_monster.current_health_points == 0:
            victor_name = opponent_monster.pokemon_name

        # Increment turn number for subsequent rounds
        session_data["current_turn_number"] += 1
        session_data["is_battle_concluded"] = is_concluded
        session_data["victorious_monster_name"] = victor_name

        return BattleTurnResolutionResponse(
            battle_session_id=battle_session_id,
            current_turn_number=turn_number,
            first_action_resolution=first_action,
            second_action_resolution=second_action,
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            is_battle_concluded=is_concluded,
            victorious_monster_name=victor_name,
        )


# Global singleton instance for injection across route handlers
battle_engine_service = BattleEngineService()
