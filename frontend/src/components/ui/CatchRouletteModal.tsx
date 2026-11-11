/**
 * Catch Roulette Modal Component (Lesson 7)
 * Renders the retro arcade Pokéball Roulette Wheel triggered when the 5-turn clock
 * expires without a knockout.
 *
 * Sequence of events:
 * 1. 'READY': Displays the 4 Pokéball tiers (Gold 90%, Silver 75%, Bronze 60%, Normal 50%).
 * 2. 'SPINNING': The selector cycles rapidly through tiers while the backend calculates the roll.
 * 3. 'LANDED': The wheel locks onto the selected Pokéball tier with high-contrast stadium glow.
 * 4. 'WOBBLING': The thrown Pokéball shakes through 3 suspenseful wobbles on the stadium floor.
 * 5. 'RESULT': Displays capture confirmation ("CLICK! ⭐ Gotcha!") or breakout ("BURST! 💨 Fled!"),
 *    updating the party pool and passing the result back to BattleArenaScreen.
 */

import React, { useEffect, useRef, useState } from "react";
import { ButtonUI } from "./ButtonUI";
import { spinCatchRoulette } from "../../services/battleService";
import type {
  CatchRouletteOutcome,
  PokeballTier,
} from "../../types/battle";

// Metadata defining visual attributes for each of the 4 Pokéball tiers
interface PokeballTierDisplayConfig {
  tier: PokeballTier;
  displayName: string;
  catchProbabilityPercentage: number;
  wheelWeightPercentage: number;
  iconSymbol: string;
  cardBorderColor: string;
  badgeBackgroundColor: string;
  badgeTextColor: string;
  description: string;
}

// Canonical tier list ordered as they appear on the retro carousel
const POKEBALL_TIERS_CONFIG: PokeballTierDisplayConfig[] = [
  {
    tier: "GOLD",
    displayName: "Gold Pokéball",
    catchProbabilityPercentage: 90,
    wheelWeightPercentage: 10,
    iconSymbol: "🟡",
    cardBorderColor: "#eab308",
    badgeBackgroundColor: "#fef08a",
    badgeTextColor: "#854d0e",
    description: "Legendary Gold Tier — Ultra-high capture probability!",
  },
  {
    tier: "SILVER",
    displayName: "Silver Pokéball",
    catchProbabilityPercentage: 75,
    wheelWeightPercentage: 25,
    iconSymbol: "⚪",
    cardBorderColor: "#94a3b8",
    badgeBackgroundColor: "#e2e8f0",
    badgeTextColor: "#334155",
    description: "Reinforced Silver Tier — Excellent 75% capture rate.",
  },
  {
    tier: "BRONZE",
    displayName: "Bronze Pokéball",
    catchProbabilityPercentage: 60,
    wheelWeightPercentage: 35,
    iconSymbol: "🟤",
    cardBorderColor: "#b45309",
    badgeBackgroundColor: "#fed7aa",
    badgeTextColor: "#7c2d12",
    description: "Heavy Bronze Tier — Dependable 60% capture rate.",
  },
  {
    tier: "NORMAL",
    displayName: "Normal Pokéball",
    catchProbabilityPercentage: 50,
    wheelWeightPercentage: 30,
    iconSymbol: "🔴",
    cardBorderColor: "#ef4444",
    badgeBackgroundColor: "#fee2e2",
    badgeTextColor: "#991b1b",
    description: "Classic Crimson Tier — Standard 50% coin-flip odds.",
  },
];

interface CatchRouletteModalProps {
  isOpen: boolean;
  trainerName: string;
  opponentMonsterName: string;
  opponentPokemonId: number;
  opponentSpriteUrl: string;
  opponentLevel: number;
  onCatchResolved: (catchOutcome: CatchRouletteOutcome) => void;
  onCloseModal: () => void;
}

// Lifecycle phases for the interactive overtime capture sequence
type RouletteModalPhase = "READY" | "SPINNING" | "LANDED" | "WOBBLING" | "RESULT";

export const CatchRouletteModal: React.FC<CatchRouletteModalProps> = ({
  isOpen,
  trainerName,
  opponentMonsterName,
  opponentPokemonId,
  opponentSpriteUrl,
  opponentLevel,
  onCatchResolved,
  onCloseModal,
}) => {
  // Phase state machine driving the visual sequence
  const [modalPhase, setModalPhase] = useState<RouletteModalPhase>("READY");
  // Index of the currently highlighted tier card during spinning (0 to 3)
  const [highlightedTierIndex, setHighlightedTierIndex] = useState<number>(0);
  // Resolved outcome returned by backend API
  const [finalOutcome, setFinalOutcome] = useState<CatchRouletteOutcome | null>(null);
  // Wobble step counter (1 = left, 2 = right, 3 = center snap, 4 = final resolution)
  const [wobbleStep, setWobbleStep] = useState<number>(0);
  // Status message displayed in the live stadium ticker
  const [statusNarrationText, setStatusNarrationText] = useState<string>(
    "⏱️ 5-Turn Clock Expired! Spin the roulette wheel to select your Pokéball!"
  );
  // Loading and error states
  const [isSpinRequestPending, setIsSpinRequestPending] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Interval reference for spinning carousel
  const carouselIntervalRef = useRef<number | null>(null);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (carouselIntervalRef.current) {
        clearInterval(carouselIntervalRef.current);
      }
    };
  }, []);

  // Reset modal state whenever opened
  useEffect(() => {
    if (isOpen) {
      setModalPhase("READY");
      setHighlightedTierIndex(0);
      setFinalOutcome(null);
      setWobbleStep(0);
      setErrorMessage(null);
      setStatusNarrationText(
        `⏱️ 5-Turn Clock Expired! Wild ${opponentMonsterName} is preparing to flee! SPIN THE ROULETTE!`
      );
    }
  }, [isOpen, opponentMonsterName]);

  // If modal is closed, render nothing
  if (!isOpen) return null;

  /**
   * Triggers the spinning wheel animation and calls the backend catch endpoint.
   */
  const handleTriggerSpin = async () => {
    if (modalPhase !== "READY" || isSpinRequestPending) return;

    setIsSpinRequestPending(true);
    setModalPhase("SPINNING");
    setErrorMessage(null);
    setStatusNarrationText("🎰 The roulette wheel is spinning rapidly across all 4 Pokéball tiers...");

    // Start high-speed carousel cycling (changes active card every 80ms)
    let currentCarouselIndex = 0;
    carouselIntervalRef.current = window.setInterval(() => {
      currentCarouselIndex = (currentCarouselIndex + 1) % POKEBALL_TIERS_CONFIG.length;
      setHighlightedTierIndex(currentCarouselIndex);
    }, 80);

    try {
      // Dispatch asynchronous request to backend roulette engine
      const outcomeResult = await spinCatchRoulette({
        trainer_name: trainerName,
        opponent_pokemon_id: opponentPokemonId,
        opponent_pokemon_name: opponentMonsterName,
        opponent_pokemon_sprite_url: opponentSpriteUrl,
        opponent_level: opponentLevel,
      });

      // Find the index of the tier landed upon
      const targetTierIndex = POKEBALL_TIERS_CONFIG.findIndex(
        (configItem) => configItem.tier === outcomeResult.selected_pokeball_tier
      );
      const resolvedTierIndex = targetTierIndex >= 0 ? targetTierIndex : 0;

      // Allow the wheel to spin visibly for at least 1.6 seconds for suspense
      setTimeout(() => {
        // Clear the high-speed interval
        if (carouselIntervalRef.current) {
          clearInterval(carouselIntervalRef.current);
          carouselIntervalRef.current = null;
        }

        // Lock onto the exact target tier
        setHighlightedTierIndex(resolvedTierIndex);
        setFinalOutcome(outcomeResult);
        setModalPhase("LANDED");

        const targetConfig = POKEBALL_TIERS_CONFIG[resolvedTierIndex];
        setStatusNarrationText(
          `🎯 The wheel landed on ${targetConfig.displayName}! (${targetConfig.catchProbabilityPercentage}% Catch Rate) Throwing Pokéball!`
        );

        // Transition to throwing and 3-wobble sequence after 900ms pause
        setTimeout(() => {
          setModalPhase("WOBBLING");
          executeWobbleSequence(outcomeResult);
        }, 900);
      }, 1600);
    } catch (apiError) {
      if (carouselIntervalRef.current) {
        clearInterval(carouselIntervalRef.current);
        carouselIntervalRef.current = null;
      }
      setErrorMessage(
        apiError instanceof Error
          ? apiError.message
          : "An unexpected error occurred during the roulette spin."
      );
      setModalPhase("READY");
    } finally {
      setIsSpinRequestPending(false);
    }
  };

  /**
   * Orchestrates the 3 iconic retro Pokéball wobbles and resolves the catch outcome.
   */
  const executeWobbleSequence = (outcome: CatchRouletteOutcome) => {
    // Wobble 1: Tilts left
    setWobbleStep(1);
    setStatusNarrationText("Wobble 1... The Pokéball trembles on the stadium turf!");

    // Wobble 2: Tilts right (after 700ms)
    setTimeout(() => {
      setWobbleStep(2);
      setStatusNarrationText("Wobble 2... The tension in the arena is electric!");

      // Wobble 3: Snaps center (after 700ms)
      setTimeout(() => {
        setWobbleStep(3);
        setStatusNarrationText("Wobble 3... Click or burst?!");

        // Final resolution: Click / Burst (after 700ms)
        setTimeout(() => {
          setWobbleStep(4);
          setModalPhase("RESULT");

          if (outcome.capture_successful) {
            setStatusNarrationText(
              `⭐ GOTCHA! Wild ${opponentMonsterName} was caught! Added to your trainer party pool!`
            );
          } else {
            setStatusNarrationText(
              `💨 BURST! Oh no! Wild ${opponentMonsterName} broke free and fled into the wild!`
            );
          }
        }, 700);
      }, 700);
    }, 700);
  };

  /**
   * Finalizes the roulette sequence and passes the outcome to the parent battle arena.
   */
  const handleProceedToDebrief = () => {
    if (finalOutcome) {
      onCatchResolved(finalOutcome);
    }
    onCloseModal();
  };

  // Retrieve active tier configuration based on highlighted index
  const activeTierConfig = POKEBALL_TIERS_CONFIG[highlightedTierIndex];

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(6px)",
        zIndex: 60,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "16px",
      }}
    >
      {/* Crisp Handheld Stadium Modal Chassis */}
      <div
        style={{
          backgroundColor: "#ffffff",
          border: "4px solid #1e293b",
          borderRadius: "14px",
          width: "100%",
          maxWidth: "860px",
          padding: "24px 28px",
          boxShadow: "0 20px 45px rgba(15, 23, 42, 0.4), 8px 8px 0px #0f172a",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
        }}
      >
        {/* Stadium Modal Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "3px solid #e2e8f0",
            paddingBottom: "12px",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "10px",
                fontFamily: "'Press Start 2P', monospace",
                color: "#2563eb",
                letterSpacing: "1px",
                marginBottom: "4px",
              }}
            >
              LESSON 7: CATCH POKÉMON ROULETTE PHASE
            </div>
            <h2
              style={{
                margin: 0,
                fontSize: "18px",
                fontFamily: "'Press Start 2P', monospace",
                color: "#0f172a",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>🎰</span> Pokéball Roulette Wheel
            </h2>
          </div>

          {/* Opponent Target Mini-Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              backgroundColor: "#f8fafc",
              border: "2px solid #cbd5e1",
              borderRadius: "8px",
              padding: "6px 12px",
            }}
          >
            {opponentSpriteUrl && (
              <img
                src={opponentSpriteUrl}
                alt={opponentMonsterName}
                style={{
                  width: "36px",
                  height: "36px",
                  imageRendering: "pixelated",
                }}
              />
            )}
            <div>
              <div
                style={{
                  fontSize: "9px",
                  fontFamily: "'Press Start 2P', monospace",
                  color: "#64748b",
                }}
              >
                TARGET (Lv {opponentLevel})
              </div>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: "bold",
                  color: "#0f172a",
                }}
              >
                {opponentMonsterName}
              </div>
            </div>
          </div>
        </div>

        {/* Live Stadium Announcer Ticker Tape */}
        <div
          style={{
            backgroundColor: "#0f172a",
            color: "#38bdf8",
            border: "2px solid #334155",
            borderRadius: "6px",
            padding: "10px 14px",
            fontSize: "11px",
            fontFamily: "'Press Start 2P', monospace",
            lineHeight: "1.6",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span style={{ fontSize: "14px" }}>🎙️</span>
          <span>{statusNarrationText}</span>
        </div>

        {/* Error notification if spin API fails */}
        {errorMessage && (
          <div
            style={{
              backgroundColor: "#fef2f2",
              border: "2px solid #ef4444",
              borderRadius: "6px",
              padding: "10px",
              color: "#b91c1c",
              fontSize: "12px",
              fontWeight: 600,
            }}
          >
            ⚠️ {errorMessage}
          </div>
        )}

        {/* Center Stage: Interactive Roulette Carousel or 3-Wobble Throw Area */}
        {modalPhase !== "WOBBLING" && modalPhase !== "RESULT" ? (
          /* 4-Tier Pokéball Carousel Cards */
          <div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "12px",
                marginBottom: "14px",
              }}
            >
              {POKEBALL_TIERS_CONFIG.map((tierConfigItem, index) => {
                const isSelected = highlightedTierIndex === index;
                return (
                  <div
                    key={tierConfigItem.tier}
                    className={isSelected ? "roulette-card-active-glow" : ""}
                    style={{
                      backgroundColor: isSelected ? "#ffffff" : "#f8fafc",
                      border: isSelected
                        ? `3px solid ${tierConfigItem.cardBorderColor}`
                        : "2px solid #cbd5e1",
                      borderRadius: "10px",
                      padding: "14px 10px",
                      textAlign: "center",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "6px",
                      transition: "transform 0.15s ease, border-color 0.15s ease",
                      boxShadow: isSelected
                        ? "0 8px 16px rgba(0,0,0,0.12)"
                        : "none",
                    }}
                  >
                    {/* Tier Ball Icon */}
                    <div style={{ fontSize: "28px", lineHeight: "1" }}>
                      {tierConfigItem.iconSymbol}
                    </div>

                    {/* Tier Title */}
                    <div
                      style={{
                        fontSize: "9px",
                        fontFamily: "'Press Start 2P', monospace",
                        color: "#0f172a",
                        marginTop: "4px",
                      }}
                    >
                      {tierConfigItem.displayName}
                    </div>

                    {/* Catch Rate Badge */}
                    <span
                      style={{
                        backgroundColor: tierConfigItem.badgeBackgroundColor,
                        color: tierConfigItem.badgeTextColor,
                        fontSize: "10px",
                        fontWeight: "bold",
                        padding: "3px 8px",
                        borderRadius: "12px",
                        border: `1px solid ${tierConfigItem.cardBorderColor}`,
                      }}
                    >
                      {tierConfigItem.catchProbabilityPercentage}% Catch
                    </span>

                    {/* Wheel Distribution Odds */}
                    <span
                      style={{
                        fontSize: "10px",
                        color: "#64748b",
                        fontStyle: "italic",
                      }}
                    >
                      {tierConfigItem.wheelWeightPercentage}% Wheel Odds
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Description of Currently Highlighted Tier */}
            <div
              style={{
                backgroundColor: "#f1f5f9",
                borderRadius: "8px",
                padding: "10px 14px",
                fontSize: "12px",
                color: "#334155",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>
                <strong>{activeTierConfig.displayName}</strong>:{" "}
                {activeTierConfig.description}
              </span>
              <span
                style={{
                  fontSize: "10px",
                  fontFamily: "'Press Start 2P', monospace",
                  color: "#2563eb",
                }}
              >
                {modalPhase === "SPINNING" ? "SPINNING..." : "READY TO SPIN"}
              </span>
            </div>
          </div>
        ) : (
          /* 3-Wobble Catch Suspense Pitch */
          <div
            style={{
              backgroundColor: "#f8fafc",
              border: "3px dashed #cbd5e1",
              borderRadius: "12px",
              padding: "28px 20px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "220px",
              gap: "16px",
            }}
          >
            {/* Animated Pokéball Sprite with CSS Wobble Classes */}
            <div
              style={{
                position: "relative",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <div
                className={
                  wobbleStep === 1
                    ? "pokeball-wobble-1"
                    : wobbleStep === 2
                    ? "pokeball-wobble-2"
                    : wobbleStep === 3
                    ? "pokeball-wobble-3"
                    : wobbleStep === 4 && finalOutcome?.capture_successful
                    ? "pokeball-caught-success"
                    : wobbleStep === 4 && !finalOutcome?.capture_successful
                    ? "pokeball-broke-free"
                    : ""
                }
                style={{
                  fontSize: "64px",
                  lineHeight: "1",
                  userSelect: "none",
                  cursor: "default",
                  display: "inline-block",
                }}
              >
                {activeTierConfig.iconSymbol}
              </div>
            </div>

            {/* Wobble Step Progress Indicator */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                alignItems: "center",
              }}
            >
              <span
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: wobbleStep >= 1 ? "#3b82f6" : "#cbd5e1",
                  border: "1px solid #1e293b",
                }}
              />
              <span
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: wobbleStep >= 2 ? "#3b82f6" : "#cbd5e1",
                  border: "1px solid #1e293b",
                }}
              />
              <span
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: wobbleStep >= 3 ? "#3b82f6" : "#cbd5e1",
                  border: "1px solid #1e293b",
                }}
              />
              <span
                style={{
                  fontSize: "10px",
                  fontFamily: "'Press Start 2P', monospace",
                  color: "#0f172a",
                  marginLeft: "8px",
                }}
              >
                {wobbleStep === 1 && "WOBBLE 1/3"}
                {wobbleStep === 2 && "WOBBLE 2/3"}
                {wobbleStep === 3 && "WOBBLE 3/3"}
                {wobbleStep === 4 && (finalOutcome?.capture_successful ? "⭐ CAUGHT!" : "💨 FLED!")}
              </span>
            </div>

            {/* Outcome Announcement Banner */}
            {modalPhase === "RESULT" && finalOutcome && (
              <div
                style={{
                  backgroundColor: finalOutcome.capture_successful
                    ? "#f0fdf4"
                    : "#fef2f2",
                  border: finalOutcome.capture_successful
                    ? "2px solid #22c55e"
                    : "2px solid #ef4444",
                  borderRadius: "8px",
                  padding: "12px 18px",
                  textAlign: "center",
                  maxWidth: "520px",
                }}
              >
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: "bold",
                    color: finalOutcome.capture_successful
                      ? "#15803d"
                      : "#b91c1c",
                    marginBottom: "4px",
                  }}
                >
                  {finalOutcome.capture_successful
                    ? `🎉 Wild ${opponentMonsterName} is now in your party roster!`
                    : `💨 Wild ${opponentMonsterName} escaped into the tall grass.`}
                </div>
                <div style={{ fontSize: "11px", color: "#475569" }}>
                  {finalOutcome.capture_successful
                    ? `You can now select ${opponentMonsterName} via the pre-turn TEAM swap button!`
                    : "No worries, Trainer! Battle again to recruit another partner!"}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal Action Footer */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "3px solid #e2e8f0",
            paddingTop: "14px",
          }}
        >
          {/* Informational Guidance */}
          <div
            style={{
              fontSize: "11px",
              color: "#64748b",
            }}
          >
            {modalPhase === "READY" && "Hit SPIN to let the weighted wheel pick your ball tier!"}
            {modalPhase === "SPINNING" && "Hold your breath! The wheel is slowing down..."}
            {modalPhase === "WOBBLING" && "Watch the Pokéball carefully on the stadium pitch!"}
            {modalPhase === "RESULT" && "Capture phase resolved. Advance to coach debrief."}
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "10px" }}>
            {modalPhase === "READY" && (
              <ButtonUI
                variant="action"
                onClick={handleTriggerSpin}
                disabled={isSpinRequestPending}
                showArrowPointer="right"
              >
                🎯 SPIN THE WHEEL!
              </ButtonUI>
            )}

            {modalPhase === "RESULT" && (
              <ButtonUI
                variant="action"
                onClick={handleProceedToDebrief}
                showArrowPointer="right"
              >
                Advance to Debrief ▸
              </ButtonUI>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
