"""
Onboarding Routes Module
Handles starter monster catalogs and trainer registration workflows.
"""

from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, status
from src.schemas.onboarding_schema import (
    StarterMonsterInfo,
    TrainerProfileResponse,
    TrainerRegistrationRequest,
)

# Instantiate dedicated APIRouter for onboarding operations
onboarding_router = APIRouter(
    prefix="/api/v1/onboarding",
    tags=["Trainer Onboarding"],
)

# Canonical catalog of the 3 Starter Monsters presented by the Game Guide
AVAILABLE_STARTER_MONSTERS_CATALOG: dict[int, StarterMonsterInfo] = {
    1: StarterMonsterInfo(
        starter_pokemon_id=1,
        monster_name="Bulbasaur",
        elemental_types=["Grass", "Poison"],
        starter_description="A strange seed was planted on its back at birth. The plant sprouts and grows with this Pokémon.",
        base_hit_points=45,
        base_attack_power=49,
        base_defense_rating=49,
        base_speed_velocity=45,
        front_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png",
    ),
    4: StarterMonsterInfo(
        starter_pokemon_id=4,
        monster_name="Charmander",
        elemental_types=["Fire"],
        starter_description="Obviously prefers hot places. When it rains, steam is said to spout from the tip of its tail.",
        base_hit_points=39,
        base_attack_power=52,
        base_defense_rating=43,
        base_speed_velocity=65,
        front_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png",
    ),
    7: StarterMonsterInfo(
        starter_pokemon_id=7,
        monster_name="Squirtle",
        elemental_types=["Water"],
        starter_description="Shoots water at prey while in the water. Withdraws into its shell when in danger.",
        base_hit_points=44,
        base_attack_power=48,
        base_defense_rating=65,
        base_speed_velocity=43,
        front_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/7.png",
    ),
}

# Mapping to accept 1-based index (1, 2, 3) as well as canonical Pokédex IDs (1, 4, 7)
STARTER_INDEX_TO_POKEDEX_ID_MAPPING: dict[int, int] = {
    1: 1,  # Bulbasaur
    2: 4,  # Charmander
    3: 7,  # Squirtle
}

# In-memory store holding active trainer registrations for this session
active_trainer_registration_store: dict[str, TrainerProfileResponse] = {}


@onboarding_router.get(
    "/starters",
    response_model=list[StarterMonsterInfo],
    summary="List Available Starter Monsters",
)
async def get_available_starter_monsters() -> list[StarterMonsterInfo]:
    """
    Returns the list of starter monsters available for the player to choose from.
    Used by the frontend to render the 3 starter cards.
    """
    # Return all 3 starter monsters in canonical catalog order
    return list(AVAILABLE_STARTER_MONSTERS_CATALOG.values())


@onboarding_router.post(
    "/register",
    response_model=TrainerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Trainer Profile",
)
async def register_trainer_profile(
    registration_request: TrainerRegistrationRequest,
) -> TrainerProfileResponse:
    """
    Registers a new trainer profile with their chosen partner starter monster.
    """
    # Resolve the requested starter ID whether passed as canonical pokedex ID or 1-3 index
    requested_id = registration_request.selected_starter_id
    resolved_pokemon_id = (
        requested_id
        if requested_id in AVAILABLE_STARTER_MONSTERS_CATALOG
        else STARTER_INDEX_TO_POKEDEX_ID_MAPPING.get(requested_id)
    )

    # Validate that the selected starter monster exists in our registered catalog
    if resolved_pokemon_id is None or resolved_pokemon_id not in AVAILABLE_STARTER_MONSTERS_CATALOG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid starter ID: {requested_id}. Must be 1 (Bulbasaur), 4 (Charmander), or 7 (Squirtle).",
        )

    # Retrieve starter monster details from the catalog
    selected_starter_details = AVAILABLE_STARTER_MONSTERS_CATALOG[resolved_pokemon_id]

    # Generate a unique registration identifier
    generated_registration_id = f"trainer-{uuid.uuid4().hex[:8]}"

    # Current UTC timestamp in ISO 8601 format
    current_utc_timestamp = datetime.now(timezone.utc).isoformat()

    # Construct the validated trainer profile response
    registered_profile = TrainerProfileResponse(
        trainer_registration_id=generated_registration_id,
        trainer_name=registration_request.trainer_name.strip(),
        selected_starter_monster=selected_starter_details,
        victories_count=0,
        stat_progression_multiplier=1.0,
        created_at_timestamp=current_utc_timestamp,
    )

    # Save to the in-memory store
    active_trainer_registration_store[generated_registration_id] = registered_profile

    return registered_profile