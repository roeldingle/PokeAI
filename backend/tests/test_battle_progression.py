"""
Battle Progression Unit Test Suite (Lesson 6)
Verifies:
1. Strict 5-Turn Battle Clock enforcement (`turn_counter <= 5` and Turn 5 expiration).
2. Pre-Turn 1 TEAM party swap validation (disabled with 1 monster; rejected after Turn 1 starts).
3. +1% incremental stat progression formula:
   effective_stat = round(base_stat * (1.0 + victories_count * 0.01))
4. Exact move slot unlock milestones at 10 victories (Move Slot 3) and 20 victories (Move Slot 4).
5. Automatic opponent recruitment into the trainer's party pool upon knockout within 5 turns.
"""

import pytest
from src.services.battle_engine import BattleEngineService
from src.services.battle_progression_service import (
    MAXIMUM_BATTLE_TURNS,
    BattleProgressionService,
)


@pytest.fixture
def isolated_progression_service() -> BattleProgressionService:
    """
    Provides a clean, isolated BattleProgressionService instance for each test.
    """
    return BattleProgressionService()


@pytest.fixture
def isolated_battle_engine(
    isolated_progression_service: BattleProgressionService,
) -> BattleEngineService:
    """
    Provides an isolated BattleEngineService wired to the isolated progression service.
    """
    return BattleEngineService(progression_service=isolated_progression_service)


def test_five_turn_battle_clock_enforces_expiration(
    isolated_battle_engine: BattleEngineService,
) -> None:
    """
    Verifies that a battle lasts a maximum of 5 turns. If neither monster is knocked out
    by the end of Turn 5, the match concludes with is_turn_limit_reached=True.
    """
    session_data = isolated_battle_engine.initialize_battle_session(
        trainer_name="ShaneilTrainer",
        selected_pokemon_id=4,  # Charmander
        opponent_pokemon_id=16,  # Pidgey
    )
    battle_session_id = session_data["battle_session_id"]

    # Boost player HP so Pidgey's Tackle cannot knock out Charmander across 5 turns
    session_data["player_monster"].current_health_points = 100
    session_data["player_monster"].maximum_health_points = 100

    # Execute Turns 1 through 4 using Growl (move_id=2, 0 base power so Pidgey never faints)
    for expected_turn_index in range(1, MAXIMUM_BATTLE_TURNS):
        turn_resolution = isolated_battle_engine.resolve_combat_round(
            battle_session_id=battle_session_id,
            selected_move_id=2,  # Growl (status move, 0 damage)
            deterministic_mode=True,
        )
        assert turn_resolution.current_turn_number == expected_turn_index
        assert turn_resolution.is_battle_concluded is False
        assert turn_resolution.is_turn_limit_reached is False

    # Execute Turn 5 (the final turn on the 5-turn match clock)
    turn_five_resolution = isolated_battle_engine.resolve_combat_round(
        battle_session_id=battle_session_id,
        selected_move_id=2,  # Growl
        deterministic_mode=True,
    )
    assert turn_five_resolution.current_turn_number == MAXIMUM_BATTLE_TURNS
    assert turn_five_resolution.is_turn_limit_reached is True
    assert turn_five_resolution.is_battle_concluded is True
    assert turn_five_resolution.victorious_monster_name is None

    # Attempting a 6th turn must raise a validation error
    with pytest.raises(ValueError, match="already concluded"):
        isolated_battle_engine.resolve_combat_round(
            battle_session_id=battle_session_id,
            selected_move_id=2,
            deterministic_mode=True,
        )


def test_team_swap_disabled_when_party_has_one_monster(
    isolated_battle_engine: BattleEngineService,
    isolated_progression_service: BattleProgressionService,
) -> None:
    """
    Verifies that when a trainer owns only 1 monster, is_team_swap_enabled is False
    and attempting to swap raises a ValueError.
    """
    session_data = isolated_battle_engine.initialize_battle_session(
        trainer_name="SoloTrainer",
        selected_pokemon_id=4,
    )

    party_state = isolated_progression_service.get_trainer_party_pool_state(
        trainer_name="SoloTrainer"
    )
    assert party_state.total_party_count == 1
    assert party_state.is_team_swap_enabled is False

    with pytest.raises(ValueError, match="only has 1 monster"):
        isolated_progression_service.execute_pre_turn_team_swap(
            battle_session=session_data,
            target_pokemon_id=4,
        )


def test_pre_turn_one_team_swap_succeeds_and_post_turn_one_swap_rejected(
    isolated_battle_engine: BattleEngineService,
    isolated_progression_service: BattleProgressionService,
) -> None:
    """
    Verifies that swapping active monsters is permitted before Turn 1 when the trainer
    owns 2+ monsters, and strictly rejected once Turn 1 has been resolved.
    """
    session_data = isolated_battle_engine.initialize_battle_session(
        trainer_name="DuoTrainer",
        selected_pokemon_id=4,  # Charmander
    )
    battle_session_id = session_data["battle_session_id"]

    # Recruit Pidgey (#16) into DuoTrainer's party pool
    isolated_progression_service.recruit_monster_into_party(
        trainer_name="DuoTrainer",
        recruited_pokemon_id=16,
    )

    party_state = isolated_progression_service.get_trainer_party_pool_state(
        trainer_name="DuoTrainer"
    )
    assert party_state.total_party_count == 2
    assert party_state.is_team_swap_enabled is True

    # Swap from Charmander (#4) to Pidgey (#16) before Turn 1 begins
    swap_result = isolated_progression_service.execute_pre_turn_team_swap(
        battle_session=session_data,
        target_pokemon_id=16,
    )
    assert swap_result.previous_pokemon_name == "Charmander"
    assert swap_result.new_active_monster.pokemon_name == "Pidgey"
    assert session_data["player_monster"].pokemon_id == 16

    # Resolve Turn 1 with Pidgey's Tackle (move_id=13)
    isolated_battle_engine.resolve_combat_round(
        battle_session_id=battle_session_id,
        selected_move_id=13,
        deterministic_mode=True,
    )

    # Attempting to swap after Turn 1 has resolved must raise a ValueError
    with pytest.raises(ValueError, match="before Turn 1 begins"):
        isolated_progression_service.execute_pre_turn_team_swap(
            battle_session=session_data,
            target_pokemon_id=4,
        )


def test_incremental_one_percent_stat_progression_formula(
    isolated_progression_service: BattleProgressionService,
) -> None:
    """
    Verifies the Lesson 6 mathematical progression formula:
    effective_stat = round(base_stat * (1.0 + victories_count * 0.01))
    """
    charmander_template = isolated_progression_service.build_baseline_species_template(
        pokemon_id=4
    )
    assert charmander_template.base_health_points == 20
    assert charmander_template.base_attack_stat == 12
    assert charmander_template.base_defense_stat == 10
    assert charmander_template.base_speed_stat == 14

    # At 10 victories (+10% multiplier = 1.10)
    charmander_at_10_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=10,
    )
    assert charmander_at_10_wins.stat_progression_multiplier == 1.10
    assert charmander_at_10_wins.effective_health_points == round(20 * 1.10)  # 22
    assert charmander_at_10_wins.effective_attack_stat == round(12 * 1.10)    # 13
    assert charmander_at_10_wins.effective_defense_stat == round(10 * 1.10)   # 11
    assert charmander_at_10_wins.effective_speed_stat == round(14 * 1.10)     # 15

    # At 20 victories (+20% multiplier = 1.20)
    charmander_at_20_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=20,
    )
    assert charmander_at_20_wins.stat_progression_multiplier == 1.20
    assert charmander_at_20_wins.effective_health_points == round(20 * 1.20)  # 24
    assert charmander_at_20_wins.effective_attack_stat == round(12 * 1.20)    # 14
    assert charmander_at_20_wins.effective_defense_stat == round(10 * 1.20)   # 12
    assert charmander_at_20_wins.effective_speed_stat == round(14 * 1.20)     # 17


def test_move_slot_unlock_milestones_at_ten_and_twenty_victories(
    isolated_progression_service: BattleProgressionService,
) -> None:
    """
    Verifies that Move Slot 3 unlocks at exactly 10 victories and Move Slot 4
    unlocks at exactly 20 victories.
    """
    charmander_template = isolated_progression_service.build_baseline_species_template(
        pokemon_id=4
    )

    # At 9 victories: Slots 1 & 2 unlocked, Slots 3 & 4 locked
    charmander_9_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=9,
    )
    assert charmander_9_wins.move_slots[0].is_unlocked is True
    assert charmander_9_wins.move_slots[1].is_unlocked is True
    assert charmander_9_wins.move_slots[2].is_unlocked is False  # Ember locked at 9W
    assert charmander_9_wins.move_slots[3].is_unlocked is False  # Flamethrower locked at 9W

    # At exactly 10 victories: Move Slot 3 (Ember) unlocks!
    charmander_10_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=10,
    )
    assert charmander_10_wins.move_slots[2].move_name == "Ember"
    assert charmander_10_wins.move_slots[2].is_unlocked is True
    assert charmander_10_wins.move_slots[3].is_unlocked is False

    # At 19 victories: Move Slot 4 (Flamethrower) still locked
    charmander_19_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=19,
    )
    assert charmander_19_wins.move_slots[2].is_unlocked is True
    assert charmander_19_wins.move_slots[3].is_unlocked is False

    # At exactly 20 victories: Move Slot 4 (Flamethrower) unlocks!
    charmander_20_wins = isolated_progression_service.apply_victory_count_to_monster(
        party_monster=charmander_template,
        new_victories_count=20,
    )
    assert charmander_20_wins.move_slots[3].move_name == "Flamethrower"
    assert charmander_20_wins.move_slots[3].is_unlocked is True


def test_knockout_auto_recruits_opponent_and_increments_victory_stats(
    isolated_battle_engine: BattleEngineService,
    isolated_progression_service: BattleProgressionService,
) -> None:
    """
    Verifies that knocking out an opponent within 5 turns automatically recruits
    that opponent into the trainer's party pool and increments the winner's victory count.
    """
    session_data = isolated_battle_engine.initialize_battle_session(
        trainer_name="ChampionRed",
        selected_pokemon_id=4,  # Charmander
        opponent_pokemon_id=16,  # Pidgey
    )
    battle_session_id = session_data["battle_session_id"]

    # Set opponent HP to 1 so Charmander's Scratch knocks out Pidgey on Turn 1
    session_data["opponent_monster"].current_health_points = 1

    resolution = isolated_battle_engine.resolve_combat_round(
        battle_session_id=battle_session_id,
        selected_move_id=1,  # Scratch
        deterministic_mode=True,
    )

    assert resolution.is_battle_concluded is True
    assert resolution.victorious_monster_name == "Charmander"
    assert resolution.progression_update is not None
    assert resolution.progression_update["updated_victories_count"] == 1
    assert resolution.progression_update["stat_progression_multiplier"] == 1.01
    assert resolution.progression_update["was_opponent_auto_recruited"] is True
    assert resolution.progression_update["recruited_opponent_pokemon_name"] == "Pidgey"

    # Verify Pidgey is now in ChampionRed's party pool and TEAM swap is enabled for the next match
    updated_pool = isolated_progression_service.get_trainer_party_pool_state(
        trainer_name="ChampionRed"
    )
    assert updated_pool.total_party_count == 2
    assert updated_pool.is_team_swap_enabled is True
    recruited_ids = [monster.pokemon_id for monster in updated_pool.party_monsters]
    assert 4 in recruited_ids
    assert 16 in recruited_ids
