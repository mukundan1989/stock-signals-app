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
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"  # Replace with your key
SA_API_HOST = "seeking-alpha.p.rapidapi.com"
PPLX_API_HOST = "perplexity2.p.rapidapi.com"
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
    """Original working URL fetcher from your old script"""
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(SA_API_HOST)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': SA_API_HOST
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
                    # Add URL to each article
                    item['url'] = f"https://seekingalpha.com/article/{item['id']}"
                    all_news_data.append(item)

            page += 1
            time.sleep(1)  # Respect rate limits

        except Exception as e:
            st.session_state["process_status"].append(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

def fetch_content_with_perplexity(url):
    """New content fetcher using Perplexity API"""
    try:
        conn = http.client.HTTPSConnection(PPLX_API_HOST)
        payload = json.dumps({
            "content": f"Extract the complete text content from this news article URL: {url}"
        })
        headers = {
            'x-rapidapi-key': st.session_state["api_key"],
            'x-rapidapi-host': PPLX_API_HOST,
            'Content-Type': "application/json"
        }
        
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        
        if res.status != 200:
            st.session_state["process_status"].append(f"Perplexity API Error: HTTP {res.status}")
            return None
            
        return res.read().decode('utf-8')
        
    except Exception as e:
        st.session_state["process_status"].append(f"Perplexity content fetch failed: {e}")
        return None

def clean_content(text):
    """Basic content cleaner"""
    if not text or pd.isna(text):
        return None
    try:
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove excessive whitespace
        clean_text = ' '.join(clean_text.split())
        return clean_text.strip()
    except Exception as e:
        st.session_state["process_status"].append(f"Content cleaning error: {e}")
        return None

# Streamlit UI (same as before with minor updates)
st.title("Seeking Alpha News Fetcher with Perplexity")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "RapidAPI Key",
    value=st.session_state["api_key"],
    type="password",
    help="Same key will be used for both Seeking Alpha and Perplexity APIs"
)

# Date inputs (same as before)
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp()

# Processing function with clear stages
def run_processing():
    st.session_state["status_table"] = []
    st.session_state["process_status"] = []
    
    # Stage 1: Fetch article URLs (original working code)
    with open(SYMBOL_FILE, "r") as f:
        symbols = [line.strip() for line in f.readlines()]
    
    for symbol in symbols:
        st.session_state["process_status"].append(f"🔍 Fetching articles for {symbol}")
        articles = fetch_articles(symbol, since_timestamp, until_timestamp)
        
        if articles:
            # Save with URL included
            df = pd.DataFrame([{
                'ID': a['id'],
                'URL': a['url'],
                'Publish_Date': a['attributes']['publishOn'],
                'Title': a['attributes']['title'],
                'Author_ID': a['relationships']['author']['data']['id'],
                'Comment_Count': a['attributes']['commentCount'],
                'Primary_Tickers': ', '.join([t['type'] for t in a['relationships']['primaryTickers']['data']]),
                'Secondary_Tickers': ', '.join([t['type'] for t in a['relationships']['secondaryTickers']['data']])
            } for a in articles])
            
            df.to_csv(os.path.join(OUTPUT_DIR, f"{symbol}_news.csv"), index=False)
            st.session_state["status_table"].append({
                "Symbol": symbol,
                "Articles": len(articles),
                "Status": "URLs Fetched"
            })
            st.session_state["process_status"].append(f"✅ Saved {len(articles)} URLs for {symbol}")
        else:
            st.session_state["status_table"].append({
                "Symbol": symbol,
                "Articles": 0,
                "Status": "Failed"
            })
    
    # Stage 2: Fetch content with Perplexity
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news.csv")]
    for csv_file in csv_files:
        symbol = csv_file.replace("_news.csv", "")
        st.session_state["process_status"].append(f"📥 Fetching content for {symbol}")
        
        df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
        if 'Content' not in df.columns:
            df['Content'] = None
        
        for idx, row in df.iterrows():
            if pd.isna(row['Content']):
                content = fetch_content_with_perplexity(row['URL'])
                df.at[idx, 'Content'] = clean_content(content) if content else None
                time.sleep(1.5)  # Perplexity rate limit
        
        df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
        st.session_state["process_status"].append(f"✅ Content updated for {symbol}")
    
    st.session_state["process_status"].append("🎉 All processing complete!")
    st.balloons()

# UI Controls
if st.button("Start Processing"):
    run_processing()
    st.rerun()

if st.button("Clear Data"):
    clear_temp_storage()
    st.rerun()

# Status displays (same as before)
if st.session_state["status_table"]:
    st.write("## Processing Summary")
    st.table(pd.DataFrame(st.session_state["status_table"]))

if st.session_state["process_status"]:
    st.write("## Detailed Log")
    st.text_area("", "\n".join(st.session_state["process_status"]), height=300)

# File downloads (same as before)
