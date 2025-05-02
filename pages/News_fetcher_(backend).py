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
DEFAULT_API_KEY = "your-api-key-here"  # Replace with your actual key
API_HOST = "seeking-alpha.p.rapidapi.com"
PERPLEXITY_HOST = "perplexity2.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdire"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state.status_table = []
if "process_status" not in st.session_state:
    st.session_state.process_status = ["Application initialized"]
if "api_key" not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY
if "processing" not in st.session_state:
    st.session_state.processing = False

def log_status(message):
    st.session_state.process_status.append(message)
    st.rerun()

def fetch_articles(symbol, since_timestamp, until_timestamp):
    try:
        conn = http.client.HTTPSConnection(API_HOST)
        headers = {
            'x-rapidapi-key': st.session_state.api_key,
            'x-rapidapi-host': API_HOST
        }
        
        url = f"/news/v2/list-by-symbol?size=20&number=1&id={symbol}&since={since_timestamp}&until={until_timestamp}"
        conn.request("GET", url, headers=headers)
        
        res = conn.getresponse()
        if res.status != 200:
            log_status(f"❌ API Error for {symbol}: HTTP {res.status}")
            return None
            
        data = json.loads(res.read().decode("utf-8"))
        return [{
            'id': item['id'],
            'url': f"https://seekingalpha.com/article/{item['id']}",
            'publish_date': item['attributes']['publishOn'],
            'title': item['attributes']['title'],
            'author_id': item['relationships']['author']['data']['id'],
            'comment_count': item['attributes']['commentCount'],
            'primary_tickers': ', '.join([t['type'] for t in item['relationships']['primaryTickers']['data']]),
            'secondary_tickers': ', '.join([t['type'] for t in item['relationships']['secondaryTickers']['data']])
        } for item in data.get('data', [])]
        
    except Exception as e:
        log_status(f"❌ Failed to fetch articles for {symbol}: {str(e)}")
        return None

def fetch_content(url):
    try:
        conn = http.client.HTTPSConnection(PERPLEXITY_HOST)
        payload = json.dumps({"content": f"Extract the full text content from: {url}"})
        
        headers = {
            'x-rapidapi-key': st.session_state.api_key,
            'x-rapidapi-host': PERPLEXITY_HOST,
            'Content-Type': "application/json"
        }
        
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        
        if res.status != 200:
            log_status(f"⚠️ Perplexity API Error for {url}: HTTP {res.status}")
            return None
            
        return res.read().decode('utf-8')
        
    except Exception as e:
        log_status(f"⚠️ Failed to fetch content for {url}: {str(e)}")
        return None

def clear_temp_storage():
    try:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        st.session_state.status_table = []
        st.session_state.process_status = ["Reset complete"]
        return True
    except Exception as e:
        log_status(f"❌ Failed to clear storage: {str(e)}")
        return False

# Streamlit UI
st.title("📰 Seeking Alpha News Fetcher")
st.caption("Fetches articles and extracts content via Perplexity API")

# API Key Input
st.session_state.api_key = st.text_input(
    "RapidAPI Key",
    value=st.session_state.api_key,
    type="password",
    help="Enter your RapidAPI key for both APIs"
)

# Date range selector
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Processing controls
if st.button("Start Full Processing") and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.status_table = []
    st.session_state.process_status = ["Starting processing..."]
    
    try:
        # Check if symbol file exists
        if not os.path.exists(SYMBOL_FILE):
            log_status(f"❌ Error: Symbol file not found at {SYMBOL_FILE}")
            st.session_state.processing = False
            st.stop()
            
        # Read symbols
        with open(SYMBOL_FILE, "r") as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]
            
        if not symbols:
            log_status("❌ Error: No symbols found in the symbol file")
            st.session_state.processing = False
            st.stop()
            
        # Process each symbol
        for symbol in symbols:
            log_status(f"🔍 Processing symbol: {symbol}")
            
            articles = fetch_articles(symbol, since_timestamp, until_timestamp)
            if not articles:
                st.session_state.status_table.append({
                    "Symbol": symbol,
                    "Articles": 0,
                    "Status": "Failed"
                })
                continue
                
            # Save articles to CSV
            filename = os.path.join(OUTPUT_DIR, f"{symbol}_news.csv")
            pd.DataFrame(articles).to_csv(filename, index=False)
            
            # Fetch content for each article
            df = pd.DataFrame(articles)
            df['content'] = None
            
            for idx, row in df.iterrows():
                if pd.isna(row['content']):
                    content = fetch_content(row['url'])
                    df.at[idx, 'content'] = content if content else "Content unavailable"
                    time.sleep(1.5)  # Rate limiting
                    
            # Save updated CSV
            df.to_csv(filename, index=False)
            
            st.session_state.status_table.append({
                "Symbol": symbol,
                "Articles": len(articles),
                "Status": "Completed"
            })
            log_status(f"✅ Completed processing for {symbol}")
            
        log_status("🎉 All processing completed successfully!")
        
    except Exception as e:
        log_status(f"❌ Critical error: {str(e)}")
    finally:
        st.session_state.processing = False

if st.button("Clear Temporary Storage"):
    clear_temp_storage()

# Status displays
st.subheader("Processing Status")
if st.session_state.process_status:
    st.text_area("Log", value="\n".join(st.session_state.process_status), height=200)

if st.session_state.status_table:
    st.subheader("Results Summary")
    st.table(pd.DataFrame(st.session_state.status_table))

# Download section
if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        st.subheader("Download Processed Files")
        for csv_file in csv_files:
            with open(os.path.join(OUTPUT_DIR, csv_file), "rb") as f:
                st.download_button(
                    label=f"Download {csv_file}",
                    data=f,
                    file_name=csv_file,
                    mime="text/csv"
                )
