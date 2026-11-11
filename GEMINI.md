# GEMINI.md — Workspace Context & Technical Conventions

> Synchronized with [AGENTS.md](file:///c:/Users/roeld.JAYMIE-DESKTOP/Desktop/CODE/projects/PokeAI/AGENTS.md), [PROJECT_PROMPT.md](file:///c:/Users/roeld.JAYMIE-DESKTOP/Desktop/CODE/projects/PokeAI/PROJECT_PROMPT.md), and [PRODUCT_DOCUMENT.md](file:///c:/Users/roeld.JAYMIE-DESKTOP/Desktop/CODE/projects/PokeAI/PRODUCT_DOCUMENT.md).

## 1. Project Identity (`backend/.env` -> `backend/src/core/config.py`)
- **`APP_ENV`**: `local`
- **`VERSION`**: `"0.1.0"`
- **`GAME_TITLE`**: `"PokeAI"`
- **`GAME_DESCRIPTION`**: `"A turn-based monster battler engineered step-by-step to master AI Engineering principles."`
- **`PROJECT_GOAL`**: `"AI Engineering Path while building a turn-based monster battler game."`
- **`GAME_GUIDE`**: Configured dynamically in `.env` (Fallback in `config.py`: `"Game Guide"`)
- **`BACKEND_CORS_ORIGINS`**: `["http://localhost:5173", "http://127.0.0.1:5173"]`

## 2. UI & UX Conventions
- **Chassis Dimensions & Responsive Layout**:
  - Locked **1200px handheld panoramic chassis** (`#root` at `width: 100%`, `.pokeai-viewport` at `width: 1200px; max-width: 100%; flex-shrink: 0;`, `.gba-screen-chassis` with `min-height: 620px; justify-content: space-between;`).
  - Gutter stability enforced with `overflow-y: scroll;` on `html` to prevent layout jumps between stages.
  - **Pure-CSS Responsive Breakpoints**:
    - **Tablet (`<= 1024px`)**: Stacks starter cards in 3 columns across the top with an elevated `310px` Guide sprite (`bottom: 80px`).
    - **Mobile & Tablet Portrait (`<= 768px`)**: Collapses split stages into vertical columns and starter cards into a 1-column stack (`grid-template-columns: 1fr`), with an elevated `240px` Guide sprite (`bottom: 90px`).
    - **Small Phones (`<= 480px`)**: Compact padding, responsive typography, and elevated `215px` Guide sprite (`bottom: 85px`).
- **Game Guide Overlay & Dialogue Box (`GameGuideDialogBox`)**:
  - **Dynamic Nameplate**: Tied directly to backend `.env` metadata (`game_guide_name` e.g., `"Shaneil"` or `"Athena"`).
  - **Player Name Highlighting**: Highlighted with a royal-blue pixel badge (`.trainer-name-highlight-badge`) in the stadium header and inline (`highlightedTerm`) inside dialogue commentary.
  - **Semi-Translucent Glassmorphism**: Frosted glass dialogue chassis (`background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(8px);`) letting the character silhouette and outfit shine through while keeping text 100% sharp and high-contrast.
  - **Elevated Character Sprite**: Anchored at `bottom: 60px` with `height: 420px` (or `360px` on starter selection), giving full visibility to her bust, lavender outfit, Pokéball badge, and guiding hand gesture.
  - **Character Asset**: Young battle guide coach with shoulder-length dark hair, lavender headband, cute compact kitsune fox-ear gaming headset, fair skin, warm open brown eyes, and instructional pose on a clean transparent PNG (`frontend/src/assets/guide_character.png`).
  - **Authentic JRPG Typewriter Effect**: Streams text character-by-character at 20ms/char with pulsing cursor (`▌`). Dual-action interaction: clicking or pressing <kbd>A</kbd>/<kbd>Enter</kbd> while typing immediately skips to the end; clicking when finished triggers stage advance.
- **Lesson 0 & Lesson 1 Onboarding Flow**:
  - **Lesson 0 (Landing Screen)**: Displays `.env` metadata (`GAME_TITLE`, `VERSION`, `GAME_DESCRIPTION`, `PROJECT_GOAL`) fetched from `backend/src/core/config.py` + `"Press Any Key to Continue"`.
  - **Lesson 1 (Game Guide Onboarding & Starters)**:
    1. **Visual Novel Welcome (54% / 46% Split)**: Left 54% holds the tournament welcome banner (`Meet Your Guide`); right 46% gives open stage to the Guide introducing herself via dynamic dialogue box (`[ Press Enter to Continue ▸ ]`).
    2. **Player Name Input (50% / 50% Split)**: Left 50% holds the streamlined Trainer Registration Card with character counter (`0 / 20 characters`) and `Press ↵ ENTER to Confirm`; right 50% gives open stage to the guide sprite.
    3. **Starter Monster Selection (68% / 32% Split)**: Left 68% features the 3 starter cards (**Bulbasaur**, **Charmander**, **Squirtle**) with click-to-highlight, pulsing `★ SELECTED` pill, highlighted player name badge in header & dialogue, and <kbd>Enter</kbd> key confirmation without button clutter; right 32% hosts the guide sprite with zero card overlap. Persistence via `POST /api/v1/onboarding/register`.
    4. **Registration Confirmed (50% / 50% Split)**: Left 50% displays the confirmed Trainer Card summary with highlighted player name badge; right 50% hosts the Guide celebrating registration completion.
- **Lesson 4 (Smart Pokédex & ChromaDB Vector Memory)**:
  - Accessible via `🔍 Open Smart Pokédex` from the Onboarding Complete or Title screen.
  - Features real-time conceptual search input with suggestion chips (e.g., *"fast electric mouse good against water flyers"*, *"fiery lizard with high special attack"*, *"heavy armored water turtle"*).
  - Displays calibrated cosine similarity match badges (`89% Match 🟢`), elemental type pills, base stats preview (`HP`, `ATK`, `DEF`, `SPD`), and species lore snippet.
  - Domain context enrichment with `ELEMENTAL_TYPE_ADVANTAGES` and `CANONICAL_MONSTER_GENERA` ensures asymmetric tactical queries accurately rank counter-types as top candidates.
  - `POST /api/v1/pokedex/seed` dynamically harvests and batch indexes tournament monsters from PokéAPI into persistent ChromaDB storage (`backend/data/chroma`).
- **Battle Mode UI Conventions (Classic GBA Style)**:
  - **Opponent HUD (Top-Left)**: Name (`Pidgey`), Level (`Lv 5`), and green HP bar.
  - **Opponent Front Sprite (Top-Right)**: Perched on circular green grassy platform.
  - **Player Back Sprite (Bottom-Left)**: Perched on circular green grassy platform (`Charmander`).
  - **Player HUD (Bottom-Right)**: Name (`Charmander`), Level (`Lv 6`), HP bar, numerical HP (`20 / 20`), and `EXP` bar.
  - **Top Stadium Ticker Tape**: Dedicated LED ticker tape across the top streaming live AI Commentator play-by-play via SSE.
  - **Bottom Control Area**:
    - Left framed dialogue box: `"Choose an action"` or attack outcome messages (`"Charmander used Ember!"`).
    - Right 2x2 action menu: `FIGHT`, `TEAM`, `ASK GUIDE`, `RUN`.
  - **Attack Move Selection (When Clicking `FIGHT`)**:
    - Replaces the 2x2 action menu with a **GBA 2x2 Move Grid** displaying Move Name, Elemental Type badge, PP (`25/25`), and **Inline Effectiveness Badges** (e.g. `Super Effective 2x`, `Neutral 1x`, `Resisted 0.5x`).
    - Unlocked slots show moves; locked slots show `[🔒 Locked: 10 Wins]` and `[🔒 Locked: 20 Wins]`. Includes a `[B] BACK` button to return to the action menu.
  - **Dynamic Move Pool Progression**:
    - **0 Wins (Start)**: Starter monster starts with **2 basic moves** (e.g. Charmander: *Scratch*, *Growl*).
    - **10 Wins Milestone**: Unlocks **Move Slot 3** (e.g. *Ember* [Fire]) alongside +10% stat boost (`stat_progression_multiplier = 1.10`).
    - **20 Wins Milestone**: Unlocks **Move Slot 4** (e.g. *Flamethrower* [Fire]) alongside +20% stat boost (`stat_progression_multiplier = 1.20`).
  - **Opponent Move Loadout**: Early wild monsters (e.g. Pidgey Lv 5) use 2 basic moves; Gym Leaders enter with 3 or 4 moves scaled to their challenge tier.
  - **`TEAM` Option (`TeamSwapModal`)**: Swaps active monster from the player's pool before Turn 1 begins (`POST /api/v1/battle/team/swap`). If the pool contains only 1 Pokémon, `TEAM` displays `TEAM (🔒 1/1)` and is disabled; after Turn 1 starts, displays `TEAM (Turn 1 Only)` and is disabled.
  - **5-Turn Battle Rule & Single-Line Header**: Every battle lasts a maximum of 5 turns (`⏱️ TURN 1 / 5` to `⏱️ TURN 5 / 5`), displayed directly beside the lesson title in a single-line stadium header (`flex-wrap: nowrap`) to preserve vertical viewport space.
  - **EXP & +1% Stat Progression (`battle_progression_service.py`)**: Winning a battle awards EXP and grants a **+1% incremental stat boost** (`stat_progression_multiplier = 1.0 + (victories_count * 0.01)`) to the active monster's HP, Attack, Defense, and Speed, displayed in the post-battle victory summary banner. This dynamically scales threat levels in AI prompts.
  - **Acquisition Rule 1 (Defeat)**: If the player defeats/KOs the opponent within 5 turns, that Pokémon is automatically added to the player's Pokémon pool.
  - **Acquisition Rule 2 (Catch Roulette Phase — Lesson 7)**: If the opponent is NOT defeated by Turn 5, the battle automatically transitions into the overtime Catch Roulette Phase (`CatchRouletteModal.tsx` & `POST /api/v1/battle/catch/roulette` via `catch_roulette_service.py`):
    - **Gold Pokéball (10% Wheel Odds)**: 90% catch chance
    - **Silver Pokéball (25% Wheel Odds)**: 75% catch chance
    - **Bronze Pokéball (35% Wheel Odds)**: 60% catch chance
    - **Normal Pokéball (30% Wheel Odds)**: 50% catch chance
    - Features rapid carousel cycling, tier landing deceleration, iconic 3-wobble Pokéball animation, and automatic party pool recruitment.
  - **`ASK GUIDE` Action**: Pauses battle and slides in the Game Guide's signature right-side portrait, dynamic nameplate, and dialogue box overlay with RAG tactical advice.
