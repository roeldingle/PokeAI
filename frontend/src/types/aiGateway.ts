/**
 * aiGateway.ts — Data Contracts for the Resilient LLM Gateway
 * Mirrors backend Pydantic models from backend/src/schemas/ai_gateway_schema.py.
 * Synchronizes provider channels, latency telemetry, and Game Guide dynamic greetings.
 */

export type AIProviderName = "ollama" | "groq" | "gemini" | "offline_fallback";

/**
 * Standard battle envelope wrapping AI completions with full latency telemetry,
 * active provider identification, and failover indicators.
 */
export interface LLMResponseEnvelope {
  // Identifies which provider channel responded to the query
  active_provider_name: AIProviderName;
  // Specific model identifier (e.g. 'qwen/qwen3.8-27b', 'gemini-3.1-flash-lite')
  model_identifier: string;
  // Execution time in milliseconds measured at the backend gateway
  execution_latency_milliseconds: number;
  // Whether the system triggered a failover to backup channels
  fallback_triggered: boolean;
  // The AI-generated or fallback text content
  generated_message_content: string;
}

/**
 * Request payload to awaken the Game Guide's AI Brain for a dynamic greeting
 * upon trainer registration completion.
 */
export interface GameGuideGreetingRequest {
  // Trainer moniker entered on the registration card
  trainer_name: string;
  // Selected starter Pokédex identifier (1, 4, or 7)
  selected_starter_id: number;
  // Display name of the starter (e.g. 'Charmander')
  starter_monster_name: string;
  // Elemental classification (e.g. 'Fire')
  starter_elemental_type: string;
}

/**
 * Health diagnostic report for an individual AI provider frequency.
 */
export interface ProviderHealthStatus {
  // Channel name (e.g. 'ollama', 'groq', 'gemini')
  provider_name: string;
  // Whether the provider is operational and reachable
  is_available: boolean;
  // Target model name configured for this channel
  configured_model: string;
  // Human-readable diagnostic description
  status_message: string;
}

/**
 * Overall health diagnostic response from the gateway endpoint.
 */
export interface GatewayHealthResponse {
  // Status reports across all three channels
  channels: ProviderHealthStatus[];
  // The recommended channel that will be attempted first on subsequent turns
  recommended_active_channel: string;
}