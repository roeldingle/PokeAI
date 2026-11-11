"""
Coach RAG Service Module
Implements the Lesson 8 'ASK GUIDE' Tactical Battle Whisperer.
Combines ChromaDB vector retrieval, deterministic elemental matchup evaluation,
and In-Context Learning (ICL) via the Resilient LLM Gateway to whisper winning counter-moves.
"""

import time
from typing import Dict, List, Optional, Tuple
from src.core import config
from src.core.llm_gateway import default_resilient_llm_gateway
from src.prompts.coach_prompts import build_coach_tactical_rag_prompt
from src.schemas.ai_gateway_schema import LLMMessageItem, LLMMessageRole
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot
from src.schemas.coach_schema import CoachTacticalAdviceResponse
from src.services.battle_engine import battle_engine_service
from src.services.vector_ingestion_service import search_pokedex_by_meaning

# Canonical fallback lore dictionary if ChromaDB vector store has not been seeded yet
CANONICAL_FALLBACK_SPECIES_LORE: Dict[str, str] = {
    "pidgey": (
        "Pidgey is a Tiny Bird Flyer Pokémon (Normal/Flying). Vulnerable to Electric, Ice, and Rock attacks; "
        "its nimble wings grant decent speed but low physical defense against direct strikes."
    ),
    "charmander": (
        "Charmander is a Lizard Pokémon (Fire). Excels against Grass, Ice, Bug, and Steel targets, "
        "but must watch out for Water, Ground, and Rock attacks."
    ),
    "bulbasaur": (
        "Bulbasaur is a Seed Pokémon (Grass/Poison). Strong against Water, Ground, and Rock monsters, "
        "while vulnerable to Fire, Flying, Ice, and Psychic moves."
    ),
    "squirtle": (
        "Squirtle is a Tiny Turtle Pokémon (Water). Its hardened shell provides high physical defense, "
        "and Water attacks deal 2x super-effective damage against Fire, Ground, and Rock foes."
    ),
    "onix": (
        "Onix is a Rock Snake Pokémon (Rock/Ground). Boasts massive physical defense and immunity to Electric, "
        "but suffers 4x quadruple weakness against Water and Grass attacks."
    ),
    "starmie": (
        "Starmie is a Mysterious Pokémon (Water/Psychic). Extremely high speed and special attack; "
        "weak to Electric, Grass, Bug, Ghost, and Dark moves."
    ),
    "pikachu": (
        "Pikachu is an Electric Mouse Pokémon (Electric). Stores high-voltage electricity in its cheeks "
        "that deals 2x super-effective damage to Water and Flying opponents."
    ),
}


class CoachRAGService:
    """
    Orchestrates Retrieval-Augmented Generation (RAG) and deterministic combat analysis
    to provide real-time tactical coaching from the Game Guide.
    """

    def retrieve_opponent_lore_from_vector_memory(
        self,
        opponent_monster: ActiveBattleEntity,
    ) -> str:
        """
        Queries ChromaDB vector memory for the active opponent's species lore and weaknesses.
        Falls back gracefully to canonical stadium lore if the vector store is empty.
        """
        # Construct a semantic search query combining species name and elemental types
        opponent_types_joined = "/".join(opponent_monster.elemental_types)
        semantic_query = (
            f"{opponent_monster.pokemon_name} {opponent_types_joined} type weaknesses stats lore"
        )

        try:
            # Execute cosine similarity search against ChromaDB
            pokedex_search_response = search_pokedex_by_meaning(
                search_query_text=semantic_query,
                maximum_results_limit=3,
            )

            # Look for an exact species match first among top vector candidates
            for candidate_result in pokedex_search_response.vector_results:
                if candidate_result.pokemon_name.lower() == opponent_monster.pokemon_name.lower():
                    return (
                        f"[ChromaDB Match {int(candidate_result.similarity_confidence_score * 100)}%] "
                        f"{candidate_result.pokemon_name.title()} ({'/'.join(candidate_result.elemental_types)}): "
                        f"{candidate_result.matched_lore_snippet}"
                    )

            # Otherwise, return the highest-ranked semantic match if available
            if pokedex_search_response.vector_results:
                top_candidate = pokedex_search_response.vector_results[0]
                return (
                    f"[ChromaDB Semantic Lore] {top_candidate.pokemon_name.title()}: "
                    f"{top_candidate.matched_lore_snippet}"
                )
        except Exception:
            # If ChromaDB raises an unexpected I/O error, fall through to canonical dictionary
            pass

        # Fallback to canonical stadium lore so coaching never fails even on unseeded setups
        normalized_opponent_name = opponent_monster.pokemon_name.strip().lower()
        fallback_snippet = CANONICAL_FALLBACK_SPECIES_LORE.get(
            normalized_opponent_name,
            f"{opponent_monster.pokemon_name} is a {opponent_types_joined}-type combatant with "
            f"Defense {opponent_monster.defense_stat} and Speed {opponent_monster.speed_stat}.",
        )
        return f"[Stadium Tactical Archive] {fallback_snippet}"

    def evaluate_optimal_unlocked_move(
        self,
        player_monster: ActiveBattleEntity,
        opponent_monster: ActiveBattleEntity,
    ) -> Tuple[PokemonMoveSlot, float, str]:
        """
        Evaluates all unlocked moves with remaining Power Points (PP) on the player's monster.
        Computes deterministic elemental effectiveness and expected damage score to identify
        the mathematically optimal move, calibrated confidence score, and matchup summary.
        """
        # Filter for unlocked move slots that still have usable Power Points
        available_unlocked_moves: List[PokemonMoveSlot] = [
            move_slot
            for move_slot in player_monster.move_slots
            if move_slot.is_unlocked and move_slot.current_power_points > 0
        ]

        # Edge case fallback if all unlocked moves are out of PP
        if not available_unlocked_moves:
            fallback_move = player_monster.move_slots[0]
            return (
                fallback_move,
                0.55,
                f"{fallback_move.move_name} (Fallback — 0 PP remaining on primary moves)",
            )

        best_move_slot: PokemonMoveSlot = available_unlocked_moves[0]
        highest_tactical_score: float = -1.0
        best_effectiveness_multiplier: float = 1.0
        matchup_descriptions: List[str] = []

        # Score each available unlocked move
        for candidate_move in available_unlocked_moves:
            effectiveness_multiplier = battle_engine_service.calculate_elemental_effectiveness(
                attacking_move_elemental_type=candidate_move.elemental_type,
                defending_pokemon_elemental_types=opponent_monster.elemental_types,
            )

            # Calculate expected offensive utility score:
            # Damaging moves scale by base_power * effectiveness * accuracy; status moves get a small baseline score
            if candidate_move.base_power > 0:
                tactical_score = (
                    candidate_move.base_power
                    * effectiveness_multiplier
                    * (candidate_move.accuracy_percentage / 100.0)
                )
            else:
                # Status move (e.g. Growl, Tail Whip) has low offensive priority compared to damaging moves
                tactical_score = 5.0

            # Classify multiplier label for readable UI telemetry
            if effectiveness_multiplier >= 2.0:
                effectiveness_label = f"Super Effective {effectiveness_multiplier:g}x"
            elif effectiveness_multiplier == 0.0:
                effectiveness_label = "Immune 0x"
            elif effectiveness_multiplier < 1.0:
                effectiveness_label = f"Resisted {effectiveness_multiplier:g}x"
            else:
                effectiveness_label = "Neutral 1x"

            matchup_descriptions.append(
                f"{candidate_move.move_name} [{candidate_move.elemental_type.upper()}] -> "
                f"Power {candidate_move.base_power}, {effectiveness_label} "
                f"(PP {candidate_move.current_power_points}/{candidate_move.maximum_power_points})"
            )

            # Track the highest scoring move
            if tactical_score > highest_tactical_score:
                highest_tactical_score = tactical_score
                best_move_slot = candidate_move
                best_effectiveness_multiplier = effectiveness_multiplier

        # Calibrate confidence rating based on effectiveness and base power
        if best_move_slot.base_power > 0 and best_effectiveness_multiplier >= 2.0:
            calibrated_confidence = 0.96
        elif best_move_slot.base_power > 0 and best_effectiveness_multiplier == 1.0:
            calibrated_confidence = 0.89
        elif best_move_slot.base_power > 0 and best_effectiveness_multiplier > 0.0:
            calibrated_confidence = 0.74
        else:
            calibrated_confidence = 0.62

        elemental_matchup_summary = " | ".join(matchup_descriptions)
        return (best_move_slot, calibrated_confidence, elemental_matchup_summary)

    def build_deterministic_coaching_whisper(
        self,
        trainer_name: str,
        player_monster: ActiveBattleEntity,
        opponent_monster: ActiveBattleEntity,
        recommended_move: PokemonMoveSlot,
        effectiveness_multiplier: float,
    ) -> str:
        """
        Generates a rich, deterministic in-character tactical whisper grounded in exact combat stats.
        Used when the LLM gateway is in offline_fallback mode or to guarantee sub-millisecond test reliability.
        """
        opponent_types_text = "/".join(t.title() for t in opponent_monster.elemental_types)
        move_type_title = recommended_move.elemental_type.title()

        if effectiveness_multiplier >= 2.0:
            return (
                f"Listen closely, {trainer_name}! {opponent_monster.pokemon_name} is {opponent_types_text}-type, "
                f"which leaves it wide open to {move_type_title} attacks! Command {player_monster.pokemon_name} "
                f"to unleash {recommended_move.move_name} for {effectiveness_multiplier:g}x super-effective damage "
                f"and seize control of this battle!"
            )
        elif recommended_move.base_power > 0:
            return (
                f"Eyes on the ring, {trainer_name}! {opponent_monster.pokemon_name} ({opponent_types_text}-type) "
                f"has {opponent_monster.current_health_points}/{opponent_monster.maximum_health_points} HP and "
                f"{opponent_monster.defense_stat} Defense. Your {player_monster.pokemon_name}'s "
                f"{recommended_move.move_name} ({recommended_move.base_power} Power) is your strongest unlocked "
                f"strike—use {recommended_move.move_name} now to pressure their HP before the 5-turn clock runs out!"
            )
        else:
            return (
                f"Stay sharp, {trainer_name}! With attacking moves depleted, use {recommended_move.move_name} "
                f"to disrupt {opponent_monster.pokemon_name} while holding your ground until the Turn 5 roulette!"
            )

    async def generate_tactical_advice(
        self,
        battle_session_id: str,
        custom_trainer_question: Optional[str] = None,
        use_llm_gateway: bool = True,
    ) -> CoachTacticalAdviceResponse:
        """
        End-to-end RAG Coaching Pipeline:
        1. Inspects active battle session state from BattleEngineService.
        2. Retrieves opponent species lore from ChromaDB vector memory.
        3. Evaluates unlocked moves to find the mathematically optimal recommendation.
        4. Queries ResilientLLMGateway (with automatic deterministic fallback) to craft the whisper.
        """
        start_timestamp = time.perf_counter()

        # Step 1: Retrieve active battle session
        session_data = battle_engine_service.active_battle_sessions.get(battle_session_id)
        if not session_data:
            raise ValueError(f"Battle session '{battle_session_id}' not found.")

        trainer_name: str = session_data.get("trainer_name", "Trainer")
        current_turn_number: int = session_data.get("current_turn_number", 1)
        maximum_turns_allowed: int = session_data.get("maximum_turns_allowed", 5)
        player_monster: ActiveBattleEntity = session_data["player_monster"]
        opponent_monster: ActiveBattleEntity = session_data["opponent_monster"]

        # Step 2: Retrieve opponent lore from ChromaDB vector store
        retrieved_lore_context = self.retrieve_opponent_lore_from_vector_memory(
            opponent_monster=opponent_monster
        )

        # Step 3: Evaluate unlocked moves and select optimal counter-move
        optimal_move_slot, confidence_rating, elemental_matchup_summary = (
            self.evaluate_optimal_unlocked_move(
                player_monster=player_monster,
                opponent_monster=opponent_monster,
            )
        )

        optimal_effectiveness = battle_engine_service.calculate_elemental_effectiveness(
            attacking_move_elemental_type=optimal_move_slot.elemental_type,
            defending_pokemon_elemental_types=opponent_monster.elemental_types,
        )

        # Prepare deterministic tactical whisper as baseline/fallback
        deterministic_whisper = self.build_deterministic_coaching_whisper(
            trainer_name=trainer_name,
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            recommended_move=optimal_move_slot,
            effectiveness_multiplier=optimal_effectiveness,
        )

        active_provider_name = "offline_fallback"
        model_identifier = "deterministic-tactical-rag"
        tactical_justification = deterministic_whisper

        # Step 4: If LLM gateway is enabled, synthesize via ResilientLLMGateway
        if use_llm_gateway:
            try:
                prompt_template = build_coach_tactical_rag_prompt()
                formatted_langchain_messages = prompt_template.format_messages(
                    game_guide_name=config.GAME_GUIDE,
                    trainer_name=trainer_name,
                    current_turn_number=current_turn_number,
                    maximum_turns_allowed=maximum_turns_allowed,
                    player_monster_name=player_monster.pokemon_name,
                    player_level=player_monster.level,
                    player_types="/".join(player_monster.elemental_types),
                    player_current_hp=player_monster.current_health_points,
                    player_max_hp=player_monster.maximum_health_points,
                    player_attack=player_monster.attack_stat,
                    player_speed=player_monster.speed_stat,
                    opponent_monster_name=opponent_monster.pokemon_name,
                    opponent_level=opponent_monster.level,
                    opponent_types="/".join(opponent_monster.elemental_types),
                    opponent_current_hp=opponent_monster.current_health_points,
                    opponent_max_hp=opponent_monster.maximum_health_points,
                    opponent_defense=opponent_monster.defense_stat,
                    opponent_speed=opponent_monster.speed_stat,
                    retrieved_lore_context=retrieved_lore_context,
                    elemental_matchup_summary=elemental_matchup_summary,
                    recommended_action_name=optimal_move_slot.move_name,
                    confidence_percentage=int(confidence_rating * 100),
                )

                # Convert LangChain prompt messages into LLMMessageItem schema objects
                gateway_messages: List[LLMMessageItem] = [
                    LLMMessageItem(
                        role=LLMMessageRole.SYSTEM if index == 0 else LLMMessageRole.USER,
                        content=str(msg.content),
                    )
                    for index, msg in enumerate(formatted_langchain_messages)
                ]

                if custom_trainer_question:
                    gateway_messages[-1].content += (
                        f"\nTrainer's specific question: {custom_trainer_question}"
                    )

                llm_envelope = await default_resilient_llm_gateway.generate_chat_completion(
                    conversation_messages=gateway_messages,
                )

                active_provider_name = llm_envelope.active_provider_name
                model_identifier = llm_envelope.model_identifier

                # If the gateway returned an actual provider response (not the generic greeting offline fallback),
                # ensure the recommended move name is mentioned; otherwise use our grounded tactical whisper
                if (
                    active_provider_name != "offline_fallback"
                    and llm_envelope.generated_message_content
                ):
                    generated_text = llm_envelope.generated_message_content.strip()
                    if optimal_move_slot.move_name.lower() not in generated_text.lower():
                        tactical_justification = (
                            f"{generated_text} Recommendation: Use {optimal_move_slot.move_name}!"
                        )
                    else:
                        tactical_justification = generated_text
            except Exception:
                # Preserve the deterministic tactical whisper on any gateway error
                pass

        elapsed_milliseconds = round((time.perf_counter() - start_timestamp) * 1000.0, 2)

        return CoachTacticalAdviceResponse(
            battle_session_id=battle_session_id,
            game_guide_name=config.GAME_GUIDE,
            recommended_action_name=optimal_move_slot.move_name,
            recommended_move_id=optimal_move_slot.move_id,
            tactical_justification=tactical_justification,
            confidence_rating=confidence_rating,
            retrieved_lore_context=retrieved_lore_context,
            elemental_matchup_summary=elemental_matchup_summary,
            active_provider_name=active_provider_name,
            model_identifier=model_identifier,
            execution_latency_milliseconds=elapsed_milliseconds,
        )


# Global singleton instance for route injection
coach_rag_service = CoachRAGService()
