/**
 * Smart Pokédex Screen (Storyboard Screen 2)
 * Demonstrates ChromaDB vector memory, semantic similarity, and cosine confidence ranking.
 */

import React, { useEffect, useState } from "react";
import { ButtonUI } from "../ui/ButtonUI";
import {
  fetchPokedexStatus,
  searchPokedexByMeaning,
  seedPokedexVectorMemory,
} from "../../services/pokedexService";
import type {
  SemanticSearchResult,
  PokedexStatusResponse,
} from "../../types/pokedex";

interface PokedexSearchScreenProps {
  onBackToPrevious: () => void;
}

const PRESET_SEARCH_QUERIES: string[] = [
  "fast electric mouse good against water flyers",
  "fiery lizard with high special attack",
  "heavy armored water turtle",
  "seed plant monster with sleep spores",
  "ghost pokemon that hides in shadows",
];

export const PokedexSearchScreen: React.FC<PokedexSearchScreenProps> = ({
  onBackToPrevious,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("fast electric mouse good against water flyers");
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[]>([]);
  const [statusInfo, setStatusInfo] = useState<PokedexStatusResponse | null>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  // Inspect vector collection status on mount
  useEffect(() => {
    loadVectorStatus();
  }, []);

  async function loadVectorStatus() {
    try {
      const status = await fetchPokedexStatus();
      setStatusInfo(status);
    } catch (err) {
      console.warn("Could not check vector status:", err);
    }
  }

  async function handleExecuteSearch(overrideQuery?: string) {
    const queryToSearch = (overrideQuery ?? searchQuery).trim();
    if (!queryToSearch) return;

    setIsSearching(true);
    setStatusMessage("");
    try {
      const response = await searchPokedexByMeaning(queryToSearch, 6);
      setSearchResults(response.vector_results);
      if (response.vector_results.length === 0) {
        setStatusMessage("No candidate monsters found in vector storage. Try seeding the memory first!");
      }
    } catch (err: any) {
      setStatusMessage(`Search failed: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  }

  async function handleSeedDatabase() {
    setIsSeeding(true);
    setStatusMessage("Harvesting tournament monsters from PokéAPI & generating vector embeddings...");
    try {
      const seedResponse = await seedPokedexVectorMemory();
      setStatusMessage(`Success! Indexed ${seedResponse.indexed_monsters_count} monsters into ChromaDB.`);
      await loadVectorStatus();
      // Auto-trigger search after seeding
      await handleExecuteSearch();
    } catch (err: any) {
      setStatusMessage(`Seeding failed: ${err.message}`);
    } finally {
      setIsSeeding(false);
    }
  }

  return (
    <div className="pokeai-viewport">
      <div className="gba-screen-chassis">
        {/* Header Bar */}
        <header className="stadium-header-bar">
          <span className="stadium-indicator">
            ● LESSON 4: SMART POKÉDEX (CHROMADB VECTOR MEMORY)
          </span>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <span
              style={{
                fontSize: "0.8rem",
                color: "var(--color-text-secondary)",
                fontWeight: "bold",
              }}
            >
              Indexed: {statusInfo?.total_indexed_monsters ?? 0}
            </span>
            <button
              type="button"
              onClick={onBackToPrevious}
              className="stadium-env-tag"
              style={{ cursor: "pointer", border: "none", background: "#f1f5f9" }}
            >
              ◀ BACK
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
          }}
        >
          {/* Search Box Card */}
          <div
            style={{
              background: "#ffffff",
              border: "3px solid #1e293b",
              borderRadius: "12px",
              padding: "14px 18px",
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <label
                htmlFor="vibe-search-input"
                style={{
                  fontWeight: "bold",
                  fontSize: "0.95rem",
                  color: "#0f172a",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                🔍 Search by Meaning, Vibe, or Battle Role
              </label>

              <ButtonUI
                onClick={handleSeedDatabase}
                variant="default"
                disabled={isSeeding || isSearching}
              >
                {isSeeding ? "📥 Seeding..." : "📥 Seed PokéAPI Lore"}
              </ButtonUI>
            </div>

            {/* Input Bar */}
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                id="vibe-search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleExecuteSearch();
                  }
                }}
                placeholder="e.g. fiery lizard with high special attack..."
                style={{
                  flex: 1,
                  padding: "10px 14px",
                  fontSize: "0.95rem",
                  border: "2px solid #cbd5e1",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
              <ButtonUI
                onClick={() => handleExecuteSearch()}
                variant="action"
                showArrowPointer="right"
                disabled={isSearching || isSeeding}
              >
                {isSearching ? "Thinking..." : "Search"}
              </ButtonUI>
            </div>

            {/* Suggestion Chips */}
            <div style={{ marginTop: "10px", display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: "bold" }}>Try:</span>
              {PRESET_SEARCH_QUERIES.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => {
                    setSearchQuery(preset);
                    handleExecuteSearch(preset);
                  }}
                  style={{
                    background: "#f1f5f9",
                    border: "1px solid #cbd5e1",
                    borderRadius: "14px",
                    padding: "3px 10px",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                    color: "#334155",
                    transition: "all 0.15s ease",
                  }}
                >
                  "{preset}"
                </button>
              ))}
            </div>
          </div>

          {/* Status Alert Banner */}
          {statusMessage && (
            <div
              style={{
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#e0f2fe",
                border: "1px solid #7dd3fc",
                color: "#0369a1",
                fontSize: "0.85rem",
                fontWeight: "500",
              }}
            >
              ℹ️ {statusMessage}
            </div>
          )}

          {/* Search Results Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "12px",
            }}
          >
            {searchResults.map((result) => {
              // Convert cosine similarity score into percentage (0.35 -> ~80% relative vibe)
              // Calibrate raw vector similarity: scores > 0.35 represent top-tier matches (>85%)
              const rawScore = result.similarity_confidence_score;
              // Normalizes the meaningful 0.15 to 0.40 similarity range to a human-friendly 50% - 98%
              const matchPercentage = Math.min(
                99,
                Math.max(
                  20,
                  Math.round(
                    rawScore >= 0.35
                      ? 85 + ((rawScore - 0.35) / 0.15) * 14
                      : 50 + ((rawScore - 0.15) / 0.20) * 34
                  )
                )
              );
              
              return (
                <div
                  key={result.pokemon_id}
                  style={{
                    background: "#ffffff",
                    border: "2px solid #1e293b",
                    borderRadius: "10px",
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.04)",
                  }}
                >
                  {/* Card Header: Sprite + Name + Match Badge */}
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        width: "60px",
                        height: "60px",
                        background: "#f8fafc",
                        borderRadius: "8px",
                        border: "1px solid #e2e8f0",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {result.front_default_sprite_url ? (
                        <img
                          src={result.front_default_sprite_url}
                          alt={result.pokemon_name}
                          style={{ width: "56px", height: "56px", imageRendering: "pixelated" }}
                        />
                      ) : (
                        <span style={{ fontSize: "1.5rem" }}>👾</span>
                      )}
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: "bold", fontSize: "1rem", color: "#0f172a", textTransform: "capitalize" }}>
                          #{result.pokemon_id.toString().padStart(3, "0")} {result.pokemon_name}
                        </span>
                        <span
                          style={{
                            background: "#dcfce7",
                            color: "#15803d",
                            border: "1px solid #86efac",
                            borderRadius: "12px",
                            padding: "2px 8px",
                            fontSize: "0.75rem",
                            fontWeight: "bold",
                          }}
                        >
                          {matchPercentage}% Match 🟢
                        </span>
                      </div>

                      {/* Type Pills */}
                      <div style={{ display: "flex", gap: "4px", marginTop: "4px" }}>
                        {result.elemental_types.map((type) => (
                          <span
                            key={type}
                            style={{
                              background: "#e2e8f0",
                              color: "#1e293b",
                              borderRadius: "4px",
                              padding: "1px 6px",
                              fontSize: "0.7rem",
                              fontWeight: "bold",
                              textTransform: "uppercase",
                            }}
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Lore Snippet */}
                  <p
                    style={{
                      margin: "10px 0 8px 0",
                      fontSize: "0.82rem",
                      color: "#475569",
                      lineHeight: "1.5",
                      fontStyle: "italic",
                      background: "#f8fafc",
                      padding: "8px",
                      borderRadius: "6px",
                      borderLeft: "3px solid #3b82f6",
                    }}
                  >
                    "{result.matched_lore_snippet}"
                  </p>

                  {/* Micro Stats Bar */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "0.72rem",
                      color: "#64748b",
                      fontWeight: "bold",
                      borderTop: "1px solid #f1f5f9",
                      paddingTop: "6px",
                    }}
                  >
                    <span>HP: {result.base_stats.hp ?? result.base_stats.hit_points ?? "-"}</span>
                    <span>ATK: {result.base_stats.attack ?? "-"}</span>
                    <span>DEF: {result.base_stats.defense ?? "-"}</span>
                    <span>SPD: {result.base_stats.speed ?? "-"}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
};