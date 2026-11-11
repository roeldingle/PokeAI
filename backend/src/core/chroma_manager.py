"""
Educational Module Docstring:
This module manages the lifecycle and connection to our local ChromaDB vector database.
In AI Engineering, vector stores bridge the gap between human language and machine computation.
This manager handles:
1. Connecting to the persistent database folder on disk (or in-memory for testing).
2. Creating or retrieving the dedicated 'pokemon_lore_pokedex' collection.
3. Configuring cosine similarity space so concept angles reflect conceptual relevance.
"""

from pathlib import Path
from typing import Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
from src.core import config

# Canonical collection identifier for monster species lore
POKEDEX_COLLECTION_NAME: str = "pokemon_lore_pokedex"

# Global module-level cache for the persistent Chroma client instance (Singleton pattern)
_persistent_chroma_client_instance: Optional[ClientAPI] = None


def resolve_chroma_storage_directory() -> Path:
    """
    Resolves and creates the persistent disk directory for ChromaDB vector files.
    Points to backend/data/chroma to ensure vector embeddings persist across server restarts.
    """
    # Combine the central backend data directory with the chroma subfolder
    chroma_storage_directory_path: Path = config.DATA_DIR / "chroma"
    
    # Ensure the target directory exists on disk, creating parent folders if necessary
    chroma_storage_directory_path.mkdir(parents=True, exist_ok=True)
    
    return chroma_storage_directory_path


def get_chroma_client(custom_client_instance: Optional[ClientAPI] = None) -> ClientAPI:
    """
    Provides access to the active ChromaDB client instance.
    Accepts an optional custom client (e.g., an EphemeralClient for unit tests).
    """
    global _persistent_chroma_client_instance

    # If the caller provides a custom client instance (e.g. during hermetic tests), return it immediately
    if custom_client_instance is not None:
        return custom_client_instance

    # If the singleton instance has not been initialized yet, create it
    if _persistent_chroma_client_instance is None:
        # Resolve the storage path on the local filesystem
        storage_path: Path = resolve_chroma_storage_directory()
        
        # Instantiate a persistent Chroma client pointing to the target directory
        _persistent_chroma_client_instance = chromadb.PersistentClient(
            path=str(storage_path)
        )

    return _persistent_chroma_client_instance


def get_default_embedding_function():
    """
    Initializes ChromaDB's standard default embedding function.
    Converts English text into a 384-dimensional dense vector space.
    """
    # Uses the bundled all-MiniLM-L6-v2 ONNX model for local, zero-cost text vectorization
    return embedding_functions.DefaultEmbeddingFunction()


def get_or_create_pokedex_collection(
    chroma_client_instance: Optional[ClientAPI] = None,
    collection_name: str = POKEDEX_COLLECTION_NAME,
) -> Collection:
    """
    Retrieves the existing Pokédex collection or initializes a new one with cosine distance metric.
    Cosine distance ensures search measures semantic angle rather than document word count.
    """
    # Obtain either the provided client or the default persistent singleton
    active_client: ClientAPI = get_chroma_client(chroma_client_instance)

    # Initialize the default sentence embedding function
    active_embedding_function = get_default_embedding_function()

    # Get or create the collection, configuring Hierarchical Navigable Small World (HNSW) space to cosine
    pokedex_collection: Collection = active_client.get_or_create_collection(
        name=collection_name,
        embedding_function=active_embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    return pokedex_collection


def reset_persistent_chroma_client_cache() -> None:
    """
    Resets the module-level client cache.
    Primarily used during automated test teardowns to guarantee fresh state.
    """
    global _persistent_chroma_client_instance
    _persistent_chroma_client_instance = None