import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import calendar
from datetime import datetime

# --- Streamlit page config ---
st.set_page_config(page_title="ENOM Dashboard", layout="wide")

# --- Sidebar Navigation (Custom Buttons) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>📊 ENOM Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")  # horizontal line

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "📈 ENOM KPI"

    # Use one column to stack buttons vertically
    col = st.container()
    with col:
        kpi_clicked = st.button("📈 ENOM KPI SONL1", use_container_width=True)
        availability_clicked = st.button("📅 Monthly Availability", use_container_width=True)


    # Update session state based on button clicked
    if kpi_clicked:
        st.session_state.page = "📈 ENOM KPI"
    elif availability_clicked:
        st.session_state.page = "📅 Monthly Availability"

# --- Load Data for ENOM KPI ---
@st.cache_data
def load_kpi_data():
    df = pd.read_excel("data/enom_kpi.xlsx", sheet_name="KPI")
    
    # Parse Period_str into Month and Year
    df["Period_str"] = df["Period_str"].astype(str).str.strip()
    df["Month"] = pd.to_datetime(df["Period_str"], format="%b-%y").dt.strftime("%b")
    df["Year"] = pd.to_datetime(df["Period_str"], format="%b-%y").dt.year.astype(str)
    
    return df

# --- Load Data for Monthly Availability ---
@st.cache_data
def load_data_ava_monthly():
    def clean_month(df):
        df['Month'] = df['Month'].astype(str).str.strip().str[:3].str.title()
        return df

    regional = pd.read_csv("data/availability_regional.csv")
    nop = pd.read_csv("data/availability_nop.csv")
    site = pd.read_csv("data/availability_site.csv")

    return clean_month(regional), clean_month(nop), clean_month(site)

regional_data, nop_data, site_data = load_data_ava_monthly()

last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Chart Function ---
def plot_line_chart(df, group_col, filters, base_title, y_range):
    filtered = df.copy()
    for col, val in filters.items():
        if val != "All":
            filtered = filtered[filtered[col] == val]

    st.write(f"Number of rows after filtering: {len(filtered)}")
    if filtered.empty:
        st.warning(f"No valid data available after filtering for {base_title}.")
        return

    filtered["Availability (Ave)"] = pd.to_numeric(filtered["Availability (Ave)"], errors='coerce')
    filtered.dropna(subset=["Availability (Ave)", "Month"], inplace=True)

    grouped = filtered.groupby(["Month", group_col], as_index=False)["Availability (Ave)"].mean()
    grouped['Month'] = grouped['Month'].str.strip().str[:3].str.title()
    valid_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    grouped = grouped[grouped['Month'].isin(valid_months)]

    try:
        grouped['Month'] = pd.to_datetime(grouped['Month'] + '-2025', format='%b-%Y')
    except Exception as e:
        st.error(f"Error converting months: {e}")
        return

    grouped.sort_values(by=['Month', group_col], inplace=True)
    grouped['Availability (Ave)'] = grouped['Availability (Ave)'].astype(float).round(2)

    filter_text = ", ".join([f"{k.title()}: {v}" for k, v in filters.items() if v != "All"])
    dynamic_title = f"{base_title}" + (f" ({filter_text})" if filter_text else "")

    fig = px.line(
        grouped,
        x="Month",
        y="Availability (Ave)",
        color=group_col,
        markers=True,
        title=dynamic_title,
        text=grouped["Availability (Ave)"].astype(str)
    )

    fig.update_layout(
        yaxis=dict(range=y_range, title="Availability (%)"),
        xaxis=dict(title="Month", tickformat="%b %Y", tickvals=grouped['Month'].dt.to_pydatetime()),
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_traces(textposition="bottom center", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# --- Main Content: ENOM KPI Placeholder ---
if st.session_state.page == "📈 ENOM KPI":
    st.title("📈 ENOM KPI SONL1")

    # Create tabs
    tab1, tab2 = st.tabs(["📈 ENOM KPI SONL1", "📊 Trend KPI SONL1"])

    # Load KPI data
    df_kpi = load_kpi_data()
    with tab1:
        st.subheader("📈 ENOM KPI SONL1")
    
        # --- Filters ---
        col1, col2, col3, col4, col5 = st.columns(5)

        # Start with full dataset for filtering
        filter_df = df_kpi.copy()

        with col1:
            area_list = ["All"] + sorted(filter_df["Area"].dropna().unique())
            selected_area = st.selectbox("Select Area", area_list)

        # Apply Area filter first
        if selected_area != "All":
            filter_df = filter_df[filter_df["Area"] == selected_area]

        with col2:
            regional_list = ["All"] + sorted(filter_df["Regional"].dropna().unique())
            selected_regional = st.selectbox("Select Regional", regional_list)

        # Apply Regional filter next
        if selected_regional != "All":
            filter_df = filter_df[filter_df["Regional"] == selected_regional]

        with col3:
            nop_list = ["All"] + sorted(filter_df["NOP"].dropna().unique())
            selected_nop = st.selectbox("Select NOP", nop_list)

        # Apply NOP filter
        if selected_nop != "All":
            filter_df = filter_df[filter_df["NOP"] == selected_nop]

        # Define the calendar order of months
        month_order = list(calendar.month_abbr)[1:]  # ['Jan', 'Feb', ..., 'Dec']
        unique_months = filter_df["Month"].dropna().unique()
        sorted_months = sorted(unique_months, key=lambda x: month_order.index(x))

        with col4:
            month_list = ["All"] + sorted_months
            selected_month = st.selectbox("Select Month", month_list)

        if selected_month != "All":
            filter_df = filter_df[filter_df["Month"] == selected_month]

        with col5:
            year_list = ["All"] + sorted(filter_df["Year"].dropna().unique())
            selected_year = st.selectbox("Select Year", year_list)

        if selected_year != "All":
            filter_df = filter_df[filter_df["Year"] == selected_year]

        # Define a function to apply the background colors based on the value
        def color_final_kpi(val):
            color = ''
            if val < 80:
                color = 'background-color: #FF0000'
            elif 80 <= val < 85:
                color = 'background-color: orange'
            elif 85 <= val < 90:
                color = 'background-color: #92D050'
            elif 90 <= val < 95:
                color = 'background-color: #00B050'
            elif val >= 95:
                color = 'background-color: #00B0F0'
            return color
    
        # Apply the conditional formatting only to the "Final KPI" column
        def apply_conditional_formatting(df):
                styled_df = df.style.applymap(color_final_kpi, subset=['Final KPI'])
                return styled_df

        # Final filtered dataframe
        filtered_df = filter_df

        # --- Columns to Display --- 
        columns_to_show = [
            "NOP", "Period_str", "Final KPI", "KPI A", "KPI B", "A1", "A2", "A3", "A4", "A5", "A6",
            "B1", "B2.1", "B2.2", "B2.3", "B3", "B4.1", "B4.2", "B5.1", "B5.2"
        ]

        # Select the columns to show
        display_df = filtered_df[columns_to_show].reset_index(drop=True)

        # Round the selected columns to 2 decimal places and format them
        display_df[columns_to_show] = display_df[columns_to_show].applymap(lambda x: "{:.2f}".format(x) if isinstance(x, (int, float)) else x)

        # Convert 'Final KPI' to numeric and round it to 2 decimal places
        display_df['Final KPI'] = pd.to_numeric(display_df['Final KPI'], errors='coerce').round(2)

        # Start the index from 1 instead of 0
        display_df.index += 1

        # Apply the conditional formatting to the 'Final KPI' column
        styled_df = display_df.style.applymap(color_final_kpi, subset=['Final KPI']).format({'Final KPI': "{:.2f}"})

        # Show the table in the Streamlit app without additional styling
        st.dataframe(styled_df, use_container_width=True)

        # --- Download as Excel ---
        import io

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            display_df.to_excel(writer, index=False, sheet_name='ENOM_KPI')
        
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Save to Excel File",
            data=processed_data,
            file_name="ENOM_KPI_Filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- Tab 2: KPI Trend ---
    with tab2:
        st.subheader("📊 Trend KPI SONL1")
        df_kpi_trend = df_kpi.copy()

        # --- Create cascading filters ---
        col1, col2, col3 = st.columns(3)

        with col1:
            area_list = ["All"] + sorted(df_kpi_trend["Area"].dropna().unique())
            selected_area = st.selectbox("Select Area", area_list, key="trend_area")

        with col2:
            regional_filtered = df_kpi_trend[df_kpi_trend["Area"] == selected_area] if selected_area != "All" else df_kpi_trend
            regional_list = ["All"] + sorted(regional_filtered["Regional"].dropna().unique())
            selected_regional = st.selectbox("Select Regional", regional_list, key="trend_regional")

        with col3:
            nop_filtered = regional_filtered[regional_filtered["Regional"] == selected_regional] if selected_regional != "All" else regional_filtered
            nop_list = ["All"] + sorted(nop_filtered["NOP"].dropna().unique())
            selected_nop = st.selectbox("Select NOP", nop_list, key="trend_nop")

        filters = {
            "Area": selected_area,
            "Regional": selected_regional,
            "NOP": selected_nop
        }

        # --- Apply filters from dict ---
        filtered_df = df_kpi_trend.copy()
        if filters["Area"] != "All":
            filtered_df = filtered_df[filtered_df["Area"] == filters["Area"]]
        if filters["Regional"] != "All":
            filtered_df = filtered_df[filtered_df["Regional"] == filters["Regional"]]
        if filters["NOP"] != "All":
            filtered_df = filtered_df[filtered_df["NOP"] == filters["NOP"]]

        # --- Parse Month for proper ordering ---
        try:
            filtered_df["Month_dt"] = pd.to_datetime(filtered_df["Period_str"], format="%b-%y", errors="coerce")
            filtered_df = filtered_df.dropna(subset=["Month_dt"]).sort_values("Month_dt")
        except Exception as e:
            st.error(f"Error parsing 'Period_str' column: {e}")
            st.stop()

        # --- Choose dynamic group column: if NOP is filtered, group by Regional; else by NOP ---
        if filters["NOP"] != "All":
            group_col = "Regional"
        elif filters["Regional"] != "All":
            group_col = "NOP"
        else:
            group_col = "NOP"  # default

        # --- Plot KPI Trend ---
        fig = px.line(
            filtered_df,
            x="Month",
            y="Final KPI",
            color=group_col,
            markers=True,
            title="Trend KPI SONL1",
            text="Final KPI"  # Add the text label at each data point
        )

        fig.update_layout(
            yaxis_range=[70, 100],
            xaxis_title="Month",
            yaxis_title="Final KPI",
            hovermode="closest",
            title={
                "text": f"Availability Chart<br><sup>Last updated: {last_updated}</sup>",
                "x": 0.5,
                "xanchor": "center"
            }
        )

        # Show data labels on hover
        fig.update_traces(textposition="bottom center", texttemplate="%{text:.2f}")  # Adjust text position and format

        # Display the chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"**Last updated:** {last_updated}")

# --- Main Content: Monthly Availability ---
elif st.session_state.page == "📅 Monthly Availability":
    st.title("📅 Monthly Availability")

    tab1, tab2, tab3 = st.tabs(["📍 Regional", "🏢 NOP", "📡 Site"])

    with tab1:
        st.header("Monthly Availability per Regional")
        area_list = ["All"] + sorted(regional_data['area'].dropna().unique())
        regional_filtered = regional_data.copy()

        col1, col2 = st.columns(2)
        with col1:
            selected_area = st.selectbox("Select Area", options=area_list, key="reg_area")
        if selected_area != "All":
            regional_filtered = regional_filtered[regional_filtered["area"] == selected_area]

        regional_list = ["All"] + sorted(regional_filtered['regional'].dropna().unique())
        with col2:
            selected_regional = st.selectbox("Select Regional", options=regional_list, key="reg_regional")

        filters = {"area": selected_area, "regional": selected_regional}
        plot_line_chart(regional_data, "regional", filters, "Regional Availability", y_range=[95, 100])

    with tab2:
        st.header("Monthly Availability per NOP")
        area_list = ["All"] + sorted(nop_data['area'].dropna().unique())
        nop_filtered = nop_data.copy()

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_area = st.selectbox("Select Area", options=area_list, key="nop_area")
        if selected_area != "All":
            nop_filtered = nop_filtered[nop_filtered["area"] == selected_area]

        regional_list = ["All"] + sorted(nop_filtered['regional'].dropna().unique())
        with col2:
            selected_regional = st.selectbox("Select Regional", options=regional_list, key="nop_regional")
        if selected_regional != "All":
            nop_filtered = nop_filtered[nop_filtered["regional"] == selected_regional]

        networksite_list = ["All"] + sorted(nop_filtered['networksite'].dropna().unique())
        with col3:
            selected_networksite = st.selectbox("Select Network Site", options=networksite_list, key="nop_networksite")

        filters = {
            "area": selected_area,
            "regional": selected_regional,
            "networksite": selected_networksite
        }
        plot_line_chart(nop_data, "networksite", filters, "NOP Availability", y_range=[90, 100])

    with tab3:
        st.header("Monthly Availability per Site")
        area_list = ["All"] + sorted(site_data['area'].dropna().unique())
        site_filtered = site_data.copy()

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            selected_area = st.selectbox("Select Area", options=area_list, key="site_area")
        if selected_area != "All":
            site_filtered = site_filtered[site_filtered["area"] == selected_area]

        regional_list = ["All"] + sorted(site_filtered['regional'].dropna().unique())
        with col2:
            selected_regional = st.selectbox("Select Regional", options=regional_list, key="site_regional")
        if selected_regional != "All":
            site_filtered = site_filtered[site_filtered["regional"] == selected_regional]

        networksite_list = ["All"] + sorted(site_filtered['networksite'].dropna().unique())
        with col3:
            selected_networksite = st.selectbox("Select Network Site", options=networksite_list, key="site_networksite")
        if selected_networksite != "All":
            site_filtered = site_filtered[site_filtered["networksite"] == selected_networksite]

        with col5:
            site_id_search = st.text_input("Search Site ID", value="")
        if site_id_search:
            site_filtered = site_filtered[site_filtered["site_id"].astype(str).str.contains(site_id_search.strip(), case=False)]

        siteid_list = ["All"] + sorted(site_filtered['site_id'].dropna().unique())
        if 'site_id' not in st.session_state or st.session_state.site_id not in siteid_list:
            st.session_state.site_id = random.choice(siteid_list[1:]) if len(siteid_list) > 1 else "All"

        with col4:
            selected_siteid = st.selectbox("Select Site ID", options=siteid_list, key="site_id", index=siteid_list.index(st.session_state.site_id))

        filters = {
            "area": selected_area,
            "regional": selected_regional,
            "networksite": selected_networksite,
            "site_id": selected_siteid
        }
        plot_line_chart(site_data, "site_id", filters, "Site Availability", y_range=[0, 105])

