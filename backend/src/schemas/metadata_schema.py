"""
Metadata Schema Module
Defines the Pydantic data contract for delivering game and configuration metadata to the frontend.
"""

from pydantic import BaseModel, ConfigDict, Field


class GameMetadataResponse(BaseModel):
    """
    Response model delivering runtime environment details and game identity to the client.
    Guarantees that the UI displays accurate stadium rules and metadata directly from the backend.
    """

    # Enforce strict type validation and documentation integrity
    model_config = ConfigDict(
        # Disallow extra undeclared attributes to prevent contract drift between frontend and backend
        extra="forbid",
        # Enable human-readable schema serialization for OpenAPI autodocumentation
        json_schema_extra={
            "example": {
                "application_environment": "local",
                "game_version": "0.1.0",
                "project_learning_goal": "AI Engineering Path while building a turn-based monster battler game.",
                "game_title": "PokeAI",
                "game_description": "A turn-based monster battler engineered step-by-step to master AI Engineering principles.",
                "game_guide_name": "Shaneil",
            }
        },
    )

    # Identifies whether the game is running locally, in staging, or in cloud production
    application_environment: str = Field(
        ...,
        description="Environment classification e.g. local, develop, production",
    )

    # Semantic version string of the PokeAI game
    game_version: str = Field(
        ...,
        description="Semver game version e.g. 0.1.0",
    )

    # The high-level learning goal powering this engineering journey
    project_learning_goal: str = Field(
        ...,
        description="High-level pedagogical mission statement of the curriculum",
    )

    # Display title of the arena
    game_title: str = Field(
        ...,
        description="Title of the game: PokeAI",
    )

    # Descriptive narrative tagline shown on the retro landing screen
    game_description: str = Field(
        ...,
        description="Tagline description of the game experience",
    )

    # Name of the personal AI mentor and guide
    game_guide_name: str = Field(
        ...,
        description="Name of the game guide: Shaneil",
    )
