/**
 * Retro Landing Title Screen Component
 * Renders the retro Game Boy Advance inspired landing experience for PokeAI Arena.
 * Dynamically fetches and displays configuration metadata directly from the backend referee.
 */

import React, { useEffect, useState, useCallback } from "react";
import type { GameMetadataResponse } from "../../types/metadata";
import { fetchStadiumGameMetadata } from "../../services/metadataService";
import { CharacterUI } from "../ui/CharacterUI";
import { ButtonUI } from "../ui/ButtonUI";

interface LandingTitleScreenProps {
  // Callback invoked when the player presses any key or clicks the start prompt
  onContinueToGame: (metadata: GameMetadataResponse) => void;
}

export const LandingTitleScreen: React.FC<LandingTitleScreenProps> = ({
  onContinueToGame,
}) => {
  // Local state tracking fetched stadium metadata
  const [stadiumMetadata, setStadiumMetadata] =
    useState<GameMetadataResponse | null>(null);

  // Local state tracking initial network request loading status
  const [isMetadataLoading, setIsMetadataLoading] = useState<boolean>(true);

  // Local state holding error details if the backend connection fails
  const [metadataRetrievalError, setMetadataRetrievalError] = useState<
    string | null
  >(null);

  // Fetches metadata from backend on mount or on manual retry
  const loadStadiumMetadata = useCallback(async () => {
    setIsMetadataLoading(true);
    setMetadataRetrievalError(null);
    try {
      // Execute the handshake request to the backend configuration endpoint
      const fetchedMetadata: GameMetadataResponse =
        await fetchStadiumGameMetadata();
      setStadiumMetadata(fetchedMetadata);
    } catch (networkError) {
      // Record error for display with diagnostic guidance
      const errorMessage: string =
        networkError instanceof Error
          ? networkError.message
          : "Unable to connect to the PokeAI Stadium backend.";
      setMetadataRetrievalError(errorMessage);
    } finally {
      setIsMetadataLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStadiumMetadata();
  }, [loadStadiumMetadata]);

  // Handle "Press Any Key to Continue" keyboard event listener
  useEffect(() => {
    const handleKeyDown = (_keyboardEvent: KeyboardEvent) => {
      // Ignore key events if metadata is still loading or has encountered an error
      if (!stadiumMetadata || isMetadataLoading) {
        return;
      }
      // Trigger the progression callback to transition to the next phase (Lesson 1 onboarding)
      onContinueToGame(stadiumMetadata);
    };

    // Attach global keyboard listener to the window
    window.addEventListener("keydown", handleKeyDown);

    // Clean up event listener when component unmounts to prevent memory leaks
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [stadiumMetadata, isMetadataLoading, onContinueToGame]);

  return (
    <div className="pokeai-viewport">
      {/* Retro Arcade Frame Container */}
      <div className="gba-screen-chassis">
        {/* Stadium Top Bar */}
        <header className="stadium-header-bar">
          <span className="stadium-indicator">● LIVE</span>
          <span className="stadium-env-tag">
            ENV: {stadiumMetadata?.application_environment.toUpperCase() || "CONNECTING..."}
          </span>
        </header>

        {/* Main Stage Content */}
        <main className="landing-stage">
          {/* Hero Branding */}
          <div className="title-logo-container">
            <h1 className="retro-title-text">
              {stadiumMetadata?.game_title || "PokeAI"}
            </h1>
            <div className="version-pill">
              VERSION {stadiumMetadata?.game_version || "0.1.0"}
            </div>
          </div>

          {/* Reusable Animated Character Mascot (Pikachu) */}
          <CharacterUI
            pokemonNationalPokedexId={25}
            characterAltDescription="Animated Pikachu Mascot"
            pixelDimensionSize={96}
            shouldDisplayPedestalShadow={true}
          />

          {/* Configuration & Mission Showcase */}
          {isMetadataLoading && (
            <div className="status-box loading-pulse">
              <p>📡 Handshaking with Stadium Backend Referee...</p>
              <span className="subtext">Reading backend/.env configuration</span>
            </div>
          )}

          {metadataRetrievalError && (
            <div className="status-box error-box">
              <p className="error-title">⚠️ Stadium Connection Alert</p>
              <p className="error-body">{metadataRetrievalError}</p>
              <p className="error-hint">
                Make sure the FastAPI server is running at <code>http://localhost:8000</code>!
              </p>
              <button
                type="button"
                className="retro-button-retry"
                onClick={loadStadiumMetadata}
              >
                🔄 Retry Handshake
              </button>
            </div>
          )}

          {stadiumMetadata && !isMetadataLoading && (
            <div className="metadata-manifest-card">
              <div className="manifest-section">
                <span className="manifest-label">MISSION GOAL</span>
                <p className="manifest-value">{stadiumMetadata.project_learning_goal}</p>
              </div>

              <div className="manifest-section">
                <span className="manifest-label">ARENA DESCRIPTION</span>
                <p className="manifest-value">{stadiumMetadata.game_description}</p>
              </div>

              <div className="manifest-footer-row">
                <div className="guide-preview-chip">
                  <span className="guide-chip-icon">🧢</span>
                  <span>Guide: <strong>{stadiumMetadata.game_guide_name}</strong></span>
                </div>
                <div className="status-online-chip">
                  <span className="online-dot"></span>
                  <span>FastAPI Referee Ready</span>
                </div>
              </div>
            </div>
          )}

          {/* Interactive Continue Prompt - Authentic Pokémon GBA Style */}
          {stadiumMetadata && !isMetadataLoading && (
            <ButtonUI
              onClick={() => onContinueToGame(stadiumMetadata)}
              variant="action"
              showArrowPointer="both"
              title="Click or press any key to enter the stadium"
            >
              PRESS ANY KEY TO CONTINUE
            </ButtonUI>
          )}
        </main>
      </div>
    </div>
  );
};
