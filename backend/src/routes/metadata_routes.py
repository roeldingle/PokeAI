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
        application_environment=config.application_environment,
        game_version=config.game_version,
        project_learning_goal=config.project_learning_goal,
        game_title=config.game_title,
        game_description=config.game_description,
        game_guide_name=config.game_guide_name,
    )
