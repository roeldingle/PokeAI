"""
Educational Module Docstring:
Automated test suite for the asynchronous PokéAPI client.
In professional software engineering, automated unit tests must be hermetic and fast;
they should never make live network calls to third-party public web APIs.
We mock httpx.AsyncClient.get calls to test validation, parsing, and failure branches.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from src.services.pokeapi_client import PokeApiClient, PokeApiScoutingError
from src.schemas.pokeapi_schema import PokemonSpeciesLoreRecord


# Sample mocked payload simulating PokéAPI /pokemon/charmander
MOCK_COMBAT_PAYLOAD = {
    "id": 4,
    "name": "charmander",
    "types": [
        {"slot": 1, "type": {"name": "fire"}}
    ],
    "stats": [
        {"base_stat": 39, "stat": {"name": "hp"}},
        {"base_stat": 52, "stat": {"name": "attack"}},
        {"base_stat": 43, "stat": {"name": "defense"}},
        {"base_stat": 60, "stat": {"name": "special-attack"}},
        {"base_stat": 50, "stat": {"name": "special-defense"}},
        {"base_stat": 65, "stat": {"name": "speed"}},
    ],
    "abilities": [
        {"ability": {"name": "blaze"}, "is_hidden": False}
    ],
    "sprites": {
        "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png"
    }
}

# Sample mocked payload simulating PokéAPI /pokemon-species/charmander with dirty formatting
MOCK_SPECIES_PAYLOAD = {
    "flavor_text_entries": [
        {
            "flavor_text": "Obviously prefers\nhot places. When\nit rains, steam\nis said to spout\ffrom the tip of\nits tail.",
            "language": {"name": "en"}
        },
        {
            "flavor_text": "Il préfère les endroits chauds.",
            "language": {"name": "fr"}
        }
    ]
}


def test_sanitize_lore_flavor_text() -> None:
    """
    Validates that form-feeds (\\f) and newlines (\\n) are properly collapsed into clean single-line strings.
    """
    dirty_text = "Obviously prefers\nhot places. When\nit rains,\fsteam spouts."
    cleaned_text = PokeApiClient.sanitize_lore_flavor_text(dirty_text)
    
    assert "\n" not in cleaned_text
    assert "\f" not in cleaned_text
    assert cleaned_text == "Obviously prefers hot places. When it rains, steam spouts."


@pytest.mark.anyio
async def test_fetch_full_pokemon_lore_record_success() -> None:
    """
    Tests successful concurrent retrieval and normalization of both combat metrics and species lore.
    """
    scouting_client = PokeApiClient(enable_in_memory_cache=False)

    # Create mock response objects for the two endpoints
    mock_combat_response = MagicMock(spec=httpx.Response)
    mock_combat_response.status_code = 200
    mock_combat_response.json.return_value = MOCK_COMBAT_PAYLOAD
    mock_combat_response.raise_for_status.return_value = None

    mock_species_response = MagicMock(spec=httpx.Response)
    mock_species_response.status_code = 200
    mock_species_response.json.return_value = MOCK_SPECIES_PAYLOAD
    mock_species_response.raise_for_status.return_value = None

    # Side-effect function to return the correct mock depending on the URL requested
    async def mock_get_handler(url: str, **kwargs: Any) -> MagicMock:
        if "/pokemon-species/" in url:
            return mock_species_response
        return mock_combat_response

    # Patch httpx.AsyncClient.get
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mocked_get_method:
        mocked_get_method.side_effect = mock_get_handler

        result_record = await scouting_client.fetch_full_pokemon_lore_record("charmander")

        # Verify normalized record fields
        assert isinstance(result_record, PokemonSpeciesLoreRecord)
        assert result_record.pokemon_id == 4
        assert result_record.pokemon_name == "charmander"
        assert result_record.elemental_types == ["fire"]
        assert result_record.base_stats["hp"] == 39
        assert result_record.base_stats["speed"] == 65
        assert result_record.abilities == ["blaze"]
        assert "steam is said to spout from the tip" in result_record.lore_flavor_text
        assert result_record.front_default_sprite_url.startswith("https://")


@pytest.mark.anyio
async def test_fetch_pokemon_not_found_raises_scouting_error() -> None:
    """
    Validates that 404 responses are caught and re-raised as clear PokeApiScoutingError exceptions.
    """
    scouting_client = PokeApiClient(enable_in_memory_cache=False)

    mock_not_found_response = MagicMock(spec=httpx.Response)
    mock_not_found_response.status_code = 404
    http_error_exception = httpx.HTTPStatusError(
        message="404 Not Found",
        request=MagicMock(),
        response=mock_not_found_response,
    )
    mock_not_found_response.raise_for_status.side_effect = http_error_exception

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mocked_get_method:
        mocked_get_method.return_value = mock_not_found_response

        with pytest.raises(PokeApiScoutingError) as caught_error_info:
            await scouting_client.fetch_full_pokemon_lore_record("nonexistent_monster_999")

        assert "does not exist in National Pokédex" in str(caught_error_info.value)


@pytest.mark.anyio
async def test_in_memory_caching_prevents_duplicate_network_calls() -> None:
    """
    Validates that repeated requests for the same monster resolve from memory cache without new HTTP calls.
    """
    caching_client = PokeApiClient(enable_in_memory_cache=True)

    mock_combat_response = MagicMock(spec=httpx.Response)
    mock_combat_response.status_code = 200
    mock_combat_response.json.return_value = MOCK_COMBAT_PAYLOAD
    mock_combat_response.raise_for_status.return_value = None

    mock_species_response = MagicMock(spec=httpx.Response)
    mock_species_response.status_code = 200
    mock_species_response.json.return_value = MOCK_SPECIES_PAYLOAD
    mock_species_response.raise_for_status.return_value = None

    async def mock_get_handler(url: str, **kwargs: Any) -> MagicMock:
        if "/pokemon-species/" in url:
            return mock_species_response
        return mock_combat_response

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mocked_get_method:
        mocked_get_method.side_effect = mock_get_handler

        # First retrieval should invoke HTTP calls
        first_record = await caching_client.fetch_full_pokemon_lore_record("charmander")
        initial_call_count = mocked_get_method.call_count
        assert initial_call_count == 2

        # Second retrieval should hit in-memory cache and trigger 0 additional calls
        second_record = await caching_client.fetch_full_pokemon_lore_record("charmander")
        assert mocked_get_method.call_count == initial_call_count
        assert first_record.pokemon_name == second_record.pokemon_name