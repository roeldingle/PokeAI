"""
Test Coach RAG Module
Unit and integration tests for Lesson 8 'ASK GUIDE' Tactical Battle Whisperer:
1. Super-effective counter-move recommendation against known elemental weaknesses.
2. Strict enforcement of locked move slots (10W / 20W) and preference for damaging moves over status moves.
3. Skipping moves with 0 Power Points (PP) remaining.
4. ChromaDB vector lore retrieval and canonical tactical archive fallback.
5. End-to-end CoachRAGService pipeline verification.
6. FastAPI POST /api/v1/battle/coach and GET /api/v1/battle/coach/{session_id} endpoints.
"""

import asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot
from src.services.battle_engine import battle_engine_service
from src.services.coach_rag_service import coach_rag_service


client = TestClient(app)


def test_coach_recommends_super_effective_move_against_known_weakness() -> None:
    """
    Verifies that when a monster has a super-effective move unlocked (e.g., Fire move Ember
    against a Grass/Poison Bulbasaur), the Coach selects Ember with high confidence (>= 0.95).
    """
    # Create Charmander with Slot 3 (Ember - Fire, Power 40) unlocked
    player_charmander = ActiveBattleEntity(
        pokemon_id=4,
        pokemon_name="Charmander",
        level=8,
        elemental_types=["fire"],
        current_health_points=24,
        maximum_health_points=24,
        attack_stat=14,
        defense_stat=11,
        speed_stat=16,
        sprite_front_url="https://example.com/charmander_front.gif",
        sprite_back_url="https://example.com/charmander_back.gif",
        move_slots=[
            PokemonMoveSlot(
                move_id=1,
                move_name="Scratch",
                elemental_type="normal",
                base_power=40,
                accuracy_percentage=100,
                current_power_points=35,
                maximum_power_points=35,
                is_unlocked=True,
                unlock_victory_threshold=0,
            ),
            PokemonMoveSlot(
                move_id=2,
                move_name="Growl",
                elemental_type="normal",
                base_power=0,
                accuracy_percentage=100,
                current_power_points=40,
                maximum_power_points=40,
                is_unlocked=True,
                unlock_victory_threshold=0,
            ),
            PokemonMoveSlot(
                move_id=3,
                move_name="Ember",
                elemental_type="fire",
                base_power=40,
                accuracy_percentage=100,
                current_power_points=25,
                maximum_power_points=25,
                is_unlocked=True,
                unlock_victory_threshold=10,
            ),
        ],
    )

    # Create Grass/Poison opponent Bulbasaur (2x weak to Fire)
    opponent_bulbasaur = ActiveBattleEntity(
        pokemon_id=1,
        pokemon_name="Bulbasaur",
        level=6,
        elemental_types=["grass", "poison"],
        current_health_points=21,
        maximum_health_points=21,
        attack_stat=11,
        defense_stat=11,
        speed_stat=11,
        sprite_front_url="https://example.com/bulbasaur_front.gif",
        sprite_back_url="https://example.com/bulbasaur_back.gif",
        move_slots=[],
    )

    optimal_move, confidence_rating, matchup_summary = (
        coach_rag_service.evaluate_optimal_unlocked_move(
            player_monster=player_charmander,
            opponent_monster=opponent_bulbasaur,
        )
    )

    assert optimal_move.move_name == "Ember"
    assert optimal_move.move_id == 3
    assert confidence_rating >= 0.95
    assert "Super Effective 2x" in matchup_summary


def test_coach_respects_locked_move_slots_and_prefers_damaging_move() -> None:
    """
    Verifies that at 0 victories (when Ember and Flamethrower are locked),
    the Coach never recommends a locked move and prioritizes Scratch (Power 40)
    over the 0-power status move Growl.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="Lesson8ZeroWinsTrainer",
        selected_pokemon_id=4,  # Charmander with 0 wins
        opponent_pokemon_id=16,  # Pidgey
    )

    player_monster: ActiveBattleEntity = session_state["player_monster"]
    opponent_monster: ActiveBattleEntity = session_state["opponent_monster"]

    optimal_move, confidence_rating, matchup_summary = (
        coach_rag_service.evaluate_optimal_unlocked_move(
            player_monster=player_monster,
            opponent_monster=opponent_monster,
        )
    )

    assert optimal_move.move_name == "Scratch"
    assert optimal_move.is_unlocked is True
    assert confidence_rating >= 0.85
    assert "Ember" not in matchup_summary
    assert "Flamethrower" not in matchup_summary


def test_coach_skips_zero_pp_exhausted_moves() -> None:
    """
    Verifies that if the primary damaging move has 0 Power Points (PP) remaining,
    the Coach skips it and recommends an available move with remaining PP.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="Lesson8ExhaustedPPTrainer",
        selected_pokemon_id=4,
        opponent_pokemon_id=16,
    )
    player_monster: ActiveBattleEntity = session_state["player_monster"]
    opponent_monster: ActiveBattleEntity = session_state["opponent_monster"]

    # Exhaust Scratch PP to 0
    player_monster.move_slots[0].current_power_points = 0

    optimal_move, _, _ = coach_rag_service.evaluate_optimal_unlocked_move(
        player_monster=player_monster,
        opponent_monster=opponent_monster,
    )

    # Should fall back to Growl (move_id=2) since Scratch has 0 PP and slots 3 & 4 are locked
    assert optimal_move.move_name == "Growl"
    assert optimal_move.current_power_points > 0


def test_coach_retrieves_chromadb_vector_lore_or_graceful_archive_fallback() -> None:
    """
    Verifies that retrieve_opponent_lore_from_vector_memory returns rich tactical lore
    for the active opponent whether ChromaDB is seeded or unseeded.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="Lesson8LoreTester",
        selected_pokemon_id=7,  # Squirtle
        opponent_pokemon_id=16,  # Pidgey
    )
    opponent_monster: ActiveBattleEntity = session_state["opponent_monster"]

    lore_context = coach_rag_service.retrieve_opponent_lore_from_vector_memory(
        opponent_monster=opponent_monster
    )

    assert isinstance(lore_context, str)
    assert len(lore_context) > 20
    assert "pidgey" in lore_context.lower()


def test_coach_tactical_advice_service_pipeline() -> None:
    """
    Verifies the end-to-end CoachRAGService.generate_tactical_advice coroutine
    returns a complete, valid CoachTacticalAdviceResponse envelope.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="AshTacticalHero",
        selected_pokemon_id=4,
        opponent_pokemon_id=16,
    )
    battle_session_id = session_state["battle_session_id"]

    advice_response = asyncio.run(
        coach_rag_service.generate_tactical_advice(
            battle_session_id=battle_session_id,
            use_llm_gateway=False,
        )
    )

    assert advice_response.battle_session_id == battle_session_id
    assert advice_response.recommended_action_name == "Scratch"
    assert advice_response.recommended_move_id == 1
    assert advice_response.confidence_rating >= 0.85
    assert "Scratch" in advice_response.tactical_justification
    assert "AshTacticalHero" in advice_response.tactical_justification


def test_fastapi_coach_endpoints_post_and_get() -> None:
    """
    Verifies that both POST /api/v1/battle/coach and GET /api/v1/battle/coach/{session_id}
    return 200 OK with grounded RAG tactical coaching advice, and 404 for unknown sessions.
    """
    init_response = client.post(
        "/api/v1/battle/initiate",
        json={
            "trainer_name": "EndpointCoachTrainer",
            "selected_pokemon_id": 1,  # Bulbasaur
            "opponent_pokemon_id": 16,  # Pidgey
        },
    )
    assert init_response.status_code == 201
    battle_session_id = init_response.json()["battle_session"]["battle_session_id"]

    # 1. Test POST /api/v1/battle/coach
    post_response = client.post(
        "/api/v1/battle/coach",
        json={
            "battle_session_id": battle_session_id,
            "custom_trainer_question": "What is my strongest attack right now?",
            "use_llm_gateway": False,
        },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["battle_session_id"] == battle_session_id
    assert post_payload["recommended_action_name"] == "Tackle"
    assert post_payload["confidence_rating"] >= 0.80
    assert len(post_payload["tactical_justification"]) > 15
    assert len(post_payload["retrieved_lore_context"]) > 10

    # 2. Test GET /api/v1/battle/coach/{battle_session_id}
    get_response = client.get(
        f"/api/v1/battle/coach/{battle_session_id}?use_llm_gateway=false"
    )
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["recommended_action_name"] == "Tackle"

    # 3. Test 404 Not Found on nonexistent session
    missing_response = client.get("/api/v1/battle/coach/nonexistent-session-999")
    assert missing_response.status_code == 404
