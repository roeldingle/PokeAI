/**
 * Reusable Game Guide Dialogue Box Component
 * Authentic JRPG / Visual Novel style dialogue box with character portrait overlay and typewriter text streaming.
 * Supports configurable typing speed, skip-to-end on click, dynamic guide nameplate, and customizable sprite overlay.
 */

import React, { useEffect, useState, useRef } from "react";
import defaultShaneilCharacterImage from "../../assets/guide_character.png";

export type CharacterPlacement = "right" | "left" | "none";

export interface GameGuideDialogBoxProps {
  // Full spoken narrative commentary delivered by the character
  dialogueMessage: string;

  // Name displayed on the floating nameplate badge (defaults to "SHANEIL")
  characterName?: string;

  // Optional character portrait image URL or imported asset (defaults to Shaneil)
  characterImageUrl?: string;

  // Placement of character image overlay: "right", "left", or "none" (defaults to "right")
  characterImagePlacement?: CharacterPlacement;

  // Visual prompt hint shown in the bottom corner (e.g. "[ Press A to Next ▸ ]")
  promptActionHint?: string;

  // Optional click or keypress handler when player advances dialogue
  onAdvanceDialogue?: () => void;

  // Optional custom character image height in pixels (defaults to 420)
  characterImageHeightPixels?: number;

  // Speed in milliseconds per character for the typewriter effect (defaults to 20ms)
  typingSpeedMilliseconds?: number;

  // Flag to enable or bypass the typewriter streaming animation (defaults to true)
  enableTypewriterEffect?: boolean;

  // Optional player name or phrase to highlight inline within the dialogue speech
  highlightedTerm?: string;

  // Optional extra CSS classes for layout adjustments
  additionalContainerClassName?: string;
}

export const GameGuideDialogBox: React.FC<GameGuideDialogBoxProps> = ({
  dialogueMessage,
  characterName = "SHANEIL",
  characterImageUrl = defaultShaneilCharacterImage,
  characterImagePlacement = "right",
  promptActionHint = "[ Press Enter to Continue ▸ ]",
  onAdvanceDialogue,
  characterImageHeightPixels = 420,
  typingSpeedMilliseconds = 20,
  enableTypewriterEffect = true,
  highlightedTerm,
  additionalContainerClassName = "",
}) => {
  // Current visible text revealed by the typewriter streamer
  const [displayedDialogueText, setDisplayedDialogueText] = useState<string>(
    enableTypewriterEffect ? "" : dialogueMessage
  );

  // Tracks whether the current sentence has finished typing out completely
  const [isTypewriterComplete, setIsTypewriterComplete] = useState<boolean>(
    !enableTypewriterEffect
  );

  // Mutable reference tracking active interval timer to guarantee clean unmounting
  const typingIntervalTimerReference = useRef<number | null>(null);

  // Typewriter streaming effect triggered whenever the target dialogue message changes
  useEffect(() => {
    // If typewriter effect is disabled, display full text immediately
    if (!enableTypewriterEffect) {
      setDisplayedDialogueText(dialogueMessage);
      setIsTypewriterComplete(true);
      return;
    }

    // Reset typewriter state for the new sentence
    setDisplayedDialogueText("");
    setIsTypewriterComplete(false);

    let currentCharacterIndexPointer = 0;
    const totalMessageCharacterCount = dialogueMessage.length;

    // Clear any existing active timer to prevent overlapping stream loops
    if (typingIntervalTimerReference.current !== null) {
      window.clearInterval(typingIntervalTimerReference.current);
    }

    // Create tick interval that progressively unveils characters one by one
    typingIntervalTimerReference.current = window.setInterval(() => {
      currentCharacterIndexPointer += 1;

      // Slice message up to current pointer position
      setDisplayedDialogueText(
        dialogueMessage.slice(0, currentCharacterIndexPointer)
      );

      // Once the full string is revealed, terminate timer and mark as complete
      if (currentCharacterIndexPointer >= totalMessageCharacterCount) {
        if (typingIntervalTimerReference.current !== null) {
          window.clearInterval(typingIntervalTimerReference.current);
          typingIntervalTimerReference.current = null;
        }
        setIsTypewriterComplete(true);
      }
    }, typingSpeedMilliseconds);

    // Cleanup interval timer on component unmount or when dialogueMessage changes
    return () => {
      if (typingIntervalTimerReference.current !== null) {
        window.clearInterval(typingIntervalTimerReference.current);
        typingIntervalTimerReference.current = null;
      }
    };
  }, [dialogueMessage, typingSpeedMilliseconds, enableTypewriterEffect]);

  // Handle player advance interaction (dual-action: skip-typing if streaming, advance if done)
  const handleUserDialogueInteraction = () => {
    // If still typing, clicking instantly reveals the entire message (JRPG skip-to-end standard)
    if (!isTypewriterComplete) {
      if (typingIntervalTimerReference.current !== null) {
        window.clearInterval(typingIntervalTimerReference.current);
        typingIntervalTimerReference.current = null;
      }
      setDisplayedDialogueText(dialogueMessage);
      setIsTypewriterComplete(true);
      return;
    }

    // If already fully typed, advance to next stage or trigger callback
    onAdvanceDialogue?.();
  };

  // Global keyboard listener so pressing Enter anywhere on the screen skips typing or advances dialogue
  useEffect(() => {
    const handleGlobalKeyDown = (keyboardEvent: KeyboardEvent) => {
      // Do not intercept Enter if the user is typing inside an input or textarea
      const activeElementTag = document.activeElement?.tagName.toLowerCase();
      if (activeElementTag === "input" || activeElementTag === "textarea") {
        return;
      }

      if (keyboardEvent.key === "Enter") {
        keyboardEvent.preventDefault();
        if (!isTypewriterComplete) {
          if (typingIntervalTimerReference.current !== null) {
            window.clearInterval(typingIntervalTimerReference.current);
            typingIntervalTimerReference.current = null;
          }
          setDisplayedDialogueText(dialogueMessage);
          setIsTypewriterComplete(true);
        } else {
          onAdvanceDialogue?.();
        }
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => {
      window.removeEventListener("keydown", handleGlobalKeyDown);
    };
  }, [isTypewriterComplete, dialogueMessage, onAdvanceDialogue]);

  // Keyboard accessibility handler for standard Game Boy / JRPG keys (Enter, Space, A)
  const handleKeyDown = (keyboardEvent: React.KeyboardEvent<HTMLDivElement>) => {
    if (
      keyboardEvent.key === "Enter" ||
      keyboardEvent.key === " " ||
      keyboardEvent.key === "a" ||
      keyboardEvent.key === "A"
    ) {
      keyboardEvent.preventDefault();
      handleUserDialogueInteraction();
    }
  };

  // Determine if character image should be rendered
  const shouldRenderCharacterSprite: boolean =
    characterImagePlacement !== "none" && Boolean(characterImageUrl);

    // Render displayed text with optional highlighted player name badge (case-insensitive)
    const renderHighlightedDialogueText = () => {
      if (!highlightedTerm || !highlightedTerm.trim()) {
        return displayedDialogueText;
      }

      // Escape special regex characters in the trainer moniker
      const escapedMoniker = highlightedTerm.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(`(${escapedMoniker})`, "gi");

      if (!regex.test(displayedDialogueText)) {
        return displayedDialogueText;
      }

      const segments = displayedDialogueText.split(regex);
      return segments.map((segment, index) => {
        if (segment.toLowerCase() === highlightedTerm.trim().toLowerCase()) {
          return (
            <span key={index} className="dialogue-trainer-highlight">
              {segment}
            </span>
          );
        }
        return <React.Fragment key={index}>{segment}</React.Fragment>;
      });
    };

  return (
    <div
      className={`dialogue-box-wrapper placement-${characterImagePlacement} ${additionalContainerClassName}`}
    >
      {/* Character Sprite Overlay (Elevated on stage, layered behind dialogue box) */}
      {shouldRenderCharacterSprite && (
        <div
          className={`dialogue-character-overlay overlay-${characterImagePlacement}`}
          aria-hidden="true"
        >
          <img
            src={characterImageUrl}
            alt={`${characterName} Guide Sprite`}
            className="dialogue-character-sprite"
            style={{ height: `${characterImageHeightPixels}px` }}
          />
        </div>
      )}

      {/* Primary Semi-Translucent Frosted Dialogue Chassis */}
      <div
        className="dialogue-frame-chassis"
        onClick={handleUserDialogueInteraction}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        title={
          isTypewriterComplete
            ? "Click or press A / Enter to continue"
            : "Click to reveal full text"
        }
      >
        {/* Floating Tactile Nameplate Badge */}
        {characterName && (
          <div className="dialogue-nameplate-badge">
            <span className="nameplate-gem">💎</span>
            <span className="nameplate-name">{characterName}</span>
          </div>
        )}

        {/* Dialogue Speech & Action Hint Area */}
        <div className="dialogue-speech-content">
          <p className="dialogue-speech-text">
            {renderHighlightedDialogueText()}
            {/* Blinking typewriter cursor shown while active typing is underway */}
            {!isTypewriterComplete && (
              <span className="typewriter-active-cursor">▌</span>
            )}
          </p>

          {/* Action prompt indicator shown once message is fully revealed */}
          {promptActionHint && isTypewriterComplete && (
            <div className="dialogue-action-hint">
              <span className="blinking-prompt">{promptActionHint}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
