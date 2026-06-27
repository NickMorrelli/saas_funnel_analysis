"""
time_to_convert.py
------------------
Analyzes how long users take to move through each funnel stage.

Why does time matter?
---------------------
Speed through the funnel is a strong predictor of conversion:
  - Users who verify their email within 1 hour convert at 3x the rate
    of users who take more than 24 hours
  - Users who activate (use core feature) within the first session
    are far more likely to become paying customers

This analysis identifies:
  1. Median time between each funnel stage
  2. How time-to-activate correlates with paid conversion
  3. Optimal intervention windows (when to send nudge emails)

Key Metric: Time to Activation
-------------------------------
'Activation' is the moment a user first gets value from the product.
In our funnel, this is 'first_feature_used'. Research by companies
like Intercom and HubSpot shows that users who activate within 24 hours
of signup have 2-3x higher paid conversion rates.
"""

import pandas as pd
import numpy as np
from scipy import stats


# ── Time Bucket Analysis ──────────────────────────────────────────────────────

def analyze_time_to_stage(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate time-to-complete statistics for each funnel transition.

    Parameters
    ----------
    summary : pd.DataFrame  User-level summary with hours_to_* columns.

    Returns
    -------
    pd.DataFrame  Summary statistics per stage transition.
    """
    time_cols = {
        "Signup → Email Verified"     : "hours_to_verify",
        "Email → Profile Completed"   : "hours_to_profile",
        "Profile → First Feature Used": "hours_to_activate",
        "First Feature → Team Invited": "hours_to_team",
        "Team Invited → Paid"         : "hours_to_paid",
        "Signup → Paid (Total)"       : "hours_to_convert",
    }

    rows = []
    for label, col in time_cols.items():
        data = summary[col].dropna()
        if len(data) == 0:
            continue
        rows.append({
            "transition" : label,
            "n_users"    : len(data),
            "median_hrs" : data.median(),
            "mean_hrs"   : data.mean(),
            "p25_hrs"    : data.quantile(0.25),
            "p75_hrs"    : data.quantile(0.75),
            "median_days": data.median() / 24,
        })

    return pd.DataFrame(rows)


# ── Activation Speed vs Conversion ───────────────────────────────────────────

def analyze_activation_speed(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze how quickly users activate (use first feature) and whether
    speed correlates with paid conversion.

    Buckets users into activation speed groups:
      - < 1 hour    : Same session activation
      - 1–24 hours  : Same day activation
      - 1–3 days    : Short delay
      - 3–7 days    : Week delay
      - 7+ days     : Slow activation

    Parameters
    ----------
    summary : pd.DataFrame

    Returns
    -------
    pd.DataFrame  Conversion rate by activation speed bucket.
    """
    activated = summary[summary["hours_to_activate"].notna()].copy()

    # Bin by time to activate
    bins   = [0, 1, 24, 72, 168, float("inf")]
    labels = ["< 1 hour", "1–24 hours", "1–3 days", "3–7 days", "7+ days"]
    activated["activation_speed"] = pd.cut(
        activated["hours_to_activate"], bins=bins, labels=labels
    )

    speed_df = (
        activated.groupby("activation_speed", observed=True)
        .agg(
            users          = ("user_id",    "count"),
            converted      = ("converted",  "sum"),
            conversion_rate= ("converted",  "mean"),
        )
        .reset_index()
    )

    return speed_df


# ── Intervention Windows ──────────────────────────────────────────────────────

def identify_intervention_windows(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Identify the optimal timing for nudge interventions at each stage.

    For each stage, we find the time window where users who eventually
    complete the stage do so — this tells us when to send reminder emails
    or in-app nudges.

    Parameters
    ----------
    summary : pd.DataFrame

    Returns
    -------
    pd.DataFrame  Recommended intervention windows per stage.
    """
    interventions = []

    stage_cols = {
        "Email Verification": "hours_to_verify",
        "Profile Completion": "hours_to_profile",
        "First Feature Use" : "hours_to_activate",
        "Team Invitation"   : "hours_to_team",
        "Paid Conversion"   : "hours_to_paid",
    }

    for stage_name, col in stage_cols.items():
        data = summary[col].dropna()
        if len(data) == 0:
            continue

        p25 = data.quantile(0.25)
        p50 = data.median()
        p75 = data.quantile(0.75)

        # Nudge before the median — catch users before they drop off
        nudge_time = p25

        interventions.append({
            "stage"            : stage_name,
            "median_hours"     : p50,
            "p25_hours"        : p25,
            "p75_hours"        : p75,
            "recommended_nudge": nudge_time,
            "nudge_timing"     : f"{nudge_time:.0f} hours after previous stage",
        })

    return pd.DataFrame(interventions)


# ── Print Report ──────────────────────────────────────────────────────────────

def print_time_report(time_df: pd.DataFrame, speed_df: pd.DataFrame):
    print("\n" + "=" * 65)
    print("  TIME-TO-CONVERT ANALYSIS")
    print("=" * 65)

    print(f"\n  {'Transition':<35} {'Median':>10} {'Mean':>10} {'P25–P75':>15}")
    print("  " + "-" * 72)
    for _, row in time_df.iterrows():
        p25_d = row["p25_hrs"] / 24
        p75_d = row["p75_hrs"] / 24
        print(f"  {row['transition']:<35} "
              f"{row['median_hrs']:>8.1f}h "
              f"{row['mean_hrs']:>8.1f}h  "
              f"{p25_d:.1f}–{p75_d:.1f} days")

    print(f"\n  Activation Speed vs Paid Conversion:")
    print(f"  {'Speed Bucket':<15} {'Users':>8} {'Converted':>10} {'Conv Rate':>10}")
    print("  " + "-" * 48)
    for _, row in speed_df.iterrows():
        print(f"  {str(row['activation_speed']):<15} {int(row['users']):>8,} "
              f"{int(row['converted']):>10,} {row['conversion_rate']:>9.1%}")
    print()


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_time_pipeline(summary: pd.DataFrame) -> tuple:
    """
    Full time-to-convert analysis pipeline.

    Returns
    -------
    time_df        : stage transition timing statistics
    speed_df       : activation speed vs conversion
    intervention_df: recommended nudge timing windows
    """
    print("\n" + "=" * 55)
    print("  TIME-TO-CONVERT ANALYSIS")
    print("=" * 55)

    time_df         = analyze_time_to_stage(summary)
    speed_df        = analyze_activation_speed(summary)
    intervention_df = identify_intervention_windows(summary)

    print_time_report(time_df, speed_df)

    return time_df, speed_df, intervention_df
