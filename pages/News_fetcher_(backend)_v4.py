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

# Thread-safe locks
status_lock = threading.Lock()
file_lock = threading.Lock()

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
    try:
        if "seeking_alpha_api_keys" in st.session_state and st.session_state["seeking_alpha_api_keys"]:
            keys = st.session_state["seeking_alpha_api_keys"]
            
            if "current_key_index_seeking_alpha" not in st.session_state:
                st.session_state["current_key_index_seeking_alpha"] = 0
            
            if st.session_state["current_key_index_seeking_alpha"] >= len(keys):
                st.session_state["current_key_index_seeking_alpha"] = 0
            
            if "stocks_processed_with_current_key_seeking_alpha" in st.session_state:
                if st.session_state["stocks_processed_with_current_key_seeking_alpha"] >= st.session_state["stocks_per_key_seeking_alpha"]:
                    st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
                    st.session_state["current_key_index_seeking_alpha"] = (st.session_state["current_key_index_seeking_alpha"] + 1) % len(keys)
                
                st.session_state["stocks_processed_with_current_key_seeking_alpha"] += 1
            else:
                st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 1
            
            return keys[st.session_state["current_key_index_seeking_alpha"]]
    except Exception as e:
        st.error(f"Error getting Seeking Alpha API key from session state: {e}")
    
    try:
        if GLOBAL_SEEKING_ALPHA_KEYS:
            return GLOBAL_SEEKING_ALPHA_KEYS[0]
    except:
        pass
    
    return DEFAULT_API_KEY

def get_next_perplexity_api_key():
    try:
        if "perplexity_api_keys" in st.session_state and st.session_state["perplexity_api_keys"]:
            keys = st.session_state["perplexity_api_keys"]
            
            if "current_key_index_perplexity" not in st.session_state:
                st.session_state["current_key_index_perplexity"] = 0
            
            if st.session_state["current_key_index_perplexity"] >= len(keys):
                st.session_state["current_key_index_perplexity"] = 0
            
            if "stocks_processed_with_current_key_perplexity" in st.session_state:
                if st.session_state["stocks_processed_with_current_key_perplexity"] >= st.session_state["stocks_per_key_perplexity"]:
                    st.session_state["stocks_processed_with_current_key_perplexity"] = 0
                    st.session_state["current_key_index_perplexity"] = (st.session_state["current_key_index_perplexity"] + 1) % len(keys)
                
                st.session_state["stocks_processed_with_current_key_perplexity"] += 1
            else:
                st.session_state["stocks_processed_with_current_key_perplexity"] = 1
            
            return keys[st.session_state["current_key_index_perplexity"]]
    except Exception as e:
        st.error(f"Error getting Perplexity API key from session state: {e}")
    
    try:
        if GLOBAL_PERPLEXITY_KEYS:
            return GLOBAL_PERPLEXITY_KEYS[0]
    except:
        pass
    
    return DEFAULT_API_KEY

def test_api_key(api_key, api_host):
    try:
        conn = http.client.HTTPSConnection(api_host)
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
    except:
        return False

def fetch_articles_for_symbol(worker_id: int, symbol: str, since_timestamp: int, until_timestamp: int, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    try:
        api_key = get_next_seeking_alpha_api_key()
        status_queue.put(f"Worker {worker_id}: Fetching articles for: {symbol}")
        
        conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA)
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
                time.sleep(0.5)

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
    """Update the summary for a specific article in its CSV file"""
    try:
        file_path = os.path.join(dirs["articles"], f"{symbol.lower()}_news_data.csv")
        
        # Use file lock to prevent concurrent access
        with file_lock:
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
                st.error(f"Article ID {article_id} not found in {symbol} data")
                return False
    except Exception as e:
        st.error(f"Error updating summary for {symbol} article {article_id}: {e}")
        return False

def fetch_content_for_article(worker_id: int, article_id: int, symbol: str, title: str, publish_date: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
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
        
        status_queue.put(f"Worker {worker_id}: Fetching summary for: {title}")
        
        conn = http.client.HTTPSConnection(API_HOST_PERPLEXITY)
        
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST_PERPLEXITY,
            'Content-Type': "application/json"
        }
        
        query = summary_prompt_template.replace("{title}", title).replace("{date}", str(formatted_date))
        payload = json.dumps({"content": query})
        
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data_bytes = res.read()
        
        if not data_bytes:
            error_msg = f"Empty response for article '{title}'"
            status_queue.put(error_msg)
            result_queue.put((article_id, symbol, f"Error: {error_msg}"))
            return
        
        try:
            data = data_bytes.decode("utf-8")
            json_data = json.loads(data)
            
            if "choices" in json_data and "content" in json_data["choices"] and "parts" in json_data["choices"]["content"]:
                parts = json_data["choices"]["content"]["parts"]
                if parts and len(parts) > 0 and "text" in parts[0]:
                    summary = parts[0]["text"]
                    # Immediately update the CSV file with the new summary
                    if update_article_summary(symbol, article_id, summary):
                        result_queue.put((article_id, symbol, summary))
                        return
            
            if "answer" in json_data:
                summary = json_data["answer"]
                if update_article_summary(symbol, article_id, summary):
                    result_queue.put((article_id, symbol, summary))
                    return
                
            summary = f"API response structure unexpected. Raw response (truncated): {str(json_data)[:500]}"
            if update_article_summary(symbol, article_id, summary):
                result_queue.put((article_id, symbol, summary))
            
        except json.JSONDecodeError:
            summary = f"Non-JSON response: {data[:500]}"
            if update_article_summary(symbol, article_id, summary):
                result_queue.put((article_id, symbol, summary))
            
    except Exception as e:
        error_msg = f"Error fetching summary for '{title}': {e}"
        status_queue.put(error_msg)
        result_queue.put((article_id, symbol, f"Error: {str(e)}"))

def divide_into_chunks(items, num_chunks):
    if not items:
        return []
    
    avg = len(items) / float(num_chunks)
    result = []
    last = 0.0
    
    while last < len(items):
        result.append(items[int(last):int(last + avg)])
        last += avg
        
    return result

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2025, 4, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2025, 4, 30))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        valid_keys = []
        for key in st.session_state["seeking_alpha_api_keys"]:
            if test_api_key(key, API_HOST_SEEKING_ALPHA):
                valid_keys.append(key)
        
        if not valid_keys:
            st.error("No valid Seeking Alpha API keys found! Please enter at least one valid key.")
        else:
            st.session_state["seeking_alpha_api_keys"] = valid_keys
            update_global_seeking_alpha_keys(valid_keys)
            
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            st.session_state["articles_fetched"] = False
            st.session_state["content_fetched"] = False
            st.session_state["processed_symbols_seeking_alpha"] = set()
            
            try:
                with open(SYMBOL_FILE, "r") as f:
                    symbols = [line.strip() for line in f.readlines()]
            except FileNotFoundError:
                st.error(f"Symbol file not found: {SYMBOL_FILE}")
                os.makedirs(os.path.dirname(SYMBOL_FILE), exist_ok=True)
                with open(SYMBOL_FILE, "w") as f:
                    f.write("AAPL\nMSFT\nGOOG")
                symbols = ["AAPL", "MSFT", "GOOG"]
            
            num_workers = min(max_workers, len(valid_keys))
            st.write(f"Using {num_workers} parallel workers for fetching articles")
            
            status_queue = Queue()
            result_queue = Queue()
            error_queue = Queue()
            
            symbol_batches = divide_into_chunks(symbols, num_workers)
            
            progress_bar = st.progress(0)
            status_area = st.empty()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = []
                for i in range(min(num_workers, len(symbol_batches))):
                    if i < len(symbol_batches) and symbol_batches[i]:
                        for symbol in symbol_batches[i]:
                            future = executor.submit(
                                fetch_articles_for_symbol,
                                i+1, symbol, since_timestamp, until_timestamp,
                                status_queue, result_queue, error_queue
                            )
                            futures.append((future, symbol))
                
                results = {}
                processed_count = 0
                total_count = len(symbols)
                
                while processed_count < total_count:
                    status_messages = []
                    while not status_queue.empty():
                        status = status_queue.get()
                        st.session_state["process_status"].append(status)
                        status_messages.append(status)
                    
                    if status_messages:
                        status_area.text("\n".join(status_messages[-5:]))
                    
                    while not result_queue.empty():
                        symbol, articles = result_queue.get()
                        processed_count += 1
                        
                        if articles:
                            results[symbol] = articles
                            st.session_state["processed_symbols_seeking_alpha"].add(symbol)
                        
                        progress_bar.progress(processed_count / total_count)
                    
                    while not error_queue.empty():
                        symbol, timestamp, reason = error_queue.get()
                        st.session_state["failed_symbols"][symbol] = {
                            "timestamp": timestamp,
                            "reason": reason
                        }
                    
                    for future, symbol in list(futures):
                        if future.done():
                            futures.remove((future, symbol))
                            try:
                                future.result()
                            except Exception as e:
                                st.error(f"Error in worker thread for {symbol}: {e}")
                                if symbol not in results:
                                    processed_count += 1
                    
                    if not futures and processed_count < total_count:
                        st.error(f"All workers finished but only processed {processed_count}/{total_count} symbols")
                        break
                    
                    time.sleep(0.1)
            
            for symbol, articles in results.items():
                try:
                    os.makedirs(dirs["articles"], exist_ok=True)
                    
                    file_name = os.path.join(dirs["articles"], f"{symbol.lower()}_news_data.csv")
                    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['ID', 'Publish Date', 'Title', 'Author ID', 'Comment Count', 'Summary']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in articles:
                            writer.writerow({
                                'ID': item['id'],
                                'Publish Date': item['attributes']['publishOn'],
                                'Title': item['attributes']['title'],
                                'Author ID': item['relationships']['author']['data']['id'],
                                'Comment Count': item['attributes']['commentCount'],
                                'Summary': ""
                            })
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": len(articles)
                    })
                    st.session_state["process_status"].append(f"Saved {len(articles)} articles for {symbol}")
                    
                    if symbol in st.session_state["failed_symbols"]:
                        del st.session_state["failed_symbols"][symbol]
                except Exception as e:
                    st.error(f"Error saving articles for {symbol}: {e}")
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": f"Error: {e}"
                    })
            
            save_failed_symbols()
            st.session_state["articles_fetched"] = True
            st.success("Articles fetched successfully! You can now fetch content summaries.")

with col2:
    if st.button("Fetch Content", disabled=not st.session_state["articles_fetched"]):
        valid_keys = []
        for key in st.session_state["perplexity_api_keys"]:
            if test_api_key(key, API_HOST_PERPLEXITY):
                valid_keys.append(key)
        
        if not valid_keys:
            st.error("No valid Perplexity API keys found! Please enter at least one valid key.")
        else:
            st.session_state["perplexity_api_keys"] = valid_keys
            update_global_perplexity_keys(valid_keys)
            
            st.session_state["process_status"].append("Starting to fetch content summaries...")
            st.session_state["processed_symbols_perplexity"] = set()
            
            try:
                os.makedirs(dirs["articles"], exist_ok=True)
                csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
                
                # NEW WORKER CALCULATION LOGIC
                articles_per_key = st.session_state["stocks_per_key_perplexity"]
                all_articles = []
                symbol_to_file = {}
                
                for csv_file in csv_files:
                    symbol = csv_file.replace("_news_data.csv", "")
                    file_path = os.path.join(dirs["articles"], csv_file)
                    symbol_to_file[symbol] = file_path
                    
                    df = pd.read_csv(file_path)
                    
                    for _, row in df.iterrows():
                        if pd.isna(row['Summary']) or row['Summary'].startswith("Error:"):
                            article_id = row['ID']
                            title = row['Title']
                            publish_date = row['Publish Date']
                            all_articles.append((article_id, symbol, title, publish_date))
                
                # Calculate optimal worker count
                keys_needed = min(len(valid_keys), (len(all_articles) + articles_per_key - 1) // articles_per_key)
                num_workers = min(max_workers, keys_needed)
                num_workers = max(1, num_workers)  # Ensure at least 1 worker
                
                st.write(f"Using {num_workers} workers ({keys_needed} keys needed for {len(all_articles)} articles at {articles_per_key} per key)")
                
                # NEW TASK DISTRIBUTION LOGIC
                articles_per_worker = articles_per_key
                article_batches = []
                for i in range(num_workers):
                    start_idx = i * articles_per_worker
                    end_idx = (i + 1) * articles_per_worker
                    article_batches.append(all_articles[start_idx:end_idx])
                
                st.write(f"Work distribution: {[len(batch) for batch in article_batches]} batches")
                
                status_queue = Queue()
                result_queue = Queue()
                error_queue = Queue()
                
                progress_bar = st.progress(0)
                status_area = st.empty()
                eta_display = st.empty()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = []
                    for i in range(num_workers):
                        if i < len(article_batches) and article_batches[i]:
                            for article_id, symbol, title, publish_date in article_batches[i]:
                                future = executor.submit(
                                    fetch_content_for_article,
                                    i+1, article_id, symbol, title, publish_date,
                                    status_queue, result_queue, error_queue
                                )
                                futures.append((future, article_id, symbol))
                                time.sleep(st.session_state["delay_between_calls"])
                
                elapsed_time = time.time() - start_time
                st.session_state["content_fetched"] = True
                st.success(f"Content summaries fetched successfully! Added {total_count} summaries in {elapsed_time:.1f} seconds.")
            except Exception as e:
                st.error(f"Error fetching content: {e}")

with col3:
    if st.button("Clean Up"):
        st.session_state["process_status"] = []
        st.session_state["process_status"].append("Starting cleanup...")
        
        try:
            if os.path.exists(dirs["articles"]):
                csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
                file_count = len(csv_files)
                
                for file in csv_files:
                    file_path = os.path.join(dirs["articles"], file)
                    try:
                        os.remove(file_path)
                        st.session_state["process_status"].append(f"Deleted: {file}")
                    except Exception as e:
                        st.session_state["process_status"].append(f"Error deleting {file}: {e}")
                
                st.session_state["process_status"].append(f"Cleanup complete. Deleted {file_count} files.")
                st.success(f"Cleanup complete. Deleted {file_count} files.")
            else:
                st.warning("Articles directory does not exist. Nothing to clean up.")
        except Exception as e:
            st.error(f"Error during cleanup: {e}")

# Display failed symbols
if st.session_state["failed_symbols"]:
    with st.expander("Failed Symbols", expanded=True):
        st.write(f"There are {len(st.session_state['failed_symbols'])} symbols that failed processing:")
        failed_data = []
        for symbol, details in st.session_state["failed_symbols"].items():
            failed_data.append({
                "Symbol": symbol,
                "Timestamp": details["timestamp"],
                "Reason": details["reason"]
            })
        
        failed_df = pd.DataFrame(failed_data)
        st.dataframe(failed_df)
        
        if st.button("Clear Failed Symbols List"):
            st.session_state["failed_symbols"] = {}
            save_failed_symbols()
            st.success("Failed symbols list cleared.")

# Display API key usage
with st.expander("API Key Usage"):
    st.write("### Seeking Alpha API")
    st.write(f"Number of keys: {len(st.session_state['seeking_alpha_api_keys'])}")
    st.write(f"Current key index: {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['seeking_alpha_api_keys'])}")
    st.write(f"Stocks processed with current key: {st.session_state['stocks_processed_with_current_key_seeking_alpha']} of {st.session_state['stocks_per_key_seeking_alpha']}")
    st.write(f"Total stocks processed: {len(st.session_state['processed_symbols_seeking_alpha'])}")
    
    st.write("### Perplexity API")
    st.write(f"Number of keys: {len(st.session_state['perplexity_api_keys'])}")
    st.write(f"Current key index: {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['perplexity_api_keys'])}")
    st.write(f"Stocks processed with current key: {st.session_state['stocks_processed_with_current_key_perplexity']} of {st.session_state['stocks_per_key_perplexity']}")
    st.write(f"Total stocks processed: {len(st.session_state['processed_symbols_perplexity'])}")

# Display status table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.table(status_df)

# Display process status
if st.session_state["process_status"]:
    st.write("### Process Status")
    status_container = st.container()
    with status_container:
        for status in st.session_state["process_status"]:
            st.write(status)

# Preview section for summaries
if st.session_state["content_fetched"]:
    st.write("### Content Summaries Preview")
    try:
        if os.path.exists(dirs["articles"]):
            csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
            
            if csv_files:
                tabs = st.tabs([f.replace("_news_data.csv", "").upper() for f in csv_files])
                
                for i, tab in enumerate(tabs):
                    with tab:
                        file_path = os.path.join(dirs["articles"], csv_files[i])
                        df = pd.read_csv(file_path)
                        
                        if 'Summary' in df.columns and not df['Summary'].isna().all():
                            for _, row in df.iterrows():
                                with st.expander(f"{row['Title']} ({row['Publish Date']})"):
                                    st.write(row['Summary'])
                        else:
                            st.write("No summaries available for this symbol.")
            else:
                st.warning("No CSV files found in the articles directory.")
        else:
            st.warning("Articles directory does not exist.")
    except Exception as e:
        st.error(f"Error displaying summaries: {e}")

# Download Section
try:
    if os.path.exists(dirs["articles"]):
        csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
        if csv_files:
            st.write("### Download Extracted Files")
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    try:
                        with open(os.path.join(dirs["articles"], csv_file), "r") as f:
                            st.download_button(
                                label=f"Download {csv_file}",
                                data=f.read(),
                                file_name=csv_file,
                                mime="text/csv"
                            )
                    except Exception as e:
                        st.error(f"Error creating download button for {csv_file}: {e}")
        else:
            st.warning("No CSV files found in the output directory.")
    else:
        st.warning("Output directory does not exist.")
except Exception as e:
    st.error(f"Error in download section: {e}")

# Display storage information
with st.expander("Storage Information"):
    try:
        total_size = 0
        file_count = 0
        
        if os.path.exists(st.session_state["output_dir"]):
            for root, dirs, files in os.walk(st.session_state["output_dir"]):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            if total_size < 1024:
                size_str = f"{total_size} bytes"
            elif total_size < 1024 * 1024:
                size_str = f"{total_size/1024:.2f} KB"
            else:
                size_str = f"{total_size/(1024*1024):.2f} MB"
            
            st.write(f"Total storage used: {size_str}")
            st.write(f"Total files: {file_count}")
        else:
            st.warning("Output directory does not exist.")
        
        st.write("### Directory Structure:")
        if isinstance(dirs, dict):
            for dir_name, dir_path in dirs.items():
                st.write(f"- {dir_name}: {dir_path}")
                if os.path.exists(dir_path):
                    files = os.listdir(dir_path)
                    if files:
                        st.write(f"  Contains {len(files)} files")
                    else:
                        st.write("  Empty directory")
                else:
                    st.write("  Directory does not exist")
        else:
            st.error("Directory structure information is not available.")
    except Exception as e:
        st.error(f"Error displaying storage information: {e}")

# Debug information
with st.expander("Debug Information"):
    st.write("### Session State Variables")
    st.write(f"seeking_alpha_api_keys exists: {'seeking_alpha_api_keys' in st.session_state}")
    if 'seeking_alpha_api_keys' in st.session_state:
        st.write(f"seeking_alpha_api_keys value: {st.session_state['seeking_alpha_api_keys']}")
    
    st.write(f"perplexity_api_keys exists: {'perplexity_api_keys' in st.session_state}")
    if 'perplexity_api_keys' in st.session_state:
        st.write(f"perplexity_api_keys value: {st.session_state['perplexity_api_keys']}")
    
    st.write("### Global Variables")
    st.write(f"GLOBAL_SEEKING_ALPHA_KEYS: {GLOBAL_SEEKING_ALPHA_KEYS}")
    st.write(f"GLOBAL_PERPLEXITY_KEYS: {GLOBAL_PERPLEXITY_KEYS}")
    
    st.write("### Test API Keys")
    if st.button("Test Seeking Alpha Keys"):
        for i, key in enumerate(st.session_state.get("seeking_alpha_api_keys", [])):
            is_valid = test_api_key(key, API_HOST_SEEKING_ALPHA)
            st.write(f"Key {i+1}: {'Valid' if is_valid else 'Invalid'}")
    
    if st.button("Test Perplexity Keys"):
        for i, key in enumerate(st.session_state.get("perplexity_api_keys", [])):
            is_valid = test_api_key(key, API_HOST_PERPLEXITY)
            st.write(f"Key {i+1}: {'Valid' if is_valid else 'Invalid'}")

def verify_summaries():
    try:
        if not os.path.exists(dirs["articles"]):
            st.error("Articles directory does not exist")
            return
        
        csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
        if not csv_files:
            st.error("No CSV files found in articles directory")
            return
        
        st.write("### Summary Verification")
        
        for csv_file in csv_files:
            file_path = os.path.join(dirs["articles"], csv_file)
            symbol = csv_file.replace("_news_data.csv", "")
            
            try:
                df = pd.read_csv(file_path)
                
                if 'Summary' not in df.columns:
                    st.error(f"Error: 'Summary' column not found in {csv_file}")
                    continue
                
                total_rows = len(df)
                non_empty_summaries = df['Summary'].notna().sum()
                empty_summaries = total_rows - non_empty_summaries
                
                st.write(f"**{symbol.upper()}**: {non_empty_summaries}/{total_rows} summaries ({empty_summaries} empty)")
                
                if non_empty_summaries > 0:
                    with st.expander(f"Sample summaries for {symbol.upper()}"):
                        sample_df = df[df['Summary'].notna() & (df['Summary'] != "")].head(3)
                        for _, row in sample_df.iterrows():
                            st.write(f"**{row['Title']}**")
                            st.write(row['Summary'])
                            st.write("---")
            except Exception as e:
                st.error(f"Error verifying summaries for {csv_file}: {e}")
    except Exception as e:
        st.error(f"Error in verify_summaries: {e}")

if st.session_state["content_fetched"]:
    if st.button("Verify Summaries"):
        verify_summaries()
