/**
 * Player Name Input Screen Component
 * Allows the trainer to enter their name while Guide Shaneil guides them from the dialogue box.
 */

import React, { useState } from "react";
import { GameGuideDialogBox } from "../ui/GameGuideDialogBox";

export interface PlayerNameInputScreenProps {
  // Callback when trainer confirms their valid name
  onConfirmTrainerName: (trainerName: string) => void;

  // Callback to return back to previous step
  onBackToPreviousStep: () => void;

  // Dynamic Guide Name fetched from backend metadata
  guideName?: string;
}

export const PlayerNameInputScreen: React.FC<PlayerNameInputScreenProps> = ({
  onConfirmTrainerName,
  onBackToPreviousStep,
  guideName = "Shaneil",
}) => {
  // Input state for trainer name
  const [trainerNameInput, setTrainerNameInput] = useState<string>("");

  // Validation error message if input violates constraints
  const [inputValidationError, setInputValidationError] = useState<string>("");

  // Handler for form submission
  const handleSubmitTrainerName = (event?: React.FormEvent) => {
    if (event) {
      event.preventDefault();
    }

    const trimmedTrainerName = trainerNameInput.trim();

    if (trimmedTrainerName.length < 2) {
      setInputValidationError("Trainer name must be at least 2 characters long.");
      return;
    }

    if (trimmedTrainerName.length > 20) {
      setInputValidationError("Trainer name cannot exceed 20 characters.");
      return;
    }

    setInputValidationError("");
    onConfirmTrainerName(trimmedTrainerName);
  };

  return (
    <div className="pokeai-viewport">
      <div className="gba-screen-chassis">
        {/* Stadium Header Bar */}
        <header className="stadium-header-bar">
          <span className="stadium-indicator">● LESSON 1: TRAINER REGISTRATION</span>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              type="button"
              onClick={onBackToPreviousStep}
              className="stadium-env-tag"
              style={{ cursor: "pointer", border: "none", background: "#f1f5f9" }}
              title="Return to previous step"
            >
              ◀ BACK
            </button>
            <span className="stadium-env-tag">STEP 2 OF 3</span>
          </div>
        </header>

        {/* 50% / 50% Split Registration Stage */}
        <main className="landing-stage name-input-split-stage">
          {/* Left 50%: Trainer Name Registration Card */}
          <div className="name-input-left-column">
            <div className="name-input-card">
              <div className="title-badge-top">🪪 TRAINER CARD</div>
              <h2 style={{ margin: "10px 0", color: "var(--color-accent-blue)", fontSize: "1.3rem" }}>
                Register Your Trainer Name
              </h2>
              <p style={{ color: "var(--color-text-secondary)", marginBottom: "16px", fontSize: "0.95rem" }}>
                Please enter the name that will be announced on the stadium scoreboards.
              </p>

              <form onSubmit={handleSubmitTrainerName} style={{ width: "100%" }}>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={trainerNameInput}
                    onChange={(event) => {
                      setTrainerNameInput(event.target.value);
                      if (inputValidationError) setInputValidationError("");
                    }}
                    placeholder="e.g. Red_Champion"
                    maxLength={20}
                    className="trainer-name-text-input"
                    autoFocus
                  />
                </div>

                <div className="trainer-input-helper-row">
                  <span className="trainer-char-count">
                    {trainerNameInput.trim().length} / 20 characters
                  </span>
                  <span className="trainer-enter-prompt">
                    Press <kbd className="retro-key">↵ ENTER</kbd> to Confirm
                  </span>
                </div>

                {inputValidationError && (
                  <div style={{ color: "var(--color-accent-red)", marginTop: "8px", fontSize: "0.85rem" }}>
                    ⚠ {inputValidationError}
                  </div>
                )}
              </form>
            </div>
          </div>

          {/* Right 50%: Dedicated space for Shaneil's 420px sprite rising from behind dialogue box */}
          <div className="name-input-right-column" aria-hidden="true"></div>
        </main>

        {/* Right-Anchored Game Guide Dialogue Box with Guide Layered BEHIND */}
        <footer style={{ padding: "0 24px 20px 24px" }}>
          <GameGuideDialogBox
            characterName={guideName}
            dialogueMessage="Before I hand you your first partner monster, tell me—what is your name, Trainer? Type your name above and press Enter to confirm!"
            promptActionHint="[ Press Enter to Confirm ▸ ]"
            characterImagePlacement="right"
            characterImageHeightPixels={420}
            onAdvanceDialogue={() => handleSubmitTrainerName()}
          />
        </footer>
      </div>
    </div>
  );
};