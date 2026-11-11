/**
 * useCommentatorStream Hook (Lesson 10)
 * Connects to the FastAPI Server-Sent Events (SSE) endpoint (/api/v1/battle/stream/{battle_session_id})
 * using the browser's native EventSource API to stream real-time play-by-play tokens
 * onto the top Stadium LED Ticker Tape.
 */

import { useState, useCallback, useRef, useEffect } from "react";

const BACKEND_API_BASE_URL =
  import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

export interface CommentatorStreamState {
  commentaryText: string;
  isStreaming: boolean;
  timeToFirstTokenMs: number | null;
  totalTokensStreamed: number;
  triggerCommentaryStream: (
    battleSessionId: string,
    customHeadline?: string
  ) => void;
}

export function useCommentatorStream(
  initialHeadline: string = "🎙️ WELCOME TO POKEAI STADIUM! BOTH COMBATANTS ENTER THE RING!"
): CommentatorStreamState {
  const [commentaryText, setCommentaryText] = useState<string>(initialHeadline);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [timeToFirstTokenMs, setTimeToFirstTokenMs] = useState<number | null>(
    null
  );
  const [totalTokensStreamed, setTotalTokensStreamed] = useState<number>(0);

  // Reference to active EventSource so we can cleanly close prior streams on new turns
  const activeEventSourceRef = useRef<EventSource | null>(null);

  const closeActiveStream = useCallback(() => {
    if (activeEventSourceRef.current) {
      activeEventSourceRef.current.close();
      activeEventSourceRef.current = null;
    }
  }, []);

  const triggerCommentaryStream = useCallback(
    (battleSessionId: string, customHeadline?: string) => {
      if (!battleSessionId) return;

      // Close any previous in-flight EventSource stream
      closeActiveStream();

      setCommentaryText("");
      setIsStreaming(true);
      setTotalTokensStreamed(0);

      const queryParams = customHeadline
        ? `?headline=${encodeURIComponent(customHeadline)}`
        : "";
      const streamUrl = `${BACKEND_API_BASE_URL}/api/v1/battle/stream/${encodeURIComponent(
        battleSessionId
      )}${queryParams}`;

      try {
        const eventSource = new EventSource(streamUrl);
        activeEventSourceRef.current = eventSource;

        // 1. Handle incoming syllable/word tokens
        eventSource.addEventListener("announcer_token", (messageEvent) => {
          try {
            const payload = JSON.parse(messageEvent.data);
            if (typeof payload.token === "string") {
              setCommentaryText((prev) => prev + payload.token);
            }
            if (typeof payload.sequence_id === "number") {
              setTotalTokensStreamed(payload.sequence_id);
            }
            if (typeof payload.ttft_milliseconds === "number") {
              setTimeToFirstTokenMs(payload.ttft_milliseconds);
            }
          } catch {
            // Ignore malformed individual frame
          }
        });

        // 2. Handle stream completion
        eventSource.addEventListener("stream_complete", (messageEvent) => {
          try {
            const payload = JSON.parse(messageEvent.data);
            if (typeof payload.full_commentary_text === "string") {
              setCommentaryText(payload.full_commentary_text);
            }
            if (typeof payload.total_tokens_streamed === "number") {
              setTotalTokensStreamed(payload.total_tokens_streamed);
            }
          } catch {
            // Ignore parse error
          } finally {
            setIsStreaming(false);
            closeActiveStream();
          }
        });

        // 3. Graceful fallback on EventSource network disconnect
        eventSource.onerror = () => {
          setIsStreaming(false);
          closeActiveStream();
          setCommentaryText((prev) =>
            prev.trim().length > 0
              ? prev
              : customHeadline ||
                "🎙️ STADIUM ANNOUNCER: Both monsters clash fiercely in the center ring!"
          );
        };
      } catch {
        setIsStreaming(false);
        setCommentaryText(
          customHeadline ||
            "🎙️ STADIUM ANNOUNCER: Both monsters clash fiercely in the center ring!"
        );
      }
    },
    [closeActiveStream]
  );

  // Clean up EventSource on component unmount
  useEffect(() => {
    return () => {
      closeActiveStream();
    };
  }, [closeActiveStream]);

  return {
    commentaryText,
    isStreaming,
    timeToFirstTokenMs,
    totalTokensStreamed,
    triggerCommentaryStream,
  };
}
