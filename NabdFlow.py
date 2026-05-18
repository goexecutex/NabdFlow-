"""
NabdFlow v2.0 – AI-Powered Water Intelligence
University Campus Facility Management Dashboard
2026 Edition

New in v2:
  • Sustainability Score (0–100 with A+–F grade) — headline campus metric
  • CO₂ equivalent calculations (UAE desalination context)
  • 7-day demand forecast with confidence bands
  • Location × Time-Period heatmap for instant anomaly mapping
  • Efficiency ranking — L/person (occupancy-adjusted)
  • UAE benchmark comparison
  • Alert confidence scoring on leak detection
  • Alert timeline heatmap (Date × Location)
  • Savings Roadmap — ranked, actionable, AED-quantified
  • Global sidebar filters (date range + location)
  • Week-over-week trend arrows on KPIs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io

# ════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════
st.set_page_config(
    page_title="NabdFlow v2 – Water Intelligence",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════
# DESIGN CONSTANTS
# ════════════════════════════════════════════
PALETTE = {
    "primary":   "#0077b6",
    "secondary": "#00b4d8",
    "accent":    "#0096c7",
    "dark":      "#03045e",
    "light":     "#caf0f8",
    "success":   "#22c55e",
    "warning":   "#f59e0b",
    "danger":    "#ef4444",
    "purple":    "#8b5cf6",
    "bg":        "#f0f6fb",
}

ALERT_COLOR = {
    "Normal Variation":   "#22c55e",
    "Monitor":            "#f59e0b",
    "High Usage Alert":   "#ef4444",
    "Possible Leak":      "#3b82f6",
    "Priority Inspection":"#8b5cf6",
}

ALERT_WEIGHT = {
    "Normal Variation":   0,
    "Monitor":            1,
    "High Usage Alert":   2,
    "Possible Leak":      3,
    "Priority Inspection":4,
}

# UAE context constants
WATER_COST_AED_PER_M3    = 4.50   # AED per m³
CO2_KG_PER_M3            = 0.65   # kg CO₂ per m³ (UAE desalination + distribution)
UAE_BENCH_L_PERSON_DAY   = 180.0  # UAE university average litres/person/day
TREES_PER_100KG_CO2      = 1      # 1 tree absorbs ~100 kg CO₂/yr

# ════════════════════════════════════════════
# PREMIUM CSS
# ════════════════════════════════════════════
st.markdown(f"""
<style>
  /* ── Base ── */
  .main {{ background: {PALETTE['bg']}; }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #03045e 0%, #023e8a 60%, #0077b6 100%);
  }}
  section[data-testid="stSidebar"] * {{ color: #e0f2fe !important; }}
  section[data-testid="stSidebar"] .stRadio > div > label {{
    background: rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 6px 10px;
    margin: 2px 0;
    transition: background 0.2s;
  }}
  section[data-testid="stSidebar"] .stRadio > div > label:hover {{
    background: rgba(255,255,255,0.15);
  }}

  /* ── KPI Cards ── */
  .kpi-card {{
    background: #ffffff;
    border-radius: 16px;
    padding: 20px 18px 14px;
    box-shadow: 0 2px 16px rgba(0,100,200,0.09);
    border-top: 4px solid {PALETTE['primary']};
    position: relative;
    overflow: hidden;
    height: 120px;
  }}
  .kpi-card::after {{
    content: "";
    position: absolute;
    right: -20px; bottom: -20px;
    width: 80px; height: 80px;
    border-radius: 50%;
    background: {PALETTE['light']};
    opacity: 0.5;
  }}
  .kpi-label {{
    font-size: 0.72rem; color: #64748b;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em;
  }}
  .kpi-value {{
    font-size: 1.75rem; font-weight: 900;
    color: {PALETTE['dark']}; line-height: 1.2; margin: 4px 0 2px;
  }}
  .kpi-sub {{ font-size: 0.72rem; color: #94a3b8; }}
  .kpi-trend-up   {{ color: #ef4444; font-size: 0.78rem; font-weight:700; }}
  .kpi-trend-down {{ color: #22c55e; font-size: 0.78rem; font-weight:700; }}
  .kpi-trend-flat {{ color: #94a3b8; font-size: 0.78rem; font-weight:700; }}

  /* ── Score Card ── */
  .score-hero {{
    background: linear-gradient(135deg, #03045e 0%, #0077b6 100%);
    border-radius: 20px;
    padding: 32px 36px;
    color: #fff;
    box-shadow: 0 8px 32px rgba(0,80,180,0.25);
    margin-bottom: 16px;
  }}
  .score-hero h1 {{ font-size: 3.5rem; font-weight: 900; margin: 0; line-height:1; }}
  .score-hero .grade {{ font-size: 2.2rem; font-weight: 800; }}
  .score-hero p {{ color: #90caf9; margin: 4px 0 0; font-size: 0.9rem; }}

  /* ── Section header ── */
  .section-header {{
    font-size: 1.3rem; font-weight: 800; color: {PALETTE['dark']};
    padding-bottom: 6px;
    border-bottom: 3px solid {PALETTE['secondary']};
    margin-bottom: 18px;
  }}

  /* ── Alert badges ── */
  .badge-normal   {{ background:#dcfce7; color:#166534; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:700; }}
  .badge-monitor  {{ background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:700; }}
  .badge-high     {{ background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:700; }}
  .badge-leak     {{ background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:700; }}
  .badge-priority {{ background:#ede9fe; color:#4c1d95; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:700; }}

  /* ── Recommendation cards ── */
  .rec-card {{
    background: #ffffff;
    border-left: 5px solid {PALETTE['accent']};
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,100,180,0.07);
  }}

  /* ── Roadmap table ── */
  .roadmap-row {{
    display: flex; align-items: center;
    background: #fff; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px;
    box-shadow: 0 1px 6px rgba(0,80,160,0.07);
    gap: 16px;
  }}
  .roadmap-rank {{
    font-size: 1.4rem; font-weight: 900; color: {PALETTE['primary']};
    min-width: 36px;
  }}
  .roadmap-loc {{ font-weight: 700; color: {PALETTE['dark']}; font-size: 0.95rem; }}
  .roadmap-action {{ color: #475569; font-size: 0.85rem; }}
  .roadmap-aed {{
    margin-left: auto;
    background: {PALETTE['light']};
    color: {PALETTE['dark']};
    font-weight: 800; font-size: 0.9rem;
    padding: 4px 12px; border-radius: 20px;
    white-space: nowrap;
  }}

  /* ── Impact report ── */
  .report-box {{
    background: #fff; border-radius: 16px;
    padding: 32px; box-shadow: 0 4px 24px rgba(0,80,160,0.10);
  }}
  .sdg-chip {{
    display: inline-block;
    background: #1d4ed8; color: #fff;
    font-size: 0.78rem; font-weight: 700;
    padding: 4px 12px; border-radius: 20px;
    margin: 3px;
  }}

  /* ── Divider ── */
  hr {{ border: none; border-top: 1px solid #e2ecf5; margin: 22px 0; }}

  /* ── Benchmark bar ── */
  .bench-bar-wrap {{ background: #e2ecf5; border-radius: 8px; height:14px; margin: 4px 0; }}
  .bench-bar {{ border-radius: 8px; height: 14px; }}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# SAMPLE DATA
# ════════════════════════════════════════════
LOCATIONS = [
    "Washroom Block A",
    "Cafeteria/Pantry",
    "Garden Irrigation",
    "Admin Building",
    "Student Common Area",
]
TIME_PERIODS = ["Morning", "Afternoon", "Evening", "Night"]
NOTES_POOL  = [
    "Routine reading", "Post-event usage", "Holiday period", "",
    "Maintenance window", "High foot traffic", "Irrigation cycle", "Staff only",
]

BASELINES = {
    ("Washroom Block A",    "Morning"):   520,
    ("Washroom Block A",    "Afternoon"): 480,
    ("Washroom Block A",    "Evening"):   310,
    ("Washroom Block A",    "Night"):     40,
    ("Cafeteria/Pantry",    "Morning"):   380,
    ("Cafeteria/Pantry",    "Afternoon"): 620,
    ("Cafeteria/Pantry",    "Evening"):   290,
    ("Cafeteria/Pantry",    "Night"):     20,
    ("Garden Irrigation",   "Morning"):   700,
    ("Garden Irrigation",   "Afternoon"): 850,
    ("Garden Irrigation",   "Evening"):   500,
    ("Garden Irrigation",   "Night"):     50,
    ("Admin Building",      "Morning"):   260,
    ("Admin Building",      "Afternoon"): 300,
    ("Admin Building",      "Evening"):   120,
    ("Admin Building",      "Night"):     15,
    ("Student Common Area", "Morning"):   410,
    ("Student Common Area", "Afternoon"): 530,
    ("Student Common Area", "Evening"):   470,
    ("Student Common Area", "Night"):     30,
}

OCC_BASE = {"Morning": 180, "Afternoon": 210, "Evening": 130, "Night": 12}


@st.cache_data
def generate_sample_data(days: int = 42, seed: int = 42) -> pd.DataFrame:
    rng    = np.random.default_rng(seed)
    recs   = []
    start  = datetime(2024, 9, 1)

    for day_i in range(days):
        date = (start + timedelta(days=day_i)).strftime("%Y-%m-%d")
        for loc in LOCATIONS:
            for tp in TIME_PERIODS:
                expected    = BASELINES[(loc, tp)]
                noise       = rng.normal(1.0, 0.07)
                anomaly     = rng.random()
                if anomaly < 0.05:
                    noise *= rng.uniform(1.28, 1.65)
                elif anomaly < 0.08:
                    noise *= rng.uniform(1.16, 1.27)
                elif anomaly < 0.11 and tp == "Night":
                    noise *= rng.uniform(1.30, 2.40)
                actual   = max(0.0, round(expected * noise, 1))
                occ      = max(0, int(OCC_BASE[tp] * rng.normal(1, 0.15)))
                note     = rng.choice(NOTES_POOL)
                recs.append({
                    "Date":                 date,
                    "Location":             loc,
                    "Time_Period":          tp,
                    "Actual_Usage_Litres":  actual,
                    "Expected_Usage_Litres":float(expected),
                    "Occupancy_Count":      occ,
                    "Notes":               note,
                })
    return pd.DataFrame(recs)


# ════════════════════════════════════════════
# CORE CALCULATIONS
# ════════════════════════════════════════════
REQUIRED_COLS = [
    "Date", "Location", "Time_Period",
    "Actual_Usage_Litres", "Expected_Usage_Litres",
    "Occupancy_Count", "Notes",
]


def validate_df(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    # ── Core water metrics
    df["Excess_Usage_Litres"]    = df["Actual_Usage_Litres"] - df["Expected_Usage_Litres"]
    df["Avoidable_Excess_Litres"]= df["Excess_Usage_Litres"].clip(lower=0)
    df["Difference_Percentage"]  = (
        (df["Actual_Usage_Litres"] - df["Expected_Usage_Litres"])
        / df["Expected_Usage_Litres"].replace(0, np.nan)
    ) * 100
    df["Estimated_AED_Savings"]  = (df["Avoidable_Excess_Litres"] / 1000) * WATER_COST_AED_PER_M3
    df["CO2_Equivalent_kg"]      = (df["Avoidable_Excess_Litres"] / 1000) * CO2_KG_PER_M3

    # ── Occupancy-adjusted intensity (L per person)
    df["Usage_Per_Person"] = (
        df["Actual_Usage_Litres"]
        / df["Occupancy_Count"].replace(0, np.nan)
    )

    # ── Z-score anomaly detection within location+time groups
    df["Z_Score"] = df.groupby(["Location", "Time_Period"])["Actual_Usage_Litres"].transform(
        lambda x: (x - x.mean()) / x.std().replace(0, np.nan)
    )
    df["Z_Score"] = df["Z_Score"].fillna(0)

    # ── Alert classification (rule-based)
    def classify(row):
        pct = row["Difference_Percentage"]
        tp  = str(row["Time_Period"]).strip().lower()
        if pct >= 25 and tp == "night":
            return "Possible Leak"
        elif pct >= 25:
            return "High Usage Alert"
        elif pct >= 15:
            return "Monitor"
        else:
            return "Normal Variation"

    df["Alert_Category"] = df.apply(classify, axis=1)

    # ── Upgrade to Priority Inspection: same location High Usage on ≥2 dates
    high_df    = df[df["Alert_Category"] == "High Usage Alert"].copy()
    loc_days   = (
        high_df.groupby(["Location", "Date"])
               .size()
               .reset_index(name="n")
               .groupby("Location")
               .size()
               .reset_index(name="days")
    )
    priority_locs = set(loc_days.loc[loc_days["days"] >= 2, "Location"])
    df.loc[
        (df["Alert_Category"] == "High Usage Alert") & (df["Location"].isin(priority_locs)),
        "Alert_Category"
    ] = "Priority Inspection"

    # ── Confidence score (combines % deviation + Z-score)
    def confidence(row):
        pct = abs(row["Difference_Percentage"])
        z   = abs(row["Z_Score"])
        if pct >= 50 and z >= 2.5:  return "Very High"
        elif pct >= 35 and z >= 2.0: return "High"
        elif pct >= 25:              return "Medium"
        else:                        return "Low"

    df["Alert_Confidence"] = df.apply(confidence, axis=1)
    df["Alert_Weight"]     = df["Alert_Category"].map(ALERT_WEIGHT)

    return df


# ════════════════════════════════════════════
# ANALYTICS HELPERS
# ════════════════════════════════════════════

def sustainability_score(df: pd.DataFrame) -> float:
    total = len(df)
    if total == 0:
        return 100.0
    w_sum   = df["Alert_Weight"].sum()
    max_w   = total * 4
    score   = 100.0 * (1 - w_sum / max_w)
    return max(0.0, min(100.0, round(score, 1)))


def score_grade(s: float):
    if s >= 88: return "A+", "#22c55e"
    if s >= 78: return "A",  "#4ade80"
    if s >= 68: return "B",  "#84cc16"
    if s >= 58: return "C",  "#f59e0b"
    if s >= 45: return "D",  "#f97316"
    return "F", "#ef4444"


def week_trend(df: pd.DataFrame, col: str) -> tuple:
    """Return (current_week_val, prev_week_val, pct_change)."""
    daily   = df.groupby("Date")[col].sum().sort_index()
    if len(daily) < 8:
        return daily.sum(), None, None
    curr    = daily.iloc[-7:].sum()
    prev    = daily.iloc[-14:-7].sum()
    if prev == 0:
        return curr, prev, None
    change  = (curr - prev) / prev * 100
    return curr, prev, change


def forecast_7d(df: pd.DataFrame) -> pd.DataFrame:
    """Simple 7-day forward forecast using last-14-day linear trend."""
    daily = (
        df.groupby("Date")["Actual_Usage_Litres"]
          .sum()
          .reset_index()
          .sort_values("Date")
    )
    if len(daily) < 7:
        return pd.DataFrame()
    last14  = daily["Actual_Usage_Litres"].tail(14).values
    slope   = np.polyfit(range(len(last14)), last14, 1)[0]
    base    = daily["Actual_Usage_Litres"].tail(7).mean()
    last_d  = daily["Date"].max()
    dates   = [last_d + timedelta(days=i + 1) for i in range(7)]
    vals    = [max(0, base + slope * (i + 1)) for i in range(7)]
    return pd.DataFrame({
        "Date":    dates,
        "Forecast":vals,
        "Upper":   [v * 1.09 for v in vals],
        "Lower":   [v * 0.91 for v in vals],
    })


# ════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════

def kpi_card(label, value, sub="", trend=None, col=None):
    if trend is None:
        trend_html = ""
    elif trend > 2:
        trend_html = f'<div class="kpi-trend-up">▲ {trend:+.1f}% vs last week</div>'
    elif trend < -2:
        trend_html = f'<div class="kpi-trend-down">▼ {trend:+.1f}% vs last week</div>'
    else:
        trend_html = '<div class="kpi-trend-flat">→ Stable</div>'

    html = f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
      {trend_html}
    </div>"""
    (col or st).markdown(html, unsafe_allow_html=True)


def section(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8fbff",
    margin=dict(l=12, r=12, t=36, b=12),
    font=dict(family="Inter, Arial, sans-serif", size=12),
)

# ════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💧 NabdFlow")
    st.markdown("*AI Water Intelligence · v2.0*")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "📊 Overview Dashboard",
            "📍 Location Analysis",
            "🔍 Leak Detection",
            "🤖 AI Recommendations",
            "📄 Impact Report",
            "ℹ️ About NabdFlow",
        ],
    )
    st.markdown("---")

    st.markdown("**Data Source**")
    use_sample   = st.checkbox("Use built-in sample data", value=True)
    uploaded_file = None
    if not use_sample:
        uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv","xlsx","xls"])

    st.markdown("---")
    st.markdown("**🔎 Global Filters**")

# ════════════════════════════════════════════
# LOAD DATA
# ════════════════════════════════════════════
df_raw = None

if use_sample or uploaded_file is None:
    df_raw = generate_sample_data()
    st.sidebar.success("✅ Sample dataset (42 days)")
else:
    try:
        df_raw = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
        validate_df(df_raw)
        st.sidebar.success(f"✅ {uploaded_file.name}")
    except ValueError as e:
        st.error(f"❌ {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Cannot read file: {e}")
        st.stop()

df_all = calculate_metrics(df_raw)

# ── Global filters (sidebar) ──────────────────────────────────────
with st.sidebar:
    min_d = df_all["Date"].min().date()
    max_d = df_all["Date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    all_locs = sorted(df_all["Location"].unique())
    sel_locs = st.multiselect("Locations", all_locs, default=all_locs)
    st.markdown("---")
    st.caption("University Facility Manager Tool")
    st.caption("NabdFlow 2026 · Sustainability Competition")

# Apply global filters
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    d0, d1 = df_all["Date"].min(), df_all["Date"].max()

df = df_all[
    (df_all["Date"] >= d0) &
    (df_all["Date"] <= d1) &
    (df_all["Location"].isin(sel_locs if sel_locs else all_locs))
].copy()

if df.empty:
    st.warning("⚠️ No data for selected filters. Please adjust the date range or location selection.")
    st.stop()

# ════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW DASHBOARD
# ════════════════════════════════════════════════════════════════════
if page == "📊 Overview Dashboard":

    # ── Sustainability Score hero ──────────────────────────────────
    score             = sustainability_score(df)
    grade, grade_col  = score_grade(score)
    total_actual      = df["Actual_Usage_Litres"].sum()
    total_expected    = df["Expected_Usage_Litres"].sum()
    total_avoid       = df["Avoidable_Excess_Litres"].sum()
    total_aed         = df["Estimated_AED_Savings"].sum()
    total_co2         = df["CO2_Equivalent_kg"].sum()
    high_cnt          = df[df["Alert_Category"].isin(["High Usage Alert","Priority Inspection"])].shape[0]
    leak_cnt          = df[df["Alert_Category"] == "Possible Leak"].shape[0]
    prio_cnt          = df[df["Alert_Category"] == "Priority Inspection"].shape[0]
    top_loc           = df.groupby("Location")["Actual_Usage_Litres"].sum().idxmax()
    avg_daily         = df.groupby("Date")["Actual_Usage_Litres"].sum().mean()

    # Week trends
    _, _, trend_actual  = week_trend(df, "Actual_Usage_Litres")
    _, _, trend_avoid   = week_trend(df, "Avoidable_Excess_Litres")

    # Hero card
    st.markdown(f"""
    <div class="score-hero">
      <div style="display:flex; align-items:center; gap:32px; flex-wrap:wrap;">
        <div>
          <div style="font-size:0.8rem;letter-spacing:0.1em;color:#90caf9;font-weight:700;
                      text-transform:uppercase;">Campus Sustainability Score</div>
          <h1 style="font-size:4rem;font-weight:900;margin:4px 0;color:#fff;">{score:.0f}
            <span style="font-size:1.8rem;color:{grade_col};">{grade}</span>
          </h1>
          <p>Based on {len(df):,} readings across {df['Location'].nunique()} locations
             · {d0.strftime('%d %b')} – {d1.strftime('%d %b %Y')}</p>
        </div>
        <div style="display:flex;gap:28px;flex-wrap:wrap;margin-left:auto;">
          <div style="text-align:center;">
            <div style="font-size:2rem;font-weight:800;color:#fff;">{total_avoid/1000:,.1f}</div>
            <div style="color:#90caf9;font-size:0.78rem;">m³ Avoidable Waste</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:2rem;font-weight:800;color:#ffd166;">AED {total_aed:,.0f}</div>
            <div style="color:#90caf9;font-size:0.78rem;">Potential Savings</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:2rem;font-weight:800;color:#80ffb4;">{total_co2:,.1f}</div>
            <div style="color:#90caf9;font-size:0.78rem;">kg CO₂ Equivalent</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:2rem;font-weight:800;color:#ff8fa3;">{prio_cnt + leak_cnt}</div>
            <div style="color:#90caf9;font-size:0.78rem;">Priority Alerts</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── KPI Cards (8) ──────────────────────────────────────────────
    section("📐 Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    kpi_card("Total Water Used",       f"{total_actual:,.0f} L",   f"{total_actual/1000:,.1f} m³", trend_actual,  c1)
    kpi_card("Expected Water Use",     f"{total_expected:,.0f} L", f"{total_expected/1000:,.1f} m³", None,         c2)
    kpi_card("Avoidable Excess",       f"{total_avoid:,.0f} L",   f"{total_avoid/1000:,.2f} m³",  trend_avoid,   c3)
    kpi_card("Estimated AED Savings",  f"AED {total_aed:,.2f}",    "@ AED 4.5 / m³",              None,          c4)

    c5, c6, c7, c8 = st.columns(4)
    kpi_card("CO₂ Equivalent",        f"{total_co2:,.1f} kg",     "Water waste carbon cost",      None, c5)
    kpi_card("High Usage Alerts",     str(high_cnt),               "Needs investigation",          None, c6)
    kpi_card("Possible Leaks",        str(leak_cnt),               "Night-time anomalies",         None, c7)
    kpi_card("Avg Daily Usage",       f"{avg_daily:,.0f} L",       f"Peak: {top_loc}",             None, c8)

    st.markdown("---")

    # ── Chart 1: Daily usage with rolling avg + forecast ──────────
    section("📈 Daily Usage Trend · Actual vs Expected · 7-Day Forecast")

    daily = (
        df.groupby("Date")
          .agg(Actual=("Actual_Usage_Litres","sum"), Expected=("Expected_Usage_Litres","sum"))
          .reset_index()
          .sort_values("Date")
    )
    daily["Rolling_7d"] = daily["Actual"].rolling(7, min_periods=2).mean()
    fcast = forecast_7d(df)

    fig_daily = go.Figure()
    # Expected band
    fig_daily.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Expected"],
        name="Expected", mode="lines",
        line=dict(color="#90caf9", width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(144,202,249,0.08)",
    ))
    # Actual
    fig_daily.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Actual"],
        name="Actual", mode="lines+markers",
        line=dict(color="#0077b6", width=2.5),
        marker=dict(size=4),
    ))
    # 7-day rolling average
    fig_daily.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Rolling_7d"],
        name="7-Day Average", mode="lines",
        line=dict(color="#f59e0b", width=2, dash="dash"),
    ))
    # Forecast confidence band
    if not fcast.empty:
        fig_daily.add_trace(go.Scatter(
            x=pd.concat([fcast["Date"], fcast["Date"].iloc[::-1]]),
            y=pd.concat([fcast["Upper"], fcast["Lower"].iloc[::-1]]),
            fill="toself", fillcolor="rgba(0,180,216,0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Forecast Band", hoverinfo="skip",
        ))
        fig_daily.add_trace(go.Scatter(
            x=fcast["Date"], y=fcast["Forecast"],
            name="7-Day Forecast", mode="lines",
            line=dict(color="#00b4d8", width=2, dash="longdash"),
        ))

    fig_daily.update_layout(
        **CHART_LAYOUT, height=360,
        xaxis_title="Date", yaxis_title="Litres",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_daily, use_container_width=True)
    st.caption("Forecast uses a 14-day linear trend projected 7 days forward. Shaded band = ±9% confidence range.")

    st.markdown("---")

    # ── Chart 2: Heatmap – Location × Time_Period ──────────────────
    section("🌡️ Anomaly Heatmap · Location vs Time of Day")
    st.caption("Average % deviation above expected. Red = consistent overuse; green = efficient.")

    heat = (
        df.groupby(["Location","Time_Period"])["Difference_Percentage"]
          .mean()
          .reset_index()
    )
    order_tp = ["Morning","Afternoon","Evening","Night"]
    heat_pivot = (
        heat.pivot(index="Location", columns="Time_Period", values="Difference_Percentage")
            .reindex(columns=order_tp)
    )
    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
        text_auto=".1f",
        zmin=-10, zmax=35,
        labels=dict(color="Δ% vs Expected"),
    )
    fig_heat.update_layout(**CHART_LAYOUT, height=280,
                           coloraxis_colorbar=dict(title="Δ%", thickness=14))
    fig_heat.update_traces(textfont=dict(size=11))
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ── Chart 3: Usage by location stacked ────────────────────────
    section("🏢 Water Usage by Location")

    loc_sum = (
        df.groupby("Location")
          .agg(Actual=("Actual_Usage_Litres","sum"), Expected=("Expected_Usage_Litres","sum"))
          .reset_index()
          .sort_values("Actual", ascending=False)
    )
    fig_loc = go.Figure()
    fig_loc.add_trace(go.Bar(x=loc_sum["Location"], y=loc_sum["Actual"],   name="Actual",   marker_color="#0077b6"))
    fig_loc.add_trace(go.Bar(x=loc_sum["Location"], y=loc_sum["Expected"], name="Expected", marker_color="#90e0ef"))
    fig_loc.update_layout(
        **CHART_LAYOUT, barmode="group", height=340,
        xaxis_title="Location", yaxis_title="Total Litres",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_loc, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# PAGE 2 — LOCATION ANALYSIS
# ════════════════════════════════════════════════════════════════════
elif page == "📍 Location Analysis":
    section("📍 Location Analysis")
    st.caption("Occupancy-adjusted water efficiency, benchmarking, and risk ranking by campus location.")
    st.markdown("---")

    # Build location summary
    loc_tbl = (
        df.groupby("Location").agg(
            Total_Actual        =("Actual_Usage_Litres",   "sum"),
            Total_Expected      =("Expected_Usage_Litres",  "sum"),
            Avoidable_Excess    =("Avoidable_Excess_Litres","sum"),
            AED_Savings         =("Estimated_AED_Savings",  "sum"),
            CO2_kg              =("CO2_Equivalent_kg",       "sum"),
            Avg_L_Per_Person    =("Usage_Per_Person",        "mean"),
            Alert_Count         =("Alert_Category",
                                  lambda x: x.isin(["Monitor","High Usage Alert",
                                                     "Possible Leak","Priority Inspection"]).sum()),
            Worst_Alert         =("Alert_Weight",            "max"),
        )
        .reset_index()
    )
    loc_tbl["Diff_Pct"] = (
        (loc_tbl["Total_Actual"] - loc_tbl["Total_Expected"])
        / loc_tbl["Total_Expected"].replace(0, np.nan) * 100
    ).round(1)
    # Efficiency score per location (0-100)
    loc_tbl["Efficiency_Score"] = loc_tbl.apply(
        lambda r: max(0, min(100, 100 - r["Diff_Pct"])) if r["Diff_Pct"] > 0 else 100, axis=1
    ).round(0)
    loc_tbl = loc_tbl.sort_values("Total_Actual", ascending=False)

    # ── Efficiency ranking ─────────────────────────────────────────
    section("🏆 Efficiency Ranking (Occupancy-Adjusted)")
    st.caption(f"L/person = average litres consumed per occupant per reading. UAE benchmark: {UAE_BENCH_L_PERSON_DAY:.0f} L/person/day.")

    eff_sorted = loc_tbl.sort_values("Avg_L_Per_Person")
    for _, row in eff_sorted.iterrows():
        lpp        = row["Avg_L_Per_Person"]
        vs_bench   = lpp - (UAE_BENCH_L_PERSON_DAY / 4)  # per reading (~quarter of a day)
        bar_pct    = min(100, (lpp / (UAE_BENCH_L_PERSON_DAY / 2)) * 100)
        bar_color  = "#22c55e" if vs_bench <= 0 else ("#f59e0b" if vs_bench < 20 else "#ef4444")
        grade_s, gc = score_grade(row["Efficiency_Score"])
        col_a, col_b, col_c = st.columns([2, 4, 1])
        with col_a:
            st.markdown(f"**{row['Location']}**  "
                        f"<span style='color:{gc};font-weight:900;'>{grade_s}</span>",
                        unsafe_allow_html=True)
        with col_b:
            st.markdown(
                f'<div class="bench-bar-wrap">'
                f'<div class="bench-bar" style="width:{bar_pct:.0f}%;background:{bar_color};"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_c:
            st.markdown(f"`{lpp:.0f} L/p`")

    st.markdown("---")

    # ── Summary table ──────────────────────────────────────────────
    section("📋 Location-wise Summary Table")

    disp = loc_tbl.copy()
    disp_show = pd.DataFrame({
        "Location":           disp["Location"],
        "Total Actual (L)":   disp["Total_Actual"].map("{:,.0f}".format),
        "Total Expected (L)": disp["Total_Expected"].map("{:,.0f}".format),
        "Excess (L)":         disp["Avoidable_Excess"].map("{:,.0f}".format),
        "Diff %":             disp["Diff_Pct"].map("{:+.1f}%".format),
        "AED Savings":        disp["AED_Savings"].map("AED {:.2f}".format),
        "CO₂ Saved (kg)":     disp["CO2_kg"].map("{:.2f}".format),
        "L/Person":           disp["Avg_L_Per_Person"].map("{:.1f}".format),
        "Alerts":             disp["Alert_Count"].astype(int),
    })
    st.dataframe(disp_show, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Chart: Actual vs Expected ──────────────────────────────────
    section("📊 Actual vs Expected by Location")
    fig_ae = go.Figure()
    fig_ae.add_trace(go.Bar(x=loc_tbl["Location"], y=loc_tbl["Total_Actual"],    name="Actual",    marker_color="#0077b6"))
    fig_ae.add_trace(go.Bar(x=loc_tbl["Location"], y=loc_tbl["Total_Expected"],  name="Expected",  marker_color="#48cae4"))
    fig_ae.add_trace(go.Bar(x=loc_tbl["Location"], y=loc_tbl["Avoidable_Excess"],name="Avoidable", marker_color="#ef4444", opacity=0.75))
    fig_ae.update_layout(
        **CHART_LAYOUT, barmode="group", height=360,
        xaxis_title="Location", yaxis_title="Total Litres",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_ae, use_container_width=True)

    st.markdown("---")

    # ── Chart: Bubble — Usage vs Occupancy ────────────────────────
    section("🔵 Usage vs Occupancy Bubble Chart")
    st.caption("Bubble size = estimated AED savings. Locations outside the trend line may have inefficient fixtures or practices.")

    bub = df.groupby("Location").agg(
        Avg_Actual  =("Actual_Usage_Litres", "mean"),
        Avg_Occ     =("Occupancy_Count",     "mean"),
        AED         =("Estimated_AED_Savings","sum"),
    ).reset_index()
    fig_bub = px.scatter(
        bub, x="Avg_Occ", y="Avg_Actual",
        size="AED", color="Location",
        text="Location",
        size_max=60,
        labels={"Avg_Occ":"Avg Occupancy","Avg_Actual":"Avg Actual Usage (L)"},
        height=380,
    )
    fig_bub.update_traces(textposition="top center", marker=dict(opacity=0.8))
    fig_bub.update_layout(**CHART_LAYOUT, showlegend=False)
    st.plotly_chart(fig_bub, use_container_width=True)

    st.markdown("---")

    # ── UAE Benchmark comparison ───────────────────────────────────
    section("🌍 UAE Benchmark Comparison")
    st.caption(f"UAE university benchmark: {UAE_BENCH_L_PERSON_DAY:.0f} L/person/day. "
               "Locations above this line may benefit from awareness campaigns and fixture upgrades.")

    bench_per_reading = UAE_BENCH_L_PERSON_DAY / len(TIME_PERIODS)
    bcomp = loc_tbl[["Location","Avg_L_Per_Person"]].copy()
    bcomp["Benchmark"] = bench_per_reading
    bcomp["Status"]    = bcomp["Avg_L_Per_Person"].apply(
        lambda x: "Above Benchmark" if x > bench_per_reading else "Within Benchmark"
    )
    fig_bench = go.Figure()
    fig_bench.add_trace(go.Bar(
        x=bcomp["Location"], y=bcomp["Avg_L_Per_Person"],
        name="Campus (L/person)", marker_color=[
            "#ef4444" if s == "Above Benchmark" else "#22c55e"
            for s in bcomp["Status"]
        ],
    ))
    fig_bench.add_hline(
        y=bench_per_reading, line_dash="dash", line_color="#f59e0b",
        annotation_text=f"UAE Benchmark ({bench_per_reading:.0f} L/p/reading)",
        annotation_position="top right",
    )
    fig_bench.update_layout(**CHART_LAYOUT, height=320,
                            xaxis_title="Location", yaxis_title="Avg L / Person")
    st.plotly_chart(fig_bench, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# PAGE 3 — LEAK DETECTION
# ════════════════════════════════════════════════════════════════════
elif page == "🔍 Leak Detection":
    section("🔍 Leak Detection & Anomaly Intelligence")
    st.caption("Rule-based alerts enhanced with statistical Z-score confidence scoring.")
    st.markdown("---")

    # ── Summary counts ─────────────────────────────────────────────
    alert_types = ["Priority Inspection","Possible Leak","High Usage Alert","Monitor","Normal Variation"]
    cols_ac = st.columns(5)
    for i, at in enumerate(alert_types):
        cnt = (df["Alert_Category"] == at).sum()
        cols_ac[i].metric(at, cnt)

    st.markdown("---")

    # ── Filters ────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_locs   = st.multiselect("Location", sorted(df["Location"].unique()),
                                        default=sorted(df["Location"].unique()), key="leak_loc")
    with col_f2:
        filter_alerts = st.multiselect("Alert Type",
                                        ["Priority Inspection","Possible Leak","High Usage Alert","Monitor"],
                                        default=["Priority Inspection","Possible Leak","High Usage Alert","Monitor"],
                                        key="leak_alert")
    with col_f3:
        filter_conf   = st.multiselect("Confidence",
                                        ["Very High","High","Medium","Low"],
                                        default=["Very High","High","Medium"],
                                        key="leak_conf")

    filt = df[
        (df["Location"].isin(filter_locs)) &
        (df["Alert_Category"].isin(filter_alerts)) &
        (df["Alert_Confidence"].isin(filter_conf))
    ]
    st.markdown(f"**{len(filt):,} records** match the current filters.")

    # ── Alert timeline heatmap ─────────────────────────────────────
    section("🗓️ Alert Timeline Heatmap · Location × Date")
    st.caption("Colour intensity = severity level. Dark purple = Priority Inspection. Quickly spot recurring problem areas.")

    tl = df.copy()
    tl["Alert_Num"] = tl["Alert_Weight"]
    tl_piv = tl.pivot_table(index="Location", columns="Date", values="Alert_Num", aggfunc="max")
    tl_piv.columns = [d.strftime("%d %b") for d in tl_piv.columns]

    fig_tl = px.imshow(
        tl_piv,
        color_continuous_scale=["#f0fdf4","#fef9c3","#fee2e2","#dbeafe","#ede9fe"],
        aspect="auto",
        zmin=0, zmax=4,
        labels=dict(color="Severity"),
    )
    fig_tl.update_layout(**CHART_LAYOUT, height=240,
                         xaxis=dict(tickangle=-45),
                         coloraxis_colorbar=dict(
                             tickvals=[0,1,2,3,4],
                             ticktext=["Normal","Monitor","High","Leak","Priority"],
                             thickness=14, title="",
                         ))
    st.plotly_chart(fig_tl, use_container_width=True)

    st.markdown("---")

    # ── Alert distribution ─────────────────────────────────────────
    col_pie, col_bar = st.columns([1, 2])
    with col_pie:
        section("Distribution")
        ac = df["Alert_Category"].value_counts().reset_index()
        ac.columns = ["Alert","Count"]
        fig_pie = px.pie(
            ac, names="Alert", values="Count", hole=0.48,
            color="Alert",
            color_discrete_map={k: v for k, v in ALERT_COLOR.items()},
            height=280,
        )
        fig_pie.update_layout(paper_bgcolor="white", margin=dict(l=0,r=0,t=20,b=0),
                               legend=dict(orientation="v", font=dict(size=10)))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        section("Alerts Over Time")
        bad = df[df["Alert_Category"] != "Normal Variation"].copy()
        if not bad.empty:
            bad["Week"] = bad["Date"].dt.to_period("W").astype(str)
            weekly = bad.groupby(["Week","Alert_Category"]).size().reset_index(name="Count")
            fig_wk = px.bar(
                weekly, x="Week", y="Count", color="Alert_Category",
                color_discrete_map=ALERT_COLOR, height=280,
                labels={"Alert_Category":"Alert","Week":""},
            )
            fig_wk.update_layout(**CHART_LAYOUT, barmode="stack",
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            st.plotly_chart(fig_wk, use_container_width=True)

    st.markdown("---")

    # ── Flagged records table ──────────────────────────────────────
    section("📋 Flagged Records with Confidence Score")
    if filt.empty:
        st.info("No records match current filters.")
    else:
        show_cols = filt[[
            "Date","Location","Time_Period",
            "Actual_Usage_Litres","Expected_Usage_Litres",
            "Difference_Percentage","Z_Score",
            "Alert_Category","Alert_Confidence","Notes",
        ]].copy()
        show_cols["Date"]                 = show_cols["Date"].dt.strftime("%Y-%m-%d")
        show_cols["Difference_Percentage"]= show_cols["Difference_Percentage"].round(1)
        show_cols["Z_Score"]              = show_cols["Z_Score"].round(2)
        show_cols                         = show_cols.sort_values(
            by=["Alert_Confidence","Difference_Percentage"],
            ascending=[False, False],
        )
        st.dataframe(show_cols, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Priority action table ──────────────────────────────────────
    section("🚨 Priority Action Table")

    prio_meta = {
        "Priority Inspection": ("🔴 Urgent",   "Repeated ≥25% excess on ≥2 days",           "Immediate on-site inspection — pipes, fixtures, isolation valves"),
        "Possible Leak":       ("🟠 High",     "Night-time excess ≥25% (low occupancy)",     "Check overnight valve seals, cisterns, auto-fill mechanisms"),
        "High Usage Alert":    ("🟡 Medium",   "Single-day excess ≥25%",                     "Review usage event; check for open taps or equipment faults"),
        "Monitor":             ("🟢 Low",      "Excess 15–25% above expected",               "Track for 3+ days; escalate if trend continues"),
    }
    prows = []
    for at, (pri, reason, action) in prio_meta.items():
        for loc in df[df["Alert_Category"] == at]["Location"].unique():
            cnt = (df[(df["Alert_Category"] == at) & (df["Location"] == loc)]).shape[0]
            prows.append({"Priority": pri, "Location": loc, "Alert": at,
                          "Occurrences": cnt, "Reason": reason, "Action": action})
    if prows:
        pdf = pd.DataFrame(prows).sort_values(
            by="Priority", key=lambda s: s.map({"🔴 Urgent":0,"🟠 High":1,"🟡 Medium":2,"🟢 Low":3})
        )
        st.dataframe(pdf, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No priority actions for current selection.")


# ════════════════════════════════════════════════════════════════════
# PAGE 4 — AI RECOMMENDATIONS
# ════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Recommendations":
    section("🤖 AI-Powered Recommendations")
    st.caption("Data-driven insights generated from the campus water usage patterns. Ranked by estimated AED impact.")
    st.markdown("---")

    # ── Build recommendation objects ───────────────────────────────
    recs = []   # {rank, icon, tag, loc, text, aed_impact, action_type}

    # 1. Priority Inspection locations
    for loc in df[df["Alert_Category"] == "Priority Inspection"]["Location"].unique():
        cnt     = (df[(df["Alert_Category"] == "Priority Inspection") & (df["Location"] == loc)]).shape[0]
        aed_imp = df[(df["Location"] == loc)]["Estimated_AED_Savings"].sum()
        recs.append(dict(
            icon="🔴", tag="URGENT – PRIORITY INSPECTION", loc=loc,
            text=(
                f"<b>{loc}</b> has triggered Priority Inspection alerts on multiple days ({cnt} readings). "
                "Repeated high consumption indicates a persistent fault — likely a running tap, faulty flush valve, "
                "or distribution pipe leak. Schedule an immediate physical inspection; do not wait for the next meter cycle."
            ),
            aed=aed_imp,
        ))

    # 2. Possible Leaks (night-time)
    for loc in df[df["Alert_Category"] == "Possible Leak"]["Location"].unique():
        cnt     = (df[(df["Alert_Category"] == "Possible Leak") & (df["Location"] == loc)]).shape[0]
        max_pct = df[(df["Alert_Category"] == "Possible Leak") & (df["Location"] == loc)]["Difference_Percentage"].max()
        aed_imp = df[(df["Location"] == loc) & (df["Alert_Category"] == "Possible Leak")]["Estimated_AED_Savings"].sum()
        recs.append(dict(
            icon="🔵", tag="LEAK RISK – NIGHT USAGE", loc=loc,
            text=(
                f"Night-time water flow at <b>{loc}</b> exceeded expected by up to <b>{max_pct:.0f}%</b> "
                f"on {cnt} occasion(s). With minimal occupancy at night, this excess strongly suggests a hidden leak. "
                "Inspect overflow valves, auto-fill cisterns, and any unmetered supply lines. "
                "Consider installing an automatic shut-off valve on this line between 23:00–05:00."
            ),
            aed=aed_imp,
        ))

    # 3. Irrigation-specific
    irr_locs = df[
        (df["Alert_Category"].isin(["High Usage Alert","Priority Inspection"])) &
        (df["Location"].str.contains("Garden|Irrigation", case=False, na=False))
    ]["Location"].unique()
    for loc in irr_locs:
        excess = df[(df["Location"] == loc)]["Avoidable_Excess_Litres"].sum()
        aed_imp= df[(df["Location"] == loc)]["Estimated_AED_Savings"].sum()
        recs.append(dict(
            icon="🌿", tag="IRRIGATION EFFICIENCY", loc=loc,
            text=(
                f"<b>{loc}</b> shows excess usage of <b>{excess:,.0f} L</b> above baseline. "
                "Recommendations: (1) Shift irrigation to 05:00–07:00 to cut evaporation losses by 20–30%. "
                "(2) Install soil-moisture sensors to trigger demand-based watering only. "
                "(3) Reduce run duration by 15% and monitor for 7 days before adjusting further."
            ),
            aed=aed_imp,
        ))

    # 4. Cafeteria
    cafe_locs = df[
        (df["Alert_Category"].isin(["High Usage Alert","Priority Inspection","Monitor"])) &
        (df["Location"].str.contains("Cafeteria|Pantry", case=False, na=False))
    ]["Location"].unique()
    for loc in cafe_locs:
        pm_excess = df[(df["Location"] == loc) & (df["Time_Period"] == "Afternoon")]["Avoidable_Excess_Litres"].sum()
        aed_imp = df[(df["Location"] == loc)]["Estimated_AED_Savings"].sum()
        recs.append(dict(
            icon="🍽️", tag="CAFETERIA / FOOD PREP", loc=loc,
            text=(
                f"Afternoon excess of <b>{pm_excess:,.0f} L</b> detected at <b>{loc}</b>. "
                "Common causes: extended pre-rinse cycles, dishwasher pre-soak overuse, or staff running taps during prep. "
                "Introduce a water-use checklist for catering staff. "
                "Installing flow restrictors on prep sinks can reduce consumption by 15–20% with no impact on operations."
            ),
            aed=aed_imp,
        ))

    # 5. Washroom fixtures
    wash_locs = df[
        (df["Alert_Category"].isin(["High Usage Alert","Priority Inspection"])) &
        (df["Location"].str.contains("Washroom|Block", case=False, na=False))
    ]["Location"].unique()
    for loc in wash_locs:
        excess = df[(df["Location"] == loc)]["Avoidable_Excess_Litres"].sum()
        aed_imp = df[(df["Location"] == loc)]["Estimated_AED_Savings"].sum()
        recs.append(dict(
            icon="🚿", tag="FIXTURE MAINTENANCE", loc=loc,
            text=(
                f"Excess usage of <b>{excess:,.0f} L</b> at <b>{loc}</b>. "
                "Prioritise: (1) Replace dual-flush cisterns if >5 years old — faulty internals waste up to 200 L/day each. "
                "(2) Check tap aerators quarterly — a 2mm drip wastes ~90 L/day. "
                "(3) Sensor-activated taps in high-traffic washrooms reduce usage by up to 30%."
            ),
            aed=aed_imp,
        ))

    # 6. Night-time general
    night_excess = df[(df["Time_Period"] == "Night") & (df["Avoidable_Excess_Litres"] > 0)]["Avoidable_Excess_Litres"].sum()
    if night_excess > 300:
        recs.append(dict(
            icon="🌙", tag="NIGHT-TIME MANAGEMENT", loc="All Locations",
            text=(
                f"Total campus night-time avoidable excess: <b>{night_excess:,.0f} L</b> "
                f"(AED {night_excess/1000*WATER_COST_AED_PER_M3:.2f} estimated cost). "
                "With minimal occupancy after 22:00, any significant flow is abnormal. "
                "Install zone-level automated shutoff on non-critical lines (washrooms, cafeteria) between 23:00–05:30. "
                "Smart-valve solutions cost approximately AED 400–800 per zone — payback period under 6 months at current rates."
            ),
            aed=night_excess / 1000 * WATER_COST_AED_PER_M3,
        ))

    # 7. CO₂ impact awareness
    total_co2 = df["CO2_Equivalent_kg"].sum()
    trees_eq   = max(1, int(total_co2 / 100))
    recs.append(dict(
        icon="🌍", tag="ENVIRONMENTAL IMPACT", loc="Campus-wide",
        text=(
            f"The <b>{total_co2:.1f} kg CO₂</b> equivalent from avoidable water waste "
            f"corresponds to approximately <b>{trees_eq} trees'</b> annual carbon absorption. "
            "Addressing identified waste aligns with <b>SDG 6</b> and the "
            "<b>UAE Water Security Strategy 2036</b>. "
            "Report these figures quarterly to Senior Management — "
            "environmental KPIs are increasingly tied to university accreditation and rankings."
        ),
        aed=0,
    ))

    # 8. Monitor locations — generic trend warning
    mon_locs = df[df["Alert_Category"] == "Monitor"]["Location"].unique()
    for loc in mon_locs[:2]:
        recs.append(dict(
            icon="🟡", tag="MONITOR – TREND WATCH", loc=loc,
            text=(
                f"<b>{loc}</b> is in the 15–25% excess band. While not yet critical, "
                "this often precedes a high-usage event. Set a 7-day monitoring window. "
                "If excess persists, check for behavioural changes (new equipment, event bookings, staffing changes) "
                "before escalating to a physical inspection."
            ),
            aed=df[(df["Location"] == loc)]["Estimated_AED_Savings"].sum(),
        ))

    # Sort by AED impact (descending), remove duplicates
    recs_deduped = []
    seen_loc_tag = set()
    for r in sorted(recs, key=lambda x: x["aed"], reverse=True):
        key = (r["loc"], r["tag"])
        if key not in seen_loc_tag:
            seen_loc_tag.add(key)
            recs_deduped.append(r)

    # ── Savings Roadmap ────────────────────────────────────────────
    section("🗺️ Savings Roadmap · Ranked by Impact")
    st.caption("Prioritised action list. Address top items first for maximum water and cost reduction.")

    for i, rec in enumerate(recs_deduped, 1):
        aed_str = f"AED {rec['aed']:,.2f}" if rec["aed"] > 0 else "—"
        st.markdown(f"""
        <div class="roadmap-row">
          <div class="roadmap-rank">#{i}</div>
          <div>
            <div class="roadmap-loc">{rec['icon']} {rec['loc']}</div>
            <div class="roadmap-action">{rec['tag']}</div>
          </div>
          <div class="roadmap-aed">{aed_str}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Detailed recommendation cards ─────────────────────────────
    section("💡 Detailed Insights")

    if not recs_deduped:
        st.success("✅ No significant anomalies — campus water usage is within normal range.")
    else:
        for rec in recs_deduped:
            st.markdown(f"""
            <div class="rec-card">
              <div style="margin-bottom:5px;">
                <span style="font-size:1.3rem;">{rec['icon']}</span>
                <b style="color:#0077b6;font-size:0.76rem;text-transform:uppercase;
                          letter-spacing:0.08em;">{rec['tag']}</b>
                {f'<span style="float:right;background:#e0f2fe;color:#0077b6;font-weight:800;'
                  f'font-size:0.8rem;padding:2px 10px;border-radius:12px;">AED {rec["aed"]:,.2f}</span>'
                  if rec["aed"] > 0 else ''}
              </div>
              <div style="color:#334155;font-size:0.92rem;line-height:1.55;">{rec['text']}</div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# PAGE 5 — IMPACT REPORT
# ════════════════════════════════════════════════════════════════════
elif page == "📄 Impact Report":
    section("📄 Sustainability Impact Report")
    st.caption("Structured summary for management reporting, grant applications, and sustainability audits.")
    st.markdown("---")

    # User inputs
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        people_reached  = st.number_input("Estimated students/staff reached", min_value=1, value=250, step=10)
        pilot_location  = st.text_input("Pilot Location", value="Main University Campus")
        pilot_weeks     = st.slider("Pilot Duration (weeks)", 2, 16, 6)
    with col_in2:
        red_target      = st.slider("Water Reduction Target (%)", 5, 35, 15, 1)
        report_title    = st.text_input("Report Title", value="NabdFlow Campus Water Intelligence Report")
        reporting_period= st.text_input("Reporting Period", value=f"{d0.strftime('%d %b %Y')} – {d1.strftime('%d %b %Y')}")

    st.markdown("---")

    # Computed figures
    total_actual    = df["Actual_Usage_Litres"].sum()
    total_avoid     = df["Avoidable_Excess_Litres"].sum()
    total_aed       = df["Estimated_AED_Savings"].sum()
    total_co2       = df["CO2_Equivalent_kg"].sum()
    trees_eq        = max(1, int(total_co2 / 100))
    score           = sustainability_score(df)
    grade, gclr     = score_grade(score)
    high_cnt        = df[df["Alert_Category"].isin(["High Usage Alert","Priority Inspection"])].shape[0]
    leak_cnt        = df[df["Alert_Category"] == "Possible Leak"].shape[0]
    prio_cnt        = df[df["Alert_Category"] == "Priority Inspection"].shape[0]
    total_alerts    = high_cnt + leak_cnt + prio_cnt

    proj_save_l     = total_actual * (red_target / 100)
    proj_save_aed   = (proj_save_l / 1000) * WATER_COST_AED_PER_M3
    proj_save_co2   = (proj_save_l / 1000) * CO2_KG_PER_M3
    per_person      = proj_save_l / people_reached if people_reached else 0

    # ── Report ─────────────────────────────────────────────────────
    st.markdown('<div class="report-box">', unsafe_allow_html=True)

    st.markdown(f"## 💧 {report_title}")
    st.markdown(f"**Reporting Period:** {reporting_period}  |  **Generated:** {datetime.now().strftime('%d %B %Y %H:%M')}")

    st.markdown("---")

    # Headline score
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.markdown(f"""
        <div style="text-align:center;background:linear-gradient(135deg,#03045e,#0077b6);
                    border-radius:16px;padding:24px;color:#fff;">
          <div style="font-size:0.8rem;letter-spacing:0.1em;color:#90caf9;">CAMPUS SCORE</div>
          <div style="font-size:4rem;font-weight:900;line-height:1;">{score:.0f}</div>
          <div style="font-size:2rem;font-weight:800;color:{gclr};">{grade}</div>
          <div style="font-size:0.78rem;color:#90caf9;margin-top:4px;">Water Sustainability Index</div>
        </div>""", unsafe_allow_html=True)
    with col_s2:
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Usage",       f"{total_actual/1000:,.1f} m³")
        r2.metric("Avoidable Waste",   f"{total_avoid/1000:,.2f} m³")
        r3.metric("AED Potential Savings", f"AED {total_aed:,.2f}")
        r4, r5, r6 = st.columns(3)
        r4.metric("CO₂ Equivalent",    f"{total_co2:.1f} kg",  f"≈ {trees_eq} trees/yr")
        r5.metric("Total Alerts",      str(total_alerts))
        r6.metric("Priority Actions",  str(prio_cnt + leak_cnt))

    st.markdown("---")
    st.markdown("#### 🎯 Projections (if reduction target achieved)")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Reduction Target",   f"{red_target}%")
    p2.metric("Water Saved",        f"{proj_save_l:,.0f} L",    f"{proj_save_l/1000:,.1f} m³")
    p3.metric("AED Saved",          f"AED {proj_save_aed:,.2f}")
    p4.metric("CO₂ Avoided",        f"{proj_save_co2:.1f} kg")

    q1, q2 = st.columns(2)
    q1.metric("People Reached",     f"{people_reached:,}")
    q2.metric("Saving per Person",  f"{per_person:,.1f} L")

    st.markdown("---")
    st.markdown("#### 🌍 Strategic Alignment")

    st.markdown("""
    <span class="sdg-chip">SDG 6: Clean Water</span>
    <span class="sdg-chip">SDG 12: Responsible Consumption</span>
    <span class="sdg-chip">UAE Water Security Strategy 2036</span>
    <span class="sdg-chip">Smart Water Management</span>
    <span class="sdg-chip">UAE Quality of Life Strategy</span>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
    | Framework | Specific Alignment |
    |-----------|-------------------|
    | **SDG 6** | Real-time detection of waste; promotes efficient use of a scarce resource in an arid region |
    | **SDG 12** | Quantifies and reduces institutional overconsumption through data intelligence |
    | **UAE Water Security Strategy 2036** | Supports 26% water efficiency improvement target for public facilities |
    | **UAE Smart Water Management** | Enables data-driven proactive management without additional sensor hardware |
    | **Quality of Life Strategy** | Improves campus environment; promotes awareness and community responsibility |
    """)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Visual: Projection chart ────────────────────────────────────
    section("📊 Before vs After Projection")
    fig_proj = go.Figure()
    categories = ["Total Usage", "Expected Usage", "Avoidable Waste", "Projected Savings"]
    values_cur = [total_actual/1000, df["Expected_Usage_Litres"].sum()/1000, total_avoid/1000, 0]
    values_new = [
        (total_actual - proj_save_l) / 1000,
        df["Expected_Usage_Litres"].sum() / 1000,
        max(0, total_avoid - proj_save_l) / 1000,
        proj_save_l / 1000,
    ]
    fig_proj.add_trace(go.Bar(name="Current",  x=categories, y=values_cur, marker_color="#0077b6"))
    fig_proj.add_trace(go.Bar(name="Projected",x=categories, y=values_new, marker_color="#22c55e", opacity=0.85))
    fig_proj.update_layout(**CHART_LAYOUT, barmode="group", height=320,
                           yaxis_title="m³", legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("---")

    # ── Downloads ───────────────────────────────────────────────────
    section("⬇️ Download Report")

    report_txt = f"""
{report_title}
{"="*60}
Generated   : {datetime.now().strftime('%d %B %Y %H:%M')}
Period      : {reporting_period}
Pilot Site  : {pilot_location}
Duration    : {pilot_weeks} weeks
Records     : {len(df):,}

CAMPUS SUSTAINABILITY SCORE: {score:.0f} / 100  (Grade: {grade})

WATER USAGE FINDINGS
  Total Used          : {total_actual:,.0f} L  ({total_actual/1000:,.1f} m³)
  Avoidable Excess    : {total_avoid:,.0f} L  ({total_avoid/1000:,.2f} m³)
  AED Potential Saving: AED {total_aed:,.2f}
  CO₂ Equivalent      : {total_co2:.2f} kg  (≈{trees_eq} trees/yr)
  Total Alerts        : {total_alerts}
  Possible Leaks      : {leak_cnt}
  Priority Inspections: {prio_cnt}

IMPACT PROJECTIONS  [{red_target}% Reduction Target]
  Water Saved         : {proj_save_l:,.0f} L  ({proj_save_l/1000:,.1f} m³)
  AED Saved           : AED {proj_save_aed:,.2f}
  CO₂ Avoided         : {proj_save_co2:.2f} kg
  People Reached      : {people_reached:,}
  Saving/Person       : {per_person:,.1f} L

SUSTAINABILITY ALIGNMENT
  SDG 6  : Clean Water and Sanitation
  SDG 12 : Responsible Consumption and Production
  UAE Water Security Strategy 2036
  UAE Smart Water Management
  UAE Quality of Life Strategy

{"="*60}
NabdFlow v2.0 · University Campus Water Intelligence
"""

    report_csv_df = pd.DataFrame({
        "Metric": [
            "Campus Sustainability Score","Total Water Used (L)","Total Water Used (m³)",
            "Avoidable Excess (L)","Avoidable Excess (m³)","Estimated AED Savings",
            "CO2 Equivalent (kg)","Trees Equivalent","Total Alerts",
            "Possible Leaks","Priority Inspections",
            "Reduction Target (%)","Projected Water Saved (L)","Projected AED Saved",
            "Projected CO2 Avoided (kg)","People Reached","Saving per Person (L)",
        ],
        "Value": [
            f"{score:.0f}/100 ({grade})",
            f"{total_actual:,.0f}", f"{total_actual/1000:,.1f}",
            f"{total_avoid:,.0f}", f"{total_avoid/1000:,.2f}",
            f"AED {total_aed:,.2f}", f"{total_co2:.2f}", str(trees_eq),
            total_alerts, leak_cnt, prio_cnt,
            red_target, f"{proj_save_l:,.0f}", f"AED {proj_save_aed:,.2f}",
            f"{proj_save_co2:.2f}", people_reached, f"{per_person:,.1f}",
        ],
    })

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("📄 Download TXT Report",
                           report_txt, "nabdflow_report.txt", "text/plain")
    with dl2:
        st.download_button("📊 Download CSV Summary",
                           report_csv_df.to_csv(index=False), "nabdflow_summary.csv", "text/csv")
    with dl3:
        full_csv = df.copy()
        full_csv["Date"] = full_csv["Date"].dt.strftime("%Y-%m-%d")
        st.download_button("📥 Export Full Dataset",
                           full_csv.to_csv(index=False), "nabdflow_data.csv", "text/csv")


# ════════════════════════════════════════════════════════════════════
# PAGE 6 — ABOUT
# ════════════════════════════════════════════════════════════════════
elif page == "ℹ️ About NabdFlow":
    section("ℹ️ About NabdFlow v2.0")
    st.markdown("---")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("""
### 💧 What is NabdFlow?

NabdFlow is a **campus-level water intelligence platform** designed for university facility managers.
It transforms meter readings and facility records into actionable insights — helping institutions move
from **reactive maintenance to proactive water stewardship**.

> *"Nabd" (نبض) means pulse in Arabic. NabdFlow monitors the pulse of your campus water systems.*

---

### 🆕 What's New in v2.0

| Feature | Description |
|---------|-------------|
| **Sustainability Score** | 0–100 campus health index with A+–F grade |
| **CO₂ Calculations** | Water waste converted to carbon impact (UAE desalination context) |
| **7-Day Forecast** | Linear trend projection with confidence bands |
| **Anomaly Heatmap** | Location × Time-Period visual anomaly map |
| **Z-Score Detection** | Statistical anomaly scoring alongside rule-based alerts |
| **Efficiency Ranking** | L/person occupancy-adjusted benchmark |
| **UAE Benchmark** | Compare against 180 L/person/day national average |
| **Alert Confidence** | Very High / High / Medium / Low confidence per alert |
| **Alert Timeline** | Date × Location severity heatmap |
| **Savings Roadmap** | Ranked recommendations by AED impact |
| **Global Filters** | Date range + location filter across all pages |
| **CO₂ in Report** | Environmental impact integrated into impact report |

---

### 🔢 Methodology

| Metric | Formula |
|--------|---------|
| Excess Usage | Actual − Expected |
| Avoidable Excess | max(Excess, 0) |
| Difference % | (Actual − Expected) / Expected × 100 |
| AED Savings | Avoidable (L) ÷ 1,000 × AED 4.50 |
| CO₂ Equivalent | Avoidable (m³) × 0.65 kg (UAE grid factor) |
| Usage / Person | Actual ÷ Occupancy Count |
| Z-Score | (x − μ) / σ within Location × Time group |

**Sustainability Score:**
Weighted across all readings: Normal=0, Monitor=1, High=2, Leak=3, Priority=4.
Score = 100 × (1 − weighted_sum / max_possible).

**Alert Thresholds:**
- 0–15% → Normal Variation
- 15–25% → Monitor
- ≥25% → High Usage Alert
- ≥25% + Night → Possible Leak
- ≥25% on ≥2 days, same location → Priority Inspection

---

### 🌍 Strategic Alignment

- **SDG 6** – Clean Water and Sanitation
- **SDG 12** – Responsible Consumption and Production
- **UAE Water Security Strategy 2036** (26% efficiency improvement target)
- **UAE Smart Water Management Direction**
- **UAE Quality of Life and Sustainable Communities**

---

### ⚠️ Important Notes

NabdFlow is **not a replacement** for smart metering infrastructure.
It is a **campus intelligence layer** that works with existing data — no hardware required.
CO₂ factors are indicative estimates based on UAE desalination energy intensity (~1.0 kWh/m³)
and the national grid emission factor (~0.65 kg CO₂/kWh).
        """)

    with col_side:
        st.markdown("### 📌 Quick Reference")
        st.info("**Version:** 2.0")
        st.info("**User:** Facility Manager")
        st.info("**Cost Rate:** AED 4.50 / m³")
        st.info("**CO₂ Factor:** 0.65 kg / m³")
        st.info("**UAE Benchmark:** 180 L/p/day")
        st.info("**Pilot Duration:** 4–8 weeks")
        st.success("**Open Source:** Yes")

        st.markdown("### 🔧 Tech Stack")
        st.markdown("""
- 🐍 Python 3.11+
- 📊 Streamlit 1.32+
- 🐼 Pandas / NumPy
- 📈 Plotly 5.x
        """)

        st.markdown("### 🚀 Roadmap")
        st.markdown("""
Future releases:
- IoT / smart meter API connector
- Arabic language interface
- Predictive ML anomaly model
- Multi-campus dashboard
- WhatsApp alert integration
- PDF report export
        """)

        st.markdown("### 🏆 Competition")
        st.markdown("""
Built for the **UAE University Sustainability Competition**.
Addressing water scarcity in alignment with
UAE Vision 2031 and the national commitment to
water security in an arid-zone context.
        """)
