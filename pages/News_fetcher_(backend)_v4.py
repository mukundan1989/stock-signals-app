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
# These will be used as fallbacks if session state fails
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
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Default placeholder
API_HOST_SEEKING_ALPHA = "seeking-alpha.p.rapidapi.com"
API_HOST_PERPLEXITY = "perplexity2.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4  # Maximum number of parallel workers

# CRITICAL FIX: Initialize session state variables at the very beginning
# This ensures they exist before any function tries to access them
if "seeking_alpha_api_keys" not in st.session_state:
    st.session_state["seeking_alpha_api_keys"] = [DEFAULT_API_KEY]
    # Update global fallback
    GLOBAL_SEEKING_ALPHA_KEYS = [DEFAULT_API_KEY]

if "perplexity_api_keys" not in st.session_state:
    st.session_state["perplexity_api_keys"] = [DEFAULT_API_KEY]
    # Update global fallback
    GLOBAL_PERPLEXITY_KEYS = [DEFAULT_API_KEY]

# Initialize session state
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
    st.session_state["delay_between_calls"] = 0.5  # Default to a shorter delay
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "failed_symbols" not in st.session_state:
    st.session_state["failed_symbols"] = {}  # Dictionary to store failed symbols and reasons
if "directories" not in st.session_state:
    st.session_state["directories"] = {}  # Initialize directories dictionary

# Seeking Alpha API rotation state
if "current_key_index_seeking_alpha" not in st.session_state:
    st.session_state["current_key_index_seeking_alpha"] = 0
if "stocks_processed_with_current_key_seeking_alpha" not in st.session_state:
    st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
if "stocks_per_key_seeking_alpha" not in st.session_state:
    st.session_state["stocks_per_key_seeking_alpha"] = 20  # Higher limit for Seeking Alpha

# Perplexity API rotation state
if "current_key_index_perplexity" not in st.session_state:
    st.session_state["current_key_index_perplexity"] = 0
if "stocks_processed_with_current_key_perplexity" not in st.session_state:
    st.session_state["stocks_processed_with_current_key_perplexity"] = 0
if "stocks_per_key_perplexity" not in st.session_state:
    st.session_state["stocks_per_key_perplexity"] = 6  # Lower limit for Perplexity

if "processed_symbols_seeking_alpha" not in st.session_state:
    st.session_state["processed_symbols_seeking_alpha"] = set()
if "processed_symbols_perplexity" not in st.session_state:
    st.session_state["processed_symbols_perplexity"] = set()

# Thread-safe locks for shared resources
status_lock = threading.Lock()
file_lock = threading.Lock()  # NEW: Add a lock for file operations

# Function to update global variables safely
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

# Create directory structure
def ensure_directories():
    try:
        # Main output directory
        os.makedirs(st.session_state["output_dir"], exist_ok=True)
        
        # Articles directory
        articles_dir = os.path.join(st.session_state["output_dir"], "articles")
        os.makedirs(articles_dir, exist_ok=True)
        
        # Logs directory
        logs_dir = os.path.join(st.session_state["output_dir"], "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # NEW: Add a progress directory for checkpoints
        progress_dir = os.path.join(st.session_state["output_dir"], "progress")
        os.makedirs(progress_dir, exist_ok=True)
        
        return {
            "main": st.session_state["output_dir"],
            "articles": articles_dir,
            "logs": logs_dir,
            "progress": progress_dir  # NEW: Add progress directory
        }
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        # Return a default dictionary to prevent errors
        return {
            "main": st.session_state["output_dir"],
            "articles": os.path.join(st.session_state["output_dir"], "articles"),
            "logs": os.path.join(st.session_state["output_dir"], "logs"),
            "progress": os.path.join(st.session_state["output_dir"], "progress")
        }

# Ensure directories exist and store in session state
try:
    st.session_state["directories"] = ensure_directories()
    dirs = st.session_state["directories"]
except Exception as e:
    st.error(f"Error initializing directories: {e}")
    # Provide a fallback
    dirs = {
        "main": st.session_state["output_dir"],
        "articles": os.path.join(st.session_state["output_dir"], "articles"),
        "logs": os.path.join(st.session_state["output_dir"], "logs"),
        "progress": os.path.join(st.session_state["output_dir"], "progress")
    }
    st.session_state["directories"] = dirs

# Function to save failed symbols to file
def save_failed_symbols():
    try:
        failed_file = os.path.join(dirs["logs"], "failed_symbols.txt")
        os.makedirs(os.path.dirname(failed_file), exist_ok=True)  # Ensure directory exists
        with open(failed_file, "w", encoding="utf-8") as f:
            for symbol, details in st.session_state["failed_symbols"].items():
                f.write(f"{symbol},{details['timestamp']},{details['reason']}\n")
        return failed_file
    except Exception as e:
        st.error(f"Error saving failed symbols: {e}")
        return None

# Function to load failed symbols from file
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

# Load failed symbols on startup
try:
    load_failed_symbols()
except Exception as e:
    st.error(f"Error during startup: {e}")

# CHANGE: Separate API Key Inputs for each service
st.subheader("API Keys Configuration")

# Seeking Alpha API Keys - UPDATED as per solution
seeking_alpha_keys = st.text_area(
    "Seeking Alpha API Keys (one per line)",
    help="Enter RapidAPI keys for Seeking Alpha only."
)
if seeking_alpha_keys:
    keys = [k.strip() for k in seeking_alpha_keys.split('\n') if k.strip()]
    if keys:  # Only update if we have valid keys
        st.session_state["seeking_alpha_api_keys"] = keys
        # Update global fallback
        update_global_seeking_alpha_keys(keys)
        
        total_capacity_seeking_alpha = len(keys) * st.session_state["stocks_per_key_seeking_alpha"]
        st.write(f"Found {len(keys)} Seeking Alpha API keys.")
        st.write(f"Can process approximately {total_capacity_seeking_alpha} stocks with Seeking Alpha API.")
elif not st.session_state["seeking_alpha_api_keys"]:
    # Add default key if none provided
    st.session_state["seeking_alpha_api_keys"] = [DEFAULT_API_KEY]
    update_global_seeking_alpha_keys([DEFAULT_API_KEY])
    st.warning("No Seeking Alpha API keys provided. Using default key which is rate-limited.")

# Perplexity API Keys - UPDATED as per solution
perplexity_keys = st.text_area(
    "Perplexity API Keys (one per line)",
    help="Enter RapidAPI keys for Perplexity only."
)
if perplexity_keys:
    keys = [k.strip() for k in perplexity_keys.split('\n') if k.strip()]
    if keys:  # Only update if we have valid keys
        st.session_state["perplexity_api_keys"] = keys
        # Update global fallback
        update_global_perplexity_keys(keys)
        
        total_capacity_perplexity = len(keys) * st.session_state["stocks_per_key_perplexity"]
        st.write(f"Found {len(keys)} Perplexity API keys.")
        st.write(f"Can process approximately {total_capacity_perplexity} stocks with Perplexity API.")
elif not st.session_state["perplexity_api_keys"]:
    # Add default key if none provided
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

# Advanced settings in expander
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
        step=0.1,
        help="Time to wait between API calls. Lower values make the process faster but might hit rate limits."
    )
    
    max_workers = st.slider(
        "Maximum Parallel Workers", 
        min_value=1, 
        max_value=8, 
        value=MAX_WORKERS,
        step=1,
        help="Maximum number of parallel workers. Each worker uses one API key."
    )
    
    # NEW: Add checkpoint frequency setting
    checkpoint_frequency = st.slider(
        "Checkpoint Frequency", 
        min_value=1, 
        max_value=50, 
        value=10,
        step=1,
        help="How often to save progress (every N articles processed)"
    )

# CRITICAL FIX: Completely rewritten function to be more robust
def get_next_seeking_alpha_api_key():
    """Get the next Seeking Alpha API key with robust error handling"""
    try:
        # First try to use session state
        if "seeking_alpha_api_keys" in st.session_state and st.session_state["seeking_alpha_api_keys"]:
            keys = st.session_state["seeking_alpha_api_keys"]
            
            # Make sure we have a valid index
            if "current_key_index_seeking_alpha" not in st.session_state:
                st.session_state["current_key_index_seeking_alpha"] = 0
            
            # Make sure the index is in range
            if st.session_state["current_key_index_seeking_alpha"] >= len(keys):
                st.session_state["current_key_index_seeking_alpha"] = 0
            
            # Check if we need to rotate to the next key
            if "stocks_processed_with_current_key_seeking_alpha" in st.session_state:
                if st.session_state["stocks_processed_with_current_key_seeking_alpha"] >= st.session_state["stocks_per_key_seeking_alpha"]:
                    # Reset counter and move to next key
                    st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
                    st.session_state["current_key_index_seeking_alpha"] = (st.session_state["current_key_index_seeking_alpha"] + 1) % len(keys)
                
                # Increment counter
                st.session_state["stocks_processed_with_current_key_seeking_alpha"] += 1
            else:
                st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 1
            
            # Return the current key
            return keys[st.session_state["current_key_index_seeking_alpha"]]
    except Exception as e:
        st.error(f"Error getting Seeking Alpha API key from session state: {e}")
    
    # Fallback to global variable if session state fails
    try:
        if GLOBAL_SEEKING_ALPHA_KEYS:
            return GLOBAL_SEEKING_ALPHA_KEYS[0]
    except:
        pass
    
    # Ultimate fallback to default key
    return DEFAULT_API_KEY

# CRITICAL FIX: Completely rewritten function to be more robust
def get_next_perplexity_api_key():
    """Get the next Perplexity API key with robust error handling"""
    try:
        # First try to use session state
        if "perplexity_api_keys" in st.session_state and st.session_state["perplexity_api_keys"]:
            keys = st.session_state["perplexity_api_keys"]
            
            # Make sure we have a valid index
            if "current_key_index_perplexity" not in st.session_state:
                st.session_state["current_key_index_perplexity"] = 0
            
            # Make sure the index is in range
            if st.session_state["current_key_index_perplexity"] >= len(keys):
                st.session_state["current_key_index_perplexity"] = 0
            
            # Check if we need to rotate to the next key
            if "stocks_processed_with_current_key_perplexity" in st.session_state:
                if st.session_state["stocks_processed_with_current_key_perplexity"] >= st.session_state["stocks_per_key_perplexity"]:
                    # Reset counter and move to next key
                    st.session_state["stocks_processed_with_current_key_perplexity"] = 0
                    st.session_state["current_key_index_perplexity"] = (st.session_state["current_key_index_perplexity"] + 1) % len(keys)
                
                # Increment counter
                st.session_state["stocks_processed_with_current_key_perplexity"] += 1
            else:
                st.session_state["stocks_processed_with_current_key_perplexity"] = 1
            
            # Return the current key
            return keys[st.session_state["current_key_index_perplexity"]]
    except Exception as e:
        st.error(f"Error getting Perplexity API key from session state: {e}")
    
    # Fallback to global variable if session state fails
    try:
        if GLOBAL_PERPLEXITY_KEYS:
            return GLOBAL_PERPLEXITY_KEYS[0]
    except:
        pass
    
    # Ultimate fallback to default key
    return DEFAULT_API_KEY

# CRITICAL FIX: Add a function to test API keys before using them
def test_api_key(api_key, api_host):
    """Test if an API key is valid by making a simple request"""
    try:
        conn = http.client.HTTPSConnection(api_host)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host
        }
        
        if api_host == API_HOST_SEEKING_ALPHA:
            # Use a simple endpoint for Seeking Alpha
            conn.request("GET", "/news/v2/list-by-symbol?size=1&number=1&id=AAPL", headers=headers)
        else:
            # For Perplexity, we'll just make a simple query
            headers['Content-Type'] = "application/json"
            payload = json.dumps({"content": "Hello"})
            conn.request("POST", "/", payload, headers)
            
        res = conn.getresponse()
        return res.status < 400  # Return True if status code is less than 400 (success)
    except:
        return False

# CHANGE: Updated fetch articles function to use Seeking Alpha API keys
def fetch_articles_for_symbol(worker_id: int, symbol: str, since_timestamp: int, until_timestamp: int, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    try:
        # Get the next Seeking Alpha API key
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
                time.sleep(0.5)  # Reduced delay for Seeking Alpha API

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

# CHANGE: Updated function to fetch content summary using Perplexity API keys
def fetch_content_for_article(worker_id: int, article_id: int, symbol: str, title: str, publish_date: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    try:
        # Get the next Perplexity API key
        api_key = get_next_perplexity_api_key()
        
        # Format the date if needed
        try:
            if isinstance(publish_date, str):
                # Try to parse the date string
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
        
        # Format the query to ask about the news article using the template
        query = summary_prompt_template.replace("{title}", title).replace("{date}", str(formatted_date))
        
        # Payload with just the content parameter
        payload = json.dumps({
            "content": query
        })
        
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data_bytes = res.read()
        
        if not data_bytes:
            error_msg = f"Empty response for article '{title}'"
            status_queue.put(error_msg)
            result_queue.put((article_id, symbol, f"Error: {error_msg}"))
            return
        
        # Parse the response
        try:
            data = data_bytes.decode("utf-8")
            json_data = json.loads(data)
            
            # Extract the summary from the nested JSON structure
            if "choices" in json_data and "content" in json_data["choices"] and "parts" in json_data["choices"]["content"]:
                parts = json_data["choices"]["content"]["parts"]
                if parts and len(parts) > 0 and "text" in parts[0]:
                    summary = parts[0]["text"]
                    result_queue.put((article_id, symbol, summary))
                    return
            
            # Fallback to other possible response formats
            if "answer" in json_data:
                summary = json_data["answer"]
                result_queue.put((article_id, symbol, summary))
                return
                
            # If we can't find the expected structure, return a diagnostic message
            summary = f"API response structure unexpected. Raw response (truncated): {str(json_data)[:500]}"
            result_queue.put((article_id, symbol, summary))
            
        except json.JSONDecodeError:
            # If response is not JSON, return the raw text (truncated)
            summary = f"Non-JSON response: {data[:500]}"
            result_queue.put((article_id, symbol, summary))
            
    except Exception as e:
        error_msg = f"Error fetching summary for '{title}': {e}"
        status_queue.put(error_msg)
        result_queue.put((article_id, symbol, f"Error: {str(e)}"))

# CRITICAL FIX: Add this function to debug the summary update process
def debug_summary_update(article_id, symbol, summary, df):
    """Debug function to log details about summary updates"""
    try:
        # Check if the article_id exists in the DataFrame
        if 'ID' not in df.columns:
            st.error(f"Error: 'ID' column not found in DataFrame for {symbol}")
            return False, None, article_id
        
        # Convert article_id to the same type as in the DataFrame
        df_id_type = type(df['ID'].iloc[0]) if not df.empty else "unknown"
        article_id_converted = article_id
        
        # If DataFrame ID is numeric but article_id is string, convert
        if df_id_type == int and isinstance(article_id, str):
            try:
                article_id_converted = int(article_id)
            except ValueError:
                pass
        # If DataFrame ID is string but article_id is numeric, convert
        elif df_id_type == str and isinstance(article_id, (int, float)):
            article_id_converted = str(article_id)
        
        # Find the index
        idx = df.index[df['ID'] == article_id_converted].tolist()
        
        if not idx:
            # Try alternative matching if direct match fails
            # Sometimes IDs might have different formats (e.g., with/without leading zeros)
            if isinstance(article_id, str) and article_id.isdigit():
                idx = df.index[df['ID'] == int(article_id)].tolist()
            elif isinstance(article_id, (int, float)):
                idx = df.index[df['ID'] == str(article_id)].tolist()
        
        if idx:
            return True, idx[0], article_id_converted
        else:
            # Log the failure for debugging
            st.error(f"Error: Could not find article ID {article_id} in DataFrame for {symbol}")
            st.write(f"DataFrame ID column type: {df_id_type}")
            st.write(f"Article ID type: {type(article_id)}")
            st.write(f"First few IDs in DataFrame: {df['ID'].head().tolist()}")
            return False, None, article_id_converted
    except Exception as e:
        st.error(f"Error in debug_summary_update: {e}")
        return False, None, article_id

# NEW: Add function to save DataFrame checkpoints
def save_dataframe_checkpoint(symbol, df, file_path, processed_count, total_count, checkpoint_frequency=10):
    """Save DataFrame to disk at regular checkpoints"""
    try:
        # Save at regular intervals or at specific milestones
        should_save = (
            processed_count % checkpoint_frequency == 0 or 
            processed_count == total_count or
            processed_count / total_count in [0.25, 0.5, 0.75]
        )
        
        if should_save:
            with file_lock:  # Use lock to prevent concurrent file access
                # Make sure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save the DataFrame
                df.to_csv(file_path, index=False)
                
                # Verify the file was written correctly
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    log_msg = f"Checkpoint: Saved {len(df)} rows to {file_path} ({file_size} bytes)"
                    print(log_msg)  # Print to console
                    return True
                else:
                    log_msg = f"Error: File {file_path} was not created during checkpoint"
                    print(log_msg)  # Print to console
                    return False
    except Exception as e:
        log_msg = f"Error saving DataFrame checkpoint for {symbol}: {e}"
        print(log_msg)  # Print to console
        return False
    
    return True  # No need to save at this point

# NEW: Add function to save processing progress
def save_processing_progress(symbol, processed_articles, total_articles):
    """Save processing progress to a file"""
    try:
        progress_file = os.path.join(dirs["progress"], f"{symbol}_progress.json")
        with file_lock:  # Use lock to prevent concurrent file access
            with open(progress_file, "w") as f:
                json.dump({
                    "symbol": symbol,
                    "processed_articles": processed_articles,
                    "total_articles": total_articles,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f)
        return True
    except Exception as e:
        print(f"Error saving progress for {symbol}: {e}")
        return False

# NEW: Add function to load processing progress
def load_processing_progress(symbol):
    """Load processing progress from a file"""
    try:
        progress_file = os.path.join(dirs["progress"], f"{symbol}_progress.json")
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading progress for {symbol}: {e}")
        return None

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2025, 4, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2025, 4, 30))

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Function to divide a list into approximately equal chunks
def divide_into_chunks(items, num_chunks):
    """Divide a list into approximately equal chunks"""
    if not items:
        return []
    
    avg = len(items) / float(num_chunks)
    result = []
    last = 0.0
    
    while last < len(items):
        result.append(items[int(last):int(last + avg)])
        last += avg
        
    return result

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        # CRITICAL FIX: Test API keys before proceeding
        valid_keys = []
        for key in st.session_state["seeking_alpha_api_keys"]:
            if test_api_key(key, API_HOST_SEEKING_ALPHA):
                valid_keys.append(key)
        
        if not valid_keys:
            st.error("No valid Seeking Alpha API keys found! Please enter at least one valid key.")
        else:
            # Update the keys with only valid ones
            st.session_state["seeking_alpha_api_keys"] = valid_keys
            # Update global fallback
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
                st.info("Creating a sample symbol file with default symbols.")
                os.makedirs(os.path.dirname(SYMBOL_FILE), exist_ok=True)
                with open(SYMBOL_FILE, "w") as f:
                    f.write("AAPL\nMSFT\nGOOG")
                symbols = ["AAPL", "MSFT", "GOOG"]
            
            # Determine number of workers (limited by MAX_WORKERS and available keys)
            num_workers = min(max_workers, len(valid_keys))
            st.write(f"Using {num_workers} parallel workers for fetching articles")
            
            # Create queues for thread communication
            status_queue = Queue()
            result_queue = Queue()
            error_queue = Queue()  # New queue for error reporting
            
            # Divide symbols among workers
            symbol_batches = divide_into_chunks(symbols, num_workers)
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_area = st.empty()
            
            # Use ThreadPoolExecutor for proper parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit tasks to the executor
                futures = []
                for i in range(min(num_workers, len(symbol_batches))):
                    if i < len(symbol_batches) and symbol_batches[i]:  # Check if this batch has symbols
                        for symbol in symbol_batches[i]:
                            future = executor.submit(
                                fetch_articles_for_symbol,
                                i+1, symbol, since_timestamp, until_timestamp,
                                status_queue, result_queue, error_queue
                            )
                            futures.append((future, symbol))
                
                # Process results as they come in
                results = {}
                processed_count = 0
                total_count = len(symbols)
                
                # Monitor status queue and update UI
                while processed_count < total_count:
                    # Update status messages
                    status_messages = []
                    while not status_queue.empty():
                        status = status_queue.get()
                        st.session_state["process_status"].append(status)
                        status_messages.append(status)
                    
                    if status_messages:
                        status_area.text("\n".join(status_messages[-5:]))  # Show last 5 messages
                    
                    # Process results
                    while not result_queue.empty():
                        symbol, articles = result_queue.get()
                        processed_count += 1
                        
                        if articles:
                            results[symbol] = articles
                            # Mark as processed
                            st.session_state["processed_symbols_seeking_alpha"].add(symbol)
                        
                        # Update progress
                        progress_bar.progress(processed_count / total_count)
                    
                    # Process errors
                    while not error_queue.empty():
                        symbol, timestamp, reason = error_queue.get()
                        st.session_state["failed_symbols"][symbol] = {
                            "timestamp": timestamp,
                            "reason": reason
                        }
                    
                    # Check if any futures are done
                    for future, symbol in list(futures):
                        if future.done():
                            futures.remove((future, symbol))
                            try:
                                # This will raise an exception if the future raised one
                                future.result()
                            except Exception as e:
                                st.error(f"Error in worker thread for {symbol}: {e}")
                                # Make sure we count this as processed
                                if symbol not in results:
                                    processed_count += 1
                    
                    # If all futures are done but we haven't processed all symbols, something went wrong
                    if not futures and processed_count < total_count:
                        st.error(f"All workers finished but only processed {processed_count}/{total_count} symbols")
                        break
                    
                    time.sleep(0.1)  # Prevent busy waiting
            
            # Save results to files
            for symbol, articles in results.items():
                try:
                    # Ensure the articles directory exists
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
                                'Summary': ""  # Empty summary column to be filled later
                            })
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": len(articles)
                    })
                    st.session_state["process_status"].append(f"Saved {len(articles)} articles for {symbol}")
                    
                    # Remove from failed symbols if it was there
                    if symbol in st.session_state["failed_symbols"]:
                        del st.session_state["failed_symbols"][symbol]
                except Exception as e:
                    st.error(f"Error saving articles for {symbol}: {e}")
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": f"Error: {e}"
                    })
            
            # Save failed symbols
            save_failed_symbols()
            
            st.session_state["articles_fetched"] = True
            st.success("Articles fetched successfully! You can now fetch content summaries.")

with col2:
    # UPDATED: Completely rewritten fetch content button handler
    if st.button("Fetch Content", disabled=not st.session_state["articles_fetched"]):
        # CRITICAL FIX: Test API keys before proceeding
        valid_keys = []
        for key in st.session_state["perplexity_api_keys"]:
            if test_api_key(key, API_HOST_PERPLEXITY):
                valid_keys.append(key)
        
        if not valid_keys:
            st.error("No valid Perplexity API keys found! Please enter at least one valid key.")
        else:
            # Update the keys with only valid ones
            st.session_state["perplexity_api_keys"] = valid_keys
            # Update global fallback
            update_global_perplexity_keys(valid_keys)
            
            st.session_state["process_status"].append("Starting to fetch content summaries...")
            st.session_state["processed_symbols_perplexity"] = set()
            
            try:
                # Ensure the articles directory exists
                os.makedirs(dirs["articles"], exist_ok=True)
                
                csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
                
                # Determine number of workers (limited by MAX_WORKERS and available keys)
                num_workers = min(max_workers, len(valid_keys))
                st.write(f"Using {num_workers} parallel workers for fetching content")
                
                # Create queues for thread communication
                status_queue = Queue()
                result_queue = Queue()
                error_queue = Queue()  # New queue for error reporting
                
                # Collect all articles that need summaries
                all_articles = []
                symbol_to_file = {}
                
                for csv_file in csv_files:
                    symbol = csv_file.replace("_news_data.csv", "")
                    file_path = os.path.join(dirs["articles"], csv_file)
                    symbol_to_file[symbol] = file_path
                    
                    df = pd.read_csv(file_path)
                    
                    for _, row in df.iterrows():
                        # Only process articles without summaries or with error summaries
                        if pd.isna(row['Summary']) or row['Summary'].startswith("Error:"):
                            article_id = row['ID']
                            title = row['Title']
                            publish_date = row['Publish Date']
                            all_articles.append((article_id, symbol, title, publish_date))
                
                # Create progress indicators
                progress_bar = st.progress(0)
                status_area = st.empty()
                eta_display = st.empty()
                
                # Divide articles among workers
                article_batches = divide_into_chunks(all_articles, num_workers)
                
                # Load all DataFrames
                dataframes = {}
                for symbol, file_path in symbol_to_file.items():
                    dataframes[symbol] = pd.read_csv(file_path)
                
                # Use ThreadPoolExecutor for proper parallel execution
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                    # Submit tasks to the executor
                    futures = []
                    for i in range(min(num_workers, len(article_batches))):
                        if i < len(article_batches) and article_batches[i]:  # Check if this batch has articles
                            for article_id, symbol, title, publish_date in article_batches[i]:
                                future = executor.submit(
                                    fetch_content_for_article,
                                    i+1, article_id, symbol, title, publish_date,
                                    status_queue, result_queue, error_queue
                                )
                                futures.append((future, article_id, symbol))
                                # Add a small delay to prevent overwhelming the API
                                time.sleep(0.1)
                    
                    # Process results as they come in
                    processed_count = 0
                    total_count = len(all_articles)
                    start_time = time.time()
                    
                    # NEW: Create a dictionary to track summaries by symbol
                    summaries_by_symbol = {}
                    for symbol in symbol_to_file.keys():
                        summaries_by_symbol[symbol] = 0
                    
                    # Monitor status queue and update UI
                    while processed_count < total_count:
                        # Update status messages
                        status_messages = []
                        while not status_queue.empty():
                            status = status_queue.get()
                            st.session_state["process_status"].append(status)
                            status_messages.append(status)
                        
                        if status_messages:
                            status_area.text("\n".join(status_messages[-5:]))  # Show last 5 messages
                        
                        # Process results
                        while not result_queue.empty():
                            article_id, symbol, summary = result_queue.get()
                            processed_count += 1
                            
                            # Update the DataFrame with the summary
                            if symbol in dataframes:
                                df = dataframes[symbol]
                                
                                # Use the debug function to find the correct index
                                success, idx, article_id_converted = debug_summary_update(article_id, symbol, summary, df)
                                
                                if success:
                                    # Update the summary in the DataFrame
                                    df.at[idx, 'Summary'] = summary
                                    # Ensure the update is immediately written to the dataframe
                                    dataframes[symbol] = df
                                    
                                    # Increment the summary count for this symbol
                                    summaries_by_symbol[symbol] += 1
                                    
                                    # NEW: Save checkpoint periodically
                                    file_path = symbol_to_file[symbol]
                                    save_dataframe_checkpoint(
                                        symbol, df, file_path, 
                                        processed_count, total_count, 
                                        checkpoint_frequency
                                    )
                                    
                                    # NEW: Save progress information
                                    save_processing_progress(
                                        symbol, 
                                        summaries_by_symbol[symbol], 
                                        len(df)
                                    )
                                    
                                    # Log success
                                    st.session_state["process_status"].append(f"Updated summary for article {article_id_converted} in {symbol}")
                                else:
                                    # Log failure
                                    st.session_state["process_status"].append(f"Failed to update summary for article {article_id} in {symbol}")
                            else:
                                st.error(f"Symbol {symbol} not found in dataframes dictionary")
                            
                            # Update progress
                            progress_bar.progress(processed_count / total_count)
                            
                            # Calculate and display ETA
                            if processed_count > 0:
                                elapsed_time = time.time() - start_time
                                articles_per_second = processed_count / elapsed_time
                                remaining_articles = total_count - processed_count
                                eta_seconds = remaining_articles / articles_per_second if articles_per_second > 0 else 0
                                
                                # Format ETA nicely
                                if eta_seconds < 60:
                                    eta_text = f"{eta_seconds:.0f} seconds"
                                elif eta_seconds < 3600:
                                    eta_text = f"{eta_seconds/60:.1f} minutes"
                                else:
                                    eta_text = f"{eta_seconds/3600:.1f} hours"
                                
                                eta_display.text(f"Progress: {processed_count}/{total_count} articles | ETA: {eta_text}")
                        
                        # Process errors
                        while not error_queue.empty():
                            symbol, timestamp, reason = error_queue.get()
                            st.session_state["failed_symbols"][symbol] = {
                                "timestamp": timestamp,
                                "reason": reason
                            }
                        
                        # Check if any futures are done
                        for future, article_id, symbol in list(futures):
                            if future.done():
                                futures.remove((future, article_id, symbol))
                                try:
                                    # This will raise an exception if the future raised one
                                    future.result()
                                except Exception as e:
                                    st.error(f"Error in worker thread for article {article_id}: {e}")
                                    # Make sure we count this as processed
                                    processed_count += 1
                        
                        # If all futures are done but we haven't processed all articles, something went wrong
                        if not futures and processed_count < total_count:
                            st.error(f"All workers finished but only processed {processed_count}/{total_count} articles")
                            break
                        
                        time.sleep(0.1)  # Prevent busy waiting
                
                # Save all updated DataFrames back to CSV files with retry mechanism
                for symbol, df in dataframes.items():
                    try:
                        file_path = symbol_to_file[symbol]
                        
                        # Check if the DataFrame has a Summary column
                        if 'Summary' not in df.columns:
                            st.error(f"Error: 'Summary' column not found in DataFrame for {symbol}")
                            # Add the Summary column if it doesn't exist
                            df['Summary'] = ""
                        
                        # Check if any summaries were added
                        summary_count = df['Summary'].notna().sum()
                        empty_summary_count = (df['Summary'] == "").sum()
                        
                        # Log summary statistics
                        st.session_state["process_status"].append(
                            f"Symbol {symbol}: {summary_count} summaries, {empty_summary_count} empty summaries"
                        )
                        
                        # Save the DataFrame to CSV with retry mechanism
                        max_retries = 3
                        success = False
                        
                        for retry in range(max_retries):
                            try:
                                with file_lock:  # Use lock to prevent concurrent file access
                                    df.to_csv(file_path, index=False)
                                
                                # Verify the file was written correctly
                                if os.path.exists(file_path):
                                    file_size = os.path.getsize(file_path)
                                    st.session_state["process_status"].append(
                                        f"Saved {len(df)} rows to {file_path} ({file_size} bytes)"
                                    )
                                    success = True
                                    break
                                else:
                                    st.error(f"Error: File {file_path} was not created")
                            except Exception as e:
                                st.error(f"Error saving DataFrame for {symbol} (attempt {retry+1}/{max_retries}): {e}")
                                time.sleep(1)  # Wait before retrying
                        
                        if success:
                            # Mark symbol as processed
                            st.session_state["processed_symbols_perplexity"].add(symbol)
                        else:
                            st.error(f"Failed to save DataFrame for {symbol} after {max_retries} attempts")
                    except Exception as e:
                        st.error(f"Error saving DataFrame for {symbol}: {e}")

                elapsed_time = time.time() - start_time
                st.session_state["content_fetched"] = True
                st.success(f"Content summaries fetched successfully! Added {total_count} summaries in {elapsed_time:.1f} seconds.")
                
                # NEW: Automatically verify summaries
                st.write("Verifying summaries...")
                verify_summaries()
            except Exception as e:
                st.error(f"Error fetching content: {e}")

with col3:
    if st.button("Clean Up"):
        st.session_state["process_status"] = []
        st.session_state["process_status"].append("Starting cleanup...")
        
        try:
            # Ensure the articles directory exists
            if os.path.exists(dirs["articles"]):
                # Count files before deletion
                csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
                file_count = len(csv_files)
                
                # Delete all files in the articles directory
                for file in csv_files:
                    file_path = os.path.join(dirs["articles"], file)
                    try:
                        os.remove(file_path)
                        st.session_state["process_status"].append(f"Deleted: {file}")
                    except Exception as e:
                        st.session_state["process_status"].append(f"Error deleting {file}: {e}")
                
                # Also clean up progress files
                if os.path.exists(dirs["progress"]):
                    progress_files = [f for f in os.listdir(dirs["progress"]) if f.endswith("_progress.json")]
                    for file in progress_files:
                        file_path = os.path.join(dirs["progress"], file)
                        try:
                            os.remove(file_path)
                            st.session_state["process_status"].append(f"Deleted progress file: {file}")
                        except Exception as e:
                            st.session_state["process_status"].append(f"Error deleting progress file {file}: {e}")
                
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
        
        # Create a DataFrame for better display
        failed_data = []
        for symbol, details in st.session_state["failed_symbols"].items():
            failed_data.append({
                "Symbol": symbol,
                "Timestamp": details["timestamp"],
                "Reason": details["reason"]
            })
        
        failed_df = pd.DataFrame(failed_data)
        st.dataframe(failed_df)
        
        # Option to clear failed symbols
        if st.button("Clear Failed Symbols List"):
            st.session_state["failed_symbols"] = {}
            save_failed_symbols()
            st.success("Failed symbols list cleared.")

# CHANGE: Updated API key usage display to show separate key lists
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
        # Ensure the articles directory exists
        if os.path.exists(dirs["articles"]):
            csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
            
            # Create tabs for each symbol
            if csv_files:
                tabs = st.tabs([f.replace("_news_data.csv", "").upper() for f in csv_files])
                
                for i, tab in enumerate(tabs):
                    with tab:
                        file_path = os.path.join(dirs["articles"], csv_files[i])
                        df = pd.read_csv(file_path)
                        
                        # Display a preview of the summaries
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
        # Calculate storage usage
        total_size = 0
        file_count = 0
        
        if os.path.exists(st.session_state["output_dir"]):
            for root, dirs, files in os.walk(st.session_state["output_dir"]):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            # Format size nicely
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
        
        # Show directory structure
        st.write("### Directory Structure:")
        if isinstance(dirs, dict):  # Check if dirs is a dictionary
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

# CRITICAL FIX: Add a debug section to help diagnose issues
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
            is_valid = test_api_key(key, API_HOST_PERPLEXITY)  [])):
            is_valid = test_api_key(key, API_HOST_PERPLEXITY)
            st.write(f"Key {i+1}: {'Valid' if is_valid else 'Invalid'}")

# Function to verify summaries were saved
def verify_summaries():
    """Verify that summaries were properly saved to CSV files"""
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
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Check if Summary column exists
                if 'Summary' not in df.columns:
                    st.error(f"Error: 'Summary' column not found in {csv_file}")
                    continue
                
                # Count summaries
                total_rows = len(df)
                non_empty_summaries = df['Summary'].notna().sum()
                empty_summaries = total_rows - non_empty_summaries
                
                st.write(f"**{symbol.upper()}**: {non_empty_summaries}/{total_rows} summaries ({empty_summaries} empty)")
                
                # Display a sample of summaries
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

# Add a button to verify summaries
if st.session_state["content_fetched"]:
    if st.button("Verify Summaries"):
        verify_summaries()
