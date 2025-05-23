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
import platform
import threading
import concurrent.futures
from queue import Queue
from typing import List, Dict, Any, Tuple, Set

# CRITICAL FIX: Define global variables at the module level
GLOBAL_SEEKING_ALPHA_KEYS = []
GLOBAL_PERPLEXITY_KEYS = []

# Thread-safe locks
status_lock = threading.Lock()
file_lock = threading.Lock()
key_rotation_lock = threading.Lock()  # Added lock for key rotation

# Default paths based on OS
def get_default_output_dir():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Documents", "SeekingAlphaNews")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Documents", "SeekingAlphaNews")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "SeekingAlphaNews")

# Configuration
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"
API_HOST_SEEKING_ALPHA = "seeking-alpha.p.rapidapi.com"
API_HOST_PERPLEXITY = "perplexity2.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4

# Initialize session state variables
if "seeking_alpha_api_keys" not in st.session_state:
    st.session_state["seeking_alpha_api_keys"] = [DEFAULT_API_KEY]
    GLOBAL_SEEKING_ALPHA_KEYS = [DEFAULT_API_KEY]

if "perplexity_api_keys" not in st.session_state:
    st.session_state["perplexity_api_keys"] = [DEFAULT_API_KEY]
    GLOBAL_PERPLEXITY_KEYS = [DEFAULT_API_KEY]

# Initialize other session state variables
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "process_status" not in st.session_state:
    st.session_state["process_status"] = []
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY
if "articles_fetched" not in st.session_state:
    st.session_state["articles_fetched"] = False
if "content_fetched" not in st.session_state:
    st.session_state["content_fetched"] = False
if "delay_between_calls" not in st.session_state:
    st.session_state["delay_between_calls"] = 0.5
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "failed_symbols" not in st.session_state:
    st.session_state["failed_symbols"] = {}
if "directories" not in st.session_state:
    st.session_state["directories"] = {}

# API rotation states
if "current_key_index_seeking_alpha" not in st.session_state:
    st.session_state["current_key_index_seeking_alpha"] = 0
if "stocks_processed_with_current_key_seeking_alpha" not in st.session_state:
    st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
if "stocks_per_key_seeking_alpha" not in st.session_state:
    st.session_state["stocks_per_key_seeking_alpha"] = 20

if "current_key_index_perplexity" not in st.session_state:
    st.session_state["current_key_index_perplexity"] = 0
if "stocks_processed_with_current_key_perplexity" not in st.session_state:
    st.session_state["stocks_processed_with_current_key_perplexity"] = 0
if "stocks_per_key_perplexity" not in st.session_state:
    st.session_state["stocks_per_key_perplexity"] = 6

if "processed_symbols_seeking_alpha" not in st.session_state:
    st.session_state["processed_symbols_seeking_alpha"] = set()
if "processed_symbols_perplexity" not in st.session_state:
    st.session_state["processed_symbols_perplexity"] = set()

def update_global_seeking_alpha_keys(keys):
    global GLOBAL_SEEKING_ALPHA_KEYS
    GLOBAL_SEEKING_ALPHA_KEYS = keys

def update_global_perplexity_keys(keys):
    global GLOBAL_PERPLEXITY_KEYS
    GLOBAL_PERPLEXITY_KEYS = keys

# Streamlit UI
st.title("News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and process them.")

# Output directory configuration
st.session_state["output_dir"] = st.text_input(
    "Output Directory",
    value=st.session_state["output_dir"],
    help="Directory where all files will be saved"
)

def ensure_directories():
    try:
        os.makedirs(st.session_state["output_dir"], exist_ok=True)
        articles_dir = os.path.join(st.session_state["output_dir"], "articles")
        os.makedirs(articles_dir, exist_ok=True)
        logs_dir = os.path.join(st.session_state["output_dir"], "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return {
            "main": st.session_state["output_dir"],
            "articles": articles_dir,
            "logs": logs_dir
        }
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        return {
            "main": st.session_state["output_dir"],
            "articles": os.path.join(st.session_state["output_dir"], "articles"),
            "logs": os.path.join(st.session_state["output_dir"], "logs")
        }

try:
    st.session_state["directories"] = ensure_directories()
    dirs = st.session_state["directories"]
except Exception as e:
    st.error(f"Error initializing directories: {e}")
    dirs = {
        "main": st.session_state["output_dir"],
        "articles": os.path.join(st.session_state["output_dir"], "articles"),
        "logs": os.path.join(st.session_state["output_dir"], "logs")
    }
    st.session_state["directories"] = dirs

def save_failed_symbols():
    try:
        failed_file = os.path.join(dirs["logs"], "failed_symbols.txt")
        os.makedirs(os.path.dirname(failed_file), exist_ok=True)
        with open(failed_file, "w", encoding="utf-8") as f:
            for symbol, details in st.session_state["failed_symbols"].items():
                f.write(f"{symbol},{details['timestamp']},{details['reason']}\n")
        return failed_file
    except Exception as e:
        st.error(f"Error saving failed symbols: {e}")
        return None

def load_failed_symbols():
    try:
        failed_file = os.path.join(dirs["logs"], "failed_symbols.txt")
        if os.path.exists(failed_file):
            with open(failed_file, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",", 2)
                    if len(parts) >= 3:
                        symbol, timestamp, reason = parts
                        st.session_state["failed_symbols"][symbol] = {
                            "timestamp": timestamp,
                            "reason": reason
                        }
    except Exception as e:
        st.error(f"Error loading failed symbols: {e}")

try:
    load_failed_symbols()
except Exception as e:
    st.error(f"Error during startup: {e}")

# API Keys Configuration
st.subheader("API Keys Configuration")

seeking_alpha_keys = st.text_area(
    "Seeking Alpha API Keys (one per line)",
    help="Enter RapidAPI keys for Seeking Alpha only."
)
if seeking_alpha_keys:
    keys = [k.strip() for k in seeking_alpha_keys.split('\n') if k.strip()]
    if keys:
        st.session_state["seeking_alpha_api_keys"] = keys
        update_global_seeking_alpha_keys(keys)
        total_capacity_seeking_alpha = len(keys) * st.session_state["stocks_per_key_seeking_alpha"]
        st.write(f"Found {len(keys)} Seeking Alpha API keys.")
        st.write(f"Can process approximately {total_capacity_seeking_alpha} stocks with Seeking Alpha API.")
elif not st.session_state["seeking_alpha_api_keys"]:
    st.session_state["seeking_alpha_api_keys"] = [DEFAULT_API_KEY]
    update_global_seeking_alpha_keys([DEFAULT_API_KEY])
    st.warning("No Seeking Alpha API keys provided. Using default key which is rate-limited.")

perplexity_keys = st.text_area(
    "Perplexity API Keys (one per line)",
    help="Enter RapidAPI keys for Perplexity only."
)
if perplexity_keys:
    keys = [k.strip() for k in perplexity_keys.split('\n') if k.strip()]
    if keys:
        st.session_state["perplexity_api_keys"] = keys
        update_global_perplexity_keys(keys)
        total_capacity_perplexity = len(keys) * st.session_state["stocks_per_key_perplexity"]
        st.write(f"Found {len(keys)} Perplexity API keys.")
        st.write(f"Can process approximately {total_capacity_perplexity} stocks with Perplexity API.")
elif not st.session_state["perplexity_api_keys"]:
    st.session_state["perplexity_api_keys"] = [DEFAULT_API_KEY]
    update_global_perplexity_keys([DEFAULT_API_KEY])
    st.warning("No Perplexity API keys provided. Using default key which is rate-limited.")

# API rotation settings
col1, col2 = st.columns(2)
with col1:
    st.session_state["stocks_per_key_seeking_alpha"] = st.number_input(
        "Stocks per key (Seeking Alpha)",
        min_value=1,
        value=st.session_state["stocks_per_key_seeking_alpha"],
        help="Number of stocks to process with each key for Seeking Alpha API"
    )

with col2:
    st.session_state["stocks_per_key_perplexity"] = st.number_input(
        "Stocks per key (Perplexity)",
        min_value=1,
        value=st.session_state["stocks_per_key_perplexity"],
        help="Number of stocks to process with each key for Perplexity API"
    )

# Advanced settings
with st.expander("Advanced Settings"):
    summary_prompt_template = st.text_area(
        "Summary Prompt Template",
        value="Do you know about '{title}' news published on {date}? Sumarize it within 150 words. Do not judge, or have bias. Report as it is.",
        help="Template for the prompt sent to Perplexity API. Use {title} and {date} as placeholders."
    )
    
    st.session_state["delay_between_calls"] = st.slider(
        "Delay Between API Calls (seconds)", 
        min_value=0.1, 
        max_value=2.0, 
        value=st.session_state["delay_between_calls"],
        step=0.1
    )
    
    max_workers = st.slider(
        "Maximum Parallel Workers", 
        min_value=1, 
        max_value=8, 
        value=MAX_WORKERS,
        step=1
    )

def get_next_seeking_alpha_api_key():
    """Thread-safe function to get the next Seeking Alpha API key"""
    with key_rotation_lock:
        if "seeking_alpha_api_keys" not in st.session_state or not st.session_state["seeking_alpha_api_keys"]:
            return DEFAULT_API_KEY
            
        keys = st.session_state["seeking_alpha_api_keys"]
        if not keys:
            return DEFAULT_API_KEY
            
        if "current_key_index_seeking_alpha" not in st.session_state:
            st.session_state["current_key_index_seeking_alpha"] = 0
            
        if st.session_state["current_key_index_seeking_alpha"] >= len(keys):
            st.session_state["current_key_index_seeking_alpha"] = 0
            
        if "stocks_processed_with_current_key_seeking_alpha" not in st.session_state:
            st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
            
        # Increment the counter
        st.session_state["stocks_processed_with_current_key_seeking_alpha"] += 1
        
        # Check if we need to rotate to the next key
        if st.session_state["stocks_processed_with_current_key_seeking_alpha"] > st.session_state["stocks_per_key_seeking_alpha"]:
            st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 1
            st.session_state["current_key_index_seeking_alpha"] = (st.session_state["current_key_index_seeking_alpha"] + 1) % len(keys)
            
        return keys[st.session_state["current_key_index_seeking_alpha"]]

def get_next_perplexity_api_key():
    """Thread-safe function to get the next Perplexity API key"""
    with key_rotation_lock:
        if "perplexity_api_keys" not in st.session_state or not st.session_state["perplexity_api_keys"]:
            return DEFAULT_API_KEY
            
        keys = st.session_state["perplexity_api_keys"]
        if not keys:
            return DEFAULT_API_KEY
            
        if "current_key_index_perplexity" not in st.session_state:
            st.session_state["current_key_index_perplexity"] = 0
            
        if st.session_state["current_key_index_perplexity"] >= len(keys):
            st.session_state["current_key_index_perplexity"] = 0
            
        if "stocks_processed_with_current_key_perplexity" not in st.session_state:
            st.session_state["stocks_processed_with_current_key_perplexity"] = 0
            
        # Increment the counter
        st.session_state["stocks_processed_with_current_key_perplexity"] += 1
        
        # Check if we need to rotate to the next key
        if st.session_state["stocks_processed_with_current_key_perplexity"] > st.session_state["stocks_per_key_perplexity"]:
            st.session_state["stocks_processed_with_current_key_perplexity"] = 1
            st.session_state["current_key_index_perplexity"] = (st.session_state["current_key_index_perplexity"] + 1) % len(keys)
            
        return keys[st.session_state["current_key_index_perplexity"]]

def test_api_key(api_key, api_host):
    try:
        conn = http.client.HTTPSConnection(api_host, timeout=10)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host
        }
        
        if api_host == API_HOST_SEEKING_ALPHA:
            conn.request("GET", "/news/v2/list-by-symbol?size=1&number=1&id=AAPL", headers=headers)
        else:
            headers['Content-Type'] = "application/json"
            payload = json.dumps({"content": "Hello"})
            conn.request("POST", "/", payload, headers)
            
        res = conn.getresponse()
        return res.status < 400
    except Exception as e:
        print(f"Error testing API key: {e}")
        return False

def fetch_articles_for_symbol(worker_id: int, symbol: str, since_timestamp: int, until_timestamp: int, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    try:
        api_key = get_next_seeking_alpha_api_key()
        status_queue.put(f"Worker {worker_id}: Fetching articles for: {symbol}")
        
        conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA, timeout=30)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST_SEEKING_ALPHA
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
                
                # Check for rate limiting or other API errors
                if res.status == 429:  # Too Many Requests
                    status_queue.put(f"Rate limit hit for {symbol}. Waiting and trying with a different key.")
                    time.sleep(2)  # Wait before trying with a different key
                    api_key = get_next_seeking_alpha_api_key()
                    headers['x-rapidapi-key'] = api_key
                    continue
                    
                if res.status >= 400:
                    error_msg = f"API error for {symbol}: HTTP {res.status} - {res.reason}"
                    status_queue.put(error_msg)
                    error_queue.put((symbol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                    break
                
                data_bytes = res.read()
                
                if not data_bytes:
                    error_msg = f"Empty response for {symbol} on page {page}"
                    status_queue.put(error_msg)
                    error_queue.put((symbol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                    break
                
                try:
                    data = json.loads(data_bytes.decode("utf-8"))
                except json.JSONDecodeError as e:
                    error_msg = f"Error parsing JSON for {symbol} on page {page}: {e}"
                    status_queue.put(error_msg)
                    error_queue.put((symbol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                    break

                if not data.get('data'):
                    break

                for item in data['data']:
                    if item['id'] not in seen_ids:
                        seen_ids.add(item['id'])
                        all_news_data.append(item)

                page += 1
                time.sleep(st.session_state["delay_between_calls"])

            except Exception as e:
                error_msg = f"Error fetching articles for {symbol} on page {page}: {e}"
                status_queue.put(error_msg)
                error_queue.put((symbol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                break
                
        status_queue.put(f"Worker {worker_id}: Found {len(all_news_data)} articles for {symbol}")
        result_queue.put((symbol, all_news_data))
        
    except Exception as e:
        error_msg = f"Fatal error fetching articles for {symbol}: {e}"
        status_queue.put(error_msg)
        error_queue.put((symbol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((symbol, None))

def update_article_summary(symbol: str, article_id: int, summary: str):
    """Update the summary for a specific article in its CSV file with improved thread safety"""
    try:
        file_path = os.path.join(dirs["articles"], f"{symbol.lower()}_news_data.csv")
        
        # Use file lock to prevent concurrent access
        with file_lock:
            # Check if file exists
            if not os.path.exists(file_path):
                return False
                
            # Read the existing data
            df = pd.read_csv(file_path)
            
            # Update the summary
            mask = df['ID'] == article_id
            if mask.any():
                df.loc[mask, 'Summary'] = summary
                
                # Save back to file
                df.to_csv(file_path, index=False)
                return True
            else:
                return False
    except Exception as e:
        with status_lock:
            st.session_state["process_status"].append(f"Error updating summary for {symbol} article {article_id}: {e}")
        return False

def fetch_content_for_article(worker_id: int, article_id: int, symbol: str, title: str, publish_date: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    """Fetch content summary for an article with improved error handling and retry logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            api_key = get_next_perplexity_api_key()
            
            try:
                if isinstance(publish_date, str):
                    date_obj = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                else:
                    formatted_date = publish_date
            except:
                formatted_date = publish_date
            
            status_queue.put(f"Worker {worker_id}: Fetching summary for: {title} (Attempt {retry_count + 1})")
            
            conn = http.client.HTTPSConnection(API_HOST_PERPLEXITY, timeout=60)
            
            headers = {
                'x-rapidapi-key': api_key,
                'x-rapidapi-host': API_HOST_PERPLEXITY,
                'Content-Type': "application/json"
            }
            
            # Get the prompt template from session state or use a default
            prompt_template = st.session_state.get("summary_prompt_template", 
                "Do you know about '{title}' news published on {date}? Summarize it within 150 words. Do not judge, or have bias. Report as it is.")
            
            query = prompt_template.replace("{title}", title).replace("{date}", str(formatted_date))
            payload = json.dumps({"content": query})
            
            conn.request("POST", "/", payload, headers)
            res = conn.getresponse()
            
            # Check for rate limiting or other API errors
            if res.status == 429:  # Too Many Requests
                status_queue.put(f"Rate limit hit for article '{title}'. Waiting and trying with a different key.")
                time.sleep(2)  # Wait before trying with a different key
                retry_count += 1
                continue
                
            if res.status >= 400:
                error_msg = f"API error for article '{title}': HTTP {res.status} - {res.reason}"
                status_queue.put(error_msg)
                retry_count += 1
                time.sleep(1)
                continue
            
            data_bytes = res.read()
            
            if not data_bytes:
                error_msg = f"Empty response for article '{title}'"
                status_queue.put(error_msg)
                retry_count += 1
                time.sleep(1)
                continue
            
            try:
                data = data_bytes.decode("utf-8")
                json_data = json.loads(data)
                
                # Extract summary based on response structure
                summary = None
                
                # Try to extract from choices structure (newer API format)
                if "choices" in json_data and "content" in json_data["choices"] and "parts" in json_data["choices"]["content"]:
                    parts = json_data["choices"]["content"]["parts"]
                    if parts and len(parts) > 0 and "text" in parts[0]:
                        summary = parts[0]["text"]
                
                # Try to extract from answer field (older API format)
                if summary is None and "answer" in json_data:
                    summary = json_data["answer"]
                
                # If we still don't have a summary, use a fallback
                if summary is None:
                    summary = f"API response structure unexpected. Raw response (truncated): {str(json_data)[:500]}"
                
                # Update the CSV file with the new summary
                if update_article_summary(symbol, article_id, summary):
                    result_queue.put((article_id, symbol, summary))
                    return
                else:
                    error_msg = f"Failed to update summary for article '{title}'"
                    status_queue.put(error_msg)
                    retry_count += 1
                    time.sleep(1)
                    continue
                
            except json.JSONDecodeError:
                summary = f"Non-JSON response: {data[:500]}"
                if update_article_summary(symbol, article_id, summary):
                    result_queue.put((article_id, symbol, summary))
                    return
                else:
                    retry_count += 1
                    time.sleep(1)
                    continue
            
        except Exception as e:
            error_msg = f"Error fetching summary for '{title}' (Attempt {retry_count + 1}): {e}"
            status_queue.put(error_msg)
            retry_count += 1
            time.sleep(1)
    
    # If we've exhausted all retries, report failure
    error_msg = f"Failed to fetch summary for '{title}' after {max_retries} attempts"
    status_queue.put(error_msg)
    result_queue.put((article_id, symbol, f"Error: {error_msg}"))

def divide_into_chunks(items, num_chunks):
    """Divide items into chunks with improved handling of edge cases"""
    if not items:
        return []
    
    if num_chunks <= 0:
        num_chunks = 1
    
    if len(items) <= num_chunks:
        return [[item] for item in items]
    
    avg = len(items) / float(num_chunks)
    result = []
    last = 0.
