/**
 * Pokedex Vector Search Service
 * Client module for querying ChromaDB vector memory and seeding monster lore.
 */

import type {
  PokedexSearchResponse,
  PokedexStatusResponse,
  PokedexSeedResponse,
} from "../types/pokedex";

const BACKEND_BASE_URL = "http://127.0.0.1:8000";

/**
 * Checks the initialization status of the ChromaDB collection.
 */
export async function fetchPokedexStatus(): Promise<PokedexStatusResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/v1/pokedex/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch Pokédex vector status: HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Searches the vector memory using conceptual natural language queries.
 */
export async function searchPokedexByMeaning(
  query: string,
  limit: number = 6
): Promise<PokedexSearchResponse> {
  const searchUrl = new URL(`${BACKEND_BASE_URL}/api/v1/pokedex/search`);
  searchUrl.searchParams.set("query", query.trim());
  searchUrl.searchParams.set("limit", limit.toString());

  const response = await fetch(searchUrl.toString());
  if (!response.ok) {
    throw new Error(`Vector search failed: HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Triggers batch harvesting and embedding of tournament monsters into ChromaDB.
 */
export async function seedPokedexVectorMemory(): Promise<PokedexSeedResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/v1/pokedex/seed`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error(`Failed to seed vector memory: HTTP ${response.status}`);
  }
  return response.json();
}