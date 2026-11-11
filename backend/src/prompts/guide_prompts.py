"""
Game Guide & Battle Referee Prompt Templates Module
Defines reusable LangChain ChatPromptTemplates with dynamic variable injection
for the Game Guide coach persona and stadium referee play-by-play.
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

def build_game_guide_greeting_prompt() -> ChatPromptTemplate:
    """
    Constructs a LangChain ChatPromptTemplate for the Game Guide's dynamic greeting
    upon completing Trainer Registration.

    Expected input variables:
    - game_guide_name: Name of the coach loaded dynamically from config.GAME_GUIDE
    - trainer_name: Moniker chosen by the player (e.g. 'Ash_Ketchum')
    - starter_monster_name: Selected partner (e.g. 'Charmander')
    - selected_starter_id: Pokédex ID (e.g. 4)
    - starter_elemental_type: Elemental type (e.g. 'Fire')
    """
    # System instruction establishing persona, voice, and length bounds
    system_message_template = SystemMessagePromptTemplate.from_template(
        "You are {game_guide_name}, the enthusiastic, sharp, and encouraging Game Guide and Battle Coach "
        "at the PokeAI Arena Academy. You wear a tactical lavender coach jacket and headset. "
        "Speak directly and warmly to the trainer in exactly 2 concise, energetic sentences. "
        "Congratulate them by their Trainer Name on choosing their starter monster, "
        "and mention how that monster's elemental type will shine in tournament battles! "
        "Never mention that you are an AI model; stay 100% in character as the Academy Guide."
    )

    # Human intake message providing the newly registered trainer's context
    human_message_template = HumanMessagePromptTemplate.from_template(
        "Trainer '{trainer_name}' has officially registered for the tournament with partner monster "
        "{starter_monster_name} (Pokédex #{selected_starter_id}, {starter_elemental_type}-type). "
        "Welcome them to the PokeAI Academy!"
    )

    # Combine into a reusable chat prompt template
    return ChatPromptTemplate.from_messages([
        system_message_template,
        human_message_template,
    ])


def build_stadium_referee_prompt() -> ChatPromptTemplate:
    """
    Constructs a general testbench prompt template for simulating combat play-by-play
    and testing prompt passes across the Resilient Gateway.
    """
    system_message_template = SystemMessagePromptTemplate.from_template(
        "You are the official PokeAI Stadium Battle Referee. You provide sharp, objective, "
        "and dramatic 1-sentence reports of Pokémon combat actions and tactical field statuses."
    )

    human_message_template = HumanMessagePromptTemplate.from_template(
        "{battle_query}"
    )

    return ChatPromptTemplate.from_messages([
        system_message_template,
        human_message_template,
    ])