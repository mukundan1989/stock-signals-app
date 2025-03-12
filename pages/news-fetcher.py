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
API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"  # Your RapidAPI key
API_HOST = "seeking-alpha.p.rapidapi.com"  # API host
SYMBOL_FILE = "twitterdir/symbollist.txt"  # Path to the symbols file (from GitHub repo)
OUTPUT_DIR = "/tmp/twitterdir"  # Directory to save CSV files
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure the output directory exists

# Initialize session state for status table
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []

# Function to fetch article metadata
def fetch_articles(symbol, since_timestamp, until_timestamp):
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    size = 20  # Number of articles per request
    all_news_data = []
    current_until_timestamp = until_timestamp

    while True:
        try:
            conn.request("GET", f"/news/v2/list-by-symbol?until={current_until_timestamp}&since={since_timestamp}&size={size}&id={symbol}", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

            if not data['data']:
                break  # No more articles

            all_news_data.extend(data['data'])
            current_until_timestamp -= 86400  # Move one day back
            time.sleep(2)  # Avoid rate limits

        except Exception as e:
            st.error(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

# Function to fetch article content
def fetch_content(news_id):
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    try:
        conn.request("GET", f"/news/get-details?id={news_id}", headers=headers)
        res = conn.getresponse()
        return res.read().decode('utf-8')
    except Exception as e:
        st.error(f"Error fetching content for ID {news_id}: {e}")
        return None

# Function to clean HTML content
def clean_html(raw_html):
    clean_regex = re.compile('<.*?>')
    return re.sub(clean_regex, '', raw_html)

def extract_content(full_data):
    try:
        data = json.loads(full_data)
        content = data.get("data", {}).get("attributes", {}).get("content", "")
        cleaned_content = clean_html(content)
        ending_markers = ["More on", "Read more", "See also", "Learn more", "Related articles"]
        for marker in ending_markers:
            if marker in cleaned_content:
                cleaned_content = cleaned_content.split(marker)[0]
                break
        return cleaned_content.strip()
    except (json.JSONDecodeError, TypeError):
        return None

# Streamlit UI
st.title("Seeking Alpha News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and process them.")

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
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        st.session_state["status_table"] = []  # Reset status table
        with open(SYMBOL_FILE, "r") as f:
            symbols = [line.strip() for line in f.readlines()]

        for symbol in symbols:
            st.write(f"Fetching articles for: {symbol}")
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
            else:
                st.session_state["status_table"].append({
                    "Symbol": symbol,
                    "Number of Articles Extracted": "API Error"
                })

with col2:
    if st.button("Get Content"):
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
            if 'Content' not in df.columns:
                df['Content'] = None

            for index, row in df.iterrows():
                if pd.isna(row['Content']):
                    content = fetch_content(row['ID'])
                    df.at[index, 'Content'] = content
                    time.sleep(1)  # Avoid rate limits

            df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
            st.write(f"Updated content for {symbol}")

with col3:
    if st.button("Clean Up"):
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
            if 'Content' in df.columns:
                df['Extracted'] = df['Content'].apply(extract_content)
                df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
                st.write(f"Cleaned content for {symbol}")

# Display status table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.table(status_df)
else:
    st.write("No actions performed yet. Fetch articles to see the status.")
