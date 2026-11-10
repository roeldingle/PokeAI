# AGENTS.md — AI Pair-Programming & Pedagogical Standards

> **Project**: **PokeAI** (`GAME_TITLE="PokeAI"`, `GAME_GUIDE="Shaneil"`)
> **Goal**: AI Engineering Path while building a turn-based monster battler game (`Lesson 0` to `Lesson 11`).

---

## 1. Core Operating Rules

1. **DO NOT WRITE CODE UNSOLICITED**:
   - Never generate or modify application code unless explicitly requested by the user.
   - Always present architecture plans, data contracts, or step-by-step explanations first and wait for confirmation.
2. **DESCRIPTIVE VARIABLE & FUNCTION NAMES**:
   - Avoid single-letter or abbreviated names (`p`, `cfg`, `res`, `doc`).
   - Always use self-documenting identifiers (`backend_directory_path`, `environment_file_path`, `raw_origins_environment_variable`, `selected_starter_pokemon_id`).
3. **LINE-BY-LINE EDUCATIONAL COMMENTS**:
   - Every code snippet and file must include clear, intuitive line-by-line comments explaining *what* the line does and *why* it matters in production software and AI engineering.
4. **ACCESSIBLE, INTUITIVE TONE**:
   - Explain concepts using relatable stadium and battle metaphors without jargon or condescension (and never reference age).

---

## 2. Canonical Directory Structure

```text
PokeAI/
├── backend/
│   ├── .venv/
│   ├── src/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── .env
│   ├── .env.example
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── screen/       # Stage & full-screen views (e.g. LandingTitleScreen, StarterSelection)
│   │   │   └── ui/           # Reusable atomic UI widgets (e.g. CharacterUI, ButtonUI, DialogBox)
│   │   ├── services/         # REST API & SSE streaming clients
│   │   ├── types/            # TypeScript data contracts synchronized with Pydantic schemas
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── tutorials/
├── .gitignore
├── AGENTS.md
├── GEMINI.md
├── PRODUCT_DOCUMENT.md
├── PROJECT_PROMPT.md
├── CONCEPTS_AND_TECH_GUIDE.md
├── STORYBOARD.md
└── README.md
```

---

## 3. Frontend Architecture & Visual Design Standards

1. **COMPONENT DIRECTORY DISCIPLINE**:
   - `frontend/src/components/screen/`: Reserved exclusively for complete screens and game stages (e.g., `LandingTitleScreen.tsx`, `PlayerNameInputScreen.tsx`, `StarterSelectionScreen.tsx`, `BattleArenaScreen.tsx`).
   - `frontend/src/components/ui/`: Reserved for atomic, modular, and reusable widgets across lessons (e.g., `CharacterUI.tsx`, `ButtonUI.tsx`, `GameGuideDialogBox.tsx`, `ProviderStatusBadge.tsx`).
2. **DAYLIGHT STADIUM DESIGN SYSTEM**:
   - **Chassis Max-Width**: Centered handheld panoramic viewport locked to `width: 1200px; max-width: 100%;` on desktop with pure-CSS responsive breakpoints for Tablet (`<= 1024px`), Mobile (`<= 768px`), and Small Phones (`<= 480px`).
   - **Light Palette**: Crisp daylight handheld casing (`#ffffff`), soft stadium slate exterior (`#e2e8f0`), and clean parchment card layers (`#f8fafc`).
   - **Pokémon Menu Button Standard (`ButtonUI`)**: Authentic GBA dual-bevel 3D borders (`4px solid #1e293b`), tactile 3px sunken depression on `:active`, and bobbing red cursor arrows (`▶` / `◀`).
   - **Animated Sprite Mascot (`CharacterUI`)**: Pixelated animated sprites (`image-rendering: pixelated`) with circular grounding pedestal shadows.
