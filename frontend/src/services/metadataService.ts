/**
 * Stadium Metadata Service
 * Handles network requests to the backend FastAPI referee server to retrieve configuration metadata.
 */

import type { GameMetadataResponse } from "../types/metadata";

// Centralized backend API base URL fallback pointing to our FastAPI development port
const BACKEND_BASE_URL: string =
  import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

/**
 * Fetches the centralized game and environment metadata from GET /api/v1/metadata.
 * In production AI systems, verifying this handshake ensures that client and server
 * are synchronized before initiating resource-heavy inference or battle loops.
 */
export async function fetchStadiumGameMetadata(): Promise<GameMetadataResponse> {
  // Construct the absolute endpoint URL for metadata retrieval
  const requestEndpointUrl: string = `${BACKEND_BASE_URL}/api/v1/metadata`;

  // Dispatch standard HTTP GET request with abort controller safeguard
  const response: Response = await fetch(requestEndpointUrl, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

  // Verify that the referee returned a 200 OK status
  if (!response.ok) {
    throw new Error(
      `Stadium referee communication failure: ${response.status} ${response.statusText}`
    );
  }

  // Parse and return the validated JSON payload
  const metadataPayload: GameMetadataResponse = await response.json();
  return metadataPayload;
}
