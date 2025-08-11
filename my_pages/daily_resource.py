import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_daily_resource_data
import streamlit.components.v1 as components
import numpy as np
import plotly.express as px
import io

def app_tab1():
    st.subheader("📊 Daily Team Productivity")

    # --- Load Data ---
    df = load_daily_resource_data(sheet_name="Ticket Summary")
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values("Date")

    # --- Cascading Filters ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date_range = st.date_input(
            "Date Range", 
            value=(df["Date"].min(), df["Date"].max())
        )

    filtered_df = df[(df["Date"] >= pd.to_datetime(date_range[0])) & (df["Date"] <= pd.to_datetime(date_range[1]))]

    with col2:
        area_options = ["All"] + sorted(filtered_df["Area"].dropna().unique())
        selected_area = st.selectbox("Area", area_options)

    if selected_area != "All":
        filtered_df = filtered_df[filtered_df["Area"] == selected_area]

    with col3:
        regional_options = ["All"] + sorted(filtered_df["Regional"].dropna().unique())
        selected_regional = st.selectbox("Regional", regional_options)

    if selected_regional != "All":
        filtered_df = filtered_df[filtered_df["Regional"] == selected_regional]

    with col4:
        nop_options = ["All"] + sorted(filtered_df["NOP"].dropna().unique())
        selected_nop = st.selectbox("NOP", nop_options)

    if selected_nop != "All":
        filtered_df = filtered_df[filtered_df["NOP"] == selected_nop]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return

    # --- Aggregated logic per date ---
    grouped = filtered_df.groupby("Date").agg({
        "Total FME": "sum",
        "Total TO": "sum",
        "Total Tickets_x": "sum",
        "Total-Visit_x": "sum",
        "EM-Total" : "sum",
        "IM-Total" : "sum"
    }).reset_index()

    grouped["%Takeover"] = grouped["Total TO"] / grouped["Total Tickets_x"].replace({0: np.nan})
    grouped["%Visit"] = grouped["Total-Visit_x"] / grouped["Total TO"].replace({0: np.nan})

    # Fill NaNs with 0.0 so Plotly will still plot the point
    grouped["%Takeover"] = grouped["%Takeover"].fillna(0.0)
    grouped["%Visit"] = grouped["%Visit"].fillna(0.0)
    grouped["%Takeover_text"] = (grouped["%Takeover"] * 100).round(2).astype(str) + "%"
    grouped["%Visit_text"] = (grouped["%Visit"] * 100).round(2).astype(str) + "%"

    # --- Plot ---
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=grouped["Date"],
        y=grouped["Total FME"],
        name="Total FME",
        marker_color="beige",
        yaxis="y1",
        text=grouped["Total FME"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=16, color="green"),
        hovertemplate="Total FME: %{y}<extra></extra>" 
    ))

    fig.add_trace(go.Scatter(
        x=grouped["Date"],
        y=grouped["%Takeover"],
        name="%Takeover",
        mode="lines+markers+text",
        line=dict(color="green", width=4),
        yaxis="y2",
        text=grouped["%Takeover_text"],
        textposition="top center",
        textfont=dict(size=16, color="green"),
        hovertemplate="%Takeover: %{text}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=grouped["Date"],
        y=grouped["%Visit"],
        name="%Visit",
        mode="lines+markers+text",
        line=dict(color="orange", width=4),
        yaxis="y2",
        text=grouped["%Visit_text"],
        textposition="bottom center",
        textfont=dict(size=16, color="black"),
        hovertemplate="%Visit: %{text}<extra></extra>"
    ))

    fig.update_layout(
        title="📈 Productivity: Total FME vs %Takeover vs %Visit",
        xaxis=dict(
            title=dict(text="Date", font=dict(size=16)),
            tickmode="linear",
            dtick=86400000.0,
            tickformat="%d-%b",
            tickangle=-45  # Optional: to avoid overlapping labels
        ),
        yaxis=dict(
            title=dict(text="Total FME", font=dict(color="steelblue", size=16)),
            tickfont=dict(color="steelblue")
        ),
        yaxis2=dict(
            title=dict(text="%Takeover / %Visit", font=dict(color="green", size=16)),
            tickformat=".0%",
            showgrid=False,
            overlaying="y",
            side="right",
            tickfont=dict(color="green")
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="honeydew",
            font_size=14,
            font_family="Segoe UI"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="right",
            x=1,
            font=dict(size=16)
        ),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Prepare %TO_text and %Visit_x_text ---
    #filtered_df["%TO_text"] = (filtered_df["%TO"] * 100).round(1).astype(str) + "%"
    #filtered_df["%Visit_x_text"] = (filtered_df["%Visit_x"] * 100).round(1).astype(str) + "%"
    # --- Second Chart: IM/EM/Total Tickets and %TO/%Visit ---
    fig2 = go.Figure()

    # Stacked bar for IM-Total and EM-Total
    fig2.add_trace(go.Bar(
        x=grouped["Date"],
        y=grouped["IM-Total"],
        name="IM-Total",
        marker_color="lavender",
        yaxis="y1",
        text=grouped["IM-Total"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=16, color="black"),
        hovertemplate="IM-Total: %{y}<extra></extra>"
    ))

    fig2.add_trace(go.Bar(
        x=grouped["Date"],
        y=grouped["EM-Total"],
        name="EM-Total",
        marker_color="beige",
        yaxis="y1",
        text=grouped["EM-Total"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=16, color="black"),
        hovertemplate="EM-Total: %{y}<extra></extra>"
    ))

    # Line for Total Tickets_x
    fig2.add_trace(go.Scatter(
        x=grouped["Date"],
        y=grouped["Total Tickets_x"],
        name="Total Tickets",
        mode="lines+markers+text",
        line=dict(color="firebrick", width=4),
        yaxis="y1",
        text=grouped["Total Tickets_x"],
        textposition="top center",
        textfont=dict(size=16, color="firebrick"),
        hovertemplate="Total Tickets: %{y}<extra></extra>"
    ))

    # %TO Line
    fig2.add_trace(go.Scatter(
        x=grouped["Date"],
        y=grouped["%Takeover"],
        name="%Takeover",
        mode="lines+markers+text",
        line=dict(color="green", width=4),
        yaxis="y2",
        text=grouped["%Takeover_text"],
        textposition="top center",
        textfont=dict(size=16, color="green"),
        hovertemplate="%Takeover: %{y:.2%}<extra></extra>"
    ))

    # %Visit Line
    fig2.add_trace(go.Scatter(
        x=grouped["Date"],
        y=grouped["%Visit"],
        name="%Visit",
        mode="lines+markers+text",
        line=dict(color="orange", width=4),
        yaxis="y2",
        text=grouped["%Visit_text"],
        textposition="bottom center",
        textfont=dict(size=16, color="black"),
        hovertemplate="%Visit: %{y:.2%}<extra></extra>"
    ))

    fig2.update_layout(
        title="📊 IM (Incident)/EM (Event) Tickets vs Total Tickets vs %Takeover vs %Visit",
        barmode="stack",
        xaxis=dict(
            title=dict(text="Date", font=dict(size=16)),
            tickmode="linear",
            dtick=86400000.0,
            tickformat="%d-%b",
            tickangle=-45  # Optional: to avoid overlapping labels
        ),
        yaxis=dict(
            title=dict(text="Ticket Volume", font=dict(color="steelblue", size=16)),
            tickfont=dict(color="steelblue")
        ),
        yaxis2=dict(
            title=dict(text="%Takeover / %Visit", font=dict(color="green", size=16)),
            tickformat=".0%",
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(color="green")
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="honeydew",
            font_size=14,
            font_family="Segoe UI"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="right",
            x=1,
            font=dict(size=16)
        ),
        height=500
    )

    st.plotly_chart(fig2, use_container_width=True)

    # --- BPS Aggregated logic per date ---
    grouped_bps = filtered_df.groupby("Date").agg({
        "BPS-Total": "sum",
        "BPS-Takeover": "sum",
        "BPS-Visit": "sum"
    }).reset_index()

    grouped_bps["BPS-%Takeover"] = grouped_bps["BPS-Takeover"] / grouped_bps["BPS-Total"].replace({0: np.nan})
    grouped_bps["BPS-%Visit"] = grouped_bps["BPS-Visit"] / grouped_bps["BPS-Takeover"].replace({0: np.nan})
    grouped_bps["BPS-%Takeover"] = grouped_bps["BPS-%Takeover"].fillna(0.0)
    grouped_bps["BPS-%Visit"] = grouped_bps["BPS-%Visit"].fillna(0.0)
    grouped_bps["BPS-%Takeover_text"] = (grouped_bps["BPS-%Takeover"] * 100).round(2).astype(str) + "%"
    grouped_bps["BPS-%Visit_text"] = (grouped_bps["BPS-%Visit"] * 100).round(2).astype(str) + "%"

    # --- TS Aggregated logic per date ---
    grouped_ts = filtered_df.groupby("Date").agg({
        "TS-Total": "sum",
        "TS-Takeover": "sum",
        "TS-Visit": "sum"
    }).reset_index()

    grouped_ts["TS-%Takeover"] = grouped_ts["TS-Takeover"] / grouped_ts["TS-Total"].replace({0: np.nan})
    grouped_ts["TS-%Visit"] = grouped_ts["TS-Visit"] / grouped_ts["TS-Takeover"].replace({0: np.nan})
    grouped_ts["TS-%Takeover"] = grouped_ts["TS-%Takeover"].fillna(0.0)
    grouped_ts["TS-%Visit"] = grouped_ts["TS-%Visit"].fillna(0.0)
    grouped_ts["TS-%Takeover_text"] = (grouped_ts["TS-%Takeover"] * 100).round(2).astype(str) + "%"
    grouped_ts["TS-%Visit_text"] = (grouped_ts["TS-%Visit"] * 100).round(2).astype(str) + "%"
    
    # --- Format percentage fields ---
    filtered_df["BPS-%Takeover_text"] = (filtered_df["BPS-%Takeover"] * 100).round(2).astype(str) + "%"
    filtered_df["BPS-%Visit_text"] = (filtered_df["BPS-%Visit"] * 100).round(2).astype(str) + "%"
    filtered_df["TS-%Takeover_text"] = (filtered_df["TS-%Takeover"] * 100).round(2).astype(str) + "%"
    filtered_df["TS-%Visit_text"] = (filtered_df["TS-%Visit"] * 100).round(2).astype(str) + "%"

    col1, col2 = st.columns(2)

    # --- BPS Chart ---
    with col1:
        fig_bps = go.Figure()

        fig_bps.add_trace(go.Bar(
            x=grouped_bps["Date"],
            y=grouped_bps["BPS-Total"],
            name="BPS-Total",
            marker_color="aliceblue",
            yaxis="y1",
            text=grouped_bps["BPS-Total"],
            textposition="inside",
            insidetextanchor="start",
            textfont=dict(size=16, color="black"),
            hovertemplate="BPS Total: %{y}<extra></extra>"
        ))

        fig_bps.add_trace(go.Scatter(
            x=grouped_bps["Date"],
            y=grouped_bps["BPS-%Takeover"],
            name="BPS-%Takeover",
            mode="lines+markers+text",
            line=dict(color="green", width=4),
            yaxis="y2",
            text=grouped_bps["BPS-%Takeover_text"],
            textposition="top center",
            textfont=dict(size=16),
            hovertemplate="BPS-%Takeover: %{y:.2%}<extra></extra>"
        ))

        fig_bps.add_trace(go.Scatter(
            x=grouped_bps["Date"],
            y=grouped_bps["BPS-%Visit"],
            name="BPS-%Visit",
            mode="lines+markers+text",
            line=dict(color="orange", width=4),
            yaxis="y2",
            text=grouped_bps["BPS-%Visit_text"],
            textposition="bottom center",
            textfont=dict(size=16),
            hovertemplate="BPS-%Visit: %{y:.2%}<extra></extra>"
        ))

        fig_bps.update_layout(
            title="👷‍♂️ BPS Productivity",
            xaxis=dict(
                title=dict(text="Date", font=dict(size=16)),
                tickmode="linear",
                dtick=86400000.0,
                tickformat="%d-%b",
                tickangle=-45  # Optional: to avoid overlapping labels
            ),
            yaxis=dict(
                title=dict(text="BPS-Total", font=dict(size=16, color="steelblue")),
                tickfont=dict(color="steelblue")
            ),
            yaxis2=dict(
                title=dict(text="%Takeover / %Visit", font=dict(size=16, color="green")),
                tickformat=".0%",
                showgrid=False,
                overlaying="y",
                side="right",
                tickfont=dict(color="green")
            ),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="honeydew", font_size=14, font_family="Segoe UI"),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="right", x=1, font=dict(size=14)),
            height=400
        )

        st.plotly_chart(fig_bps, use_container_width=True)

    # --- TS Chart ---
    with col2:
        fig_ts = go.Figure()

        fig_ts.add_trace(go.Bar(
            x=grouped_ts["Date"],
            y=grouped_ts["TS-Total"],
            name="TS-Total",
            marker_color="mistyrose",
            yaxis="y1",
            text=grouped_ts["TS-Total"],
            textposition="inside",
            insidetextanchor="start",
            textfont=dict(size=16, color="black"),
            hovertemplate="TS Total: %{y}<extra></extra>"
        ))

        fig_ts.add_trace(go.Scatter(
            x=grouped_ts["Date"],
            y=grouped_ts["TS-%Takeover"],
            name="TS-%Takeover",
            mode="lines+markers+text",
            line=dict(color="green", width=4),
            yaxis="y2",
            text=grouped_ts["TS-%Takeover_text"],
            textposition="top center",
            textfont=dict(size=16),
            hovertemplate="TS-%Takeover: %{y:.2%}<extra></extra>"
        ))

        fig_ts.add_trace(go.Scatter(
            x=grouped_ts["Date"],
            y=grouped_ts["TS-%Visit"],
            name="TS-%Visit",
            mode="lines+markers+text",
            line=dict(color="orange", width=4),
            yaxis="y2",
            text=grouped_ts["TS-%Visit_text"],
            textposition="bottom center",
            textfont=dict(size=16),
            hovertemplate="TS-%Visit: %{y:.2%}<extra></extra>"
        ))

        fig_ts.update_layout(
            title="🧰 TS Productivity",
            xaxis=dict(
                title=dict(text="Date", font=dict(size=16)),
                tickmode="linear",
                dtick=86400000.0,
                tickformat="%d-%b",
                tickangle=-45  # Optional: to avoid overlapping labels
            ),
            yaxis=dict(
                title=dict(text="TS-Total", font=dict(size=16, color="steelblue")),
                tickfont=dict(color="steelblue")
            ),
            yaxis2=dict(
                title=dict(text="%Takeover / %Visit", font=dict(size=16, color="green")),
                tickformat=".0%",
                showgrid=False,
                overlaying="y",
                side="right",
                tickfont=dict(color="green")
            ),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="honeydew", font_size=14, font_family="Segoe UI"),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="right", x=1, font=dict(size=14)),
            height=400
        )

        st.plotly_chart(fig_ts, use_container_width=True)
    
    # --- Download filtered chart data as Excel ---
    import io

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer, sheet_name="ChartData", index=False)
        #writer.close()

    st.download_button(
        label="📥 Download All Chart Data",
        data=output.getvalue(),
        file_name="daily_team_productivity_chart_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def app_tab2():
    st.subheader("📊 Daily Rekap Resource")

    # --- Load data ---
    df = load_daily_resource_data(sheet_name="Daily PIC Summary")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # --- Get full min/max before filtering ---
    min_date, max_date = df["Date"].min(), df["Date"].max()

    # --- Filters: All in one row ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date_range = st.date_input("📅 Date Range", (min_date, max_date), key="tab2_date")

    with col2:
        area_options = ["All"] + sorted(df["Area"].dropna().unique())
        selected_area = st.selectbox("📍 Area", area_options, key="tab2_area")

    with col3:
        filtered_df_for_regional = df if selected_area == "All" else df[df["Area"] == selected_area]
        regional_options = ["All"] + sorted(filtered_df_for_regional["Regional"].dropna().unique())
        selected_regional = st.selectbox("📌 Regional", regional_options, key="tab2_regional")

    with col4:
        filtered_df_for_nop = filtered_df_for_regional if selected_regional == "All" else filtered_df_for_regional[filtered_df_for_regional["Regional"] == selected_regional]
        nop_options = ["All"] + sorted(filtered_df_for_nop["NOP"].dropna().unique())
        selected_nop = st.selectbox("👷 NOP", nop_options, key="tab2_nop")

    # --- Apply filters to main DataFrame ---
    df = df[
        (df["Date"] >= pd.to_datetime(date_range[0])) &
        (df["Date"] <= pd.to_datetime(date_range[1]))
    ]
    if selected_area != "All":
        df = df[df["Area"] == selected_area]
    if selected_regional != "All":
        df = df[df["Regional"] == selected_regional]
    if selected_nop != "All":
        df = df[df["NOP"] == selected_nop]

    # --- Grouping for Chart ---
    bps_status = df.groupby(["Date", "BPS Status"]).size().unstack(fill_value=0).reset_index()
    ts_status = df.groupby(["Date", "TS Status"]).size().unstack(fill_value=0).reset_index()

    # --- Color mapping for consistent legend ---
    status_colors = {
        "Excellent": "#A1D99B",  # light green
        "Good": "#9ECAE1",       # light blue
        "Poor": "#FDBB84",       # light orange
        "Zero": "#D9D9D9"        # light gray
    }

    # --- Two Charts Side-by-Side ---
    col1, col2 = st.columns(2)

    with col1:
        fig_bps = go.Figure()
        for col in status_colors.keys():
            if col in bps_status.columns:
                fig_bps.add_trace(go.Bar(
                    x=bps_status["Date"],
                    y=bps_status[col],
                    name=col,
                    text=bps_status[col],
                    textposition="inside",
                    textfont=dict(size=18),
                    hovertemplate="%{fullData.name}: %{y}<extra></extra>",
                    marker=dict(color=status_colors[col])
                ))
        fig_bps.update_layout(
            barmode="stack",
            title="📊 BPS Status per Date",
            xaxis=dict(
                title=dict(text="Date", font=dict(size=16)),
                tickmode="linear",
                dtick=86400000.0,
                tickformat="%d-%b",
                tickangle=-45  # Optional: to avoid overlapping labels
            ),
            yaxis_title="Jumlah PIC",
            hovermode="x unified",
            hoverlabel=dict(bgcolor="honeydew", font_size=14, font_family="Segoe UI"),
            legend=dict(orientation="h", y=-0.25, x=1, xanchor="right", font=dict(size=14)),
            height=400
        )
        st.plotly_chart(fig_bps, use_container_width=True)

    with col2:
        fig_ts = go.Figure()
        for col in status_colors.keys():
            if col in ts_status.columns:
                fig_ts.add_trace(go.Bar(
                    x=ts_status["Date"],
                    y=ts_status[col],
                    name=col,
                    text=ts_status[col],
                    textposition="inside",
                    textfont=dict(size=18),
                    hovertemplate="%{fullData.name}: %{y}<extra></extra>",
                    marker=dict(color=status_colors[col])
                ))
        fig_ts.update_layout(
            barmode="stack",
            title="📊 TS Status per Date",
            xaxis=dict(
                title=dict(text="Date", font=dict(size=16)),
                tickmode="linear",
                dtick=86400000.0,
                tickformat="%d-%b",
                tickangle=-45  # Optional: to avoid overlapping labels
            ),
            yaxis_title="Jumlah PIC",
            hovermode="x unified",
            hoverlabel=dict(bgcolor="honeydew", font_size=14, font_family="Segoe UI"),
            legend=dict(orientation="h", y=-0.25, x=1, xanchor="right", font=dict(size=14)),
            height=400
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    from io import BytesIO
    import xlsxwriter

    # --- Prepare Excel output for chart data ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        bps_status.to_excel(writer, sheet_name='BPS Status', index=False)
        ts_status.to_excel(writer, sheet_name='TS Status', index=False)
        writer.close()

    # --- Prepare Excel output for raw data ---
    raw_output = BytesIO()
    with pd.ExcelWriter(raw_output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        writer.close()

    # --- Display both buttons side by side ---
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        st.download_button(
            label="📥 Download Chart Data (Excel)",
            data=output.getvalue(),
            file_name="daily_rekap_resource_status.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with btn_col2:
        st.download_button(
            label="📥 Download Raw Data (Excel)",
            data=raw_output.getvalue(),
            file_name="daily_rekap_resource_raw_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def render_colored_table(df_grouped, date_columns):
        import streamlit.components.v1 as components
        from datetime import datetime

        fixed_columns = [
            "Area", "Regional", "NOP", "PIC Take Over Ticket",
            "TO-Total", "IM-TO", "IM-TO-Visit", "EM-TO", "EM-TO-Visit"
        ]

        # Add row numbering
        df_grouped = df_grouped.reset_index(drop=True)
        df_grouped.insert(0, "No.", df_grouped.index + 1)
        fixed_columns_with_no = ["No."] + fixed_columns

        # Define value-to-color mapping
        def get_color(val):
            try:
                val = float(val)
                if val >= 4:
                    return "#A1D99B"  # green
                elif 2 <= val <= 3:
                    return "#9ECAE1"  # blue
                elif val == 1:
                    return "#FDBB84"  # orange
                elif val == 0:
                    return "#D9D9D9"  # grey
                else:
                    return "white"
            except:
                return "white"

        def style_cell(val, col):
            if col in date_columns:
                try:
                    val_num = float(val)
                    color = get_color(val_num)
                    val_disp = f"{int(val_num)}"
                    return f'<td style="background-color:{color};">{val_disp}</td>'
                except:
                    return f"<td>{val}</td>"
            else:
                return f'<td>{val}</td>'

        # Build headers
        #headers_fixed = ''.join([f"<th>{col}</th>" for col in fixed_columns])
        #headers_dates = ''.join([f"<th>{col}</th>" for col in date_columns])
        headers_fixed = ''.join([f"<th>{col}</th>" for col in fixed_columns_with_no])
        headers_dates = ''.join([
            f'<th class="rotate"><div><span>{datetime.strptime(col, "%Y-%m-%d").strftime("%d-%b-%y")}</span></div></th>'
            for col in date_columns
        ])
        headers = headers_fixed + headers_dates

        # Build rows
        rows = ""
        for _, row in df_grouped.iterrows():
            #row_fixed = ''.join([style_cell(row[col], col) for col in fixed_columns])
            row_fixed = ''.join([style_cell(row[col], col) for col in fixed_columns_with_no])
            row_dates = ''.join([style_cell(row[col], col) for col in date_columns])
            rows += f"<tr>{row_fixed}{row_dates}</tr>"

        # Compose final HTML
        table_html = f"""
        <style>
            .custom-table-container {{
                overflow-x: auto;
                width: 100%;
                max-height: 850px;
                overflow-y: auto;
            }}
            table {{
                border-collapse: collapse;
                font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
                font-size: 18px;
                color: #333;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px 8px;
                text-align: center;
                vertical-align: middle;
                white-space: nowrap;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                position: sticky;
                top: 0;
                z-index: 2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
        </style>
        <div class="custom-table-container">
            <table>
                <thead><tr>{headers}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        #components.html(table_html, height=850, scrolling=False)


    # --- Compute IM/EM Visit ---
    df["IM-TO-Visit"] = (
        df["IM-TO-Visit(Crit+Maj)-Visit"].fillna(0) +
        df["IM-TO-Visit(Minor+Low)-Visit"].fillna(0)
    )
    df["EM-TO-Visit"] = (
        df["EM-TO-Visit(Crit+Maj)-Visit"].fillna(0) +
        df["EM-TO-Visit(Min+Low)-Visit"].fillna(0)
    )

    # --- Group and Pivot ---
    group_cols = ["Area", "Regional", "NOP", "PIC Take Over Ticket", "Date"]
    agg_df = df.groupby(group_cols).agg({
        "TO-Total": "sum",
        "IM-TO": "sum",
        "IM-TO-Visit": "sum",
        "EM-TO": "sum",
        "EM-TO-Visit": "sum"
    }).reset_index()

    # --- Sum across all dates for totals ---
    summary_df = agg_df.groupby(["Area", "Regional", "NOP", "PIC Take Over Ticket"]).agg({
        "TO-Total": "sum",
        "IM-TO": "sum",
        "IM-TO-Visit": "sum",
        "EM-TO": "sum",
        "EM-TO-Visit": "sum"
    }).reset_index()

    # --- Pivot per Date for TO-Total ---
    pivot_df = agg_df.pivot_table(
        index=["Area", "Regional", "NOP", "PIC Take Over Ticket"],
        columns="Date",
        values="TO-Total",
        aggfunc="sum"
    ).fillna(0).reset_index()

    # --- Merge total summary with pivoted date columns ---
    recap_df = summary_df.merge(pivot_df, on=["Area", "Regional", "NOP", "PIC Take Over Ticket"])

    # --- Format date columns ---
    recap_df.columns = [
        col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else col
        for col in recap_df.columns
    ]

    # --- Identify dynamic date columns for styling ---
    date_columns = [col for col in recap_df.columns if col not in [
        "Area", "Regional", "NOP", "PIC Take Over Ticket", "TO-Total", "IM-TO", "IM-TO-Visit", "EM-TO", "EM-TO-Visit"
    ]]

    # --- Sort by TO-Total within Area, Regional, and NOP ---
    recap_df["TO-Total"] = pd.to_numeric(recap_df["TO-Total"], errors="coerce").fillna(0)
    recap_df = recap_df.sort_values(
        by=["Area", "Regional", "NOP", "TO-Total"],
        ascending=[True, True, True, False]
    )
    # recap_df.insert(0, "No.", range(1, len(recap_df) + 1))
    # --- Show styled recap table ---
    st.markdown("### 📋 Rekap Takeover per PIC Daily")
    render_colored_table(recap_df, date_columns=date_columns)

    # --- Add download button ---
    csv_data = recap_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Tabel Rekap to CSV",
        data=csv_data,
        file_name="rekap_to_per_pic.csv",
        mime="text/csv"
    )

def render_html_table_with_scroll(df):
    styles = """
    <style>
    .table-container {
        width: 100%;
        max-height: 400px;
        overflow-y: auto;
        overflow-x: auto;
        border: 1px solid #ddd;
    }
    table {
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
        min-width: 800px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
        white-space: nowrap;
    }
    thead th {
        background-color: #4a90e2;
        color: white;
        font-size: 16px;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    tbody tr:nth-child(even) {
        background-color: #f5f7fa;
    }
    tbody tr:hover {
        background-color: #d0e4f5;
    }
    .total-col {
        font-weight: bold;
        font-size: 18px;
        background-color: #fffbcc;
    }
    .green-bg {
        background-color: #d4edda; /* light green */
        color: #155724;
        font-weight: bold;
    }
    .orange-bg {
        background-color: #ffe5b4; /* light orange */
        color: #7f4b00;
        font-weight: bold;
    }
    .red-bg {
        background-color: #f8d7da; /* light red */
        color: #721c24;
        font-weight: bold;
    }
    </style>
    """

    df_formatted = df.copy()
    # Format numeric columns as int (whole numbers)
    for col in df_formatted.columns:
        if col not in ["Regional name", "Nop name", "Pic name"]:
            try:
                df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce').fillna(0).astype(int)
            except Exception:
                pass

    def style_cell(col_name, val):
        # Style only date columns (excluding 'Total' and text columns)
        if col_name == "Total":
            return f'<td class="total-col">{val}</td>'
        elif col_name not in ["Regional name", "Nop name", "Pic name"]:
            # Apply color coding
            if val >= 2:
                return f'<td class="green-bg">{val}</td>'
            elif val == 1:
                return f'<td class="orange-bg">{val}</td>'
            else:
                return f'<td class="red-bg">{val}</td>'
        else:
            # Default style for text columns
            return f'<td>{val}</td>'

    table_html = "<table><thead><tr>"
    for col in df_formatted.columns:
        table_html += f"<th>{col}</th>"
    table_html += "</tr></thead><tbody>"
    for _, row in df_formatted.iterrows():
        row_html = ""
        for i, val in enumerate(row):
            col_name = df_formatted.columns[i]
            row_html += style_cell(col_name, val)
        table_html += f"<tr>{row_html}</tr>"
    table_html += "</tbody></table>"

    return styles + f"<div class='table-container'>{table_html}</div>"

def app_tab3():
    st.subheader("📊 Rekap Tiket FNA Daily")

    # --- Load data ---
    df = load_daily_resource_data(sheet_name="Daily FNA")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # --- Get full min/max before filtering ---
    min_date, max_date = df["Date"].min(), df["Date"].max()

    # --- Filters in one row ---
    col_date, col1, col2, col3 = st.columns([2, 1, 1, 1])  # Wider col for date

    with col_date:
        date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.error("Please select a valid date range.")
        return

    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    # Filter by selected date range
    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if filtered_df.empty:
        st.warning("No data found in the selected date range.")
        return

    with col1:
        regional_options = sorted(filtered_df["Regional name"].dropna().unique())
        selected_regional = st.selectbox("Regional name", options=["-- All --"] + regional_options)

    if selected_regional != "-- All --":
        filtered_df = filtered_df[filtered_df["Regional name"] == selected_regional]

    with col2:
        nop_options = sorted(filtered_df["Nop name"].dropna().unique())
        if nop_options:
            selected_nop = st.selectbox("Nop name", options=["-- All --"] + nop_options)
        else:
            st.warning("No Nop name available for selected Regional name.")
            return

    if selected_nop != "-- All --":
        filtered_df = filtered_df[filtered_df["Nop name"] == selected_nop]

    with col3:
        pic_options = sorted(filtered_df["Pic name"].dropna().unique())
        if pic_options:
            selected_pic = st.selectbox("Pic name", options=["-- All --"] + pic_options)
        else:
            st.warning("No Pic name available for selected filters.")
            return

    if selected_pic != "-- All --":
        filtered_df = filtered_df[filtered_df["Pic name"] == selected_pic]

    if filtered_df.empty:
        st.warning("No data found for selected filters.")
        return

    # --- Create pivot table ---
    pivot_df = (
        filtered_df.groupby(["Regional name", "Nop name", "Pic name", "Date"])
        .size()
        .reset_index(name="Count")
        .pivot_table(
            index=["Regional name", "Nop name", "Pic name"],
            columns="Date",
            values="Count",
            fill_value=0
        )
    )

    all_dates = pd.date_range(start=start_date, end=end_date)
    pivot_df = pivot_df.reindex(columns=all_dates, fill_value=0)

    pivot_df["Total"] = pivot_df.sum(axis=1)

    pivot_df = pivot_df[["Total"] + list(all_dates)]

    pivot_df.columns = ["Total"] + [d.strftime("%Y-%m-%d") for d in all_dates]

    display_df = pivot_df.reset_index()

    # --- Aggregate daily counts for line chart ---
    daily_counts = (
        filtered_df.groupby("Date")
        .size()
        .reindex(all_dates, fill_value=0)
        .rename("Count")
        .reset_index()
    )
    daily_counts.columns = ["Date", "Count"]

    #st.markdown("### 📈 Daily FNA Chart")
    # st.line_chart(data=daily_counts.set_index("Date"))
    # Assuming daily_counts is your DataFrame with columns: "Date" and "Count"
    fig = px.line(
        daily_counts,
        x="Date",
        y="Count",
        labels={"Date": "Date", "Count": "FNA"},
        title="📈 Daily FNA Chart"
    )

    fig.update_traces(
        mode="lines+markers+text",        # Show line, markers, and text labels
        line=dict(width=4),               # Thicker line (default is 2)
        text=daily_counts["Count"],       # Label each data point with count
        textposition="top center",         # Position labels above markers
        textfont=dict(
            size=14,          # font size in pixels
            family="Arial",   # optional font family
            color="black"     # optional font color
        ),
        hovertemplate= 'Ticket FNA : %{y}<extra></extra>'
    )

    max_y = daily_counts["Count"].max()
    min_y = 0  # or daily_counts["Count"].min() if you want dynamic min
    fig.update_layout(
        xaxis=dict(
            tickformat="%Y-%m-%d",
            tickangle=-45,
            dtick="D1",
            showgrid=False              # Hide x-axis gridlines
        ),
        yaxis=dict(
        showgrid=True,
            gridcolor='LightGray',
            range=[min_y, max_y + 5]   # set y-axis range with padding
        ),
        plot_bgcolor="white",
        title_font=dict(size=24),
        xaxis_title_font=dict(size=18),
        yaxis_title_font=dict(size=18),
        xaxis_tickfont=dict(size=14),
        yaxis_tickfont=dict(size=14),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="azure",      # background color of hover label
            font_size=14,         # font size in px
            font_family="Arial",  # font family
            font_color="black",   # font color
            bordercolor="gray"    # border color of hover label box
        ),
        height=650
    )

    st.plotly_chart(fig, use_container_width=True)

    display_df["Total"] = pd.to_numeric(display_df["Total"], errors='coerce').fillna(0).astype(int)
    display_df_sorted = display_df.sort_values(
        by=["Regional name", "Nop name", "Total"],
        ascending=[True, True, False]
    ).reset_index(drop=True)
    
    html_table = render_html_table_with_scroll(display_df_sorted)
    st.markdown(html_table, unsafe_allow_html=True)
    # Convert DataFrame to Excel bytes
    def to_excel_bytes(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.save()
        return output.getvalue()

    # Prepare Excel bytes from your sorted df
    excel_data = to_excel_bytes(display_df_sorted)

    # Add Streamlit download button
    st.download_button(
        label="📥 Download Rekap FNA",
        data=excel_data,
        file_name="rekap_fna_daily.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def app():
    col1, col2 = st.columns([9, 1])

    with col1:
        st.title("📅 Daily Team Productivity Dashboard")

    with col2:
        if st.button("🔄 Refresh Data", help="Reload resource data"):
            st.cache_data.clear()
            st.rerun()
            
    
    tab1, tab2, tab3 = st.tabs(["🎟️ Rekap Tiket Daily", "📊 Daily Rekap Resource", "Daily FNA"])

    with tab1:
        app_tab1()

    with tab2:
        app_tab2()

    with tab3:
        app_tab3()







