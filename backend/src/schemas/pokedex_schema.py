"""
Educational Module Docstring:
This module defines the Pydantic v2 data contracts for our ChromaDB vector memory.
In vector search, natural language queries are matched by spatial angle (cosine distance)
rather than exact spelling. These schemas standardize the incoming search requests,
the ranked similarity results, and the database seeding responses.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SemanticSearchResult(BaseModel):
    """
    Represents an individual monster entry retrieved from vector memory based on conceptual similarity.
    """
    # Ensures compatibility while discarding unexpected raw vector store attributes
    model_config = ConfigDict(extra="ignore")

    # National Pokédex numerical identifier
    pokemon_id: int = Field(
        ...,
        description="Official National Pokédex registration number"
    )
    # Canonical monster name in lowercase
    pokemon_name: str = Field(
        ...,
        description="Lowercase canonical monster identifier name"
    )
    # Elemental affinities (e.g., ['fire'], ['water', 'flying'])
    elemental_types: List[str] = Field(
        default_factory=list,
        description="Elemental type categories determining stadium battle advantages"
    )
    # Core combat statistics extracted from PokéAPI
    base_stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Core combat metrics including hit points, attack, defense, and speed"
    )
    # Optional URL to the official animated or static front sprite
    front_default_sprite_url: Optional[str] = Field(
        default=None,
        description="Direct web link to the monster front-facing sprite image"
    )
    # Cosine similarity confidence score bounded between 0.0 (unrelated) and 1.0 (identical vibe)
    similarity_confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mathematical similarity metric derived from cosine distance (1.0 - distance)"
    )
    # The actual narrative lore snippet that matched the trainer's conceptual query
    matched_lore_snippet: str = Field(
        ...,
        description="The canonical species lore text chunk stored inside the vector coordinate map"
    )


class PokedexSearchRequest(BaseModel):
    """
    Payload sent by the trainer when searching the Pokédex by vibe or meaning.
    """
    # The natural language concept entered by the trainer (e.g., 'heavy armored turtle')
    search_query_text: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Natural language query string describing monster characteristics or battle roles"
    )
    # Upper bound of candidate monsters to retrieve from the arena vector map
    maximum_results_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of top-matching candidates to retrieve from vector memory"
    )


class PokedexSearchResponse(BaseModel):
    """
    Stadium envelope containing the original search query and ranked candidate monsters.
    """
    # Echo back the original search query for user interface alignment
    search_query: str = Field(
        ...,
        description="The original search query evaluated by the vector memory engine"
    )
    # Count of candidate monsters found in vector storage
    total_matches_found: int = Field(
        ...,
        description="Total quantity of matching candidate monsters returned"
    )
    # Ordered list of semantic matches ranked from highest cosine confidence to lowest
    vector_results: List[SemanticSearchResult] = Field(
        default_factory=list,
        description="Candidate monsters ordered by descending similarity confidence score"
    )


class PokedexSeedResponse(BaseModel):
    """
    Status report returned after batch ingesting canonical Pokémon records into ChromaDB.
    """
    # Success indicator message
    operation_status: str = Field(
        ...,
        description="Operational status message summarizing the batch vector ingestion"
    )
    # Number of monsters successfully transformed into vector embeddings
    indexed_monsters_count: int = Field(
        ...,
        description="Total number of monster records embedded and written to persistent storage"
    )
    # List of monster names that are now searchable by meaning
    indexed_pokemon_names: List[str] = Field(
        default_factory=list,
        description="List of canonical monster names now resident in the stadium vector memory"
    )