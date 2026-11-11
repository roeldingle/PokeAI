# PokeAI Arena ⚡

> **A turn-based monster battler engineered step-by-step to master AI Engineering principles.**
> Built with Python 3.12 (FastAPI), React 18, TypeScript, and multi-model AI orchestration.

---

## 🏟️ Project Overview

**PokeAI Arena** guides learners through a comprehensive 12-lesson curriculum (Lesson 0 to Lesson 11) building a classic retro Game Boy Advance style battler powered by real-world AI engineering architectures:
- **Resilient Multi-Provider LLM Gateway**: Automatic failover across local Ollama, fast cloud Groq, and reasoning cloud Google Gemini.
- **RAG & Vector Embeddings**: ChromaDB semantic search over official monster lore and battle histories.
- **Classic GBA 5-Turn Battle Arena**: Deterministic state machine, dynamic 4-move progression, EXP multipliers, and catch roulette probability phases.
- **In-Context AI Battle Guide**: Right-side interactive coaching overlay with the Game Guide (configured dynamically via `.env`).
- **Autonomous Gym Leader AI Agent**: Non-stationary threat calibration, dynamic persona taunts, and memory.
- **Real-Time Token Streaming**: Server-Sent Events (SSE) powering the stadium's top LED ticker tape play-by-play announcer.

---

## 📂 Project Structure

```text
PokeAI/
├── backend/                  # FastAPI arena referee & AI engine
│   ├── .venv/                # Isolated Python virtual environment
│   ├── src/
│   │   ├── core/             # Centralized config & LLM gateways
│   │   ├── routes/           # Domain API routers
│   │   ├── schemas/          # Pydantic v2 data contracts
│   │   ├── services/         # AI orchestration & battle services
│   │   └── main.py           # Application entrypoint & CORS config
│   ├── tests/                # Automated pytest suites
│   ├── .env                  # Runtime configuration
│   ├── .env.example          # Environment template
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 18 + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/       # GBA styled battle and dialogue components
│   │   ├── services/         # API & SSE streaming clients
│   │   └── types/            # TypeScript data contracts
│   └── package.json
├── tutorials/                # 6-section educational guides (Lessons 00 - 11)
├── AGENTS.md                 # Agent pair-programming & pedagogical standards
├── GEMINI.md                 # Technical conventions & context
└── README.md
```

---

## 🚀 Quickstart

### 1. Launch Backend Arena Referee
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 2. Launch Frontend Game Client
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Run Automated Tests
```bash
# Backend pytest suite
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\pytest backend/tests -v
```
