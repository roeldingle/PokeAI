"""
Battle Routes Module
Exposes REST endpoints under /api/v1/battle for initiating combat matches,
submitting player attack moves, and querying active battle session state.
"""

from fastapi import APIRouter, HTTPException, status
from src.schemas.battle_schema import (
    BattleInitiationRequest,
    BattleTurnResolutionResponse,
    TurnActionRequest,
)
from src.schemas.progression_schema import (
    TeamSwapRequest,
    TeamSwapResponse,
    TrainerPartyPoolState,
)
from src.schemas.catch_schema import (
    CatchRouletteSpinRequest,
    CatchRouletteOutcome,
)
from src.schemas.coach_schema import (
    CoachTacticalAdviceRequest,
    CoachTacticalAdviceResponse,
)
from src.schemas.gym_leader_schema import (
    GymLeaderTurnDecision,
    GymLeaderTurnDecisionRequest,
)
from src.services.battle_engine import battle_engine_service
from src.services.battle_progression_service import battle_progression_service
from src.services.catch_roulette_service import catch_roulette_service
from src.services.coach_rag_service import coach_rag_service
from src.services.gym_leader_agent import gym_leader_agent_service

# Initialize dedicated battle router under /api/v1/battle
battle_router = APIRouter(
    prefix="/api/v1/battle",
    tags=["GBA Battle Arena"],
)


@battle_router.post(
    "/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a new GBA Battle match",
)
async def initiate_battle_match(
    initiation_request: BattleInitiationRequest,
) -> dict:
    """
    Starts an authentic GBA battle session with the player's chosen starter monster
    facing off against a wild opponent (default Pidgey Lv 5).
    """
    try:
        # Construct and persist initial battle session in memory
        session_state = battle_engine_service.initialize_battle_session(
            trainer_name=initiation_request.trainer_name,
            selected_pokemon_id=initiation_request.selected_pokemon_id,
            opponent_pokemon_id=initiation_request.opponent_pokemon_id or 16,
        )
        return {
            "status": "success",
            "message": "Battle session initialized successfully.",
            "battle_session": session_state,
        }
    except Exception as error_exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initiate battle: {str(error_exception)}",
        )


@battle_router.post(
    "/turn/resolve",
    response_model=BattleTurnResolutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve a round of combat based on selected player move",
)
async def resolve_battle_turn(
    action_request: TurnActionRequest,
) -> BattleTurnResolutionResponse:
    """
    Executes a complete turn: resolves speed priority, calculates deterministic damage,
    decrements move power points (PP), updates HP, and returns retro narration logs.
    """
    try:
        resolution_result = battle_engine_service.resolve_combat_round(
            battle_session_id=action_request.battle_session_id,
            selected_move_id=action_request.selected_move_id,
        )
        return resolution_result
    except ValueError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(validation_error),
        )
    except Exception as unexpected_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Combat calculation error: {str(unexpected_error)}",
        )


@battle_router.get(
    "/session/{battle_session_id}",
    status_code=status.HTTP_200_OK,
    summary="Fetch current state of an active battle session",
)
async def get_battle_session_state(
    battle_session_id: str,
) -> dict:
    """
    Retrieves the real-time health points, move slots, and turn counter for an ongoing battle.
    """
    session_data = battle_engine_service.active_battle_sessions.get(battle_session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle session '{battle_session_id}' not found.",
        )
    return {
        "status": "success",
        "battle_session": session_data,
    }


@battle_router.post(
    "/team/swap",
    response_model=TeamSwapResponse,
    status_code=status.HTTP_200_OK,
    summary="Swap active monster from trainer party pool before Turn 1 begins",
)
async def swap_active_party_monster(
    swap_request: TeamSwapRequest,
) -> TeamSwapResponse:
    """
    Executes a Lesson 6 pre-Turn 1 party swap (`TEAM` button).
    Rejected if Turn 1 has already started or if the trainer only owns 1 monster.
    """
    session_data = battle_engine_service.active_battle_sessions.get(
        swap_request.battle_session_id
    )
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle session '{swap_request.battle_session_id}' not found.",
        )

    try:
        swap_response = battle_progression_service.execute_pre_turn_team_swap(
            battle_session=session_data,
            target_pokemon_id=swap_request.target_pokemon_id,
        )
        session_data["party_pool"] = swap_response.party_pool_state.model_dump()
        return swap_response
    except ValueError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(validation_error),
        )


@battle_router.get(
    "/trainer/{trainer_name}/party",
    response_model=TrainerPartyPoolState,
    status_code=status.HTTP_200_OK,
    summary="Retrieve trainer's party pool and monster progression stats",
)
async def get_trainer_party_pool(
    trainer_name: str,
) -> TrainerPartyPoolState:
    """
    Returns the trainer's recruited monster pool, victory counts, +1% stat multipliers,
    unlocked move slots, and TEAM swap eligibility flag.
    """
    return battle_progression_service.get_trainer_party_pool_state(
        trainer_name=trainer_name
    )


@battle_router.post(
    "/catch/roulette",
    response_model=CatchRouletteOutcome,
    status_code=status.HTTP_200_OK,
    summary="Spin the Lesson 7 Pokéball Roulette Wheel upon Turn 5 expiration",
)
async def spin_catch_roulette(
    spin_request: CatchRouletteSpinRequest,
) -> CatchRouletteOutcome:
    """
    Executes the Lesson 7 Overtime Catch Roulette:
    1. Determines Pokéball tier using weighted wheel probability.
    2. Tests capture success against tier probability (50% to 90%).
    3. If caught, auto-recruits the wild monster into the trainer's party pool.
    4. Returns full outcome with 3-wobble announcer narration and updated party state.
    """
    try:
        outcome = catch_roulette_service.execute_roulette_spin_and_catch(
            spin_request=spin_request
        )
        return outcome
    except Exception as calculation_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Roulette spin calculation failed: {str(calculation_error)}",
        )


@battle_router.post(
    "/coach",
    response_model=CoachTacticalAdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Lesson 8 RAG tactical coaching advice from the Game Guide",
)
async def request_coach_tactical_advice(
    advice_request: CoachTacticalAdviceRequest,
) -> CoachTacticalAdviceResponse:
    """
    Executes the Lesson 8 'ASK GUIDE' Tactical Whisperer RAG pipeline:
    1. Queries ChromaDB vector memory for active opponent lore and weaknesses.
    2. Computes deterministic elemental effectiveness across unlocked player moves.
    3. Synthesizes an in-character tactical recommendation via the Resilient LLM Gateway.
    """
    try:
        tactical_advice = await coach_rag_service.generate_tactical_advice(
            battle_session_id=advice_request.battle_session_id,
            custom_trainer_question=advice_request.custom_trainer_question,
            use_llm_gateway=advice_request.use_llm_gateway,
        )
        return tactical_advice
    except ValueError as not_found_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(not_found_error),
        )
    except Exception as coaching_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tactical RAG coach error: {str(coaching_error)}",
        )


@battle_router.get(
    "/coach/{battle_session_id}",
    response_model=CoachTacticalAdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch Lesson 8 RAG tactical advice for a battle session by ID",
)
async def get_coach_tactical_advice_by_session(
    battle_session_id: str,
    use_llm_gateway: bool = True,
) -> CoachTacticalAdviceResponse:
    """
    GET convenience endpoint for retrieving RAG tactical advice for an active battle session.
    """
    try:
        return await coach_rag_service.generate_tactical_advice(
            battle_session_id=battle_session_id,
            use_llm_gateway=use_llm_gateway,
        )
    except ValueError as not_found_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(not_found_error),
        )
    except Exception as coaching_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tactical RAG coach error: {str(coaching_error)}",
        )


@battle_router.post(
    "/gym-leader/decide",
    response_model=GymLeaderTurnDecision,
    status_code=status.HTTP_200_OK,
    summary="Execute Lesson 9 Autonomous Gym Leader Agent decision loop",
)
async def decide_gym_leader_turn_action(
    decision_request: GymLeaderTurnDecisionRequest,
) -> GymLeaderTurnDecision:
    """
    Executes the Lesson 9 Autonomous Gym Leader AI Agent loop (Perceive -> Remember -> Decide -> Act):
    1. Perceives field HP ratios, elemental matchups, and player's +1% stat_progression_multiplier.
    2. Recalls combat memory from prior turns.
    3. Selects the mathematically optimal move slot.
    4. Emits an in-character battle taunt conditioned on persona (BROCK, MISTY, or WILD_INSTINCT).
    """
    session_data = battle_engine_service.active_battle_sessions.get(
        decision_request.battle_session_id
    )
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle session '{decision_request.battle_session_id}' not found.",
        )

    try:
        return await gym_leader_agent_service.evaluate_turn_decision_for_session(
            battle_session=session_data,
            calculate_effectiveness_fn=battle_engine_service.calculate_elemental_effectiveness,
            gym_leader_persona=decision_request.gym_leader_persona,
            use_llm_gateway=decision_request.use_llm_gateway,
        )
    except Exception as agent_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gym Leader Agent decision failed: {str(agent_error)}",
        )



