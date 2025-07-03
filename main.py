import streamlit as st
from sidebar import navigation

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="Dashboard ENOM 2.0", layout="wide")

def main():
    st.title("Dashboard ENOM 2.0")

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
    elif selected_page == "Daily":
        from my_pages import daily_availability
        daily_availability.app()
    elif selected_page == "Worst Site":
        from my_pages import worst_site
        worst_site.app()

if __name__ == "__main__":
    main()
