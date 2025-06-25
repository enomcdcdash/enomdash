import streamlit as st
import pandas as pd
from utils.data_loader import load_availability_regional_data, load_availability_nop_data, load_availability_site_data
import plotly.express as px
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.helpers import (
    summarize_availability_area,
    summarize_availability_regional,
    summarize_availability_nop,
    summarize_achievement_area,
    summarize_achievement_regional,
    summarize_achievement_nop,
    summarize_availability_overall,
    summarize_achievement_overall,
)

def app_tab1():
    st.subheader("📈 Regional Level Availability")

    df = load_availability_regional_data()
    if df.empty:
        st.warning("No regional data available.")
        return

    df.columns = df.columns.str.strip()
    df["Month"] = pd.to_datetime(df["Month"], format="%b-%y", errors='coerce')
    df = df.dropna(subset=["Month"])
    df.sort_values("Month", inplace=True)

    fig = px.line(
        df,
        x="Month",
        y="Availability (Ave)",
        color="regional",  # Optional: shows different lines per regional
        markers=True,
        text=df["Availability (Ave)"].round(2).astype(str),
        title="Monthly Availability by Regional"
    )

    fig.update_traces(
        textposition="bottom center",  # <-- Position label below marker
        textfont_size=12,
        marker=dict(size=8)
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%b-%y",  # Format: Jan-25
            dtick="M1"           # One tick per month
        ),
        yaxis=dict(
            title="Availability (%)",
            range=[95, 100]  # <-- Set Y-axis range here
        ),
        xaxis_title="Month",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab2():
    st.subheader("📊 NOP Level Availability")

    df = load_availability_nop_data()
    if df.empty:
        st.warning("No NOP-level data available.")
        return

    df.columns = df.columns.str.strip()
    df["Month"] = pd.to_datetime(df["Month"], format="%b-%y", errors='coerce')
    df = df.dropna(subset=["Month"])
    df.sort_values("Month", inplace=True)

    # Filter row with 3 columns
    col1, col2, col3 = st.columns(3)

    with col1:
        area_options = ["All"] + sorted(df["area"].dropna().unique())
        selected_area = st.selectbox("Select Area", area_options)

    if selected_area == "All":
        area_filtered_df = df.copy()
    else:
        area_filtered_df = df[df["area"] == selected_area]

    with col2:
        regional_options = ["All"] + sorted(area_filtered_df["regional"].dropna().unique())
        selected_regional = st.selectbox("Select Regional", regional_options)

    if selected_regional == "All":
        regional_filtered_df = area_filtered_df.copy()
    else:
        regional_filtered_df = area_filtered_df[area_filtered_df["regional"] == selected_regional]

    with col3:
        networksite_options = ["All"] + sorted(regional_filtered_df["networksite"].dropna().unique())
        selected_networksite = st.selectbox("Select Network Site", networksite_options)

    if selected_networksite == "All":
        final_df = regional_filtered_df.copy()
    else:
        final_df = regional_filtered_df[regional_filtered_df["networksite"] == selected_networksite]

    if final_df.empty:
        st.warning("No data available for selected filters.")
        return

    title = "Monthly Availability"
    if selected_regional != "All":
        title += f" - {selected_regional}"
    if selected_networksite != "All":
        title += f" / {selected_networksite}"

    fig = px.line(
        final_df,
        x="Month",
        y="Availability (Ave)",
        color="networksite" if selected_networksite == "All" else None,
        markers=True,
        text=final_df["Availability (Ave)"].round(2).astype(str),  # <-- Add labels as text
        title=title  # <-- Use dynamic title here
    )

    fig.update_traces(
        textposition="bottom center",  # <-- Position label below marker
        textfont_size=12,
        marker=dict(size=8)
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%b-%y",
            dtick="M1"
        ),
        yaxis=dict(
            title="Availability (%)",
            range=[90, 100]  # <-- Set Y-axis range here
        ),
        xaxis_title="Month",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab3():
    st.subheader("📍 Site Level Availability")

    df = load_availability_site_data()
    if df.empty:
        st.warning("No Site-level data available.")
        return

    df.columns = df.columns.str.strip()
    df["Month"] = pd.to_datetime(df["Month"], format="%b-%y", errors="coerce")
    df = df.dropna(subset=["Month"])
    df.sort_values("Month", inplace=True)

    # --- Cascading Filters with 'All' options ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        area_options = ["All"] + sorted(df["area"].dropna().unique())
        selected_area = st.selectbox("Select Area", area_options, key="site_area")

    filtered_df = df if selected_area == "All" else df[df["area"] == selected_area]

    with col2:
        regional_options = ["All"] + sorted(filtered_df["regional"].dropna().unique())
        selected_regional = st.selectbox("Select Regional", regional_options, key="site_regional")

    filtered_df = filtered_df if selected_regional == "All" else filtered_df[filtered_df["regional"] == selected_regional]

    with col3:
        networksite_options = ["All"] + sorted(filtered_df["networksite"].dropna().unique())
        selected_networksite = st.selectbox("Select Network Site", networksite_options, key="site_networksite")

    filtered_df = filtered_df if selected_networksite == "All" else filtered_df[filtered_df["networksite"] == selected_networksite]

    with col4:
        site_id_list = sorted(filtered_df["site_id"].dropna().unique())
        site_id_options = ["All"] + site_id_list

        # Initialize session state for site_id
        if "default_site_id" not in st.session_state:
            st.session_state.default_site_id = random.choice(site_id_list) if site_id_list else "All"

        selected_site_id = st.selectbox(
            "Select Site ID",
            site_id_options,
            index=site_id_options.index(st.session_state.default_site_id) if st.session_state.default_site_id in site_id_options else 0,
            key="site_id"
        )
    final_df = filtered_df if selected_site_id == "All" else filtered_df[filtered_df["site_id"] == selected_site_id]

    if final_df.empty:
        st.warning("No data available for selected filters.")
        return

    # --- Line Chart: Month vs Availability (Ave) + Target (%) ---
    fig = px.line(
        final_df,
        x="Month",
        y=["Availability (Ave)", "target (%)"],
        markers=True,
        labels={"value": "Availability (%)", "variable": "Legend"},
        title=f"Monthly Availability for {selected_site_id if selected_site_id != 'All' else 'All Sites'}"
    )

    # Add data point labels below markers
    for trace in fig.data:
        trace.update(mode="lines+markers+text")
        trace.update(text=final_df[trace.name].round(2).astype(str))
        trace.update(textposition="bottom center")

        # Customize target line: red + dashed
        if trace.name == "target (%)":
            trace.update(line=dict(dash="dash", color="red"))

    # Customize chart layout
    fig.update_layout(
        xaxis=dict(
            tickformat="%b-%y",
            dtick="M1"
        ),
        xaxis_title="Month",
        yaxis_title="Availability (%)",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

# --- In availability_dashboard.py tab4 ---
def app_tab4():
    st.subheader("\U0001F4CA Availability Summary")

    df = load_availability_site_data()
    if df.empty:
        st.warning("No site-level data available.")
        return

    df.columns = df.columns.str.strip()
    df["Month"] = pd.to_datetime(df["Month"], format="%b-%y", errors='coerce')
    df = df.dropna(subset=["Month"])

    # --- Filter UI ---
    col1, col2, col3 = st.columns(3)

    with col1:
        area_options = ["All"] + sorted(df["area"].dropna().unique())
        selected_area = st.selectbox("Select Area", area_options, key="tab4_area")

    filtered_df = df if selected_area == "All" else df[df["area"] == selected_area]

    with col2:
        regional_options = ["All"] + sorted(filtered_df["regional"].dropna().unique())
        selected_regional = st.selectbox("Select Regional", regional_options, key="tab4_regional")

    filtered_df = filtered_df if selected_regional == "All" else filtered_df[filtered_df["regional"] == selected_regional]

    with col3:
        networksite_options = ["All"] + sorted(filtered_df["networksite"].dropna().unique())
        selected_networksite = st.selectbox("Select Network Site", networksite_options, key="tab4_networksite")

    filtered_df = filtered_df if selected_networksite == "All" else filtered_df[filtered_df["networksite"] == selected_networksite]

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
        return

    # Row 1: Pie chart and Avg Availability line chart
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        latest_month = filtered_df["Month"].max()
        latest_df = filtered_df[filtered_df["Month"] == latest_month]

        site_class_counts = latest_df["site_class"].value_counts().reset_index()
        site_class_counts.columns = ["site_class", "count"]
        total_sites = site_class_counts["count"].sum()

        # Title and subtitle with formatting
        filter_title = f"Area: {selected_area} | Regional: {selected_regional} | Network Site: {selected_networksite}"
        full_title = (
            f"Site Class Distribution (Latest: {latest_month.strftime('%b-%y')})<br>"
            f"<sup>{filter_title} — Total Sites: {total_sites:,}</sup>"
        )

        fig_pie = px.pie(
            site_class_counts,
            values="count",
            names="site_class",
            hole=0.3
        )

        fig_pie.update_traces(textinfo='label+percent+value')

        # Properly center the title and subtitle
        fig_pie.update_layout(
            title={
                "text": full_title,
                "x": 0,
                "xanchor": "left"
            },
            title_font_size=16
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        # Availability logic based on filters
        if selected_area == "All" and selected_regional == "All" and selected_networksite == "All":
            summary = summarize_availability_overall(filtered_df)
            title = "Monthly Avg Availability – All Areas"
        elif selected_networksite != "All":
            summary = summarize_availability_nop(filtered_df)
            title = f"Monthly Avg Availability – Network Site: {selected_networksite}"
        elif selected_regional != "All":
            summary = summarize_availability_regional(filtered_df)
            title = f"Monthly Avg Availability – Regional: {selected_regional}"
        elif selected_area != "All":
            summary = summarize_availability_area(filtered_df)
            title = f"Monthly Avg Availability – Area: {selected_area}"
        else:
            summary = summarize_availability_area(filtered_df)
            title = "Monthly Avg Availability – All Areas"

        fig_line = px.line(
            summary,
            x="Month",
            y="Availability",
            color="site_class",
            markers=True,
            title=title
        )
        fig_line.update_layout(xaxis=dict(tickformat="%b-%y", dtick="M1"), height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    # Row 2: Achievement chart
    st.markdown("---")
    st.subheader("\U0001F4C8 Availability %Site Achieved Trend")

    if selected_area == "All" and selected_regional == "All" and selected_networksite == "All":
        achievement_summary = summarize_achievement_overall(filtered_df)
    elif selected_networksite != "All":
        achievement_summary = summarize_achievement_nop(filtered_df)
    elif selected_regional != "All":
        achievement_summary = summarize_achievement_regional(filtered_df)
    elif selected_area != "All":
        achievement_summary = summarize_achievement_area(filtered_df)
    else:
        achievement_summary = summarize_achievement_area(filtered_df)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Achieved bar
    fig.add_trace(
        go.Bar(
            x=achievement_summary["Month"],
            y=achievement_summary["Achieved_Count"],
            name="Achieved",
            marker_color="#2EA11A",
            opacity=0.6,
            text=achievement_summary["Achieved_Count"],
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="start",
            textfont=dict(color="black")
        ),
        secondary_y=False
    )

    # Not Achieved bar
    fig.add_trace(
        go.Bar(
            x=achievement_summary["Month"],
            y=achievement_summary["Not_Achieved_Count"],
            name="Not Achieved",
            marker_color="#FF8400",
            opacity=0.6,
            text=achievement_summary["Not_Achieved_Count"],
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="end",
            textfont=dict(color="black")
        ),
        secondary_y=False
    )

    # Achievement line
    fig.add_trace(
        go.Scatter(
            x=achievement_summary["Month"],
            y=achievement_summary["Achievement"],
            name="% Achieved",
            mode="lines+markers+text",  # Add 'text' to show labels
            line=dict(color="blue", width=3),
            text=achievement_summary["Achievement"].apply(lambda x: f"{x:.0%}"),
            textposition="bottom center",
            textfont=dict(color="blue", size=12, family="Arial", weight="bold")  # color + bold
        ),
        secondary_y=True
    )

    # Compose dynamic title
    filter_info = f"Area: {selected_area} | Regional: {selected_regional} | Network Site: {selected_networksite}"
    title_text = f"Monthly Achievement Summary<br><sup>{filter_info}</sup>"

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "xanchor": "center"
        },
        barmode="stack",
        height=460,
        xaxis=dict(tickformat="%b-%y", dtick="M1"),
        yaxis=dict(title="Number of Sites"),
        yaxis2=dict(title="% Achieved", tickformat=".0%", range=[0, 1]),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig, use_container_width=True)

def app():
    st.title("📊 Monthly Availability Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["Regional Level", "NOP Level", "Site Level", "Availability Summary"])

    with tab1:
        app_tab1()

    with tab2:
        app_tab2()

    with tab3:
        app_tab3()

    with tab4:
        app_tab4()
