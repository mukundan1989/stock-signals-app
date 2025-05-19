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
    
# CHANGE: Separate API key lists for each service
if "seeking_alpha_api_keys" not in st.session_state:
    st.session_state["seeking_alpha_api_keys"] = []
if "perplexity_api_keys" not in st.session_state:
    st.session_state["perplexity_api_keys"] = []

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

# Streamlit UI
st.title("Seeking Alpha News Fetcher")
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
        
        return {
            "main": st.session_state["output_dir"],
            "articles": articles_dir,
            "logs": logs_dir
        }
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        # Return a default dictionary to prevent errors
        return {
            "main": st.session_state["output_dir"],
            "articles": os.path.join(st.session_state["output_dir"], "articles"),
            "logs": os.path.join(st.session_state["output_dir"], "logs")
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
        "logs": os.path.join(st.session_state["output_dir"], "logs")
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

# Seeking Alpha API Keys
seeking_alpha_api_keys_input = st.text_area(
    "Seeking Alpha API Keys (one per line)",
    help="Enter your RapidAPI keys for Seeking Alpha, one per line. The app will rotate through these keys."
)

# Perplexity API Keys
perplexity_api_keys_input = st.text_area(
    "Perplexity API Keys (one per line)",
    help="Enter your RapidAPI keys for Perplexity, one per line. The app will rotate through these keys."
)

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

# CHANGE: Parse the keys for each service separately
# Parse Seeking Alpha API keys
if seeking_alpha_api_keys_input:
    st.session_state["seeking_alpha_api_keys"] = [key.strip() for key in seeking_alpha_api_keys_input.split('\n') if key.strip()]
    total_capacity_seeking_alpha = len(st.session_state["seeking_alpha_api_keys"]) * st.session_state["stocks_per_key_seeking_alpha"]
    st.write(f"Found {len(st.session_state['seeking_alpha_api_keys'])} Seeking Alpha API keys.")
    st.write(f"Can process approximately {total_capacity_seeking_alpha} stocks with Seeking Alpha API.")
elif not st.session_state["seeking_alpha_api_keys"]:
    st.session_state["seeking_alpha_api_keys"] = [DEFAULT_API_KEY]
    st.warning("No Seeking Alpha API keys provided. Using default key which is rate-limited.")

# Parse Perplexity API keys
if perplexity_api_keys_input:
    st.session_state["perplexity_api_keys"] = [key.strip() for key in perplexity_api_keys_input.split('\n') if key.strip()]
    total_capacity_perplexity = len(st.session_state["perplexity_api_keys"]) * st.session_state["stocks_per_key_perplexity"]
    st.write(f"Found {len(st.session_state['perplexity_api_keys'])} Perplexity API keys.")
    st.write(f"Can process approximately {total_capacity_perplexity} stocks with Perplexity API.")
elif not st.session_state["perplexity_api_keys"]:
    st.session_state["perplexity_api_keys"] = [DEFAULT_API_KEY]
    st.warning("No Perplexity API keys provided. Using default key which is rate-limited.")

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

# CHANGE: Updated function to get the next Seeking Alpha API key
def get_next_seeking_alpha_api_key():
    if not st.session_state["seeking_alpha_api_keys"]:
        return DEFAULT_API_KEY
    
    # Check if we need to rotate to the next key
    if st.session_state["stocks_processed_with_current_key_seeking_alpha"] >= st.session_state["stocks_per_key_seeking_alpha"]:
        # Reset counter and move to next key
        st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
        st.session_state["current_key_index_seeking_alpha"] = (st.session_state["current_key_index_seeking_alpha"] + 1) % len(st.session_state["seeking_alpha_api_keys"])
    
    # Increment counter
    st.session_state["stocks_processed_with_current_key_seeking_alpha"] += 1
    
    # Return the current key
    return st.session_state["seeking_alpha_api_keys"][st.session_state["current_key_index_seeking_alpha"]]

# CHANGE: Updated function to get the next Perplexity API key
def get_next_perplexity_api_key():
    if not st.session_state["perplexity_api_keys"]:
        return DEFAULT_API_KEY
    
    # Check if we need to rotate to the next key
    if st.session_state["stocks_processed_with_current_key_perplexity"] >= st.session_state["stocks_per_key_perplexity"]:
        # Reset counter and move to next key
        st.session_state["stocks_processed_with_current_key_perplexity"] = 0
        st.session_state["current_key_index_perplexity"] = (st.session_state["current_key_index_perplexity"] + 1) % len(st.session_state["perplexity_api_keys"])
    
    # Increment counter
    st.session_state["stocks_processed_with_current_key_perplexity"] += 1
    
    # Return the current key
    return st.session_state["perplexity_api_keys"][st.session_state["current_key_index_perplexity"]]

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

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

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
        if not st.session_state["seeking_alpha_api_keys"]:
            st.error("Please enter at least one valid Seeking Alpha API key!")
        else:
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
            num_workers = min(max_workers, len(st.session_state["seeking_alpha_api_keys"]))
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
    # New button to fetch content summaries with parallel processing
    if st.button("Fetch Content", disabled=not st.session_state["articles_fetched"]):
        if not st.session_state["perplexity_api_keys"]:
            st.error("Please enter at least one valid Perplexity API key!")
        else:
            st.session_state["process_status"].append("Starting to fetch content summaries...")
            st.session_state["processed_symbols_perplexity"] = set()
            
            try:
                # Ensure the articles directory exists
                os.makedirs(dirs["articles"], exist_ok=True)
                
                csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
                
                # Determine number of workers (limited by MAX_WORKERS and available keys)
                num_workers = min(max_workers, len(st.session_state["perplexity_api_keys"]))
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
                            df = dataframes[symbol]
                            idx = df.index[df['ID'] == article_id].tolist()
                            if idx:
                                df.at[idx[0], 'Summary'] = summary
                            
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
                
                # Save all updated DataFrames back to CSV files
                for symbol, df in dataframes.items():
                    file_path = symbol_to_file[symbol]
                    df.to_csv(file_path, index=False)
                    st.session_state["process_status"].append(f"Saved {len(df)} summaries for {symbol}")
                    # Mark symbol as processed
                    st.session_state["processed_symbols_perplexity"].add(symbol)
                
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
