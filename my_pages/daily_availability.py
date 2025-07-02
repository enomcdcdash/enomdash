import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utils.data_loader import (
    load_daily_availability_regional,
    load_daily_availability_nop
)

#st.title("📊 Daily Availability Dashboard")

# --- Load Data Once ---
@st.cache_data
def load_all_data():
    return (
        load_daily_availability_regional(),
        load_daily_availability_nop(),
    )

with st.spinner("🔄 Loading data..."):
    df_regional, df_nop = load_all_data()


def app_tab1():
    st.subheader("📍 Regional Level")

    if df_regional.empty:
        st.warning("No regional data available.")
        return

    # Ensure Date is datetime
    df_regional["Date"] = pd.to_datetime(df_regional["Date"], errors='coerce')

    # Drop invalid rows
    df_clean = df_regional.dropna(subset=["Date", "Availability (Ave)", "regional"]).copy()

    # Sort by Date
    df_clean.sort_values(by="Date", inplace=True)

    # --- Date Range Filter ---
    min_date = df_clean["Date"].min()
    max_date = df_clean["Date"].max()

    date_range = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df_clean[(df_clean["Date"] >= pd.to_datetime(start_date)) & 
                               (df_clean["Date"] <= pd.to_datetime(end_date))]
    else:
        df_filtered = df_clean

    # --- Plot Chart ---
    fig = px.line(
        df_filtered,
        x="Date",
        y="Availability (Ave)",
        color="regional",
        markers=True,
        title="Daily Availability by Regional"
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Availability (%)",
        height=500,
        legend_title="Regional",
        xaxis=dict(
            tickformat="%d-%b-%y",
            tickmode="linear",
            dtick=432000000,  # every 5 days
            tickangle=-45,
            range=[df_filtered["Date"].min(), df_filtered["Date"].max()]  # 👈 restrict axis range
        )
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab2():
    st.subheader("📊 NOP Level Availability")

    df = load_daily_availability_nop()
    if df.empty:
        st.warning("No NOP-level daily data available.")
        return

    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.dropna(subset=["Date", "Availability (Ave)"])
    df.sort_values("Date", inplace=True)

    # --- Column Filters in One Row ---
    col_date, col1, col2, col3 = st.columns(4)

    with col_date:
        min_date = df["Date"].min()
        max_date = df["Date"].max()
        selected_date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range_tab2"  # 👈 unique key to avoid conflict
        )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

    with col1:
        area_options = ["All"] + sorted(df["area"].dropna().unique())
        selected_area = st.selectbox("Select Area", area_options)

    area_filtered_df = df if selected_area == "All" else df[df["area"] == selected_area]

    with col2:
        regional_options = ["All"] + sorted(area_filtered_df["regional"].dropna().unique())
        selected_regional = st.selectbox("Select Regional", regional_options)

    regional_filtered_df = (
        area_filtered_df if selected_regional == "All"
        else area_filtered_df[area_filtered_df["regional"] == selected_regional]
    )

    with col3:
        networksite_options = ["All"] + sorted(regional_filtered_df["networksite"].dropna().unique())
        selected_networksite = st.selectbox("Select Network Site", networksite_options)

    final_df = (
        regional_filtered_df if selected_networksite == "All"
        else regional_filtered_df[regional_filtered_df["networksite"] == selected_networksite]
    )

    if final_df.empty:
        st.warning("No data available for selected filters.")
        return

    # --- Dynamic Title ---
    title = "Daily Availability"
    if selected_regional != "All":
        title += f" - {selected_regional}"
    if selected_networksite != "All":
        title += f" / {selected_networksite}"

    # --- Line Chart ---
    fig = px.line(
        final_df,
        x="Date",
        y="Availability (Ave)",
        color="networksite" if selected_networksite == "All" else None,
        markers=True,
        #text=final_df["Availability (Ave)"].round(2).astype(str),
        title=title
    )

    #fig.update_traces(
    #    textposition="bottom center",
    #    textfont_size=12,
    #    marker=dict(size=8)
    #)

    fig.update_layout(
        xaxis=dict(
            tickformat="%d-%b-%y",
            tickmode="linear",
            dtick=432000000,  # every 5 days
            tickangle=-45,
            range=[final_df["Date"].min(), final_df["Date"].max()]
        ),
        yaxis=dict(
            title="Availability (%)",
            range=[90, 100]
        ),
        xaxis_title="Date",
        height=450,
        legend_title="Network Site" if selected_networksite == "All" else None
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab3():
    st.subheader("\U0001F4CA Daily Availability Summary")

    df = load_daily_availability_nop()
    if df.empty:
        st.warning("No NOP-level data available.")
        return

    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.dropna(subset=["Date"])

    # --- Filter UI ---
    col0, col1, col2, col3 = st.columns(4)

    with col0:
        min_date, max_date = df["Date"].min(), df["Date"].max()
        selected_date_range = st.date_input("Date Range", [min_date, max_date], key="tab4_daterange")

    filtered_df = df[(df["Date"] >= pd.to_datetime(selected_date_range[0])) & (df["Date"] <= pd.to_datetime(selected_date_range[1]))]

    with col1:
        area_options = ["All"] + sorted(filtered_df["area"].dropna().unique())
        selected_area = st.selectbox("Select Area", area_options, key="tab4_area")

    filtered_df = filtered_df if selected_area == "All" else filtered_df[filtered_df["area"] == selected_area]

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
        latest_date = filtered_df["Date"].max()
        latest_df = filtered_df[filtered_df["Date"] == latest_date]

        site_class_cols = ["Diamond", "Platinum", "Gold", "Silver", "Bronze"]
        site_class_counts = latest_df[site_class_cols].sum().reset_index()
        site_class_counts.columns = ["site_class", "count"]
        total_sites = site_class_counts["count"].sum()

        filter_title = f"Area: {selected_area} | Regional: {selected_regional} | Network Site: {selected_networksite}"
        full_title = (
            f"Site Class Distribution (Latest: {latest_date.strftime('%d-%b-%y')})<br>"
            f"<sup>{filter_title} — Total Sites: {total_sites:,}</sup>"
        )

        fig_pie = px.pie(
            site_class_counts,
            values="count",
            names="site_class",
            hole=0.3
        )

        fig_pie.update_traces(textinfo='label+percent+value')
        fig_pie.update_layout(title={"text": full_title, "x": 0, "xanchor": "left"}, title_font_size=16)
        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        summary = filtered_df.groupby("Date")[
            ["Ava_Diamond", "Ava_Platinum", "Ava_Gold", "Ava_Silver", "Ava_Bronze"]
        ].mean().reset_index()

        summary_long = summary.melt(id_vars="Date", 
                                     var_name="site_class", 
                                     value_name="Availability")
        summary_long["site_class"] = summary_long["site_class"].str.replace("Ava_", "")

        fig_line = px.line(
            summary_long,
            x="Date",
            y="Availability",
            color="site_class",
            markers=True,
            title="Daily Avg Availability"
        )

        fig_line.update_layout(
            xaxis=dict(dtick="D5", tickformat="%d-%b"),
            height=400
        )

        st.plotly_chart(fig_line, use_container_width=True)

    # Row 2: Achievement Chart
    st.markdown("---")
    st.subheader("\U0001F4C8 Availability %Site Achieved Trend")

    # Correct percentage calculation
    daily_sum = filtered_df.groupby("Date")[["Achieved", "Not Achieved"]].sum().reset_index()
    daily_sum["%Achieved"] = daily_sum["Achieved"] / (daily_sum["Achieved"] + daily_sum["Not Achieved"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=daily_sum["Date"],
            y=daily_sum["Achieved"],
            name="Achieved",
            marker_color="#2EA11A",
            opacity=0.6,
            text=daily_sum["Achieved"],
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="start",
            textfont=dict(color="black")
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(
            x=daily_sum["Date"],
            y=daily_sum["Not Achieved"],
            name="Not Achieved",
            marker_color="#FF8400",
            opacity=0.6,
            text=daily_sum["Not Achieved"],
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="end",
            textfont=dict(color="black")
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=daily_sum["Date"],
            y=daily_sum["%Achieved"],
            name="% Achieved",
            mode="lines+markers+text",
            line=dict(color="blue", width=3),
            text=daily_sum["%Achieved"].apply(lambda x: f"{x:.0%}"),
            textposition="bottom center",
            textfont=dict(color="blue", size=12, family="Arial", weight="bold")
        ),
        secondary_y=True
    )

    fig.update_layout(
        title={
            "text": f"Daily Achievement Summary<br><sup>{filter_title}</sup>",
            "x": 0.5,
            "xanchor": "center"
        },
        barmode="stack",
        height=460,
        xaxis=dict(dtick="D5", tickformat="%d-%b"),
        yaxis=dict(title="Number of Sites"),
        yaxis2=dict(title="% Achieved", tickformat=".0%", range=[0, 1]),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig, use_container_width=True)


def app():
    #st.title("📈 Daily Availability Dashboard")
    col1, col2 = st.columns([9, 1]) 

    with col1:
        st.title("📈 Daily Availability Dashboard")

    with col2:
        st.markdown("")  # Add spacing if needed
        if st.button("🔄 Refresh Data", help="Reload all ticketing data"):
            st.cache_data.clear()
            st.rerun()
            
    tab1, tab2, tab3 = st.tabs([
        "📍 Regional Level",
        "🏢 NOP Level",
        "📈 Availability Summary"
    ])

    with tab1:
        app_tab1()
    with tab2:
        app_tab2()
    with tab3:
        app_tab3()
