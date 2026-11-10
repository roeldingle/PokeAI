# Product Requirements & Course Specification Document (PRD)

## Project: AI Engineering "Zero to Hero" — Turn-Based Monster Battle Game (PokeAI Arena)

---

## 1. Executive Summary & Educational Vision
**PokeAI Arena** is a comprehensive, production-grade AI Engineering curriculum packaged as a turn-based, Pokémon-like combat application.

The course bridges the gap between toy AI tutorials and professional software engineering. Rather than treating AI as simple one-off API calls, learners implement resilient fallbacks, structured schema guarantees, Retrieval-Augmented Generation (RAG) using dense vector spaces, multi-agent systems, real-time streaming, and automated evaluation suites.

The repository is published on GitHub as an interactive, follow-along open-source curriculum featuring branch-based checkpoints (`lesson-XX-starter`, `lesson-XX-solution`), step-by-step tutorial guides in `/tutorials/`, and automated GitHub Actions continuous integration.

---

## 2. GitHub Tutorial & Distribution Architecture

### 2.1 Branching Model & Release Strategy
The GitHub repository uses a **Dual-Track Learning Architecture**:
- **`main` Branch**: Contains the complete documentation, the `/tutorials/` directory (Lessons 1-8 markdown guides), shared documentation/ADRs, and the reference production codebase.
- **`lesson-XX-starter` Branches**: Minimal starter branch for each lesson with boilerplate, interfaces, and explicit `TODO:` markers with descriptive instructions.
- **`lesson-XX-solution` Branches**: Fully implemented, passing reference code for that exact lesson milestone.

```
git checkout lesson-01-starter    # Learner starts lesson 1 with guidance & tests
# ... student implements the tasks guided by /tutorials/lesson-01-setup-and-gateway.md ...
git diff origin/lesson-01-solution # Learner can inspect the reference solution at any time
```

### 2.2 Conventional Commits & Pull Request Template
All contributions, branches, and milestones follow the Conventional Commits specification:
- `feat(lesson-01): implement resilient llm fallback gateway`
- `test(lesson-02): add vector similarity assertions for pokedex rag`
- `docs(adr): record architectural decision for chromadb vector storage`

Automated GitHub Actions (`.github/workflows/ci.yml`) runs:
1. `ruff check backend/` & `ruff format --check backend/`
2. `pytest backend/tests/` (unit tests + mock AI evaluations)
3. `npm run lint` & `npm run test` in `frontend/`

---

## 3. Technology Stack & Directory Structure

```text
PokeAI (PokeAI Monorepo)
├── .github/
│   ├── workflows/
│   │   └── ci.yml                          # Continuous Integration test runner
│   └── PULL_REQUEST_TEMPLATE.md            # Self-assessment checklist for learners
├── backend/                                # Python 3.12+ (FastAPI + ChromaDB)
│   ├── .venv/                              # Dedicated Python 3.12 virtual environment
│   ├── src/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                   # Centralized .env loader (GAME_TITLE, GAME_GUIDE, CORS)
│   │   │   └── llm_gateway.py              # Resilient LLM routing gateway (Lesson 1+)
│   │   ├── routes/                         # FastAPI route controllers (REST + SSE/WS)
│   │   ├── schemas/                        # Pydantic v2 domain & battle models
│   │   ├── services/                       # Business logic, PokeAPI client, RAG & Agent loops
│   │   └── main.py                         # FastAPI application entry point
│   ├── tests/                              # Pytest unit tests, contract tests & AI evals
│   ├── .env                                # Local environment variables (git-ignored)
│   ├── .env.example                        # Template environment variables for learners
│   ├── README.md                           # Backend setup & run instructions
│   └── requirements.txt                    # Python package dependencies
├── frontend/                               # Vite + React 18 + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/                     # Landing, Right-Side Guide Overlay, Arena, HUD
│   │   ├── hooks/                          # EventSource streaming hooks, keyboard listeners
│   │   ├── types/                          # TypeScript definitions mirroring backend schemas
│   │   └── services/                       # API client & SSE listeners
│   └── tests/                              # Vitest component & hook tests
├── tutorials/                              # Step-by-step markdown tutorial guides
│   ├── lesson-00-foundation-and-env.md     # L0: Monorepo Setup, FastAPI <-> React & .env config
│   ├── lesson-01-guide-and-starters.md     # L1: Right-Side Guide Shaneil, Name Input & 3 Starters
│   ├── lesson-02-resilient-llm-gateway.md  # L2: Awakening Shaneil's AI Brain (Ollama/Groq/Gemini)
│   ├── lesson-03-pokeapi-client.md         # L3: Async PokeAPI Ingestion Service (httpx)
│   ├── lesson-04-chromadb-vector-pokedex.md# L4: Dense Text Embeddings & Semantic Pokédex Search
│   ├── lesson-05-gba-battle-engine.md      # L5: Classic GBA Battle Arena & Deterministic Combat
│   ├── lesson-06-progression-and-team.md   # L6: 5-Turn Clock, TEAM Swap & +1% Stat Progression
│   ├── lesson-07-catch-roulette.md         # L7: The Catch Pokémon Roulette Phase (4 Ball Tiers)
│   ├── lesson-08-rag-coach-shaneil.md      # L8: The ASK GUIDE Tactical RAG Coach (Right Overlay)
│   ├── lesson-09-gym-leader-agent.md       # L9: Autonomous Opponent AI & Dynamic Threat Calibration
│   ├── lesson-10-live-announcer-sse.md     # L10: Multi-Agent Live Stadium Announcer (SSE Streaming)
│   └── lesson-11-evals-and-docker.md       # L11: Automated Pytest Evals, Guardrails & Docker CI/CD
├── docs/
│   └── adr/                                # Architecture Decision Records
├── .gitignore
├── AGENTS.md                               # Agent operating instructions & coding standards
├── GEMINI.md                               # Gemini workspace context & conventions
├── CONCEPTS_AND_TECH_GUIDE.md              # Intuitive concept & tech guide (Mental models & analogies)
├── STORYBOARD.md                           # Progressive Lesson 0-11 UI wireframes & AI payloads
├── PRODUCT_DOCUMENT.md                     # Product requirements & syllabus
├── PROJECT_PROMPT.md                       # Developer agent agreement & coding rules
└── README.md                               # Root repository quickstart
```

---

## 4. Standard 6-Section Tutorial Template & Pacing Rule of 3
To guarantee that no single lesson ever feels cramped or overwhelming, every lesson strictly adheres to the **"Rule of 3"**:
- **Max 2 to 4 Files**: Each lesson creates or modifies only 2–4 focused files.
- **1 Standalone MVP Feature**: Delivers exactly 1 testable, visible feature increment.
- **1 Verification Gate**: Verified by a single terminal test command (`pytest ...` / `npm run test`).
- **Estimated Completion Time**: 30–45 minutes per lesson.

Every tutorial guide inside `tutorials/lesson-XX-*.md` contains:
1. **Lesson Goal & Architecture Diagram**: Visual mermaid diagram of the milestone.
2. **Core AI Concept Explained**: Pedagogical deep-dive with stadium metaphors.
3. **Step-by-Step Build Walkthrough**: Explicit terminal commands and line-by-line annotated code with descriptive variable names.
4. **Testing & Verification Gate**: Exact test command & expected output.
5. **Common Pitfalls & Debugging Guide**: Solutions for real-world issues.
6. **Self-Study Challenge**: An optional homework exercise to deepen mastery.

---

## 5. Comprehensive 12-Lesson Modular Blueprint (Lesson 0 – Lesson 11)

---

### Phase 1: Foundations, Onboarding & Guide's AI Brain (Lessons 0 – 2)

#### Lesson 0: Full-Stack Foundations, `.env` Config & Landing Title Screen
- **Pacing**: 3 backend files (`.env`, `src/core/config.py`, `src/main.py`), 1 test (`tests/test_config.py`), 1 screen component (`components/screen/LandingTitleScreen.tsx`), 2 reusable UI components (`components/ui/CharacterUI.tsx`, `components/ui/ButtonUI.tsx`).
- **Concept**: Centralized environment configuration and REST handshake between Python 3.12 (FastAPI) and React 18 / TypeScript (Vite).
- **Design System**: Daylight Stadium Light Palette (max-width: 960px, `#ffffff` handheld casing, `#e2e8f0` outer slate, GBA dual-bevel button framework with bobbing red pointers).
- **MVP Deliverable**: Retro landing screen displaying `GAME_TITLE="PokeAI"`, `VERSION="0.1.0"`, `PROJECT_GOAL`, and `GAME_DESCRIPTION` loaded dynamically from `backend/.env` via `config.py`, animated Pikachu mascot (`CharacterUI`), and GBA tactile continue button (`ButtonUI`).
- **Key Schema**:
  ```python
  class GameMetadataResponse(BaseModel):
      application_environment: str = Field(description="Environment classification e.g. local")
      game_version: str = Field(description="Semver game version e.g. 0.1.0")
      project_learning_goal: str = Field(description="High-level pedagogical mission")
      game_title: str = Field(description="Title of the game: PokeAI")
      game_description: str = Field(description="Tagline description")
      game_guide_name: str = Field(description="Name of the game guide: Shaneil")
  ```
- **Verification Gate**: `pytest backend/tests/test_config.py` passes 100%.

---

#### Lesson 1: Right-Side Game Guide (`Shaneil`) JRPG Onboarding & Starter Selection
- **Pacing**: 2 backend files (`schemas/onboarding_schema.py`, `routes/onboarding_routes.py`), 1 test (`tests/test_onboarding.py`), 3 UI components (`GameGuideDialogBox.tsx`, `PlayerNameInputScreen.tsx`, `StarterSelectionScreen.tsx`).
- **Concept**: Client-server state machines and reusable dialogue overlay architectures.
- **MVP Deliverable**: Guide **Shaneil** welcomes the player on the **RIGHT side** of the dialogue box (`[Press A to Next ▸]`), prompts for Trainer Name input, presents 3 Starter Monsters (**Bulbasaur**, **Charmander**, **Squirtle**), and persists the Trainer Profile to backend memory.
- **Key Schema**:
  ```python
  class TrainerRegistrationRequest(BaseModel):
      trainer_name: str = Field(min_length=2, max_length=20)
      selected_starter_id: int = Field(ge=1, le=3)
  ```
- **Verification Gate**: `pytest backend/tests/test_onboarding.py` passes 100%.

---

#### Lesson 2: Awakening Shaneil's AI Brain — Resilient LLM Gateway
- **Pacing**: 2 backend files (`core/llm_gateway.py`, `routes/health_routes.py`), 1 test (`tests/test_llm_gateway.py`), 1 UI component (`ProviderStatusBadge.tsx`).
- **Concept**: The **Resilient Gateway Pattern** with automated failover: **Ollama (local)** -> **Groq (fast cloud)** -> **Gemini (reasoning cloud)**.
- **MVP Deliverable**: Shaneil dynamically greets the newly registered trainer by name with personalized starter commentary; frontend HUD displays an active provider badge with live round-trip latency in milliseconds.
- **Key Schema**:
  ```python
  class LLMResponseEnvelope(BaseModel):
      active_provider_name: str         # "ollama" | "groq" | "gemini"
      execution_latency_milliseconds: float
      model_identifier: str
      generated_message_content: str
  ```
- **Verification Gate**: `pytest backend/tests/test_llm_gateway.py` verifies seamless failover when local Ollama is offline.

---

### Phase 2: External Ingestion & Vector Memory (Lessons 3 – 4)

#### Lesson 3: Asynchronous PokeAPI Client & Structured Ingestion
- **Pacing**: 2 backend files (`services/pokeapi_client.py`, `schemas/pokeapi_schema.py`), 1 test (`tests/test_pokeapi_client.py`), 1 script (`scripts/ingest_starter_lore.py`).
- **Concept**: Non-blocking asynchronous I/O with `httpx`, token bucket rate-limiting, and structured data normalization using Pydantic v2.
- **MVP Deliverable**: Async service ingesting raw Pokémon combat metrics, moves, elemental types, and species lore descriptions from PokéAPI into clean Python domain models.
- **Key Schema**:
  ```python
  class PokemonSpeciesLoreRecord(BaseModel):
      pokemon_id: int
      pokemon_name: str
      elemental_types: list[str]
      base_stats: dict[str, int]
      abilities: list[str]
      lore_flavor_text: str
  ```
- **Verification Gate**: `pytest backend/tests/test_pokeapi_client.py` passes with mocked HTTP fixtures.

---

#### Lesson 4: ChromaDB Vector Memory & Semantic Pokédex Search
- **Pacing**: 2 backend files (`core/chroma_manager.py`, `services/vector_ingestion_service.py`), 1 test (`tests/test_vector_search.py`), 1 UI component (`PokedexSearch.tsx`).
- **Concept**: Dense vector embeddings, cosine distance, and semantic similarity search vs exact keyword matching.
- **MVP Deliverable**: Natural language Pokédex search bar where querying *"fiery lizard with high special attack"* returns Charizard with a semantic confidence score above 0.75.
- **Key Schema**:
  ```python
  class SemanticSearchResult(BaseModel):
      pokemon_name: str
      similarity_confidence_score: float
      matched_lore_snippet: str
  ```
- **Verification Gate**: `pytest backend/tests/test_vector_search.py` confirms top-k retrieval accuracy.

---

### Phase 3: Classic GBA Battle Arena, Rules & Roulette (Lessons 5 – 7)

#### Lesson 5: Classic GBA Battle Arena & Deterministic Damage Engine
- **Pacing**: 2 backend files (`services/battle_engine.py`, `schemas/battle_schema.py`), 1 test (`tests/test_battle_engine.py`), 1 UI component (`BattleArenaView.tsx`).
- **Concept**: Deterministic rule modeling, separation of game state from AI generative logic, and structured move selection.
- **MVP Deliverable**: Classic retro GBA arena (Opponent Pidgey Lv 5 top-left with HP bar and top-right sprite on grass patch; Player Charmander Lv 6 bottom-left sprite on grass patch and bottom-right HUD with HP `20/20`). Clicking `FIGHT` transitions to a **GBA 2x2 Move Grid** displaying the 2 starting moves (e.g. Scratch & Growl) with Elemental Type badges, PP (`25/25`), **Inline Effectiveness Badges** (e.g. `Super Effective 2x`, `Neutral 1x`), locked move slots (`[🔒 Locked: 10 Wins]`, `[🔒 Locked: 20 Wins]`), and a `[B] BACK` button.
- **Key Schema**:
  ```python
  class PokemonMoveSlot(BaseModel):
      move_id: int
      move_name: str
      elemental_type: str
      base_power: int
      current_power_points: int
      maximum_power_points: int
      is_unlocked: bool = True
      unlock_victory_threshold: int = 0  # 0 for starters, 10 for slot 3, 20 for slot 4

  class TurnResolutionResult(BaseModel):
      attacker_name: str
      defender_name: str
      move_selected: str
      damage_inflicted: int
      type_effectiveness_multiplier: float  # e.g., 2.0 (Super Effective), 0.5, 1.0
      defender_remaining_hp: int
  ```
- **Verification Gate**: `pytest backend/tests/test_battle_engine.py` asserts exact damage formulas, type match-up multipliers, and PP decrement on execution.

---

#### Lesson 6: 5-Turn Battle Clock, `TEAM` Swap & +1% Stat Progression per Victory
- **Pacing**: 2 backend files (`services/battle_progression_service.py`, `schemas/progression_schema.py`), 1 test (`tests/test_battle_progression.py`), 1 UI component (`TeamSwapModal.tsx`).
- **Concept**: Dynamic entity state tracking, state machine rule enforcement, dynamic threat calibration for AI agents, and move slot unlocks.
- **MVP Deliverable**: 5-turn match clock (`turn_counter <= 5`), `TEAM` party swap button (disabled if pool has 1 monster; pre-turn swap only), auto-recruit on knockout, and **+1% incremental stat boost per victory** (`stat_progression_multiplier = 1.0 + (victories_count * 0.01)`). Reaching **10 victories** unlocks **Move Slot 3** (e.g. Ember [Fire]); reaching **20 victories** unlocks **Move Slot 4** (e.g. Flamethrower [Fire]).
- **Key Formula**:
  $$\text{effective\_stat} = \text{round}(\text{base\_stat} \times (1.0 + \text{victories\_count} \times 0.01))$$
- **Verification Gate**: `pytest backend/tests/test_battle_progression.py` verifies turn limits, disabled swaps with 1 monster, +1% stat scaling, and move slot unlocking at exactly 10 and 20 victories.

---

#### Lesson 7: Catch Pokémon Roulette Phase (Turn 5 Limit)
- **Pacing**: 2 backend files (`services/catch_roulette_service.py`, `schemas/catch_schema.py`), 1 test (`tests/test_catch_roulette.py`), 1 UI component (`CatchRouletteModal.tsx`).
- **Concept**: Weighted probability distributions, state machine transitions, and interactive UI animations.
- **MVP Deliverable**: Triggered if opponent is still standing after Turn 5. A retro spinning wheel lands on a Pokéball tier (**Gold 90%**, **Silver 75%**, **Bronze 60%**, **Normal 50%**) with a 3-wobble capture animation and pool recruitment.
- **Key Schema**:
  ```python
  class CatchRouletteOutcome(BaseModel):
      selected_pokeball_tier: str  # "GOLD" | "SILVER" | "BRONZE" | "NORMAL"
      capture_probability: float   # 0.90 | 0.75 | 0.60 | 0.50
      capture_successful: bool
      captured_monster_name: str
  ```
- **Verification Gate**: `pytest backend/tests/test_catch_roulette.py` statistically validates random seed outcomes against exact tier probabilities.

---

### Phase 4: Multi-Agent Systems, Live Streaming & Production (Lessons 8 – 11)

#### Lesson 8: `ASK GUIDE` Tactical Battle Whisperer (Shaneil Right-Side Overlay)
- **Pacing**: 2 backend files (`services/coach_rag_service.py`, `prompts/coach_prompts.py`), 1 test (`tests/test_coach_rag.py`), 1 UI component (`TacticalGuideOverlay.tsx`).
- **Concept**: In-Context Learning (ICL) and Dynamic RAG under strict latency SLAs.
- **MVP Deliverable**: Selecting `ASK GUIDE` from the 2x2 action menu pauses battle and slides in Guide **Shaneil's right-side overlay**; she queries ChromaDB for active opponent weaknesses and whispers winning counter-moves.
- **Key Schema**:
  ```python
  class CoachTacticalAdviceResponse(BaseModel):
      recommended_action_name: str
      tactical_justification: str
      confidence_rating: float
  ```
- **Verification Gate**: `pytest backend/tests/test_coach_rag.py` confirms coach recommends super-effective moves against known opponent types.

---

#### Lesson 9: Autonomous Gym Leader AI Agent (Dynamic Threat Calibration)
- **Pacing**: 2 backend files (`services/gym_leader_agent.py`, `prompts/gym_leader_prompts.py`), 1 test (`tests/test_gym_leader_agent.py`), 1 UI component (`GymLeaderBadge.tsx`).
- **Concept**: Autonomous single-agent decision loops (`Perceive -> Remember -> Decide -> Act`), persona conditioning, and dynamic threat calibration reacting to the player's +1% stat multiplier.
- **MVP Deliverable**: Gym Leader AI (Brock / Misty) that analyzes combat history, dynamically calibrates its risk model to the player's scaled stats, and emits in-character taunts.
- **Key Schema**:
  ```python
  class GymLeaderTurnDecision(BaseModel):
      selected_move_name: str
      internal_tactical_reasoning: str
      in_character_dialogue_taunt: str
  ```
- **Verification Gate**: `pytest backend/tests/test_gym_leader_agent.py` benchmarks decision quality (>90% optimal move selection under low HP).

---

#### Lesson 10: Live Stadium Announcer via FastAPI SSE Token Streaming
- **Pacing**: 2 backend files (`services/streaming_announcer_service.py`, `routes/streaming_routes.py`), 1 test (`tests/test_streaming_announcer.py`), 2 UI components (`useCommentatorStream.ts`, `CommentatorTickerBar.tsx`).
- **Concept**: Server-Sent Events (SSE) and Multi-Agent Orchestration (Gym Leader acts -> Engine resolves -> Announcer streams).
- **MVP Deliverable**: Retro stadium LED ticker tape running across the top of the arena streaming live play-by-play excitement at 280 tokens/sec.
- **Verification Gate**: `pytest backend/tests/test_streaming_announcer.py` tests event stream ordering and sub-400ms time-to-first-token.

---

#### Lesson 11: Production Evals, Guardrails, Docker & CI/CD Pipeline
- **Pacing**: 2 backend files (`services/guardrails_service.py`, `tests/evals/test_agent_evals.py`), 3 DevOps files (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `.github/workflows/ci.yml`).
- **Concept**: AI testing harnesses (LLM-as-a-judge, safety guardrails), multi-stage Docker builds, and GitHub Actions CI/CD automation.
- **MVP Deliverable**: 20-scenario automated eval suite asserting agent accuracy >85%, safety guardrail filter, and a single `docker compose up` command that boots the full production stack.
- **Verification Gate**: `pytest backend/tests/evals/test_agent_evals.py` passes 20/20 scenarios; `docker compose build` succeeds with zero errors.
