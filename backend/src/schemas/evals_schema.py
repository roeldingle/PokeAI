"""
Evals & Guardrails Schema Module (Lesson 11)
Defines Pydantic v2 data contracts for the Safety Guardrails Filter
and the 20-Scenario Production AI Evaluation Benchmark Matrix.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GuardrailCheckRequest(BaseModel):
    """
    Request payload for scanning trainer input or AI output through the Stadium Guardrails Filter.
    """
    # Text string to inspect (either user input or LLM output)
    candidate_text: str = Field(
        ...,
        min_length=1,
        description="Input prompt or generated AI output text to validate.",
    )
    # Optional list of legal unlocked move names to check for move hallucinations
    allowed_move_names: Optional[List[str]] = Field(
        default=None,
        description="Optional whitelist of unlocked move names for hallucination verification.",
    )


class GuardrailCheckResponse(BaseModel):
    """
    Result of running the Stadium Safety & Anti-Hallucination Guardrails Filter.
    """
    # True if no prompt injection, toxicity, or rule hallucination was detected
    is_safe_output: bool = Field(
        ...,
        description="True if candidate text passed all safety and rule guardrails.",
    )
    # True if an adversarial prompt injection attempt was intercepted
    was_prompt_injection_detected: bool = Field(
        default=False,
        description="True if prompt injection patterns were detected.",
    )
    # True if toxic or unsportsmanlike language was intercepted
    was_toxicity_detected: bool = Field(
        default=False,
        description="True if toxic or inappropriate content was detected.",
    )
    # True if the text attempted to cheat combat math or use locked/illegal moves
    was_rule_hallucination_detected: bool = Field(
        default=False,
        description="True if illegal moves or rule hallucinations were detected.",
    )
    # Clean, safe text approved for rendering in the stadium UI
    sanitized_output_text: str = Field(
        ...,
        description="Original text if safe, or deterministic safe stadium fallback if blocked.",
    )
    # List of human-readable violation codes triggered
    violation_reasons: List[str] = Field(
        default_factory=list,
        description="Detailed reasons for any guardrail blocks triggered.",
    )


class EvalScenarioResult(BaseModel):
    """
    Grading result for an individual golden-dataset evaluation scenario.
    """
    # Numerical scenario index (1 to 20)
    scenario_id: int = Field(..., ge=1, description="Scenario identifier (1 to 20).")
    # Descriptive title of the evaluation test case
    scenario_name: str = Field(..., description="Human-readable scenario title.")
    # Category of AI capability tested (Tactical RAG, Autonomous Agent, Guardrails)
    category: str = Field(..., description="Evaluation category.")
    # Mathematically optimal or expected action
    expected_action: str = Field(..., description="Golden expected move or guardrail action.")
    # Actual action selected by the AI service
    ai_selected_action: str = Field(..., description="Action produced by the AI system.")
    # Whether the AI matched the golden expectation
    passed: bool = Field(..., description="True if AI output matched expected golden action.")
    # Execution latency for this scenario in milliseconds
    execution_latency_ms: float = Field(..., ge=0.0, description="Execution time in milliseconds.")


class EvalBenchmarkSuiteResponse(BaseModel):
    """
    Comprehensive telemetry report for the 20-Scenario Production AI Evaluation Suite.
    """
    # Total number of golden scenarios evaluated
    total_scenarios: int = Field(..., ge=1, description="Total scenarios in benchmark suite.")
    # Number of scenarios that passed
    passed_scenarios: int = Field(..., ge=0, description="Number of passing scenarios.")
    # Overall pass rate percentage (0.0 to 100.0)
    accuracy_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of golden scenarios passed (SLA >= 85.0%).",
    )
    # Mean turn evaluation latency in milliseconds
    average_turn_latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Average turn execution latency in milliseconds (SLA < 1500ms).",
    )
    # Number of adversarial injection/hallucination scenarios successfully blocked
    guardrail_blocks_triggered: int = Field(
        ...,
        ge=0,
        description="Count of adversarial attacks intercepted by GuardrailsService.",
    )
    # True if accuracy >= 85% and average latency < 1500ms
    is_production_sla_met: bool = Field(
        ...,
        description="True if all production accuracy and latency SLAs are satisfied.",
    )
    # Row-by-row breakdown of all 20 scenarios
    scenario_results: List[EvalScenarioResult] = Field(
        ...,
        description="Individual results for each of the 20 golden scenarios.",
    )
