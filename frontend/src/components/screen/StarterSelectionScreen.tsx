/**
 * Starter Selection Screen Component
 * Presents Bulbasaur, Charmander, and Squirtle with dynamic guide commentary and registration.
 * Allows quick click-to-select and Enter to confirm without redundant button clutter.
 */

import React, { useEffect, useState, useCallback } from "react";
import { CharacterUI } from "../ui/CharacterUI";
import { GameGuideDialogBox } from "../ui/GameGuideDialogBox";
import {
  fetchAvailableStarterMonsters,
  registerTrainerProfile,
} from "../../services/onboardingService";
import type {
  StarterMonsterInfo,
  TrainerProfileResponse,
} from "../../types/onboarding";

export interface StarterSelectionScreenProps {
  confirmedTrainerName: string;
  onRegistrationComplete: (registeredProfile: TrainerProfileResponse) => void;
  onBackToNameInput: () => void;
  guideName?: string;
}

export const StarterSelectionScreen: React.FC<StarterSelectionScreenProps> = ({
  confirmedTrainerName,
  onRegistrationComplete,
  onBackToNameInput,
  guideName = "Shaneil",
}) => {
  const [startersList, setStartersList] = useState<StarterMonsterInfo[]>([]);
  const [selectedStarterId, setSelectedStarterId] = useState<number>(4); // Default to Charmander
  const [isLoadingStarters, setIsLoadingStarters] = useState<boolean>(true);
  const [isRegisteringProfile, setIsRegisteringProfile] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    let isMounted = true;
    async function loadStarters() {
      try {
        const fetchedStarters = await fetchAvailableStarterMonsters();
        if (isMounted) {
          setStartersList(fetchedStarters);
          setIsLoadingStarters(false);
        }
      } catch (error) {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load starters.");
          setIsLoadingStarters(false);
        }
      }
    }
    loadStarters();
    return () => {
      isMounted = false;
    };
  }, []);

  // Compute dynamic dialogue based on selected starter
  const getGuideStarterCommentary = (): string => {
    switch (selectedStarterId) {
      case 1:
        return `Awesome choice, ${confirmedTrainerName}! Bulbasaur is balanced and sturdy with Grass and Poison types. Great defense against Water and Electric moves!`;
      case 4:
        return `Fiery pick, ${confirmedTrainerName}! Charmander has high Attack power and deals 2x damage against Grass and Bug types!`;
      case 7:
        return `Solid choice, ${confirmedTrainerName}! Squirtle possesses incredible Defense ratings and washes away Fire and Ground types!`;
      default:
        return `Take your time, ${confirmedTrainerName}! Click a partner monster above and press Enter to confirm!`;
    }
  };

  const handleConfirmStarterRegistration = useCallback(async () => {
    if (isRegisteringProfile || isLoadingStarters) return;
    setIsRegisteringProfile(true);
    setErrorMessage("");
    try {
      const registeredProfile = await registerTrainerProfile({
        trainer_name: confirmedTrainerName,
        selected_starter_id: selectedStarterId,
      });
      onRegistrationComplete(registeredProfile);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Registration failed. Please try again."
      );
      setIsRegisteringProfile(false);
    }
  }, [confirmedTrainerName, selectedStarterId, isRegisteringProfile, isLoadingStarters, onRegistrationComplete]);

  // Keyboard shortcut listener: Press ENTER to confirm selection
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter") {
        event.preventDefault();
        handleConfirmStarterRegistration();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleConfirmStarterRegistration]);

  return (
    <div className="pokeai-viewport">
      <div className="gba-screen-chassis">
        {/* Stadium Header Bar with highlighted player name and quick back navigation */}
        <header className="stadium-header-bar">
          <span className="stadium-indicator">
            <span className="stadium-indicator-dot">●</span>
            <span>LESSON 1: CHOOSE YOUR POKEMON, TRAINER</span>
            <span className="trainer-name-highlight-badge">{confirmedTrainerName}</span>
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
            <button
              type="button"
              onClick={onBackToNameInput}
              className="stadium-env-tag"
              style={{ cursor: "pointer", border: "none", background: "#f1f5f9" }}
              title="Return to name input"
            >
              ◀ BACK
            </button>
            <span className="stadium-env-tag">STEP 3 OF 3</span>
          </div>
        </header>

        {/* Central Selection Stage: Cards on Left (68%), Guide on Right (32%) */}
        <main className="landing-stage starter-selection-split-stage">
          {/* Left Column: 3 Starter Cards */}
          <div className="starter-cards-column">
            {isLoadingStarters ? (
              <div className="status-box">Loading stadium starter catalog...</div>
            ) : errorMessage ? (
              <div className="status-box error-box">
                <div className="error-title">Starter Selection Error</div>
                <div className="error-body">{errorMessage}</div>
              </div>
            ) : (
              <div className="starters-card-grid-compact">
                {startersList.map((starter) => {
                  const isSelected = starter.starter_pokemon_id === selectedStarterId;
                  return (
                    <div
                      key={starter.starter_pokemon_id}
                      className={`starter-choice-card ${isSelected ? "starter-card-selected" : ""}`}
                      onClick={() => setSelectedStarterId(starter.starter_pokemon_id)}
                      role="button"
                      tabIndex={0}
                      title={`Click to select ${starter.monster_name}`}
                      onKeyDown={(event) => {
                        if (event.key === " " || event.key === "Enter") {
                          setSelectedStarterId(starter.starter_pokemon_id);
                        }
                      }}
                    >
                      <div className="starter-card-header">
                        <span className="starter-pokedex-number">
                          #{String(starter.starter_pokemon_id).padStart(3, "0")}
                        </span>
                        <span className="starter-card-name">{starter.monster_name}</span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "center", margin: "8px 0" }}>
                        <CharacterUI
                          pokemonNationalPokedexId={starter.starter_pokemon_id}
                          pixelDimensionSize={76}
                          shouldDisplayPedestalShadow={true}
                        />
                      </div>

                      <div className="starter-type-badges">
                        {starter.elemental_types.map((elementalType) => (
                          <span key={elementalType} className={`type-badge type-${elementalType.toLowerCase()}`}>
                            {elementalType}
                          </span>
                        ))}
                      </div>

                      <div className="starter-stat-summary">
                        <div>HP: {starter.base_hit_points}</div>
                        <div>ATK: {starter.base_attack_power}</div>
                        <div>DEF: {starter.base_defense_rating}</div>
                        <div>SPD: {starter.base_speed_velocity}</div>
                      </div>

                      {isSelected && (
                        <div className="starter-selected-pill">
                          ★ SELECTED
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Dedicated space so the Guide does not overlap Squirtle or any card */}
          <div className="starter-guide-spacer-column" aria-hidden="true"></div>
        </main>

        {/* Bottom Dialogue Box with character sprite rising cleanly in the right space */}
        <footer style={{ padding: "0 24px 20px 24px" }}>
          <GameGuideDialogBox
            characterName={guideName}
            dialogueMessage={getGuideStarterCommentary()}
            highlightedTerm={confirmedTrainerName}
            promptActionHint={
              isRegisteringProfile
                ? "[ Registering Partner... ]"
                : "[ Press Enter to Confirm Partner ▸ ]"
            }
            characterImagePlacement="right"
            characterImageHeightPixels={360}
            onAdvanceDialogue={handleConfirmStarterRegistration}
          />
        </footer>
      </div>
    </div>
  );
};
