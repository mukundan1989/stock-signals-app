import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
from datetime import datetime
from glob import glob

# [Previous code remains the same until the convert_json_to_csv function]

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
            csv_file_path = os.path.join(CSV_OUTPUT_DIR, csv_file_name)

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
                    "search_keyword": json_file.replace(".json", "").replace("_", " ")  # Add keyword source
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
                company_files = glob(os.path.join(CSV_OUTPUT_DIR, f"{company.replace(' ', '_')}*.csv"))
                combined_df = pd.DataFrame()
                
                for file in company_files:
                    df = pd.read_csv(file)
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
                
                if not combined_df.empty:
                    # Save combined CSV
                    combined_file = os.path.join(CSV_OUTPUT_DIR, f"{company.replace(' ', '_')}_COMBINED.csv")
                    combined_df.to_csv(combined_file, index=False)
                    
                    # Update status table
                    for entry in st.session_state["status_table"]:
                        if entry["Keyword"] == company:
                            entry["Combined CSV"] = "✅"
                            break
                    
            except Exception as e:
                st.error(f"Error combining files for {company}: {e}")
    
    status_placeholder.empty()

# [Rest of the code remains the same, but update the status_table dictionary to include "Combined CSV" column]

# In the UI section where you initialize status_table, add the new column:
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []

# [Rest of the code remains the same]

# Update the download section to show both individual and combined files:
if os.path.exists(CSV_OUTPUT_DIR):
    # Get all CSV files and separate combined files
    all_csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    combined_files = [f for f in all_csv_files if "_COMBINED" in f]
    individual_files = [f for f in all_csv_files if "_COMBINED" not in f]
    
    if all_csv_files:
        with st.expander("Download CSV Files"):
            st.subheader("Combined Company Files")
            for csv_file in combined_files:
                with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                    st.download_button(
                        label=f"Download {csv_file.replace('_COMBINED', '').replace('_', ' ').replace('.csv', '')} (Combined)",
                        data=f.read(),
                        file_name=csv_file,
                        mime="text/csv"
                    )
            
            st.subheader("Individual Keyword Files")
            cols = st.columns(3)
            for i, csv_file in enumerate(individual_files):
                with cols[i % 3]:
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {csv_file.replace('_', ' ').replace('.csv', '')}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found")
else:
    st.warning("CSV output directory does not exist")
