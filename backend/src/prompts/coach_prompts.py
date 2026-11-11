"""
Coach Prompts Module
Defines the In-Context Learning (ICL) and Retrieval-Augmented Generation (RAG) prompt templates
for the Lesson 8 'ASK GUIDE' Tactical Battle Whisperer.
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


def build_coach_tactical_rag_prompt() -> ChatPromptTemplate:
    """
    Constructs a structured LangChain ChatPromptTemplate that injects:
    1. Game Guide persona & trainer identity
    2. Live combat telemetry (Turn clock, Player HP/Stats, Opponent HP/Types)
    3. ChromaDB vector-retrieved opponent lore & weaknesses
    4. Deterministic move effectiveness calculations & mathematically optimal move

    This ensures the LLM never hallucinates illegal moves, locked move slots, or wrong type charts.
    """
    # System prompt grounding the Game Guide's persona, constraints, and anti-hallucination rules
    system_message_template = SystemMessagePromptTemplate.from_template(
        "You are {game_guide_name}, the sharp, encouraging Head Battle Guide at the PokeAI Arena. "
        "The trainer has pressed 'ASK GUIDE' during an active turn-based battle for urgent tactical advice. "
        "You MUST obey these strict coaching guardrails:\n"
        "1. Recommend ONLY the mathematically optimal unlocked move: '{recommended_action_name}'.\n"
        "2. Ground your explanation in the retrieved Pokédex vector lore and exact elemental multipliers provided.\n"
        "3. Speak directly to Trainer {trainer_name} in 2 to 3 crisp, high-energy sentences.\n"
        "4. Never recommend locked moves or moves with 0 Power Points (PP).\n"
        "5. Never mention being an AI; stay 100% in character as Coach {game_guide_name}."
    )

    # Human prompt injecting the dynamic In-Context Learning (ICL) battle state and RAG context
    human_message_template = HumanMessagePromptTemplate.from_template(
        "=== LIVE STADIUM BATTLE STATE (Turn {current_turn_number} of {maximum_turns_allowed}) ===\n"
        "- Trainer: {trainer_name}\n"
        "- Player Monster: {player_monster_name} (Lv {player_level}, Types: {player_types}, "
        "HP: {player_current_hp}/{player_max_hp}, ATK: {player_attack}, SPD: {player_speed})\n"
        "- Opponent Monster: {opponent_monster_name} (Lv {opponent_level}, Types: {opponent_types}, "
        "HP: {opponent_current_hp}/{opponent_max_hp}, DEF: {opponent_defense}, SPD: {opponent_speed})\n\n"
        "=== CHROMADB VECTOR LORE CONTEXT ===\n"
        "{retrieved_lore_context}\n\n"
        "=== UNLOCKED MOVE EFFECTIVENESS MATRIX ===\n"
        "{elemental_matchup_summary}\n\n"
        "=== OPTIMAL CALCULATED ACTION ===\n"
        "Recommended Move: {recommended_action_name} (Confidence: {confidence_percentage}%)\n\n"
        "Deliver your tactical whisper to {trainer_name} explaining why '{recommended_action_name}' "
        "is the winning play right now!"
    )

    # Return the combined ChatPromptTemplate for the Resilient LLM Gateway
    return ChatPromptTemplate.from_messages([
        system_message_template,
        human_message_template,
    ])
