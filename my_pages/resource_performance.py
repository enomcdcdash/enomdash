import streamlit as st
import pandas as pd
import re
import plotly.graph_objects as go
from utils.data_loader import load_resource_data
from io import BytesIO
import streamlit.components.v1 as components

def app_tab1():
    st.subheader("📌 Rekap Tiket")
    df = load_resource_data()

    if df.empty:
        st.warning("No data found.")
        return

    # --- Parse Month ---
    df["Month_Parsed"] = pd.to_datetime(df["Month"], format="%b-%y", errors="coerce")
    df = df.dropna(subset=["Month_Parsed"])
    df["Month_Display"] = df["Month_Parsed"].dt.strftime("%b-%y")

    # --- Ensure Numeric ---
    for col in ["Total Tickets", "Total TO", "Total-Visit", "%TO", "%Visit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Cascading Filters ---
    col1, col2, col3 = st.columns(3)

    area_options = ["All"] + sorted(df["Area"].dropna().unique())
    selected_area = col1.selectbox("Area", area_options)

    regional_filtered = df[df["Area"] == selected_area] if selected_area != "All" else df
    regional_options = ["All"] + sorted(regional_filtered["Regional"].dropna().unique())
    selected_regional = col2.selectbox("Regional", regional_options)

    nop_filtered = regional_filtered[regional_filtered["Regional"] == selected_regional] if selected_regional != "All" else regional_filtered
    nop_options = ["All"] + sorted(nop_filtered["NOP"].dropna().unique())
    selected_nop = col3.selectbox("NOP", nop_options)

    # --- Apply Filters ---
    filtered_df = df.copy()
    if selected_area != "All":
        filtered_df = filtered_df[filtered_df["Area"] == selected_area]
    if selected_regional != "All":
        filtered_df = filtered_df[filtered_df["Regional"] == selected_regional]
    if selected_nop != "All":
        filtered_df = filtered_df[filtered_df["NOP"] == selected_nop]

    if filtered_df.empty:
        st.info("No data available for the selected filters.")
        return

    # Build dynamic title suffix
    title_suffix = []
    if selected_area != "All":
        title_suffix.append(f"Area: {selected_area}")
    if selected_regional != "All":
        title_suffix.append(f"Regional: {selected_regional}")
    if selected_nop != "All":
        title_suffix.append(f"NOP: {selected_nop}")

    title_text = "📊 Total Tickets, TO, Visit, and % Metrics"
    if title_suffix:
        title_text += " | " + ", ".join(title_suffix)
    
    title_text_incident = "📊 Incident"
    if title_suffix:
        title_text_incident += " | " + ", ".join(title_suffix)

    title_text_event = "📊 Event"
    if title_suffix:
        title_text_event += " | " + ", ".join(title_suffix)

    # --- Chart: Total FME vs %TO ---
    fme_grouped = (
        filtered_df
        .groupby(["Month_Display", "Month_Parsed"], as_index=False)
        .agg({
            "Total FME": "sum",
            "%TO": "mean"
        })
    ).sort_values("Month_Parsed")

    fig_fme = go.Figure()

    # Bar: Total FME
    fig_fme.add_trace(go.Bar(
        x=fme_grouped["Month_Display"],
        y=fme_grouped["Total FME"],
        name="Total FME",
        #marker_color="#1f77b4",
        marker_color="lavender",
        opacity=0.9,
        text=fme_grouped["Total FME"],
        textposition="inside",  # shows text inside the bar
        insidetextanchor="start",  # anchor text to the bottom inside
        textfont=dict(color="darkblue", size=14),  # 👈 adjust font size here
        yaxis="y1",
        hovertemplate='Total FME: %{y}<extra></extra>'
    ))

    # Line: %TO
    fig_fme.add_trace(go.Scatter(
        x=fme_grouped["Month_Display"], y=fme_grouped["%TO"],
        name="%TO", mode="lines+markers+text", yaxis="y2",
        #line=dict(color="#2ca02c", width=4),
        line=dict(color="#1f77b4", width=4),
        text=fme_grouped["%TO"].apply(lambda x: f"{x:.2%}"),
        textposition="top center",
        textfont=dict(color="black", size=14),
        hovertemplate='%Takeover: %{y:.2%}<extra></extra>'
    ))

    fig_fme.update_layout(
        title=f"📊 Total FME vs %Takeover - {selected_area} | {selected_regional} | {selected_nop}",
        xaxis=dict(
            title="Month",
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title="Total FME",
            side="left",
            tickfont=dict(size=14),
        ),
        yaxis2=dict(
            title="%TO",
            overlaying="y",
            side="right",
            tickformat=".0%",
            range=[0, 1],
            tickfont=dict(size=14),
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="mintcream",
            font_size=14,
            font_family="Arial"
        ),
        height=400,
        margin=dict(t=60, b=40)
    )

    st.plotly_chart(fig_fme, use_container_width=True)

    # --- Grouping & Custom Aggregation ---
    grouped = (
        filtered_df
        .groupby(["Month_Display", "Month_Parsed"], as_index=False)
        .agg({
            "Total Tickets": "sum",
            "Total TO": "sum",
            "Total-Visit": "sum"
        })
    )

    grouped["%TO"] = grouped["Total TO"] / grouped["Total Tickets"]
    grouped["%Visit"] = grouped["Total-Visit"] / grouped["Total TO"]
    grouped = grouped.sort_values("Month_Parsed")

    # --- Clip % values to max 1.0 ---
    grouped["%TO"] = grouped["%TO"].clip(upper=1.0)
    grouped["%Visit"] = grouped["%Visit"].clip(upper=1.0)

    # --- Plot ---
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=grouped["Month_Display"], y=grouped["Total Tickets"],
        #name="Total Tickets", marker_color="#1f77b4", opacity=0.7,
        name="Total Tickets", marker_color="powderblue", opacity=0.95,
        text=grouped["Total Tickets"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color="blue", size=16),
        hovertemplate="Total Tickets: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=grouped["Month_Display"], y=grouped["Total TO"],
        #name="Total TO", marker_color="#ff7f0e", opacity=0.7,
        name="Total TO", marker_color="lemonchiffon", opacity=0.95,
        text=grouped["Total TO"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color="#ff7f0e", size=16),
        hovertemplate="Total Takeover: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=grouped["Month_Display"], y=grouped["Total-Visit"],
        #name="Total Visit", marker_color="#9467bd", opacity=0.7,
        name="Total Visit", marker_color="peachpuff", opacity=0.95,
        text=grouped["Total-Visit"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color="#2ca02c", size=16),
        hovertemplate="Total Visit: %{y}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=grouped["Month_Display"],
        y=grouped["%TO"],
        name="%TO",
        mode="lines+markers+text",  # 👈 combines line, markers, and text
        yaxis="y2",
        line=dict(color="#1f77b4", width=4),
        text=grouped["%TO"].apply(lambda x: f"{x:.2%}"),
        textposition="top center",
        textfont=dict(color="#1f77b4", size=14),
        hovertemplate="%Takeover: %{y:.2%}<extra></extra>",
        showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=grouped["Month_Display"],
        y=grouped["%Visit"],
        name="%Visit",
        mode="lines+markers+text",  # 👈 combines line, markers, and text
        yaxis="y2",
        line=dict(color="#2ca02c", width=4),
        text=grouped["%Visit"].apply(lambda x: f"{x:.2%}"),  # Label text
        textposition="top center",
        textfont=dict(color="#2ca02c", size=14),
        hovertemplate="%Visit: %{y:.2%}<extra></extra>",  # 👈 Custom hover
        showlegend=True
    ))

    fig.update_layout(
        title=title_text,
        xaxis_title="Month",
        yaxis=dict(title="Count (Tickets, TO, Visit)", side="left"),
        yaxis2=dict(
            title="% TO / Visit",
            overlaying="y",
            side="right",
            tickformat=".0%",
            range=[0, 1.1],
            showgrid=False
        ),
        barmode="group",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="lightcyan",
            font_size=14,
            font_family="Arial"
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.3,
            xanchor="right", x=1.0, title=None
        ),
        margin=dict(t=60, b=80)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Row of IM and EM charts ---
    st.markdown("### 📊 Incident and Event Breakdown")

    col_im, col_em = st.columns(2)

    # ------------------------ IM CHART ------------------------
    with col_im:
        # Debug print column names
        im_grouped = (
        filtered_df
        .groupby(["Month_Display", "Month_Parsed"], as_index=False)
        .agg({
            "IM-Total": "sum",
            "IM-Takeover": "sum",
            "IM-Visit": "sum",
            "IM-%Takeover": "mean",
            "IM-%Visit": "mean"
        })
    ).sort_values("Month_Parsed")

        fig_im = go.Figure()
        fig_im.add_trace(go.Bar(x=im_grouped["Month_Display"], y=im_grouped["IM-Total"], name="IM-Total", marker_color="powderblue", opacity=0.95, text=im_grouped["IM-Total"], textposition="inside", insidetextanchor="start", textfont=dict(color="blue", size=14), hovertemplate="Total-IM-Tickets: %{y}<extra></extra>"))
        fig_im.add_trace(go.Bar(x=im_grouped["Month_Display"], y=im_grouped["IM-Takeover"], name="IM-Takeover", marker_color="lemonchiffon", opacity=0.95, text=im_grouped["IM-Takeover"], textposition="inside", insidetextanchor="start", textfont=dict(color="#ff7f0e", size=14), hovertemplate="IM-Takeover: %{y}<extra></extra>"))
        fig_im.add_trace(go.Bar(x=im_grouped["Month_Display"], y=im_grouped["IM-Visit"], name="IM-Visit", marker_color="peachpuff", opacity=0.95, text=im_grouped["IM-Visit"], textposition="inside", insidetextanchor="start", textfont=dict(color="#2ca02c", size=14), hovertemplate="IM-Visit: %{y}<extra></extra>"))

        fig_im.add_trace(go.Scatter(
            x=im_grouped["Month_Display"], y=im_grouped["IM-%Takeover"],
            name="IM-%Takeover", mode="lines+markers+text", yaxis="y2", 
            line=dict(color="#1f77b4", width=4),
            text=im_grouped["IM-%Takeover"].apply(lambda x: f"{x:.2%}"),
            textposition="top center",
            textfont=dict(color="#1f77b4", size=14),
            hovertemplate="IM-%Takeover: %{y:.2%}<extra></extra>"
        ))
        fig_im.add_trace(go.Scatter(
            x=im_grouped["Month_Display"], y=im_grouped["IM-%Visit"],
            name="IM-%Visit", mode="lines+markers+text", yaxis="y2",
            line=dict(color="#038919", width=4),
            text=im_grouped["IM-%Visit"].apply(lambda x: f"{x:.2%}"),
            textposition="top center",
            textfont=dict(color="#038919", size=14),
            hovertemplate="IM-%Visit: %{y:.2%}<extra></extra>"
        ))

        fig_im.update_layout(
            #title="IM: Total, Takeover, Visit, % Metrics",
            title=title_text_incident,
            xaxis_title="Month",
            yaxis=dict(title="Count", side="left"),
            yaxis2=dict(title="% Takeover / Visit", overlaying="y", side="right", tickformat=".0%", range=[0, 1.1], showgrid=False),
            barmode="group",
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="lightcyan",
                font_size=14,
                font_family="Arial"
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.3,
                xanchor="right", x=1.0, title=None
            ),
            margin=dict(t=40, b=80)
            )
        st.plotly_chart(fig_im, use_container_width=True)

    # ------------------------ EM CHART ------------------------
    with col_em:
        em_grouped = (
            filtered_df
            .groupby(["Month_Display", "Month_Parsed"], as_index=False)
            .agg({
                "EM-Total": "sum",
                "EM-Takeover": "sum",
                "EM-Visit": "sum",
                "EM-%Takeover": "mean",
                "EM-%Visit": "mean"
            })
        ).sort_values("Month_Parsed")

        fig_em = go.Figure()
        fig_em.add_trace(go.Bar(x=em_grouped["Month_Display"], y=em_grouped["EM-Total"], name="EM-Total", marker_color="powderblue", opacity=0.95, text=em_grouped["EM-Total"], textposition="inside", insidetextanchor="start", textfont=dict(color="blue", size=14), hovertemplate="Total-EM-Tickets: %{y}<extra></extra>"))
        fig_em.add_trace(go.Bar(x=em_grouped["Month_Display"], y=em_grouped["EM-Takeover"], name="EM-Takeover", marker_color="lemonchiffon", opacity=0.95, text=em_grouped["EM-Takeover"], textposition="inside", insidetextanchor="start", textfont=dict(color="#ff7f0e", size=14), hovertemplate="EM-Takeover: %{y}<extra></extra>"))
        fig_em.add_trace(go.Bar(x=em_grouped["Month_Display"], y=em_grouped["EM-Visit"], name="EM-Visit", marker_color="peachpuff", opacity=0.95, text=em_grouped["EM-Visit"], textposition="inside", insidetextanchor="start", textfont=dict(color="#2ca02c", size=14), hovertemplate="EM-Visit: %{y}<extra></extra>"))

        fig_em.add_trace(go.Scatter(
            x=em_grouped["Month_Display"], y=em_grouped["EM-%Takeover"],
            name="EM-%Takeover",  mode="lines+markers+text", yaxis="y2",
            line=dict(color="#1f77b4", width=4),
            text=em_grouped["EM-%Takeover"].apply(lambda x: f"{x:.2%}"),
            textposition="top center",
            textfont=dict(color="#1f77b4", size=14),
            hovertemplate="EM-%Takeover: %{y:.2%}<extra></extra>"
        ))
        fig_em.add_trace(go.Scatter(
            x=em_grouped["Month_Display"], y=em_grouped["EM-%Visit"],
            name="EM-%Visit", yaxis="y2", mode="lines+markers+text",
            line=dict(color="#038919", width=4),
            text=em_grouped["EM-%Visit"].apply(lambda x: f"{x:.2%}"),
            textposition="top center",
            textfont=dict(color="#038919", size=14),
            hovertemplate="EM-%Visit: %{y:.2%}<extra></extra>"
        ))

        fig_em.update_layout(
            #title="EM: Total, Takeover, Visit, % Metrics",
            title=title_text_event,
            xaxis_title="Month",
            yaxis=dict(title="Count", side="left"),
            yaxis2=dict(title="% Takeover / Visit", overlaying="y", side="right", tickformat=".0%", range=[0, 1.1], showgrid=False),
            barmode="group",
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="lightcyan",
                font_size=14,
                font_family="Arial"
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.3,
                xanchor="right", x=1.0, title=None
            ),
            margin=dict(t=40, b=80)
        )
        st.plotly_chart(fig_em, use_container_width=True)

# Helper to get most common value
def most_common(series):
    return series.mode().iloc[0] if not series.mode().empty else None

def render_colored_table(df, week_columns):
    def style_cell(val, col):
        if col in week_columns:
            try:
                val_num = float(val)
                ratio = val_num / 7
                val_disp = f"{int(val_num)}"  # Show as integer only
                if ratio > 1:
                    color = "#d4edda"  # green
                elif ratio > 0:
                    color = "#fff3cd"  # orange
                else:
                    color = "#f8d7da"  # red
                return f'<td style="background-color:{color}">{val_disp}</td>'
            except:
                return f"<td>{val}</td>"
        return f"<td>{val}</td>"

    headers = ''.join([f"<th>{col}</th>" for col in df.columns])
    rows = ''
    for _, row in df.iterrows():
        row_html = ''.join([style_cell(row[col], col) for col in df.columns])
        rows += f"<tr>{row_html}</tr>"

    table_html = f"""
    <style>
        .custom-table-container {{
            width: 100%;
            max-height: 600px;
            overflow-y: auto;
        }}
        table {{
            width: 100%;
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
            background-color: #4CAF50;
            color: white;
            position: sticky;
            top: 0;
            z-index: 2;
        }}
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
    </style>
    <div class="custom-table-container">
        <table>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """
    #components.html(table_html, height=600, scrolling=False)
    st.markdown(table_html, unsafe_allow_html=True)

def app_tab2():
    st.subheader("🧑‍🔧 Rekap Resource")
    try:
        df = load_resource_data(sheet_name="Rekap Resource")

        if df.empty:
            st.warning("No resource data found in 'Rekap Resource' sheets.")
            return

        # --- Step 1: Clean & Select Columns ---
        week_columns = [col for col in df.columns if col.startswith("TO-W")]
        base_columns = ["Regional", "NOP", "PIC Take Over Ticket"]
        kpi_columns = ["TO-Total", "IM-TO", "IM-TO-Visit", "EM-TO", "EM-TO-Visit", "Average TO/day", "Performance"]
        selected_columns = base_columns + kpi_columns + week_columns
        available_columns = [col for col in selected_columns if col in df.columns]

        df = df[available_columns].copy()

        # --- Step 2: Rename TO-Wnn → Wnn ---
        to_week_columns = [col for col in df.columns if re.match(r"^TO-W\d+$", col)]
        renamed_week_columns = {col: f"W{col.split('-W')[-1]}" for col in to_week_columns}
        df = df.rename(columns=renamed_week_columns)

        # --- Step 3: Sort Week Columns ---
        week_columns = sorted(
            renamed_week_columns.values(),
            key=lambda x: int(re.findall(r"\d+", x)[0])
        )

        # --- Step 4: Filters ---
        st.markdown("### 🔎 Filters")
        unique_regional = ["All"] + sorted(df["Regional"].dropna().unique())
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_regional = st.selectbox("Regional", unique_regional)

        filtered_df = df[df["Regional"] == selected_regional] if selected_regional != "All" else df
        unique_nop = ["All"] + sorted(filtered_df["NOP"].dropna().unique())

        with col2:
            selected_nop = st.selectbox("NOP", unique_nop)

        filtered_df = filtered_df[filtered_df["NOP"] == selected_nop] if selected_nop != "All" else filtered_df
        unique_pic = ["All"] + sorted(filtered_df["PIC Take Over Ticket"].dropna().unique())

        with col3:
            selected_pic = st.selectbox("PIC Take Over Ticket", unique_pic)

        if selected_pic != "All":
            filtered_df = filtered_df[filtered_df["PIC Take Over Ticket"] == selected_pic]

        # --- Step 5: Convert numeric fields ---
        for col in ["Average TO/day"]:
            if col in filtered_df.columns:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce")

        # --- Step 6: Grouping ---
        group_keys = [col for col in base_columns if col in filtered_df.columns]
        grouped_df = (
            filtered_df
            .groupby(group_keys, as_index=False)
            .agg({
                **{col: "sum" for col in ["TO-Total", "IM-TO", "IM-TO-Visit", "EM-TO", "EM-TO-Visit"] if col in filtered_df.columns},
                **{col: "mean" for col in ["Average TO/day"] if col in filtered_df.columns},
                **{col: most_common for col in ["Performance"] if col in filtered_df.columns},
                **{col: "sum" for col in week_columns}
            })
        )

        grouped_df = grouped_df.sort_values(
            by=["Regional", "NOP", "TO-Total"],
            ascending=[True, True, True]
        ).reset_index(drop=True)

        # Re-add number column
        grouped_df.insert(0, "No", range(1, len(grouped_df) + 1))

        # --- Step 7: Final Column Order ---
        final_columns = (
            ["No"] +
            base_columns +
            ["TO-Total", "IM-TO", "IM-TO-Visit", "EM-TO", "EM-TO-Visit"] +
            week_columns
        )
        available_final_columns = [col for col in final_columns if col in grouped_df.columns]
        grouped_df = grouped_df[available_final_columns]

        # --- Step 8: Summary Cards ---
        #st.markdown("### 📊 Summary")
        #col1, col2, col3 = st.columns(3)
        #col1.metric("Total TO", int(grouped_df["TO-Total"].sum()))
        #col2.metric("Avg TO/day", round(grouped_df["Average TO/day"].mean(), 2))
        #good_pct = (grouped_df["Performance"] == "Good").mean() * 100
        #col3.metric("Good Performance", f"{good_pct:.1f}%")

        # --- Step 9: Data Table ---
        st.markdown("### 📋 Rekap Table")
        render_colored_table(grouped_df, week_columns)

        # --- Step 10: Download Button ---
        output = BytesIO()
        grouped_df.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="💾 Download Excel",
            data=output.getvalue(),
            file_name="rekap_resource_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Failed to load resource tracking data: {e}")


# --- Tab 3: Ava per Site Class ---
def app_tab3():
    st.subheader("📊 Availability per Site Class")
    df = load_resource_data()

    if df.empty:
        st.warning("No data found.")
        return

    if "Site Class" in df.columns and "Availability" in df.columns:
        avg_ava = df.groupby("Site Class")["Availability"].mean().reset_index()
        st.dataframe(avg_ava, use_container_width=True)
    else:
        st.info("Columns 'Site Class' or 'Availability' not found in data.")

# --- Main App ---
def app():
    col1, col2 = st.columns([9, 1])

    with col1:
        st.title("👷 Resource Performance")

    with col2:
        if st.button("🔄 Refresh Data", help="Reload resource data"):
            st.cache_data.clear()
            st.rerun()

    tab1, tab2 = st.tabs([
        "📌 Rekap Tiket",
        "🧑‍🔧 Rekap Resource",
    ])

    with tab1:
        app_tab1()
    with tab2:
        app_tab2()

