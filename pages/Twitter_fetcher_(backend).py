import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
from datetime import datetime
from glob import glob

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
CSV_OUTPUT_DIR = "/tmp/data/csv_output"  # Corrected variable name

# Ensure output directories exist
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)  # Using correct variable name

# [Rest of your functions remain the same...]

def convert_json_to_csv():
    """Convert all JSON files to CSV and combine by company"""
    if not os.path.exists(JSON_OUTPUT_DIR):
        st.warning("No JSON files found. Please fetch tweets first.")
        return

    json_files = [f for f in os.listdir(JSON_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No JSON files found in the output directory.")
        return

    status_placeholder = st.empty()
    
    # First convert all JSON to individual CSV files
    for json_file in json_files:
        try:
            status_placeholder.write(f"Converting {json_file} to CSV...")
            json_file_path = os.path.join(JSON_OUTPUT_DIR, json_file)
            csv_file_name = f"{os.path.splitext(json_file)[0]}.csv"
            csv_file_path = os.path.join(CSV_OUTPUT_DIR, csv_file_name)  # Using correct variable name

            with open(json_file_path, "r") as file:
                data = json.load(file)

            records = []
            for item in data.get("results", []):
                flat_item = {
                    "tweet_id": item.get("tweet_id"),
                    "creation_date": item.get("creation_date"),
                    "text": item.get("text"),
                    "language": item.get("language"),
                    "favorite_count": item.get("favorite_count"),
                    "retweet_count": item.get("retweet_count"),
                    "reply_count": item.get("reply_count"),
                    "views": item.get("views"),
                    "search_keyword": json_file.replace(".json", "").replace("_", " ")
                }
                user_info = item.get("user", {})
                for key, value in user_info.items():
                    flat_item[f"user_{key}"] = value
                records.append(flat_item)

            df = pd.DataFrame(records)
            df.to_csv(csv_file_path, index=False)

            keyword = json_file.replace(".json", "").replace("_", " ")
            for entry in st.session_state["status_table"]:
                if entry["Keyword"] == keyword:
                    entry["CSV Output"] = "✅"
                    break

        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")
    
    # Now combine CSVs by company
    if base_keywords:
        status_placeholder.write("Combining CSV files by company...")
        for company in base_keywords:
            try:
                # Get all CSVs for this company (main + combinations)
                company_pattern = os.path.join(CSV_OUTPUT_DIR, f"{company.replace(' ', '_')}*.csv")  # Using correct variable name
                company_files = glob(company_pattern)
                combined_df = pd.DataFrame()
                
                for file in company_files:
                    df = pd.read_csv(file)
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
                
                if not combined_df.empty:
                    # Save combined CSV
                    combined_file = os.path.join(CSV_OUTPUT_DIR, f"{company.replace(' ', '_')}_COMBINED.csv")  # Using correct variable name
                    combined_df.to_csv(combined_file, index=False)
                    
                    # Update status table
                    for entry in st.session_state["status_table"]:
                        if entry["Keyword"] == company:
                            entry["Combined CSV"] = "✅"
                            break
                    
            except Exception as e:
                st.error(f"Error combining files for {company}: {e}")
    
    status_placeholder.empty()

# [Rest of your code remains the same, ensuring CSV_OUTPUT_DIR is used consistently]
