/**
 * ProviderStatusBadge.tsx — Daylight Stadium HUD Telemetry Pill
 * Renders real-time connection status, active LLM provider channel, and round-trip latency in milliseconds.
 */

import React from "react";
import type { AIProviderName } from "../../types/aiGateway";

interface ProviderStatusBadgeProps {
  activeProvider?: AIProviderName;
  modelIdentifier?: string;
  latencyMilliseconds?: number;
  fallbackTriggered?: boolean;
  isLoading?: boolean;
  onClickBadge?: () => void;
}

export const ProviderStatusBadge: React.FC<ProviderStatusBadgeProps> = ({
  activeProvider = "offline_fallback",
  modelIdentifier,
  latencyMilliseconds,
  fallbackTriggered = false,
  isLoading = false,
  onClickBadge,
}) => {
  const getProviderIndicatorColor = (provider: AIProviderName): string => {
    switch (provider) {
      case "ollama":
        return "#3b82f6"; // Royal blue for local Ollama
      case "groq":
        return "#10b981"; // Emerald green for high-speed Groq LPU
      case "gemini":
        return "#8b5cf6"; // Purple for Google Gemini reasoning
      case "offline_fallback":
      default:
        return "#f59e0b"; // Warm amber for offline fallback
    }
  };

  const getProviderDisplayLabel = (provider: AIProviderName): string => {
    switch (provider) {
      case "ollama":
        return "OLLAMA";
      case "groq":
        return "GROQ";
      case "gemini":
        return "GEMINI";
      case "offline_fallback":
      default:
        return "OFFLINE";
    }
  };

  const indicatorColor = getProviderIndicatorColor(activeProvider);
  const displayLabel = getProviderDisplayLabel(activeProvider);

  return (
    <div
      className="provider-status-badge-container"
      onClick={onClickBadge}
      role={onClickBadge ? "button" : undefined}
      tabIndex={onClickBadge ? 0 : undefined}
      title={
        fallbackTriggered
          ? `Primary channel failed; failover active (${displayLabel})`
          : `Active AI channel: ${displayLabel}`
      }
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        padding: "4px 12px",
        backgroundColor: "#ffffff",
        border: "2px solid #1e293b",
        borderRadius: "20px",
        fontSize: "0.75rem",
        fontWeight: "700",
        fontFamily: "var(--font-arcade-display, monospace)",
        color: "#1e293b",
        boxShadow: "0 2px 0 #1e293b",
        cursor: onClickBadge ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      {/* Pulsing channel frequency dot */}
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: isLoading ? "#94a3b8" : indicatorColor,
          boxShadow: isLoading ? "none" : `0 0 6px ${indicatorColor}`,
          display: "inline-block",
        }}
      />

      {/* Active Provider Tag */}
      <span>{isLoading ? "ROUTING..." : displayLabel}</span>

      {/* Model Name snippet */}
      {modelIdentifier && !isLoading && (
        <span
          style={{
            color: "#64748b",
            fontWeight: "600",
            maxWidth: "120px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          [{modelIdentifier}]
        </span>
      )}

      {/* Latency Meter */}
      {typeof latencyMilliseconds === "number" && !isLoading && (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "2px",
            color: latencyMilliseconds < 500 ? "#059669" : "#d97706",
            fontWeight: "800",
          }}
        >
          ⚡ {latencyMilliseconds}ms
        </span>
      )}

      {/* Failover pill */}
      {fallbackTriggered && !isLoading && (
        <span
          style={{
            backgroundColor: "#fef3c7",
            color: "#b45309",
            border: "1px solid #f59e0b",
            borderRadius: "4px",
            padding: "1px 4px",
            fontSize: "0.65rem",
          }}
        >
          FALLBACK
        </span>
      )}
    </div>
  );
};