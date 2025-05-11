import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
import time
import threading
import concurrent.futures
from queue import Queue
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set

# Custom CSS
st.markdown(
    """
    <style>
    .stButton > button:hover {
        background-color: #000000;
        color: white;
    }
    .stButton > button {
        background-color: #282828;
        color: white;
    }
    .stButton > button:active {
        background-color: #282828;
        color: white;
    }    
    </style>
    """,
    unsafe_allow_html=True
)

# Configuration
API_HOST = "twitter154.p.rapidapi.com"
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
KEYWORDS_FILE = "data/keywords.txt"
JSON_OUTPUT_DIR = "/tmp/data/output"
CSV_OUTPUT_DIR = "/tmp/data/csv_output"
MAX_WORKERS = 4  # Maximum number of parallel workers

# Ensure output directories exist
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "process_status" not in st.session_state:
    st.session_state["process_status"] = []
if "combined_keywords" not in st.session_state:
    st.session_state["combined_keywords"] = {}
if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = None
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY
if "failed_keywords" not in st.session_state:
    st.session_state["failed_keywords"] = {}  # Dictionary to store failed keywords and reasons
if "processed_keywords" not in st.session_state:
    st.session_state["processed_keywords"] = set()

# API key rotation state
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []
if "current_key_index" not in st.session_state:
    st.session_state["current_key_index"] = 0
if "keywords_processed_with_current_key" not in st.session_state:
    st.session_state["keywords_processed_with_current_key"] = 0
if "keywords_per_key" not in st.session_state:
    st.session_state["keywords_per_key"] = 10  # Default limit

# Thread-safe locks for shared resources
status_lock = threading.Lock()

def generate_combined_keywords(base_keywords):
    """Generate default combined keywords for each base keyword with + instead of spaces"""
    combined = {}
    for keyword in base_keywords:
        combined[keyword] = [
            f"{keyword}+Portfolio",
            f"{keyword}+Stock",
            f"{keyword}+Earnings",
            f"{keyword}+Analysis"
        ]
    return combined

def format_keyword_for_api(keyword):
    """Replace spaces with + for API queries while preserving original for display"""
    return keyword.replace(" ", "+")

def get_current_api_key():
    """Get the current API key from the rotation"""
    if not st.session_state["api_keys"]:
        return DEFAULT_API_KEY
    return st.session_state["api_keys"][st.session_state["current_key_index"]]

def rotate_to_next_api_key():
    """Rotate to the next API key and reset the counter"""
    st.session_state["keywords_processed_with_current_key"] = 0
    if len(st.session_state["api_keys"]) > 1:
        st.session_state["current_key_index"] = (st.session_state["current_key_index"] + 1) % len(st.session_state["api_keys"])
        with status_lock:
            st.session_state["process_status"].append(f"Switched to API key {st.session_state['current_key_index'] + 1} of {len(st.session_state['api_keys'])}")
    return get_current_api_key()

def save_failed_keywords():
    """Save failed keywords to a file"""
    try:
        os.makedirs(os.path.join(JSON_OUTPUT_DIR, "logs"), exist_ok=True)
        failed_file = os.path.join(JSON_OUTPUT_DIR, "logs", "failed_keywords.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for keyword, details in st.session_state["failed_keywords"].items():
                f.write(f"{keyword},{details['timestamp']},{details['reason']}\n")
        return failed_file
    except Exception as e:
        st.error(f"Error saving failed keywords: {e}")
        return None

def load_failed_keywords():
    """Load failed keywords from a file"""
    try:
        failed_file = os.path.join(JSON_OUTPUT_DIR, "logs", "failed_keywords.txt")
        if os.path.exists(failed_file):
            with open(failed_file, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",", 2)
                    if len(parts) >= 3:
                        keyword, timestamp, reason = parts
                        st.session_state["failed_keywords"][keyword] = {
                            "timestamp": timestamp,
                            "reason": reason
                        }
    except Exception as e:
        st.error(f"Error loading failed keywords: {e}")

# Load failed keywords on startup
try:
    load_failed_keywords()
except Exception as e:
    st.error(f"Error during startup: {e}")

def fetch_tweets_for_keyword_worker(worker_id: int, keyword: str, start_date, end_date, api_key: str, 
                                   status_queue: Queue, result_queue: Queue, error_queue: Queue):
    """Worker function to fetch tweets for a specific keyword"""
    try:
        display_keyword = keyword.replace("+", " ")
        status_queue.put(f"Worker {worker_id}: Fetching tweets for: {display_keyword}")
        
        conn = http.client.HTTPSConnection(API_HOST)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST
        }
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        api_query = format_keyword_for_api(keyword)
        endpoint = f"/search/search?query={api_query}&section=latest&min_retweets=1&min_likes=1&limit=50&start_date={start_date_str}&language=en&end_date={end_date_str}"
        
        try:
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data_bytes = res.read()
            
            if not data_bytes:
                error_msg = f"Empty response for {display_keyword}"
                status_queue.put(error_msg)
                error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                result_queue.put((keyword, None))
                return
            
            try:
                data = json.loads(data_bytes.decode("utf-8"))
                status_queue.put(f"Worker {worker_id}: Found {len(data.get('results', []))} tweets for {display_keyword}")
                result_queue.put((keyword, data))
            except json.JSONDecodeError as e:
                error_msg = f"Error parsing JSON for {display_keyword}: {e}"
                status_queue.put(error_msg)
                error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                result_queue.put((keyword, None))
        except Exception as e:
            error_msg = f"API request failed for {display_keyword}: {e}"
            status_queue.put(error_msg)
            error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            result_queue.put((keyword, None))
        finally:
            conn.close()
            
    except Exception as e:
        error_msg = f"Fatal error fetching tweets for {keyword.replace('+', ' ')}: {e}"
        status_queue.put(error_msg)
        error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((keyword, None))

def fetch_tweets_parallel(start_date, end_date, keywords_to_fetch, max_workers=MAX_WORKERS):
    """Fetch tweets for specified keywords using parallel workers"""
    if not keywords_to_fetch:
        st.warning("No keywords selected to fetch")
        return
    
    if not st.session_state["api_keys"] and not st.session_state["api_key"].strip():
        st.error("API key is missing!")
        return
    
    # If no API keys in rotation but we have a single key, add it
    if not st.session_state["api_keys"] and st.session_state["api_key"].strip():
        st.session_state["api_keys"] = [st.session_state["api_key"]]
    
    # Determine number of workers (limited by MAX_WORKERS and available keys)
    num_workers = min(max_workers, len(st.session_state["api_keys"]))
    st.write(f"Using {num_workers} parallel workers for fetching tweets")
    
    # Create queues for thread communication
    status_queue = Queue()
    result_queue = Queue()
    error_queue = Queue()
    
    # Divide keywords among workers
    keyword_batches = divide_into_chunks(keywords_to_fetch, num_workers)
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_area = st.empty()
    eta_display = st.empty()
    
    # Use ThreadPoolExecutor for proper parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit tasks to the executor
        futures = []
        for i in range(min(num_workers, len(keyword_batches))):
            if i < len(keyword_batches) and keyword_batches[i]:  # Check if this batch has keywords
                api_key = st.session_state["api_keys"][i % len(st.session_state["api_keys"])]
                for keyword in keyword_batches[i]:
                    future = executor.submit(
                        fetch_tweets_for_keyword_worker,
                        i+1, keyword, start_date, end_date, api_key,
                        status_queue, result_queue, error_queue
                    )
                    futures.append((future, keyword))
                    # Add a small delay to prevent overwhelming the API
                    time.sleep(0.1)
        
        # Process results as they come in
        results = {}
        processed_count = 0
        total_count = len(keywords_to_fetch)
        start_time = time.time()
        
        # Monitor status queue and update UI
        while processed_count < total_count:
            # Update status messages
            status_messages = []
            while not status_queue.empty():
                status = status_queue.get()
                with status_lock:
                    st.session_state["process_status"].append(status)
                status_messages.append(status)
            
            if status_messages:
                status_area.text("\n".join(status_messages[-5:]))  # Show last 5 messages
            
            # Process results
            while not result_queue.empty():
                keyword, data = result_queue.get()
                processed_count += 1
                
                if data:
                    results[keyword] = data
                    # Mark as processed
                    st.session_state["processed_keywords"].add(keyword)
                
                # Update progress
                progress_bar.progress(processed_count / total_count)
                
                # Calculate and display ETA
                if processed_count > 0:
                    elapsed_time = time.time() - start_time
                    keywords_per_second = processed_count / elapsed_time
                    remaining_keywords = total_count - processed_count
                    eta_seconds = remaining_keywords / keywords_per_second if keywords_per_second > 0 else 0
                    
                    # Format ETA nicely
                    if eta_seconds < 60:
                        eta_text = f"{eta_seconds:.0f} seconds"
                    elif eta_seconds < 3600:
                        eta_text = f"{eta_seconds/60:.1f} minutes"
                    else:
                        eta_text = f"{eta_seconds/3600:.1f} hours"
                    
                    eta_display.text(f"Progress: {processed_count}/{total_count} keywords | ETA: {eta_text}")
            
            # Process errors
            while not error_queue.empty():
                keyword, timestamp, reason = error_queue.get()
                st.session_state["failed_keywords"][keyword] = {
                    "timestamp": timestamp,
                    "reason": reason
                }
            
            # Check if any futures are done
            for future, keyword in list(futures):
                if future.done():
                    futures.remove((future, keyword))
                    try:
                        # This will raise an exception if the future raised one
                        future.result()
                    except Exception as e:
                        st.error(f"Error in worker thread for {keyword}: {e}")
                        # Make sure we count this as processed
                        if keyword not in results:
                            processed_count += 1
            
            # If all futures are done but we haven't processed all keywords, something went wrong
            if not futures and processed_count < total_count:
                st.error(f"All workers finished but only processed {processed_count}/{total_count} keywords")
                break
            
            time.sleep(0.1)  # Prevent busy waiting
    
    # Save results to files
    for keyword, data in results.items():
        try:
            sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
            output_file = os.path.join(JSON_OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                json.dump(data, outfile)
            
            display_keyword = keyword.replace("+", " ")
            keyword_type = "Combined" if any(keyword in combos for combos in st.session_state["combined_keywords"].values()) else "Base"
            
            st.session_state["status_table"].append({
                "Keyword": display_keyword,
                "Type": keyword_type,
                "Tweet Extract JSON": "✅",
                "CSV Output": "❌",
                "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            })
            
            # Remove from failed keywords if it was there
            if keyword in st.session_state["failed_keywords"]:
                del st.session_state["failed_keywords"][keyword]
        except Exception as e:
            st.error(f"Error saving tweets for {keyword.replace('+', ' ')}: {e}")
    
    # Save failed keywords
    save_failed_keywords()
    
    eta_display.empty()
    status_area.empty()
    
    return results

def convert_json_to_csv_worker(worker_id: int, json_file: str, status_queue: Queue, result_queue: Queue, error_queue: Queue):
    """Worker function to convert a JSON file to CSV"""
    try:
        status_queue.put(f"Worker {worker_id}: Converting {json_file} to CSV...")
        
        json_file_path = os.path.join(JSON_OUTPUT_DIR, json_file)
        csv_file_name = f"{os.path.splitext(json_file)[0]}.csv"
        csv_file_path = os.path.join(CSV_OUTPUT_DIR, csv_file_name)
        
        with open(json_file_path, "r") as file:
            data = json.load(file)
        
        records = []
        for item in data.get("results", []):
            flat_item = {
                "tweet_id": item.get("tweet_id"),
                "creation_date": item.get("creation_date"),
                "text": item.get("text"),
                "language": item.get("language"),
                "favorite_count": item.get("favorite_count"),
                "retweet_count": item.get("retweet_count"),
                "reply_count": item.get("reply_count"),
                "views": item.get("views"),
            }
            user_info = item.get("user", {})
            for key, value in user_info.items():
                flat_item[f"user_{key}"] = value
            records.append(flat_item)
        
        df = pd.DataFrame(records)
        df.to_csv(csv_file_path, index=False)
        
        keyword = json_file.replace(".json", "").replace("_", " ")
        result_queue.put((json_file, keyword, True))
        
    except Exception as e:
        error_msg = f"Error converting {json_file} to CSV: {e}"
        status_queue.put(error_msg)
        error_queue.put((json_file, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((json_file, None, False))

def convert_json_to_csv_parallel(max_workers=MAX_WORKERS):
    """Convert all JSON files to CSV using parallel workers"""
    if not os.path.exists(JSON_OUTPUT_DIR):
        st.warning("No JSON files found. Please fetch tweets first.")
        return
    
    json_files = [f for f in os.listdir(JSON_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No JSON files found in the output directory.")
        return
    
    # Determine number of workers
    num_workers = min(max_workers, len(json_files))
    st.write(f"Using {num_workers} parallel workers for converting JSON to CSV")
    
    # Create queues for thread communication
    status_queue = Queue()
    result_queue = Queue()
    error_queue = Queue()
    
    # Divide files among workers
    file_batches = divide_into_chunks(json_files, num_workers)
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_area = st.empty()
    
    # Use ThreadPoolExecutor for proper parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit tasks to the executor
        futures = []
        for i in range(min(num_workers, len(file_batches))):
            if i < len(file_batches) and file_batches[i]:  # Check if this batch has files
                for json_file in file_batches[i]:
                    future = executor.submit(
                        convert_json_to_csv_worker,
                        i+1, json_file, status_queue, result_queue, error_queue
                    )
                    futures.append((future, json_file))
        
        # Process results as they come in
        processed_count = 0
        total_count = len(json_files)
        
        # Monitor status queue and update UI
        while processed_count < total_count:
            # Update status messages
            status_messages = []
            while not status_queue.empty():
                status = status_queue.get()
                with status_lock:
                    st.session_state["process_status"].append(status)
                status_messages.append(status)
            
            if status_messages:
                status_area.text("\n".join(status_messages[-5:]))  # Show last 5 messages
            
            # Process results
            while not result_queue.empty():
                json_file, keyword, success = result_queue.get()
                processed_count += 1
                
                if success and keyword:
                    # Update status table
                    for entry in st.session_state["status_table"]:
                        if entry["Keyword"] == keyword:
                            entry["CSV Output"] = "✅"
                            break
                
                # Update progress
                progress_bar.progress(processed_count / total_count)
            
            # Process errors
            while not error_queue.empty():
                json_file, timestamp, reason = error_queue.get()
                st.error(f"Error converting {json_file}: {reason}")
            
            # Check if any futures are done
            for future, json_file in list(futures):
                if future.done():
                    futures.remove((future, json_file))
                    try:
                        # This will raise an exception if the future raised one
                        future.result()
                    except Exception as e:
                        st.error(f"Error in worker thread for {json_file}: {e}")
                        # Make sure we count this as processed
                        processed_count += 1
            
            # If all futures are done but we haven't processed all files, something went wrong
            if not futures and processed_count < total_count:
                st.error(f"All workers finished but only processed {processed_count}/{total_count} files")
                break
            
            time.sleep(0.1)  # Prevent busy waiting
    
    status_area.empty()

def combine_company_csvs(company_name):
    """Merge all CSV files for a company's combined keywords into one DataFrame"""
    if not os.path.exists(CSV_OUTPUT_DIR):
        return None
    
    company_prefix = company_name.replace(" ", "_")
    csv_files = [
        f for f in os.listdir(CSV_OUTPUT_DIR) 
        if f.startswith(company_prefix) and f.endswith(".csv")
    ]
    
    if not csv_files:
        return None
    
    combined_df = pd.concat(
        [pd.read_csv(os.path.join(CSV_OUTPUT_DIR, f)) for f in csv_files],
        ignore_index=True
    )
    return combined_df

def clear_temp():
    """Clear temporary files"""
    try:
        if os.path.exists(JSON_OUTPUT_DIR):
            shutil.rmtree(JSON_OUTPUT_DIR)
            os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

        if os.path.exists(CSV_OUTPUT_DIR):
            shutil.rmtree(CSV_OUTPUT_DIR)
            os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        st.session_state["failed_keywords"] = {}
        st.session_state["processed_keywords"] = set()
        st.success("Temporary files cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing temporary files: {e}")

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

# Streamlit UI
st.title("Twitter Data Fetcher")

# API Key Input
api_keys_input = st.text_area(
    "Twitter API Keys (one per line)",
    help="Enter your RapidAPI keys, one per line. The app will rotate through these keys."
)

# Parse the keys
if api_keys_input:
    st.session_state["api_keys"] = [key.strip() for key in api_keys_input.split('\n') if key.strip()]
    total_capacity = len(st.session_state["api_keys"]) * st.session_state["keywords_per_key"]
    st.write(f"Found {len(st.session_state['api_keys'])} API keys.")
    st.write(f"Can process approximately {total_capacity} keywords.")
elif not st.session_state["api_keys"]:
    st.session_state["api_keys"] = [DEFAULT_API_KEY]
    st.warning("No API keys provided. Using default key which is rate-limited.")

# API rotation settings
st.session_state["keywords_per_key"] = st.number_input(
    "Keywords per key",
    min_value=1,
    value=st.session_state["keywords_per_key"],
    help="Number of keywords to process with each key before rotating"
)

# Advanced settings in expander
with st.expander("Advanced Settings"):
    max_workers = st.slider(
        "Maximum Parallel Workers", 
        min_value=1, 
        max_value=8, 
        value=MAX_WORKERS,
        step=1,
        help="Maximum number of parallel workers. Each worker uses one API key."
    )

# Date input section
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=datetime(2025, 3, 10))

# Load base keywords
base_keywords = []
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]
else:
    # Create the directory and file if it doesn't exist
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w") as file:
        file.write("AAPL\nMSFT\nGOOG\nAMZN\nFB")
    base_keywords = ["AAPL", "MSFT", "GOOG", "AMZN", "FB"]
    st.info(f"Created sample keywords file at {KEYWORDS_FILE}")

# Initialize combined keywords if not exists
if not st.session_state["combined_keywords"] and base_keywords:
    st.session_state["combined_keywords"] = generate_combined_keywords(base_keywords)

# Company selection dropdown
if base_keywords:
    st.session_state["selected_company"] = st.selectbox(
        "Select Company to Manage Combinations",
        base_keywords,
        index=0
    )
    
    # Combined CSV download button
    combined_csv = combine_company_csvs(st.session_state["selected_company"])
    if combined_csv is not None:
        csv_data = combined_csv.to_csv(index=False)
        st.download_button(
            label=f"Download ALL {st.session_state['selected_company']} Data (Combined)",
            data=csv_data,
            file_name=f"{st.session_state['selected_company'].replace(' ', '_')}_ALL.csv",
            mime="text/csv",
            key=f"combined_{st.session_state['selected_company']}"
        )
    
    st.subheader(f"Combination Keywords for: {st.session_state['selected_company']}")
    
    if st.session_state["selected_company"] not in st.session_state["combined_keywords"]:
        st.session_state["combined_keywords"][st.session_state["selected_company"]] = generate_combined_keywords(
            [st.session_state["selected_company"]]
        )[st.session_state["selected_company"]]
    
    cols = st.columns(4)
    for i in range(4):
        with cols[i]:
            display_value = st.session_state["combined_keywords"][st.session_state["selected_company"]][i].replace("+", " ")
            new_value = st.text_input(
                f"Combination {i+1}",
                value=display_value,
                key=f"combo_{st.session_state['selected_company']}_{i}"
            )
            st.session_state["combined_keywords"][st.session_state["selected_company"]][i] = new_value.replace(" ", "+")
else:
    st.warning("No companies found in keywords.txt")

# Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Fetch Base Keywords"):
        if start_date <= end_date and base_keywords:
            fetch_tweets_parallel(start_date, end_date, base_keywords, max_workers)
        else:
            st.warning("Invalid date range or no base keywords!")

with col2:
    if st.button("Fetch All Combined Keywords"):
        if start_date <= end_date and st.session_state["combined_keywords"]:
            all_combined = []
            for combos in st.session_state["combined_keywords"].values():
                all_combined.extend(combos)
            fetch_tweets_parallel(start_date, end_date, all_combined, max_workers)
        else:
            st.warning("Invalid date range or no combined keywords!")

with col3:
    if st.button("Convert JSON to CSV"):
        convert_json_to_csv_parallel(max_workers)

with col4:
    if st.button("Clear Temp"):
        clear_temp()

# Display failed keywords
if st.session_state["failed_keywords"]:
    with st.expander("Failed Keywords", expanded=True):
        st.write(f"There are {len(st.session_state['failed_keywords'])} keywords that failed processing:")
        
        # Create a DataFrame for better display
        failed_data = []
        for keyword, details in st.session_state["failed_keywords"].items():
            failed_data.append({
                "Keyword": keyword.replace("+", " "),
                "Timestamp": details["timestamp"],
                "Reason": details["reason"]
            })
        
        failed_df = pd.DataFrame(failed_data)
        st.dataframe(failed_df)
        
        # Option to clear failed keywords
        if st.button("Clear Failed Keywords List"):
            st.session_state["failed_keywords"] = {}
            save_failed_keywords()
            st.success("Failed keywords list cleared.")

# Display API key usage
with st.expander("API Key Usage"):
    st.write(f"Current key index: {st.session_state['current_key_index'] + 1} of {len(st.session_state['api_keys'])}")
    st.write(f"Keywords processed with current key: {st.session_state['keywords_processed_with_current_key']} of {st.session_state['keywords_per_key']}")
    st.write(f"Total keywords processed: {len(st.session_state['processed_keywords'])}")

# Display process status
if st.session_state["process_status"]:
    with st.expander("Process Status", expanded=True):
        status_container = st.container()
        with status_container:
            for status in st.session_state["process_status"][-20:]:  # Show last 20 messages
                st.write(status)

# Status Table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.dataframe(status_df, hide_index=True)
else:
    st.write("No actions performed yet. Fetch tweets to see the status.")

# CSV Download Section
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download Individual CSV Files"):
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {csv_file.replace('_', ' ').replace('.csv', '')}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found")
else:
    st.warning("CSV output directory does not exist")
