import streamlit as st

from neo_api import observe


def detail_page():
    st.set_page_config(page_title="Neo: Near Earth Observation", layout="wide")

    # 1. Initialize session state first
    if "observation_df" not in st.session_state:
        st.session_state.observation_df = None
        st.session_state.observation_csv = None
        st.session_state.api_limit = None
        st.session_state.last_query_id = None

    st.write("# ☄️ Neo: Near Earth Observation")
    st.write(
        "Fetch and analyze Near Earth Objects from NASA's database (Up to 31 days)."
    )
    st.divider()

    col1, col2, col3 = st.columns([2, 1, 1])
    api_key = col1.text_input("Nasa API Key", type="password")
    start_date = col2.date_input("Start Date")
    end_date = col3.date_input("End Date")

    # 2. Query ID check for auto-reset
    current_query_id = f"{api_key}-{start_date}-{end_date}"
    if st.session_state.last_query_id is not None:
        if st.session_state.last_query_id != current_query_id:
            st.session_state.observation_df = None
            st.session_state.observation_csv = None

    if start_date and end_date:
        day_diff = (end_date - start_date).days

        if start_date > end_date:
            st.error("🚨 Start date must be before end date.")
        elif day_diff > 30:
            st.error(f"🚨 Range is {day_diff + 1} days. Max is 31.")
        elif api_key and len(api_key) == 40:
            if st.button("Fetch Asteroid Data"):
                with st.spinner("Accessing NASA deep space database..."):
                    result = observe(api_key, start_date, end_date)

                    if result and result[0] is not None:
                        st.session_state.observation_df = result[0]
                        st.session_state.observation_csv = result[1]
                        st.session_state.api_limit = result[2]
                        st.session_state.last_query_id = current_query_id
                    else:
                        st.error("API Error. Check your key.")

    # 3. Persistent Display
    if st.session_state.observation_df is not None:
        m1, m2 = st.columns([1, 1])
        m1.metric("API Requests Remaining", st.session_state.api_limit)
        m2.download_button(
            "📥 Download Data as CSV",
            st.session_state.observation_csv,
            file_name=f"asteroid_data_{start_date}_to_{end_date}.csv",
            mime="text/csv",
        )

        def highlight_hazardous(row):
            # If Hazardous is True, make the background red, otherwise no style
            return [
                "background-color: #dc381f; color: white" if row.Hazardous else ""
                for _ in row
            ]

        # Apply the style to the dataframe
        styled_df = st.session_state.observation_df.style.apply(
            highlight_hazardous, axis=1
        )

        # Displaying with high-visibility formatting
        st.dataframe(
            styled_df,
            width="stretch",
            column_config={
                "Hazardous": st.column_config.TextColumn("Hazardous"),
                "Relative Velocity": st.column_config.NumberColumn(format="%.2f km/s"),
            },
        )
