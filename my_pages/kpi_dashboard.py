import streamlit as st
import pandas as pd
from utils.data_loader import load_kpi_data

def app_tab1():
    st.header("📌 Daily KPI Summary")

    # Load KPI_Data sheet
    df = load_kpi_data(sheet_name="KPI_Data")
    df = df.dropna(subset=["AREA", "Month", "Year"])  # Clean-up

    display_cols = [
        "REGIONAL", "NOP", "SON L1 Score",
        "SON L1 Status", "SOMSA L0 Score", "SOMSA L0 Status"
    ]

    # --- Filters ---
    with st.container():
        col1, col2 = st.columns(2)

        # Month sorting
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        all_years = sorted(df["Year"].dropna().unique(), reverse=True)
        latest_year = all_years[0]
        latest_months_df = df[df["Year"] == latest_year]

        if df["Month"].dtype == object:
            all_months = sorted(set(df["Month"].dropna().unique()), key=lambda m: month_order.index(m))
            latest_month = max(latest_months_df["Month"], key=lambda m: month_order.index(m))
        else:
            all_months = sorted(df["Month"].dropna().unique())
            latest_month = max(latest_months_df["Month"])

        with col1:
            month = st.selectbox("Select Month", all_months, index=all_months.index(latest_month))
        with col2:
            year = st.selectbox("Select Year", all_years, index=0)

    # --- Apply Filters ---
    filtered_df = df[(df["Year"] == year) & (df["Month"] == month)]

    # --- Score Category Colors ---
    score_categories = {
        "Istimewa": "#3498db",
        "Baik Sekali": "#0f834b",
        "Baik": "#2ecc71",
        "Cukup": "#e67e22",
        "Kurang": "#e74c3c",
    }

    def highlight_sonl1_score(row):
        def get_color(score):
            if pd.isna(score):
                return "#ffffff"
            elif score >= 95:
                return "#3498db"
            elif score >= 90:
                return "#0f834b"
            elif score >= 85:
                return "#2ecc71"
            elif score >= 80:
                return "#e67e22"
            else:
                return "#e74c3c"

        styles = []
        for col in row.index:
            if col in ["SON L1 Score", "SOMSA L0 Score"]:
                score = row[col]
                background = get_color(score)
                font_color = "black" if background.lower() in ["#2ecc71", "#ffffff"] else "white"
                styles.append(
                    f"background-color: {background}; color: {font_color}; font-weight: bold; font-size: 18px"
                )
            else:
                styles.append("")
        return styles

    status_colors = {
        "CLOSED": "#0f834b",
        "DRAFT": "#ffffff",
        "ENOM REVIEW": "#b5acdd",
        "NOP APPROVAL": "#3498db"
    }

    def highlight_status(row):
        styles = []
        for col in row.index:
            if col in ["SON L1 Status", "SOMSA L0 Status"]:
                color = status_colors.get(row[col], "#ffffff")
                font_color = "black" if color.lower() in ["#ffffff", "#dcd6f7"] else "white"
                styles.append(f"background-color: {color}; color: {font_color}; font-weight: bold")
            else:
                styles.append("")
        return styles

    alignment_style = {
        "SON L1 Score": "text-align: center; vertical-align: middle",
        "SON L1 Status": "text-align: center; vertical-align: middle",
        "SOMSA L0 Score": "text-align: center; vertical-align: middle",
        "SOMSA L0 Status": "text-align: center; vertical-align: middle",
    }

    # --- KPI Summary for AREA 1 & 3 ---
    st.markdown("### 📊 SONL 1 Score Category Count (AREA 1 & AREA 3)")
    html_code = None  # <-- Declare upfront to avoid UnboundLocalError

    filtered_df_area_1_3 = filtered_df[filtered_df["AREA"].isin(["AREA 1", "AREA 3"])]
    score_counts = filtered_df_area_1_3["SONL 1 Score Category"].value_counts().reindex(score_categories.keys(), fill_value=0)

    cols = st.columns(len(score_categories))
    for idx, (category, color) in enumerate(score_categories.items()):
        count = int(score_counts[category])
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background-color:{color};padding:10px;border-radius:10px;text-align:center">
                    <h4 style="color:white;margin:0;font-size:24px">{category}</h4>
                    <p style="font-size:32px;color:white;margin:0"><strong>{count}</strong></p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- Tables AREA 1 & AREA 3 ---
    col1, col2 = st.columns(2)

    # --- AREA 1 ---
    with col1:
        st.subheader(f"📍 AREA 1 — {month} {year}")
    
        df_area1 = filtered_df[filtered_df["AREA"] == "AREA 1"].copy()
    
        if not df_area1.empty:
            # ... your processing and styling steps here ...
            df_area1["REGIONAL"] = pd.Categorical(
                df_area1["REGIONAL"],
                categories=["R01 SUMBAGUT", "R10 SUMBAGTENG", "R02 SUMBAGSEL"],
                ordered=True
            )
            df_area1 = df_area1.sort_values(["REGIONAL", "NOP"])
    
            df_area1_display_full = df_area1[display_cols + ["SONL 1 Score Category"]].reset_index(drop=True)
            df_area1_display_full.index += 1
    
            styled_df_visible = df_area1_display_full.drop(columns=["SONL 1 Score Category"]).style \
                .format({"SON L1 Score": "{:.2f}", "SOMSA L0 Score": "{:.2f}"}) \
                .apply(highlight_sonl1_score, axis=1) \
                .apply(highlight_status, axis=1) \
                .set_properties(**alignment_style)
    
            table_html = styled_df_visible.to_html(escape=False)
            columns = styled_df_visible.columns.tolist()
            left_align_cols = ["REGIONAL", "NOP"]
            left_align_indexes = [f"col{i}" for i, col in enumerate(columns) if col in left_align_cols]
            left_align_css = ", ".join([f'td.{idx}' for idx in left_align_indexes])
    
            html_code = f"""
            <div style="overflow-x: auto; width: 100%;">
                <div style="min-width: 800px;">
                    <style>
                        table {{
                            width: 100%;
                            table-layout: auto;
                            border-collapse: collapse;
                            font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
                            font-size: 14px;
                            color: #333;
                            border: 1px solid #ccc;
                        }}
                        th, td {{
                            padding: 5px;
                            white-space: nowrap;
                            text-align: center;
                            vertical-align: middle;
                            border: 1px solid #ccc;
                        }}
                        th {{
                            background-color: #f2f2f2;
                            font-weight: 600;
                        }}
                        {left_align_css} {{
                            text-align: left !important;
                        }}
                        tr:nth-child(even) {{
                            background-color: #fafafa;
                        }}
                    </style>
                    {table_html}
                </div>
            </div>
            """
            components.html(html_code, height=700, scrolling=False)
        else:
            st.warning("No data available for AREA 1.")
    # --- AREA 3 ---
    with col2:
        st.subheader(f"📍 AREA 3 — {month} {year}")

        df_area3 = filtered_df[filtered_df["AREA"] == "AREA 3"].copy()
        df_area3["REGIONAL"] = pd.Categorical(
            df_area3["REGIONAL"],
            categories=["R05 JAWA TENGAH", "R06 JAWA TIMUR", "R07 BALI NUSRA"],
            ordered=True
        )
        df_area3 = df_area3.sort_values(["REGIONAL", "NOP"])

        # Step 1: Create full DataFrame for styling
        df_area3_display_full = df_area3[display_cols + ["SONL 1 Score Category"]].reset_index(drop=True)
        df_area3_display_full.index += 1

        # Step 2: Apply styles using full DataFrame
        styled_df_full_3 = df_area3_display_full.style \
            .format({"SON L1 Score": "{:.2f}", "SOMSA L0 Score": "{:.2f}"}) \
            .apply(highlight_sonl1_score, axis=1) \
            .apply(highlight_status, axis=1)

        # Step 3: Drop the category column before display
        df_area3_visible = df_area3_display_full.drop(columns=["SONL 1 Score Category"])

        # Step 4: Apply styles again only on visible columns
        styled_df_visible_3 = df_area3_visible.style \
            .format({"SON L1 Score": "{:.2f}", "SOMSA L0 Score": "{:.2f}"}) \
            .apply(highlight_sonl1_score, axis=1) \
            .apply(highlight_status, axis=1) \
            .set_properties(**alignment_style)

        #st.markdown(f"📅 Showing data for: **{month} {year}**")  # ← Add this line
        #st.dataframe(
        #    styled_df_visible_3,
        #    height=635,
        #    use_container_width=True
        #)
        #st.table(styled_df_visible)
        #st.markdown(styled_df_visible.to_html(escape=False), unsafe_allow_html=True)

        # Convert styled DataFrame to HTML (keep conditional formatting)
        import streamlit.components.v1 as components

        # Convert styled DataFrame to HTML
        table_html = styled_df_visible_3.to_html(escape=False)

        # Get column positions for left-aligning REGIONAL and NOP
        columns = styled_df_visible.columns.tolist()
        left_align_cols = ["REGIONAL", "NOP"]
        left_align_indexes = [f"col{i}" for i, col in enumerate(columns) if col in left_align_cols]

        # Build CSS to apply left alignment to specific columns
        left_align_css = ", ".join([f'td.{idx}' for idx in left_align_indexes])

        # Final HTML with professional styles
        # Final HTML with professional styles
        html_code = f"""
        <div style="overflow-x: auto; width: 100%;">
            <style>
                table {{
                    width: 100% !important;
                    table-layout: auto !important;
                    border-collapse: collapse !important;
                    font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif !important;
                    font-size: 14px !important;
                    color: #333 !important;
                    border: 1px solid #ccc;
                }}
                th, td {{
                    padding: 5px !important;
                    white-space: nowrap;
                    text-align: center !important;
                    vertical-align: middle !important;
                    border: 1px solid #ccc;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: 600;
                }}
                {left_align_css} {{
                    text-align: left !important;
                }}
                tr:nth-child(even) {{
                    background-color: #fafafa;
                }}
            </style>
            {table_html}
        </div>
        """

        # Render in Streamlit
        components.html(html_code, height=700, scrolling=True)
    
    # --- Summary Score Cards for AREA 1 & 3 Combined ---
    st.markdown(f"### 📋 Average Scores Summary — {month} {year}")

    # Calculate averages
    sonl1_avg_area1 = df_area1["SON L1 Score"].mean()
    somsa_avg_area1 = df_area1["SOMSA L0 Score"].mean()

    sonl1_avg_area3 = df_area3["SON L1 Score"].mean()
    somsa_avg_area3 = df_area3["SOMSA L0 Score"].mean()

    df_combined = filtered_df[filtered_df["AREA"].isin(["AREA 1", "AREA 3"])]
    combined_sonl1_avg = df_combined["SON L1 Score"].mean()
    combined_somsa_avg = df_combined["SOMSA L0 Score"].mean()

    # Define cards
    card_data = [
        ("AREA 1 — SON L1", f"{sonl1_avg_area1:.2f}", "#2980b9"),
        ("AREA 1 — SOMSA L0", f"{somsa_avg_area1:.2f}", "#27ae60"),
        ("AREA 3 — SON L1", f"{sonl1_avg_area3:.2f}", "#8e44ad"),
        ("AREA 3 — SOMSA L0", f"{somsa_avg_area3:.2f}", "#16a085"),
        ("AREA 1 & 3 — SON L1", f"{combined_sonl1_avg:.2f}", "#e67e22"),
        ("AREA 1 & 3 — SOMSA L0", f"{combined_somsa_avg:.2f}", "#c0392b"),
    ]

    # Layout
    cols = st.columns(len(card_data))
    for idx, (label, value, color) in enumerate(card_data):
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background-color:{color};padding:12px;border-radius:10px;text-align:center">
                    <h4 style="color:white;margin:0;font-size:18px">{label}</h4>
                    <p style="font-size:28px;color:white;margin:0"><strong>{value}</strong></p>
                </div>
                """,
                unsafe_allow_html=True
            )

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_kpi_data

def app_tab2():
    st.header("📈 Daily KPI Trend")

    # Load KPI_Trend sheet
    df = load_kpi_data(sheet_name="KPI_Trend")

    # Ensure Date column is datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # --- Filter Columns ---
    col1, col2, col3, col4 = st.columns(4)

    # --- Prepare latest month & year ---
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Ensure Month and Year have values
    df = df.dropna(subset=["Month", "Year"])

    # Convert Year to int and sort
    df["Year"] = df["Year"].astype(int)
    years = sorted(df["Year"].unique(), reverse=True)
    default_year = years[0]

    # Get available months sorted
    months = sorted(df["Month"].dropna().unique(), key=lambda m: month_order.index(m))

    # Get latest month in the latest year
    latest_month_data = df[df["Year"] == default_year]["Month"].dropna().unique()
    latest_month = max(latest_month_data, key=lambda m: month_order.index(m))

    # --- Streamlit select boxes ---
    with col1:
        month = st.selectbox("Select Month", months, index=months.index(latest_month), key="select_month")

    with col2:
        year = st.selectbox("Select Year", years, index=0, key="select_year")

    # Filter by month and year
    filtered_df = df[(df["Year"] == year) & (df["Month"] == month)]

    with col3:
        regional = st.selectbox(
            "Select Regional",
            sorted(filtered_df["Regional"].dropna().unique()),
            key="select_regional"
        )

    # Filter by regional
    regional_df = filtered_df[filtered_df["Regional"] == regional]

    with col4:
        nop_options = ["All"] + sorted(regional_df["NOP"].dropna().unique())
        nop = st.selectbox("Select NOP", nop_options, key="select_nop")

    # Base filtering by selected Month, Year, Regional
    base_df = df[
        (df["Month"] == month) &
        (df["Year"] == year) &
        (df["Regional"] == regional)
    ].copy()

    # Convert types
    base_df["KPI SWFM"] = pd.to_numeric(base_df["KPI SWFM"], errors="coerce") * 100
    base_df["Date"] = pd.to_datetime(base_df["Date"], errors="coerce")
    base_df = base_df.dropna(subset=["Date", "KPI SWFM"]).sort_values("Date")

    # --- Plot logic ---
    if nop == "All":
        final_df = base_df.copy()

        subtitle = f"<span style='color:blue; font-weight:bold; font-size:18px'>{regional} / All NOPs ({month} {year})</span>"

        fig = px.line(
            final_df,
            x="Date",
            y="KPI SWFM",
            color="NOP",  # Multiple lines for each NOP
            markers=True
        )

    else:
        final_df = base_df[base_df["NOP"] == nop].copy()

        subtitle = f"<span style='color:blue; font-weight:bold; font-size:18px'>{regional} / {nop} ({month} {year})</span>"

        fig = px.line(
            final_df,
            x="Date",
            y="KPI SWFM",
            markers=True
        )

    # Apply line thickness
    fig.update_traces(line=dict(width=3))

    # --- Add 85% reference line ---
    fig.add_hline(
        y=85,
        line_dash="dash",
        line_color="red",
        annotation_text="Target 85%",
        annotation_position="top left"
    )

    # --- Layout with styled title ---
    fig.update_layout(
        title={
            "text": f"KPI SWFM Trend<br>{subtitle}",
            "x": 0.5,
            "xanchor": "center"
        },
        yaxis_title="KPI SWFM (%)",
        xaxis_title="Date",
        yaxis_range=[0, 100],
        height=500
    )

    # --- X-axis formatting to show all dates ---
    fig.update_xaxes(
        tickmode="linear",
        dtick="D1",
        tickformat="%d-%b",
        tickangle=315
    )

    # --- Show plot ---
    st.plotly_chart(fig, use_container_width=True)

# --- Unified app() with tabs ---
def app():
    col1, col2 = st.columns([9, 1])  # 6:1 ratio keeps the button narrow and aligned right

    with col1:
        st.title("📶 KPI Monitoring Dashboard")

    with col2:
        st.markdown("")  # Add spacing if needed
        if st.button("🔄 Refresh Data", help="Reload all ticketing data"):
            st.cache_data.clear()
            st.rerun()
            
    tab1, tab2 = st.tabs(["📌 Daily KPI Summary", "📈 Daily KPI Trend"])
    with tab1:
        app_tab1()
    with tab2:
        app_tab2()




