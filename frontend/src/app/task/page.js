"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, ArrowRight, Check, X as XIcon } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TaskPage() {
    const router = useRouter();

    // Experiment state
    const [participantId, setParticipantId] = useState(null);
    const [conditionId, setConditionId] = useState(null);
    const [condition, setCondition] = useState(null);

    // Task state
    const [recommendation, setRecommendation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [phase, setPhase] = useState("loading"); // loading | deciding | complete
    const [decision, setDecision] = useState(null);
    const [latencyMs, setLatencyMs] = useState(null);

    // High-resolution timing
    const renderTimestamp = useRef(null);

    // ─── Load experiment data from session ─────────────────────
    useEffect(() => {
        const pid = sessionStorage.getItem("participant_id");
        const cid = sessionStorage.getItem("condition_id");
        const cond = sessionStorage.getItem("condition");

        if (!pid || !cid || !cond) {
            router.push("/");
            return;
        }

        setParticipantId(pid);
        setConditionId(parseInt(cid));
        setCondition(JSON.parse(cond));
    }, [router]);

    // ─── Fetch AI recommendation once condition is loaded ──────
    useEffect(() => {
        if (!conditionId) return;

        const fetchRecommendation = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/recommendation`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ condition_id: conditionId }),
                });
                if (!res.ok) throw new Error("Failed to fetch recommendation");
                const data = await res.json();
                setRecommendation(data.recommendation);
                setLoading(false);
                setPhase("deciding");

                // Mark the exact moment the AI response is rendered
                // Using performance.now() for sub-millisecond precision
                renderTimestamp.current = performance.now();
            } catch (err) {
                console.error("Recommendation error:", err);
                alert("Failed to load AI recommendation. Check the backend.");
            }
        };

        fetchRecommendation();
    }, [conditionId]);

    // ─── Handle decision ───────────────────────────────────────
    const handleDecision = useCallback(
        async (userDecision) => {
            if (phase !== "deciding") return;

            // Calculate latency from render to click using performance.now()
            const clickTimestamp = performance.now();
            const latency = Math.round((clickTimestamp - renderTimestamp.current) * 100) / 100;

            setDecision(userDecision);
            setLatencyMs(latency);
            setPhase("complete");

            // Build cue metadata
            const cueMetadata = {
                agent_name: condition?.agent_identity?.name || "",
                tone_style: condition?.tone?.style || "",
                confidence_framing: condition?.confidence?.framing || "",
            };

            // Log to backend
            try {
                await fetch(`${API_BASE}/api/log`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        participant_id: participantId,
                        condition_id: conditionId,
                        cue_metadata: cueMetadata,
                        ai_recommendation: recommendation?.recommendation || "",
                        scenario_id: recommendation?.scenario_id || null,
                        correct_answer: recommendation?.correct_answer || "",
                        confidence_score: recommendation?.confidence_score || null,
                        decision: userDecision,
                        latency_ms: latency,
                        timestamp: new Date().toISOString(),
                    }),
                });
            } catch (err) {
                console.error("Logging error:", err);
            }
        },
        [phase, condition, participantId, conditionId, recommendation]
    );

    // ─── Loading State ─────────────────────────────────────────
    if (loading || !condition) {
        return (
            <div className="page-center">
                <div className="loading-container animate-fade-in">
                    <div className="spinner" />
                    <p className="text-body">Preparing your decision task...</p>
                    <p className="text-small">
                        Condition #{conditionId} · Participant {participantId}
                    </p>
                </div>
            </div>
        );
    }

    // ─── Completion State ──────────────────────────────────────
    if (phase === "complete") {
        return (
            <div className="page-center">
                <div className="glass-card completion-card animate-fade-in">
                    <div className="completion-icon"><CheckCircle size={64} className="text-success" /></div>
                    <h2 className="heading-lg" style={{ marginBottom: "0.75rem" }}>
                        Task Complete
                    </h2>
                    <p className="text-body">
                        Thank you for participating in this experiment.
                    </p>

                    <div className="completion-stats">
                        <div className="stat-item">
                            <div className="stat-value">{decision}</div>
                            <div className="stat-label">Your Decision</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{latencyMs}ms</div>
                            <div className="stat-label">Response Latency</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">#{conditionId}</div>
                            <div className="stat-label">Condition</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{participantId}</div>
                            <div className="stat-label">Participant ID</div>
                        </div>
                    </div>

                    <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
                        <button
                            className="btn btn-primary"
                            onClick={() => {
                                sessionStorage.clear();
                                router.push("/");
                            }}
                        >
                            Start New Session
                        </button>
                        <button
                            className="btn btn-ghost"
                            onClick={() => router.push("/admin/export")}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        >
                            View Data <ArrowRight size={16} />
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // ─── Decision Task UI ──────────────────────────────────────
    const agentName = condition.agent_identity?.name || "AI Assistant";
    const toneStyle = condition.tone?.style || "Technical";
    const confidenceFraming = condition.confidence?.framing || "Probabilistic";
    const rec = recommendation || {};

    return (
        <div className="page-center">
            <div
                className="animate-fade-in"
                style={{ maxWidth: 720, width: "100%" }}
            >
                {/* Header Bar */}
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "1.5rem",
                        flexWrap: "wrap",
                        gap: "0.75rem",
                    }}
                >
                    <div>
                        <span className="badge badge-blue">Condition #{conditionId}</span>
                    </div>
                    <div className="text-mono text-small">
                        Participant: {participantId}
                    </div>
                </div>

                {/* Cue Display Grid */}
                <div className="cue-grid">
                    <div className="cue-item">
                        <div className="cue-label">Agent Identity</div>
                        <div className="cue-value">{agentName}</div>
                    </div>
                    <div className="cue-item">
                        <div className="cue-label">Tone</div>
                        <div className="cue-value">{toneStyle}</div>
                    </div>
                    <div className="cue-item">
                        <div className="cue-label">Confidence</div>
                        <div className="cue-value">{confidenceFraming}</div>
                    </div>
                </div>

                {/* Scenario Context */}
                <div className="scenario-card animate-slide-up animate-delay-1">
                    <div className="scenario-label">Decision Scenario</div>
                    <div className="scenario-text">
                        {rec.scenario || "Loading scenario..."}
                    </div>
                </div>

                {/* AI Recommendation */}
                <div className="ai-response-card animate-slide-up animate-delay-2">
                    {/* Agent Header */}
                    <div className="ai-agent-header">
                        <div className="ai-avatar">
                            {agentName === "Sarah" ? "S" : "X"}
                        </div>
                        <div>
                            <div className="ai-agent-name">{agentName}</div>
                            <div className="ai-agent-role">AI Decision Advisor</div>
                        </div>
                    </div>

                    {/* Recommendation */}
                    <div
                        className={`ai-recommendation ${rec.recommendation === "Accept" ? "accept" : "reject"
                            }`}
                    >
                        <span>{rec.recommendation === "Accept" ? <Check size={20} /> : <XIcon size={20} />}</span>
                        <span>
                            Recommendation:{" "}
                            <strong>{rec.recommendation || "..."}</strong>
                        </span>
                    </div>

                    {/* Confidence Bar */}
                    <div className="ai-confidence">
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >
                            <span className="text-small">Confidence Level</span>
                            <span
                                className="text-mono"
                                style={{ color: "var(--accent-blue)" }}
                            >
                                {rec.confidence_score || 0}%
                            </span>
                        </div>
                        <div className="confidence-bar">
                            <div
                                className="confidence-fill"
                                style={{ width: `${rec.confidence_score || 0}%` }}
                            />
                        </div>
                    </div>

                    {/* Explanation */}
                    <div className="ai-explanation">{rec.explanation || "..."}</div>
                </div>

                {/* Decision Prompt */}
                <div
                    className="animate-slide-up animate-delay-3"
                    style={{ textAlign: "center", marginTop: "1.5rem" }}
                >
                    <p
                        className="heading-md"
                        style={{ marginBottom: "0.5rem" }}
                    >
                        What is your decision?
                    </p>
                    <p className="text-small" style={{ marginBottom: "1.5rem" }}>
                        Do you accept or override the AI recommendation?
                    </p>

                    <div className="decision-buttons">
                        <button
                            className="btn btn-accept"
                            onClick={() => handleDecision("Accept")}
                            id="accept-btn"
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                        >
                            <Check size={18} /> Accept Recommendation
                        </button>
                        <button
                            className="btn btn-override"
                            onClick={() => handleDecision("Override")}
                            id="override-btn"
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                        >
                            <XIcon size={18} /> Override Recommendation
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
