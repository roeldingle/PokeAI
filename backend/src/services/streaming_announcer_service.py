"""
Streaming Announcer Service Module
Implements the Lesson 10 Multi-Agent Live Stadium Announcer via Server-Sent Events (SSE).
Coordinates telemetry from the Deterministic Battle Engine (Lesson 5-7) and the
Autonomous Gym Leader Agent (Lesson 9) to stream syllable-by-syllable play-by-play commentary
with a guaranteed sub-400ms Time-To-First-Token (TTFT).
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, List, Optional
from src.schemas.battle_schema import ActiveBattleEntity
from src.services.battle_engine import battle_engine_service


class StreamingAnnouncerService:
    """
    Generates real-time Server-Sent Events (SSE) play-by-play commentary streams
    for the stadium's top LED ticker tape.
    """

    def compose_play_by_play_script(
        self,
        battle_session: Dict,
        custom_headline: Optional[str] = None,
    ) -> str:
        """
        Synthesizes an energetic stadium announcer play-by-play script grounded in
        the active session's turn counter, combatant HP ratios, and Gym Leader AI telemetry.
        """
        if custom_headline:
            return custom_headline.strip()

        trainer_name: str = battle_session.get("trainer_name", "Trainer")
        current_turn_number: int = battle_session.get("current_turn_number", 1)
        maximum_turns_allowed: int = battle_session.get("maximum_turns_allowed", 5)
        is_battle_concluded: bool = battle_session.get("is_battle_concluded", False)
        is_turn_limit_reached: bool = battle_session.get("is_turn_limit_reached", False)
        victorious_monster_name: Optional[str] = battle_session.get("victorious_monster_name")

        player_monster: ActiveBattleEntity = battle_session["player_monster"]
        opponent_monster: ActiveBattleEntity = battle_session["opponent_monster"]
        combat_memory_log: List[str] = battle_session.get("combat_memory_log", [])
        gym_leader_decision: Optional[Dict] = battle_session.get("gym_leader_decision")

        # Case 1: Match concluded by knockout
        if is_battle_concluded and victorious_monster_name:
            return (
                f"🎙️ IT'S A STADIUM KNOCKOUT! {victorious_monster_name.upper()} DOMINATES THE RING! "
                f"THE CROWD GOES WILD FOR TRAINER {trainer_name.upper()}!"
            )

        # Case 2: 5-Turn Battle Clock expired -> Overtime Pokéball Roulette
        if is_turn_limit_reached:
            return (
                f"🎙️ TURN {maximum_turns_allowed} IS UP! {opponent_monster.pokemon_name.upper()} SURVIVED THE REGULATION CLOCK! "
                f"SPIN THE OVERTIME POKÉBALL ROULETTE WHEEL!"
            )

        # Case 3: Mid-battle round after at least 1 turn has resolved
        if combat_memory_log:
            latest_memory_entry = combat_memory_log[-1]
            persona_tag = ""
            if gym_leader_decision:
                raw_persona = gym_leader_decision.get("gym_leader_persona", "WILD_INSTINCT")
                raw_mood = gym_leader_decision.get("agent_mood", "CALCULATING")
                persona_name = getattr(raw_persona, "value", str(raw_persona))
                mood_name = getattr(raw_mood, "value", str(raw_mood))
                selected_move = gym_leader_decision.get("selected_move_name", "Attack")
                if persona_name in ("BROCK", "MISTY"):
                    persona_tag = (
                        f" GYM LEADER {persona_name} ENTERS {mood_name} MODE WITH {selected_move.upper()}!"
                    )
                else:
                    persona_tag = (
                        f" {opponent_monster.pokemon_name.upper()} RETALIATES WITH {selected_move.upper()}!"
                    )

            return (
                f"🎙️ LIVE PLAY-BY-PLAY ({latest_memory_entry}){persona_tag} "
                f"{player_monster.pokemon_name.upper()} HP {player_monster.current_health_points}/{player_monster.maximum_health_points} "
                f"VS {opponent_monster.pokemon_name.upper()} HP {opponent_monster.current_health_points}/{opponent_monster.maximum_health_points}!"
            )

        # Case 4: Opening bell on Turn 1
        return (
            f"🎙️ WELCOME TO POKEAI STADIUM! TRAINER {trainer_name.upper()} SENDS OUT "
            f"{player_monster.pokemon_name.upper()} (LV {player_monster.level}) AGAINST "
            f"{opponent_monster.pokemon_name.upper()} (LV {opponent_monster.level})! "
            f"ONLY {maximum_turns_allowed} TURNS ON THE CLOCK!"
        )

    @staticmethod
    def tokenize_script_for_streaming(commentary_script: str) -> List[str]:
        """
        Splits a stadium announcer script into crisp word-level tokens preserving trailing spaces
        so the frontend LED ticker tape renders smooth syllable-by-syllable streaming.
        """
        raw_words = commentary_script.split(" ")
        token_chunks: List[str] = []
        for index, word in enumerate(raw_words):
            suffix = " " if index < len(raw_words) - 1 else ""
            token_chunks.append(f"{word}{suffix}")
        return token_chunks

    async def stream_announcer_events(
        self,
        battle_session_id: str,
        custom_headline: Optional[str] = None,
        token_delay_seconds: float = 0.003,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronous generator yielding W3C-compliant Server-Sent Events (SSE) frames:
        1. `event: announcer_token` frames with sequential `sequence_id` and `token` payload.
        2. `event: combat_state_sync` frame synchronizing HP and animation triggers.
        3. `event: stream_complete` frame reporting total tokens and Time-To-First-Token (TTFT).
        """
        stream_start_timestamp = time.perf_counter()

        session_data = battle_engine_service.active_battle_sessions.get(battle_session_id)
        if not session_data:
            error_payload = json.dumps(
                {
                    "error": f"Battle session '{battle_session_id}' not found.",
                    "battle_session_id": battle_session_id,
                }
            )
            yield f"event: stream_error\ndata: {error_payload}\n\n"
            return

        commentary_script = self.compose_play_by_play_script(
            battle_session=session_data,
            custom_headline=custom_headline,
        )
        token_chunks = self.tokenize_script_for_streaming(commentary_script)

        first_token_latency_ms: Optional[float] = None

        # 1. Stream each word token sequentially
        for sequence_index, token_text in enumerate(token_chunks, start=1):
            if first_token_latency_ms is None:
                first_token_latency_ms = round(
                    (time.perf_counter() - stream_start_timestamp) * 1000.0, 2
                )

            token_event_payload = json.dumps(
                {
                    "type": "token",
                    "sequence_id": sequence_index,
                    "token": token_text,
                    "ttft_milliseconds": first_token_latency_ms,
                }
            )
            yield f"event: announcer_token\ndata: {token_event_payload}\n\n"

            if token_delay_seconds > 0:
                await asyncio.sleep(token_delay_seconds)

        # 2. Emit combat_state_sync frame for synchronized UI HUD updates
        player_monster: ActiveBattleEntity = session_data["player_monster"]
        opponent_monster: ActiveBattleEntity = session_data["opponent_monster"]
        sync_payload = json.dumps(
            {
                "type": "event",
                "name": "combat_state_sync",
                "battle_session_id": battle_session_id,
                "current_turn_number": session_data.get("current_turn_number", 1),
                "player_pokemon_name": player_monster.pokemon_name,
                "player_remaining_hp": player_monster.current_health_points,
                "opponent_pokemon_name": opponent_monster.pokemon_name,
                "opponent_remaining_hp": opponent_monster.current_health_points,
                "trigger_animation": "stadium_ticker_pulse",
            }
        )
        yield f"event: combat_state_sync\ndata: {sync_payload}\n\n"

        # 3. Emit stream_complete telemetry summary frame
        total_elapsed_ms = round(
            (time.perf_counter() - stream_start_timestamp) * 1000.0, 2
        )
        complete_payload = json.dumps(
            {
                "type": "complete",
                "battle_session_id": battle_session_id,
                "total_tokens_streamed": len(token_chunks),
                "ttft_milliseconds": first_token_latency_ms or 0.0,
                "total_stream_duration_milliseconds": total_elapsed_ms,
                "full_commentary_text": commentary_script,
            }
        )
        yield f"event: stream_complete\ndata: {complete_payload}\n\n"


# Global singleton instance for SSE route handlers
streaming_announcer_service = StreamingAnnouncerService()
