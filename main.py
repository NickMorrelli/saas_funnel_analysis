"""
main.py
-------
End-to-end pipeline for the SaaS Onboarding Funnel Analysis.

Usage
-----
    python main.py          (run from the saas_funnel_analysis/ folder)

Steps
-----
1. Generate 5,000 synthetic SaaS user events across 6 funnel stages.
2. Calculate overall funnel conversion and drop-off rates.
3. Segment funnel by acquisition channel, device, and plan type.
4. Analyze time-to-convert and activation speed.
5. Run significance tests between segments.
6. Generate all visualizations and save to /outputs/.
"""

import os
import sys

from src.data_prep       import run_prep_pipeline
from src.funnel          import run_funnel_pipeline
from src.time_to_convert import run_time_pipeline
from src.visualizations  import generate_all_plots

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "outputs")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "funnel_executive_summary.txt")


# ── Pipeline ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  SAAS ONBOARDING FUNNEL ANALYSIS")
    print("  Signup → Email → Profile → Activation → Team → Paid")
    print("=" * 65)

    # ── Step 1: Data Generation ────────────────────────────────────────────
    print("\n[1/4] Generating Data")
    users, events_df, summary = run_prep_pipeline()

    # ── Step 2: Funnel Analysis ────────────────────────────────────────────
    print("\n[2/4] Funnel Analysis")
    funnel_df, channel_funnel, device_funnel, plan_funnel, sig_channel, sig_plan = (
        run_funnel_pipeline(summary)
    )

    # ── Step 3: Time Analysis ──────────────────────────────────────────────
    print("\n[3/4] Time-to-Convert Analysis")
    time_df, speed_df, intervention_df = run_time_pipeline(summary)

    # ── Step 4: Visualizations ─────────────────────────────────────────────
    print("\n[4/4] Generating Visualizations")
    generate_all_plots(
        funnel_df, channel_funnel, device_funnel,
        plan_funnel, speed_df, summary
    )

    # ── Executive Summary ──────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary_text = build_executive_summary(
        summary, funnel_df, channel_funnel, speed_df, sig_channel
    )
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"  Executive summary saved to: {SUMMARY_PATH}")

    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print(f"  Outputs saved to: {OUTPUT_DIR}")
    print("=" * 65)


# ── Executive Summary Builder ─────────────────────────────────────────────────

def build_executive_summary(summary, funnel_df, channel_funnel,
                             speed_df, sig_channel) -> str:
    total = len(summary)
    paid  = summary["converted"].sum()

    lines = []
    lines.append("=" * 70)
    lines.append("  SAAS ONBOARDING FUNNEL — EXECUTIVE SUMMARY")
    lines.append("=" * 70)
    lines.append(f"\n  Total Users Analyzed  : {total:,}")
    lines.append(f"  Paid Conversions      : {paid:,} ({paid/total:.1%})")
    lines.append(f"  Median Time to Paid   : {summary['hours_to_convert'].median()/24:.1f} days")
    lines.append("\n" + "-" * 70)
    lines.append("\n  FUNNEL OVERVIEW")
    lines.append("-" * 70)

    for _, row in funnel_df.iterrows():
        if row["stage"] == "signup":
            lines.append(f"\n  {row['label']:<28}: {row['users_reached']:,} users (100%)")
        else:
            lines.append(f"\n  {row['label']:<28}: {row['users_reached']:,} users "
                         f"({row['absolute_rate']:.1%} overall | "
                         f"{row['step_rate']:.1%} from previous step)")
            if row["drop_off_rate"] > 0.5:
                lines.append(f"  ⚠️  HIGH DROP-OFF: {row['drop_off_rate']:.1%} of users lost here")

    lines.append("\n\n" + "-" * 70)
    lines.append("  KEY FINDINGS & RECOMMENDATIONS")
    lines.append("-" * 70)

    # Find biggest drop-off
    non_signup = funnel_df[funnel_df["stage"] != "signup"]
    worst_step = non_signup.loc[non_signup["drop_off_rate"].idxmax()]
    lines.append(f"\n  1. BIGGEST BOTTLENECK: {worst_step['label']}")
    lines.append(f"     {worst_step['drop_off_rate']:.1%} of users drop off at this step.")
    lines.append(f"     Recommendation: Add in-app guidance and reduce friction here.")

    # Channel insights
    paid_by_channel = channel_funnel[channel_funnel["stage"] == "paid_conversion"].sort_values(
        "absolute_rate", ascending=False
    )
    best_ch  = paid_by_channel.iloc[0]
    worst_ch = paid_by_channel.iloc[-1]
    lines.append(f"\n  2. BEST ACQUISITION CHANNEL: {best_ch['segment'].upper()}")
    lines.append(f"     Converts at {best_ch['absolute_rate']:.1%} vs "
                 f"{worst_ch['absolute_rate']:.1%} for {worst_ch['segment']}.")
    lines.append(f"     Recommendation: Increase budget allocation to {best_ch['segment']}.")

    # Activation speed insight
    fastest = speed_df.iloc[0]
    slowest = speed_df.iloc[-1]
    lines.append(f"\n  3. ACTIVATION SPEED MATTERS:")
    lines.append(f"     Users activating in {fastest['activation_speed']} convert at "
                 f"{fastest['conversion_rate']:.1%}")
    lines.append(f"     vs {slowest['conversion_rate']:.1%} for {slowest['activation_speed']} users.")
    lines.append(f"     Recommendation: Send activation nudge emails within 1 hour of signup.")

    lines.append("\n" + "=" * 70 + "\n")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
