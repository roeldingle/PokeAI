"""
Gym Leader Prompts Module
Defines LangChain prompt templates for the Lesson 9 Autonomous Gym Leader AI Agent.
Implements the Perceive -> Remember -> Decide -> Act agent state loop and persona conditioning.
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


def build_gym_leader_agent_prompt() -> ChatPromptTemplate:
    """
    Constructs a LangChain ChatPromptTemplate for the Gym Leader AI Agent's
    in-character taunt and tactical reasoning synthesis.

    Injects:
    - gym_leader_persona: BROCK, MISTY, or WILD_INSTINCT
    - agent_mood: CALCULATING, AGGRESSIVE, DEFENSIVE, or DESPERATE_CLUTCH
    - calibrated_threat_score: 0.0 to 10.0 threat index
    - detected_player_stat_multiplier: e.g. 1.05x (+5% from victories)
    - opponent_monster_name, opponent_hp_ratio, selected_move_name
    - player_monster_name, combat_memory_summary
    """
    # System instruction defining the autonomous persona and strict combat voice
    system_message_template = SystemMessagePromptTemplate.from_template(
        "You are roleplaying as the Autonomous Opponent AI Agent in the PokeAI Arena "
        "with persona '{gym_leader_persona}' and current tactical mood '{agent_mood}'.\n"
        "- If BROCK: Speak as Brock, the Rock-Solid Pewter City Gym Leader—stoic, disciplined, and unyielding.\n"
        "- If MISTY: Speak as Misty, the Cerulean City Water Master—confident, fierce, and relentless.\n"
        "- If WILD_INSTINCT: Express a vivid 1-sentence battle cry describing the wild monster's sharp combat instinct.\n"
        "Deliver a crisp 1-sentence in-character battle taunt referencing your chosen attack '{selected_move_name}' "
        "and acknowledging the player's {detected_player_stat_multiplier}x scaled threat!"
    )

    # Human message injecting Perceive + Remember + Decide state variables
    human_message_template = HumanMessagePromptTemplate.from_template(
        "=== PERCEIVE (Field Telemetry) ===\n"
        "Your Monster: {opponent_monster_name} (HP: {opponent_hp_percentage}%)\n"
        "Player Monster: {player_monster_name} (Stat Progression Multiplier: {detected_player_stat_multiplier}x)\n"
        "Calibrated Threat Score: {calibrated_threat_score} / 10.0 | Mood: {agent_mood}\n\n"
        "=== REMEMBER (Recent Combat History) ===\n"
        "{combat_memory_summary}\n\n"
        "=== DECIDE & ACT ===\n"
        "Selected Move: {selected_move_name} ({internal_tactical_reasoning})\n\n"
        "Emit your 1-sentence in-character stadium battle taunt now:"
    )

    return ChatPromptTemplate.from_messages([
        system_message_template,
        human_message_template,
    ])
