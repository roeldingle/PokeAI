/**
 * Tactical Guide Overlay Component (Lesson 8)
 * Slides in the Game Guide's right-side portrait, dynamic nameplate, and RAG tactical telemetry
 * when the trainer selects 'ASK GUIDE' from the 2x2 GBA battle menu.
 */

import React from "react";
import { GameGuideDialogBox } from "./GameGuideDialogBox";
import { ButtonUI } from "./ButtonUI";
import type { CoachTacticalAdviceResponse } from "../../types/battle";

interface TacticalGuideOverlayProps {
  isOpen: boolean;
  isLoadingAdvice: boolean;
  trainerName: string;
  gameGuideName: string;
  tacticalAdvice: CoachTacticalAdviceResponse | null;
  onExecuteRecommendedMove: (recommendedMoveId: number) => void;
  onReturnToActionMenu: () => void;
}

export const TacticalGuideOverlay: React.FC<TacticalGuideOverlayProps> = ({
  isOpen,
  isLoadingAdvice,
  trainerName,
  gameGuideName,
  tacticalAdvice,
  onExecuteRecommendedMove,
  onReturnToActionMenu,
}) => {
  // Do not render anything when the tactical overlay is closed
  if (!isOpen) {
    return null;
  }

  // Format confidence percentage badge
  const confidencePercentage: number = tacticalAdvice
    ? Math.round(tacticalAdvice.confidence_rating * 100)
    : 90;

  return (
    <div
      className="guide-post-battle-container"
      style={{
        width: "100%",
        padding: "16px 24px 20px 24px",
        background: "linear-gradient(180deg, rgba(30, 41, 59, 0.96) 0%, #0f172a 100%)",
      }}
    >
      {/* Top RAG Telemetry & Vector Lore Banner (with 260px right clearance for Guide sprite) */}
      <div
        className="post-battle-progression-banner"
        style={{
          backgroundColor: "rgba(255, 255, 255, 0.96)",
          border: "3px solid #3b82f6",
          borderRadius: "10px",
          padding: "12px 18px",
          paddingRight: "260px",
          marginBottom: "14px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-pixel)",
              fontSize: "0.7rem",
              color: "#1d4ed8",
            }}
          >
            💡 LESSON 8 TACTICAL RAG COACH:{" "}
            {isLoadingAdvice
              ? "SCANNING CHROMADB VECTOR LORE..."
              : `USE ${tacticalAdvice?.recommended_action_name.toUpperCase() || "ATTACK"}!`}
          </div>

          {tacticalAdvice && (
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span
                style={{
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.56rem",
                  backgroundColor: "#dcfce7",
                  color: "#15803d",
                  border: "2px solid #22c55e",
                  padding: "3px 8px",
                  borderRadius: "6px",
                  whiteSpace: "nowrap",
                }}
              >
                🎯 {confidencePercentage}% RAG Confidence
              </span>
              <span
                style={{
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.56rem",
                  backgroundColor: "#f1f5f9",
                  color: "#334155",
                  border: "2px solid #94a3b8",
                  padding: "3px 8px",
                  borderRadius: "6px",
                  whiteSpace: "nowrap",
                }}
              >
                ⚡ {tacticalAdvice.execution_latency_milliseconds}ms
              </span>
            </div>
          )}
        </div>

        {/* ChromaDB Retrieved Lore & Matchup Matrix */}
        {tacticalAdvice && (
          <div
            style={{
              fontSize: "0.75rem",
              color: "#334155",
              lineHeight: 1.45,
              borderTop: "1px dashed #cbd5e1",
              paddingTop: "6px",
            }}
          >
            <div>
              <strong>🧬 Vector Memory:</strong> {tacticalAdvice.retrieved_lore_context}
            </div>
            <div style={{ marginTop: "3px", color: "#475569", fontSize: "0.72rem" }}>
              <strong>⚔️ Move Matrix:</strong> {tacticalAdvice.elemental_matchup_summary}
            </div>
          </div>
        )}
      </div>

      {/* Right-Side Game Guide Dialogue Box */}
      <GameGuideDialogBox
        characterName={gameGuideName}
        highlightedTerm={trainerName}
        dialogueMessage={
          isLoadingAdvice
            ? `Hold on, ${trainerName}! I'm querying our ChromaDB Pokédex vector memory and calculating elemental matchups against your opponent...`
            : tacticalAdvice?.tactical_justification ||
              `Stay focused, ${trainerName}! Strike with your highest-power unlocked attack!`
        }
        promptActionHint={
          isLoadingAdvice
            ? "[ Retrieving ChromaDB Vector Lore... ]"
            : `[ Recommended: ${tacticalAdvice?.recommended_action_name || "Attack"} | Press Enter to Return ▸ ]`
        }
        onAdvanceDialogue={onReturnToActionMenu}
        characterImagePlacement="right"
        characterImageHeightPixels={280}
      />

      {/* Action Buttons: One-Click Execute Recommended Move or Return to Menu */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          justifyContent: "center",
          marginTop: "14px",
          flexWrap: "wrap",
        }}
      >
        {tacticalAdvice?.recommended_move_id != null && !isLoadingAdvice && (
          <ButtonUI
            onClick={() =>
              onExecuteRecommendedMove(tacticalAdvice.recommended_move_id!)
            }
            variant="action"
            showArrowPointer="right"
          >
            ⚡ Execute {tacticalAdvice.recommended_action_name} Now
          </ButtonUI>
        )}
        <ButtonUI
          onClick={onReturnToActionMenu}
          variant="default"
          showArrowPointer="left"
        >
          ◀ Return to Battle Menu
        </ButtonUI>
      </div>
    </div>
  );
};
