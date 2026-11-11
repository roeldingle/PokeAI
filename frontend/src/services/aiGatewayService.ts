/**
 * aiGatewayService.ts — REST Client for the Three-Channel Resilient LLM Gateway
 * Dispatches requests to backend endpoints for health diagnostics, general completions,
 * and dynamic Game Guide greetings.
 */

import type {
  GatewayHealthResponse,
  GameGuideGreetingRequest,
  LLMResponseEnvelope,
} from "../types/aiGateway";

const BACKEND_BASE_URL = "http://localhost:8000";

/**
 * Checks the operational health and readiness of all 3 provider channels (Ollama, Groq, Gemini).
 */
export async function checkGatewayHealth(): Promise<GatewayHealthResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/v1/ai/health`);
  if (!response.ok) {
    throw new Error(`Failed to check AI gateway health: HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Invokes the Resilient Gateway to awaken the Game Guide's AI Brain with a personalized greeting.
 */
export async function fetchGameGuideGreeting(
  greetingRequest: GameGuideGreetingRequest
): Promise<LLMResponseEnvelope> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/v1/ai/guide/greeting`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(greetingRequest),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to generate Game Guide dynamic greeting: HTTP ${response.status}`
    );
  }

  return response.json();
}

/**
 * Sends a generic prompt payload through the Resilient Gateway.
 */
export async function sendResilientPrompt(
  promptMessage: string,
  systemInstructions?: string
): Promise<LLMResponseEnvelope> {
  const messages = [];

  if (systemInstructions) {
    messages.push({
      role: "system",
      content: systemInstructions,
    });
  }

  messages.push({
    role: "user",
    content: promptMessage,
  });

  const response = await fetch(`${BACKEND_BASE_URL}/api/v1/ai/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messages,
      temperature: 0.7,
      max_tokens: 200,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to dispatch prompt through AI gateway: HTTP ${response.status}`);
  }

  return response.json();
}