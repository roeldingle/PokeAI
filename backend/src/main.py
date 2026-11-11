"""
Main Application Entrypoint
Initializes the FastAPI application, mounts CORS security middleware, and attaches domain routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core import config
from src.routes.metadata_routes import metadata_router
from src.routes.onboarding_routes import onboarding_router
from src.routes.ai_routes import ai_router


def create_pokeai_application() -> FastAPI:
    """
    Application factory pattern that constructs, configures, and returns the central FastAPI application.
    Using a factory function enables flexible test harnesses and reproducible staging setups.
    """
    # Instantiate the primary FastAPI server instance with descriptive arena metadata
    pokeai_application = FastAPI(
        title=config.GAME_TITLE,
        version=config.VERSION,
        description=config.GAME_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure Cross-Origin Resource Sharing (CORS) middleware
    # In production web apps, CORS prevents untrusted external domains from hijacking battle commands
    pokeai_application.add_middleware(
        CORSMiddleware,
        allow_origins=config.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain routers under /api/v1
    pokeai_application.include_router(metadata_router)
    pokeai_application.include_router(onboarding_router)
    pokeai_application.include_router(ai_router)

    # Provide a simple root status endpoint for quick ping verifications
    @pokeai_application.get("/", tags=["Stadium Health"])
    async def get_stadium_root_status() -> dict[str, str]:
        """
        Returns a friendly confirmation that the PokeAI stadium backend is online and awaiting trainers.
        """
        return {
            "status": "online",
            "message": f"Welcome to the {config.GAME_TITLE} Stadium! Access /docs for interactive API documentation.",
        }

    return pokeai_application


# Create the global app instance for ASGI servers like Uvicorn
app = create_pokeai_application()
