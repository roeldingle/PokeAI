/**
 * Team Swap Modal Component (Lesson 6)
 * Renders an authentic retro GBA party roster overlay allowing the trainer
 * to swap their active monster before Turn 1 combat begins.
 * Displays each monster's animated sprite, cumulative victory count,
 * +1% stat mastery multiplier, effective stats, and unlocked move slots.
 */

import React from "react";
import { ButtonUI } from "./ButtonUI";
import type { RecruitedPartyMonster } from "../../types/battle";

interface TeamSwapModalProps {
  isOpen: boolean;
  trainerName: string;
  activePokemonId: number;
  partyMonsters: RecruitedPartyMonster[];
  isSwapInProgress: boolean;
  onSelectPartyMonster: (targetPokemonId: number) => void;
  onCloseModal: () => void;
}

export const TeamSwapModal: React.FC<TeamSwapModalProps> = ({
  isOpen,
  trainerName,
  activePokemonId,
  partyMonsters,
  isSwapInProgress,
  onSelectPartyMonster,
  onCloseModal,
}) => {
  // Do not render when modal is closed
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.72)",
        backdropFilter: "blur(6px)",
        zIndex: 50,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "24px",
      }}
    >
      {/* Crisp Daylight Stadium Modal Chassis */}
      <div
        style={{
          backgroundColor: "#ffffff",
          border: "4px solid #1e293b",
          borderRadius: "14px",
          width: "100%",
          maxWidth: "820px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(15, 23, 42, 0.35), 8px 8px 0px #0f172a",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "3px solid #e2e8f0",
            paddingBottom: "14px",
          }}
        >
          <div>
            <h3
              style={{
                fontFamily: "var(--font-pixel)",
                fontSize: "0.95rem",
                color: "#0f172a",
                margin: "0 0 6px 0",
              }}
            >
              🔄 {trainerName}&apos;s Party Pool ({partyMonsters.length} Monsters)
            </h3>
            <p
              style={{
                fontSize: "0.82rem",
                color: "#475569",
                margin: 0,
              }}
            >
              Pre-Turn 1 Tactical Switch — Select a partner from your pool to lead the match.
            </p>
          </div>

          <ButtonUI onClick={onCloseModal} variant="default">
            ✕ Close
          </ButtonUI>
        </div>

        {/* Party Monsters Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "16px",
            maxHeight: "380px",
            overflowY: "auto",
            padding: "4px",
          }}
        >
          {partyMonsters.map((partyMonster) => {
            const isCurrentlyActive = partyMonster.pokemon_id === activePokemonId;
            const bonusPercentage = Math.round(
              (partyMonster.stat_progression_multiplier - 1.0) * 100
            );
            const unlockedMoveNames = partyMonster.move_slots
              .filter((slot) => slot.is_unlocked)
              .map((slot) => slot.move_name);

            return (
              <div
                key={partyMonster.pokemon_id}
                style={{
                  backgroundColor: isCurrentlyActive ? "#eff6ff" : "#f8fafc",
                  border: isCurrentlyActive
                    ? "3px solid #2563eb"
                    : "3px solid #334155",
                  borderRadius: "10px",
                  padding: "14px 16px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "12px",
                  boxShadow: "4px 4px 0px rgba(15, 23, 42, 0.12)",
                }}
              >
                {/* Top Row: Sprite + Name + Active Badge */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                  }}
                >
                  <img
                    src={partyMonster.sprite_front_url}
                    alt={partyMonster.pokemon_name}
                    style={{
                      width: "64px",
                      height: "64px",
                      objectFit: "contain",
                      imageRendering: "pixelated",
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "4px",
                      }}
                    >
                      <strong
                        style={{
                          fontFamily: "var(--font-pixel)",
                          fontSize: "0.78rem",
                          color: "#0f172a",
                        }}
                      >
                        {partyMonster.pokemon_name}
                      </strong>
                      <span
                        style={{
                          fontFamily: "var(--font-pixel)",
                          fontSize: "0.62rem",
                          color: "#475569",
                        }}
                      >
                        Lv {partyMonster.level}
                      </span>
                    </div>

                    {/* Victory Count & +1% Stat Mastery Pill */}
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-pixel)",
                          fontSize: "0.55rem",
                          backgroundColor: "#fef3c7",
                          color: "#b45309",
                          border: "1px solid #f59e0b",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        🏆 {partyMonster.victories_count}W
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-pixel)",
                          fontSize: "0.55rem",
                          backgroundColor: "#dcfce7",
                          color: "#15803d",
                          border: "1px solid #4ade80",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        +{bonusPercentage}% Stats
                      </span>
                    </div>
                  </div>
                </div>

                {/* Scaled Effective Stats Preview */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "6px",
                    backgroundColor: "#ffffff",
                    border: "2px solid #cbd5e1",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    textAlign: "center",
                    fontFamily: "var(--font-pixel)",
                    fontSize: "0.55rem",
                  }}
                >
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "2px" }}>HP</div>
                    <strong style={{ color: "#0f172a" }}>
                      {partyMonster.effective_health_points}
                    </strong>
                  </div>
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "2px" }}>ATK</div>
                    <strong style={{ color: "#0f172a" }}>
                      {partyMonster.effective_attack_stat}
                    </strong>
                  </div>
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "2px" }}>DEF</div>
                    <strong style={{ color: "#0f172a" }}>
                      {partyMonster.effective_defense_stat}
                    </strong>
                  </div>
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "2px" }}>SPD</div>
                    <strong style={{ color: "#0f172a" }}>
                      {partyMonster.effective_speed_stat}
                    </strong>
                  </div>
                </div>

                {/* Unlocked Moves List */}
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: "#334155",
                  }}
                >
                  <strong style={{ fontSize: "0.65rem", color: "#64748b" }}>
                    Unlocked Moves ({unlockedMoveNames.length}/4):{" "}
                  </strong>
                  {unlockedMoveNames.join(", ")}
                </div>

                {/* Action Button: Active Lead vs Swap In */}
                {isCurrentlyActive ? (
                  <div
                    style={{
                      fontFamily: "var(--font-pixel)",
                      fontSize: "0.62rem",
                      textAlign: "center",
                      padding: "8px",
                      backgroundColor: "#dbeafe",
                      color: "#1e40af",
                      borderRadius: "6px",
                      border: "2px solid #93c5fd",
                    }}
                  >
                    ★ ACTIVE IN RING
                  </div>
                ) : (
                  <ButtonUI
                    onClick={() => onSelectPartyMonster(partyMonster.pokemon_id)}
                    variant="action"
                    showArrowPointer="right"
                    disabled={isSwapInProgress}
                  >
                    {isSwapInProgress
                      ? "Swapping..."
                      : `Send Out ${partyMonster.pokemon_name}`}
                  </ButtonUI>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
