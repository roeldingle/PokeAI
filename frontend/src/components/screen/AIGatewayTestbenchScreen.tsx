/**
 * AIGatewayTestbenchScreen.tsx — Resilient AI Gateway Playground
 * Implements Storyboard Screen 1: Three-Channel Fallback Monitor & Prompt Testbench.
 */

import React, { useEffect, useState } from "react";
import { ButtonUI } from "../ui/ButtonUI";
import { ProviderStatusBadge } from "../ui/ProviderStatusBadge";
import { checkGatewayHealth, sendResilientPrompt } from "../../services/aiGatewayService";
import type {
  GatewayHealthResponse,
  LLMResponseEnvelope,
} from "../../types/aiGateway";

interface AIGatewayTestbenchScreenProps {
  onBackToPrevious: () => void;
}

export const AIGatewayTestbenchScreen: React.FC<AIGatewayTestbenchScreenProps> = ({
  onBackToPrevious,
}) => {
  const [healthData, setHealthData] = useState<GatewayHealthResponse | null>(null);
  const [testPrompt, setTestPrompt] = useState<string>("Ready for tournament battle, Trainer?");
  const [lastResponse, setLastResponse] = useState<LLMResponseEnvelope | null>(null);
  const [isPinging, setIsPinging] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadHealth() {
      try {
        const diagnostics = await checkGatewayHealth();
        setHealthData(diagnostics);
      } catch (err) {
        console.warn("Gateway health probe failed:", err);
      }
    }
    loadHealth();
  }, []);

  const handlePingGateway = async () => {
    if (!testPrompt.trim() || isPinging) return;
    setIsPinging(true);
    setErrorMessage(null);

    try {
      const responseEnvelope = await sendResilientPrompt(
        testPrompt,
        "You are the official PokeAI Stadium Battle Referee. Answer in 1 energetic sentence."
      );
      setLastResponse(responseEnvelope);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to ping gateway");
    } finally {
      setIsPinging(false);
    }
  };

  return (
    <div className="pokeai-viewport">
      <div className="gba-screen-chassis">
        <header className="stadium-header-bar">
          <span className="stadium-indicator">● LESSON 2: RESILIENT AI GATEWAY TESTBENCH</span>
          <ProviderStatusBadge
            activeProvider={lastResponse?.active_provider_name}
            modelIdentifier={lastResponse?.model_identifier}
            latencyMilliseconds={lastResponse?.execution_latency_milliseconds}
            fallbackTriggered={lastResponse?.fallback_triggered}
            isLoading={isPinging}
          />
        </header>

        <main className="landing-stage" style={{ padding: "20px", display: "flex", justifyContent: "center" }}>
          <div
            style={{
              width: "100%",
              maxWidth: "680px",
              backgroundColor: "#ffffff",
              border: "3px solid #1e293b",
              borderRadius: "12px",
              padding: "24px",
              boxShadow: "0 4px 0 #1e293b",
            }}
          >
            <div className="title-badge-top" style={{ marginBottom: "16px" }}>
              📡 THREE-CHANNEL RADIO TESTBENCH
            </div>

            {/* Channels Status Panel */}
            <div
              style={{
                backgroundColor: "#f8fafc",
                border: "2px solid #e2e8f0",
                borderRadius: "8px",
                padding: "12px 16px",
                marginBottom: "20px",
              }}
            >
              <div style={{ fontSize: "0.8rem", fontWeight: "700", color: "#64748b", marginBottom: "8px" }}>
                FALLBACK CASCADE FREQUENCIES:
              </div>
              {healthData?.channels.map((channel, idx) => (
                <div
                  key={channel.provider_name}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "4px 0",
                    fontSize: "0.85rem",
                    fontFamily: "var(--font-arcade-display, monospace)",
                  }}
                >
                  <span>
                    {idx + 1}. [{channel.provider_name.toUpperCase()}] ({channel.configured_model})
                  </span>
                  <span
                    style={{
                      color: channel.is_available ? "#059669" : "#94a3b8",
                      fontWeight: "700",
                    }}
                  >
                    {channel.is_available ? "● READY" : "○ UNCONFIGURED"}
                  </span>
                </div>
              ))}
            </div>

            {/* Test Prompt Input */}
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "700", marginBottom: "6px" }}>
              Test Arena Prompt:
            </label>
            <input
              type="text"
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              placeholder="Enter a prompt..."
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "2px solid #1e293b",
                borderRadius: "6px",
                fontSize: "0.95rem",
                fontFamily: "var(--font-arcade-display, monospace)",
                marginBottom: "16px",
                boxSizing: "border-box",
              }}
            />

            <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
              <ButtonUI onClick={handlePingGateway} variant="action" disabled={isPinging}>
                {isPinging ? "⚡ Pinging Cascade..." : "⚡ PING AI GATEWAY"}
              </ButtonUI>
              <ButtonUI onClick={onBackToPrevious} variant="default">
                ◀ Back to Registration
              </ButtonUI>
            </div>

            {/* Response Box */}
            {lastResponse && (
              <div
                style={{
                  backgroundColor: "#f1f5f9",
                  border: "2px solid #1e293b",
                  borderRadius: "8px",
                  padding: "16px",
                }}
              >
                <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", marginBottom: "6px" }}>
                  AI REFEREE RESPONSE (via {lastResponse.active_provider_name.toUpperCase()} in {lastResponse.execution_latency_milliseconds}ms):
                </div>
                <p style={{ margin: 0, fontSize: "1rem", lineHeight: "1.6", color: "#1e293b" }}>
                  "{lastResponse.generated_message_content}"
                </p>
              </div>
            )}

            {errorMessage && (
              <div style={{ color: "#dc2626", marginTop: "12px", fontSize: "0.85rem" }}>
                ⚠️ {errorMessage}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};