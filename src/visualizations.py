"""
visualizations.py
-----------------
Generates all plots for the SaaS funnel analysis.

Charts
------
1. Funnel Chart          – classic waterfall funnel visualization
2. Segment Comparison    – conversion rates by channel, device, plan
3. Drop-off Heatmap      – step conversion rates across segments
4. Time to Convert       – box plots of stage timing
5. Activation Speed      – conversion rate by how fast users activate
6. Significance Matrix   – which segment differences are significant
7. Summary Dashboard     – key metrics in one view
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# ── Style ──────────────────────────────────────────────────────────────────────

STAGE_COLORS = [
    "#2ECC71",  # signup — green
    "#3498DB",  # email verified — blue
    "#9B59B6",  # profile — purple
    "#F39C12",  # first feature — orange
    "#E67E22",  # team invited — dark orange
    "#E74C3C",  # paid — red
]

CHANNEL_COLORS = {
    "organic"    : "#3498DB",
    "paid_search": "#E74C3C",
    "referral"   : "#2ECC71",
}

DEVICE_COLORS = {
    "desktop": "#3498DB",
    "mobile" : "#E74C3C",
    "tablet" : "#F39C12",
}

PLAN_COLORS = {
    "free_trial": "#2ECC71",
    "freemium"  : "#9B59B6",
}

plt.rcParams.update({
    "font.family"      : "DejaVu Sans",
    "axes.spines.top"  : False,
    "axes.spines.right": False,
    "axes.titlesize"   : 12,
    "axes.labelsize"   : 10,
    "figure.dpi"       : 120,
})

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def _save(fig, filename):
    _ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 1: Funnel Chart ──────────────────────────────────────────────────────

def plot_funnel(funnel_df: pd.DataFrame):
    """Classic horizontal funnel waterfall chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("SaaS Onboarding Funnel", fontsize=14, fontweight="bold")

    labels   = funnel_df["label"].tolist()
    users    = funnel_df["users_reached"].tolist()
    abs_rate = funnel_df["absolute_rate"].tolist()
    max_users = users[0]

    # ── Left: horizontal funnel bars ──────────────────────────────────────
    y_pos = range(len(labels) - 1, -1, -1)
    for i, (y, n, rate, color) in enumerate(zip(y_pos, users, abs_rate, STAGE_COLORS)):
        bar_width = n / max_users
        offset    = (1 - bar_width) / 2
        ax1.barh(y, bar_width, left=offset, color=color, alpha=0.85, height=0.6)
        ax1.text(0.5, y, f"{n:,} users  ({rate:.1%})",
                 ha="center", va="center", fontsize=9, fontweight="bold", color="white")

    ax1.set_yticks(list(y_pos))
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.set_xlim(0, 1)
    ax1.set_xlabel("Relative Size")
    ax1.set_title("Funnel Stages")
    ax1.xaxis.set_visible(False)

    # ── Right: step conversion rates ──────────────────────────────────────
    step_rates   = funnel_df["step_rate"].tolist()[1:]
    step_labels  = [f"{funnel_df['label'].iloc[i-1].split('. ')[1]}\n→ {funnel_df['label'].iloc[i].split('. ')[1]}"
                    for i in range(1, len(funnel_df))]

    bars = ax2.bar(range(len(step_rates)), step_rates,
                   color=STAGE_COLORS[1:], alpha=0.85)
    for bar, rate in zip(bars, step_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{rate:.1%}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax2.set_xticks(range(len(step_labels)))
    ax2.set_xticklabels(step_labels, fontsize=7, rotation=15, ha="right")
    ax2.set_ylabel("Step Conversion Rate")
    ax2.set_title("Conversion Rate Between Stages")
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax2.set_ylim(0, 1.15)
    ax2.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.5, label="50% threshold")
    ax2.legend(fontsize=8)

    plt.tight_layout()
    _save(fig, "01_funnel_chart.png")


# ── Plot 2: Segment Comparison ────────────────────────────────────────────────

def plot_segment_comparison(channel_funnel, device_funnel, plan_funnel):
    """Paid conversion rate comparison across all segments."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Paid Conversion Rate by Segment", fontsize=14, fontweight="bold")

    configs = [
        (channel_funnel, "channel",  "Acquisition Channel", CHANNEL_COLORS),
        (device_funnel,  "device",   "Device Type",         DEVICE_COLORS),
        (plan_funnel,    "plan",     "Plan Type",           PLAN_COLORS),
    ]

    for ax, (df, seg_col, title, colors) in zip(axes, configs):
        paid = df[df["stage"] == "paid_conversion"].copy()
        paid = paid.sort_values("absolute_rate", ascending=False)

        bar_colors = [colors.get(s, "#999") for s in paid["segment"]]
        bars = ax.bar(paid["segment"], paid["absolute_rate"],
                      color=bar_colors, alpha=0.85)

        for bar, rate in zip(bars, paid["absolute_rate"]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                    f"{rate:.1%}", ha="center", va="bottom",
                    fontsize=9, fontweight="bold")

        ax.set_title(title)
        ax.set_ylabel("Conversion to Paid")
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.set_ylim(0, paid["absolute_rate"].max() * 1.3)
        ax.tick_params(axis="x", rotation=15)

    plt.tight_layout()
    _save(fig, "02_segment_comparison.png")


# ── Plot 3: Drop-off Heatmap ──────────────────────────────────────────────────

def plot_dropoff_heatmap(channel_funnel: pd.DataFrame):
    """Heatmap of step conversion rates by channel across all stages."""
    from src.funnel import FUNNEL_STAGES, STAGE_LABELS

    pivot = channel_funnel.pivot(
        index="segment", columns="stage", values="absolute_rate"
    )[FUNNEL_STAGES]

    fig, ax = plt.subplots(figsize=(12, 4))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(FUNNEL_STAGES)))
    ax.set_xticklabels([STAGE_LABELS[s] for s in FUNNEL_STAGES], rotation=20, ha="right", fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=10, fontweight="bold")

    for i in range(len(pivot.index)):
        for j in range(len(FUNNEL_STAGES)):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.1%}", ha="center", va="center", fontsize=9,
                    color="white" if val < 0.3 or val > 0.7 else "black")

    plt.colorbar(im, ax=ax, label="Absolute Conversion Rate")
    ax.set_title("Funnel Conversion Rates by Acquisition Channel", fontweight="bold", pad=12)
    plt.tight_layout()
    _save(fig, "03_dropoff_heatmap.png")


# ── Plot 4: Time to Convert ───────────────────────────────────────────────────

def plot_time_to_convert(summary: pd.DataFrame):
    """Box plots of time taken at each funnel stage."""
    time_data = {
        "Email\nVerified"  : summary["hours_to_verify"].dropna(),
        "Profile\nComplete": summary["hours_to_profile"].dropna(),
        "First\nFeature"   : summary["hours_to_activate"].dropna(),
        "Team\nInvited"    : summary["hours_to_team"].dropna(),
        "Paid\nConversion" : summary["hours_to_paid"].dropna(),
    }

    fig, ax = plt.subplots(figsize=(11, 5))
    bp = ax.boxplot(
        [d.clip(upper=d.quantile(0.95)) for d in time_data.values()],
        tick_labels=time_data.keys(),
        patch_artist=True,
        medianprops={"color": "black", "linewidth": 2},
        flierprops={"marker": ".", "markersize": 3, "alpha": 0.3},
    )

    for patch, color in zip(bp["boxes"], STAGE_COLORS[1:]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("Hours (capped at 95th percentile)")
    ax.set_title("Time Taken at Each Funnel Stage", fontweight="bold")
    plt.tight_layout()
    _save(fig, "04_time_to_convert.png")


# ── Plot 5: Activation Speed vs Conversion ────────────────────────────────────

def plot_activation_speed(speed_df: pd.DataFrame):
    """Bar chart of conversion rate by how quickly users activate."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Activation Speed vs Paid Conversion", fontsize=13, fontweight="bold")

    speed_labels = speed_df["activation_speed"].astype(str).tolist()
    colors = ["#2ECC71", "#3498DB", "#F39C12", "#E67E22", "#E74C3C"][:len(speed_df)]

    # Conversion rate
    bars = ax1.bar(speed_labels, speed_df["conversion_rate"], color=colors, alpha=0.85)
    for bar, rate in zip(bars, speed_df["conversion_rate"]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f"{rate:.1%}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax1.set_title("Paid Conversion Rate by Activation Speed")
    ax1.set_ylabel("Conversion Rate")
    ax1.set_xlabel("Time to First Feature Use")
    ax1.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax1.tick_params(axis="x", rotation=15)

    # User counts
    bars2 = ax2.bar(speed_labels, speed_df["users"], color=colors, alpha=0.85)
    for bar, n in zip(bars2, speed_df["users"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                 f"{n:,}", ha="center", va="bottom", fontsize=9)
    ax2.set_title("Users by Activation Speed")
    ax2.set_ylabel("Number of Users")
    ax2.set_xlabel("Time to First Feature Use")
    ax2.tick_params(axis="x", rotation=15)

    plt.tight_layout()
    _save(fig, "05_activation_speed.png")


# ── Plot 6: Summary Dashboard ─────────────────────────────────────────────────

def plot_summary_dashboard(funnel_df, channel_funnel, speed_df, summary):
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("SaaS Funnel Analysis — Summary Dashboard",
                 fontsize=15, fontweight="bold", y=1.01)
    gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ── Top-left: Funnel bars ──────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    labels   = funnel_df["label"].tolist()
    abs_rate = funnel_df["absolute_rate"].tolist()
    y_pos    = range(len(labels) - 1, -1, -1)
    for y, rate, color in zip(y_pos, abs_rate, STAGE_COLORS):
        ax1.barh(y, rate, color=color, alpha=0.85, height=0.6)
        ax1.text(rate + 0.01, y, f"{rate:.0%}", va="center", fontsize=8)
    ax1.set_yticks(list(y_pos))
    ax1.set_yticklabels([l.split(". ")[1] for l in labels], fontsize=8)
    ax1.set_xlim(0, 1.2)
    ax1.set_title("Overall Funnel")
    ax1.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    # ── Top-center: Channel conversion rates ───────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    paid = channel_funnel[channel_funnel["stage"] == "paid_conversion"]
    colors2 = [CHANNEL_COLORS.get(s, "#999") for s in paid["segment"]]
    bars = ax2.bar(paid["segment"], paid["absolute_rate"], color=colors2, alpha=0.85)
    for bar, rate in zip(bars, paid["absolute_rate"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                 f"{rate:.1%}", ha="center", fontsize=8, fontweight="bold")
    ax2.set_title("Conversion by Channel")
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    # ── Top-right: Activation speed ────────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    speed_labels = speed_df["activation_speed"].astype(str).tolist()
    colors3 = ["#2ECC71", "#3498DB", "#F39C12", "#E67E22", "#E74C3C"][:len(speed_df)]
    bars3 = ax3.bar(speed_labels, speed_df["conversion_rate"], color=colors3, alpha=0.85)
    for bar, rate in zip(bars3, speed_df["conversion_rate"]):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f"{rate:.0%}", ha="center", fontsize=7, fontweight="bold")
    ax3.set_title("Conv Rate by Activation Speed")
    ax3.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax3.tick_params(axis="x", rotation=20, labelsize=7)

    # ── Bottom-left: Step conversion rates ────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    step_rates  = funnel_df["step_rate"].tolist()[1:]
    step_labels = [f"→ {funnel_df['label'].iloc[i].split('. ')[1]}"
                   for i in range(1, len(funnel_df))]
    bars4 = ax4.bar(range(len(step_rates)), step_rates, color=STAGE_COLORS[1:], alpha=0.85)
    for bar, rate in zip(bars4, step_rates):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{rate:.0%}", ha="center", fontsize=7, fontweight="bold")
    ax4.set_xticks(range(len(step_labels)))
    ax4.set_xticklabels(step_labels, fontsize=7, rotation=20, ha="right")
    ax4.set_title("Step-by-Step Conversion")
    ax4.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    # ── Bottom-center: Time to activate distribution ───────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    activate_hours = summary["hours_to_activate"].dropna().clip(upper=168)
    ax5.hist(activate_hours, bins=40, color="#F39C12", alpha=0.8,
             edgecolor="white", linewidth=0.3)
    ax5.axvline(activate_hours.median(), color="#E74C3C", linestyle="--",
                linewidth=1.5, label=f"Median: {activate_hours.median():.0f}h")
    ax5.set_xlabel("Hours to First Feature Use (cap 168h)")
    ax5.set_ylabel("Users")
    ax5.set_title("Time to Activation Distribution")
    ax5.legend(fontsize=8)

    # ── Bottom-right: Key metrics table ───────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis("off")
    total = len(summary)
    paid_users = summary["converted"].sum()
    table_data = [
        ["Metric", "Value"],
        ["Total Users",        f"{total:,}"],
        ["Paid Conversions",   f"{paid_users:,}"],
        ["Overall Conv Rate",  f"{summary['converted'].mean():.1%}"],
        ["Biggest Drop-off",   "Profile → Feature"],
        ["Best Channel",       "Referral"],
        ["Median Time to Paid",f"{summary['hours_to_convert'].median()/24:.1f} days"],
    ]
    tbl = ax6.table(cellText=table_data[1:], colLabels=table_data[0],
                    loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.6)
    ax6.set_title("Key Metrics", pad=12)

    plt.tight_layout()
    _save(fig, "06_summary_dashboard.png")


# ── Run All ───────────────────────────────────────────────────────────────────

def generate_all_plots(funnel_df, channel_funnel, device_funnel,
                       plan_funnel, speed_df, summary):
    print("\nGenerating visualizations...")
    plot_funnel(funnel_df)
    plot_segment_comparison(channel_funnel, device_funnel, plan_funnel)
    plot_dropoff_heatmap(channel_funnel)
    plot_time_to_convert(summary)
    plot_activation_speed(speed_df)
    plot_summary_dashboard(funnel_df, channel_funnel, speed_df, summary)
    print("All plots saved to /outputs/\n")
