import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime
import shutil
import re

# Configuration
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Default placeholder
API_HOST = "seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdire"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "process_status" not in st.session_state:
    st.session_state["process_status"] = []
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY

# Streamlit UI
st.title("Seeking Alpha News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and process them.")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "Seeking Alpha API Key",
    value=st.session_state["api_key"],
    type="password",
    help="Default key is rate-limited. Replace with your own RapidAPI key."
)

# Fetch articles function
def fetch_articles(symbol, since_timestamp, until_timestamp):
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': API_HOST
    }
    size = 20
    page = 1
    all_news_data = []
    seen_ids = set()

    while True:
        try:
            conn.request(
                "GET",
                f"/news/v2/list-by-symbol?size={size}&number={page}&id={symbol}&since={since_timestamp}&until={until_timestamp}",
                headers=headers
            )
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

            if not data['data']:
                break

            for item in data['data']:
                if item['id'] not in seen_ids:
                    seen_ids.add(item['id'])
                    all_news_data.append(item)

            page += 1
            time.sleep(1)

        except Exception as e:
            st.session_state["process_status"].append(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Fetch Articles"):
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            with open(SYMBOL_FILE, "r") as f:
                symbols = [line.strip() for line in f.readlines()]

            for symbol in symbols:
                st.session_state["process_status"].append(f"Fetching articles for: {symbol}")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)
                if articles:
                    file_name = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_news_data.csv")
                    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['ID', 'Publish Date', 'Title', 'Author ID', 'Comment Count', 'Primary Tickers', 'Secondary Tickers', 'Image URL']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in articles:
                            writer.writerow({
                                'ID': item['id'],
                                'Publish Date': item['attributes']['publishOn'],
                                'Title': item['attributes']['title'],
                                'Author ID': item['relationships']['author']['data']['id'],
                                'Comment Count': item['attributes']['commentCount'],
                                'Primary Tickers': ', '.join([t['type'] for t in item['relationships']['primaryTickers']['data']]),
                                'Secondary Tickers': ', '.join([t['type'] for t in item['relationships']['secondaryTickers']['data']]),
                                'Image URL': item['attributes'].get('gettyImageUrl', 'N/A')
                            })
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": len(articles)
                    })
                    st.session_state["process_status"].append(f"Saved {len(articles)} articles for {symbol}")
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": "API Error"
                    })
                    st.session_state["process_status"].append(f"Failed to fetch articles for {symbol}")

with col2:
    if st.button("Clean Up"):
        st.session_state["process_status"] = []
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            st.session_state["process_status"].append(f"Cleaning content for {symbol}")
            df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
            # No 'Content' column to clean now — placeholder logic removed
            st.session_state["process_status"].append(f"Cleanup skipped: no content to clean for {symbol}")

# Display status table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.table(status_df)

# Display process status
if st.session_state["process_status"]:
    st.write("### Process Status")
    for status in st.session_state["process_status"]:
        st.write(status)

# Download Section
if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### Download Extracted Files")
        cols = st.columns(3)
        for i, csv_file in enumerate(csv_files):
            with cols[i % 3]:
                with open(os.path.join(OUTPUT_DIR, csv_file), "r") as f:
                    st.download_button(
                        label=f"Download {csv_file}",
                        data=f.read(),
                        file_name=csv_file,
                        mime="text/csv"
                    )
    else:
        st.warning("No CSV files found in the output directory.")
else:
    st.warning("Output directory does not exist.")
