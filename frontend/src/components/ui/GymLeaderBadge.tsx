/**
 * Gym Leader Badge & Autonomous Agent Telemetry Component (Lesson 9)
 * Displays the opponent's autonomous AI mood state, calibrated threat score
 * (reacting to the player's +1% stat progression multiplier), in-character battle taunt,
 * and pre-Turn 1 challenger selection pills (Wild Pidgey, Gym Leader Brock, Gym Leader Misty).
 */

import React from "react";
import type { AgentMoodState, GymLeaderTurnDecision } from "../../types/battle";

interface GymLeaderBadgeProps {
  opponentPokemonId: number;
  currentTurnNumber: number;
  isTurnResolving: boolean;
  gymLeaderDecision: GymLeaderTurnDecision | null;
  onSelectOpponentChallenger?: (targetOpponentPokemonId: number) => void;
}

export const GymLeaderBadge: React.FC<GymLeaderBadgeProps> = ({
  opponentPokemonId,
  currentTurnNumber,
  isTurnResolving,
  gymLeaderDecision,
  onSelectOpponentChallenger,
}) => {
  // Determine mood badge color palette
  const getMoodBadgeColors = (
    mood?: AgentMoodState
  ): { background: string; text: string; border: string } => {
    switch (mood) {
      case "DESPERATE_CLUTCH":
        return {
          background: "#fef2f2",
          text: "#b91c1c",
          border: "#ef4444",
        };
      case "AGGRESSIVE":
        return {
          background: "#fff7ed",
          text: "#c2410c",
          border: "#f97316",
        };
      case "DEFENSIVE":
        return {
          background: "#eff6ff",
          text: "#1d4ed8",
          border: "#3b82f6",
        };
      default:
        return {
          background: "#f8fafc",
          text: "#334155",
          border: "#94a3b8",
        };
    }
  };

  const activeMood: AgentMoodState =
    gymLeaderDecision?.agent_mood || "CALCULATING";
  const moodColors = getMoodBadgeColors(activeMood);

  const personaTitle =
    opponentPokemonId === 95
      ? "🪨 GYM LEADER BROCK"
      : opponentPokemonId === 121
      ? "🌊 GYM LEADER MISTY"
      : "🕊️ WILD AI INSTINCT";

  return (
    <div
      style={{
        marginTop: "8px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
      }}
    >
      {/* Pre-Turn 1 Challenger Tier Selector */}
      {currentTurnNumber === 1 && onSelectOpponentChallenger && (
        <div
          style={{
            display: "flex",
            gap: "4px",
            flexWrap: "wrap",
          }}
        >
          {[
            { id: 16, label: "🕊️ Wild Pidgey" },
            { id: 95, label: "🪨 Brock (Onix)" },
            { id: 121, label: "🌊 Misty (Starmie)" },
          ].map((challengerOption) => {
            const isSelected = opponentPokemonId === challengerOption.id;
            return (
              <button
                key={challengerOption.id}
                type="button"
                disabled={isTurnResolving || isSelected}
                onClick={() => onSelectOpponentChallenger(challengerOption.id)}
                style={{
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.48rem",
                  padding: "3px 6px",
                  borderRadius: "4px",
                  border: isSelected
                    ? "2px solid #0f172a"
                    : "1px solid #cbd5e1",
                  backgroundColor: isSelected ? "#e2e8f0" : "#ffffff",
                  color: "#0f172a",
                  cursor: isSelected ? "default" : "pointer",
                  fontWeight: isSelected ? 800 : 600,
                }}
              >
                {challengerOption.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Agent Mood & Dynamic Threat Calibration Pill */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "8px",
          backgroundColor: moodColors.background,
          color: moodColors.text,
          border: `1.5px solid ${moodColors.border}`,
          borderRadius: "6px",
          padding: "4px 8px",
          fontFamily: "var(--font-pixel)",
          fontSize: "0.52rem",
        }}
      >
        <span>
          🧠 {personaTitle}: {activeMood}
        </span>
        {gymLeaderDecision && (
          <span>
            ⚡ Threat {gymLeaderDecision.calibrated_threat_score.toFixed(1)}/10 (
            {gymLeaderDecision.detected_player_stat_multiplier.toFixed(2)}x)
          </span>
        )}
      </div>

      {/* In-Character Gym Leader Battle Taunt Bubble */}
      {gymLeaderDecision?.in_character_dialogue_taunt && (
        <div
          style={{
            backgroundColor: "#f8fafc",
            border: "1.5px dashed #64748b",
            borderRadius: "6px",
            padding: "5px 8px",
            fontSize: "0.68rem",
            color: "#1e293b",
            fontStyle: "italic",
            lineHeight: 1.35,
            maxWidth: "330px",
          }}
        >
          💬 {gymLeaderDecision.in_character_dialogue_taunt}
        </div>
      )}
    </div>
  );
};
