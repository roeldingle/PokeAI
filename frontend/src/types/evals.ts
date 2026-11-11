/**
 * AI Evals & Safety Guardrails TypeScript Contracts (Lesson 11)
 * Synchronized with backend/src/schemas/evals_schema.py
 */

export interface GuardrailCheckRequest {
  candidate_text: string;
  allowed_move_names?: string[];
}

export interface GuardrailCheckResponse {
  is_safe_output: boolean;
  was_prompt_injection_detected: boolean;
  was_toxicity_detected: boolean;
  was_rule_hallucination_detected: boolean;
  sanitized_output_text: string;
  violation_reasons: string[];
}

export interface EvalScenarioResult {
  scenario_id: number;
  scenario_name: string;
  category: string;
  expected_action: string;
  ai_selected_action: string;
  passed: boolean;
  execution_latency_ms: number;
}

export interface EvalBenchmarkSuiteResponse {
  total_scenarios: number;
  passed_scenarios: number;
  accuracy_percentage: number;
  average_turn_latency_ms: number;
  guardrail_blocks_triggered: number;
  is_production_sla_met: boolean;
  scenario_results: EvalScenarioResult[];
}
