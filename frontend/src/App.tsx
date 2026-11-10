/**
 * App Root Component
 * Coordinates the active stage in PokeAI Arena:
 * - Stage 0: Landing Title Screen (.env configuration display & handshake)
 * - Stage 1+: Onboarding with Guide Shaneil & Battle Arena
 */

import React, { useState } from "react";
import { LandingTitleScreen } from "./components/screen/LandingTitleScreen";
import { ButtonUI } from "./components/ui/ButtonUI";
import type { GameMetadataResponse } from "./types/metadata";

// Enumeration of high-level game stages
type GameStage = "TITLE_SCREEN" | "GUIDE_ONBOARDING_PREVIEW";

export const App: React.FC = () => {
  // Active stage within our game state machine
  const [currentStage, setCurrentStage] = useState<GameStage>("TITLE_SCREEN");

  // Cached metadata received from the successful Lesson 0 backend handshake
  const [activeMetadata, setActiveMetadata] =
    useState<GameMetadataResponse | null>(null);

  // Transition handler when player advances past the landing screen
  const handleProceedFromTitleScreen = (metadata: GameMetadataResponse) => {
    setActiveMetadata(metadata);
    setCurrentStage("GUIDE_ONBOARDING_PREVIEW");
  };

  // Handler to return back to title screen
  const handleReturnToTitle = () => {
    setCurrentStage("TITLE_SCREEN");
  };

  return (
    <div className="pokeai-root-container">
      {currentStage === "TITLE_SCREEN" && (
        <LandingTitleScreen onContinueToGame={handleProceedFromTitleScreen} />
      )}

      {currentStage === "GUIDE_ONBOARDING_PREVIEW" && (
        <div className="pokeai-viewport">
          <div className="gba-screen-chassis">
            <header className="stadium-header-bar">
              <span className="stadium-indicator">● LESSON 0 COMPLETE</span>
              <span className="stadium-env-tag">GATEWAY READY</span>
            </header>

            <main className="landing-stage">
              <div className="metadata-manifest-card">
                <div className="title-badge-top">NEXT MILESTONE</div>
                <h2 style={{ margin: "8px 0", color: "var(--color-accent-blue)", fontSize: "1.4rem" }}>
                  Ready for Lesson 1: Guide {activeMetadata?.game_guide_name}
                </h2>
                <p style={{ color: "var(--color-text-secondary)", lineHeight: "1.6" }}>
                  Configuration handshake verified! In Lesson 1, Guide{" "}
                  <strong>{activeMetadata?.game_guide_name}</strong> will take the right-side stage
                  to welcome the trainer and present the starter monsters.
                </p>

                <div style={{ marginTop: "24px" }}>
                  <ButtonUI
                    onClick={handleReturnToTitle}
                    showArrowPointer="left"
                    variant="default"
                  >
                    Back to Title Screen
                  </ButtonUI>
                </div>
              </div>
            </main>


          </div>
        </div>
      )}
    </div>
  );
};

export default App;
