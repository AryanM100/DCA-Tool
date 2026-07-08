import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go

# Arps Hyperbolic Decline Model
def arps_hyperbolic(t, qi, b, Di):
    return qi / (1.0 + b * Di * t) ** (1.0 / b)


def calculate_eur(qi, b, Di, abandonment_rate, max_months=6000):
    """Integrate production until rate drops to the abandonment limit."""
    t = np.arange(1, max_months + 1, dtype=float)
    q = arps_hyperbolic(t, qi, b, Di)
    mask = q >= abandonment_rate
    if not np.any(mask):
        return 0.0, t[:1], q[:1]
    q_above = q[mask]
    t_above = t[mask]
    eur = np.trapezoid(q_above * 30.44, t_above)  # bbl/day × ~days/month → bbl
    return eur, t_above, q_above


# Page Config
st.set_page_config(
    page_title="DCA & EUR Forecasting",
    page_icon="bbl",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label {color: #94a3b8 !important; font-size: 0.85rem;}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #f8fafc !important; font-size: 1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# Sidebar
with st.sidebar:
    st.header("DCA Configuration")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload Production CSV",
        type=["csv"],
        help="CSV with columns: **Month** (integer) and **Rate** (bbl/day)",
    )

    st.markdown("---")
    st.subheader("Forecast Settings")

    forecast_months = st.number_input(
        "Forecast Duration (Months)",
        min_value=1,
        max_value=600,
        value=60,
        step=12,
    )

    abandonment_rate = st.number_input(
        "Abandonment Rate (bbl/day)",
        min_value=0.1,
        max_value=500.0,
        value=10.0,
        step=1.0,
    )

    st.markdown("---")
    y_scale = st.radio("Y-Axis Scale", ["Linear", "Logarithmic"], index=0)


# Main Page
st.title("Automated DCA & Reserves Forecasting")
st.markdown(
    "This tool fits the **Arps Hyperbolic Decline** equation to historical "
    "production data using non-linear regression, then forecasts future "
    "production and estimates **EUR** (Estimated Ultimate Recovery)."
)

if uploaded_file is None:
    st.info(
        "Upload a CSV file with **Month** and **Rate** columns in the sidebar to get started.",
        icon="📂",
    )
    st.stop()


# Data Loading
try:
    df = pd.read_csv(uploaded_file)
    if "Month" not in df.columns or "Rate" not in df.columns:
        st.error("CSV must contain **Month** and **Rate** columns.")
        st.stop()
    df = df.dropna(subset=["Month", "Rate"])
    df = df.sort_values("Month").reset_index(drop=True)
    t_hist = df["Month"].values.astype(float)
    q_hist = df["Rate"].values.astype(float)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

with st.expander("Raw Production Data", expanded=False):
    st.dataframe(df, use_container_width=True)


# Curve Fitting
try:
    p0 = [q_hist[0], 0.5, 0.1]
    bounds_lower = [0.0, 0.001, 0.0]
    bounds_upper = [np.inf, 2.0, np.inf]

    popt, pcov = curve_fit(
        arps_hyperbolic,
        t_hist,
        q_hist,
        p0=p0,
        bounds=(bounds_lower, bounds_upper),
        maxfev=10000,
    )

    qi_opt, b_opt, Di_opt = popt

    t_fit = np.linspace(t_hist.min(), t_hist.max(), 300)
    q_fit = arps_hyperbolic(t_fit, *popt)

    t_forecast_start = t_hist.max()
    t_forecast = np.linspace(t_forecast_start, t_forecast_start + forecast_months, 500)
    q_forecast = arps_hyperbolic(t_forecast, *popt)

    eur, _, _ = calculate_eur(qi_opt, b_opt, Di_opt, abandonment_rate)

except RuntimeError:
    st.error(
        "Curve fitting failed to converge. Try adjusting your data or check "
        "for anomalies in the production history."
    )
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during analysis: {e}")
    st.stop()


# Plotly Chart
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=t_hist,
        y=q_hist,
        mode="markers",
        name="Historical Data",
        marker=dict(color="black", size=7, symbol="circle", line=dict(width=1, color="#555")),
    )
)

fig.add_trace(
    go.Scatter(
        x=t_fit,
        y=q_fit,
        mode="lines",
        name="Fitted Curve",
        line=dict(color="#2563eb", width=3),
    )
)

fig.add_trace(
    go.Scatter(
        x=t_forecast,
        y=q_forecast,
        mode="lines",
        name="Forecast",
        line=dict(color="#dc2626", width=2.5, dash="dash"),
    )
)

fig.add_hline(
    y=abandonment_rate,
    line_dash="dot",
    line_color="#f59e0b",
    line_width=1.5,
    annotation_text=f"Abandonment: {abandonment_rate} bbl/d",
    annotation_position="top left",
    annotation_font_color="#f59e0b",
)

yaxis_type = "log" if y_scale == "Logarithmic" else "linear"

fig.update_layout(
    title=dict(text="Production Decline Curve Analysis", font=dict(size=20)),
    xaxis_title="Time (Months)",
    yaxis_title="Production Rate (bbl/day)",
    yaxis_type=yaxis_type,
    template="plotly_dark",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=13),
    ),
    height=560,
    margin=dict(l=60, r=30, t=80, b=60),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)


# Metrics
st.markdown("### Optimized Parameters & EUR")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Initial Rate (qi)", f"{qi_opt:,.1f} bbl/d")
with c2:
    st.metric("b-Factor", f"{b_opt:.4f}")
with c3:
    st.metric("Decline Rate (Di)", f"{Di_opt:.4f} /month")
with c4:
    if eur >= 1_000_000:
        st.metric("EUR", f"{eur / 1_000_000:,.2f} MMbbl")
    else:
        st.metric("EUR", f"{eur:,.0f} bbl")
