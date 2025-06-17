import streamlit as st
from sidebar import navigation

def main():
    st.set_page_config(page_title="Dashboard ENOM 2.0", layout="wide")
    st.title("📊 Dashboard ENOM 2.0")

    selected_page = navigation()

    if selected_page == "KPI":
        from my_pages import kpi_dashboard
        kpi_dashboard.app()
    elif selected_page == "Ticketing":
        from my_pages import ticketing_dashboard
        ticketing_dashboard.app()
    elif selected_page == "Availability":
        from my_pages import availability_dashboard
        availability_dashboard.app()

if __name__ == "__main__":
    main()
