"""
Test Catch Roulette Module
Unit and integration tests for Lesson 7 Catch Pokémon Roulette Phase:
1. Exact calibrated capture probabilities for each Pokéball tier.
2. Deterministic cumulative distribution boundaries for tier selection.
3. Catch success and failure threshold evaluations.
4. Automatic party recruitment upon successful overtime capture.
5. Monte Carlo statistical distribution validation across 1,000 simulated spins.
6. FastAPI REST endpoint contract verification.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.schemas.catch_schema import CatchRouletteSpinRequest, PokeballTier
from src.services.catch_roulette_service import (
    CatchRouletteService,
    TIER_SPECIFICATIONS,
    catch_roulette_service,
)
from src.services.battle_progression_service import battle_progression_service


client = TestClient(app)


def test_pokeball_tier_calibrated_probabilities() -> None:
    """
    Verifies that all 4 Pokéball tiers map to their exact, calibrated capture rates.
    """
    assert CatchRouletteService.get_tier_capture_probability(PokeballTier.GOLD) == 0.90
    assert CatchRouletteService.get_tier_capture_probability(PokeballTier.SILVER) == 0.75
    assert CatchRouletteService.get_tier_capture_probability(PokeballTier.BRONZE) == 0.60
    assert CatchRouletteService.get_tier_capture_probability(PokeballTier.NORMAL) == 0.50


def test_deterministic_tier_selection_boundaries() -> None:
    """
    Verifies that the roulette wheel's cumulative probability boundaries land
    deterministically on the intended Pokéball tier:
    - [0.00, 0.10) -> GOLD
    - [0.10, 0.35) -> SILVER
    - [0.35, 0.70) -> BRONZE
    - [0.70, 1.00] -> NORMAL
    """
    # Gold segment: 0.00 to 0.099
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.00) == PokeballTier.GOLD
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.08) == PokeballTier.GOLD

    # Silver segment: 0.10 to 0.349
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.10) == PokeballTier.SILVER
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.25) == PokeballTier.SILVER

    # Bronze segment: 0.35 to 0.699
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.35) == PokeballTier.BRONZE
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.55) == PokeballTier.BRONZE

    # Normal segment: 0.70 to 1.00
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.70) == PokeballTier.NORMAL
    assert CatchRouletteService.select_pokeball_tier(injected_tier_roll=0.99) == PokeballTier.NORMAL


def test_deterministic_catch_evaluation_success_and_failure() -> None:
    """
    Validates that a catch attempt succeeds if and only if the catch roll is strictly
    below the tier's designated capture threshold.
    """
    # GOLD (90% threshold): roll 0.89 succeeds, roll 0.91 fails
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.GOLD,
        injected_catch_roll=0.89,
    ) is True
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.GOLD,
        injected_catch_roll=0.91,
    ) is False

    # SILVER (75% threshold): roll 0.74 succeeds, roll 0.76 fails
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.SILVER,
        injected_catch_roll=0.74,
    ) is True
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.SILVER,
        injected_catch_roll=0.76,
    ) is False

    # BRONZE (60% threshold): roll 0.59 succeeds, roll 0.61 fails
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.BRONZE,
        injected_catch_roll=0.59,
    ) is True
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.BRONZE,
        injected_catch_roll=0.61,
    ) is False

    # NORMAL (50% threshold): roll 0.49 succeeds, roll 0.51 fails
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.NORMAL,
        injected_catch_roll=0.49,
    ) is True
    assert CatchRouletteService.evaluate_catch_attempt(
        pokeball_tier=PokeballTier.NORMAL,
        injected_catch_roll=0.51,
    ) is False


def test_catch_roulette_successful_recruitment_updates_party_pool() -> None:
    """
    Verifies that a successful overtime capture:
    1. Sets capture_successful to True.
    2. Recruits the target species into the trainer's party pool.
    3. Returns the updated party pool state with total_party_count incremented.
    4. Generates the victorious 3-wobble announcer narration.
    """
    test_trainer_name = "RouletteTesterSuccess"
    # Ensure trainer party starts with Bulbasaur (#1)
    battle_progression_service.ensure_trainer_party_initialized(
        trainer_name=test_trainer_name,
        starter_pokemon_id=1,
    )

    spin_request = CatchRouletteSpinRequest(
        trainer_name=test_trainer_name,
        opponent_pokemon_id=16,  # Wild Pidgey
        opponent_pokemon_name="Pidgey",
        opponent_pokemon_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/16.png",
        opponent_level=5,
        injected_tier_roll=0.20,   # Lands on SILVER tier (0.10 - 0.35)
        injected_catch_roll=0.10,  # Below SILVER 0.75 -> Guaranteed Catch!
    )

    outcome = catch_roulette_service.execute_roulette_spin_and_catch(spin_request=spin_request)

    assert outcome.selected_pokeball_tier == PokeballTier.SILVER
    assert outcome.capture_probability == 0.75
    assert outcome.capture_successful is True
    assert "CLICK! ⭐ Gotcha!" in outcome.narrative_outcome
    assert outcome.updated_party_pool is not None
    assert outcome.updated_party_pool.total_party_count >= 2
    # Verify Pidgey (ID 16) is present in the party roster
    recruited_ids = [m.pokemon_id for m in outcome.updated_party_pool.party_monsters]
    assert 16 in recruited_ids


def test_catch_roulette_failure_narrative_and_no_recruitment() -> None:
    """
    Verifies that when a catch roll fails:
    1. Sets capture_successful to False.
    2. The monster is not added to the party roster.
    3. The narrative announces the monster broke free.
    """
    test_trainer_name = "RouletteTesterFail"
    # Ensure trainer party starts with Squirtle (#7)
    battle_progression_service.ensure_trainer_party_initialized(
        trainer_name=test_trainer_name,
        starter_pokemon_id=7,
    )

    spin_request = CatchRouletteSpinRequest(
        trainer_name=test_trainer_name,
        opponent_pokemon_id=25,  # Wild Pikachu
        opponent_pokemon_name="Pikachu",
        opponent_pokemon_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
        opponent_level=5,
        injected_tier_roll=0.85,   # Lands on NORMAL tier (0.70 - 1.00)
        injected_catch_roll=0.95,  # Far above NORMAL 0.50 -> Break Free!
    )

    outcome = catch_roulette_service.execute_roulette_spin_and_catch(spin_request=spin_request)

    assert outcome.selected_pokeball_tier == PokeballTier.NORMAL
    assert outcome.capture_probability == 0.50
    assert outcome.capture_successful is False
    assert "BURST! 💨 Oh no!" in outcome.narrative_outcome
    # Pikachu should NOT have been recruited
    party_state = battle_progression_service.get_trainer_party_pool_state(trainer_name=test_trainer_name)
    recruited_ids = [m.pokemon_id for m in party_state.party_monsters]
    assert 25 not in recruited_ids


def test_statistical_distribution_simulation() -> None:
    """
    Monte Carlo simulation running 1,000 unseeded random spins to statistically validate:
    1. All 4 tiers are generated by the wheel.
    2. Gold tier occurs around ~10% (tolerating [5%, 16%]).
    3. Silver tier occurs around ~25% (tolerating [18%, 32%]).
    4. Bronze tier occurs around ~35% (tolerating [27%, 43%]).
    5. Normal tier occurs around ~30% (tolerating [22%, 38%]).
    """
    simulation_counts = {
        PokeballTier.GOLD: 0,
        PokeballTier.SILVER: 0,
        PokeballTier.BRONZE: 0,
        PokeballTier.NORMAL: 0,
    }

    sample_size = 1000
    for _ in range(sample_size):
        selected_tier = CatchRouletteService.select_pokeball_tier()
        simulation_counts[selected_tier] += 1

    # Verify every tier was reached at least once
    for tier, count in simulation_counts.items():
        assert count > 0, f"Tier {tier} was never selected in {sample_size} spins!"

    # Verify statistical percentage tolerances
    gold_pct = simulation_counts[PokeballTier.GOLD] / sample_size
    silver_pct = simulation_counts[PokeballTier.SILVER] / sample_size
    bronze_pct = simulation_counts[PokeballTier.BRONZE] / sample_size
    normal_pct = simulation_counts[PokeballTier.NORMAL] / sample_size

    assert 0.05 <= gold_pct <= 0.16, f"Gold distribution {gold_pct:.3f} outside expected [0.05, 0.16]"
    assert 0.18 <= silver_pct <= 0.32, f"Silver distribution {silver_pct:.3f} outside expected [0.18, 0.32]"
    assert 0.27 <= bronze_pct <= 0.43, f"Bronze distribution {bronze_pct:.3f} outside expected [0.27, 0.43]"
    assert 0.22 <= normal_pct <= 0.38, f"Normal distribution {normal_pct:.3f} outside expected [0.22, 0.38]"


def test_fastapi_roulette_endpoint() -> None:
    """
    Verifies that POST /api/v1/battle/catch/roulette successfully accepts requests,
    executes the spin, and returns the CatchRouletteOutcome data envelope.
    """
    request_payload = {
        "trainer_name": "EndpointTesterTrainer",
        "opponent_pokemon_id": 16,
        "opponent_pokemon_name": "Pidgey",
        "opponent_pokemon_sprite_url": "https://example.com/pidgey.png",
        "opponent_level": 5,
        "injected_tier_roll": 0.05,   # Forces GOLD
        "injected_catch_roll": 0.05,  # Forces guaranteed catch
    }

    http_response = client.post("/api/v1/battle/catch/roulette", json=request_payload)
    assert http_response.status_code == 200

    json_data = http_response.json()
    assert json_data["selected_pokeball_tier"] == "GOLD"
    assert json_data["capture_probability"] == 0.90
    assert json_data["capture_successful"] is True
    assert json_data["captured_monster_name"] == "Pidgey"
    assert "CLICK! ⭐ Gotcha!" in json_data["narrative_outcome"]
    assert json_data["updated_party_pool"] is not None
