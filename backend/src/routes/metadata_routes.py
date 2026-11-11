"""
Metadata Routes Module
Exposes endpoints providing stadium identity, engine version, and environment configuration.
"""

from fastapi import APIRouter, status
from src.core import config
from src.schemas.metadata_schema import GameMetadataResponse

# Instantiate an isolated router for game metadata endpoints
metadata_router = APIRouter(
    prefix="/api/v1",
    tags=["Stadium Metadata"],
)


@metadata_router.get(
    "/metadata",
    response_model=GameMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve PokeAI Stadium Metadata",
    description="Returns the active environment configuration, game version, and identity details.",
)
async def get_stadium_game_metadata() -> GameMetadataResponse:
    """
    Handles GET requests to retrieve centralized stadium configuration metadata.
    Acts as the initial handshake between the frontend client and the backend engine.
    """
    # Construct the validated response using values loaded directly from the core configuration
    return GameMetadataResponse(
        application_environment=config.APP_ENV,
        game_version=config.VERSION,
        project_learning_goal=config.PROJECT_GOAL,
        game_title=config.GAME_TITLE,
        game_description=config.GAME_DESCRIPTION,
        game_guide_name=config.GAME_GUIDE,
    )
