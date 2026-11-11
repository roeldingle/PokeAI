"""
Gym Leader Agent Service Module
Implements the Lesson 9 Autonomous Gym Leader AI Agent:
- Autonomous single-agent loop: Perceive -> Remember -> Decide -> Act
- Dynamic Threat Calibration reacting to the player's +1% stat_progression_multiplier
- Persona conditioning for Gym Leader Brock (Onix), Gym Leader Misty (Starmie), and Wild Instinct (Pidgey)
"""

import time
from typing import Callable, Dict, List, Optional, Tuple
from src.core.llm_gateway import default_resilient_llm_gateway
from src.prompts.gym_leader_prompts import build_gym_leader_agent_prompt
from src.schemas.ai_gateway_schema import LLMMessageItem, LLMMessageRole
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot
from src.schemas.gym_leader_schema import (
    AgentMoodState,
    GymLeaderPersona,
    GymLeaderTurnDecision,
)


class GymLeaderAgentService:
    """
    Autonomous opponent agent executing a 4-stage Perceive -> Remember -> Decide -> Act loop
    on every turn of combat.
    """

    @staticmethod
    def resolve_persona_for_opponent(opponent_pokemon_id: int) -> GymLeaderPersona:
        """
        Maps the opponent species ID to its canonical Gym Leader or Wild persona.
        - #95 Onix -> Gym Leader Brock
        - #121 Starmie -> Gym Leader Misty
        - Default (#16 Pidgey, etc.) -> Wild Instinct
        """
        if opponent_pokemon_id == 95:
            return GymLeaderPersona.BROCK
        elif opponent_pokemon_id == 121:
            return GymLeaderPersona.MISTY
        return GymLeaderPersona.WILD_INSTINCT

    def calculate_dynamic_threat_level(
        self,
        player_monster: ActiveBattleEntity,
        opponent_monster: ActiveBattleEntity,
        stat_progression_multiplier: float,
        calculate_effectiveness_fn: Callable[[str, List[str]], float],
    ) -> Tuple[float, AgentMoodState]:
        """
        STAGE 1 (PERCEIVE): Analyzes the battlefield state, HP ratios, elemental matchups,
        and the player's accumulated +1% victory stat multiplier to compute a calibrated
        threat score (0.0 to 10.0) and tactical AgentMoodState.
        """
        # Compute remaining HP percentage of the autonomous opponent
        opponent_hp_ratio: float = opponent_monster.current_health_points / max(
            1, opponent_monster.maximum_health_points
        )

        # Baseline threat starts at 4.0 and scales upward with the player's +1% stat multiplier
        # Every +1% stat boost (+0.01 multiplier) adds +15.0 to the threat calculation
        progression_bonus_threat: float = max(0.0, (stat_progression_multiplier - 1.0) * 15.0)

        # Evaluate highest elemental multiplier the player has unlocked against this opponent
        highest_player_effectiveness: float = 1.0
        for player_move in player_monster.move_slots:
            if player_move.is_unlocked and player_move.base_power > 0 and player_move.current_power_points > 0:
                effectiveness = calculate_effectiveness_fn(
                    player_move.elemental_type,
                    opponent_monster.elemental_types,
                )
                if effectiveness > highest_player_effectiveness:
                    highest_player_effectiveness = effectiveness

        # Evaluate highest elemental multiplier the opponent has against the player
        highest_opponent_effectiveness: float = 1.0
        for opponent_move in opponent_monster.move_slots:
            if opponent_move.is_unlocked and opponent_move.base_power > 0 and opponent_move.current_power_points > 0:
                effectiveness = calculate_effectiveness_fn(
                    opponent_move.elemental_type,
                    player_monster.elemental_types,
                )
                if effectiveness > highest_opponent_effectiveness:
                    highest_opponent_effectiveness = effectiveness

        # Combine baseline threat, progression scaling, type danger, and low-HP urgency
        raw_threat_score: float = (
            4.0
            + progression_bonus_threat
            + (1.8 if highest_player_effectiveness >= 2.0 else 0.0)
            + ((1.0 - opponent_hp_ratio) * 3.0)
        )
        calibrated_threat_score: float = round(min(10.0, max(1.0, raw_threat_score)), 2)

        # Determine Agent Mood State from perceived telemetry
        if opponent_hp_ratio <= 0.30:
            # Critical low HP triggers all-out Desperate Clutch finishing posture
            agent_mood = AgentMoodState.DESPERATE_CLUTCH
            calibrated_threat_score = max(calibrated_threat_score, 8.5)
        elif stat_progression_multiplier >= 1.10 or highest_opponent_effectiveness >= 2.0:
            # High player stat scaling or super-effective offensive opening triggers Aggressive mode
            agent_mood = AgentMoodState.AGGRESSIVE
        elif highest_player_effectiveness >= 2.0:
            # Facing a super-effective threat while healthy shifts agent to Defensive focus
            agent_mood = AgentMoodState.DEFENSIVE
        else:
            agent_mood = AgentMoodState.CALCULATING

        return (calibrated_threat_score, agent_mood)

    def select_optimal_opponent_move(
        self,
        opponent_monster: ActiveBattleEntity,
        player_monster: ActiveBattleEntity,
        agent_mood: AgentMoodState,
        stat_progression_multiplier: float,
        calculate_effectiveness_fn: Callable[[str, List[str]], float],
    ) -> Tuple[PokemonMoveSlot, str]:
        """
        STAGE 3 (DECIDE): Evaluates all unlocked opponent moves with remaining Power Points (PP)
        and selects the move that maximizes tactical utility for the current AgentMoodState.
        """
        available_moves: List[PokemonMoveSlot] = [
            move_slot
            for move_slot in opponent_monster.move_slots
            if move_slot.is_unlocked and move_slot.current_power_points > 0
        ]

        if not available_moves:
            fallback_move = opponent_monster.move_slots[0]
            return (
                fallback_move,
                f"All moves exhausted PP; defaulting to {fallback_move.move_name}.",
            )

        best_move_slot: PokemonMoveSlot = available_moves[0]
        highest_utility_score: float = -999.0
        best_reasoning_trace: str = ""

        for candidate_move in available_moves:
            effectiveness_multiplier = calculate_effectiveness_fn(
                candidate_move.elemental_type,
                player_monster.elemental_types,
            )

            # Never pick a 0.0x immune move if any non-immune move exists
            if effectiveness_multiplier == 0.0 and candidate_move.base_power > 0:
                utility_score = -100.0
                reasoning_note = (
                    f"Avoided {candidate_move.move_name} because {player_monster.pokemon_name} is immune (0x)."
                )
            elif candidate_move.base_power > 0:
                # Expected damage utility weighted by base power, elemental multiplier, and accuracy
                expected_damage_index = (
                    candidate_move.base_power
                    * effectiveness_multiplier
                    * (candidate_move.accuracy_percentage / 100.0)
                )

                # Under DESPERATE_CLUTCH or AGGRESSIVE mood, or when player has +1% stat boosts,
                # heavily reward maximum offensive output
                aggression_weight = (
                    1.35
                    if agent_mood in (AgentMoodState.DESPERATE_CLUTCH, AgentMoodState.AGGRESSIVE)
                    or stat_progression_multiplier > 1.0
                    else 1.15
                )
                utility_score = expected_damage_index * aggression_weight

                reasoning_note = (
                    f"Selected {candidate_move.move_name} [{candidate_move.elemental_type.upper()}] "
                    f"(Power {candidate_move.base_power}, {effectiveness_multiplier:g}x effectiveness vs "
                    f"{'/'.join(player_monster.elemental_types)}) under {agent_mood.value} posture "
                    f"against {stat_progression_multiplier:.2f}x scaled player threat."
                )
            else:
                # Status/defensive move (0 base power): low utility compared to damaging strikes
                utility_score = 8.0 if agent_mood == AgentMoodState.DEFENSIVE else 2.0
                reasoning_note = (
                    f"Selected tactical status move {candidate_move.move_name} under {agent_mood.value} posture."
                )

            if utility_score > highest_utility_score:
                highest_utility_score = utility_score
                best_move_slot = candidate_move
                best_reasoning_trace = reasoning_note

        return (best_move_slot, best_reasoning_trace)

    def generate_persona_taunt(
        self,
        persona: GymLeaderPersona,
        agent_mood: AgentMoodState,
        opponent_monster: ActiveBattleEntity,
        player_monster: ActiveBattleEntity,
        selected_move: PokemonMoveSlot,
        stat_progression_multiplier: float,
    ) -> str:
        """
        STAGE 4 (ACT): Generates an in-character stadium battle taunt conditioned on
        persona (BROCK, MISTY, or WILD_INSTINCT), current mood, and player stat scaling.
        """
        bonus_percent = int(round((stat_progression_multiplier - 1.0) * 100))
        scaling_callout = (
            f"even with your +{bonus_percent}% victory stat boost"
            if bonus_percent > 0
            else "in this arena"
        )

        if persona == GymLeaderPersona.BROCK:
            if agent_mood == AgentMoodState.DESPERATE_CLUTCH:
                return (
                    f"Brock: 'My rock-hard willpower never crumbles! Onix, unleash everything with {selected_move.move_name}!'"
                )
            return (
                f"Brock: 'Your {player_monster.pokemon_name} hits hard {scaling_callout}, "
                f"but {opponent_monster.pokemon_name}'s defense is impenetrable—counter with {selected_move.move_name}!'"
            )
        elif persona == GymLeaderPersona.MISTY:
            if agent_mood == AgentMoodState.DESPERATE_CLUTCH:
                return (
                    f"Misty: 'Don't think you've won yet! {opponent_monster.pokemon_name}, Turn the tide with {selected_move.move_name}!'"
                )
            return (
                f"Misty: 'My policy is an all-out offensive with Water-type Pokémon! "
                f"Even {scaling_callout}, {opponent_monster.pokemon_name}'s {selected_move.move_name} will wash {player_monster.pokemon_name} away!'"
            )
        else:
            if agent_mood == AgentMoodState.DESPERATE_CLUTCH:
                return (
                    f"Wild {opponent_monster.pokemon_name}'s eyes flare in a desperate clutch—launching a fierce {selected_move.move_name}!"
                )
            return (
                f"Wild {opponent_monster.pokemon_name} senses {player_monster.pokemon_name}'s "
                f"{stat_progression_multiplier:.2f}x battle aura and strikes back with {selected_move.move_name}!"
            )

    def evaluate_turn_decision_sync(
        self,
        player_monster: ActiveBattleEntity,
        opponent_monster: ActiveBattleEntity,
        calculate_effectiveness_fn: Callable[[str, List[str]], float],
        stat_progression_multiplier: float = 1.0,
        gym_leader_persona: Optional[GymLeaderPersona] = None,
        combat_memory_log: Optional[List[str]] = None,
    ) -> GymLeaderTurnDecision:
        """
        Synchronous execution of the Perceive -> Remember -> Decide -> Act agent loop.
        Used directly inside BattleEngineService.resolve_combat_round for zero-latency combat math.
        """
        start_timestamp = time.perf_counter()

        # Resolve persona from opponent ID if not explicitly provided
        resolved_persona = (
            gym_leader_persona
            if gym_leader_persona is not None
            else self.resolve_persona_for_opponent(opponent_monster.pokemon_id)
        )

        # 1. PERCEIVE: Compute dynamic threat level and mood
        calibrated_threat_score, agent_mood = self.calculate_dynamic_threat_level(
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            stat_progression_multiplier=stat_progression_multiplier,
            calculate_effectiveness_fn=calculate_effectiveness_fn,
        )

        # 2. REMEMBER: Inspect recent combat memory log if present
        memory_entries_count = len(combat_memory_log) if combat_memory_log else 0

        # 3. DECIDE: Choose the mathematically optimal move slot
        selected_move, reasoning_trace = self.select_optimal_opponent_move(
            opponent_monster=opponent_monster,
            player_monster=player_monster,
            agent_mood=agent_mood,
            stat_progression_multiplier=stat_progression_multiplier,
            calculate_effectiveness_fn=calculate_effectiveness_fn,
        )
        if memory_entries_count > 0:
            reasoning_trace = f"[Memory: {memory_entries_count} prior turns analyzed] {reasoning_trace}"

        # 4. ACT: Generate persona-conditioned battle taunt
        dialogue_taunt = self.generate_persona_taunt(
            persona=resolved_persona,
            agent_mood=agent_mood,
            opponent_monster=opponent_monster,
            player_monster=player_monster,
            selected_move=selected_move,
            stat_progression_multiplier=stat_progression_multiplier,
        )

        elapsed_ms = round((time.perf_counter() - start_timestamp) * 1000.0, 2)

        return GymLeaderTurnDecision(
            selected_move_id=selected_move.move_id,
            selected_move_name=selected_move.move_name,
            internal_tactical_reasoning=reasoning_trace,
            in_character_dialogue_taunt=dialogue_taunt,
            agent_mood=agent_mood,
            calibrated_threat_score=calibrated_threat_score,
            detected_player_stat_multiplier=round(stat_progression_multiplier, 2),
            gym_leader_persona=resolved_persona,
            active_provider_name="autonomous_agent_engine",
            execution_latency_milliseconds=elapsed_ms,
        )

    async def evaluate_turn_decision_for_session(
        self,
        battle_session: Dict,
        calculate_effectiveness_fn: Callable[[str, List[str]], float],
        gym_leader_persona: Optional[GymLeaderPersona] = None,
        use_llm_gateway: bool = False,
    ) -> GymLeaderTurnDecision:
        """
        Asynchronous wrapper that evaluates a live battle session dictionary,
        extracts the active monster's +1% stat_progression_multiplier from the party pool,
        and optionally enriches the battle taunt via the Resilient LLM Gateway.
        """
        start_timestamp = time.perf_counter()
        player_monster: ActiveBattleEntity = battle_session["player_monster"]
        opponent_monster: ActiveBattleEntity = battle_session["opponent_monster"]

        # Extract the active monster's stat_progression_multiplier from party_pool metadata
        detected_multiplier: float = 1.0
        party_pool_dict = battle_session.get("party_pool") or {}
        for party_member in party_pool_dict.get("party_monsters", []):
            if party_member.get("pokemon_id") == player_monster.pokemon_id:
                detected_multiplier = float(
                    party_member.get("stat_progression_multiplier", 1.0)
                )
                break

        combat_memory_log: List[str] = battle_session.setdefault("combat_memory_log", [])

        base_decision = self.evaluate_turn_decision_sync(
            player_monster=player_monster,
            opponent_monster=opponent_monster,
            calculate_effectiveness_fn=calculate_effectiveness_fn,
            stat_progression_multiplier=detected_multiplier,
            gym_leader_persona=gym_leader_persona,
            combat_memory_log=combat_memory_log,
        )

        if use_llm_gateway:
            try:
                prompt_template = build_gym_leader_agent_prompt()
                opponent_hp_pct = int(
                    round(
                        (
                            opponent_monster.current_health_points
                            / max(1, opponent_monster.maximum_health_points)
                        )
                        * 100
                    )
                )
                formatted_messages = prompt_template.format_messages(
                    gym_leader_persona=base_decision.gym_leader_persona.value,
                    agent_mood=base_decision.agent_mood.value,
                    opponent_monster_name=opponent_monster.pokemon_name,
                    opponent_hp_percentage=opponent_hp_pct,
                    player_monster_name=player_monster.pokemon_name,
                    detected_player_stat_multiplier=f"{detected_multiplier:.2f}",
                    calibrated_threat_score=base_decision.calibrated_threat_score,
                    combat_memory_summary=" | ".join(combat_memory_log[-3:])
                    if combat_memory_log
                    else "Opening round of the match.",
                    selected_move_name=base_decision.selected_move_name,
                    internal_tactical_reasoning=base_decision.internal_tactical_reasoning,
                )
                gateway_messages = [
                    LLMMessageItem(
                        role=LLMMessageRole.SYSTEM if idx == 0 else LLMMessageRole.USER,
                        content=str(msg.content),
                    )
                    for idx, msg in enumerate(formatted_messages)
                ]
                llm_envelope = await default_resilient_llm_gateway.generate_chat_completion(
                    conversation_messages=gateway_messages,
                )
                if (
                    llm_envelope.active_provider_name != "offline_fallback"
                    and llm_envelope.generated_message_content
                ):
                    base_decision.in_character_dialogue_taunt = (
                        llm_envelope.generated_message_content.strip()
                    )
                    base_decision.active_provider_name = llm_envelope.active_provider_name
            except Exception:
                pass

        base_decision.execution_latency_milliseconds = round(
            (time.perf_counter() - start_timestamp) * 1000.0, 2
        )
        return base_decision


# Global singleton instance for BattleEngineService and FastAPI routes
gym_leader_agent_service = GymLeaderAgentService()
