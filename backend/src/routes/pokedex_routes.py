"""
Educational Module Docstring:
This routing module exposes our ChromaDB vector memory through clean REST endpoints.
In modern fullstack AI architectures, the frontend should never touch the vector database directly;
FastAPI acts as the gatekeeper, validating queries and formatting responses.
"""

from fastapi import APIRouter, Query, HTTPException, status
from src.core.chroma_manager import get_or_create_pokedex_collection
from src.schemas.pokedex_schema import (
    PokedexSearchResponse,
    PokedexSeedResponse,
)
from src.services.vector_ingestion_service import (
    search_pokedex_by_meaning,
    seed_canonical_starter_pokedex,
)

# Instantiate the dedicated Pokédex API router with a standard stadium prefix
pokedex_router = APIRouter(
    prefix="/api/v1/pokedex",
    tags=["Smart Pokédex (Vector Memory)"],
)


@pokedex_router.get(
    "/search",
    response_model=PokedexSearchResponse,
    summary="Semantic vector search by concept, vibe, or battle role",
)
async def search_pokedex(
    query: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Natural language description of the monster (e.g. 'heavy armored water turtle')",
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum quantity of top-matching candidates to retrieve",
    ),
) -> PokedexSearchResponse:
    """
    Executes a semantic vector query against ChromaDB using cosine similarity.
    Returns candidate monsters ordered by descending similarity confidence.
    """
    try:
        search_response = search_pokedex_by_meaning(
            search_query_text=query,
            maximum_results_limit=limit,
        )
        return search_response
    except Exception as search_exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic vector search failed: {str(search_exception)}",
        )


@pokedex_router.post(
    "/seed",
    response_model=PokedexSeedResponse,
    summary="Seed vector store with canonical starter and tournament monsters",
)
async def seed_pokedex_vector_memory() -> PokedexSeedResponse:
    """
    Harvests starter records from PokéAPI and converts them into dense vector embeddings.
    """
    try:
        seed_result = await seed_canonical_starter_pokedex()
        return seed_result
    except Exception as seed_exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed vector memory: {str(seed_exception)}",
        )


@pokedex_router.get(
    "/status",
    summary="Check Pokédex vector memory index status",
)
async def get_pokedex_vector_status() -> dict:
    """
    Returns telemetry regarding the number of monsters currently indexed in ChromaDB.
    """
    try:
        active_collection = get_or_create_pokedex_collection()
        total_indexed_monsters: int = active_collection.count()
        return {
            "status": "ready",
            "collection_name": active_collection.name,
            "total_indexed_monsters": total_indexed_monsters,
            "is_memory_seeded": total_indexed_monsters > 0,
        }
    except Exception as status_exception:
        return {
            "status": "error",
            "message": f"Could not inspect vector collection: {str(status_exception)}",
            "total_indexed_monsters": 0,
            "is_memory_seeded": False,
        }