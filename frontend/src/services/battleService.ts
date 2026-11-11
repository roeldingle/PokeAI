/**
 * Battle Service Client
 * Dispatches asynchronous HTTP calls to FastAPI /api/v1/battle endpoints:
 * - initiateBattleMatch: Starts a new combat match against an opponent.
 * - resolveBattleTurn: Resolves combat round with speed initiative and PP decrement.
 * - fetchBattleSession: Retrieves real-time battle session state.
 * - swapActivePartyMonster: Executes pre-Turn 1 party swap (Lesson 6).
 * - fetchTrainerPartyPool: Fetches trainer's recruited party roster and progression stats.
 * - spinCatchRoulette: Executes Lesson 7 overtime capture wheel when Turn 5 expires.
 * - fetchCoachTacticalAdvice: Requests Lesson 8 RAG tactical advice from the Game Guide.
 */

import type {
  BattleSessionData,
  BattleTurnResolutionResponse,
  CatchRouletteOutcome,
  CatchRouletteSpinRequest,
  CoachTacticalAdviceResponse,
  GymLeaderPersona,
  GymLeaderTurnDecision,
  TeamSwapResponse,
  TrainerPartyPoolState,
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

/**
 * Executes a Lesson 6 pre-Turn 1 party swap (`TEAM` button).
 */
export async function swapActivePartyMonster(
  battleSessionId: string,
  targetPokemonId: number
): Promise<TeamSwapResponse> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/team/swap`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        battle_session_id: battleSessionId,
        target_pokemon_id: targetPokemonId,
      }),
    }
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Failed to swap party monster (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Retrieves the trainer's complete party pool and progression stats.
 */
export async function fetchTrainerPartyPool(
  trainerName: string
): Promise<TrainerPartyPoolState> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/trainer/${encodeURIComponent(trainerName)}/party`
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Failed to fetch trainer party pool (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Lesson 7: Dispatches a roulette spin and overtime capture attempt.
 */
export async function spinCatchRoulette(
  spinRequest: CatchRouletteSpinRequest
): Promise<CatchRouletteOutcome> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/catch/roulette`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(spinRequest),
    }
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail || `Catch roulette failed (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Lesson 8: Requests real-time RAG tactical coaching advice from the Game Guide.
 */
export async function fetchCoachTacticalAdvice(
  battleSessionId: string,
  customTrainerQuestion?: string
): Promise<CoachTacticalAdviceResponse> {
  const response = await fetch(`${BACKEND_API_BASE_URL}/api/v1/battle/coach`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      battle_session_id: battleSessionId,
      custom_trainer_question: customTrainerQuestion ?? null,
    }),
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail ||
        `Failed to fetch tactical coach advice (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Lesson 9: Queries the Autonomous Gym Leader AI Agent's decision loop.
 */
export async function fetchGymLeaderDecision(
  battleSessionId: string,
  gymLeaderPersona?: GymLeaderPersona,
  useLlmGateway: boolean = false
): Promise<GymLeaderTurnDecision> {
  const response = await fetch(
    `${BACKEND_API_BASE_URL}/api/v1/battle/gym-leader/decide`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        battle_session_id: battleSessionId,
        gym_leader_persona: gymLeaderPersona ?? null,
        use_llm_gateway: useLlmGateway,
      }),
    }
  );

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(
      errorPayload.detail ||
        `Failed to fetch Gym Leader decision (Status ${response.status})`
    );
  }

  return response.json();
}

