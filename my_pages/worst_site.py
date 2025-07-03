import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from utils.data_loader import load_worst_site_data

def app_tab1():
    st.subheader("🧁 Worst Site Distribution")

    df = load_worst_site_data()
    if df.empty:
        st.warning("No data available.")
        return

    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["Site ID"])

    # ✅ Filter only AREA1 and AREA3
    df = df[df["Area"].isin(["AREA1", "AREA3"])]

    if df.empty:
        st.info("No data available for AREA1 and AREA3.")
        return

    # --- Add filters ---
    col1, col2, col3 = st.columns(3)

    with col1:
        area_options = ["All"] + sorted(df["Area"].dropna().unique())
        area_selected = st.selectbox("Select Area", area_options, key="filter_area")

    with col2:
        filtered_df = df if area_selected == "All" else df[df["Area"] == area_selected]
        regional_options = ["All"] + sorted(filtered_df["Regional"].dropna().unique())
        regional_selected = st.selectbox("Select Regional", regional_options, key="filter_regional")

    with col3:
        filtered_df = filtered_df if regional_selected == "All" else filtered_df[filtered_df["Regional"] == regional_selected]
        nop_options = ["All"] + sorted(filtered_df["NOP"].dropna().unique())
        nop_selected = st.selectbox("Select NOP", nop_options, key="filter_nop")

    # --- Apply filters ---
    if area_selected != "All":
        df = df[df["Area"] == area_selected]
    if regional_selected != "All":
        df = df[df["Regional"] == regional_selected]
    if nop_selected != "All":
        df = df[df["NOP"] == nop_selected]

    if df.empty:
        st.info("No data available for the selected filters.")
        return

    # --- Show total site count ---
    total_sites = df["Site ID"].nunique()
    st.markdown(f"""
        <div style="font-size: 22px; font-weight: bold; color: #2F5597;">
            Total Sites: {total_sites:,}
        </div>
    """, unsafe_allow_html=True)

    # --- Pie Charts ---
    col1, col2, col3 = st.columns(3)

    with col1:
        if "Regional" in df.columns:
            summary = df.groupby("Regional")["Site ID"].nunique().reset_index(name="Site Count")
            fig = px.pie(summary, names="Regional", values="Site Count", title="Breakdown By Regional", hole=0.3)
            fig.update_traces(textinfo="label+percent+value")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "Class S1 2025" in df.columns:
            summary = df.groupby("Class S1 2025")["Site ID"].nunique().reset_index(name="Site Count")
            fig = px.pie(summary, names="Class S1 2025", values="Site Count", title="Breakdown By Site Class", hole=0.3)
            fig.update_traces(textinfo="label+percent+value")
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        if "Prio" in df.columns:
            summary = df.groupby("Prio")["Site ID"].nunique().reset_index(name="Site Count")
            fig = px.pie(summary, names="Prio", values="Site Count", title="Breakdown By Priority", hole=0.3)
            fig.update_traces(textinfo="label+percent+value")
            st.plotly_chart(fig, use_container_width=True)

    # --- Stacked Bar Chart ---
    st.markdown("---")
    st.markdown("### 📊 Weekly Site Status (Open vs Closed vs Reopen)")

    akumulasi_columns = [col for col in df.columns if col.startswith("Akumulasi W")]
    df_status = df[["Site ID"] + akumulasi_columns].copy()

    status_long = df_status.melt(
        id_vars="Site ID",
        var_name="Week",
        value_name="Status"
    ).dropna(subset=["Status"])

    status_long["Week"] = status_long["Week"].str.replace("Akumulasi ", "", regex=False)
    valid_statuses = ["Open", "Closed", "Reopen"]
    status_long = status_long[status_long["Status"].isin(valid_statuses)]

    status_counts = (
        status_long.groupby(["Week", "Status"])["Site ID"]
        .count()
        .reset_index(name="Count")
    )

    fig = px.bar(
        status_counts,
        x="Week",
        y="Count",
        color="Status",
        title="Open vs Closed vs Reopen Sites by Week",
        barmode="stack",
        text_auto=True,
        color_discrete_map={
            "Open": "#d62728",
            "Closed": "#2ca02c",
            "Reopen": "#1f77b4"
        }
    )
    fig.update_traces(opacity=0.7)
    fig.update_traces(textfont=dict(size=14, family="Arial", color="white"))
    fig.update_layout(
        yaxis_title="Site Count",
        xaxis_title="Week",
        legend_title="Status",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab2():
    st.subheader("📍 Site Tracking Over Time")

    df = load_worst_site_data()

    if df.empty:
        st.warning("No data available.")
        return

    # Clean columns and filter Area 1 and 3
    df.columns = df.columns.str.strip()
    df = df[df["Area"].isin(["AREA1", "AREA3"])]

    # Select only W columns + metadata
    week_cols = sorted([col for col in df.columns if re.match(r"Avail W\d{2}", col)])
    meta_cols = ["Site ID", "Area", "Regional", "NOP", "Target"]
    if "Class S1 2025" in df.columns:
        meta_cols.append("Class S1 2025")

    if not all(col in df.columns for col in meta_cols):
        st.warning("Missing required columns for filtering or plotting.")
        return

    df = df[meta_cols + week_cols].dropna(subset=["Site ID"])

    df_long = df.melt(
        id_vars=meta_cols,
        value_vars=week_cols,
        var_name="Week",
        value_name="Availability"
    )

    # Melt the week columns into long format
    df_long = df.melt(
        id_vars=["Site ID", "Area", "Regional", "NOP", "Target", "Class S1 2025"],
        value_vars=week_cols,
        var_name="Week",
        value_name="Availability"
    )
    df_long["Week"] = df_long["Week"].str.replace("Avail ", "", regex=False)
    df_long["Target Line"] = df_long["Target"]
    df_long["WeekNum"] = df_long["Week"].str.extract(r"W(\d{2})").astype(int)
    df_long = df_long.sort_values("WeekNum")

    # --- Cascading Filters with "All" Option ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        area_options = ["All"] + sorted(df_long["Area"].dropna().unique())
        area_selected = st.selectbox("Select Area", area_options, key="area")

    with col2:
        if area_selected == "All":
            regional_options = ["All"] + sorted(df_long["Regional"].dropna().unique())
        else:
            regional_options = ["All"] + sorted(df_long[df_long["Area"] == area_selected]["Regional"].dropna().unique())
        regional_selected = st.selectbox("Select Regional", regional_options, key="regional")

    with col3:
        filtered_nop = df_long.copy()
        if area_selected != "All":
            filtered_nop = filtered_nop[filtered_nop["Area"] == area_selected]
        if regional_selected != "All":
            filtered_nop = filtered_nop[filtered_nop["Regional"] == regional_selected]
        nop_options = ["All"] + sorted(filtered_nop["NOP"].dropna().unique())
        nop_selected = st.selectbox("Select NOP", nop_options, key="nop")

    with col4:
        filtered_site = df_long.copy()
        if area_selected != "All":
            filtered_site = filtered_site[filtered_site["Area"] == area_selected]
        if regional_selected != "All":
            filtered_site = filtered_site[filtered_site["Regional"] == regional_selected]
        if nop_selected != "All":
            filtered_site = filtered_site[filtered_site["NOP"] == nop_selected]

        site_options = sorted(filtered_site["Site ID"].dropna().unique())
        site_options_with_all = ["All"] + site_options

        site_selected = st.selectbox("Select Site", site_options_with_all, key="site")

    filtered_df = df_long.copy()

    if area_selected != "All":
        filtered_df = filtered_df[filtered_df["Area"] == area_selected]
    if regional_selected != "All":
        filtered_df = filtered_df[filtered_df["Regional"] == regional_selected]
    if nop_selected != "All":
        filtered_df = filtered_df[filtered_df["NOP"] == nop_selected]
    if site_selected != "All":
        filtered_df = filtered_df[filtered_df["Site ID"] == site_selected]

    if filtered_df.empty:
        st.warning("No data matching selected filters.")
        return

    # --- Unique site count ---
    unique_sites = filtered_df["Site ID"].dropna().unique()
    site_count = len(unique_sites)

    # --- Title components ---
    area_text = f"Area: {area_selected}" if area_selected != "All" else "All Areas"
    regional_text = f" | Regional: {regional_selected}" if regional_selected != "All" else ""
    nop_text = f" | NOP: {nop_selected}" if nop_selected != "All" else ""

    # Site text logic
    site_text = ""
    site_class_text = ""

    if site_count == 1:
        site = unique_sites[0]
        site_text = f" | Site ID: {site}"

        # ✅ Add Site Class
        site_class = (
            filtered_df.loc[filtered_df["Site ID"] == site, "Class S1 2025"]
            .dropna()
            .astype(str)
            .unique()
        )
        if len(site_class) > 0:
            site_class_text = f" | Site Class: {site_class[0]}"

    elif isinstance(site_selected, list) and site_selected != ["All"]:
        site_text = f" | {len(site_selected)} Sites Selected"
    elif isinstance(site_selected, str) and site_selected != "All":
        site_text = f" | Site ID: {site_selected}"

    # --- Combine full title ---
    title_text = f"{area_text}{regional_text}{nop_text}{site_text}{site_class_text} | Total Sites: {site_count}"

    # --- Chart rendering ---
    if site_count == 1:
        site = unique_sites[0]
        site_df = filtered_df[filtered_df["Site ID"] == site].sort_values("Week")

        fig = go.Figure()

        # Green availability line with labels
        fig.add_trace(go.Scatter(
            x=site_df["Week"],
            y=site_df["Availability"],
            mode="lines+markers+text",  # ✅ Needed for labels
            name=f"{site}",
            line=dict(color="green", width=4),
            text=site_df["Availability"].round(2).astype(str) + "%",
            textposition="bottom center",
            textfont=dict(color="green", size=14, family="Arial Black")
        ))

        # Blue dashed target line
        fig.add_trace(go.Scatter(
            x=site_df["Week"],
            y=site_df["Target Line"],
            mode="lines",
            name=f"Target - {site}",
            line=dict(color="blue", dash="dash", width=4)
        ))
    else:
        # Multiple sites
        fig = px.line(
            filtered_df,
            x="Week",
            y="Availability",
            color="Site ID",
            markers=True
        )

    # --- Update layout ---
    fig.update_layout(
        title={
            "text": f"<b><span style='color:#2F5597; font-size:20px;'>{title_text}</span></b>",
            "x": 0.5,
            "xanchor": "center"
        },
        yaxis_title="Availability (%)",
        xaxis_title="Week",
        legend_title="Site",
        height=550
    )

    st.plotly_chart(fig, use_container_width=True)

def app_tab3():
    st.subheader("📊 Regional Red Zone Distribution")
    df = load_worst_site_data()

    if df.empty or "Regional" not in df.columns:
        st.warning("Data not available or missing 'Regional' column.")
        return

    regional_summary = (
        df.groupby("Regional")["Site ID"]
        .nunique()
        .reset_index(name="Total Red Zone Sites")
        .sort_values("Total Red Zone Sites", ascending=False)
    )
    st.bar_chart(regional_summary.set_index("Regional"), use_container_width=True)


def app():
    col1, col2 = st.columns([9, 1])

    with col1:
        st.title("📉 Worst Site Dashboard")

    with col2:
        if st.button("🔄 Refresh Data", help="Reload worst site data"):
            st.cache_data.clear()
            st.rerun()

    tab1, tab2, tab3 = st.tabs([
        "📌 Red Zone Summary",
        "📈 Site Tracking",
        "📊 Regional Breakdown"
    ])

    with tab1:
        app_tab1()
    with tab2:
        app_tab2()
    with tab3:
        app_tab3()
