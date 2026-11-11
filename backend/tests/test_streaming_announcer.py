"""
Test Streaming Announcer Module
Unit and integration tests for Lesson 10 Live Stadium Announcer via SSE:
1. Play-by-play script composition across opening, mid-battle, overtime, and knockout states.
2. SSE event stream ordering (announcer_token -> combat_state_sync -> stream_complete) and sequence_id integrity.
3. Sub-400ms Time-To-First-Token (TTFT) latency SLA verification.
4. FastAPI text/event-stream endpoints (path and query parameter variants).
"""

import asyncio
import json
import time
from typing import List, Tuple
from fastapi.testclient import TestClient
from src.main import app
from src.services.battle_engine import battle_engine_service
from src.services.streaming_announcer_service import streaming_announcer_service


client = TestClient(app)


def _parse_sse_frames(raw_sse_stream_text: str) -> List[Tuple[str, dict]]:
    """
    Helper that parses raw W3C Server-Sent Events text into a list of (event_name, json_payload) tuples.
    """
    parsed_events: List[Tuple[str, dict]] = []
    raw_blocks = [block.strip() for block in raw_sse_stream_text.strip().split("\n\n") if block.strip()]
    for block in raw_blocks:
        lines = block.splitlines()
        event_name = "message"
        data_json = "{}"
        for line in lines:
            if line.startswith("event:"):
                event_name = line.replace("event:", "", 1).strip()
            elif line.startswith("data:"):
                data_json = line.replace("data:", "", 1).strip()
        parsed_events.append((event_name, json.loads(data_json)))
    return parsed_events


def test_announcer_script_composition_across_battle_phases() -> None:
    """
    Verifies that compose_play_by_play_script accurately reflects:
    - Opening bell on Turn 1
    - Mid-battle multi-agent clash (Player move + Gym Leader Misty AI counter)
    - Match conclusion knockout headline
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="AnnouncerTester",
        selected_pokemon_id=4,    # Charmander
        opponent_pokemon_id=121,  # Gym Leader Misty's Starmie
    )
    battle_session_id = session_state["battle_session_id"]

    # 1. Opening bell script
    opening_script = streaming_announcer_service.compose_play_by_play_script(
        battle_session=session_state
    )
    assert "CHARMANDER" in opening_script
    assert "STARMIE" in opening_script
    assert "5 TURNS" in opening_script

    # 2. Resolve 1 round of combat and verify multi-agent play-by-play script
    battle_engine_service.resolve_combat_round(
        battle_session_id=battle_session_id,
        selected_move_id=1,  # Scratch
        deterministic_mode=True,
    )
    mid_battle_script = streaming_announcer_service.compose_play_by_play_script(
        battle_session=session_state
    )
    assert "GYM LEADER MISTY" in mid_battle_script
    assert "WATER GUN" in mid_battle_script

    # 3. Simulate knockout conclusion
    session_state["is_battle_concluded"] = True
    session_state["victorious_monster_name"] = "Charmander"
    knockout_script = streaming_announcer_service.compose_play_by_play_script(
        battle_session=session_state
    )
    assert "KNOCKOUT" in knockout_script
    assert "CHARMANDER" in knockout_script


def test_sse_token_stream_ordering_and_sequence_integrity() -> None:
    """
    Verifies that stream_announcer_events yields:
    1. Sequential announcer_token events (sequence_id = 1..N) that reconstruct the exact script.
    2. A combat_state_sync event containing live HP telemetry.
    3. A stream_complete event summarizing token count and latency.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="StreamOrderTester",
        selected_pokemon_id=1,  # Bulbasaur
        opponent_pokemon_id=95, # Brock's Onix
    )
    battle_session_id = session_state["battle_session_id"]

    async def collect_stream() -> str:
        chunks: List[str] = []
        async for sse_frame in streaming_announcer_service.stream_announcer_events(
            battle_session_id=battle_session_id,
            token_delay_seconds=0.0,
        ):
            chunks.append(sse_frame)
        return "".join(chunks)

    raw_stream_output = asyncio.run(collect_stream())
    parsed_frames = _parse_sse_frames(raw_stream_output)

    # Must have at least 5 token frames + 1 sync frame + 1 complete frame
    assert len(parsed_frames) >= 7

    # Last two frames must be combat_state_sync followed by stream_complete
    assert parsed_frames[-2][0] == "combat_state_sync"
    assert parsed_frames[-1][0] == "stream_complete"

    # All preceding frames must be announcer_token with strictly sequential sequence_ids
    token_frames = parsed_frames[:-2]
    reconstructed_text = ""
    for expected_seq, (event_name, payload) in enumerate(token_frames, start=1):
        assert event_name == "announcer_token"
        assert payload["sequence_id"] == expected_seq
        reconstructed_text += payload["token"]

    assert reconstructed_text == parsed_frames[-1][1]["full_commentary_text"]


def test_sub_400ms_time_to_first_token_sla() -> None:
    """
    Verifies that the first announcer_token event is emitted in well under 400ms
    to guarantee instant stadium ticker tape responsiveness.
    """
    session_state = battle_engine_service.initialize_battle_session(
        trainer_name="LatencySLATester",
        selected_pokemon_id=7,
        opponent_pokemon_id=16,
    )
    battle_session_id = session_state["battle_session_id"]

    async def measure_first_token_ms() -> float:
        start_time = time.perf_counter()
        async for sse_frame in streaming_announcer_service.stream_announcer_events(
            battle_session_id=battle_session_id,
            token_delay_seconds=0.0,
        ):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            parsed = _parse_sse_frames(sse_frame)
            assert parsed[0][0] == "announcer_token"
            return elapsed_ms
        return 9999.0

    measured_ttft_ms = asyncio.run(measure_first_token_ms())
    assert measured_ttft_ms < 400.0


def test_fastapi_sse_streaming_endpoints_path_and_query() -> None:
    """
    Verifies both GET /api/v1/battle/stream/{battle_session_id} and
    GET /api/v1/battle/stream?battle_session_id=... return text/event-stream responses.
    """
    init_response = client.post(
        "/api/v1/battle/initiate",
        json={
            "trainer_name": "SSEEndpointTrainer",
            "selected_pokemon_id": 4,
            "opponent_pokemon_id": 16,
        },
    )
    assert init_response.status_code == 201
    battle_session_id = init_response.json()["battle_session"]["battle_session_id"]

    # 1. Test path parameter SSE endpoint
    path_response = client.get(f"/api/v1/battle/stream/{battle_session_id}")
    assert path_response.status_code == 200
    assert "text/event-stream" in path_response.headers["content-type"]
    path_frames = _parse_sse_frames(path_response.text)
    assert any(event_name == "announcer_token" for event_name, _ in path_frames)
    assert path_frames[-1][0] == "stream_complete"

    # 2. Test query parameter SSE endpoint with custom headline
    query_response = client.get(
        f"/api/v1/battle/stream?battle_session_id={battle_session_id}&headline=CHARMANDER+STEPS+INTO+THE+RING!"
    )
    assert query_response.status_code == 200
    query_frames = _parse_sse_frames(query_response.text)
    assert query_frames[-1][1]["full_commentary_text"] == "CHARMANDER STEPS INTO THE RING!"

    # 3. Test 404 for unknown battle session
    missing_response = client.get("/api/v1/battle/stream/nonexistent-sse-session")
    assert missing_response.status_code == 404
