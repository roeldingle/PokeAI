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
from src.services.battle_engine import battle_engine_service

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
