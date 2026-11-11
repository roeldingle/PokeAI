"""
Educational Module Docstring:
This service provides an asynchronous, non-blocking HTTP client for PokéAPI.
In high-throughput AI applications, making sequential blocking web calls freezes the event loop.
Here, we use httpx.AsyncClient combined with asyncio.gather to query both combat statistics
and lore descriptions simultaneously, cutting external latency in half.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
import httpx

from src.schemas.pokeapi_schema import (
    PokemonCombatStats,
    PokemonSpeciesLoreRecord,
)


class PokeApiScoutingError(Exception):
    """Custom exception raised when external scouting queries fail."""
    pass


class PokeApiClient:
    """
    The Academy Researcher's Scouting Telescope.
    Asynchronously queries official PokéAPI endpoints with rate safety, caching, and normalization.
    """

    # Base endpoint URL for the official public PokéAPI v2
    POKEAPI_BASE_URL: str = "https://pokeapi.co/api/v2"

    def __init__(
        self,
        request_timeout_seconds: float = 10.0,
        enable_in_memory_cache: bool = True,
    ) -> None:
        """
        Initializes the async scouting client.
        
        :param request_timeout_seconds: Maximum seconds to wait before terminating an unresponsive scout.
        :param enable_in_memory_cache: Whether to store resolved records in local memory to respect API quotas.
        """
        # Store configuration parameters as private attributes
        self._request_timeout_seconds: float = request_timeout_seconds
        # Local cache dictionary keyed by lowercase monster identifier
        self._lore_records_cache: Dict[str, PokemonSpeciesLoreRecord] = {}
        self._enable_in_memory_cache: bool = enable_in_memory_cache

    @staticmethod
    def sanitize_lore_flavor_text(raw_flavor_text: str) -> str:
        """
        Cleans legacy Pokédex text formatting.
        Old Game Boy ROM dumps contain newline characters (\\n), page breaks (\\f),
        and irregular spacing that degrade vector embedding quality.
        """
        # Replace line breaks, form-feeds, and carriage returns with a single whitespace
        cleaned_single_line_text = re.sub(r"[\n\f\r]+", " ", raw_flavor_text)
        # Collapse multiple consecutive whitespace characters into one
        standardized_spacing_text = re.sub(r"\s+", " ", cleaned_single_line_text)
        # Return stripped text with no leading or trailing margins
        return standardized_spacing_text.strip()

    async def fetch_pokemon_combat_data(
        self,
        pokemon_identifier: str | int,
        async_http_client: httpx.AsyncClient,
    ) -> Dict[str, Any]:
        """
        Queries the /pokemon/{id} endpoint to retrieve combat statistics, types, and sprites.
        """
        # Formulate canonical target scouting URL
        scouting_url = f"{self.POKEAPI_BASE_URL}/pokemon/{str(pokemon_identifier).strip().lower()}"

        try:
            # Issue non-blocking GET request to PokéAPI
            scouting_response = await async_http_client.get(
                scouting_url,
                timeout=self._request_timeout_seconds,
            )
            # Raise an HTTPStatusError if response code is 4xx or 5xx
            scouting_response.raise_for_status()
            # Return parsed JSON dictionary
            return scouting_response.json()
        except httpx.HTTPStatusError as http_error_status:
            # Handle specific 404 Not Found error with clear stadium messaging
            if http_error_status.response.status_code == 404:
                raise PokeApiScoutingError(
                    f"Scout reported target monster '{pokemon_identifier}' does not exist in National Pokédex."
                ) from http_error_status
            # Handle general HTTP errors
            raise PokeApiScoutingError(
                f"Scouting radio failed with HTTP status code: {http_error_status.response.status_code}"
            ) from http_error_status
        except httpx.RequestError as network_request_error:
            # Handle connection timeouts, DNS resolution issues, or dropped sockets
            raise PokeApiScoutingError(
                f"Scouting signal lost: Could not connect to PokéAPI server ({str(network_request_error)})."
            ) from network_request_error

    async def fetch_pokemon_species_lore(
        self,
        pokemon_identifier: str | int,
        async_http_client: httpx.AsyncClient,
    ) -> Dict[str, Any]:
        """
        Queries the /pokemon-species/{id} endpoint to retrieve Pokédex lore flavor text.
        """
        # Formulate canonical target lore URL
        lore_scouting_url = f"{self.POKEAPI_BASE_URL}/pokemon-species/{str(pokemon_identifier).strip().lower()}"

        try:
            # Issue non-blocking GET request
            lore_response = await async_http_client.get(
                lore_scouting_url,
                timeout=self._request_timeout_seconds,
            )
            # Check for HTTP error responses
            lore_response.raise_for_status()
            # Return parsed species JSON payload
            return lore_response.json()
        except httpx.HTTPStatusError as http_error_status:
            if http_error_status.response.status_code == 404:
                raise PokeApiScoutingError(
                    f"Scout reported no species lore found for monster '{pokemon_identifier}'."
                ) from http_error_status
            raise PokeApiScoutingError(
                f"Species lore scouting failed with HTTP status code: {http_error_status.response.status_code}"
            ) from http_error_status
        except httpx.RequestError as network_request_error:
            raise PokeApiScoutingError(
                f"Species lore signal lost: Could not connect to PokéAPI ({str(network_request_error)})."
            ) from network_request_error

    def extract_english_flavor_text(self, raw_species_payload: Dict[str, Any]) -> str:
        """
        Extracts the first canonical English flavor text description from the species payload.
        """
        # Retrieve flavor text entries array from the payload
        flavor_text_entries_list: List[Dict[str, Any]] = raw_species_payload.get("flavor_text_entries", [])

        # Iterate through flavor entries to find the first English description
        for flavor_text_entry in flavor_text_entries_list:
            # Check if language tag matches English ('en')
            language_record = flavor_text_entry.get("language", {})
            if language_record.get("name") == "en":
                raw_text_value = flavor_text_entry.get("flavor_text", "")
                return self.sanitize_lore_flavor_text(raw_text_value)

        # Fallback if no English entry is found
        return "No English Pokédex description available in stadium archives."

    async def fetch_full_pokemon_lore_record(
        self,
        pokemon_identifier: str | int,
    ) -> PokemonSpeciesLoreRecord:
        """
        Orchestrates concurrent async requests for combat data and species lore,
        normalizing both into a single validated PokemonSpeciesLoreRecord.
        """
        # Normalize lookup key for caching
        cache_lookup_key = str(pokemon_identifier).strip().lower()

        # Check in-memory cache first to avoid unnecessary HTTP round-trips
        if self._enable_in_memory_cache and cache_lookup_key in self._lore_records_cache:
            return self._lore_records_cache[cache_lookup_key]

        # Use an async client context manager for connection pooling and proper cleanup
        async with httpx.AsyncClient() as async_http_client:
            # Concurrently launch both scouting requests with asyncio.gather
            raw_combat_payload, raw_species_payload = await asyncio.gather(
                self.fetch_pokemon_combat_data(pokemon_identifier, async_http_client),
                self.fetch_pokemon_species_lore(pokemon_identifier, async_http_client),
            )

        # Extract elemental types from the combat payload
        extracted_elemental_types: List[str] = [
            type_entry["type"]["name"]
            for type_entry in raw_combat_payload.get("types", [])
            if "type" in type_entry and "name" in type_entry["type"]
        ]

        # Extract base combat statistics into a key-value dictionary
        extracted_base_stats: Dict[str, int] = {}
        for stat_entry in raw_combat_payload.get("stats", []):
            stat_name = stat_entry.get("stat", {}).get("name", "")
            base_value = stat_entry.get("base_stat", 0)
            if stat_name:
                extracted_base_stats[stat_name] = base_value

        # Extract list of abilities
        extracted_abilities: List[str] = [
            ability_entry["ability"]["name"]
            for ability_entry in raw_combat_payload.get("abilities", [])
            if "ability" in ability_entry and "name" in ability_entry["ability"]
        ]

        # Extract front sprite URL
        front_sprite_url = (
            raw_combat_payload.get("sprites", {}).get("front_default")
        )

        # Clean and extract English Pokédex lore
        extracted_lore_flavor_text = self.extract_english_flavor_text(raw_species_payload)

        # Construct and validate the standardized domain record
        validated_lore_record = PokemonSpeciesLoreRecord(
            pokemon_id=raw_combat_payload.get("id", 0),
            pokemon_name=raw_combat_payload.get("name", cache_lookup_key),
            elemental_types=extracted_elemental_types,
            base_stats=extracted_base_stats,
            abilities=extracted_abilities,
            lore_flavor_text=extracted_lore_flavor_text,
            front_default_sprite_url=front_sprite_url,
        )

        # Store in cache if enabled
        if self._enable_in_memory_cache:
            self._lore_records_cache[cache_lookup_key] = validated_lore_record
            self._lore_records_cache[str(validated_lore_record.pokemon_id)] = validated_lore_record

        return validated_lore_record