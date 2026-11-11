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
from src.services.battle_progression_service import (
    MAXIMUM_BATTLE_TURNS,
    BattleProgressionService,
    battle_progression_service,
)
from src.services.gym_leader_agent import gym_leader_agent_service

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

    def __init__(
        self,
        progression_service: Optional[BattleProgressionService] = None,
    ) -> None:
        # In-memory storage for active battle sessions
        # Maps unique battle_session_id to active match dictionaries
        self.active_battle_sessions: Dict[str, Dict] = {}
        # Progression service tracking party pools, +1% stat growth, and move unlocks
        self.progression_service: BattleProgressionService = (
            progression_service if progression_service is not None else BattleProgressionService()
        )

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
        Creates an authentic opponent combatant:
        - #95 Onix (Lv 8, Rock/Ground): Gym Leader Brock's signature monster with 3 moves
        - #121 Starmie (Lv 9, Water/Psychic): Gym Leader Misty's signature monster with 4 moves
        - #16 Pidgey (Lv 5, Normal/Flying): Wild opponent with 2 basic moves
        """
        if pokemon_id == 95:
            return ActiveBattleEntity(
                pokemon_id=95,
                pokemon_name="Onix",
                level=8,
                elemental_types=["rock", "ground"],
                current_health_points=24,
                maximum_health_points=24,
                attack_stat=11,
                defense_stat=18,
                speed_stat=11,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/95.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/95.gif",
                move_slots=[
                    PokemonMoveSlot(move_id=17, move_name="Rock Throw", elemental_type="rock", base_power=50, accuracy_percentage=90, current_power_points=15, maximum_power_points=15, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=18, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=19, move_name="Harden", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=30, maximum_power_points=30, is_unlocked=True, unlock_victory_threshold=0),
                ],
            )
        if pokemon_id == 121:
            return ActiveBattleEntity(
                pokemon_id=121,
                pokemon_name="Starmie",
                level=9,
                elemental_types=["water", "psychic"],
                current_health_points=25,
                maximum_health_points=25,
                attack_stat=13,
                defense_stat=14,
                speed_stat=16,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/121.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/121.gif",
                move_slots=[
                    PokemonMoveSlot(move_id=21, move_name="Water Gun", elemental_type="water", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=22, move_name="Swift", elemental_type="normal", base_power=60, accuracy_percentage=100, current_power_points=20, maximum_power_points=20, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=23, move_name="Psybeam", elemental_type="psychic", base_power=65, accuracy_percentage=100, current_power_points=20, maximum_power_points=20, is_unlocked=True, unlock_victory_threshold=0),
                    PokemonMoveSlot(move_id=24, move_name="Recover", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=10, maximum_power_points=10, is_unlocked=True, unlock_victory_threshold=0),
                ],
            )
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
        Integrates Lesson 6 progression state: loads the trainer's party pool, applies
        any accumulated +1% victory stat boosts and unlocked moves, and starts the 5-turn clock.
        """
        # Generate unique UUID string for tracking this battle instance
        session_id = str(uuid.uuid4())

        # Ensure trainer party pool is initialized and retrieve current progression state
        party_pool_state = self.progression_service.ensure_trainer_party_initialized(
            trainer_name=trainer_name,
            starter_pokemon_id=selected_pokemon_id,
        )
        normalized_trainer_key = trainer_name.strip().lower()
        trainer_roster = self.progression_service.trainer_party_rosters.get(
            normalized_trainer_key, {}
        )

        # Build player combat entity from progression record (or baseline starter fallback)
        if selected_pokemon_id in trainer_roster:
            player_entity = self.progression_service.convert_party_monster_to_battle_entity(
                party_monster=trainer_roster[selected_pokemon_id]
            )
        else:
            player_entity = self.create_starter_pokemon_entity(
                pokemon_id=selected_pokemon_id,
                trainer_name=trainer_name,
            )

        opponent_entity = self.create_wild_opponent_entity(
            pokemon_id=opponent_pokemon_id,
        )

        # Store session record in memory with 5-Turn Battle Clock and Party Pool metadata
        session_payload = {
            "battle_session_id": session_id,
            "trainer_name": trainer_name,
            "current_turn_number": 1,
            "maximum_turns_allowed": MAXIMUM_BATTLE_TURNS,
            "is_turn_limit_reached": False,
            "is_battle_concluded": False,
            "victorious_monster_name": None,
            "player_monster": player_entity,
            "opponent_monster": opponent_entity,
            "party_pool": party_pool_state.model_dump(),
            "progression_update": None,
            "combat_memory_log": [],
            "gym_leader_decision": None,
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
        1. Validates 5-turn match clock and player move, then decrements PP.
        2. Compares speed initiative to determine turn order.
        3. Executes first strike; knocks out defender if HP reaches 0.
        4. If defender survives, executes retaliation strike.
        5. Enforces 5-turn match limit, awards +1% stat growth & auto-recruit on KO,
           and returns structured response.
        """
        # Retrieve session state
        session_data = self.active_battle_sessions.get(battle_session_id)
        if not session_data:
            raise ValueError(f"Battle session '{battle_session_id}' not found.")

        if session_data["is_battle_concluded"]:
            raise ValueError("This battle has already concluded.")

        # Enforce strict 5-Turn Battle Clock before resolving action
        current_turn_number: int = session_data["current_turn_number"]
        maximum_turns_allowed: int = session_data.get("maximum_turns_allowed", MAXIMUM_BATTLE_TURNS)
        if current_turn_number > maximum_turns_allowed:
            raise ValueError(
                f"The {maximum_turns_allowed}-turn battle clock has expired."
            )

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

        # Lesson 9 Autonomous Gym Leader AI Agent: Perceive -> Remember -> Decide -> Act
        detected_multiplier: float = 1.0
        party_pool_dict = session_data.get("party_pool") or {}
        for party_member in party_pool_dict.get("party_monsters", []):
            if party_member.get("pokemon_id") == player_monster.pokemon_id:
                detected_multiplier = float(
                    party_member.get("stat_progression_multiplier", 1.0)
                )
                break

        combat_memory_log: List[str] = session_data.setdefault("combat_memory_log", [])
        agent_decision = gym_leader_agent_service.evaluate_turn_decision_sync(
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            calculate_effectiveness_fn=self.calculate_elemental_effectiveness,
            stat_progression_multiplier=detected_multiplier,
            combat_memory_log=combat_memory_log,
        )

        # Resolve the chosen opponent move slot from the agent's decision
        opponent_move = next(
            (
                move
                for move in opponent_monster.move_slots
                if move.move_id == agent_decision.selected_move_id
            ),
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

        # Check match conclusion (Knockout OR 5-Turn Battle Clock expiration)
        turn_number = session_data["current_turn_number"]
        is_knockout = (
            (player_monster.current_health_points == 0)
            or (opponent_monster.current_health_points == 0)
        )
        # If Turn 5 finishes and neither monster fainted, the 5-turn match clock expires
        is_turn_limit_reached = (not is_knockout) and (turn_number >= maximum_turns_allowed)
        is_concluded = is_knockout or is_turn_limit_reached

        victor_name: Optional[str] = None
        progression_update_payload: Optional[Dict] = None

        if opponent_monster.current_health_points == 0:
            victor_name = player_monster.pokemon_name
            # Player won by knockout within 5 turns: award +1% stat boost, check 10/20W move unlocks, and auto-recruit opponent
            progression_reward = self.progression_service.record_victory_and_auto_recruit(
                trainer_name=session_data["trainer_name"],
                victorious_pokemon_id=player_monster.pokemon_id,
                defeated_opponent_pokemon_id=opponent_monster.pokemon_id,
                defeated_opponent_name=opponent_monster.pokemon_name,
            )
            progression_update_payload = progression_reward.model_dump()
            session_data["party_pool"] = progression_reward.updated_party_pool.model_dump()
        elif player_monster.current_health_points == 0:
            victor_name = opponent_monster.pokemon_name

        # Increment turn number for subsequent rounds and record combat memory for Lesson 9 Agent
        combat_memory_log.append(
            f"Turn {turn_number}: {player_monster.pokemon_name} used {chosen_player_move.move_name}; "
            f"{opponent_monster.pokemon_name} chose {opponent_move.move_name} ({agent_decision.agent_mood.value})."
        )
        gym_leader_decision_payload = agent_decision.model_dump(mode="json")
        session_data["current_turn_number"] += 1
        session_data["is_turn_limit_reached"] = is_turn_limit_reached
        session_data["is_battle_concluded"] = is_concluded
        session_data["victorious_monster_name"] = victor_name
        session_data["progression_update"] = progression_update_payload
        session_data["gym_leader_decision"] = gym_leader_decision_payload

        return BattleTurnResolutionResponse(
            battle_session_id=battle_session_id,
            current_turn_number=turn_number,
            first_action_resolution=first_action,
            second_action_resolution=second_action,
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            is_battle_concluded=is_concluded,
            victorious_monster_name=victor_name,
            maximum_turns_allowed=maximum_turns_allowed,
            is_turn_limit_reached=is_turn_limit_reached,
            progression_update=progression_update_payload,
            gym_leader_decision=gym_leader_decision_payload,
        )


# Global singleton instance for injection across route handlers
battle_engine_service = BattleEngineService(progression_service=battle_progression_service)
