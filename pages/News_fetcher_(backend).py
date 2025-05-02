import streamlit as st
import http.client
import json
import time
import os
import pandas as pd
from datetime import datetime
import shutil

# Configuration
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
API_HOST = "seeking-alpha.p.rapidapi.com"
PERPLEXITY_HOST = "perplexity2.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdire"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state.status_table = []
if "process_status" not in st.session_state:
    st.session_state.process_status = ["Ready to begin processing"]
if "api_key" not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY
if "processing" not in st.session_state:
    st.session_state.processing = False
if "current_stage" not in st.session_state:
    st.session_state.current_stage = ""

def log_status(message):
    st.session_state.process_status.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
    st.rerun()

def update_stage(stage):
    st.session_state.current_stage = stage
    log_status(f"ENTERING STAGE: {stage}")

def fetch_articles(symbol):
    try:
        update_stage(f"Fetching URLs for {symbol}")
        conn = http.client.HTTPSConnection(API_HOST)
        headers = {
            'x-rapidapi-key': st.session_state.api_key,
            'x-rapidapi-host': API_HOST
        }
        
        url = f"/news/v2/list-by-symbol?size=20&number=1&id={symbol}&since={since_timestamp}&until={until_timestamp}"
        conn.request("GET", url, headers=headers)
        
        res = conn.getresponse()
        if res.status != 200:
            log_status(f"❌ HTTP Error {res.status} for {symbol}")
            return None
            
        data = json.loads(res.read().decode("utf-8"))
        articles = data.get('data', [])
        
        if not articles:
            log_status(f"⚠️ No articles found for {symbol}")
            return []
            
        processed_articles = []
        for item in articles:
            processed_articles.append({
                'id': item['id'],
                'url': f"https://seekingalpha.com/article/{item['id']}",
                'publish_date': item['attributes']['publishOn'],
                'title': item['attributes']['title'],
                'author_id': item['relationships']['author']['data']['id'],
                'comment_count': item['attributes']['commentCount'],
                'primary_tickers': ', '.join([t['type'] for t in item['relationships']['primaryTickers']['data']]),
                'secondary_tickers': ', '.join([t['type'] for t in item['relationships']['secondaryTickers']['data']])
            })
        
        log_status(f"✅ Found {len(processed_articles)} articles for {symbol}")
        return processed_articles
        
    except Exception as e:
        log_status(f"❌ Failed to fetch articles for {symbol}: {str(e)}")
        return None

def fetch_content(url):
    try:
        update_stage(f"Extracting content from {url[:50]}...")
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
            log_status(f"⚠️ Perplexity Error {res.status} for {url[:50]}...")
            return None
            
        content = res.read().decode('utf-8')
        log_status(f"✓ Content extracted from {url[:50]}...")
        return content
        
    except Exception as e:
        log_status(f"⚠️ Failed to extract content: {str(e)}")
        return None

# Streamlit UI
st.title("📰 News Fetcher with Progress Tracking")
st.caption("Shows real-time progress for each processing stage")

# API Key Input
st.session_state.api_key = st.text_input(
    "RapidAPI Key",
    value=st.session_state.api_key,
    type="password"
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
if st.button("Start Processing") and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.status_table = []
    st.session_state.process_status = ["Starting processing..."]
    
    try:
        # Verify symbol file
        if not os.path.exists(SYMBOL_FILE):
            log_status(f"❌ Missing symbol file at {SYMBOL_FILE}")
            st.stop()
            
        # Read symbols
        with open(SYMBOL_FILE, "r") as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]
            
        if not symbols:
            log_status("❌ No symbols found in the file")
            st.stop()
            
        # Process each symbol
        for symbol in symbols:
            log_status(f"\n🔷 PROCESSING SYMBOL: {symbol}")
            
            # Stage 1: Fetch article URLs
            articles = fetch_articles(symbol)
            if articles is None:
                st.session_state.status_table.append({
                    "Symbol": symbol,
                    "Stage": "URL Fetch Failed",
                    "Articles": 0
                })
                continue
                
            if not articles:
                st.session_state.status_table.append({
                    "Symbol": symbol,
                    "Stage": "No Articles Found",
                    "Articles": 0
                })
                continue
                
            # Stage 2: Save initial data
            filename = os.path.join(OUTPUT_DIR, f"{symbol}_news.csv")
            pd.DataFrame(articles).to_csv(filename, index=False)
            
            # Stage 3: Fetch content
            log_status(f"⏳ Beginning content extraction for {len(articles)} articles...")
            df = pd.DataFrame(articles)
            df['content'] = None
            
            success_count = 0
            for idx, row in df.iterrows():
                content = fetch_content(row['url'])
                if content:
                    df.at[idx, 'content'] = content
                    success_count += 1
                time.sleep(1.5)  # Rate limiting
                
            # Save final data
            df.to_csv(filename, index=False)
            
            st.session_state.status_table.append({
                "Symbol": symbol,
                "Stage": "Completed",
                "Articles": len(articles),
                "Content Extracted": success_count
            })
            log_status(f"✅ Finished {symbol}: {success_count}/{len(articles)} content extracted")
            
        log_status("\n🎉 ALL PROCESSING COMPLETED!")
        
    except Exception as e:
        log_status(f"❌ CRITICAL ERROR: {str(e)}")
    finally:
        st.session_state.processing = False

# Status displays
st.subheader("Current Stage")
stage_placeholder = st.empty()

st.subheader("Processing Log")
log_placeholder = st.empty()

st.subheader("Results Summary")
table_placeholder = st.empty()

# Live updates
def refresh_display():
    stage_placeholder.markdown(f"**Current Stage:** `{st.session_state.current_stage}`")
    
    if st.session_state.process_status:
        log_placeholder.text_area("", value="\n".join(st.session_state.process_status[-15:]), 
                                height=300, key="log_area")
    
    if st.session_state.status_table:
        table_placeholder.table(pd.DataFrame(st.session_state.status_table))

refresh_display()

# Manual refresh button
if st.button("Refresh Display"):
    refresh_display()
    st.rerun()

# Clear data button
if st.button("Clear All Data"):
    st.session_state.processing = False
    st.session_state.process_status = ["Data cleared - ready for new processing"]
    st.session_state.status_table = []
    st.session_state.current_stage = ""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    refresh_display()
