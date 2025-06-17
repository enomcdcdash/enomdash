import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_ticketing_data

# 2. Add takeover/visit charts function FIRST
def add_takeover_visit_charts(df_d, df_m, st):
    chart_config = [
        {"title": "Takeover", "daily": "IM-TO-Daily", "mtd": "IM-%TO-MTD", "target": 80},
        {"title": "Takeover High", "daily": "IM-TO-High-Daily", "mtd": "IM-%TO-High-MTD", "target": 80},
        {"title": "Takeover Low", "daily": "IM-TO-Low-Daily", "mtd": "IM-%TO-Low-MTD", "target": 80},
        {"title": "Site Visit", "daily": "IM-Visit-Daily", "mtd": "IM-%Visit-MTD", "target": 90},
    ]

    for i in range(0, len(chart_config), 2):
        col1, col2 = st.columns(2)
        for col, cfg in zip([col1, col2], chart_config[i:i+2]):
            daily_col = cfg["daily"]
            mtd_col = cfg["mtd"]
            target_val = cfg["target"]
            title = cfg["title"]

            if daily_col not in df_d.columns or mtd_col not in df_m.columns:
                col.warning(f"Missing required columns for {title}")
                continue

            df_d = df_d.sort_values("Date")
            df_m = df_m.sort_values("Date").copy()

            # Clean percentage column if needed
            if df_m[mtd_col].dtype == 'object':
                df_m[mtd_col] = df_m[mtd_col].str.replace('%', '').astype(float)

            fig = go.Figure()

            # Bar chart: daily count (right Y-axis)
            fig.add_trace(go.Bar(
                x=df_d["Date"],
                y=df_d[daily_col],
                name="Daily (count)",
                yaxis="y2",
                #marker_color="#FFAA00",  # orange
                marker_color="#2FB1F2",
                opacity=0.6,
                text=df_d[daily_col],
                textposition="inside",
                insidetextanchor="start"
            ))


            # Line chart: MTD (%) trend (left Y-axis)
            fig.add_trace(go.Scatter(
                x=df_m["Date"],
                y=df_m[mtd_col] * 100,
                mode="lines+markers",
                name="MTD (%)",
                line=dict(color="#2CA02C", width=3),
                yaxis="y1"
            ))

            # Target line (left Y-axis)
            fig.add_trace(go.Scatter(
                x=df_m["Date"],
                y=[target_val] * len(df_m),
                mode="lines",
                name="Target",
                line=dict(color="#D62728", dash="dash"),
                yaxis="y1"
            ))

            fig.update_layout(
                title=f"{title} Performance",
                xaxis=dict(title="Date"),
                yaxis=dict(
                    title="Percentage (%)",
                    range=[0, 100],
                    showgrid=False
                ),
                yaxis2=dict(
                    title="Daily Count",
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                height=350,
                margin=dict(t=30, b=30),
                legend=dict(x=1, y=1.2, xanchor="right", orientation="h"),
            )

            col.plotly_chart(fig, use_container_width=True)

def app_tab1():
    st.header("📌 Incident - MTTR P90 by Severity")

    # Load and prepare data
    df_daily, df_mtd = load_ticketing_data()

    if df_daily.empty or df_mtd.empty:
        st.warning("Ticketing data not found or empty.")
        return

    # Extract unique filter values
    months = df_daily["Month"].dropna().unique().tolist()
    years = sorted(df_daily["Year"].dropna().unique())
    regionals = df_daily["Regional"].dropna().unique().tolist()
    nops = df_daily["NOP"].dropna().unique().tolist()

    import calendar

    # Sort months using calendar module
    month_order = list(calendar.month_name)[1:]  # ['January', ..., 'December']
    months = sorted(set(df_daily["Month"].dropna()), key=lambda x: month_order.index(x))

    years = sorted(df_daily["Year"].dropna().unique())
    regionals = sorted(df_daily["Regional"].dropna().unique())

    # Select latest month by calendar order
    latest_month = max(months, key=lambda x: month_order.index(x))

    # Regional selection
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        selected_month = st.selectbox("Month", months, index=months.index(latest_month))
    with c2:
        selected_year = st.selectbox("Year", years)
    with c3:
        selected_regional = st.selectbox("Regional", regionals)

    # Cascading: show only NOPs under selected regional
    filtered_nops = df_daily[df_daily["Regional"] == selected_regional]["NOP"].dropna().unique()
    filtered_nops = sorted(filtered_nops)

    with c4:
        selected_nop = st.selectbox("NOP", filtered_nops)

    # Apply filters
    df_d = df_daily[
        (df_daily["Month"] == selected_month) &
        (df_daily["Year"] == selected_year) &
        (df_daily["Regional"] == selected_regional) &
        (df_daily["NOP"] == selected_nop)
    ].copy()

    df_m = df_mtd[
        (df_mtd["Month"] == selected_month) &
        (df_mtd["Year"] == selected_year) &
        (df_mtd["Regional"] == selected_regional) &
        (df_mtd["NOP"] == selected_nop)
    ].copy()

    severity_map = {
        "Critical": {"daily": "IM-MTTRP90-Critical-Daily", "mtd": "IM-Critical-MTD", "target": 4},
        "Major": {"daily": "IM-MTTRP90-Major-Daily", "mtd": "IM-Major-MTD", "target": 8},
        "Minor": {"daily": "IM-MTTRP90-Minor-Daily", "mtd": "IM-Minor-MTD", "target": 10},
        "Low": {"daily": "IM-MTTRP90-Low-Daily", "mtd": "IM-Low-MTD", "target": 13},
    }

    severities = list(severity_map.keys())
    for i in range(0, len(severities), 2):
        col1, col2 = st.columns(2)
        for col, sev in zip([col1, col2], severities[i:i+2]):
            daily_col = severity_map[sev]["daily"]
            mtd_col = severity_map[sev]["mtd"]
            target_val = severity_map[sev]["target"]

            if df_d.empty:
                col.warning(f"No daily data for {sev}")
                continue
            if df_m.empty:
                col.warning(f"No MTD data for {sev}")
                continue
            if daily_col not in df_d.columns or mtd_col not in df_m.columns:
                col.warning(f"Missing required columns for {sev}")
                continue

            fig = go.Figure()

            # Add shaded area under the Daily line (light blue fill)
            fig.add_trace(go.Scatter(
                x=df_d["Date"],
                y=df_d[daily_col],
                mode="lines",
                name="Daily (Shaded)",
                line=dict(color="rgba(0, 123, 255, 0.3)", width=0),
                fill='tozeroy',
                fillcolor='rgba(47, 177, 242, 0.4)',
                hoverinfo='skip',
                showlegend=False
            ))

            # Add actual Daily line (blue line on top of the shading)
            fig.add_trace(go.Scatter(
                x=df_d["Date"],
                y=df_d[daily_col],
                mode="lines+markers",
                name="Daily",
                line=dict(color="rgba(0, 123, 255, 1)", width=2),
            ))

            # Add MTD line (solid green, thick)
            fig.add_trace(go.Scatter(
                x=df_m["Date"],
                y=df_m[mtd_col],
                mode="lines+markers",
                name="MTD",
                line=dict(color="green", width=3),
            ))

            # Add Target line (dashed red)
            fig.add_trace(go.Scatter(
                x=df_d["Date"],
                y=[target_val] * len(df_d),
                mode="lines",
                name="Target",
                line=dict(color="red", dash="dash"),
            ))

            fig.update_layout(
                title=f"{sev} MTTR P90",
                xaxis_title="Date",
                yaxis_title="Hours",
                height=350,
                margin=dict(t=30, b=30),
                hovermode="x unified",
            )

            col.plotly_chart(fig, use_container_width=True)

    #st.markdown("---")
    #st.subheader("📌 Additional Ticketing KPIs")

    add_takeover_visit_charts(df_d, df_m, st)


def app_tab2():
    st.header("📈 Event - MTTR P90 & Operational Performance")

    # Load data
    df_daily, df_mtd = load_ticketing_data()

    if df_daily.empty or df_mtd.empty:
        st.warning("Ticketing data not found or empty.")
        return

    from datetime import datetime

    # Extract unique filter values
    months = sorted(df_daily["Month"].dropna().unique().tolist(), key=lambda x: datetime.strptime(x, "%B"))
    years = sorted(df_daily["Year"].dropna().unique())
    regionals = sorted(df_daily["Regional"].dropna().unique().tolist())

    # Default month = latest
    default_month = months[-1] if months else None

    # Filter UI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        selected_month = st.selectbox("Month", months, index=months.index(default_month), key="month_tab2")
    with c2:
        selected_year = st.selectbox("Year", years, key="year_tab2")
    with c3:
        selected_regional = st.selectbox("Regional", regionals, key="regional_tab2")

    # Cascading NOP
    available_nops = df_daily[df_daily["Regional"] == selected_regional]["NOP"].dropna().unique().tolist()
    with c4:
        selected_nop = st.selectbox("NOP", available_nops, key="nop_tab2")

    # Filtered data
    df_d = df_daily[
        (df_daily["Month"] == selected_month) &
        (df_daily["Year"] == selected_year) &
        (df_daily["Regional"] == selected_regional) &
        (df_daily["NOP"] == selected_nop)
    ].copy()

    df_m = df_mtd[
        (df_mtd["Month"] == selected_month) &
        (df_mtd["Year"] == selected_year) &
        (df_mtd["Regional"] == selected_regional) &
        (df_mtd["NOP"] == selected_nop)
    ].copy()

    severity_map = {
        "Critical": {"daily": "EM-MTTRP90-Critical-Daily", "mtd": "EM-Critical-MTD", "target": 2},
        "Major": {"daily": "EM-MTTRP90-Major-Daily", "mtd": "EM-Major-MTD", "target": 4},
        "Minor": {"daily": "EM-MTTRP90-Minor-Daily", "mtd": "EM-Minor-MTD", "target": 15},
        "Low": {"daily": "EM-MTTRP90-Low-Daily", "mtd": "EM-Low-MTD", "target": 48},
    }

    severities = list(severity_map.keys())
    for i in range(0, len(severities), 2):
        col1, col2 = st.columns(2)
        for col, sev in zip([col1, col2], severities[i:i+2]):
            daily_col = severity_map[sev]["daily"]
            mtd_col = severity_map[sev]["mtd"]
            target_val = severity_map[sev]["target"]

            if daily_col not in df_d.columns or mtd_col not in df_m.columns:
                col.warning(f"Missing data for {sev}")
                continue

            try:
                mtd_value = df_m[mtd_col].iloc[0]
            except IndexError:
                col.warning(f"No MTD value for {sev}")
                continue

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_d["Date"], y=df_d[daily_col],
                                     mode="lines+markers", name="Daily",
                                     line=dict(color="#2FB1F2"),
                                     fill="tozeroy", fillcolor="rgba(47, 177, 242, 0.2)"))
            fig.add_trace(go.Scatter(x=df_d["Date"], y=df_m[mtd_col],
                                     mode="lines+markers", name="MTD",
                                     line=dict(color="green", width=3)))
            fig.add_trace(go.Scatter(x=df_d["Date"], y=[target_val] * len(df_d),
                                     mode="lines", name="Target",
                                     line=dict(color="red", dash="dash")))

            fig.update_layout(
                title=f"{sev} MTTR P90",
                xaxis_title="Date",
                yaxis_title="Hours",
                height=350,
                margin=dict(t=30, b=30),
                legend=dict(x=1, y=1.2, xanchor="right", orientation="h")
            )
            col.plotly_chart(fig, use_container_width=True)

    # Clean percentage columns in MTD
    percent_cols = ["EM-%TO-MTD", "EM-%TO-High-MTD", "EM-%TO-Low-MTD", "EM-%Visit-MTD"]
    for col in percent_cols:
        if col in df_m.columns:
            df_m[col] = df_m[col].astype(str).str.replace('%', '', regex=False)
            df_m[col] = pd.to_numeric(df_m[col], errors='coerce')

    # Add takeover + visit charts
    chart_specs = [
        ("Takeover", "EM-TO-Daily", "EM-%TO-MTD", 80),
        ("Takeover High", "EM-TO-High-Daily", "EM-%TO-High-MTD", 80),
        ("Takeover Low", "EM-TO-Low-Daily", "EM-%TO-Low-MTD", 80),
        ("Site Visit", "EM-Visit-Daily", "EM-%Visit-MTD", 90),
    ]

    for i in range(0, len(chart_specs), 2):
        col1, col2 = st.columns(2)
        for col, (title, daily_col, mtd_col, target_val) in zip([col1, col2], chart_specs[i:i+2]):
            if daily_col not in df_d.columns or mtd_col not in df_m.columns:
                col.warning(f"Missing columns for {title}")
                continue

            if df_m.empty or df_d.empty:
                col.warning(f"No data available for {title}")
                continue

            try:
                mtd_series = df_m[mtd_col].astype(float) * 100
            except Exception as e:
                col.warning(f"Invalid MTD % format for {title}: {e}")
                continue

            fig = go.Figure()

            # Bar chart: daily count (right Y-axis)
            fig.add_trace(go.Bar(
                x=df_d["Date"],
                y=df_d[daily_col],
                name="Daily (count)",
                yaxis="y2",
                marker_color="#2FB1F2",
                opacity=0.6,
                text=df_d[daily_col],
                textposition="outside",
                insidetextanchor="start",
                textfont=dict(size=10),
            ))

            # Line: MTD percentage (left Y-axis)
            fig.add_trace(go.Scatter(
                x=df_m["Date"],
                y=mtd_series,
                name="MTD (%)",
                mode="lines+markers",
                line=dict(color="green", width=3)
            ))

            # Line: Target (left Y-axis)
            fig.add_trace(go.Scatter(
                x=df_d["Date"],
                y=[target_val] * len(df_d),
                name="Target",
                mode="lines",
                line=dict(color="red", dash="dash")
            ))

            fig.update_layout(
                title=f"{title} Performance",
                xaxis=dict(title="Date"),
                yaxis=dict(title="Percentage (%)", range=[0, 100], showgrid=False),
                yaxis2=dict(title="Daily Count", overlaying='y', side='right', showgrid=False),
                height=350,
                margin=dict(t=30, b=30),
                legend=dict(x=1, y=1.2, xanchor="right", orientation="h")
            )

            col.plotly_chart(fig, use_container_width=True)



def app():
    st.header("🛠️ Ticketing Dashboard")

    tab1, tab2 = st.tabs(["📍 Incident", "📍 Event"])
    with tab1:
        app_tab1()
    with tab2:
        app_tab2()

