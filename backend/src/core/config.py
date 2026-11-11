"""
Configuration Settings Module
Centralized management of environment variables, paths, and model configurations,
adhering to the standard PokeAI configuration pattern.
"""

import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Mute noisy HTTP and model-loading info logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

# Resolve path hierarchy: __file__ is in backend/src/core/config.py
CORE_DIR: Path = Path(__file__).resolve().parent
SRC_DIR: Path = CORE_DIR.parent
BACKEND_DIR: Path = SRC_DIR.parent

# Load environment variables from backend/.env file
ENV_FILE_PATH: Path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH)

# --- Environment Mode ---
# local | develop | prod
APP_ENV: str = os.getenv("APP_ENV", "local")

# --- Game Metadata & Identity ---
VERSION: str = os.getenv("VERSION", "0.1.0")
PROJECT_GOAL: str = os.getenv(
    "PROJECT_GOAL",
    "AI Engineering Path while building a turn-based monster battler game.",
)
GAME_TITLE: str = os.getenv("GAME_TITLE", "PokeAI")
GAME_DESCRIPTION: str = os.getenv(
    "GAME_DESCRIPTION",
    "A turn-based monster battler (PokeMon like) engineered step-by-step to master AI Engineering principles.",
)
# Name of the Game Guide loaded dynamically from .env (defaults to 'Athena')
GAME_GUIDE: str = os.getenv("GAME_GUIDE", "Athena")

# --- Helpers ---
PROMPTS_DIR: Path = SRC_DIR / "prompts"
DATA_DIR: Path = BACKEND_DIR / "data"

# --- API Keys ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# --- Model Definitions ---
# Groq: Fast inference using open-weights models
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# Gemini: High capacity, robust reasoning fallback
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Local Ollama: 100% offline fallback
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# --- Allowed Origins for Cross-Origin Resource Sharing (CORS) ---
_raw_cors_origins: str = os.getenv("BACKEND_CORS_ORIGINS", "")
if _raw_cors_origins:
    try:
        BACKEND_CORS_ORIGINS: list[str] = json.loads(_raw_cors_origins)
    except Exception:
        BACKEND_CORS_ORIGINS = [
            individual_origin.strip().strip("'\"[] ")
            for individual_origin in _raw_cors_origins.split(",")
            if individual_origin.strip()
        ]
else:
    BACKEND_CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# --- Model Hyperparameters ---
# Sampling temperature (0.0 = deterministic, 2.0 = highly expressive)
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
# Standard token output ceiling to ensure snappy sub-second turns
MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "250"))
