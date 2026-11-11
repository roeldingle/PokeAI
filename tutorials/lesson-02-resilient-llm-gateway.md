# Tutorial: Lesson 02 - Awakening the AI Brain (The Resilient LLM Gateway Pattern)

> **Branch Checkpoints**:
> - Starter Code: `git checkout lesson-02-starter`
> - Reference Solution: `git checkout lesson-02-solution`

---

## 1. Lesson Overview & Architecture

In **Lesson 01**, we constructed the tournament onboarding concourse: collecting trainer identification, selecting a partner monster, and persisting the profile into server memory.

In **Lesson 02**, our Game Guide's AI Brain officially awakens! Rather than tying our battler to a single brittle cloud endpoint that could crash mid-battle upon reaching a rate limit, we engineer the **Three-Channel Tactical Radio Gateway** using **LangChain**:
- **Channel 1 (Tactical Belt Radio)**: Local Ollama runtime (`http://localhost:11434`, `qwen2.5:3b`). Free, private, zero internet required.
- **Channel 2 (High-Speed Satellite Relay)**: Groq Cloud API (`qwen/qwen3.8-27b`). Sub-200ms ultra-fast inference.
- **Channel 3 (Grandmaster Direct Hotline)**: Google Gemini Cloud API (`gemini-3.1-flash-lite`). Deep strategic reasoning backup.
- **Emergency Offline Fallback**: Deterministic safety rules engine that prevents 500 crashes if all towers are dark.

### Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Frontend Handheld Client (1200px Chassis)"]
        CONFIRM["Registration Confirmed Screen<br/>(Dynamic AI Greeting)"]
        TESTBENCH["Resilient Gateway Testbench Screen<br/>(Storyboard Screen 1)"]
        HUD["ProviderStatusBadge.tsx<br/>[🟢 OLLAMA: qwen2.5:3b | ⚡ 2062ms]"]
    end

    subgraph Backend["FastAPI Stadium Referee"]
        ROUTES["POST /api/v1/ai/guide/greeting<br/>POST /api/v1/ai/generate<br/>GET /api/v1/ai/health"]
        PROMPTS["LangChain ChatPromptTemplate<br/>(prompts/guide_prompts.py)"]
        GATEWAY["ResilientLLMGateway Service<br/>(core/llm_gateway.py)"]
        PROVIDER["LLM Provider Factory<br/>(core/llm_provider.py)"]
        CALLBACK["ResilientGatewayCallbackHandler<br/>(AsyncCallbackHandler)"]
    end

    subgraph Cascade["LangChain Resilient Model Cascade (.with_fallbacks)"]
        CH1["Primary: ChatOllama (Local :11434)<br/>qwen2.5:3b"]
        CH2["Fallback 1: ChatGroq (Fast Cloud)<br/>qwen/qwen3.8-27b"]
        CH3["Fallback 2: ChatGoogleGenerativeAI (Reasoning)<br/>gemini-3.1-flash-lite"]
        OFFLINE["Emergency: Pre-baked Offline Dialogue"]
    end

    CONFIRM -->|POST /api/v1/ai/guide/greeting| ROUTES
    TESTBENCH -->|POST /api/v1/ai/generate| ROUTES
    ROUTES --> PROMPTS
    PROMPTS --> GATEWAY
    GATEWAY --> PROVIDER
    PROVIDER --> CALLBACK

    PROVIDER -->|with_fallbacks| CH1
    CH1 -- Connection Refused / Timeout -->|Auto Failover| CH2
    CH2 -- Rate Limit / Quota Exceeded -->|Auto Failover| CH3
    CH3 -- All External Down --> OFFLINE

    CALLBACK -->|Telemetry Envelope| HUD
    CALLBACK -->|Streamed Dialogue| CONFIRM
    CALLBACK -->|Prompt Telemetry| TESTBENCH
```

---

## 2. Core AI Engineering Concepts Explained

### The Stadium Metaphor: The Three-Channel Headset
Imagine coaching high-stakes tournament matches:
- Your primary channel is the battery-powered walkie-talkie on your tactical belt. It costs nothing and works even during arena power surges.
- If interference blocks Channel 1, your headset silently hops within milliseconds to satellite feed Channel 2.
- If satellite feeds saturate, your headset switches to Channel 3.
- If all radios fail, you read directly from your laminated emergency playbook. The game **never freezes or stops**.

### Technical Pillars in Production AI Engineering

#### 1. High Availability & Automated Failover Cascades
In production AI engineering, single-provider dependency is an anti-pattern. Providers suffer outages, cold starts, and HTTP 429 rate limits. Using LangChain's `.with_fallbacks([backup_1, backup_2])` enables declarative, resilient fallback chains that fail gracefully.

#### 2. Environment-Aware Routing (`APP_ENV`)
In local development (`APP_ENV=local`), localhost Ollama is preferred to eliminate API costs. In staging or production cloud deployments (`APP_ENV=production`), localhost is unreachable, so the gateway routes directly to Groq with Gemini as backup.

#### 3. High-Precision Latency Telemetry (`time.perf_counter()`)
Every production AI service must track execution latency. We record wall-clock round-trip time in milliseconds and package it in the `LLMResponseEnvelope` alongside `active_provider_name` and `fallback_triggered`.

#### 4. Separation of Prompt Templates from Application State
Prompt text is isolated in `src/prompts/guide_prompts.py` using LangChain's `ChatPromptTemplate`. Global stadium configurations (like `config.GAME_GUIDE`) bind dynamically, while trainer-specific attributes are supplied per request.

---

## 3. Step-by-Step Build Walkthrough

### Step 3.1: Python Dependencies & Configuration
Configure `backend/requirements.txt`:
```txt
langchain-core>=0.3.0
langchain-ollama>=0.2.0
langchain-groq>=0.2.0
langchain-google-genai>=2.0.0
```

Configure `backend/.env` & `backend/src/core/config.py`:
```python
# API Keys & Endpoints
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model Definitions
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Model Hyperparameters
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "250"))
```

### Step 3.2: Pydantic v2 & TypeScript Data Contracts
Define `LLMResponseEnvelope` in `backend/src/schemas/ai_gateway_schema.py` and mirror in `frontend/src/types/aiGateway.ts`:
```python
class LLMResponseEnvelope(BaseModel):
    active_provider_name: Literal["ollama", "groq", "gemini", "offline_fallback"]
    model_identifier: str
    execution_latency_milliseconds: float
    fallback_triggered: bool
    generated_message_content: str
```

### Step 3.3: LLM Provider Factory (`backend/src/core/llm_provider.py`)
Implements clean text extraction across multiple chunk schemas and assembles `.with_fallbacks()`:
```python
def create_resilient_ai_brain(temperature: float = TEMPERATURE, max_output_tokens: int = MAX_OUTPUT_TOKENS):
    local_ollama_model = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, timeout=2.0)
    groq_cloud_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, max_retries=1)
    gemini_cloud_model = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, max_retries=1)

    backup_models = [m for m in [groq_cloud_model, gemini_cloud_model] if m]
    if APP_ENV == "local":
        return local_ollama_model.with_fallbacks(backup_models) if backup_models else local_ollama_model
    return backup_models[0].with_fallbacks(backup_models[1:])
```

### Step 3.4: Resilient Gateway & Telemetry Callbacks (`backend/src/core/llm_gateway.py`)
Intercepts invocation lifecycle events via `ResilientGatewayCallbackHandler(AsyncCallbackHandler)` to record `active_provider_name`, model tag, and failover status.

### Step 3.5: REST Endpoints & Frontend HUD
- `GET /api/v1/ai/health`: Probes channel readiness.
- `POST /api/v1/ai/guide/greeting`: Formats persona prompt and generates dynamic welcome.
- `ProviderStatusBadge.tsx`: Displays Daylight Stadium HUD pill with active provider dot and latency meter.
- `AIGatewayTestbenchScreen.tsx`: Storyboard Screen 1 interactive testbench.

---

## 4. Verification & Testing Playbook

Execute the automated test suite verifying failover, dynamic greeting, and health endpoints:

```powershell
backend/.venv/Scripts/python -m pytest backend/tests -v
```

Expected output:
```text
backend/tests/test_config.py::test_configuration_values_loaded PASSED
backend/tests/test_config.py::test_get_metadata_endpoint_success PASSED
backend/tests/test_config.py::test_root_status_endpoint PASSED
backend/tests/test_llm_gateway.py::test_gateway_primary_channel_ollama_success PASSED
backend/tests/test_llm_gateway.py::test_gateway_emergency_offline_fallback_when_all_fail PASSED
backend/tests/test_llm_gateway.py::test_game_guide_dynamic_greeting_generation PASSED
backend/tests/test_llm_gateway.py::test_api_route_ai_health_endpoint PASSED
backend/tests/test_llm_gateway.py::test_api_route_game_guide_greeting_endpoint PASSED
backend/tests/test_onboarding.py::test_get_available_starters_returns_three_monsters PASSED
backend/tests/test_onboarding.py::test_register_trainer_profile_success PASSED
backend/tests/test_onboarding.py::test_register_trainer_fails_on_invalid_starter_id PASSED
backend/tests/test_onboarding.py::test_register_trainer_fails_on_short_name PASSED
============================== 12 passed in 1.2s ==============================
```

Verify frontend build:
```powershell
cd frontend; npm run build; cd ..
```

---

## 5. Common Pitfalls & Troubleshooting Guide

| Issue / Error Message | Root Cause | Solution |
| :--- | :--- | :--- |
| `Microsoft Visual C++ 14.0 or greater is required` | Virtual environment was created with experimental Python 3.15, which lacks pre-compiled wheels for C-dependencies like `zstandard`. | Recreate `.venv` with Python 3.12 (`py -3.12 -m venv backend/.venv`), which has 100% pre-compiled binary wheels for all LangChain dependencies. |
| `AttributeError: module 'src.core.config' has no attribute 'application_environment'` | Old tests expected lowercase names after transitioning `config.py` to uppercase. | Synchronize `test_config.py` to assert the uppercase constants (`config.APP_ENV`, `config.GAME_GUIDE`, etc.). |
| Trainer name not highlighted in Game Guide dialogue speech | Case mismatch: trainer registered as uppercase (`ROJAY GAMER`), but LLM generated lowercase (`rojay gamer`), and `string.includes()` is case-sensitive. | Use regex-based case-insensitive matching (`new RegExp(...)`) in `GameGuideDialogBox.tsx` so all case variations wrap in the royal-blue badge. |
| LLM obeys prompt injection (`IGNORE YOUR RULE`) | Lightweight 3B models (`qwen2.5:3b`) have weak instruction hierarchy defense when user prompts are directly concatenated. | This vulnerability is intentional for Lesson 02! It sets the stage for **Lesson 11**, where we implement XML delimiter sandboxing and defensive guardrails. |

---

## 6. Self-Study Challenge

1. **Simulate a Provider Outage**: Stop your local Ollama daemon (`Stop-Process -Name "ollama"`), then click `[ ⚡ PING AI GATEWAY ]` in the testbench. Observe the top-right HUD badge hop from `OLLAMA` to `GROQ` and display the `FALLBACK` badge!
2. **Dynamic Guide Persona**: Change `GAME_GUIDE="Professor Oak"` in your `backend/.env`. Observe the nameplate and AI dialogue dynamically re-anchor to Professor Oak without touching any code!

---

## 7. Next Lesson Teaser

Now that our AI Brain is awake and resilient, where does it get authentic Pokémon lore, moves, and battle statistics?

In **[Lesson 03: The Pokémon Researcher's Telescope — Async PokéAPI Ingestion](lesson-03-pokeapi-client.md)**, we construct a high-speed, non-blocking asynchronous ingestion client using `httpx.AsyncClient` and token bucket rate-limiting to ingest official Gen-1 battle statistics directly from the public PokéAPI!
