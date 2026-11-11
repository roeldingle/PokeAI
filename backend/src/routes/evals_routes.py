"""
Evals & Safety Guardrails FastAPI Routes Module (Lesson 11)
Exposes REST endpoints for scanning text through the Stadium Safety Guardrails Filter
and executing the 20-Scenario Golden AI Evaluation Benchmark Matrix.
"""

from fastapi import APIRouter
from src.schemas.evals_schema import (
    EvalBenchmarkSuiteResponse,
    GuardrailCheckRequest,
    GuardrailCheckResponse,
)
from src.services.guardrails_service import guardrails_service

# Initialize dedicated router for Lesson 11 AI QA & Guardrails endpoints
evals_router = APIRouter(
    prefix="/api/v1/evals",
    tags=["Lesson 11 - AI Evals & Safety Guardrails"],
)


@evals_router.post(
    "/guardrails/check",
    response_model=GuardrailCheckResponse,
    summary="Inspect candidate trainer input or AI output for safety and rule violations",
)
def check_guardrails_endpoint(
    request_payload: GuardrailCheckRequest,
) -> GuardrailCheckResponse:
    """
    Runs deterministic prompt-injection, toxicity, and move-hallucination filters
    on the supplied candidate text.
    """
    return guardrails_service.inspect_and_sanitize_text(
        candidate_text=request_payload.candidate_text,
        allowed_move_names=request_payload.allowed_move_names,
    )


@evals_router.post(
    "/run-benchmark",
    response_model=EvalBenchmarkSuiteResponse,
    summary="Execute the 20-Scenario Golden AI Evaluation Benchmark Suite",
)
def run_eval_benchmark_post_endpoint() -> EvalBenchmarkSuiteResponse:
    """
    Executes all 20 golden test scenarios across CoachRAGService,
    GymLeaderAgentService, and GuardrailsService and returns the graded matrix.
    """
    return guardrails_service.run_golden_eval_benchmark_suite()


@evals_router.get(
    "/benchmark",
    response_model=EvalBenchmarkSuiteResponse,
    summary="Retrieve the 20-Scenario Golden AI Evaluation Benchmark Suite results",
)
def get_eval_benchmark_endpoint() -> EvalBenchmarkSuiteResponse:
    """
    Convenience GET endpoint returning the 20-scenario golden benchmark telemetry.
    """
    return guardrails_service.run_golden_eval_benchmark_suite()
