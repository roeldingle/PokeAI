"""
Battle Engine Unit Test Suite
Verifies the deterministic damage arithmetic, 18-type elemental advantage matrices,
PP decrementation, turn initiative ordering, and knockout handling.
"""

import pytest
from src.services.battle_engine import BattleEngineService
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot


@pytest.fixture
def test_battle_engine() -> BattleEngineService:
    """
    Test fixture providing an isolated instance of the BattleEngineService.
    """
    return BattleEngineService()


def test_elemental_type_effectiveness_calculations(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies that type advantage multipliers calculate with 100% mathematical precision.
    """
    # Fire vs Grass is Super Effective (2.0x)
    fire_vs_grass_multiplier = test_battle_engine.calculate_elemental_effectiveness(
        attacking_move_elemental_type="fire",
        defending_pokemon_elemental_types=["grass"],
    )
    assert fire_vs_grass_multiplier == 2.0

    # Water vs Fire is Super Effective (2.0x)
    water_vs_fire_multiplier = test_battle_engine.calculate_elemental_effectiveness(
        attacking_move_elemental_type="water",
        defending_pokemon_elemental_types=["fire"],
    )
    assert water_vs_fire_multiplier == 2.0

    # Fire vs Water is Not Very Effective (0.5x)
    fire_vs_water_multiplier = test_battle_engine.calculate_elemental_effectiveness(
        attacking_move_elemental_type="fire",
        defending_pokemon_elemental_types=["water"],
    )
    assert fire_vs_water_multiplier == 0.5

    # Electric vs Ground is Completely Immune (0.0x)
    electric_vs_ground_multiplier = test_battle_engine.calculate_elemental_effectiveness(
        attacking_move_elemental_type="electric",
        defending_pokemon_elemental_types=["ground"],
    )
    assert electric_vs_ground_multiplier == 0.0

    # Dual-typing advantage: Grass attack against Water/Ground target (2.0 * 2.0 = 4.0x)
    grass_vs_water_ground_multiplier = test_battle_engine.calculate_elemental_effectiveness(
        attacking_move_elemental_type="grass",
        defending_pokemon_elemental_types=["water", "ground"],
    )
    assert grass_vs_water_ground_multiplier == 4.0


def test_deterministic_damage_formula(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies that the Gen-1 inspired damage arithmetic is deterministic and bounds correctly.
    """
    attacker_charmander = ActiveBattleEntity(
        pokemon_id=4,
        pokemon_name="Charmander",
        level=6,
        elemental_types=["fire"],
        current_health_points=20,
        maximum_health_points=20,
        attack_stat=12,
        defense_stat=10,
        speed_stat=14,
        sprite_front_url="",
        sprite_back_url="",
        move_slots=[],
    )

    defender_pidgey = ActiveBattleEntity(
        pokemon_id=16,
        pokemon_name="Pidgey",
        level=5,
        elemental_types=["normal", "flying"],
        current_health_points=18,
        maximum_health_points=18,
        attack_stat=10,
        defense_stat=9,
        speed_stat=12,
        sprite_front_url="",
        sprite_back_url="",
        move_slots=[],
    )

    scratch_move = PokemonMoveSlot(
        move_id=1,
        move_name="Scratch",
        elemental_type="normal",
        base_power=40,
        accuracy_percentage=100,
        current_power_points=35,
        maximum_power_points=35,
        is_unlocked=True,
    )

    calculated_damage, type_multiplier, is_critical = test_battle_engine.calculate_damage_output(
        attacker_entity=attacker_charmander,
        defender_entity=defender_pidgey,
        move_to_execute=scratch_move,
        enforce_deterministic_variance=True,
    )

    # Scratch is Normal type vs Normal/Flying, which is neutral (1.0x)
    assert type_multiplier == 1.0
    # Damage must be strictly positive
    assert calculated_damage >= 5
    assert is_critical is False


def test_battle_session_initialization(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies that a new battle session initializes with 4 move slots, correct unlock thresholds,
    and valid combatant HP.
    """
    session_data = test_battle_engine.initialize_battle_session(
        trainer_name="Ash",
        selected_pokemon_id=4,  # Charmander
        opponent_pokemon_id=16,  # Pidgey
    )

    assert "battle_session_id" in session_data
    player_monster: ActiveBattleEntity = session_data["player_monster"]
    assert player_monster.pokemon_name == "Charmander"
    assert player_monster.current_health_points == 20
    assert len(player_monster.move_slots) == 4

    # Slot 1 and Slot 2 must be unlocked
    assert player_monster.move_slots[0].is_unlocked is True
    assert player_monster.move_slots[1].is_unlocked is True

    # Slot 3 (Ember) and Slot 4 (Flamethrower) must be locked behind 10 and 20 wins
    assert player_monster.move_slots[2].is_unlocked is False
    assert player_monster.move_slots[2].unlock_victory_threshold == 10
    assert player_monster.move_slots[3].is_unlocked is False
    assert player_monster.move_slots[3].unlock_victory_threshold == 20


def test_turn_resolution_speed_initiative_and_pp_decrement(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies turn execution: Charmander (Speed 14) outspeeds Pidgey (Speed 12)
    and PP correctly decrements on use.
    """
    session_data = test_battle_engine.initialize_battle_session(
        trainer_name="Ash",
        selected_pokemon_id=4,
    )
    session_id = session_data["battle_session_id"]

    initial_scratch_pp = session_data["player_monster"].move_slots[0].current_power_points

    resolution = test_battle_engine.resolve_combat_round(
        battle_session_id=session_id,
        selected_move_id=1,  # Scratch
        deterministic_mode=True,
    )

    # Charmander has Speed 14 vs Pidgey Speed 12 -> Charmander must strike first
    assert resolution.first_action_resolution.attacker_name == "Charmander"
    # Player's Scratch PP decremented by 1
    assert resolution.player_monster.move_slots[0].current_power_points == initial_scratch_pp - 1
    # Defender Pidgey HP was reduced
    assert resolution.opponent_monster.current_health_points < resolution.opponent_monster.maximum_health_points


def test_locked_move_raises_validation_error(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies that selecting a locked move slot (e.g. Ember at 0 wins) is strictly rejected.
    """
    session_data = test_battle_engine.initialize_battle_session(
        trainer_name="Ash",
        selected_pokemon_id=4,
    )
    session_id = session_data["battle_session_id"]

    with pytest.raises(ValueError, match="locked behind 10 wins"):
        test_battle_engine.resolve_combat_round(
            battle_session_id=session_id,
            selected_move_id=3,  # Ember (locked)
        )


def test_knockout_resolution_prevents_retaliation(test_battle_engine: BattleEngineService) -> None:
    """
    Verifies that if the first attacker reduces defender HP to 0,
    the defender does NOT get to retaliate in the same turn.
    """
    session_data = test_battle_engine.initialize_battle_session(
        trainer_name="Ash",
        selected_pokemon_id=4,
    )
    session_id = session_data["battle_session_id"]

    # Manually reduce opponent HP to 1 so the next attack knocks them out
    session_data["opponent_monster"].current_health_points = 1

    resolution = test_battle_engine.resolve_combat_round(
        battle_session_id=session_id,
        selected_move_id=1,  # Scratch
        deterministic_mode=True,
    )

    # Opponent should be at 0 HP
    assert resolution.opponent_monster.current_health_points == 0
    # Match is concluded
    assert resolution.is_battle_concluded is True
    assert resolution.victorious_monster_name == "Charmander"
    # Second action must be None because defender was knocked out
    assert resolution.second_action_resolution is None
