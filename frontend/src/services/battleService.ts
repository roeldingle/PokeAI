/**
 * Battle Service Client
 * Dispatches asynchronous HTTP calls to FastAPI /api/v1/battle endpoints.
 */

import type {
  BattleSessionData,
  BattleTurnResolutionResponse,
} from "../types/battle";

// Central API base URL pointing to FastAPI server
const BACKEND_API_BASE_URL =
  import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

/**
 * Initiates a new GBA Battle match between the player's monster and a wild opponent.
 */
export async function initiateBattleMatch(
  trainerName: string,
  selectedPokemonId: number,
  opponentPokemonId: number = 16
): Promise<BattleSessionData> {
  const response = await fetch(`${BACKEND_API_BASE_URL}/api/v1/battle/initiate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      trainer_name: trainerName,
      selected_pokemon_id: selectedPokemonId,
      opponent_pokemon_id: opponentPokemonId,
    }),
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Failed to initiate battle (Status ${response.status})`
    );
  }

  const jsonResult = await response.json();
  return jsonResult.battle_session;
}

/**
 * Resolves a round of combat after the player chooses an attack move from the 2x2 grid.
 */
export async function resolveBattleTurn(
  battleSessionId: string,
  selectedMoveId: number
): Promise<BattleTurnResolutionResponse> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/turn/resolve`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        battle_session_id: battleSessionId,
        selected_move_id: selectedMoveId,
      }),
    }
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Failed to resolve battle turn (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Fetches the active battle session state.
 */
export async function fetchBattleSession(
  battleSessionId: string
): Promise<BattleSessionData> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/session/${battleSessionId}`
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Failed to fetch session (Status ${response.status})`
    );
  }

  const jsonResult = await response.json();
  return jsonResult.battle_session;
}
