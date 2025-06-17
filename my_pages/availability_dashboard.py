import streamlit as st
import pandas as pd
from utils.data_loader import load_availability_regional_data, load_availability_nop_data, load_availability_site_data
import plotly.express as px
import random

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

def app():
    st.title("📊 Availability Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["Regional Level", "NOP Level", "Site Level", "Availability Summary"])

    with tab1:
        app_tab1()

    with tab2:
        app_tab2()

    with tab3:
        app_tab3()

    with tab4:
        st.info("Tab 4 (Summary) will be implemented later.")
