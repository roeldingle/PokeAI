/**
 * Commentator Ticker Bar Component (Lesson 10)
 * Renders the top Stadium LED Ticker Tape streaming live AI Commentator play-by-play
 * syllable-by-syllable via FastAPI Server-Sent Events (SSE).
 */

import React from "react";

interface CommentatorTickerBarProps {
  commentaryText: string;
  isStreaming: boolean;
  timeToFirstTokenMs: number | null;
  totalTokensStreamed: number;
}

export const CommentatorTickerBar: React.FC<CommentatorTickerBarProps> = ({
  commentaryText,
  isStreaming,
  timeToFirstTokenMs,
  totalTokensStreamed,
}) => {
  return (
    <div
      style={{
        backgroundColor: "#0f172a",
        borderBottom: "3px solid #334155",
        padding: "8px 20px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "12px",
        color: "#f8fafc",
      }}
    >
      {/* Left: Live Streaming Commentary Text + Blinking Cursor */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flex: 1,
          minWidth: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-pixel)",
            fontSize: "0.52rem",
            backgroundColor: isStreaming ? "#22c55e" : "#3b82f6",
            color: "#ffffff",
            padding: "3px 7px",
            borderRadius: "4px",
            whiteSpace: "nowrap",
            letterSpacing: "0.5px",
          }}
        >
          {isStreaming ? "📡 SSE STREAMING" : "📡 SSE TICKER"}
        </span>

        <div
          style={{
            fontFamily: "var(--font-pixel)",
            fontSize: "0.64rem",
            color: "#fef08a",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            letterSpacing: "0.3px",
          }}
          title={commentaryText}
        >
          {commentaryText}
          {isStreaming && (
            <span
              style={{
                display: "inline-block",
                marginLeft: "4px",
                color: "#22c55e",
              }}
            >
              ▋
            </span>
          )}
        </div>
      </div>

      {/* Right: SSE TTFT & Token Telemetry */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          flexShrink: 0,
          fontFamily: "var(--font-pixel)",
          fontSize: "0.5rem",
          color: "#94a3b8",
        }}
      >
        {timeToFirstTokenMs !== null && (
          <span>⚡ TTFT {timeToFirstTokenMs}ms</span>
        )}
        {totalTokensStreamed > 0 && <span>• {totalTokensStreamed} tok</span>}
      </div>
    </div>
  );
};
