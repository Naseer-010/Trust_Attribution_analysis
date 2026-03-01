"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, MessageSquare, BarChart, ArrowRight } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/start`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to start experiment");
      const data = await res.json();

      // Store experiment data in sessionStorage
      sessionStorage.setItem("participant_id", data.participant_id);
      sessionStorage.setItem("condition_id", String(data.condition_id));
      sessionStorage.setItem("condition", JSON.stringify(data.condition));

      router.push("/task");
    } catch (err) {
      console.error("Start error:", err);
      alert("Could not connect to the experiment server. Is the backend running?");
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <div
        className="glass-card animate-fade-in"
        style={{ maxWidth: 680, width: "100%", textAlign: "center" }}
      >
        {/* Badge */}
        <div style={{ marginBottom: "1.5rem" }}>
          <span className="badge badge-purple">GSoC 2026 · Research Prototype</span>
        </div>

        {/* Title */}
        <h1 className="heading-xl" style={{ marginBottom: "1rem" }}>
          Human–AI Trust
          <br />
          Experimentation Engine
        </h1>

        {/* Description */}
        <p className="text-body" style={{ maxWidth: 480, margin: "0 auto 2rem" }}>
          Explore how interface cues like AI naming, tone, and confidence framing
          influence trust in AI-assisted decision making.
        </p>

        {/* Feature Grid */}
        <div className="feature-grid">
          <div className="feature-item animate-slide-up animate-delay-1">
            <div className="feature-icon"><Bot size={32} /></div>
            <div className="feature-title">Agent Identity</div>
            <div className="feature-desc">
              Neutral label vs. humanlike name
            </div>
          </div>
          <div className="feature-item animate-slide-up animate-delay-2">
            <div className="feature-icon"><MessageSquare size={32} /></div>
            <div className="feature-title">Communication Tone</div>
            <div className="feature-desc">
              Technical/formal vs. empathetic/social
            </div>
          </div>
          <div className="feature-item animate-slide-up animate-delay-3">
            <div className="feature-icon"><BarChart size={32} /></div>
            <div className="feature-title">Confidence Framing</div>
            <div className="feature-desc">
              Calibrated probability vs. authoritative
            </div>
          </div>
        </div>

        {/* Experiment Info */}
        <div
          className="glass-card-sm animate-slide-up animate-delay-4"
          style={{
            background: "var(--bg-glass)",
            border: "1px solid var(--border-glass)",
            borderRadius: "var(--radius-md)",
            padding: "1.25rem",
            marginBottom: "2rem",
          }}
        >
          <p className="text-small" style={{ marginBottom: "0.5rem" }}>
            <strong>What to expect:</strong>
          </p>
          <p className="text-small">
            You will be randomly assigned to an experimental condition. An AI
            assistant will present a recommendation for a business decision. You
            decide whether to <strong>Accept</strong> or{" "}
            <strong>Override</strong> the AI's recommendation. Your response time
            is measured at millisecond precision.
          </p>
        </div>

        {/* Start Button */}
        <button
          className={`btn btn-primary btn-lg ${loading ? "btn-disabled" : ""}`}
          onClick={handleStart}
          disabled={loading}
          id="start-experiment-btn"
        >
          {loading ? (
            <>
              <span
                className="spinner"
                style={{ width: 20, height: 20, borderWidth: 2 }}
              />
              Assigning Condition...
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              Start Experiment <ArrowRight size={18} />
            </div>
          )}
        </button>

        <p className="text-small" style={{ marginTop: "1rem" }}>
          IRB Protocol Placeholder · Data collected for research purposes only
        </p>
      </div>
    </div>
  );
}
