import streamlit as st

def navigation():
    with st.sidebar:
        # --- Inject custom button CSS style ---
        button_style = """
        <style>
        div.stButton > button {
            width: 100%;
            text-align: center;
            background-color: #2F5597;
            color: white;
            font-weight: 500;
            padding: 0.5em 1em;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)

        # --- Sidebar header ---
        st.markdown("""
            <div style='text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 10px;'>
                📊 Dashboard ENOM 2.0
            </div>
        """, unsafe_allow_html=True)

        # --- Logo ---
        st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="https://portal.telkominfra.com/resources/img/telkominfra-logo-2.png" width="200">
            </div>
        """, unsafe_allow_html=True)

        # --- Divider ---
        st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)

        # --- Persistent page selection ---
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = "KPI"

        # --- Navigation buttons ---
        if st.button("📈 KPI Tracking", use_container_width=True):
            st.session_state.selected_page = "KPI"
        if st.button("🎟️ Ticketing Performance", use_container_width=True):
            st.session_state.selected_page = "Ticketing"
        if st.button("📡 Monthly Availability", use_container_width=True):
            st.session_state.selected_page = "Availability"
        if st.button("📅 Daily Availability", use_container_width=True):
            st.session_state.selected_page = "Daily"
        if st.button("📉 Worst Site Dashboard", use_container_width=True):
            st.session_state.selected_page = "Worst Site"
        if st.button("👷 Resource Performance", use_container_width=True):
            st.session_state.selected_page = "Resource Productivity"

    return st.session_state.selected_page
