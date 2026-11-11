"""
Streaming Routes Module (Lesson 10)
Exposes Server-Sent Events (SSE) endpoints under /api/v1/battle/stream
for real-time syllable-by-syllable Stadium Announcer play-by-play commentary.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from src.services.battle_engine import battle_engine_service
from src.services.streaming_announcer_service import streaming_announcer_service

# Initialize dedicated SSE streaming router
streaming_router = APIRouter(
    prefix="/api/v1/battle",
    tags=["Live Stadium Announcer (SSE)"],
)

# Standard HTTP headers required to prevent reverse proxies from buffering SSE token streams
SSE_RESPONSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@streaming_router.get(
    "/stream/{battle_session_id}",
    summary="Stream live play-by-play Stadium Announcer tokens via SSE",
)
async def stream_battle_commentary_by_path(
    battle_session_id: str,
    headline: Optional[str] = Query(
        default=None,
        description="Optional custom announcer headline to stream.",
    ),
) -> StreamingResponse:
    """
    Opens a unidirectional Server-Sent Events (SSE) stream (`text/event-stream`)
    emitting `announcer_token`, `combat_state_sync`, and `stream_complete` events.
    """
    if battle_session_id not in battle_engine_service.active_battle_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle session '{battle_session_id}' not found.",
        )

    event_generator = streaming_announcer_service.stream_announcer_events(
        battle_session_id=battle_session_id,
        custom_headline=headline,
    )
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers=SSE_RESPONSE_HEADERS,
    )


@streaming_router.get(
    "/stream",
    summary="Stream live Stadium Announcer tokens via query parameter",
)
async def stream_battle_commentary_by_query(
    battle_session_id: str = Query(
        ...,
        min_length=1,
        description="Active battle session ID to stream commentary for.",
    ),
    headline: Optional[str] = Query(
        default=None,
        description="Optional custom announcer headline to stream.",
    ),
) -> StreamingResponse:
    """
    Query-parameter SSE endpoint (`GET /api/v1/battle/stream?battle_session_id=...`)
    matching Storyboard Screen 6 EventSource convention.
    """
    if battle_session_id not in battle_engine_service.active_battle_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle session '{battle_session_id}' not found.",
        )

    event_generator = streaming_announcer_service.stream_announcer_events(
        battle_session_id=battle_session_id,
        custom_headline=headline,
    )
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers=SSE_RESPONSE_HEADERS,
    )
