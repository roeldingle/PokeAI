/**
 * App Root Component
 * Coordinates game stages: Title Screen -> Welcome -> Name Input -> Starter Select -> Registered -> AI Testbench
 */

import React, { useEffect, useState } from "react";
import { LandingTitleScreen } from "./components/screen/LandingTitleScreen";
import { PlayerNameInputScreen } from "./components/screen/PlayerNameInputScreen";
import { StarterSelectionScreen } from "./components/screen/StarterSelectionScreen";
import { AIGatewayTestbenchScreen } from "./components/screen/AIGatewayTestbenchScreen";
import { GameGuideDialogBox } from "./components/ui/GameGuideDialogBox";
import { ButtonUI } from "./components/ui/ButtonUI";
import { ProviderStatusBadge } from "./components/ui/ProviderStatusBadge";
import { fetchStadiumGameMetadata } from "./services/metadataService";
import { fetchGameGuideGreeting } from "./services/aiGatewayService";
import type { GameMetadataResponse } from "./types/metadata";
import type { TrainerProfileResponse } from "./types/onboarding";
import type { LLMResponseEnvelope } from "./types/aiGateway";

type GameStage =
  | "TITLE_SCREEN"
  | "GUIDE_WELCOME"
  | "NAME_INPUT"
  | "STARTER_SELECT"
  | "ONBOARDING_COMPLETE"
  | "AI_GATEWAY_TESTBENCH";

export const App: React.FC = () => {
  const [currentStage, setCurrentStage] = useState<GameStage>("TITLE_SCREEN");
  const [activeMetadata, setActiveMetadata] = useState<GameMetadataResponse | null>(null);
  const [confirmedTrainerName, setConfirmedTrainerName] = useState<string>("");
  const [registeredTrainerProfile, setRegisteredTrainerProfile] =
    useState<TrainerProfileResponse | null>(null);

  // Telemetry state for Lesson 02: AI Brain dynamic greeting
  const [aiGreetingEnvelope, setAiGreetingEnvelope] = useState<LLMResponseEnvelope | null>(null);
  const [isAiGreetingLoading, setIsAiGreetingLoading] = useState<boolean>(false);

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

  // When registration is confirmed, awaken the Game Guide's AI Brain with dynamic greeting
  useEffect(() => {
    if (currentStage === "ONBOARDING_COMPLETE" && registeredTrainerProfile && !aiGreetingEnvelope) {
      let isMounted = true;
      setIsAiGreetingLoading(true);

      async function triggerAIGreeting() {
        try {
          const envelope = await fetchGameGuideGreeting({
            trainer_name: registeredTrainerProfile!.trainer_name,
            selected_starter_id: registeredTrainerProfile!.selected_starter_monster.starter_pokemon_id,
            starter_monster_name: registeredTrainerProfile!.selected_starter_monster.monster_name,
            starter_elemental_type: registeredTrainerProfile!.selected_starter_monster.elemental_types[0] || "Normal",
          });
          if (isMounted) {
            setAiGreetingEnvelope(envelope);
          }
        } catch (err) {
          console.warn("Failed to generate AI greeting:", err);
        } finally {
          if (isMounted) {
            setIsAiGreetingLoading(false);
          }
        }
      }

      triggerAIGreeting();
      return () => {
        isMounted = false;
      };
    }
  }, [currentStage, registeredTrainerProfile, aiGreetingEnvelope]);

  const dynamicGuideName: string = activeMetadata?.game_guide_name || "Athena";

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

      {/* Stage 1: Guide Welcome */}
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

            <main className="landing-stage visual-novel-welcome-stage">
              <div className="welcome-hero-banner">
                <span className="welcome-tag-pill">{activeMetadata?.game_title || "POKEAI"} ARENA TOURNAMENT</span>
                <h1 className="welcome-hero-title">Meet Your Guide, {dynamicGuideName}</h1>
                <p className="welcome-hero-subtitle">
                  Welcome to the stadium! {dynamicGuideName} is preparing your official registration.
                </p>
              </div>
            </main>

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
            setAiGreetingEnvelope(null); // Reset for new greeting
            setCurrentStage("ONBOARDING_COMPLETE");
          }}
          onBackToNameInput={() => setCurrentStage("NAME_INPUT")}
        />
      )}

      {/* Stage 4: Registration Confirmed + Awakened AI Brain (Lesson 02) */}
      {currentStage === "ONBOARDING_COMPLETE" && registeredTrainerProfile && (
        <div className="pokeai-viewport">
          <div className="gba-screen-chassis">
            <header className="stadium-header-bar">
              <span className="stadium-indicator">● LESSON 2: AI BRAIN AWAKENED</span>
              <ProviderStatusBadge
                activeProvider={aiGreetingEnvelope?.active_provider_name}
                modelIdentifier={aiGreetingEnvelope?.model_identifier}
                latencyMilliseconds={aiGreetingEnvelope?.execution_latency_milliseconds}
                fallbackTriggered={aiGreetingEnvelope?.fallback_triggered}
                isLoading={isAiGreetingLoading}
              />
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

                  <div style={{ marginTop: "24px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <ButtonUI
                      onClick={() => setCurrentStage("AI_GATEWAY_TESTBENCH")}
                      variant="action"
                      showArrowPointer="right"
                    >
                      📡 Open Gateway Testbench
                    </ButtonUI>
                    <ButtonUI
                      onClick={() => setCurrentStage("TITLE_SCREEN")}
                      variant="default"
                      showArrowPointer="left"
                    >
                      Title Screen
                    </ButtonUI>
                  </div>
                </div>
              </div>
              <div className="name-input-right-column" aria-hidden="true" />
            </main>

            <footer style={{ padding: "0 24px 20px 24px" }}>
              <GameGuideDialogBox
                characterName={dynamicGuideName}
                highlightedTerm={registeredTrainerProfile.trainer_name}
                dialogueMessage={
                  isAiGreetingLoading
                    ? `Awakening AI radio channels to greet you...`
                    : aiGreetingEnvelope?.generated_message_content ||
                      `Registration complete! You and ${registeredTrainerProfile.selected_starter_monster.monster_name} make a formidable team!`
                }
                promptActionHint={
                  aiGreetingEnvelope
                    ? `[ Active: ${aiGreetingEnvelope.active_provider_name.toUpperCase()} | ⚡ ${aiGreetingEnvelope.execution_latency_milliseconds}ms ]`
                    : "[ Awakening AI Brain... ]"
                }
                characterImagePlacement="right"
              />
            </footer>
          </div>
        </div>
      )}

      {/* Stage 5: Gateway Testbench Screen (Storyboard Screen 1) */}
      {currentStage === "AI_GATEWAY_TESTBENCH" && (
        <AIGatewayTestbenchScreen
          onBackToPrevious={() => setCurrentStage("ONBOARDING_COMPLETE")}
        />
      )}
    </div>
  );
};

export default App;