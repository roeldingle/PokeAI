"""
Educational Module Docstring:
This service manages the semantic indexing and vector similarity search pipeline.
It transforms structured PokéAPI domain models into dense vector embeddings within ChromaDB,
and executes nearest-neighbor cosine similarity queries for our Smart Pokédex UI.
"""

import json
from typing import List, Optional
from chromadb.api.models.Collection import Collection
from src.core.chroma_manager import get_or_create_pokedex_collection
from src.schemas.pokeapi_schema import PokemonSpeciesLoreRecord
from src.schemas.pokedex_schema import (
    SemanticSearchResult,
    PokedexSearchResponse,
    PokedexSeedResponse,
)
from src.services.pokeapi_client import PokeApiClient

# Domain Knowledge Graph: Maps elemental types to what they are super-effective against
ELEMENTAL_TYPE_ADVANTAGES: dict[str, list[str]] = {
    "normal": [],
    "fire": ["grass", "ice", "bug", "steel"],
    "water": ["fire", "ground", "rock"],
    "electric": ["water", "flying"],
    "grass": ["water", "ground", "rock"],
    "ice": ["grass", "ground", "flying", "dragon"],
    "fighting": ["normal", "ice", "rock", "dark", "steel"],
    "poison": ["grass", "fairy"],
    "ground": ["fire", "electric", "poison", "rock", "steel"],
    "flying": ["grass", "fighting", "bug"],
    "psychic": ["fighting", "poison"],
    "bug": ["grass", "psychic", "dark"],
    "rock": ["fire", "ice", "flying", "bug"],
    "ghost": ["psychic", "ghost"],
    "dragon": ["dragon"],
    "steel": ["ice", "rock", "fairy"],
    "fairy": ["fighting", "dragon", "dark"],
}

# Canonical species classifications (genus) to bridge queries like "mouse", "turtle", "lizard"
CANONICAL_MONSTER_GENERA: dict[str, str] = {
    "bulbasaur": "Seed Pokémon",
    "ivysaur": "Seed Pokémon",
    "venusaur": "Seed Pokémon",
    "charmander": "Lizard Pokémon",
    "charmeleon": "Flame Pokémon",
    "charizard": "Flame Dragon Pokémon",
    "squirtle": "Tiny Turtle Pokémon",
    "wartortle": "Turtle Pokémon",
    "blastoise": "Shellfish Water Pokémon",
    "pikachu": "Electric Mouse Pokémon",
    "raichu": "Electric Mouse Pokémon",
    "pidgey": "Tiny Bird Flyer Pokémon",
    "onix": "Rock Snake Pokémon",
    "gengar": "Shadow Ghost Pokémon",
}


def construct_composite_lore_document(monster_record: PokemonSpeciesLoreRecord) -> str:
    """
    Synthesizes monster identity, elemental typings, species genus, combat stats,
    type matchup counters, and narrative lore into an information-rich document
    optimal for dense text embeddings.
    """
    # 1. Resolve species genus (e.g., 'Electric Mouse Pokémon')
    species_genus: str = CANONICAL_MONSTER_GENERA.get(
        monster_record.pokemon_name.lower(), "Battle Pokémon"
    )

    # 2. Extract type advantages to bridge tactical queries like 'good against water flyers'
    counters_list: list[str] = []
    for elemental_type in monster_record.elemental_types:
        advantages = ELEMENTAL_TYPE_ADVANTAGES.get(elemental_type.lower(), [])
        counters_list.extend(advantages)
    
    # Remove duplicates while preserving readability
    unique_counters = list(dict.fromkeys(counters_list))
    counters_text: str = (
        f"Super effective and strong in battle against: {', '.join(unique_counters)} type monsters."
        if unique_counters
        else "Standard neutral battle coverage."
    )

    # 3. Join elemental typings and abilities
    elemental_types_text: str = ", ".join(monster_record.elemental_types) or "Normal"
    abilities_text: str = ", ".join(monster_record.abilities) or "Standard Combat"

    # 4. Format combat stats
    stats_summary: str = (
        f"HP: {monster_record.base_stats.get('hp', monster_record.base_stats.get('hit_points', 0))}, "
        f"Attack: {monster_record.base_stats.get('attack', 0)}, "
        f"Defense: {monster_record.base_stats.get('defense', 0)}, "
        f"Special Attack: {monster_record.base_stats.get('special_attack', 0)}, "
        f"Special Defense: {monster_record.base_stats.get('special_defense', 0)}, "
        f"Speed: {monster_record.base_stats.get('speed', 0)}"
    )

    # 5. Build unified enriched profile
    composite_document: str = (
        f"{monster_record.pokemon_name.title()} (National Dex #{monster_record.pokemon_id}) "
        f"is an official {species_genus} with {elemental_types_text} elemental typing. "
        f"Abilities: {abilities_text}. "
        f"Tactical Battle Matchups: {counters_text} "
        f"Combat statistics: {stats_summary}. "
        f"Pokédex Lore: {monster_record.lore_flavor_text}"
    )

    return composite_document

def index_pokemon_records(
    monster_records: List[PokemonSpeciesLoreRecord],
    target_collection: Optional[Collection] = None,
) -> int:
    """
    Converts a batch of PokemonSpeciesLoreRecord domain models into vector embeddings
    and stores them with rich metadata inside the ChromaDB collection.
    """
    # Resolve the active collection
    active_collection: Collection = target_collection or get_or_create_pokedex_collection()

    # Prepare batch arrays required by ChromaDB's upsert API
    document_identifiers: List[str] = []
    text_documents: List[str] = []
    metadata_dictionaries: List[dict] = []

    # Iterate through each harvested monster record
    for monster_record in monster_records:
        # Create a unique, deterministic document identifier (e.g., 'pokemon_4')
        unique_document_id: str = f"pokemon_{monster_record.pokemon_id}"
        
        # Build the semantic text representation for embedding calculation
        semantic_text: str = construct_composite_lore_document(monster_record)

        # Build metadata dictionary (Chroma requires primitive types: str, int, float, bool)
        metadata: dict = {
            "pokemon_id": monster_record.pokemon_id,
            "pokemon_name": monster_record.pokemon_name.lower(),
            "elemental_types_csv": ",".join(monster_record.elemental_types),
            "front_default_sprite_url": monster_record.front_default_sprite_url or "",
            "base_stats_json": json.dumps(monster_record.base_stats),
            "lore_flavor_text": monster_record.lore_flavor_text,
        }

        document_identifiers.append(unique_document_id)
        text_documents.append(semantic_text)
        metadata_dictionaries.append(metadata)

    # Upsert prevents duplicates by overwriting existing documents with matching IDs
    active_collection.upsert(
        ids=document_identifiers,
        documents=text_documents,
        metadatas=metadata_dictionaries,
    )

    return len(document_identifiers)


def search_pokedex_by_meaning(
    search_query_text: str,
    maximum_results_limit: int = 5,
    target_collection: Optional[Collection] = None,
) -> PokedexSearchResponse:
    """
    Performs semantic vector search against the Pokédex collection using cosine similarity.
    Calculates similarity confidence scores and reconstructs domain models for the UI.
    """
    # Obtain the target vector collection
    active_collection: Collection = target_collection or get_or_create_pokedex_collection()

    # If the collection has no documents, return an empty response gracefully
    collection_item_count: int = active_collection.count()
    if collection_item_count == 0:
        return PokedexSearchResponse(
            search_query=search_query_text,
            total_matches_found=0,
            vector_results=[],
        )

    # Bound the retrieval limit to the actual number of documents stored
    safe_retrieval_limit: int = min(maximum_results_limit, collection_item_count)

    # Query ChromaDB using natural language; Chroma automatically computes the embedding
    query_results = active_collection.query(
        query_texts=[search_query_text],
        n_results=safe_retrieval_limit,
        include=["metadatas", "documents", "distances"],
    )

    # Parse query outputs
    matched_search_results: List[SemanticSearchResult] = []
    
    # Extract result lists for the first (and only) search query
    extracted_metadatas = query_results.get("metadatas", [[]])[0]
    extracted_distances = query_results.get("distances", [[]])[0]

    for index, metadata_dict in enumerate(extracted_metadatas):
        # Extract cosine distance; with cosine distance, similarity = 1.0 - distance
        raw_cosine_distance: float = extracted_distances[index]
        
        # Clamp confidence score between 0.0 and 1.0 and round for UI readability
        calculated_confidence_score: float = round(
            max(0.0, min(1.0, 1.0 - raw_cosine_distance)), 2
        )

        # Deserialize the stored elemental types and combat metrics
        types_csv: str = metadata_dict.get("elemental_types_csv", "")
        elemental_types_list: List[str] = [t.strip() for t in types_csv.split(",") if t.strip()]

        raw_stats_json: str = metadata_dict.get("base_stats_json", "{}")
        try:
            parsed_base_stats: dict = json.loads(raw_stats_json)
        except Exception:
            parsed_base_stats = {}

        # Reconstruct the strongly-typed SemanticSearchResult
        search_result = SemanticSearchResult(
            pokemon_id=int(metadata_dict.get("pokemon_id", 0)),
            pokemon_name=str(metadata_dict.get("pokemon_name", "")),
            elemental_types=elemental_types_list,
            base_stats=parsed_base_stats,
            front_default_sprite_url=metadata_dict.get("front_default_sprite_url") or None,
            similarity_confidence_score=calculated_confidence_score,
            matched_lore_snippet=str(metadata_dict.get("lore_flavor_text", "")),
        )
        matched_search_results.append(search_result)

    return PokedexSearchResponse(
        search_query=search_query_text,
        total_matches_found=len(matched_search_results),
        vector_results=matched_search_results,
    )


async def seed_canonical_starter_pokedex(
    target_collection: Optional[Collection] = None,
) -> PokedexSeedResponse:
    """
    Harvests an iconic roster of tournament monsters using the Lesson 03 PokéAPI client
    and indexes them into persistent vector memory.
    """
    # Canonical starter roster + iconic tournament companions
    starter_roster_names: List[str] = [
        "bulbasaur",
        "charmander",
        "squirtle",
        "pikachu",
        "pidgey",
        "charizard",
        "blastoise",
        "venusaur",
        "onix",
        "gengar",
    ]

    scouting_client = PokeApiClient()
    harvested_records: List[PokemonSpeciesLoreRecord] = []

    # Harvest species records using our Lesson 03 async client
    for monster_name in starter_roster_names:
        try:
            lore_record = await scouting_client.fetch_full_pokemon_lore_record(monster_name)
            harvested_records.append(lore_record)
        except Exception as harvest_exception:
            # Continue gracefully if external network drops an individual species
            print(f"Warning: Failed to harvest {monster_name} for vector seeding: {harvest_exception}")

    # Index all harvested records into ChromaDB
    total_indexed_count: int = index_pokemon_records(
        monster_records=harvested_records,
        target_collection=target_collection,
    )

    indexed_names: List[str] = [record.pokemon_name for record in harvested_records]

    return PokedexSeedResponse(
        operation_status="Successfully seeded vector memory with tournament monsters",
        indexed_monsters_count=total_indexed_count,
        indexed_pokemon_names=indexed_names,
    )