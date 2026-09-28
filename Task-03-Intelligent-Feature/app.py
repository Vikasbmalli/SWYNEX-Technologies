"""
Professional dashboard for the Electricity Bill Anomaly Detector.

Run:
    streamlit run app.py
"""

import matplotlib.pyplot as plt
import streamlit as st

from detector import BillError, analyze


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Electricity Bill Anomaly Detector",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# Custom theme / styling
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main application */
    .stApp {
        background:
            radial-gradient(circle at 85% 5%, rgba(37, 99, 235, 0.12), transparent 28%),
            radial-gradient(circle at 10% 20%, rgba(14, 165, 233, 0.08), transparent 25%),
            #08111f;
        color: #e5edf7;
    }

    .block-container {
        max-width: 1500px;
        padding: 1.5rem 2.5rem 2.5rem 2.5rem;
    }

    /* Hide Streamlit default chrome where possible */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent;}

    /* Header */
    .dashboard-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        padding: 22px 26px;
        margin-bottom: 20px;
        border: 1px solid #1d3048;
        border-radius: 18px;
        background: linear-gradient(135deg, #0e1c30 0%, #0b1728 100%);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .brand-icon {
        width: 52px;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        font-size: 28px;
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.30);
    }

    .brand-title {
        margin: 0;
        color: #f8fafc;
        font-size: 27px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .brand-subtitle {
        margin: 4px 0 0 0;
        color: #8fa3bb;
        font-size: 13px;
    }

    .status-pill {
        padding: 8px 14px;
        border-radius: 999px;
        color: #86efac;
        background: rgba(34, 197, 94, 0.10);
        border: 1px solid rgba(34, 197, 94, 0.25);
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #07101d;
        border-right: 1px solid #1b2b40;
    }

    section[data-testid="stSidebar"] > div {
        padding: 1.5rem 1.1rem;
    }

    .sidebar-title {
        color: #f8fafc;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .sidebar-text {
        color: #8296ae;
        font-size: 12px;
        line-height: 1.5;
        margin-bottom: 18px;
    }

    /* Cards */
    .metric-card {
        min-height: 118px;
        padding: 18px 20px;
        border-radius: 16px;
        border: 1px solid #1d3048;
        background: linear-gradient(145deg, #0e1c30, #0b1727);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
    }

    .metric-label {
        color: #8296ae;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 29px;
        font-weight: 800;
        margin-top: 8px;
    }

    .metric-note {
        color: #647b96;
        font-size: 11px;
        margin-top: 3px;
    }

    /* Section headings */
    .section-title {
        color: #f1f5f9;
        font-size: 17px;
        font-weight: 800;
        margin: 22px 0 10px 2px;
    }

    /* Streamlit widgets */
    .stSlider label, .stFileUploader label, .stCheckbox label {
        color: #d7e2ef !important;
        font-weight: 600 !important;
    }

    div[data-testid="stFileUploader"] {
        border: 1px dashed #2b4664;
        border-radius: 12px;
        background: #0b1727;
        padding: 6px;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border: 1px solid #1d3048;
        border-radius: 14px;
        overflow: hidden;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border: 0;
        border-radius: 10px;
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        color: white;
        font-weight: 700;
    }

    /* Mobile fallback */
    @media (max-width: 900px) {
        .block-container {
            padding: 1rem;
        }

        .dashboard-header {
            align-items: flex-start;
        }

        .status-pill {
            display: none;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="dashboard-header">
        <div class="brand">
            <div class="brand-icon">⚡</div>
            <div>
                <div class="brand-title">Electricity Bill Anomaly Detector</div>
                <div class="brand-subtitle">
                    AI-powered electricity consumption monitoring and anomaly analysis
                </div>
            </div>
        </div>
        <div class="status-pill">● DETECTOR ONLINE</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Sidebar controls
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Analysis Controls</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-text">Upload your monthly electricity data and adjust the expected anomaly sensitivity.</div>',
        unsafe_allow_html=True,
    )

    sensitivity = st.slider(
        "Sensitivity",
        min_value=0.01,
        max_value=0.30,
        value=0.10,
        step=0.01,
        format="%.2f",
        help="Expected share of unusual months.",
    )

    st.caption(f"Expected unusual months: approximately {sensitivity:.0%}")

    uploaded = st.file_uploader(
        "Upload monthly CSV",
        type="csv",
        help="Required columns: month, usage_kwh, bill_amount",
    )

    use_sample = st.checkbox(
        "Use included sample data",
        value=uploaded is None,
    )

    st.markdown("---")
    st.markdown("**Required CSV columns**")
    st.code("month\nusage_kwh\nbill_amount", language="text")

    st.markdown("---")
    st.caption("Detection engine: machine-learning based anomaly analysis")


source = uploaded if uploaded is not None else ("sample_bills.csv" if use_sample else None)


# -------------------------------------------------------------------
# Empty state
# -------------------------------------------------------------------
if source is None:
    st.markdown(
        """
        <div class="metric-card" style="text-align:center; padding:55px;">
            <div style="font-size:42px;">📊</div>
            <h2 style="color:#f8fafc;">No data loaded</h2>
            <p style="color:#8296ae;">
                Upload a CSV from the left panel to start electricity bill analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# -------------------------------------------------------------------
# Analysis
# -------------------------------------------------------------------
try:
    result, warnings = analyze(source, sensitivity)
except BillError as e:
    st.error(str(e))
    st.stop()


for warning in warnings:
    st.warning(warning)


flagged = result[result["is_anomaly"]].copy()
normal_count = len(result) - len(flagged)
total_count = len(result)
anomaly_rate = (len(flagged) / total_count * 100) if total_count else 0


# -------------------------------------------------------------------
# KPI cards
# -------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total Months</div>
            <div class="metric-value">{total_count}</div>
            <div class="metric-note">Records analyzed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Anomalies</div>
            <div class="metric-value">{len(flagged)}</div>
            <div class="metric-note">Unusual months detected</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Normal Months</div>
            <div class="metric-value">{normal_count}</div>
            <div class="metric-note">Within expected range</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Anomaly Rate</div>
            <div class="metric-value">{anomaly_rate:.1f}%</div>
            <div class="metric-note">Of all analyzed months</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# Main chart
# -------------------------------------------------------------------
st.markdown('<div class="section-title">Electricity Consumption Overview</div>', unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(14, 5.2))
fig.patch.set_facecolor("#0b1727")
ax.set_facecolor("#0b1727")

ax.plot(
    result["month"],
    result["usage_kwh"],
    color="#38bdf8",
    linewidth=2.5,
    marker="o",
    markersize=3.5,
    label="Usage (kWh)",
)

if len(flagged):
    ax.scatter(
        flagged["month"],
        flagged["usage_kwh"],
        color="#f43f5e",
        s=70,
        zorder=5,
        edgecolors="#ffffff",
        linewidths=0.8,
        label="Anomaly",
    )

ax.set_ylabel("Energy Usage (kWh)", color="#a8bad0", fontsize=10)
ax.set_xlabel("Month", color="#a8bad0", fontsize=10)
ax.tick_params(axis="both", colors="#8296ae", labelsize=9)
ax.grid(True, color="#1d3048", alpha=0.65, linewidth=0.8)

for spine in ax.spines.values():
    spine.set_color("#1d3048")

legend = ax.legend(
    loc="upper right",
    facecolor="#0e1c30",
    edgecolor="#1d3048",
    framealpha=1,
)
for text in legend.get_texts():
    text.set_color("#d7e2ef")

fig.autofmt_xdate()
plt.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)


# -------------------------------------------------------------------
# Detection summary
# -------------------------------------------------------------------
st.markdown(
    f"""
    <div class="section-title">
        Detected Anomalies
        <span style="color:#647b96;font-size:12px;font-weight:500;">
            &nbsp;•&nbsp; {len(flagged)} unusual month(s) out of {total_count}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(flagged):
    table = flagged[
        ["month", "usage_kwh", "bill_amount", "severity", "reason"]
    ].copy()

    table["month"] = table["month"].dt.strftime("%Y-%m")
    table.columns = [
        "Month",
        "Usage (kWh)",
        "Bill Amount",
        "Severity",
        "Detection Reason",
    ]

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        height=min(420, 80 + len(table) * 36),
    )
else:
    st.success("No unusual months found at the selected sensitivity.")


# -------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------
st.markdown(
    """
    <div style="
        margin-top:28px;
        padding-top:16px;
        border-top:1px solid #1d3048;
        text-align:center;
        color:#647b96;
        font-size:11px;">
        Electricity Bill Anomaly Detector &nbsp;•&nbsp; AI / Machine Learning Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)
