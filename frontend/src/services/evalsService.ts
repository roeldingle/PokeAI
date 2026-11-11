/**
 * AI Evals & Safety Guardrails API Service Client (Lesson 11)
 * Communicates with /api/v1/evals endpoints on the FastAPI backend.
 */

import type {
  EvalBenchmarkSuiteResponse,
  GuardrailCheckRequest,
  GuardrailCheckResponse,
} from "../types/evals";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Executes the 20-Scenario Golden AI Evaluation Benchmark Suite on the backend.
 */
export async function runEvalBenchmarkSuite(): Promise<EvalBenchmarkSuiteResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/evals/run-benchmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to execute AI Eval Benchmark Suite (${response.status})`);
  }

  return response.json();
}

/**
 * Scans candidate input/output text through the Stadium Safety Guardrails Filter.
 */
export async function checkStadiumGuardrails(
  payload: GuardrailCheckRequest
): Promise<GuardrailCheckResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/evals/guardrails/check`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(`Guardrail inspection request failed (${response.status})`);
  }

  return response.json();
}
