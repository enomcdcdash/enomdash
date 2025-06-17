import streamlit as st

def navigation():
    with st.sidebar:
        # Sidebar header
        st.markdown("""
            <div style='text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 10px;'>
                📊 Dashboard ENOM 2.0
            </div>
        """, unsafe_allow_html=True)

        # Logo
        st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="https://portal.telkominfra.com/resources/img/telkominfra-logo-2.png" width="200">
            </div>
        """, unsafe_allow_html=True)

        # Divider
        st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)

        # Persistent page selection
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = "KPI"

        # Navigation buttons
        if st.button("📈 KPI", use_container_width=True):
            st.session_state.selected_page = "KPI"

        if st.button("🎟️ Ticketing", use_container_width=True):
            st.session_state.selected_page = "Ticketing"

        if st.button("📡 Availability", use_container_width=True):
            st.session_state.selected_page = "Availability"

    return st.session_state.selected_page
