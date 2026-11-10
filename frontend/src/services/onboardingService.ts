/**
 * Onboarding Service Client
 * Handles HTTP requests to the FastAPI backend for starter catalogs and trainer registration.
 */

import type {
  StarterMonsterInfo,
  TrainerProfileResponse,
  TrainerRegistrationRequest,
} from "../types/onboarding";

// Base backend API URL
const BACKEND_API_BASE_URL: string = "http://localhost:8000/api/v1/onboarding";

/**
 * Fetches the 3 canonical starter monsters (Bulbasaur, Charmander, Squirtle)
 */
export async function fetchAvailableStarterMonsters(): Promise<StarterMonsterInfo[]> {
  const httpResponse = await fetch(`${BACKEND_API_BASE_URL}/starters`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!httpResponse.ok) {
    throw new Error(
      `Failed to retrieve starter monsters catalog. Status code: ${httpResponse.status}`
    );
  }

  const startersPayload: StarterMonsterInfo[] = await httpResponse.json();
  return startersPayload;
}

/**
 * Sends trainer registration request to the backend referee
 */
export async function registerTrainerProfile(
  registrationPayload: TrainerRegistrationRequest
): Promise<TrainerProfileResponse> {
  const httpResponse = await fetch(`${BACKEND_API_BASE_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(registrationPayload),
  });

  if (!httpResponse.ok) {
    const errorBody = await httpResponse.text();
    throw new Error(
      `Registration rejected by referee server (${httpResponse.status}): ${errorBody}`
    );
  }

  const profileResponsePayload: TrainerProfileResponse = await httpResponse.json();
  return profileResponsePayload;
}