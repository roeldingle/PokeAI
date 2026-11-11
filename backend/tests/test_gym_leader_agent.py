"""
Test Gym Leader Agent Module
Unit and integration tests for Lesson 9 Autonomous Gym Leader AI Agent:
1. Persona mapping for Gym Leader Brock (#95 Onix), Misty (#121 Starmie), and Wild Instinct (#16 Pidgey).
2. Dynamic threat calibration scaling upward with the player's +1% stat_progression_multiplier.
3. Desperate Clutch mood activation and >90% optimal move selection under low HP (<= 30%).
4. Immunity avoidance (never selecting 0.0x moves when damaging alternatives exist).
5. Integration with BattleEngineService.resolve_combat_round and combat memory persistence.
6. FastAPI POST /api/v1/battle/gym-leader/decide endpoint verification.
"""

from fastapi.testclient import TestClient
from src.main import app
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot
from src.schemas.gym_leader_schema import AgentMoodState, GymLeaderPersona
from src.services.battle_engine import battle_engine_service
from src.services.gym_leader_agent import gym_leader_agent_service


client = TestClient(app)


def test_persona_resolution_for_brock_misty_and_wild_instinct() -> None:
    """
    Verifies that opponent species IDs map deterministically to their canonical personas.
    """
    assert gym_leader_agent_service.resolve_persona_for_opponent(95) == GymLeaderPersona.BROCK
    assert gym_leader_agent_service.resolve_persona_for_opponent(121) == GymLeaderPersona.MISTY
    assert gym_leader_agent_service.resolve_persona_for_opponent(16) == GymLeaderPersona.WILD_INSTINCT


def test_dynamic_threat_calibration_scales_with_player_victory_stat_multiplier() -> None:
    """
    Verifies that as the player's +1% victory stat_progression_multiplier increases
    (e.g., from 1.00x at 0 wins to 1.15x at 15 wins), the Gym Leader AI's perceived
    calibrated_threat_score increases and its taunt acknowledges the scaled threat.
    """
    player_charmander = battle_engine_service.create_starter_pokemon_entity(
        pokemon_id=4,
        trainer_name="ThreatScalerTrainer",
    )
    opponent_pidgey = battle_engine_service.create_wild_opponent_entity(pokemon_id=16)

    # Decision at baseline 1.00x multiplier (0 victories)
    baseline_decision = gym_leader_agent_service.evaluate_turn_decision_sync(
        player_monster=player_charmander,
        opponent_monster=opponent_pidgey,
        calculate_effectiveness_fn=battle_engine_service.calculate_elemental_effectiveness,
        stat_progression_multiplier=1.00,
        gym_leader_persona=GymLeaderPersona.BROCK,
    )

    # Decision at scaled 1.15x multiplier (15 victories -> +15% stats)
    scaled_decision = gym_leader_agent_service.evaluate_turn_decision_sync(
        player_monster=player_charmander,
        opponent_monster=opponent_pidgey,
        calculate_effectiveness_fn=battle_engine_service.calculate_elemental_effectiveness,
        stat_progression_multiplier=1.15,
        gym_leader_persona=GymLeaderPersona.BROCK,
    )

    assert scaled_decision.calibrated_threat_score > baseline_decision.calibrated_threat_score
    assert scaled_decision.detected_player_stat_multiplier == 1.15
    assert scaled_decision.agent_mood == AgentMoodState.AGGRESSIVE
    assert "+15% victory stat boost" in scaled_decision.in_character_dialogue_taunt


def test_desperate_clutch_mood_and_optimal_move_selection_under_low_hp() -> None:
    """
    Verifies that when Gym Leader Brock's Onix drops to <= 30% HP against Charmander (Fire),
    the agent transitions into DESPERATE_CLUTCH mood and selects its 2x super-effective
    Rock Throw move (100% optimal across benchmark runs).
    """
    player_charmander = battle_engine_service.create_starter_pokemon_entity(
        pokemon_id=4,
        trainer_name="ClutchTester",
    )
    brock_onix = battle_engine_service.create_wild_opponent_entity(pokemon_id=95)
    # Reduce Onix HP to 5 / 24 (~20.8% HP -> <= 30% low-HP threshold)
    brock_onix.current_health_points = 5

    optimal_selections = 0
    total_trials = 10
    for _ in range(total_trials):
        decision = gym_leader_agent_service.evaluate_turn_decision_sync(
            player_monster=player_charmander,
            opponent_monster=brock_onix,
            calculate_effectiveness_fn=battle_engine_service.calculate_elemental_effectiveness,
            stat_progression_multiplier=1.05,
        )
        assert decision.agent_mood == AgentMoodState.DESPERATE_CLUTCH
        assert decision.calibrated_threat_score >= 8.5
        if decision.selected_move_name == "Rock Throw":
            optimal_selections += 1

    # Benchmark gate: must achieve > 90% optimal move selection under low HP
    assert (optimal_selections / total_trials) >= 0.90


def test_agent_avoids_zero_multiplier_immune_moves() -> None:
    """
    Verifies that when an opponent has a move that deals 0x damage due to elemental immunity
    (e.g., Electric move vs Rock/Ground Onix), the agent avoids the immune move and chooses
    a damaging alternative.
    """
    defender_onix = battle_engine_service.create_wild_opponent_entity(pokemon_id=95)
    attacker_raichu = ActiveBattleEntity(
        pokemon_id=26,
        pokemon_name="Raichu",
        level=8,
        elemental_types=["electric"],
        current_health_points=22,
        maximum_health_points=22,
        attack_stat=14,
        defense_stat=11,
        speed_stat=16,
        sprite_front_url="",
        sprite_back_url="",
        move_slots=[
            PokemonMoveSlot(
                move_id=90,
                move_name="Thunderbolt",
                elemental_type="electric",
                base_power=90,
                accuracy_percentage=100,
                current_power_points=15,
                maximum_power_points=15,
                is_unlocked=True,
            ),
            PokemonMoveSlot(
                move_id=91,
                move_name="Iron Tail",
                elemental_type="steel",
                base_power=75,
                accuracy_percentage=100,
                current_power_points=15,
                maximum_power_points=15,
                is_unlocked=True,
            ),
        ],
    )

    decision = gym_leader_agent_service.evaluate_turn_decision_sync(
        player_monster=defender_onix,
        opponent_monster=attacker_raichu,
        calculate_effectiveness_fn=battle_engine_service.calculate_elemental_effectiveness,
    )

    # Must avoid Thunderbolt (0x vs Ground) and choose Iron Tail (2x vs Rock)
    assert decision.selected_move_name == "Iron Tail"
    assert decision.selected_move_id == 91


def test_battle_engine_integrates_autonomous_gym_leader_decision_and_combat_memory() -> None:
    """
    Verifies that BattleEngineService.resolve_combat_round executes the Lesson 9
    Autonomous Gym Leader AI loop and attaches gym_leader_decision telemetry.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="MistyChallenger",
        selected_pokemon_id=4,   # Charmander (Fire)
        opponent_pokemon_id=121, # Gym Leader Misty's Starmie (Water/Psychic)
    )
    battle_session_id = session_state["battle_session_id"]

    resolution = battle_engine_service.resolve_combat_round(
        battle_session_id=battle_session_id,
        selected_move_id=1,  # Scratch
        deterministic_mode=True,
    )

    assert resolution.gym_leader_decision is not None
    assert resolution.gym_leader_decision["gym_leader_persona"] == "MISTY"
    # Water Gun (40 * 2.0 = 80 expected score) outscores Psybeam (65 * 1.0 = 65) against Fire-type Charmander
    assert resolution.gym_leader_decision["selected_move_name"] == "Water Gun"
    assert len(session_state["combat_memory_log"]) == 1


def test_fastapi_gym_leader_decide_endpoint() -> None:
    """
    Verifies that POST /api/v1/battle/gym-leader/decide returns a valid
    GymLeaderTurnDecision payload for an active Brock battle session.
    """
    init_response = client.post(
        "/api/v1/battle/initiate",
        json={
            "trainer_name": "BrockChallenger",
            "selected_pokemon_id": 4,   # Charmander
            "opponent_pokemon_id": 95,  # Brock's Onix
        },
    )
    assert init_response.status_code == 201
    battle_session_id = init_response.json()["battle_session"]["battle_session_id"]

    decide_response = client.post(
        "/api/v1/battle/gym-leader/decide",
        json={
            "battle_session_id": battle_session_id,
            "use_llm_gateway": False,
        },
    )
    assert decide_response.status_code == 200
    payload = decide_response.json()

    assert payload["gym_leader_persona"] == "BROCK"
    assert payload["selected_move_name"] == "Rock Throw"
    assert payload["calibrated_threat_score"] >= 1.0
    assert "Brock:" in payload["in_character_dialogue_taunt"]

    # Verify 404 for unknown battle session
    missing_response = client.post(
        "/api/v1/battle/gym-leader/decide",
        json={"battle_session_id": "unknown-session-id"},
    )
    assert missing_response.status_code == 404
