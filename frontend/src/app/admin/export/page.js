"use client";

import { useState, useEffect } from "react";
import { RefreshCw, Download, AlertTriangle, Inbox, Check, X, ArrowLeft } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminExportPage() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/data`);
            if (!res.ok) throw new Error("Failed to fetch data");
            const json = await res.json();
            setData(json.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        window.open(`${API_BASE}/admin/export`, "_blank");
    };

    // ─── Summary Stats ──────────────────────────────────────────
    const totalEntries = data.length;
    const acceptCount = data.filter((d) => d.decision === "Accept").length;
    const overrideCount = data.filter((d) => d.decision === "Override").length;
    const avgLatency =
        totalEntries > 0
            ? Math.round(
                data.reduce((sum, d) => sum + parseFloat(d.latency_ms || 0), 0) /
                totalEntries
            )
            : 0;

    return (
        <div className="page-top">
            <div style={{ maxWidth: 1100, width: "100%" }}>
                {/* Header */}
                <div className="admin-header animate-fade-in">
                    <div>
                        <h1 className="heading-lg">Experiment Dashboard</h1>
                        <p className="text-small" style={{ marginTop: "0.35rem" }}>
                            Accumulated behavioral data from all participants
                        </p>
                    </div>
                    <div style={{ display: "flex", gap: "0.75rem" }}>
                        <button className="btn btn-ghost" onClick={() => fetchData()} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <RefreshCw size={16} /> Refresh
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={handleDownload}
                            disabled={totalEntries === 0}
                            id="download-csv-btn"
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        >
                            <Download size={16} /> Download CSV
                        </button>
                    </div>
                </div>

                {/* Summary Stats */}
                <div
                    className="animate-slide-up"
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(4, 1fr)",
                        gap: "1rem",
                        marginBottom: "2rem",
                    }}
                >
                    <div className="glass-card glass-card-sm" style={{ textAlign: "center" }}>
                        <div className="stat-value">{totalEntries}</div>
                        <div className="stat-label">Total Responses</div>
                    </div>
                    <div className="glass-card glass-card-sm" style={{ textAlign: "center" }}>
                        <div className="stat-value" style={{ color: "var(--accent-teal)" }}>
                            {acceptCount}
                        </div>
                        <div className="stat-label">Accepted</div>
                    </div>
                    <div className="glass-card glass-card-sm" style={{ textAlign: "center" }}>
                        <div className="stat-value" style={{ color: "var(--accent-rose)" }}>
                            {overrideCount}
                        </div>
                        <div className="stat-label">Overridden</div>
                    </div>
                    <div className="glass-card glass-card-sm" style={{ textAlign: "center" }}>
                        <div className="stat-value">{avgLatency}ms</div>
                        <div className="stat-label">Avg Latency</div>
                    </div>
                </div>

                {/* Data Table */}
                <div className="glass-card animate-slide-up animate-delay-2" style={{ padding: "0", overflow: "hidden" }}>
                    {loading ? (
                        <div className="loading-container" style={{ padding: "3rem" }}>
                            <div className="spinner" />
                            <p className="text-body">Loading data...</p>
                        </div>
                    ) : error ? (
                        <div className="empty-state">
                            <div className="empty-state-icon"><AlertTriangle size={48} className="text-muted" /></div>
                            <p className="text-body">Error: {error}</p>
                            <p className="text-small">Make sure the backend is running on port 8000</p>
                        </div>
                    ) : totalEntries === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon"><Inbox size={48} className="text-muted" /></div>
                            <p className="text-body">No data collected yet</p>
                            <p className="text-small">
                                Complete an experiment task to see data here
                            </p>
                        </div>
                    ) : (
                        <div className="admin-table-wrapper">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Participant</th>
                                        <th>Condition</th>
                                        <th>Agent</th>
                                        <th>Tone</th>
                                        <th>Confidence</th>
                                        <th>Decision</th>
                                        <th>Latency</th>
                                        <th>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.map((row, i) => (
                                        <tr key={i}>
                                            <td className="text-mono">{row.participant_id}</td>
                                            <td>
                                                <span className="badge badge-blue">#{row.condition_id}</span>
                                            </td>
                                            <td>{row.agent_name}</td>
                                            <td>{row.tone_style}</td>
                                            <td>{row.confidence_framing}</td>
                                            <td
                                                className={
                                                    row.decision === "Accept"
                                                        ? "decision-accept"
                                                        : "decision-override"
                                                }
                                            >
                                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                                                    {row.decision === "Accept" ? <Check size={16} /> : <X size={16} />}
                                                    {row.decision}
                                                </div>
                                            </td>
                                            <td className="text-mono">
                                                {parseFloat(row.latency_ms).toFixed(1)}ms
                                            </td>
                                            <td className="text-small">
                                                {new Date(row.timestamp).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Back link */}
                <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
                    <a
                        href="/"
                        className="text-small"
                        style={{ color: "var(--accent-blue)", textDecoration: "none", display: 'inline-flex', alignItems: 'center', gap: '0.25rem', justifyContent: 'center' }}
                    >
                        <ArrowLeft size={16} /> Back to Experiment
                    </a>
                </div>
            </div>
        </div>
    );
}
