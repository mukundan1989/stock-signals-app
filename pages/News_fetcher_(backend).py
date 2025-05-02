import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime
import shutil

# Configuration
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Replace with your key
API_HOST = "seeking-alpha.p.rapidapi.com"
PERPLEXITY_HOST = "perplexity2.p.rapidapi.com"
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

def fetch_articles(symbol, since_timestamp, until_timestamp):
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
                    # Add article URL to the item data
                    item['url'] = f"https://seekingalpha.com/article/{item['id']}"
                    all_news_data.append(item)

            page += 1
            time.sleep(1)

        except Exception as e:
            st.session_state["process_status"].append(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

def fetch_content(url):
    conn = http.client.HTTPSConnection(PERPLEXITY_HOST)
    payload = json.dumps({
        "content": f"What is the content of this news article? URL: {url}"
    })
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': PERPLEXITY_HOST,
        'Content-Type': "application/json"
    }

    try:
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        return data
    except Exception as e:
        st.session_state["process_status"].append(f"Error fetching content for URL {url}: {e}")
        return None

def clear_temp_storage():
    try:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        return True
    except Exception as e:
        st.error(f"Error clearing temp storage: {e}")
        return False

# Streamlit UI
st.title("Seeking Alpha News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and extract content via Perplexity")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "RapidAPI Key",
    value=st.session_state["api_key"],
    type="password",
    help="Enter your RapidAPI key for both Seeking Alpha and Perplexity APIs"
)

# Date input
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

status_placeholder = st.empty()

# Processing buttons
proc_col, util_col = st.columns([3, 1])

with proc_col:
    if st.button("Start Full Processing"):
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            
            # 1. Fetch Articles
            with open(SYMBOL_FILE, "r") as f:
                symbols = [line.strip() for line in f.readlines()]
            
            status_placeholder.write("🚀 Starting article fetching process...")
            
            for symbol in symbols:
                status_placeholder.write(f"⏳ Fetching articles for: {symbol}")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)
                
                if articles:
                    file_name = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_news_data.csv")
                    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['ID', 'URL', 'Publish Date', 'Title', 'Author ID', 
                                    'Comment Count', 'Primary Tickers', 'Secondary Tickers']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in articles:
                            writer.writerow({
                                'ID': item['id'],
                                'URL': item['url'],
                                'Publish Date': item['attributes']['publishOn'],
                                'Title': item['attributes']['title'],
                                'Author ID': item['relationships']['author']['data']['id'],
                                'Comment Count': item['attributes']['commentCount'],
                                'Primary Tickers': ', '.join([t['type'] for t in item['relationships']['primaryTickers']['data']]),
                                'Secondary Tickers': ', '.join([t['type'] for t in item['relationships']['secondaryTickers']['data']])
                            })
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Articles Found": len(articles)
                    })
                    st.session_state["process_status"].append(f"✅ Saved {len(articles)} articles for {symbol}")
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Articles Found": 0
                    })
                    st.session_state["process_status"].append(f"❌ No articles found for {symbol}")
            
            status_placeholder.write("✔️ Article fetching complete! Starting content extraction...")
            
            # 2. Fetch Content via Perplexity
            csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
            for csv_file in csv_files:
                symbol = csv_file.replace("_news_data.csv", "")
                status_placeholder.write(f"⏳ Extracting content for: {symbol}")
                df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
                
                if 'Content' not in df.columns:
                    df['Content'] = None
                
                for index, row in df.iterrows():
                    if pd.isna(row['Content']):
                        content = fetch_content(row['URL'])
                        df.at[index, 'Content'] = content if content else "Content unavailable"
                        time.sleep(1.5)  # Respect rate limits
                
                df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
                st.session_state["process_status"].append(f"✔️ Content extracted for {symbol}")
            
            status_placeholder.write("🎉 All operations completed successfully!")
            st.balloons()
            st.rerun()

with util_col:
    if st.button("Clear Temporary Storage"):
        if clear_temp_storage():
            st.success("Temporary files and status cleared!")
            st.balloons()
            st.rerun()

# Display status
if st.session_state["status_table"]:
    st.write("### Status Table")
    st.table(pd.DataFrame(st.session_state["status_table"]))

if st.session_state["process_status"]:
    st.write("### Process Log")
    for status in st.session_state["process_status"]:
        st.write(status)

# Download Section
if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### Download Processed Files")
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
