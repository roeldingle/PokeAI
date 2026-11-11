/**
 * Battle Arena Screen Component
 * Renders the authentic retro GBA Battle Arena layout:
 * - High-definition animated showdown sprites scaled for daylight stadium presentation
 * - Isometric 3D grassy battle pedestals with authentic grounding
 * - Visual combat effects: attacker lunges, impact starbursts, floating damage numbers,
 *   and violent red-flash damage flickers
 * - Authentic GBA Pokémon faint sink animation when HP reaches 0
 * - Post-battle Game Guide debrief overlay delivering personalized commentary to the trainer
 * - 2x2 Tactical Action Menu & Move Selection Grid with PP and effectiveness badges
 */

import React, { useEffect, useState, useCallback } from "react";
import { ButtonUI } from "../ui/ButtonUI";
import { ProviderStatusBadge } from "../ui/ProviderStatusBadge";
import { GameGuideDialogBox } from "../ui/GameGuideDialogBox";
import {
  initiateBattleMatch,
  resolveBattleTurn,
} from "../../services/battleService";
import type {
  ActiveBattleEntity,
  BattleSessionData,
  BattleTurnResolutionResponse,
  PokemonMoveSlot,
} from "../../types/battle";

interface BattleArenaScreenProps {
  trainerName: string;
  selectedPokemonId: number;
  gameGuideName?: string;
  onExitBattle: () => void;
}

export const BattleArenaScreen: React.FC<BattleArenaScreenProps> = ({
  trainerName,
  selectedPokemonId,
  gameGuideName = "Shaneil",
  onExitBattle,
}) => {
  // Session tracking state
  const [activeSession, setActiveSession] = useState<BattleSessionData | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Combat loop & view states
  const [isMoveGridActive, setIsMoveGridActive] = useState<boolean>(false);
  const [isTurnResolving, setIsTurnResolving] = useState<boolean>(false);
  const [battleNarrationText, setBattleNarrationText] = useState<string>(
    "A wild Pidgey appeared! What will you do?"
  );

  // Active combatant entity states
  const [playerMonster, setPlayerMonster] = useState<ActiveBattleEntity | null>(null);
  const [opponentMonster, setOpponentMonster] = useState<ActiveBattleEntity | null>(null);

  // Dynamic animation trigger states
  const [isPlayerAttacking, setIsPlayerAttacking] = useState<boolean>(false);
  const [isOpponentAttacking, setIsOpponentAttacking] = useState<boolean>(false);
  const [isPlayerTakingDamage, setIsPlayerTakingDamage] = useState<boolean>(false);
  const [isOpponentTakingDamage, setIsOpponentTakingDamage] = useState<boolean>(false);

  // Faint and loss animation states
  const [isOpponentFainted, setIsOpponentFainted] = useState<boolean>(false);
  const [isPlayerFainted, setIsPlayerFainted] = useState<boolean>(false);

  // Post-battle Game Guide debrief presentation states
  const [showPostBattleGuide, setShowPostBattleGuide] = useState<boolean>(false);
  const [battleOutcome, setBattleOutcome] = useState<"VICTORY" | "DEFEAT" | null>(null);

  // Visual impact overlays & floating combat damage numbers
  const [opponentFloatingDamage, setOpponentFloatingDamage] = useState<number | null>(null);
  const [playerFloatingDamage, setPlayerFloatingDamage] = useState<number | null>(null);
  const [showOpponentImpactStar, setShowOpponentImpactStar] = useState<boolean>(false);
  const [showPlayerImpactStar, setShowPlayerImpactStar] = useState<boolean>(false);

  // Function to initialize or restart a battle match
  const startCombatMatch = useCallback(async () => {
    try {
      setIsLoadingSession(true);
      setErrorMessage(null);
      setIsOpponentFainted(false);
      setIsPlayerFainted(false);
      setShowPostBattleGuide(false);
      setBattleOutcome(null);
      setIsMoveGridActive(false);

      const sessionResult = await initiateBattleMatch(
        trainerName,
        selectedPokemonId,
        16 // Pidgey ID
      );

      setActiveSession(sessionResult);
      setPlayerMonster(sessionResult.player_monster);
      setOpponentMonster(sessionResult.opponent_monster);
      setBattleNarrationText(
        `A wild ${sessionResult.opponent_monster.pokemon_name} appeared! What will ${sessionResult.player_monster.pokemon_name} do?`
      );
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to load battle arena."
      );
    } finally {
      setIsLoadingSession(false);
    }
  }, [trainerName, selectedPokemonId]);

  // Mount effect to start combat
  useEffect(() => {
    startCombatMatch();
  }, [startCombatMatch]);

  // Handle move execution
  const handleExecuteMove = async (selectedMove: PokemonMoveSlot) => {
    if (!activeSession || isTurnResolving || !selectedMove.is_unlocked) return;

    if (selectedMove.current_power_points <= 0) {
      setBattleNarrationText(`No PP left for ${selectedMove.move_name}!`);
      return;
    }

    setIsTurnResolving(true);
    setIsMoveGridActive(false);

    try {
      const resolutionResult: BattleTurnResolutionResponse = await resolveBattleTurn(
        activeSession.battle_session_id,
        selectedMove.move_id
      );

      const isPlayerFirst =
        resolutionResult.first_action_resolution.attacker_name === playerMonster?.pokemon_name;

      if (isPlayerFirst) {
        // Step 1: Player lunges forward
        setIsPlayerAttacking(true);
        setBattleNarrationText(
          resolutionResult.first_action_resolution.narrative_announcement
        );

        // Step 2: Opponent takes hit animation after lunge (350ms)
        setTimeout(() => {
          setIsPlayerAttacking(false);
          setIsOpponentTakingDamage(true);
          setShowOpponentImpactStar(true);
          setOpponentFloatingDamage(
            resolutionResult.first_action_resolution.calculated_damage
          );

          // Update opponent HP immediately so faint check is real-time
          setOpponentMonster((prev) =>
            prev
              ? {
                  ...prev,
                  current_health_points:
                    resolutionResult.first_action_resolution
                      .defender_remaining_health_points,
                }
              : null
          );

          // If opponent fainted from first strike, trigger faint animation
          if (
            resolutionResult.first_action_resolution
              .defender_remaining_health_points === 0
          ) {
            setIsOpponentFainted(true);
          }

          setTimeout(() => {
            setIsOpponentTakingDamage(false);
            setShowOpponentImpactStar(false);
            setOpponentFloatingDamage(null);
          }, 700);
        }, 350);

        // Step 3: If retaliation occurred, opponent strikes player
        if (resolutionResult.second_action_resolution) {
          setTimeout(() => {
            setIsOpponentAttacking(true);
            setBattleNarrationText(
              resolutionResult.second_action_resolution!.narrative_announcement
            );

            setTimeout(() => {
              setIsOpponentAttacking(false);
              setIsPlayerTakingDamage(true);
              setShowPlayerImpactStar(true);
              setPlayerFloatingDamage(
                resolutionResult.second_action_resolution!.calculated_damage
              );

              // Update player HP
              setPlayerMonster((prev) =>
                prev
                  ? {
                      ...prev,
                      current_health_points:
                        resolutionResult.second_action_resolution!
                          .defender_remaining_health_points,
                    }
                  : null
              );

              // Check if player fainted
              if (
                resolutionResult.second_action_resolution!
                  .defender_remaining_health_points === 0
              ) {
                setIsPlayerFainted(true);
              }

              setTimeout(() => {
                setIsPlayerTakingDamage(false);
                setShowPlayerImpactStar(false);
                setPlayerFloatingDamage(null);
              }, 700);
            }, 350);
          }, 1400);
        }
      } else {
        // Opponent attacks first
        setIsOpponentAttacking(true);
        setBattleNarrationText(
          resolutionResult.first_action_resolution.narrative_announcement
        );

        setTimeout(() => {
          setIsOpponentAttacking(false);
          setIsPlayerTakingDamage(true);
          setShowPlayerImpactStar(true);
          setPlayerFloatingDamage(
            resolutionResult.first_action_resolution.calculated_damage
          );

          // Update player HP
          setPlayerMonster((prev) =>
            prev
              ? {
                  ...prev,
                  current_health_points:
                    resolutionResult.first_action_resolution
                      .defender_remaining_health_points,
                }
              : null
          );

          // Check if player fainted
          if (
            resolutionResult.first_action_resolution
              .defender_remaining_health_points === 0
          ) {
            setIsPlayerFainted(true);
          }

          setTimeout(() => {
            setIsPlayerTakingDamage(false);
            setShowPlayerImpactStar(false);
            setPlayerFloatingDamage(null);
          }, 700);
        }, 350);

        // Player retaliates
        if (resolutionResult.second_action_resolution) {
          setTimeout(() => {
            setIsPlayerAttacking(true);
            setBattleNarrationText(
              resolutionResult.second_action_resolution!.narrative_announcement
            );

            setTimeout(() => {
              setIsPlayerAttacking(false);
              setIsOpponentTakingDamage(true);
              setShowOpponentImpactStar(true);
              setOpponentFloatingDamage(
                resolutionResult.second_action_resolution!.calculated_damage
              );

              // Update opponent HP
              setOpponentMonster((prev) =>
                prev
                  ? {
                      ...prev,
                      current_health_points:
                        resolutionResult.second_action_resolution!
                          .defender_remaining_health_points,
                    }
                  : null
              );

              // Check if opponent fainted
              if (
                resolutionResult.second_action_resolution!
                  .defender_remaining_health_points === 0
              ) {
                setIsOpponentFainted(true);
              }

              setTimeout(() => {
                setIsOpponentTakingDamage(false);
                setShowOpponentImpactStar(false);
                setOpponentFloatingDamage(null);
              }, 700);
            }, 350);
          }, 1400);
        }
      }

      // Sync final state
      setTimeout(() => {
        setPlayerMonster(resolutionResult.player_monster);
        setOpponentMonster(resolutionResult.opponent_monster);
      }, 600);

      // Handle match conclusion and trigger Game Guide post-match debrief
      if (resolutionResult.is_battle_concluded) {
        const isVictor =
          resolutionResult.victorious_monster_name === playerMonster?.pokemon_name;
        setBattleOutcome(isVictor ? "VICTORY" : "DEFEAT");

        // First display the defeat/victory stadium log
        setTimeout(() => {
          if (isVictor) {
            setBattleNarrationText(
              `🏆 VICTORY! Wild ${opponentMonster?.pokemon_name} fainted! You earned 45 EXP!`
            );
          } else {
            setBattleNarrationText(
              `💥 ${playerMonster?.pokemon_name} fainted! You whited out!`
            );
          }
        }, 1600);

        // Slide in the Game Guide debrief after the faint animation finishes
        setTimeout(() => {
          setShowPostBattleGuide(true);
        }, 2200);
      }
    } catch (err) {
      setBattleNarrationText(
        err instanceof Error ? err.message : "Error resolving turn."
      );
    } finally {
      setTimeout(() => {
        setIsTurnResolving(false);
      }, 1800);
    }
  };

  // Compute HP percentage for health bars
  const calculateHealthPercentage = (currentHp: number, maxHp: number): number => {
    return Math.max(0, Math.min(100, Math.round((currentHp / maxHp) * 100)));
  };

  const getHealthBarColor = (percentage: number): string => {
    if (percentage > 50) return "#22c55e"; // Vibrant Green
    if (percentage > 20) return "#eab308"; // Amber
    return "#ef4444"; // Urgent Red
  };

  if (isLoadingSession) {
    return (
      <div className="pokeai-viewport">
        <div className="gba-screen-chassis" style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          <p style={{ fontFamily: "var(--font-pixel)", fontSize: "0.85rem", color: "#475569" }}>
            Preparing the Stadium Battle Ring...
          </p>
        </div>
      </div>
    );
  }

  if (errorMessage || !playerMonster || !opponentMonster) {
    return (
      <div className="pokeai-viewport">
        <div className="gba-screen-chassis" style={{ padding: "32px", textAlign: "center" }}>
          <h2 style={{ fontFamily: "var(--font-pixel)", color: "#ef4444", marginBottom: "16px" }}>
            Arena Connection Error
          </h2>
          <p style={{ color: "#475569", marginBottom: "24px" }}>{errorMessage}</p>
          <ButtonUI onClick={onExitBattle} variant="default">
            Return to Academy
          </ButtonUI>
        </div>
      </div>
    );
  }

  const opponentHpPercent = calculateHealthPercentage(
    opponentMonster.current_health_points,
    opponentMonster.maximum_health_points
  );
  const playerHpPercent = calculateHealthPercentage(
    playerMonster.current_health_points,
    playerMonster.maximum_health_points
  );

  return (
    <div className="pokeai-viewport">
      <div className="gba-screen-chassis" style={{ minHeight: "680px" }}>
        {/* Top Stadium Header */}
        <header className="stadium-header-bar">
          <span className="stadium-indicator">
            ● LESSON 5: CLASSIC GBA BATTLE ARENA (DETERMINISTIC DAMAGE)
          </span>
          <ProviderStatusBadge />
        </header>

        {/* Retro GBA Battle Stage with Daylight Field Atmosphere */}
        <main
          style={{
            flex: 1,
            position: "relative",
            background: "radial-gradient(ellipse at 50% 40%, #f0fdf4 0%, #e2e8f0 100%)",
            padding: "24px 40px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            overflow: "hidden",
          }}
        >
          {/* Top Row: Opponent HUD (Left) & Opponent Sprite on Grassy Pedestal (Right) */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              width: "100%",
              position: "relative",
              zIndex: 5,
            }}
          >
            {/* Opponent HUD Card */}
            <div
              style={{
                background: "#ffffff",
                border: "3px solid #1e293b",
                borderRadius: "10px",
                padding: "12px 18px",
                minWidth: "290px",
                boxShadow: "6px 6px 0px rgba(15, 23, 42, 0.12)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.82rem",
                  marginBottom: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <strong>{opponentMonster.pokemon_name}</strong>
                  <span
                    style={{
                      fontSize: "0.6rem",
                      backgroundColor: "#fee2e2",
                      color: "#dc2626",
                      padding: "1px 6px",
                      borderRadius: "3px",
                      border: "1px solid #fca5a5",
                    }}
                  >
                    FOE
                  </span>
                </div>
                <span style={{ color: "#475569", fontSize: "0.75rem" }}>
                  Lv {opponentMonster.level}
                </span>
              </div>

              {/* HP Bar */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span
                  style={{
                    fontFamily: "var(--font-pixel)",
                    fontSize: "0.65rem",
                    color: "#f59e0b",
                    fontWeight: 800,
                  }}
                >
                  HP
                </span>
                <div
                  style={{
                    flex: 1,
                    height: "12px",
                    backgroundColor: "#e2e8f0",
                    borderRadius: "6px",
                    overflow: "hidden",
                    border: "2px solid #64748b",
                    boxShadow: "inset 0 2px 4px rgba(0,0,0,0.15)",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${opponentHpPercent}%`,
                      backgroundColor: getHealthBarColor(opponentHpPercent),
                      transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Opponent Sprite Stage on Grassy Pedestal */}
            <div
              style={{
                position: "relative",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                marginRight: "60px",
                marginTop: "10px",
              }}
            >
              {/* Floating Combat Damage Popup */}
              {opponentFloatingDamage !== null && (
                <div className="floating-damage-popup">
                  -{opponentFloatingDamage} HP
                </div>
              )}

              {/* Impact Starburst Flash */}
              {showOpponentImpactStar && (
                <div className="impact-starburst-overlay" style={{ fontSize: "4.5rem" }}>
                  💥
                </div>
              )}

              {/* Animated Showdown Opponent Sprite with Faint Support */}
              <img
                src={opponentMonster.sprite_front_url}
                alt={opponentMonster.pokemon_name}
                className={`${isOpponentTakingDamage ? "pokemon-hit-active" : ""} ${
                  isOpponentAttacking ? "opponent-attacking-lunge" : ""
                } ${isOpponentFainted ? "pokemon-fainted" : ""}`}
                style={{
                  width: "170px",
                  height: "170px",
                  objectFit: "contain",
                  imageRendering: "pixelated",
                  position: "relative",
                  zIndex: 2,
                  marginBottom: "-34px",
                  transformOrigin: "bottom center",
                }}
              />

              {/* 3D Grassy Battle Pedestal */}
              <div
                className="battle-grass-pedestal"
                style={{
                  width: "250px",
                  height: "52px",
                  zIndex: 1,
                }}
              />
            </div>
          </div>

          {/* Bottom Row: Player Sprite on Grassy Pedestal (Left) & Player HUD (Right) */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              width: "100%",
              position: "relative",
              zIndex: 5,
              marginBottom: "10px",
            }}
          >
            {/* Player Sprite Stage on Grassy Pedestal */}
            <div
              style={{
                position: "relative",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                marginLeft: "60px",
              }}
            >
              {/* Floating Combat Damage Popup */}
              {playerFloatingDamage !== null && (
                <div className="floating-damage-popup">
                  -{playerFloatingDamage} HP
                </div>
              )}

              {/* Impact Starburst Flash */}
              {showPlayerImpactStar && (
                <div className="impact-starburst-overlay" style={{ fontSize: "5rem" }}>
                  💥
                </div>
              )}

              {/* Animated Showdown Player Back Sprite with Faint Support */}
              <img
                src={playerMonster.sprite_back_url}
                alt={playerMonster.pokemon_name}
                className={`${isPlayerTakingDamage ? "pokemon-hit-active" : ""} ${
                  isPlayerAttacking ? "player-attacking-lunge" : ""
                } ${isPlayerFainted ? "pokemon-fainted" : ""}`}
                style={{
                  width: "225px",
                  height: "225px",
                  objectFit: "contain",
                  imageRendering: "pixelated",
                  position: "relative",
                  zIndex: 2,
                  marginBottom: "-42px",
                  transformOrigin: "bottom center",
                }}
              />

              {/* 3D Grassy Battle Pedestal */}
              <div
                className="battle-grass-pedestal"
                style={{
                  width: "305px",
                  height: "60px",
                  zIndex: 1,
                }}
              />
            </div>

            {/* Player HUD Card */}
            <div
              style={{
                background: "#ffffff",
                border: "3px solid #1e293b",
                borderRadius: "10px",
                padding: "14px 20px",
                minWidth: "320px",
                boxShadow: "6px 6px 0px rgba(15, 23, 42, 0.12)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.85rem",
                  marginBottom: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <strong>{playerMonster.pokemon_name}</strong>
                  <span
                    style={{
                      fontSize: "0.6rem",
                      backgroundColor: "#dbeafe",
                      color: "#1e40af",
                      padding: "1px 6px",
                      borderRadius: "3px",
                      border: "1px solid #bfdbfe",
                    }}
                  >
                    YOU
                  </span>
                </div>
                <span style={{ color: "#475569", fontSize: "0.75rem" }}>
                  Lv {playerMonster.level}
                </span>
              </div>

              {/* HP Bar */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span
                  style={{
                    fontFamily: "var(--font-pixel)",
                    fontSize: "0.65rem",
                    color: "#f59e0b",
                    fontWeight: 800,
                  }}
                >
                  HP
                </span>
                <div
                  style={{
                    flex: 1,
                    height: "12px",
                    backgroundColor: "#e2e8f0",
                    borderRadius: "6px",
                    overflow: "hidden",
                    border: "2px solid #64748b",
                    boxShadow: "inset 0 2px 4px rgba(0,0,0,0.15)",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${playerHpPercent}%`,
                      backgroundColor: getHealthBarColor(playerHpPercent),
                      transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
                    }}
                  />
                </div>
              </div>

              {/* Numerical HP Display */}
              <div
                style={{
                  textAlign: "right",
                  fontFamily: "var(--font-pixel)",
                  fontSize: "0.72rem",
                  color: "#1e293b",
                  marginTop: "6px",
                  fontWeight: 700,
                }}
              >
                {playerMonster.current_health_points} / {playerMonster.maximum_health_points}
              </div>

              {/* EXP Bar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginTop: "6px",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-pixel)",
                    fontSize: "0.58rem",
                    color: "#2563eb",
                    fontWeight: 700,
                  }}
                >
                  EXP
                </span>
                <div
                  style={{
                    flex: 1,
                    height: "6px",
                    backgroundColor: "#e2e8f0",
                    borderRadius: "3px",
                    overflow: "hidden",
                    border: "1px solid #cbd5e1",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: "65%",
                      backgroundColor: "#3b82f6",
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Bottom GBA Control Panel / Post-Battle Game Guide Overlay */}
        <footer
          style={{
            background: "#1e293b",
            borderTop: "4px solid #0f172a",
            padding: showPostBattleGuide ? "0 0" : "18px 28px",
            position: "relative",
            zIndex: 10,
          }}
        >
          {showPostBattleGuide ? (
            /* Post-Battle Game Guide Debrief */
            <div
              className="guide-post-battle-container"
              style={{
                width: "100%",
                padding: "16px 24px 20px 24px",
                background: "linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, #0f172a 100%)",
              }}
            >
              <GameGuideDialogBox
                characterName={gameGuideName}
                highlightedTerm={trainerName}
                dialogueMessage={
                  battleOutcome === "VICTORY"
                    ? `Outstanding battle, ${trainerName}! Your ${playerMonster.pokemon_name} completely dominated the arena with pinpoint Scratch attacks. Wild ${opponentMonster.pokemon_name} has fainted! That's 45 EXP earned. You're well on your way to becoming a champion!`
                    : `Hang in there, ${trainerName}! Every Champion suffers tough setbacks early on. ${playerMonster.pokemon_name} gave it everything! Let's patch up at the Pokémon Center, study our elemental type charts, and jump right back in!`
                }
                promptActionHint={
                  battleOutcome === "VICTORY"
                    ? "[ Press Enter to Return to Academy ▸ ]"
                    : "[ Press Enter to Recover ▸ ]"
                }
                onAdvanceDialogue={onExitBattle}
                characterImagePlacement="right"
                characterImageHeightPixels={360}
              />

              {/* Action Buttons to Replay or Return */}
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  justifyContent: "center",
                  marginTop: "16px",
                  flexWrap: "wrap",
                }}
              >
                <ButtonUI
                  onClick={onExitBattle}
                  variant="action"
                  showArrowPointer="right"
                >
                  🏆 Return to Academy
                </ButtonUI>
                <ButtonUI
                  onClick={startCombatMatch}
                  variant="default"
                  showArrowPointer="right"
                >
                  🔄 Battle Again
                </ButtonUI>
              </div>
            </div>
          ) : (
            /* Active Combat Control Panel: Dialogue + 2x2 Menu */
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1.2fr 1fr",
                gap: "20px",
                alignItems: "center",
              }}
            >
              {/* Left Dialogue / Narration Box */}
              <div
                style={{
                  background: "#ffffff",
                  border: "3px solid #334155",
                  borderRadius: "10px",
                  padding: "16px 20px",
                  minHeight: "96px",
                  display: "flex",
                  alignItems: "center",
                  boxShadow: "inset 0 2px 6px rgba(0,0,0,0.08)",
                }}
              >
                <p
                  style={{
                    fontFamily: "var(--font-pixel)",
                    fontSize: "0.78rem",
                    lineHeight: "1.65",
                    color: "#0f172a",
                  }}
                >
                  {battleNarrationText}
                </p>
              </div>

              {/* Right Action Menu OR 2x2 Move Grid */}
              {!isMoveGridActive ? (
                /* Classic 2x2 Action Menu */
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                  }}
                >
                  <ButtonUI
                    onClick={() => setIsMoveGridActive(true)}
                    variant="action"
                    showArrowPointer="right"
                    disabled={
                      isTurnResolving ||
                      opponentMonster.current_health_points === 0 ||
                      playerMonster.current_health_points === 0
                    }
                  >
                    FIGHT
                  </ButtonUI>

                  <ButtonUI
                    onClick={() => {}}
                    variant="default"
                    disabled={true}
                    title="Only 1 monster in party (Unlocked in Lesson 6)"
                  >
                    TEAM (🔒)
                  </ButtonUI>

                  <ButtonUI
                    onClick={() =>
                      setBattleNarrationText(
                        "Coach Guide: Scratch deals steady physical damage! (Tactical RAG unlocks in Lesson 8)"
                      )
                    }
                    variant="default"
                    showArrowPointer="right"
                  >
                    ASK GUIDE
                  </ButtonUI>

                  <ButtonUI
                    onClick={onExitBattle}
                    variant="default"
                    showArrowPointer="left"
                  >
                    RUN
                  </ButtonUI>
                </div>
              ) : (
                /* 2x2 Attack Move Selection Palette */
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "10px",
                    }}
                  >
                    {playerMonster.move_slots.map((moveSlot) => (
                      <button
                        key={moveSlot.move_id}
                        onClick={() => handleExecuteMove(moveSlot)}
                        disabled={!moveSlot.is_unlocked || isTurnResolving}
                        style={{
                          background: moveSlot.is_unlocked ? "#ffffff" : "#f1f5f9",
                          border: "2px solid #334155",
                          borderRadius: "8px",
                          padding: "8px 12px",
                          textAlign: "left",
                          cursor: moveSlot.is_unlocked ? "pointer" : "not-allowed",
                          opacity: moveSlot.is_unlocked ? 1 : 0.6,
                          fontFamily: "var(--font-pixel)",
                          transition: "transform 0.1s ease, box-shadow 0.1s ease",
                          boxShadow: moveSlot.is_unlocked
                            ? "0 3px 0 #1e293b"
                            : "none",
                        }}
                        onMouseDown={(e) => {
                          if (moveSlot.is_unlocked) {
                            e.currentTarget.style.transform = "translateY(2px)";
                            e.currentTarget.style.boxShadow = "0 1px 0 #1e293b";
                          }
                        }}
                        onMouseUp={(e) => {
                          if (moveSlot.is_unlocked) {
                            e.currentTarget.style.transform = "none";
                            e.currentTarget.style.boxShadow = "0 3px 0 #1e293b";
                          }
                        }}
                      >
                        {moveSlot.is_unlocked ? (
                          <div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontSize: "0.72rem",
                                marginBottom: "4px",
                              }}
                            >
                              <strong>{moveSlot.move_name}</strong>
                              <span
                                style={{
                                  fontSize: "0.55rem",
                                  padding: "2px 5px",
                                  backgroundColor: "#e2e8f0",
                                  borderRadius: "4px",
                                  textTransform: "uppercase",
                                  fontWeight: 700,
                                }}
                              >
                                {moveSlot.elemental_type.slice(0, 4)}
                              </span>
                            </div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontSize: "0.58rem",
                                color: "#64748b",
                              }}
                            >
                              <span>
                                PP {moveSlot.current_power_points}/
                                {moveSlot.maximum_power_points}
                              </span>
                              <span style={{ color: "#2563eb", fontWeight: 800 }}>
                                {moveSlot.base_power > 0 ? "1x Neutral" : "--"}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div
                            style={{
                              fontSize: "0.62rem",
                              color: "#94a3b8",
                              textAlign: "center",
                              padding: "8px 0",
                            }}
                          >
                            🔒 Locked: {moveSlot.unlock_victory_threshold}W
                          </div>
                        )}
                      </button>
                    ))}
                  </div>

                  {/* Back to Action Menu */}
                  <button
                    onClick={() => setIsMoveGridActive(false)}
                    style={{
                      background: "#475569",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 10px",
                      fontSize: "0.68rem",
                      fontFamily: "var(--font-pixel)",
                      cursor: "pointer",
                      letterSpacing: "0.5px",
                    }}
                  >
                    [B] BACK to Action Menu
                  </button>
                </div>
              )}
            </div>
          )}
        </footer>
      </div>
    </div>
  );
};
