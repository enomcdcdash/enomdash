import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_ticketing_overview_data
import calendar


def filter_severity_data(df):
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Ensure Month and Year columns exist and have valid data
    df = df.copy()
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    # Define correct month order
    month_order = list(calendar.month_name)[1:]  # ['January', ..., 'December']

    # Clean and sort Month as string
    df = df[df['Month'].isin(month_order)]
    sorted_months = [m for m in month_order if m in df['Month'].unique()]
    sorted_years = sorted(df['Year'].dropna().unique().astype(int), reverse=True)

    if not sorted_months or not sorted_years:
        st.warning("No valid Month or Year data available.")
        return pd.DataFrame(), "All", "All", "All", "All", "All", None, None

    latest_year = sorted_years[0]
    latest_months = df[df["Year"] == latest_year]['Month'].dropna().unique().tolist()

    # Get latest month by order
    latest_month = None
    for m in reversed(month_order):
        if m in latest_months:
            latest_month = m
            break
    if latest_month is None:
        latest_month = sorted_months[-1]

    # Selectboxes with default latest selected
    month = col1.selectbox("Month", sorted_months, index=sorted_months.index(latest_month))
    year = col2.selectbox("Year", sorted_years, index=0)

    df_base = df[(df["Month"] == month) & (df["Year"] == year)]

    area_options = ['All'] + sorted(df_base['Area'].dropna().unique())
    area = col3.selectbox("Area", area_options)

    df_area = df_base if area == 'All' else df_base[df_base['Area'] == area]

    regional_options = ['All'] + sorted(df_area['Regional'].dropna().unique())
    regional = col4.selectbox("Regional", regional_options)

    df_reg = df_area if regional == 'All' else df_area[df_area['Regional'] == regional]

    nop_options = ['All'] + sorted(df_reg['NOP'].dropna().unique())
    nop = col5.selectbox("NOP", nop_options)

    df_nop = df_reg if nop == 'All' else df_reg[df_reg['NOP'] == nop]

    cluster_options = ['All'] + sorted(df_nop['Cluster TO'].dropna().unique())
    cluster = col6.selectbox("Cluster TO", cluster_options)

    df_filtered = df_nop if cluster == 'All' else df_nop[df_nop['Cluster TO'] == cluster]

    type_ticket = st.selectbox("Type Ticket", ['All', 'Incident', 'Event'])

    return df_filtered, type_ticket, area, regional, nop, cluster, month, year

def plot_severity_charts(df, type_ticket, area, regional, nop, cluster):
    import plotly.express as px

    # Determine severity columns
    if type_ticket == "Incident":
        sev_cols = ["Critical_Incident", "Major_Incident", "Minor_Incident", "Low_Incident"]
    elif type_ticket == "Event":
        sev_cols = ["Critical_Event", "Major_Event", "Minor_Event", "Low_Event"]
    else:
        df = df.copy()
        df["Critical"] = df["Critical_Incident"] + df["Critical_Event"]
        df["Major"] = df["Major_Incident"] + df["Major_Event"]
        df["Minor"] = df["Minor_Incident"] + df["Minor_Event"]
        df["Low"] = df["Low_Incident"] + df["Low_Event"]
        sev_cols = ["Critical", "Major", "Minor", "Low"]

    # Determine grouping level
    group_keys = ["Date"]
    if cluster != "All":
        group_keys.append("Cluster TO")
    elif nop != "All":
        group_keys.append("NOP")
    elif regional != "All":
        group_keys.append("Regional")
    elif area != "All":
        group_keys.append("Area")

    # Group and sum
    df_grouped = df.groupby(group_keys)[sev_cols].sum().reset_index()
    df_grouped["Total"] = df_grouped[sev_cols].sum(axis=1)

    # Prepare for plotting
    df_melted = df_grouped.melt(
        id_vars=["Date", "Total"],
        value_vars=sev_cols,
        var_name="Severity",
        value_name="Count"
    )

    # Build filter summary
    filter_parts = []
    if area != "All": filter_parts.append(f"Area: {area}")
    if regional != "All": filter_parts.append(f"Regional: {regional}")
    if nop != "All": filter_parts.append(f"NOP: {nop}")
    if cluster != "All": filter_parts.append(f"Cluster TO: {cluster}")
    filter_summary = " | ".join(filter_parts) if filter_parts else "All Areas"

    # Layout
    col12, col3 = st.columns([5, 2])

    # --- Stacked Bar Chart + Green Line ---
    with col12:
        st.markdown("### 📊 Tickets Distribution based on Severity")

        fig = px.bar(
            df_melted,
            x="Date",
            y="Count",
            color="Severity",
            barmode="stack",
            title=f"Daily Tickets per Severity ({type_ticket}) - {filter_summary}"
        )

        # Customize bar hover
        fig.update_traces(
            selector=dict(type="bar"),
            hovertemplate="<b>Date:</b> %{x}<br><b>Severity:</b> %{fullData.name}<br><b>Count:</b> %{y}<extra></extra>"
        )

        # Add green total line with labels
        fig.add_scatter(
            x=df_grouped["Date"],
            y=df_grouped["Total"],
            mode="lines+markers+text",
            name="Total Tickets",
            line=dict(color="green", width=4),
            marker=dict(size=6),
            text=df_grouped["Total"],
            textposition="top center",
            hovertemplate="<b>Date:</b> %{x}<br><b>Total Tickets:</b> %{y}<extra></extra>"
        )

        fig.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            legend_title_text="",
            hovermode="x unified",
            xaxis=dict(
                tickmode='array',
                tickvals=df_grouped["Date"],
                tickformat="%d-%b",
                tickangle=-45
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- Pie Chart ---
    with col3:
        st.markdown("### 🥧 Severity Distribution")
        pie_data = df_melted.groupby("Severity")["Count"].sum().reset_index()

        fig_pie = px.pie(
            pie_data,
            names="Severity",
            values="Count",
            hole=0.3
        )

        fig_pie.update_traces(
            textinfo="label+value+percent",
            textposition="outside",
            textfont=dict(size=16),
            insidetextorientation='radial',  # fallback for tight slices
            showlegend=False
        )

        fig_pie.update_layout(
            title_text=f"Severity Distribution - {filter_summary}",
            title_font_size=16,
            margin=dict(t=60, b=60, l=60, r=60),
            showlegend=False,
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )

        st.plotly_chart(fig_pie, use_container_width=True)


def app_tab1(df_severity, df_rc_cat):
    if df_severity.empty:
        st.warning("No data found in Severity sheet.")
        return

    df_filtered, type_ticket, area, regional, nop, cluster, month, year = filter_severity_data(df_severity)

    if df_filtered.empty:
        st.warning("No data matches the selected filters.")
        return

    plot_severity_charts(df_filtered, type_ticket, area, regional, nop, cluster)

    # --- RC Category PIE and TABLE ---
    st.markdown("---")
    st.markdown("### 🧩 RC Category Breakdown")

    df_rc = df_rc_cat.copy()

    if month != "All":
        df_rc = df_rc[df_rc["Month"] == month]
    if year != "All":
        df_rc = df_rc[df_rc["Year"] == int(year)]
    if area != "All":
        df_rc = df_rc[df_rc["Area"] == area]
    if regional != "All":
        df_rc = df_rc[df_rc["Regional"] == regional]
    if nop != "All":
        df_rc = df_rc[df_rc["NOP"] == nop]
    if cluster != "All":
        df_rc = df_rc[df_rc["Cluster TO"] == cluster]

    if type_ticket == "Incident":
        sev_cols = ["Critical_Incident", "Major_Incident", "Minor_Incident", "Low_Incident"]
    elif type_ticket == "Event":
        sev_cols = ["Critical_Event", "Major_Event", "Minor_Event", "Low_Event"]
    else:
        df_rc = df_rc.copy()
        df_rc["Critical"] = df_rc["Critical_Incident"] + df_rc["Critical_Event"]
        df_rc["Major"] = df_rc["Major_Incident"] + df_rc["Major_Event"]
        df_rc["Minor"] = df_rc["Minor_Incident"] + df_rc["Minor_Event"]
        df_rc["Low"] = df_rc["Low_Incident"] + df_rc["Low_Event"]
        sev_cols = ["Critical", "Major", "Minor", "Low"]

    df_pie_rc = df_rc.groupby("RC Category")[sev_cols].sum().reset_index()
    df_pie_rc["Total"] = df_pie_rc[sev_cols].sum(axis=1)

    df_table = df_rc.groupby(["RC Category", "RC 1 Clean"])[sev_cols].sum().reset_index()
    df_table["Total"] = df_table[sev_cols].sum(axis=1)
    df_table = df_table.sort_values(by="Total", ascending=False)

    rc_category_order = ["Power", "Transmisi", "Radio", "Aktivitas", "Lain - lain"]
    df_table["RC Category"] = pd.Categorical(df_table["RC Category"], categories=rc_category_order, ordered=True)
    df_table = df_table.sort_values(by=["RC Category", "RC 1 Clean"]).reset_index(drop=True)
    df_table.index += 1

    col_pie, col_table = st.columns([2, 5])

    with col_pie:
        st.markdown("#### 🥧 RC Category Share")
        fig_rc = px.pie(
            df_pie_rc,
            names="RC Category",
            values="Total",
            hole=0.3
        )
        fig_rc.update_traces(
            textinfo="label+value+percent",
            textposition="outside",
            textfont=dict(size=14),
            hovertemplate="<b>RC Category:</b> %{label}<br><b>Count:</b> %{value}<br><b>Percent:</b> %{percent}<extra></extra>",
            #pull=[0.05] * len(df_pie_rc),
            automargin=True  # Helps with layout
        )
        fig_rc.update_layout(
            #title_text=f"RC Category - {type_ticket} - Filtered",
            margin=dict(t=90, b=40, l=40, r=40),  # widen left/right
            height=450,
            showlegend=False,
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig_rc, use_container_width=True)

    with col_table:
        st.markdown("#### 📋 RC Category Details")
        display_cols = ["RC Category", "RC 1 Clean"] + sev_cols + ["Total"]
        styled_table = df_table[display_cols].style.set_table_attributes(
            'style="width:100%; border-collapse:collapse;"'
        ).set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#f0f0f0'), ('font-size', '20px'), ('text-align', 'center'), ('padding', '6px')]},
            {'selector': 'tbody td', 'props': [('font-size', '20px'), ('text-align', 'center'), ('padding', '6px')]},
            {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#fafafa')]},
            {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
        ])
        st.markdown(
            f"""
            <div style="max-height:500px; overflow-y:auto; width:100%;">
                {styled_table.to_html(index=True, index_names=False)}</div>""",
            unsafe_allow_html=True
        )

def filter_ticket_data(df):
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Ensure Year is numeric
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    # Use standard month names for ordering
    month_order = list(calendar.month_name)[1:]  # ['January', 'February', ..., 'December']
    df = df[df['Month'].isin(month_order)]

    # Sort months and years from the data
    months_in_data = df['Month'].dropna().unique().tolist()
    sorted_months = [m for m in month_order if m in months_in_data]

    sorted_years = sorted(df['Year'].dropna().unique().astype(int), reverse=True)

    # Safe defaults
    if not sorted_months or not sorted_years:
        st.warning("⚠️ No valid Month or Year data available.")
        return pd.DataFrame(), "All", "All", "All", "All", None, None

    latest_year = sorted_years[0]
    months_for_latest_year = df[df['Year'] == latest_year]['Month'].dropna().unique().tolist()
    latest_month = next((m for m in reversed(month_order) if m in months_for_latest_year), sorted_months[-1])

    # Month and Year Selectboxes
    month = col1.selectbox("Month", sorted_months, index=sorted_months.index(latest_month), key="filter_month")
    year = col2.selectbox("Year", sorted_years, index=0, key="filter_year")

    # Filter base dataframe
    df_base = df[(df["Month"] == month) & (df["Year"] == year)]

    # AREA filter
    area_options = ['All'] + sorted(df_base['Area'].dropna().unique())
    selected_area = col3.selectbox("Area", area_options, key="filter_area")
    df_area = df_base if selected_area == 'All' else df_base[df_base['Area'] == selected_area]

    # REGIONAL filter
    regional_options = ['All'] + sorted(df_area['Regional'].dropna().unique())
    selected_regional = col4.selectbox("Regional", regional_options, key="filter_regional")
    df_reg = df_area if selected_regional == 'All' else df_area[df_area['Regional'] == selected_regional]

    # NOP filter
    nop_options = ['All'] + sorted(df_reg['NOP'].dropna().unique())
    selected_nop = col5.selectbox("NOP", nop_options, key="filter_nop")
    df_nop = df_reg if selected_nop == 'All' else df_reg[df_reg['NOP'] == selected_nop]

    # CLUSTER TO filter
    cluster_options = ['All'] + sorted(df_nop['Cluster TO'].dropna().unique())
    selected_cluster = col6.selectbox("Cluster TO", cluster_options, key="filter_cluster")
    df_filtered = df_nop if selected_cluster == 'All' else df_nop[df_nop['Cluster TO'] == selected_cluster]

    return df_filtered, selected_area, selected_regional, selected_nop, selected_cluster, month, year

def prepare_top20_table(df, ticket_type):
    suffix = f"_{ticket_type}"
    cols = [
        "NOP", "Cluster TO",
        f"Site Id{suffix}", f"Site Name{suffix}", f"Site Class{suffix}", f"{ticket_type}_Ticket_Count"
    ]
    df_top = df[cols].copy()
    df_top.columns = [
        "Site Id" if col == f"Site Id{suffix}" else
        "Site Name" if col == f"Site Name{suffix}" else
        "Site Class" if col == f"Site Class{suffix}" else
        "Ticket Count" if col == f"{ticket_type}_Ticket_Count" else
        col for col in df_top.columns
    ]

    df_top = df_top.sort_values(by="Ticket Count", ascending=False).head(20)

    df_top["Ticket Count"] = df_top["Ticket Count"].astype(int)

    df_top = df_top.reset_index(drop=True)
    df_top.index += 1

    styled_table = df_top.style.set_table_attributes(
        'style="width:100%; border-collapse:collapse;"'
    ).set_table_styles([
        {'selector': 'thead th', 'props': [
            ('background-color', "#0A5ED7" if ticket_type == "Event" else "#D7263D"),
            ('font-size', '18px'), ('text-align', 'center'),
            ('color', 'white'), ('padding', '6px')
        ]},
        {'selector': 'tbody td', 'props': [
            ('font-size', '17px'), ('padding', '6px')
        ]},
        {'selector': 'tbody td.col0', 'props': [('text-align', 'left')]},   # NOP
        {'selector': 'tbody td.col1', 'props': [('text-align', 'left')]},   # Cluster TO
        {'selector': 'tbody td.col3', 'props': [('text-align', 'left')]},   # Site Name
        {'selector': 'tbody td.col5', 'props': [('text-align', 'center')]}, # Site Class
        {'selector': 'tbody td.col6', 'props': [('text-align', 'center')]}, # Ticket Count
        {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},
        {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
    ])

    return styled_table.to_html(index=True, index_names=False)

def app_tab2(df_ticket, df_dpg):
    st.markdown("### 🧾 Ticket Summary Top 20")

    df_filtered, selected_area, selected_regional, selected_nop, selected_cluster, month, year = filter_ticket_data(df_ticket)

    # Filter df_dpg using the same filter logic
    df_dpg_filtered = df_dpg.copy()
    df_dpg_filtered = df_dpg_filtered[
        (df_dpg_filtered["Month"] == month) & (df_dpg_filtered["Year"] == year)
    ]
    if selected_area != "All":
        df_dpg_filtered = df_dpg_filtered[df_dpg_filtered["Area"] == selected_area]
    if selected_regional != "All":
        df_dpg_filtered = df_dpg_filtered[df_dpg_filtered["Regional"] == selected_regional]
    if selected_nop != "All":
        df_dpg_filtered = df_dpg_filtered[df_dpg_filtered["NOP"] == selected_nop]
    if selected_cluster != "All":
        df_dpg_filtered = df_dpg_filtered[df_dpg_filtered["Cluster TO"] == selected_cluster]

    filters_summary = " | ".join([
        f"Area: {selected_area}" if selected_area != "All" else "",
        f"Regional: {selected_regional}" if selected_regional != "All" else "",
        f"NOP: {selected_nop}" if selected_nop != "All" else "",
        f"Cluster TO: {selected_cluster}" if selected_cluster != "All" else ""
    ])
    filters_summary = " | ".join(filter for filter in filters_summary.split(" | ") if filter)

    # Top 20 DPG Sites Tables
    st.markdown(f"### 🏅 Top 20 DPG Sites – {filters_summary}")
    col_dpg_inc, col_dpg_evt = st.columns(2)

    with col_dpg_inc:
        st.markdown("#### 🟥 Incident (DPG)")
        df_dpg_inc = prepare_top20_table(df_dpg_filtered, "Incident")
        st.markdown(df_dpg_inc, unsafe_allow_html=True)

    with col_dpg_evt:
        st.markdown("#### 🟦 Event (DPG)")
        df_dpg_evt = prepare_top20_table(df_dpg_filtered, "Event")
        st.markdown(df_dpg_evt, unsafe_allow_html=True)

    # Top 20 Recurring Sites Tables
    st.markdown("---")
    st.markdown(f"### 🏅 Top 20 - All Site Classes – {filters_summary}")
    col_incident, col_event = st.columns(2)

    with col_incident:
        st.markdown(f"#### 🟥 Incident")
        df_incident_top = prepare_top20_table(df_filtered, "Incident")
        st.markdown(df_incident_top, unsafe_allow_html=True)

    with col_event:
        st.markdown(f"#### 🟦 Event")
        df_event_top = prepare_top20_table(df_filtered, "Event")
        st.markdown(df_event_top, unsafe_allow_html=True)

def app():
    col1, col2 = st.columns([9, 1])

    with col1:
        st.title("📋 Ticketing Overview")

    with col2:
        if st.button("🔄 Refresh Data", help="Reload ticketing overview data"):
            st.cache_data.clear()
            st.rerun()

    df_severity, df_rc_cat, df_ticket, df_dpg = load_ticketing_overview_data()

    tab1, tab2 = st.tabs([
        "📊 Overview",
        "📄 Problematic Sites"
    ])

    with tab1:
        app_tab1(df_severity, df_rc_cat)
    with tab2:
        app_tab2(df_ticket, df_dpg)
