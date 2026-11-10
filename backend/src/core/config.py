"""
Configuration Settings
Centralized management of environment variables, model configurations, and file paths.
"""

import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Mute noisy HTTP and lower-level networking logs so console output stays focused on battle events
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

# Resolve the absolute path to the backend project root directory
# __file__ gives the current config.py path -> parent is 'core' -> parent is 'src' -> parent is 'backend'
backend_directory_path: Path = Path(__file__).resolve().parent.parent.parent

# Construct the exact file path pointing to the .env configuration file
environment_file_path: Path = backend_directory_path / ".env"

# Explicitly load environment variables from the designated .env path into Python's os.environ
load_dotenv(dotenv_path=environment_file_path)

# Environment classification: 'local' during development, 'develop' in staging, or 'production' in cloud
application_environment: str = os.getenv("APP_ENV", "local")

# Semantic version of the PokeAI game engine
game_version: str = os.getenv("VERSION", "0.1.0")

# High-level pedagogical mission statement of this engineering track
project_learning_goal: str = os.getenv(
    "PROJECT_GOAL",
    "AI Engineering Path while building a turn-based monster battler game.",
)

# Display title of the game shown on the retro landing screen
game_title: str = os.getenv("GAME_TITLE", "PokeAI")

# Narrative description and tagline of the battler game
game_description: str = os.getenv(
    "GAME_DESCRIPTION",
    "A turn-based monster battler engineered step-by-step to master AI Engineering principles.",
)

# Name of our AI Game Guide who coaches the player throughout the tournament (defaults to 'Athena' if omitted)
game_guide_name: str = os.getenv("GAME_GUIDE", "Athena")

# Fetch raw Cross-Origin Resource Sharing (CORS) origins string from the environment
raw_origins_environment_variable: str = os.getenv("BACKEND_CORS_ORIGINS", "")

# Robust CORS origin parsing supporting both JSON arrays and comma-delimited strings
if raw_origins_environment_variable:
    try:
        # First attempt parsing as a strict JSON array (e.g. '["http://localhost:5173"]')
        backend_cors_origins: list[str] = json.loads(raw_origins_environment_variable)
    except Exception:
        # Fallback: gracefully parse comma-separated lists and strip extra quotes or brackets
        cleaned_origins: list[str] = [
            individual_origin.strip().strip("'\"[] ")
            for individual_origin in raw_origins_environment_variable.split(",")
            if individual_origin.strip()
        ]
        backend_cors_origins = cleaned_origins
else:
    # Default fallback origins for local development between Vite and FastAPI
    backend_cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# Backwards-compatible aliases matching uppercase convention if required by standard modules
APP_ENV = application_environment
VERSION = game_version
PROJECT_GOAL = project_learning_goal
GAME_TITLE = game_title
GAME_DESCRIPTION = game_description
GAME_GUIDE = game_guide_name
BACKEND_CORS_ORIGINS = backend_cors_origins
