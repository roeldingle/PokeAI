"""
Educational Module Docstring:
This standalone ingestion script demonstrates non-blocking concurrent data harvesting.
It queries PokéAPI for our 3 tournament starter monsters and our early wild encounter,
validates the retrieved payloads, and prints a structured stadium scouting report.
In Lesson 04, these records will be piped directly into ChromaDB vector collections.
"""

import asyncio
import sys
from pathlib import Path

# Add backend root directory to sys.path so 'src' can be imported cleanly
current_script_path = Path(__file__).resolve()
# Point to the backend directory (three levels up: scripts -> src -> backend)
backend_root_directory = current_script_path.parent.parent.parent
sys.path.insert(0, str(backend_root_directory))

from src.services.pokeapi_client import PokeApiClient, PokeApiScoutingError


# Canonical list of monsters required for Phase 1 & 2 of PokeAI
STARTER_AND_WILD_TARGETS = ["bulbasaur", "charmander", "squirtle", "pidgey"]


async def run_starter_lore_ingestion() -> None:
    """
    Asynchronously scouts and displays lore summaries for starter monsters.
    """
    print("\n==================================================================")
    print("🔭 POKEAI RESEARCHER TELESCOPE: INGESTING POKÉAPI LORE (LESSON 03)")
    print("==================================================================\n")

    # Instantiate the asynchronous scouting client
    scouting_client = PokeApiClient(request_timeout_seconds=12.0)

    # Ingest targets concurrently using asyncio.gather
    try:
        scouting_tasks = [
            scouting_client.fetch_full_pokemon_lore_record(target_name)
            for target_name in STARTER_AND_WILD_TARGETS
        ]
        scouted_records = await asyncio.gather(*scouting_tasks)

        for record in scouted_records:
            print(f"🏟️  #{record.pokemon_id:03d} {record.pokemon_name.upper()}")
            print(f"   Types:     {', '.join(record.elemental_types)}")
            print(f"   Abilities: {', '.join(record.abilities)}")
            print(f"   HP: {record.base_stats.get('hp')} | ATK: {record.base_stats.get('attack')} | DEF: {record.base_stats.get('defense')} | SPD: {record.base_stats.get('speed')}")
            print(f"   Sprite:    {record.front_default_sprite_url}")
            print(f"   Lore Text: \"{record.lore_flavor_text}\"")
            print("-" * 66)

        print("\n✅ All target monsters scouted, validated, and normalized successfully!")

    except PokeApiScoutingError as scouting_error:
        print(f"\n❌ Scouting mission failed: {scouting_error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_starter_lore_ingestion())