import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
from datetime import datetime

# Custom CSS
st.markdown(
    """
    <style>
    .stButton > button:hover {
        background-color: #000000;
        color: white;
    }
    .stButton > button {
        background-color: #282828;
        color: white;
    }
    .stButton > button:active {
        background-color: #282828;
        color: white;
    }
    /* Make the tabs more compact */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
    /* Compact text inputs */
    .stTextInput input {
        padding: 0.3rem 0.5rem !important;
        font-size: 0.9rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# [Previous configuration and function definitions remain the same until the UI section...]

# Streamlit UI
st.title("Twitter Data Fetcher")

# Date input section
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=datetime(2025, 3, 10))

# Load base keywords
base_keywords = []
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]

# Generate or load combined keywords
if not st.session_state["combined_keywords"] and base_keywords:
    st.session_state["combined_keywords"] = generate_combined_keywords(base_keywords)

# Compact Combination Keywords Section
st.subheader("Combination Keywords")

if base_keywords:
    # Add search functionality
    search_term = st.text_input("Search companies", placeholder="Type to filter companies...")
    
    # Filter companies based on search
    filtered_companies = [company for company in base_keywords 
                         if search_term.lower() in company.lower()] if search_term else base_keywords
    
    if not filtered_companies and search_term:
        st.warning("No companies match your search")
    else:
        # Use tabs for compact organization
        tabs = st.tabs([f" {i+1} " for i in range(0, len(filtered_companies), 10)])
        
        for i, tab in enumerate(tabs):
            start_idx = i * 10
            end_idx = min((i + 1) * 10, len(filtered_companies))
            current_companies = filtered_companies[start_idx:end_idx]
            
            with tab:
                for company in current_companies:
                    with st.expander(f"🔍 {company}", expanded=False):
                        cols = st.columns(4)
                        for j in range(4):
                            with cols[j]:
                                combo_key = f"combo_{company}_{j}"
                                new_value = st.text_input(
                                    f"Combination {j+1}",
                                    value=st.session_state["combined_keywords"][company][j],
                                    key=combo_key,
                                    label_visibility="collapsed",
                                    placeholder=f"{company} combo {j+1}"
                                )
                                st.session_state["combined_keywords"][company][j] = new_value
else:
    st.warning("No base keywords found to generate combinations")

# Action Buttons
st.subheader("Actions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Fetch Base Keywords"):
        if start_date <= end_date:
            with st.spinner("Fetching tweets for base keywords..."):
                fetch_tweets(start_date, end_date, use_combined=False)
            st.success("Base keywords fetch completed!")
        else:
            st.warning("Please fix the date range")

with col2:
    if st.button("Fetch Combined Keywords"):
        if start_date <= end_date:
            with st.spinner("Fetching tweets for combined keywords..."):
                fetch_tweets(start_date, end_date, use_combined=True)
            st.success("Combined keywords fetch completed!")
        else:
            st.warning("Please fix the date range")

with col3:
    if st.button("Convert to CSV"):
        with st.spinner("Converting JSON to CSV..."):
            convert_json_to_csv()
        st.success("Conversion completed!")

with col4:
    if st.button("Clear Temp"):
        with st.spinner("Clearing temporary files..."):
            clear_temp()
        st.success("Temporary files cleared!")

# Status Table
if st.session_state["status_table"]:
    st.subheader("Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.dataframe(status_df, hide_index=True, use_container_width=True)
else:
    st.info("No actions performed yet. Fetch tweets to see the status.")

# Download Section
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("📁 Download CSV Files", expanded=False):
            # Show in a compact grid
            cols = st.columns(4)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 4]:
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"⬇️ {csv_file[:20]}...",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv",
                            help=f"Download {csv_file}"
                        )
    else:
        st.warning("No CSV files found")
else:
    st.warning("CSV output directory does not exist")
