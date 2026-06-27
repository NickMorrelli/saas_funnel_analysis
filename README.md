# 🔬 SaaS Onboarding Funnel Analysis

An end-to-end product analytics pipeline analyzing a **B2B SaaS onboarding funnel** — from signup through to paid conversion. The analysis measures drop-off rates at each stage, compares performance across user segments, and identifies the optimal timing for re-engagement interventions.

---

## 🎯 Business Questions

> - *Where are users dropping off in the onboarding funnel?*
> - *Which acquisition channels produce the highest-quality users?*
> - *How does activation speed affect paid conversion?*
> - *When should we send nudge emails to maximize conversion?*

---

## 📁 Project Structure

```
saas_funnel_analysis/
├── outputs/                     # Charts + event data + executive summary
├── src/
│   ├── data_prep.py             # Synthetic event generation (5,000 users)
│   ├── funnel.py                # Conversion rates, drop-off analysis, significance tests
│   ├── time_to_convert.py       # Stage timing analysis + intervention windows
│   └── visualizations.py       # All charts and summary dashboard
├── main.py                      # Run the full pipeline
├── requirements.txt
└── README.md
```

---

## 🧪 Funnel Design

### Stages

| # | Stage | Description |
|---|---|---|
| 1 | **Signup** | User creates an account |
| 2 | **Email Verified** | User confirms their email |
| 3 | **Profile Completed** | User fills out their profile |
| 4 | **First Feature Used** | User tries the core feature **(Activation)** |
| 5 | **Team Invited** | User invites a colleague **(Aha Moment)** |
| 6 | **Paid Conversion** | User upgrades to a paid plan **(Goal)** |

### User Segments

| Dimension | Values |
|---|---|
| Acquisition Channel | Organic, Paid Search, Referral |
| Device | Desktop, Mobile, Tablet |
| Plan Type | Free Trial, Freemium |

### Industry Benchmark Conversion Rates

| Step | Benchmark Rate | Source |
|---|---|---|
| Signup → Email Verified | ~75% | Email friction |
| Email → Profile | ~60% | Optional step skipping |
| Profile → Activation | ~50% | Hardest step in SaaS |
| Activation → Team | ~35% | Requires collaboration |
| Team → Paid | ~25% | Free-to-paid conversion |

---

## 📐 Methodology

### Funnel Metrics
- **Absolute conversion rate**: % of all signups who reach a stage
- **Step conversion rate**: % who complete a stage out of those who completed the previous stage
- **Drop-off rate**: 1 − step conversion rate

### Segment Analysis
Funnel metrics broken down by channel, device, and plan type to identify which user segments convert best.

### Statistical Significance
Two-proportion z-test to determine whether conversion rate differences between segments are statistically significant (α = 0.05).

### Time-to-Convert Analysis
- Median hours between each funnel stage
- Activation speed buckets (< 1 hour, 1–24 hours, 1–3 days, etc.)
- Correlation between activation speed and paid conversion rate
- Recommended intervention timing windows

---

## 📈 Output Files

| File | Description |
|---|---|
| `01_funnel_chart.png` | Waterfall funnel + step conversion rates |
| `02_segment_comparison.png` | Paid conversion by channel, device, plan |
| `03_dropoff_heatmap.png` | Conversion rates across channels and stages |
| `04_time_to_convert.png` | Box plots of time at each stage |
| `05_activation_speed.png` | Conversion rate by activation speed |
| `06_summary_dashboard.png` | Full summary dashboard |
| `events.csv` | Raw event-level data |
| `user_summary.csv` | User-level funnel summary |
| `funnel_executive_summary.txt` | Business recommendations |

---

## 🚀 Getting Started

```bash
git clone https://github.com/yourusername/saas_funnel_analysis.git
cd saas_funnel_analysis
pip install -r requirements.txt
python main.py
```

No data download required — data is generated synthetically with realistic SaaS industry benchmarks.

---

## 🛠 Tech Stack

- **Python 3.14+**
- `pandas` — event data processing
- `numpy` — simulation and numerical computing
- `scipy` — statistical significance testing
- `matplotlib` — all visualizations

---

## 💡 Key Concepts Demonstrated

- Event-level funnel data modeling
- Absolute vs relative conversion rate analysis
- Multi-dimensional segment comparison
- Two-proportion z-test for significance testing
- Time-to-activate analysis and intervention design
- Product analytics executive reporting

---

## 👤 Author

Built as part of a data science / product analytics portfolio project.  
Background: 15+ years in Marketing Analytics | SQL | Python | Statistical Modeling
