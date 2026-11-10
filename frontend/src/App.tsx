/**
 * App Root Component
 * Coordinates game stages: Title Screen -> Welcome -> Name Input -> Starter Select -> Registered
 */

import React, { useEffect, useState } from "react";
import { LandingTitleScreen } from "./components/screen/LandingTitleScreen";
import { PlayerNameInputScreen } from "./components/screen/PlayerNameInputScreen";
import { StarterSelectionScreen } from "./components/screen/StarterSelectionScreen";
import { GameGuideDialogBox } from "./components/ui/GameGuideDialogBox";
import { ButtonUI } from "./components/ui/ButtonUI";
import { fetchStadiumGameMetadata } from "./services/metadataService";
import type { GameMetadataResponse } from "./types/metadata";
import type { TrainerProfileResponse } from "./types/onboarding";

type GameStage =
  | "TITLE_SCREEN"
  | "GUIDE_WELCOME"
  | "NAME_INPUT"
  | "STARTER_SELECT"
  | "ONBOARDING_COMPLETE";

export const App: React.FC = () => {
  const [currentStage, setCurrentStage] = useState<GameStage>("TITLE_SCREEN");
  const [activeMetadata, setActiveMetadata] = useState<GameMetadataResponse | null>(null);
  const [confirmedTrainerName, setConfirmedTrainerName] = useState<string>("");
  const [registeredTrainerProfile, setRegisteredTrainerProfile] =
    useState<TrainerProfileResponse | null>(null);

  // Preload stadium metadata on mount so Guide name is always dynamic
  useEffect(() => {
    let isMounted = true;
    async function preloadStadiumMetadata() {
      try {
        const metadata = await fetchStadiumGameMetadata();
        if (isMounted) {
          setActiveMetadata(metadata);
        }
      } catch (error) {
        console.warn("Preloading metadata in App:", error);
      }
    }
    preloadStadiumMetadata();
    return () => {
      isMounted = false;
    };
  }, []);

  // Dynamically resolved guide name from backend metadata
  const dynamicGuideName: string = activeMetadata?.game_guide_name || "Shaneil";

  return (
    <div className="pokeai-root-container">
      {/* Stage 0: Title Screen */}
      {currentStage === "TITLE_SCREEN" && (
        <LandingTitleScreen
          onContinueToGame={(metadata) => {
            setActiveMetadata(metadata);
            setCurrentStage("GUIDE_WELCOME");
          }}
        />
      )}

      {/* Stage 1: Guide Shaneil Welcome (Visual Novel Style - No Welcome Card) */}
      {currentStage === "GUIDE_WELCOME" && (
        <div className="pokeai-viewport">
          <div className="gba-screen-chassis">
            <header className="stadium-header-bar">
              <span className="stadium-indicator">● LESSON 1: TOURNAMENT REGISTRATION</span>
              <button
                type="button"
                onClick={() => setCurrentStage("TITLE_SCREEN")}
                className="stadium-env-tag"
                style={{ cursor: "pointer", border: "none", background: "#f1f5f9" }}
                title="Return to Title Screen"
              >
                ◀ TITLE SCREEN
              </button>
            </header>

            {/* Open Visual Novel Stage (Card Removed) */}
            <main className="landing-stage visual-novel-welcome-stage">
              <div className="welcome-hero-banner">
                <span className="welcome-tag-pill">{activeMetadata?.game_title || "POKEAI"} ARENA TOURNAMENT</span>
                <h1 className="welcome-hero-title">Meet Your Guide, {activeMetadata?.game_guide_name || "Shaneil"}</h1>
                <p className="welcome-hero-subtitle">
                  Welcome to the stadium! {activeMetadata?.game_guide_name || "Shaneil"} is preparing your official registration.
                </p>
              </div>
            </main>

            {/* Bottom JRPG Dialogue Box with Shaneil Rising from Behind */}
            <footer style={{ padding: "0 24px 20px 24px" }}>
              <GameGuideDialogBox
                characterName={dynamicGuideName}
                dialogueMessage={`Hello there, Trainer! Welcome to the world of PokeAI! I'm ${dynamicGuideName}, your Head Battle Guide! Before you step onto the battlefield, let's get you registered for the tournament!`}
                promptActionHint="[ Press Enter to Continue ▸ ]"
                characterImagePlacement="right"
                characterImageHeightPixels={420}
                onAdvanceDialogue={() => setCurrentStage("NAME_INPUT")}
              />
            </footer>
          </div>
        </div>
      )}

      {/* Stage 2: Trainer Name Input */}
      {currentStage === "NAME_INPUT" && (
        <PlayerNameInputScreen
          guideName={dynamicGuideName}
          onConfirmTrainerName={(trainerName) => {
            setConfirmedTrainerName(trainerName);
            setCurrentStage("STARTER_SELECT");
          }}
          onBackToPreviousStep={() => setCurrentStage("GUIDE_WELCOME")}
        />
      )}

      {/* Stage 3: Starter Selection */}
      {currentStage === "STARTER_SELECT" && (
        <StarterSelectionScreen
          guideName={dynamicGuideName}
          confirmedTrainerName={confirmedTrainerName}
          onRegistrationComplete={(profile) => {
            setRegisteredTrainerProfile(profile);
            setCurrentStage("ONBOARDING_COMPLETE");
          }}
          onBackToNameInput={() => setCurrentStage("NAME_INPUT")}
        />
      )}

      {/* Stage 4: Onboarding Complete & Ready for Lesson 2 (AI Gateway Brain) */}
      {currentStage === "ONBOARDING_COMPLETE" && registeredTrainerProfile && (
        <div className="pokeai-viewport">
          <div className="gba-screen-chassis">
            <header className="stadium-header-bar">
              <span className="stadium-indicator">● LESSON 1 COMPLETE</span>
              <span className="stadium-env-tag">TRAINER ID: {registeredTrainerProfile.trainer_registration_id}</span>
            </header>

            <main className="landing-stage name-input-split-stage">
              <div className="name-input-left-column">
                <div className="name-input-card">
                  <div className="title-badge-top">REGISTRATION CONFIRMED</div>
                  <h2 style={{ margin: "10px 0", color: "var(--color-accent-green)", fontSize: "1.4rem" }}>
                    Trainer Card Registered!
                  </h2>
                  <p style={{ color: "var(--color-text-secondary)", lineHeight: "1.8" }}>
                    Welcome to the stadium,{" "}
                    <span className="trainer-name-highlight-badge">
                      {registeredTrainerProfile.trainer_name}
                    </span>
                    ! Your partner monster{" "}
                    <strong>{registeredTrainerProfile.selected_starter_monster.monster_name}</strong> is registered and ready.
                  </p>

                  <div style={{ marginTop: "24px" }}>
                    <ButtonUI onClick={() => setCurrentStage("TITLE_SCREEN")} variant="default" showArrowPointer="left">
                      Back to Title Screen
                    </ButtonUI>
                  </div>
                </div>
              </div>
              <div className="name-input-right-column" aria-hidden="true" />
            </main>

            <footer style={{ padding: "0 24px 20px 24px" }}>
              <GameGuideDialogBox
                characterName={dynamicGuideName}
                dialogueMessage={`Registration complete! You and ${registeredTrainerProfile.selected_starter_monster.monster_name} make a formidable team! Next up: Awakening my AI Brain in Lesson 2!`}
                promptActionHint="[ Lesson 1 Complete ★ ]"
                characterImagePlacement="right"
              />
            </footer>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;