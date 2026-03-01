"""
Trust Experiment Analysis Script
=================================
Comprehensive trust calibration analysis for Human-AI decision experiments.

Metrics computed:
  1. Trust Agreement Rate (decision matches AI recommendation)
  2. Appropriate Reliance (accept when AI is correct)
  3. Over-reliance (accept when AI is wrong)
  4. Under-reliance (override when AI is correct)
  5. Trust Discrimination Score (appropriate trust vs over-trust ratio)
  6. Latency-based insights (deliberation patterns)
  7. Cue dimension effects with statistical testing
  8. Per-participant trust profiles

Usage:
    python analyze_results.py
    python analyze_results.py --csv ../data/results.csv
"""

import argparse
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)


# ─── Data Loading ────────────────────────────────────────────────────────────

def load_data(csv_path: str) -> pd.DataFrame:
    """Load and validate experiment data from CSV."""
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        print("   Run the experiment first to generate data.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")

    if "confidence_score" in df.columns:
        df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce")

    # Derived columns
    if "ai_recommendation" in df.columns and "correct_answer" in df.columns:
        df["ai_is_correct"] = df["ai_recommendation"] == df["correct_answer"]
        df["user_agreed_with_ai"] = df["decision"] == df["ai_recommendation"]
        df["user_was_correct"] = df["decision"] == df["correct_answer"]
    else:
        df["ai_is_correct"] = np.nan
        df["user_agreed_with_ai"] = np.nan
        df["user_was_correct"] = np.nan

    print(f"Loaded {len(df)} records from {csv_path}\n")
    return df


# ─── Core Trust Metrics ─────────────────────────────────────────────────────

def compute_overall_trust_metrics(df: pd.DataFrame) -> dict:
    """Compute the fundamental trust calibration metrics."""
    total = len(df)
    if total == 0:
        return {}

    accepts = (df["decision"] == "Accept").sum()
    overrides = (df["decision"] == "Override").sum()

    metrics = {
        "total_responses": total,
        "accept_count": int(accepts),
        "override_count": int(overrides),
        "reliance_rate_pct": round(accepts / total * 100, 1),
        "override_rate_pct": round(overrides / total * 100, 1),
    }

    # Trust agreement: how often user decision matches AI recommendation
    if df["user_agreed_with_ai"].notna().any():
        agreed = df["user_agreed_with_ai"].sum()
        metrics["trust_agreement_rate_pct"] = round(agreed / total * 100, 1)

    # Appropriate reliance: accept when AI is correct
    ai_correct = df[df["ai_is_correct"] == True]
    if len(ai_correct) > 0:
        appropriate = (ai_correct["decision"] == "Accept").sum()
        metrics["appropriate_reliance_pct"] = round(
            appropriate / len(ai_correct) * 100, 1
        )
        # Under-reliance: override when AI is correct
        under_reliance = (ai_correct["decision"] == "Override").sum()
        metrics["under_reliance_pct"] = round(
            under_reliance / len(ai_correct) * 100, 1
        )
        metrics["ai_correct_count"] = len(ai_correct)

    # Over-reliance: accept when AI is wrong
    ai_wrong = df[df["ai_is_correct"] == False]
    if len(ai_wrong) > 0:
        over_reliance = (ai_wrong["decision"] == "Accept").sum()
        metrics["over_reliance_pct"] = round(
            over_reliance / len(ai_wrong) * 100, 1
        )
        # Appropriate override: override when AI is wrong (good!)
        appropriate_override = (ai_wrong["decision"] == "Override").sum()
        metrics["appropriate_override_pct"] = round(
            appropriate_override / len(ai_wrong) * 100, 1
        )
        metrics["ai_wrong_count"] = len(ai_wrong)

    # Trust discrimination: ratio of appropriate reliance to over-reliance
    # Higher = better calibrated. >1 means user can distinguish good from bad AI
    appr = metrics.get("appropriate_reliance_pct", 0)
    over = metrics.get("over_reliance_pct", 0)
    if over > 0:
        metrics["trust_discrimination_ratio"] = round(appr / over, 2)
    elif appr > 0:
        metrics["trust_discrimination_ratio"] = float("inf")
    else:
        metrics["trust_discrimination_ratio"] = 0.0

    # User accuracy: how often user's final decision was correct
    if df["user_was_correct"].notna().any():
        correct = df["user_was_correct"].sum()
        metrics["user_accuracy_pct"] = round(correct / total * 100, 1)

    return metrics


# ─── Latency Analysis ────────────────────────────────────────────────────────

def compute_latency_insights(df: pd.DataFrame) -> dict:
    """Analyze response time patterns for trust-related insights."""
    insights = {}

    # Overall latency
    insights["overall"] = {
        "mean_ms": round(df["latency_ms"].mean(), 1),
        "median_ms": round(df["latency_ms"].median(), 1),
        "std_ms": round(df["latency_ms"].std(), 1),
    }

    # Latency by decision type
    for dec in ["Accept", "Override"]:
        subset = df[df["decision"] == dec]["latency_ms"]
        if len(subset) > 0:
            insights[f"{dec.lower()}_latency"] = {
                "mean_ms": round(subset.mean(), 1),
                "median_ms": round(subset.median(), 1),
                "count": len(subset),
            }

    # Statistical test: Accept vs Override latency
    accept_lat = df[df["decision"] == "Accept"]["latency_ms"].dropna()
    override_lat = df[df["decision"] == "Override"]["latency_ms"].dropna()
    if len(accept_lat) >= 2 and len(override_lat) >= 2:
        t_stat, p_val = stats.ttest_ind(accept_lat, override_lat, equal_var=False)
        insights["accept_vs_override_ttest"] = {
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_val, 4),
            "significant_at_05": p_val < 0.05,
            "interpretation": (
                "Users take significantly different time for Accept vs Override decisions"
                if p_val < 0.05
                else "No significant latency difference between Accept and Override"
            ),
        }

    # Latency when AI is correct vs incorrect
    if df["ai_is_correct"].notna().any():
        correct_lat = df[df["ai_is_correct"] == True]["latency_ms"].dropna()
        wrong_lat = df[df["ai_is_correct"] == False]["latency_ms"].dropna()
        if len(correct_lat) > 0:
            insights["ai_correct_latency"] = {
                "mean_ms": round(correct_lat.mean(), 1),
                "count": len(correct_lat),
            }
        if len(wrong_lat) > 0:
            insights["ai_wrong_latency"] = {
                "mean_ms": round(wrong_lat.mean(), 1),
                "count": len(wrong_lat),
            }
        if len(correct_lat) >= 2 and len(wrong_lat) >= 2:
            t_stat, p_val = stats.ttest_ind(correct_lat, wrong_lat, equal_var=False)
            insights["correct_vs_wrong_ttest"] = {
                "t_statistic": round(t_stat, 3),
                "p_value": round(p_val, 4),
                "significant_at_05": p_val < 0.05,
                "interpretation": (
                    "Users respond significantly differently when AI is correct vs wrong"
                    if p_val < 0.05
                    else "No significant latency difference based on AI correctness"
                ),
            }

    return insights


# ─── Cue Dimension Analysis ─────────────────────────────────────────────────

def _analyze_cue_dimension(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Compute trust metrics grouped by a single cue dimension."""
    if col not in df.columns or df[col].isna().all():
        return pd.DataFrame()

    groups = df.groupby(col)
    rows = []
    for name, group in groups:
        n = len(group)
        accepts = (group["decision"] == "Accept").sum()
        reliance = round(accepts / n * 100, 1) if n > 0 else 0

        row = {
            col: name,
            "n": n,
            "reliance_rate_pct": reliance,
            "mean_latency_ms": round(group["latency_ms"].mean(), 1),
        }

        # Trust agreement
        if group["user_agreed_with_ai"].notna().any():
            agreed = group["user_agreed_with_ai"].sum()
            row["trust_agreement_pct"] = round(agreed / n * 100, 1)

        # Over-reliance
        ai_wrong = group[group["ai_is_correct"] == False]
        if len(ai_wrong) > 0:
            over = (ai_wrong["decision"] == "Accept").sum()
            row["over_reliance_pct"] = round(over / len(ai_wrong) * 100, 1)
        else:
            row["over_reliance_pct"] = np.nan

        # Appropriate reliance
        ai_correct = group[group["ai_is_correct"] == True]
        if len(ai_correct) > 0:
            appr = (ai_correct["decision"] == "Accept").sum()
            row["appropriate_reliance_pct"] = round(appr / len(ai_correct) * 100, 1)
        else:
            row["appropriate_reliance_pct"] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


def analyze_cue_effects(df: pd.DataFrame) -> dict:
    """Analyze trust patterns across all cue dimensions with chi-square tests."""
    results = {}

    cue_cols = {
        "agent_name": "Agent Identity",
        "tone_style": "Tone Style",
        "confidence_framing": "Confidence Framing",
    }

    for col, label in cue_cols.items():
        if col not in df.columns:
            continue

        summary = _analyze_cue_dimension(df, col)
        if summary.empty:
            continue

        entry = {"summary": summary, "label": label}

        # Chi-square test: is decision independent of this cue?
        ct = pd.crosstab(df[col], df["decision"])
        if ct.shape[0] >= 2 and ct.shape[1] >= 2:
            chi2, p, dof, expected = stats.chi2_contingency(ct)
            entry["chi_square"] = {
                "chi2": round(chi2, 3),
                "p_value": round(p, 4),
                "dof": dof,
                "significant_at_05": p < 0.05,
                "interpretation": (
                    f"{label} has a SIGNIFICANT effect on user decisions"
                    if p < 0.05
                    else f"{label} does NOT significantly affect user decisions"
                ),
            }

        results[col] = entry

    return results


# ─── Condition-Level Analysis ────────────────────────────────────────────────

def analyze_by_condition(df: pd.DataFrame) -> pd.DataFrame:
    """Compute full trust metrics for each experimental condition."""
    rows = []
    for cid, group in df.groupby("condition_id"):
        n = len(group)
        accepts = (group["decision"] == "Accept").sum()

        row = {
            "condition_id": cid,
            "n": n,
            "reliance_rate_pct": round(accepts / n * 100, 1) if n > 0 else 0,
            "override_rate_pct": round((n - accepts) / n * 100, 1) if n > 0 else 0,
            "mean_latency_ms": round(group["latency_ms"].mean(), 1),
            "median_latency_ms": round(group["latency_ms"].median(), 1),
        }

        # Trust agreement
        if group["user_agreed_with_ai"].notna().any():
            agreed = group["user_agreed_with_ai"].sum()
            row["trust_agreement_pct"] = round(agreed / n * 100, 1)

        # Appropriate vs over-reliance
        ai_correct = group[group["ai_is_correct"] == True]
        ai_wrong = group[group["ai_is_correct"] == False]

        if len(ai_correct) > 0:
            row["appropriate_reliance_pct"] = round(
                (ai_correct["decision"] == "Accept").sum() / len(ai_correct) * 100, 1
            )
        if len(ai_wrong) > 0:
            row["over_reliance_pct"] = round(
                (ai_wrong["decision"] == "Accept").sum() / len(ai_wrong) * 100, 1
            )

        rows.append(row)

    return pd.DataFrame(rows)


# ─── Per-Participant Profiles ────────────────────────────────────────────────

def analyze_per_participant(df: pd.DataFrame) -> pd.DataFrame:
    """Create individual trust profiles for each participant."""
    rows = []
    for pid, group in df.groupby("participant_id"):
        n = len(group)
        accepts = (group["decision"] == "Accept").sum()

        row = {
            "participant_id": pid,
            "condition_id": group["condition_id"].iloc[0],
            "n_decisions": n,
            "reliance_rate_pct": round(accepts / n * 100, 1) if n > 0 else 0,
            "mean_latency_ms": round(group["latency_ms"].mean(), 1),
        }

        if group["user_agreed_with_ai"].notna().any():
            row["trust_agreement_pct"] = round(
                group["user_agreed_with_ai"].sum() / n * 100, 1
            )

        if group["user_was_correct"].notna().any():
            row["accuracy_pct"] = round(
                group["user_was_correct"].sum() / n * 100, 1
            )

        rows.append(row)

    return pd.DataFrame(rows)


# ─── Report Printer ──────────────────────────────────────────────────────────

def print_report(
    metrics: dict,
    condition_df: pd.DataFrame,
    cue_effects: dict,
    latency_insights: dict,
    participant_df: pd.DataFrame,
):
    """Print a comprehensive, formatted analysis report."""
    w = 72

    print("=" * w)
    print("  HUMAN-AI TRUST EXPERIMENT: ANALYSIS REPORT")
    print("=" * w)

    # ── Overall Trust Metrics
    print(f"\n{'─' * w}")
    print("  OVERALL TRUST METRICS")
    print(f"{'─' * w}")
    print(f"  Total Responses:            {metrics.get('total_responses', 0)}")
    print(f"  Reliance Rate:              {metrics.get('reliance_rate_pct', 0)}%")
    print(f"  Override Rate:              {metrics.get('override_rate_pct', 0)}%")

    if "trust_agreement_rate_pct" in metrics:
        print(f"\n  Trust Agreement Rate:        {metrics['trust_agreement_rate_pct']}%")
        print(f"    (How often user's decision matched AI's recommendation)")

    if "appropriate_reliance_pct" in metrics:
        print(f"\n  Appropriate Reliance:        {metrics['appropriate_reliance_pct']}%")
        print(f"    (Accepted when AI was correct -- {metrics.get('ai_correct_count', '?')} cases)")

    if "under_reliance_pct" in metrics:
        print(f"  Under-reliance:              {metrics['under_reliance_pct']}%")
        print(f"    (Overrode when AI was actually correct -- missed opportunities)")

    if "over_reliance_pct" in metrics:
        print(f"\n  Over-reliance:               {metrics['over_reliance_pct']}%")
        print(f"    (Accepted when AI was WRONG -- {metrics.get('ai_wrong_count', '?')} error cases)")

    if "appropriate_override_pct" in metrics:
        print(f"  Appropriate Override:        {metrics['appropriate_override_pct']}%")
        print(f"    (Correctly overrode wrong AI -- good calibration)")

    if "trust_discrimination_ratio" in metrics:
        tdr = metrics["trust_discrimination_ratio"]
        tdr_str = f"{tdr}" if tdr != float("inf") else "INF (perfect)"
        verdict = (
            "Well-calibrated"
            if tdr > 1.5
            else "Moderately calibrated"
            if tdr > 1.0
            else "Poorly calibrated (over-trusting AI)"
        )
        print(f"\n  Trust Discrimination Ratio:  {tdr_str}")
        print(f"    Verdict: {verdict}")

    if "user_accuracy_pct" in metrics:
        print(f"\n  User Final Accuracy:         {metrics['user_accuracy_pct']}%")
        print(f"    (How often user's final decision was objectively correct)")

    # ── Latency Insights
    print(f"\n{'─' * w}")
    print("  LATENCY ANALYSIS")
    print(f"{'─' * w}")

    ov = latency_insights.get("overall", {})
    print(f"  Overall:  mean={ov.get('mean_ms', '?')}ms  "
          f"median={ov.get('median_ms', '?')}ms  "
          f"std={ov.get('std_ms', '?')}ms")

    for key in ["accept_latency", "override_latency"]:
        val = latency_insights.get(key)
        if val:
            label = key.replace("_latency", "").capitalize()
            print(f"  {label:10s}: mean={val['mean_ms']}ms  "
                  f"median={val['median_ms']}ms  (n={val['count']})")

    for test_key in ["accept_vs_override_ttest", "correct_vs_wrong_ttest"]:
        test = latency_insights.get(test_key)
        if test:
            label = test_key.replace("_ttest", "").replace("_", " ").title()
            sig = "***" if test["significant_at_05"] else "(n.s.)"
            print(f"\n  {label}: t={test['t_statistic']}, p={test['p_value']} {sig}")
            print(f"    {test['interpretation']}")

    if "ai_correct_latency" in latency_insights or "ai_wrong_latency" in latency_insights:
        print(f"\n  Latency by AI Correctness:")
        cl = latency_insights.get("ai_correct_latency", {})
        wl = latency_insights.get("ai_wrong_latency", {})
        if cl:
            print(f"    AI Correct: mean={cl['mean_ms']}ms (n={cl['count']})")
        if wl:
            print(f"    AI Wrong:   mean={wl['mean_ms']}ms (n={wl['count']})")

    # ── By Condition
    print(f"\n{'─' * w}")
    print("  TRUST METRICS BY CONDITION")
    print(f"{'─' * w}\n")

    display_cols = [c for c in [
        "condition_id", "n", "reliance_rate_pct", "trust_agreement_pct",
        "appropriate_reliance_pct", "over_reliance_pct",
        "mean_latency_ms",
    ] if c in condition_df.columns]
    print(condition_df[display_cols].to_string(index=False))

    # ── By Cue Dimension
    for col, entry in cue_effects.items():
        print(f"\n{'─' * w}")
        print(f"  EFFECT OF {entry['label'].upper()}")
        print(f"{'─' * w}\n")

        summary = entry["summary"]
        display_cols = [c for c in [
            col, "n", "reliance_rate_pct", "trust_agreement_pct",
            "appropriate_reliance_pct", "over_reliance_pct",
            "mean_latency_ms",
        ] if c in summary.columns]
        print(summary[display_cols].to_string(index=False))

        chi = entry.get("chi_square")
        if chi:
            sig = "***" if chi["significant_at_05"] else "(n.s.)"
            print(f"\n  Chi-square test: X2={chi['chi2']}, df={chi['dof']}, "
                  f"p={chi['p_value']} {sig}")
            print(f"  {chi['interpretation']}")

    # ── Key Findings Summary
    print(f"\n{'─' * w}")
    print("  KEY FINDINGS")
    print(f"{'─' * w}")

    findings = _generate_key_findings(metrics, cue_effects, latency_insights, condition_df)
    for i, finding in enumerate(findings, 1):
        print(f"\n  {i}. {finding}")

    # ── Per-Participant (compact)
    if len(participant_df) <= 20:
        print(f"\n{'─' * w}")
        print("  PER-PARTICIPANT TRUST PROFILES")
        print(f"{'─' * w}\n")

        display_cols = [c for c in [
            "participant_id", "condition_id", "n_decisions",
            "reliance_rate_pct", "trust_agreement_pct", "accuracy_pct",
            "mean_latency_ms",
        ] if c in participant_df.columns]
        print(participant_df[display_cols].to_string(index=False))

    print(f"\n{'=' * w}")


def _generate_key_findings(
    metrics: dict,
    cue_effects: dict,
    latency_insights: dict,
    condition_df: pd.DataFrame,
) -> list:
    """Auto-generate key findings from the computed metrics."""
    findings = []

    # Finding 1: Overall trust calibration
    tdr = metrics.get("trust_discrimination_ratio", 0)
    appr = metrics.get("appropriate_reliance_pct", 0)
    over = metrics.get("over_reliance_pct", 0)
    if appr and over:
        if tdr > 1.5:
            findings.append(
                f"Users show GOOD trust calibration: they accept AI {appr}% of "
                f"the time when it's correct but only {over}% when it's wrong "
                f"(discrimination ratio: {tdr})."
            )
        elif tdr > 1.0:
            findings.append(
                f"Users show MODERATE trust calibration: appropriate reliance ({appr}%) "
                f"exceeds over-reliance ({over}%), but the gap is small "
                f"(discrimination ratio: {tdr})."
            )
        else:
            findings.append(
                f"WARNING: Users show POOR trust calibration -- over-reliance ({over}%) "
                f"is comparable to or exceeds appropriate reliance ({appr}%). "
                f"Users struggle to detect when AI is wrong."
            )

    # Finding 2: Cue effects
    sig_cues = [
        entry["label"]
        for entry in cue_effects.values()
        if entry.get("chi_square", {}).get("significant_at_05", False)
    ]
    if sig_cues:
        findings.append(
            f"Significant cue effect(s) detected: {', '.join(sig_cues)} "
            f"significantly influence user trust decisions (p < 0.05)."
        )
    else:
        findings.append(
            "No individual cue dimension shows a statistically significant "
            "effect on trust decisions (all p > 0.05). This may be due to "
            "sample size or interaction effects between cues."
        )

    # Finding 3: Latency patterns
    test = latency_insights.get("accept_vs_override_ttest")
    if test and test["significant_at_05"]:
        acc = latency_insights.get("accept_latency", {}).get("mean_ms", 0)
        ovr = latency_insights.get("override_latency", {}).get("mean_ms", 0)
        if ovr > acc:
            findings.append(
                f"Override decisions take significantly longer than Accepts "
                f"({ovr}ms vs {acc}ms, p={test['p_value']}), suggesting "
                f"users deliberate more when disagreeing with AI."
            )
        else:
            findings.append(
                f"Accept decisions take significantly longer than Overrides "
                f"({acc}ms vs {ovr}ms, p={test['p_value']}), suggesting "
                f"users think carefully before following AI advice."
            )

    # Finding 4: Best/worst conditions
    if "trust_agreement_pct" in condition_df.columns:
        best = condition_df.loc[condition_df["trust_agreement_pct"].idxmax()]
        worst = condition_df.loc[condition_df["trust_agreement_pct"].idxmin()]
        if best["trust_agreement_pct"] != worst["trust_agreement_pct"]:
            findings.append(
                f"Highest trust agreement in Condition {int(best['condition_id'])} "
                f"({best['trust_agreement_pct']}%), lowest in Condition "
                f"{int(worst['condition_id'])} ({worst['trust_agreement_pct']}%)."
            )

    # Finding 5: User accuracy
    acc = metrics.get("user_accuracy_pct")
    if acc is not None:
        if acc >= 70:
            findings.append(
                f"Users achieve {acc}% final decision accuracy, suggesting "
                f"the combination of AI advice and human judgment is effective."
            )
        else:
            findings.append(
                f"Users achieve only {acc}% final decision accuracy, which may "
                f"indicate over-reliance on incorrect AI or poor independent judgment."
            )

    return findings


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Human-AI Trust Experiment results"
    )
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "results.csv"),
        help="Path to results.csv (default: ../data/results.csv)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "analysis_summary.csv"),
        help="Output path for summary CSV",
    )
    args = parser.parse_args()

    # Load
    df = load_data(args.csv)

    # Check if we have AI recommendation data
    has_ai_data = (
        "ai_recommendation" in df.columns
        and df["ai_recommendation"].notna().any()
        and not (df["ai_recommendation"] == "Unknown").all()
    )

    if not has_ai_data:
        print("WARNING: ai_recommendation column is missing or all 'Unknown'.")
        print("   Trust calibration metrics will be limited.")
        print("   Make sure the frontend properly logs AI recommendations.\n")

    # Compute all analyses
    metrics = compute_overall_trust_metrics(df)
    latency_insights = compute_latency_insights(df)
    condition_df = analyze_by_condition(df)
    cue_effects = analyze_cue_effects(df)
    participant_df = analyze_per_participant(df)

    # Print full report
    print_report(metrics, condition_df, cue_effects, latency_insights, participant_df)

    # Save condition summary
    condition_df.to_csv(args.output, index=False)
    print(f"\nCondition summary saved to: {args.output}")

    # Save detailed per-participant data
    participant_output = args.output.replace("summary", "participants")
    participant_df.to_csv(participant_output, index=False)
    print(f"Participant profiles saved to: {participant_output}")


if __name__ == "__main__":
    main()
