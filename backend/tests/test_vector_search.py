"""
Educational Test Docstring:
This test module verifies our ChromaDB vector memory and semantic search pipeline.
It validates:
1. Document synthesis formatting for vector embeddings.
2. Indexing and cosine similarity retrieval using an isolated, ephemeral in-memory collection.
3. Accurate semantic ranking (e.g. querying 'fiery lizard' correctly surfaces Charmander as #1).
4. Graceful handling of empty collections.
5. FastAPI integration via TestClient.
"""

import uuid
import chromadb
import pytest
from fastapi.testclient import TestClient
from src.core.chroma_manager import get_or_create_pokedex_collection
from src.main import app
from src.schemas.pokeapi_schema import PokemonSpeciesLoreRecord
from src.services.vector_ingestion_service import (
    construct_composite_lore_document,
    index_pokemon_records,
    search_pokedex_by_meaning,
)


@pytest.fixture
def mock_tournament_roster() -> list[PokemonSpeciesLoreRecord]:
    """
    Provides a controlled, representative set of four canonical monster lore records.
    """
    return [
        PokemonSpeciesLoreRecord(
            pokemon_id=1,
            pokemon_name="bulbasaur",
            elemental_types=["grass", "poison"],
            base_stats={"hit_points": 45, "attack": 49, "defense": 49, "special_attack": 65, "special_defense": 65, "speed": 45},
            abilities=["overgrow", "chlorophyll"],
            lore_flavor_text="A strange seed was planted on its back at birth. The plant sprouts and grows with this monster.",
            front_default_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png",
        ),
        PokemonSpeciesLoreRecord(
            pokemon_id=4,
            pokemon_name="charmander",
            elemental_types=["fire"],
            base_stats={"hit_points": 39, "attack": 52, "defense": 43, "special_attack": 60, "special_defense": 50, "speed": 65},
            abilities=["blaze", "solar-power"],
            lore_flavor_text="Obviously prefers hot places. When it rains, steam is said to spout from the tip of its tail.",
            front_default_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png",
        ),
        PokemonSpeciesLoreRecord(
            pokemon_id=7,
            pokemon_name="squirtle",
            elemental_types=["water"],
            base_stats={"hit_points": 44, "attack": 48, "defense": 65, "special_attack": 50, "special_defense": 64, "speed": 43},
            abilities=["torrent", "rain-dish"],
            lore_flavor_text="After birth, its back swells and hardens into a protective shell. Powerfully sprays foam from its mouth.",
            front_default_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/7.png",
        ),
        PokemonSpeciesLoreRecord(
            pokemon_id=25,
            pokemon_name="pikachu",
            elemental_types=["electric"],
            base_stats={"hit_points": 35, "attack": 55, "defense": 40, "special_attack": 50, "special_defense": 50, "speed": 90},
            abilities=["static", "lightning-rod"],
            lore_flavor_text="When several of these monsters gather, their electricity could build and cause lightning storms.",
            front_default_sprite_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
        ),
    ]


@pytest.fixture
def ephemeral_test_collection():
    """
    Creates an isolated in-memory ChromaDB collection with a unique UUID name
    so tests never share state or leak documents between each other.
    """
    in_memory_client = chromadb.EphemeralClient()
    unique_collection_name = f"test_ephemeral_pokedex_{uuid.uuid4().hex}"
    test_collection = get_or_create_pokedex_collection(
        chroma_client_instance=in_memory_client,
        collection_name=unique_collection_name,
    )
    return test_collection


def test_construct_composite_lore_document_formatting(mock_tournament_roster):
    """
    Asserts that the text synthesizer formats name, typing, stats, and narrative lore properly.
    """
    charmander_record = mock_tournament_roster[1]
    composite_doc = construct_composite_lore_document(charmander_record)

    # Validate essential tokens are present
    assert "Charmander" in composite_doc
    assert "fire" in composite_doc
    assert "Attack: 52" in composite_doc
    assert "tip of its tail" in composite_doc


def test_vector_indexing_and_semantic_retrieval(mock_tournament_roster, ephemeral_test_collection):
    """
    Indexes the 4 monsters into ChromaDB and validates conceptual similarity queries.
    """
    # 1. Ingest test monsters into the isolated in-memory vector store
    indexed_count = index_pokemon_records(
        monster_records=mock_tournament_roster,
        target_collection=ephemeral_test_collection,
    )
    assert indexed_count == 4
    assert ephemeral_test_collection.count() == 4

    # 2. Semantic query for fiery reptile concept
    fire_query_response = search_pokedex_by_meaning(
        search_query_text="fiery reptile with hot flame on its tail",
        maximum_results_limit=2,
        target_collection=ephemeral_test_collection,
    )

    assert fire_query_response.total_matches_found >= 1
    top_fire_match = fire_query_response.vector_results[0]
    # Assert Charmander is the #1 ranked semantic match
    assert top_fire_match.pokemon_name == "charmander"
    assert top_fire_match.pokemon_id == 4
    assert "fire" in top_fire_match.elemental_types
    # Assert positive similarity confidence and clear superiority over candidate #2
    assert top_fire_match.similarity_confidence_score > 0.30
    if len(fire_query_response.vector_results) > 1:
        assert top_fire_match.similarity_confidence_score > fire_query_response.vector_results[1].similarity_confidence_score

    # 3. Semantic query for electric mouse concept
    electric_query_response = search_pokedex_by_meaning(
        search_query_text="electric rodent that discharges lightning storms",
        maximum_results_limit=2,
        target_collection=ephemeral_test_collection,
    )

    assert electric_query_response.total_matches_found >= 1
    top_electric_match = electric_query_response.vector_results[0]
    # Assert Pikachu is the #1 ranked semantic match
    assert top_electric_match.pokemon_name == "pikachu"
    assert "electric" in top_electric_match.elemental_types
    assert top_electric_match.similarity_confidence_score > 0.30
    if len(electric_query_response.vector_results) > 1:
        assert top_electric_match.similarity_confidence_score > electric_query_response.vector_results[1].similarity_confidence_score


def test_empty_collection_returns_empty_response(ephemeral_test_collection):
    """
    Verifies that querying an unpopulated collection returns an empty list without crashing.
    """
    search_response = search_pokedex_by_meaning(
        search_query_text="mysterious shadowy dragon",
        maximum_results_limit=3,
        target_collection=ephemeral_test_collection,
    )

    assert search_response.total_matches_found == 0
    assert len(search_response.vector_results) == 0


def test_fastapi_pokedex_status_and_search_endpoints():
    """
    End-to-end integration test validating the FastAPI REST endpoints.
    """
    test_client = TestClient(app)

    # 1. Check status endpoint
    status_response = test_client.get("/api/v1/pokedex/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] == "ready"
    assert "total_indexed_monsters" in status_payload

    # 2. Check search endpoint validation (too short query should trigger 422)
    invalid_query_response = test_client.get("/api/v1/pokedex/search?query=a")
    assert invalid_query_response.status_code == 422

    # 3. Check search endpoint execution with valid query
    valid_query_response = test_client.get("/api/v1/pokedex/search?query=fire+lizard")
    assert valid_query_response.status_code == 200
    search_payload = valid_query_response.json()
    assert "search_query" in search_payload
    assert "vector_results" in search_payload