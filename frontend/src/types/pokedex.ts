/**
 * Pokedex Vector Search Types
 * Data contracts synchronized with backend/src/schemas/pokedex_schema.py
 */

export interface SemanticSearchResult {
  pokemon_id: number;
  pokemon_name: string;
  elemental_types: string[];
  base_stats: Record<string, number>;
  front_default_sprite_url: string | null;
  similarity_confidence_score: number;
  matched_lore_snippet: string;
}

export interface PokedexSearchResponse {
  search_query: string;
  total_matches_found: number;
  vector_results: SemanticSearchResult[];
}

export interface PokedexStatusResponse {
  status: "ready" | "error";
  collection_name: string;
  total_indexed_monsters: number;
  is_memory_seeded: boolean;
}

export interface PokedexSeedResponse {
  operation_status: string;
  indexed_monsters_count: number;
  indexed_pokemon_names: string[];
}