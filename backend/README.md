# PokeAI Arena - Backend Engine

The referee and intelligence engine powering the **PokeAI** turn-based monster battler tournament.

## Tech Stack
- **Python 3.12+**
- **FastAPI**: Asynchronous REST & Server-Sent Events (SSE) framework.
- **Pydantic v2**: Type-safe schema validation and deterministic boundary contracts.
- **Pytest**: Automated testing harness.

## Quickstart

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# On macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

### 3. Run the Development Server
```bash
# From the backend directory
uvicorn src.main:app --reload --port 8000
```
Interactive OpenAPI documentation will be accessible at `http://localhost:8000/docs`.

### 4. Run Automated Tests
```bash
# From the workspace root
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\pytest backend/tests -v
```
