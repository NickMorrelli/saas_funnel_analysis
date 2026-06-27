"""
funnel.py
---------
Core funnel analysis: conversion rates, drop-off rates, and statistical
significance testing between funnel stages.

Key Metrics
-----------
1. Stage Conversion Rate  : % of users who completed a given stage
                            out of ALL users who entered the funnel
                            (absolute conversion)

2. Step Conversion Rate   : % of users who completed a stage out of
                            those who completed the PREVIOUS stage
                            (relative conversion — where drop-off happens)

3. Drop-off Rate          : 1 - step conversion rate

4. Statistical Significance: Is the difference in conversion rates
                             between segments statistically significant?
                             We use a two-proportion z-test.

Why both absolute and relative rates?
--------------------------------------
Absolute rates tell you how many users make it to each stage overall.
Relative rates tell you which step is the biggest bottleneck.

Example:
  Signup → Email Verified : 75% relative (25% drop here)
  Signup → Paid           :  5% absolute (only 5% of all signups pay)

Both matter — the relative rate helps you prioritize where to fix
the funnel, the absolute rate shows the overall business impact.
"""

import pandas as pd
import numpy as np
from scipy import stats


# ── Funnel Stage Order ────────────────────────────────────────────────────────

FUNNEL_STAGES = [
    "signup",
    "email_verified",
    "profile_completed",
    "first_feature_used",
    "team_invited",
    "paid_conversion",
]

STAGE_LABELS = {
    "signup"            : "1. Signup",
    "email_verified"    : "2. Email Verified",
    "profile_completed" : "3. Profile Completed",
    "first_feature_used": "4. First Feature Used",
    "team_invited"      : "5. Team Invited",
    "paid_conversion"   : "6. Paid Conversion",
}


# ── Core Funnel Metrics ───────────────────────────────────────────────────────

def calculate_funnel_metrics(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate stage-level funnel metrics for the overall population.

    Parameters
    ----------
    summary : pd.DataFrame  User-level funnel summary from data_prep.

    Returns
    -------
    pd.DataFrame with one row per stage and columns:
        stage, label, users_reached, absolute_rate, step_rate, drop_off_rate,
        users_dropped
    """
    total_users = len(summary)
    rows = []

    prev_users = total_users
    for stage in FUNNEL_STAGES:
        if stage == "signup":
            users_reached = total_users
        else:
            users_reached = summary[stage].notna().sum()

        absolute_rate = users_reached / total_users
        step_rate     = users_reached / prev_users if prev_users > 0 else 0
        drop_off_rate = 1 - step_rate
        users_dropped = prev_users - users_reached

        rows.append({
            "stage"        : stage,
            "label"        : STAGE_LABELS[stage],
            "users_reached": users_reached,
            "users_dropped": users_dropped if stage != "signup" else 0,
            "absolute_rate": absolute_rate,
            "step_rate"    : step_rate,
            "drop_off_rate": drop_off_rate if stage != "signup" else 0,
        })

        prev_users = users_reached

    funnel_df = pd.DataFrame(rows)
    return funnel_df


# ── Segment Funnel Comparison ─────────────────────────────────────────────────

def funnel_by_segment(summary: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """
    Calculate funnel conversion rates broken down by a segment column.

    Parameters
    ----------
    summary     : pd.DataFrame  User-level summary.
    segment_col : str           Column to segment by (e.g. 'channel', 'device').

    Returns
    -------
    pd.DataFrame  Conversion rates per segment per stage.
    """
    segments = summary[segment_col].unique()
    rows = []

    for segment in segments:
        seg_df = summary[summary[segment_col] == segment]
        n_total = len(seg_df)

        for stage in FUNNEL_STAGES:
            if stage == "signup":
                n_reached = n_total
            else:
                n_reached = seg_df[stage].notna().sum()

            rows.append({
                "segment"      : segment,
                "stage"        : stage,
                "label"        : STAGE_LABELS[stage],
                "users_total"  : n_total,
                "users_reached": n_reached,
                "absolute_rate": n_reached / n_total if n_total > 0 else 0,
            })

    return pd.DataFrame(rows)


# ── Statistical Significance Testing ─────────────────────────────────────────

def test_segment_significance(summary: pd.DataFrame, segment_col: str,
                               stage: str = "paid_conversion") -> pd.DataFrame:
    """
    Test whether conversion rate differences between segments are
    statistically significant using a two-proportion z-test.

    Why z-test for proportions?
    ---------------------------
    We're comparing conversion rates (proportions) between two groups.
    The two-proportion z-test checks whether the observed difference
    could have occurred by chance.

    H0: conversion_rate_A = conversion_rate_B (no difference)
    H1: conversion_rate_A ≠ conversion_rate_B (significant difference)

    Parameters
    ----------
    summary     : pd.DataFrame
    segment_col : str           Segmentation column.
    stage       : str           Funnel stage to test (default: paid_conversion).

    Returns
    -------
    pd.DataFrame  Pairwise comparison results with z-stat and p-value.
    """
    segments = sorted(summary[segment_col].unique())
    rows = []

    for i, seg_a in enumerate(segments):
        for seg_b in segments[i+1:]:
            df_a = summary[summary[segment_col] == seg_a]
            df_b = summary[summary[segment_col] == seg_b]

            n_a    = len(df_a)
            n_b    = len(df_b)
            conv_a = df_a[stage].notna().sum() if stage != "signup" else n_a
            conv_b = df_b[stage].notna().sum() if stage != "signup" else n_b

            p_a = conv_a / n_a
            p_b = conv_b / n_b

            # Pooled proportion under H0
            p_pool = (conv_a + conv_b) / (n_a + n_b)
            se     = np.sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
            z_stat = (p_a - p_b) / (se + 1e-9)
            p_val  = 2 * (1 - stats.norm.cdf(abs(z_stat)))

            rows.append({
                "segment_a"   : seg_a,
                "segment_b"   : seg_b,
                "rate_a"      : p_a,
                "rate_b"      : p_b,
                "difference"  : p_a - p_b,
                "z_statistic" : z_stat,
                "p_value"     : p_val,
                "significant" : p_val < 0.05,
            })

    return pd.DataFrame(rows)


# ── Print Funnel Report ───────────────────────────────────────────────────────

def print_funnel_report(funnel_df: pd.DataFrame):
    """Print a formatted funnel conversion report."""
    print("\n" + "=" * 65)
    print("  FUNNEL ANALYSIS REPORT")
    print("=" * 65)
    print(f"\n  {'Stage':<28} {'Users':>8} {'Abs Rate':>10} {'Step Rate':>10} {'Drop-off':>10}")
    print("  " + "-" * 68)

    for _, row in funnel_df.iterrows():
        bar_len = int(row["absolute_rate"] * 30)
        bar     = "█" * bar_len + "░" * (30 - bar_len)
        drop_str = f"{row['drop_off_rate']:.1%}" if row["stage"] != "signup" else "  —"
        step_str = f"{row['step_rate']:.1%}"     if row["stage"] != "signup" else "100%"
        print(f"  {row['label']:<28} {row['users_reached']:>8,} "
              f"{row['absolute_rate']:>9.1%} {step_str:>10} {drop_str:>10}")
        print(f"  {bar}")
        if row["stage"] != "signup" and row["users_dropped"] > 0:
            print(f"  ↳ {row['users_dropped']:,} users dropped off here")

    print()


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_funnel_pipeline(summary: pd.DataFrame) -> tuple:
    """
    Full funnel analysis pipeline.

    Returns
    -------
    funnel_df       : overall funnel metrics
    channel_funnel  : funnel by acquisition channel
    device_funnel   : funnel by device
    plan_funnel     : funnel by plan type
    sig_channel     : significance tests by channel
    sig_plan        : significance tests by plan
    """
    print("\n" + "=" * 55)
    print("  FUNNEL ANALYSIS")
    print("=" * 55)

    funnel_df      = calculate_funnel_metrics(summary)
    channel_funnel = funnel_by_segment(summary, "channel")
    device_funnel  = funnel_by_segment(summary, "device")
    plan_funnel    = funnel_by_segment(summary, "plan")
    sig_channel    = test_segment_significance(summary, "channel")
    sig_plan       = test_segment_significance(summary, "plan")

    print_funnel_report(funnel_df)

    print("  Channel Significance Tests (Paid Conversion):")
    for _, row in sig_channel.iterrows():
        sig = "✅ Significant" if row["significant"] else "❌ Not significant"
        print(f"    {row['segment_a']} vs {row['segment_b']}: "
              f"{row['rate_a']:.1%} vs {row['rate_b']:.1%}  "
              f"p={row['p_value']:.4f}  {sig}")

    return funnel_df, channel_funnel, device_funnel, plan_funnel, sig_channel, sig_plan
