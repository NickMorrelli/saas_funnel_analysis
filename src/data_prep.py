"""
data_prep.py
------------
Generates realistic synthetic event-level data for a SaaS onboarding
funnel analysis.

What is Funnel Analysis?
------------------------
A funnel is a sequence of steps users must complete to reach a goal.
In SaaS, the onboarding funnel tracks the journey from signup to
becoming a paying customer. At each step, some users drop off — funnel
analysis tells us WHERE they drop off and WHY.

Funnel Stages (our fictional B2B SaaS product)
----------------------------------------------
1. signup              : User creates an account
2. email_verified      : User verifies their email address
3. profile_completed   : User fills out their profile
4. first_feature_used  : User tries the core feature (ACTIVATION)
5. team_invited        : User invites a team member (AHA MOMENT)
6. paid_conversion     : User upgrades to a paid plan (GOAL)

Why these stages?
-----------------
These mirror real SaaS onboarding funnels used by companies like
Slack, Notion, and HubSpot. The "aha moment" (inviting a team member)
is a well-documented predictor of long-term retention in B2B SaaS —
users who collaborate are far less likely to churn.

User Segments
-------------
We simulate three acquisition channels and two plan types:
  - channel : organic, paid_search, referral
  - device  : desktop, mobile, tablet
  - plan    : free_trial, freemium

Realistic Drop-off Rates
------------------------
Based on industry benchmarks for B2B SaaS:
  - Signup → Email Verified  : ~75% (friction from email confirmation)
  - Email → Profile          : ~60% (users skip optional steps)
  - Profile → First Feature  : ~50% (activation is the hardest step)
  - First Feature → Team     : ~35% (collaboration requires effort)
  - Team → Paid              : ~25% (conversion from free to paid)

These rates vary by segment — paid search users convert better,
mobile users drop off faster, referral users have higher activation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ── Constants ─────────────────────────────────────────────────────────────────

RANDOM_SEED  = 42
N_USERS      = 5_000
START_DATE   = datetime(2024, 1, 1)
END_DATE     = datetime(2024, 12, 31)

FUNNEL_STAGES = [
    "signup",
    "email_verified",
    "profile_completed",
    "first_feature_used",
    "team_invited",
    "paid_conversion",
]

# Base conversion rates (probability of completing each step given previous)
BASE_CONVERSION_RATES = {
    "email_verified"    : 0.75,
    "profile_completed" : 0.60,
    "first_feature_used": 0.50,
    "team_invited"      : 0.35,
    "paid_conversion"   : 0.25,
}

# Multipliers by acquisition channel
CHANNEL_MULTIPLIERS = {
    "organic"    : 1.0,
    "paid_search": 1.2,   # Higher intent — converts better
    "referral"   : 1.35,  # Word-of-mouth — highest quality
}

# Multipliers by device
DEVICE_MULTIPLIERS = {
    "desktop": 1.0,
    "mobile" : 0.75,   # Mobile users drop off faster in SaaS
    "tablet" : 0.90,
}

# Multipliers by plan type
PLAN_MULTIPLIERS = {
    "free_trial": 1.15,  # Trial users have more urgency
    "freemium"  : 0.85,  # Freemium users are less committed
}

# Channel distribution (how users are acquired)
CHANNEL_DISTRIBUTION = {"organic": 0.45, "paid_search": 0.35, "referral": 0.20}

# Device distribution
DEVICE_DISTRIBUTION = {"desktop": 0.60, "mobile": 0.30, "tablet": 0.10}

# Plan distribution
PLAN_DISTRIBUTION = {"free_trial": 0.55, "freemium": 0.45}

# Median days between stages (realistic time-to-complete)
STAGE_DELAYS_HOURS = {
    "email_verified"    : (0.5, 2),    # (median hours, std) — usually same day
    "profile_completed" : (2,   12),
    "first_feature_used": (24,  48),   # Activation often next day
    "team_invited"      : (72,  96),   # Takes a few days
    "paid_conversion"   : (168, 120),  # ~1 week after activation
}


# ── Data Generation ───────────────────────────────────────────────────────────

def generate_users(n_users: int = N_USERS) -> pd.DataFrame:
    """
    Generate synthetic user attributes.

    Parameters
    ----------
    n_users : int  Number of users to simulate.

    Returns
    -------
    pd.DataFrame  One row per user with demographic/acquisition attributes.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # Random signup dates spread across the year
    signup_days = rng.integers(0, (END_DATE - START_DATE).days, n_users)
    signup_dates = [START_DATE + timedelta(days=int(d)) for d in signup_days]

    # Sample acquisition attributes
    channels = rng.choice(
        list(CHANNEL_DISTRIBUTION.keys()),
        size=n_users,
        p=list(CHANNEL_DISTRIBUTION.values())
    )
    devices = rng.choice(
        list(DEVICE_DISTRIBUTION.keys()),
        size=n_users,
        p=list(DEVICE_DISTRIBUTION.values())
    )
    plans = rng.choice(
        list(PLAN_DISTRIBUTION.keys()),
        size=n_users,
        p=list(PLAN_DISTRIBUTION.values())
    )

    users = pd.DataFrame({
        "user_id"    : [f"U{str(i+1).zfill(5)}" for i in range(n_users)],
        "signup_date": signup_dates,
        "channel"    : channels,
        "device"     : devices,
        "plan"       : plans,
    })

    return users


def generate_events(users: pd.DataFrame) -> pd.DataFrame:
    """
    Generate event-level data for each user moving through the funnel.

    For each user, we probabilistically determine which stages they complete
    based on their attributes (channel, device, plan). We then assign
    realistic timestamps to each completed stage.

    Parameters
    ----------
    users : pd.DataFrame  Output of generate_users().

    Returns
    -------
    pd.DataFrame  One row per user-event with timestamp and stage.
    """
    rng = np.random.default_rng(RANDOM_SEED + 1)
    events = []

    for _, user in users.iterrows():
        # Compute this user's conversion multiplier
        multiplier = (
            CHANNEL_MULTIPLIERS[user["channel"]]
            * DEVICE_MULTIPLIERS[user["device"]]
            * PLAN_MULTIPLIERS[user["plan"]]
        )

        # Everyone starts at signup
        current_time = user["signup_date"]
        events.append({
            "user_id"   : user["user_id"],
            "stage"     : "signup",
            "timestamp" : current_time,
            "channel"   : user["channel"],
            "device"    : user["device"],
            "plan"      : user["plan"],
        })

        # Walk through subsequent stages
        for stage in FUNNEL_STAGES[1:]:
            base_rate = BASE_CONVERSION_RATES[stage]

            # Apply multiplier but cap at 0.95 to keep it realistic
            conversion_prob = min(base_rate * multiplier, 0.95)

            if rng.random() < conversion_prob:
                # Add realistic time delay
                median_hrs, std_hrs = STAGE_DELAYS_HOURS[stage]
                delay_hours = max(0.1, rng.normal(median_hrs, std_hrs))
                current_time = current_time + timedelta(hours=float(delay_hours))

                events.append({
                    "user_id"  : user["user_id"],
                    "stage"    : stage,
                    "timestamp": current_time,
                    "channel"  : user["channel"],
                    "device"   : user["device"],
                    "plan"     : user["plan"],
                })
            else:
                # User dropped off — stop here
                break

    events_df = pd.DataFrame(events)
    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"])

    return events_df


def build_user_funnel_summary(events_df: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """
    Build a user-level summary showing the furthest stage each user reached
    and the time taken between stages.

    Parameters
    ----------
    events_df : pd.DataFrame  Event-level data from generate_events().
    users     : pd.DataFrame  User attributes from generate_users().

    Returns
    -------
    pd.DataFrame  One row per user with funnel progress and timing.
    """
    # Furthest stage reached per user
    stage_order = {stage: i for i, stage in enumerate(FUNNEL_STAGES)}
    events_df["stage_order"] = events_df["stage"].map(stage_order)

    # Pivot to wide format: one column per stage with timestamp
    pivot = events_df.pivot_table(
        index="user_id", columns="stage", values="timestamp", aggfunc="first"
    ).reset_index()

    # Ensure all stage columns exist
    for stage in FUNNEL_STAGES:
        if stage not in pivot.columns:
            pivot[stage] = pd.NaT

    # Add user attributes
    summary = users.merge(pivot, on="user_id", how="left")

    # Furthest stage reached
    def get_furthest_stage(row):
        for stage in reversed(FUNNEL_STAGES):
            if pd.notna(row.get(stage)):
                return stage
        return "signup"

    summary["furthest_stage"]       = summary.apply(get_furthest_stage, axis=1)
    summary["furthest_stage_order"] = summary["furthest_stage"].map(stage_order)
    summary["converted"]            = (summary["furthest_stage"] == "paid_conversion").astype(int)

    # Time between stages (in hours)
    summary["hours_to_verify"]    = (summary["email_verified"]     - summary["signup"]).dt.total_seconds() / 3600
    summary["hours_to_profile"]   = (summary["profile_completed"]  - summary["email_verified"]).dt.total_seconds() / 3600
    summary["hours_to_activate"]  = (summary["first_feature_used"] - summary["profile_completed"]).dt.total_seconds() / 3600
    summary["hours_to_team"]      = (summary["team_invited"]       - summary["first_feature_used"]).dt.total_seconds() / 3600
    summary["hours_to_paid"]      = (summary["paid_conversion"]    - summary["team_invited"]).dt.total_seconds() / 3600
    summary["hours_to_convert"]   = (summary["paid_conversion"]    - summary["signup"]).dt.total_seconds() / 3600

    return summary


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_prep_pipeline() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Full data preparation pipeline.

    Returns
    -------
    users     : user-level attributes
    events_df : event-level funnel data
    summary   : user-level funnel summary
    """
    print("=" * 55)
    print("  DATA PREPARATION — SaaS Funnel Analysis")
    print("=" * 55)

    print(f"\n  Generating {N_USERS:,} synthetic users...")
    users     = generate_users(N_USERS)
    print(f"  Generating events...")
    events_df = generate_events(users)
    print(f"  Building funnel summary...")
    summary   = build_user_funnel_summary(events_df, users)

    # Save outputs
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    events_df.to_csv(os.path.join(out_dir, "events.csv"), index=False)
    summary.to_csv(os.path.join(out_dir, "user_summary.csv"), index=False)

    print(f"\n  Users generated    : {len(users):,}")
    print(f"  Events generated   : {len(events_df):,}")
    print(f"  Overall conversion : {summary['converted'].mean():.1%}")
    print(f"\n  Channel breakdown:")
    for ch, grp in summary.groupby("channel"):
        print(f"    {ch:<15}: {len(grp):,} users  |  {grp['converted'].mean():.1%} converted")

    return users, events_df, summary


if __name__ == "__main__":
    users, events_df, summary = run_prep_pipeline()
    print("\nSample events:")
    print(events_df.head(10).to_string(index=False))
