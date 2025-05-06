import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import random

# Set Streamlit page config
st.set_page_config(page_title="ENOM Availability Dashboard", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    def clean_month(df):
        df['Month'] = df['Month'].astype(str).str.strip().str[:3].str.title()
        return df

    regional = pd.read_csv("C:/Ariya Data/python/enomdashboard/data/availability_regional.csv")
    nop = pd.read_csv("C:/Ariya Data/python/enomdashboard/data/availability_nop.csv")
    site = pd.read_csv("C:/Ariya Data/python/enomdashboard/data/availability_site.csv")

    return clean_month(regional), clean_month(nop), clean_month(site)

regional_data, nop_data, site_data = load_data()

# --- Plotting Function ---
def plot_line_chart(df, group_col, filters, base_title, y_range):
    filtered = df.copy()

    # Apply filters
    for col, val in filters.items():
        if val != "All":
            filtered = filtered[filtered[col] == val]

    st.write(f"Number of rows after filtering: {len(filtered)}")
    if filtered.empty:
        st.warning(f"No valid data available after filtering for {base_title}.")
        return

    # Convert 'Availability (Ave)' to numeric and drop rows with missing values in 'Month' or 'Availability (Ave)'
    filtered["Availability (Ave)"] = pd.to_numeric(filtered["Availability (Ave)"], errors='coerce')
    filtered.dropna(subset=["Availability (Ave)", "Month"], inplace=True)

    # Group and aggregate data (calculate the average availability per group and month)
    grouped = filtered.groupby(["Month", group_col], as_index=False)["Availability (Ave)"].mean()

    if grouped.empty:
        st.warning(f"No valid data available after aggregation for {base_title}.")
        return

    # Ensure all month values are in the correct format (e.g., 'Jan', 'Feb', etc.)
    grouped['Month'] = grouped['Month'].str.strip().str[:3].str.title()

    # Filter out invalid months that may have been improperly formatted
    valid_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    grouped = grouped[grouped['Month'].isin(valid_months)]

    # Convert months to datetime for proper sorting and formatting
    try:
        grouped['Month'] = pd.to_datetime(grouped['Month'] + '-2025', format='%b-%Y')
    except Exception as e:
        st.error(f"Error converting months: {e}")
        return

    grouped.sort_values(by=['Month', group_col], inplace=True)

    # Format the 'Availability (Ave)' values to two decimals for the data labels
    grouped['Availability (Ave)'] = grouped['Availability (Ave)'].astype(float).round(2)

    # --- Build dynamic title ---
    filter_text = ", ".join([f"{k.title()}: {v}" for k, v in filters.items() if v != "All"])
    dynamic_title = f"{base_title}" + (f" ({filter_text})" if filter_text else "")

    # Plot the line chart with data labels
    fig = px.line(
        grouped,
        x="Month",
        y="Availability (Ave)",
        color=group_col,
        markers=True,
        title=dynamic_title,
        text=grouped["Availability (Ave)"].astype(str)  # ensure text is string
    )

    # Update layout and axes
    fig.update_layout(
        yaxis=dict(range=y_range, title="Availability (%)"),
        xaxis=dict(
            title="Month",
            tickformat="%b %Y",
            tickvals=grouped['Month'].dt.to_pydatetime()
        ),
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_traces(textposition="bottom center", showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

# --- Dashboard Title ---
st.title("📈 Monthly Availability")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📍 Regional", "🏢 NOP", "📡 Site"])

# --- Regional Tab ---
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

# --- NOP Tab ---
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

# --- Site Tab ---
with tab3:
    st.header("Monthly Availability per Site")

    area_list = ["All"] + sorted(site_data['area'].dropna().unique())
    site_filtered = site_data.copy()

    # Define columns for filter row
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

    # --- Text filter for site_id ---
    with col5:
        site_id_search = st.text_input("Search Site ID", value="")

    if site_id_search:
        site_filtered = site_filtered[site_filtered["site_id"].astype(str).str.contains(site_id_search.strip(), case=False)]

    siteid_list = ["All"] + sorted(site_filtered['site_id'].dropna().unique())

    # Reset session state if invalid
    if 'site_id' not in st.session_state or st.session_state.site_id not in siteid_list:
        if len(siteid_list) > 1:
            st.session_state.site_id = random.choice(siteid_list[1:])
        else:
            st.session_state.site_id = "All"

    with col4:
        selected_siteid = st.selectbox("Select Site ID", options=siteid_list, key="site_id", index=siteid_list.index(st.session_state.site_id))

    # Apply filters
    filters = {
        "area": selected_area,
        "regional": selected_regional,
        "networksite": selected_networksite,
        "site_id": selected_siteid
    }

    plot_line_chart(site_data, "site_id", filters, "Site Availability", y_range=[0, 105])