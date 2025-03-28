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
    </style>
    """,
    unsafe_allow_html=True
)

# Configuration
API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
API_HOST = "twitter154.p.rapidapi.com"
KEYWORDS_FILE = "data/keywords.txt"
JSON_OUTPUT_DIR = "/tmp/data/output"
CSV_OUTPUT_DIR = "/tmp/data/csv_output"

# Ensure output directories exist
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "combined_keywords" not in st.session_state:
    st.session_state["combined_keywords"] = {}

def generate_combined_keywords(base_keywords):
    """Generate default combined keywords for each base keyword"""
    combined = {}
    for keyword in base_keywords:
        combined[keyword] = [
            f"{keyword} Portfolio",
            f"{keyword} Stock",
            f"{keyword} Earnings",
            f"{keyword} Analysis"
        ]
    return combined

def fetch_tweets_for_keyword(keyword, start_date, end_date):
    """Fetch tweets for a specific keyword from the API"""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    endpoint = f"/search/search?query={keyword}&section=latest&min_retweets=1&min_likes=1&limit=50&start_date={start_date_str}&language=en&end_date={end_date_str}"
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return data.decode("utf-8")

def fetch_tweets(start_date, end_date, use_combined=False):
    """Fetch tweets for keywords with optional combined keywords"""
    if not os.path.exists(KEYWORDS_FILE):
        st.error(f"Keywords file '{KEYWORDS_FILE}' does not exist.")
        return

    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]

    if not base_keywords:
        st.warning("No keywords found in the file.")
        return

    if use_combined:
        keywords = []
        for base_keyword, combos in st.session_state["combined_keywords"].items():
            if base_keyword in base_keywords:  # Only include if base keyword exists
                keywords.extend(combos)
    else:
        keywords = base_keywords

    status_placeholder = st.empty()

    for keyword in keywords:
        try:
            status_placeholder.write(f"Fetching tweets for: {keyword}")
            result = fetch_tweets_for_keyword(keyword, start_date, end_date)

            sanitized_keyword = keyword.replace(" ", "_").replace("/", "_")
            output_file = os.path.join(JSON_OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)

            st.session_state["status_table"].append({
                "Keyword": keyword,
                "Type": "Combined" if use_combined else "Base",
                "Tweet Extract JSON": "✅",
                "CSV Output": "❌",
                "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            })

            status_placeholder.write(f"Saved tweets for: {keyword}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

    status_placeholder.empty()

# [Rest of your existing functions (convert_json_to_csv, clear_temp) remain the same...]

# Streamlit UI
st.title("Twitter Data Fetcher")

# Date input section
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=datetime(2025, 3, 10))

# Load and display base keywords
base_keywords = []
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]

# Generate or load combined keywords
if not st.session_state["combined_keywords"] and base_keywords:
    st.session_state["combined_keywords"] = generate_combined_keywords(base_keywords)

# Combination Keywords Section
st.subheader("Combination Keywords")
if base_keywords:
    for base_keyword in base_keywords:
        if base_keyword not in st.session_state["combined_keywords"]:
            st.session_state["combined_keywords"][base_keyword] = generate_combined_keywords([base_keyword])[base_keyword]
        
        with st.expander(f"Combinations for: {base_keyword}"):
            cols = st.columns(4)
            for i in range(4):
                with cols[i]:
                    new_value = st.text_input(
                        f"Combination {i+1}",
                        value=st.session_state["combined_keywords"][base_keyword][i],
                        key=f"combo_{base_keyword}_{i}"
                    )
                    st.session_state["combined_keywords"][base_keyword][i] = new_value
else:
    st.warning("No base keywords found to generate combinations")

# Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Fetch Base Keywords"):
        if start_date <= end_date:
            st.write("Fetching tweets for base keywords...")
            fetch_tweets(start_date, end_date, use_combined=False)
            st.write("Process completed!")
        else:
            st.warning("Please fix the date range")

with col2:
    if st.button("Fetch Combined Keywords"):
        if start_date <= end_date:
            st.write("Fetching tweets for combined keywords...")
            fetch_tweets(start_date, end_date, use_combined=True)
            st.write("Process completed!")
        else:
            st.warning("Please fix the date range")

with col3:
    if st.button("Convert JSON to CSV"):
        st.write("Converting JSON files to CSV...")
        convert_json_to_csv()
        st.write("Conversion completed!")

with col4:
    if st.button("Clear Temp"):
        st.write("Clearing temporary files...")
        clear_temp()
        st.write("Process completed!")

# Status Table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.dataframe(status_df, hide_index=True)
else:
    st.write("No actions performed yet. Fetch tweets to see the status.")

# Display CSV files
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download Converted CSV Files"):
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {csv_file}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found")
else:
    st.warning("CSV output directory does not exist")
