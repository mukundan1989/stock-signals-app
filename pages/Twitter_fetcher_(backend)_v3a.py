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
from datetime import datetime, timedelta, date
import calendar
import platform
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

# Default paths based on OS
def get_default_output_dir():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Documents", "TwitterData")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Documents", "TwitterData")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "TwitterData")

# Get previous month's date range
def get_previous_month_range():
    today = date.today()
    
    # If we're in the first month of the year
    if today.month == 1:
        prev_month = 12
        year = today.year - 1
    else:
        prev_month = today.month - 1
        year = today.year
    
    # Get the first day of the previous month
    first_day = date(year, prev_month, 1)
    
    # Get the last day of the previous month
    _, last_day_num = calendar.monthrange(year, prev_month)
    last_day = date(year, prev_month, last_day_num)
    
    return first_day, last_day

# Configuration
API_HOST = "twitter154.p.rapidapi.com"
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
KEYWORDS_FILE = "data/keywords.txt"
MAX_WORKERS = 4  # Maximum number of parallel workers
TWEETS_PER_REQUEST = 20  # Maximum tweets per API request

# Get previous month's date range
prev_month_start, prev_month_end = get_previous_month_range()

# Initialize session state for output directories
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "directories" not in st.session_state:
    st.session_state["directories"] = {}

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
if "failed_companies" not in st.session_state:
    st.session_state["failed_companies"] = {}  # Dictionary to store failed companies and reasons
if "processed_companies" not in st.session_state:
    st.session_state["processed_companies"] = set()
if "use_date_segmentation" not in st.session_state:
    st.session_state["use_date_segmentation"] = True
if "segment_size_days" not in st.session_state:
    st.session_state["segment_size_days"] = 7  # Default to weekly segments
if "tweet_section" not in st.session_state:
    st.session_state["tweet_section"] = "latest"  # Default to latest tweets

# API key rotation state
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []
if "current_key_index" not in st.session_state:
    st.session_state["current_key_index"] = 0
if "companies_processed_with_current_key" not in st.session_state:
    st.session_state["companies_processed_with_current_key"] = 0
if "companies_per_key" not in st.session_state:
    st.session_state["companies_per_key"] = 5  # Default limit

# Thread-safe locks for shared resources
status_lock = threading.Lock()

# Streamlit UI
st.title("Twitter Data Fetcher")

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
        
        # JSON output directory (now used only temporarily)
        json_dir = os.path.join(st.session_state["output_dir"], "json_temp")
        os.makedirs(json_dir, exist_ok=True)
        
        # CSV output directory
        csv_dir = os.path.join(st.session_state["output_dir"], "csv_output")
        os.makedirs(csv_dir, exist_ok=True)
        
        # Logs directory
        logs_dir = os.path.join(st.session_state["output_dir"], "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Combined results directory
        combined_dir = os.path.join(st.session_state["output_dir"], "combined_output")
        os.makedirs(combined_dir, exist_ok=True)
        
        return {
            "main": st.session_state["output_dir"],
            "json": json_dir,
            "csv": csv_dir,
            "logs": logs_dir,
            "combined": combined_dir
        }
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        # Return a default dictionary to prevent errors
        return {
            "main": st.session_state["output_dir"],
            "json": os.path.join(st.session_state["output_dir"], "json_temp"),
            "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs"),
            "combined": os.path.join(st.session_state["output_dir"], "combined_output")
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
        "json": os.path.join(st.session_state["output_dir"], "json_temp"),
        "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
        "logs": os.path.join(st.session_state["output_dir"], "logs"),
        "combined": os.path.join(st.session_state["output_dir"], "combined_output")
    }
    st.session_state["directories"] = dirs

# Now we can use dirs["json"] and dirs["csv"] instead of hardcoded paths
JSON_TEMP_DIR = dirs["json"]
CSV_OUTPUT_DIR = dirs["csv"]
COMBINED_OUTPUT_DIR = dirs["combined"]

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
    st.session_state["companies_processed_with_current_key"] = 0
    if len(st.session_state["api_keys"]) > 1:
        st.session_state["current_key_index"] = (st.session_state["current_key_index"] + 1) % len(st.session_state["api_keys"])
        with status_lock:
            st.session_state["process_status"].append(f"Switched to API key {st.session_state['current_key_index'] + 1} of {len(st.session_state['api_keys'])}")
    return get_current_api_key()

def save_failed_companies():
    """Save failed companies to a file"""
    try:
        failed_file = os.path.join(dirs["logs"], "failed_companies.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for company, details in st.session_state["failed_companies"].items():
                f.write(f"{company},{details['timestamp']},{details['reason']}\n")
        return failed_file
    except Exception as e:
        st.error(f"Error saving failed companies: {e}")
        return None

def load_failed_companies():
    """Load failed companies from a file"""
    try:
        failed_file = os.path.join(dirs["logs"], "failed_companies.txt")
        if os.path.exists(failed_file):
            with open(failed_file, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",", 2)
                    if len(parts) >= 3:
                        company, timestamp, reason = parts
                        st.session_state["failed_companies"][company] = {
                            "timestamp": timestamp,
                            "reason": reason
                        }
    except Exception as e:
        st.error(f"Error loading failed companies: {e}")

# Load failed companies on startup
try:
    load_failed_companies()
except Exception as e:
    st.error(f"Error during startup: {e}")

def split_date_range(start_date, end_date, segment_size_days=7):
    """Split a date range into segments of specified size in days"""
    segments = []
    current_start = start_date
    
    while current_start <= end_date:
        # Calculate the end of this segment
        segment_end = min(current_start + timedelta(days=segment_size_days - 1), end_date)
        segments.append((current_start, segment_end))
        
        # Move to the next segment
        current_start = segment_end + timedelta(days=1)
    
    return segments

def fetch_tweets_for_keyword_worker(worker_id: int, keyword: str, start_date, end_date, api_key: str, 
                                   status_queue: Queue, result_queue: Queue, error_queue: Queue,
                                   segment_id: str = "", tweet_section: str = "latest"):
    """Worker function to fetch tweets for a specific keyword"""
    try:
        display_keyword = keyword.replace("+", " ")
        status_queue.put(f"Worker {worker_id}: Fetching tweets for: {display_keyword} ({start_date} to {end_date})")
        
        conn = http.client.HTTPSConnection(API_HOST)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST
        }
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        api_query = format_keyword_for_api(keyword)
        
        # Enhanced API endpoint with sort_by parameter to ensure latest tweets
        endpoint = (
            f"/search/search?query={api_query}"
            f"&section={tweet_section}"
            f"&min_retweets=1"
            f"&min_likes=1"
            f"&limit={TWEETS_PER_REQUEST}"
            f"&start_date={start_date_str}"
            f"&end_date={end_date_str}"
            f"&language=en"
            f"&sort_by=recency"  # Sort by most recent tweets first
        )
        
        try:
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data_bytes = res.read()
            
            if not data_bytes:
                error_msg = f"Empty response for {display_keyword} ({start_date} to {end_date})"
                status_queue.put(error_msg)
                error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                result_queue.put((keyword, None, segment_id))
                return
            
            try:
                data = json.loads(data_bytes.decode("utf-8"))
                tweet_count = len(data.get('results', []))
                status_queue.put(f"Worker {worker_id}: Found {tweet_count} tweets for {display_keyword} ({start_date} to {end_date})")
                result_queue.put((keyword, data, segment_id))
            except json.JSONDecodeError as e:
                error_msg = f"Error parsing JSON for {display_keyword} ({start_date} to {end_date}): {e}"
                status_queue.put(error_msg)
                error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                result_queue.put((keyword, None, segment_id))
        except Exception as e:
            error_msg = f"API request failed for {display_keyword} ({start_date} to {end_date}): {e}"
            status_queue.put(error_msg)
            error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            result_queue.put((keyword, None, segment_id))
        finally:
            conn.close()
            
    except Exception as e:
        error_msg = f"Fatal error fetching tweets for {keyword.replace('+', ' ')} ({start_date} to {end_date}): {e}"
        status_queue.put(error_msg)
        error_queue.put((keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((keyword, None, segment_id))

def fetch_company_data_worker(worker_id: int, company: str, combined_keywords: List[str], 
                             start_date, end_date, api_key: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue,
                             segment_id: str = "", tweet_section: str = "latest"):
    """Worker function to fetch data for a company and all its combinations"""
    try:
        status_queue.put(f"Worker {worker_id}: Processing company: {company} ({start_date} to {end_date})")
        
        # First, fetch the base company keyword
        all_keywords = [company] + combined_keywords
        company_results = {}
        success_count = 0
        
        for keyword in all_keywords:
            try:
                display_keyword = keyword.replace("+", " ")
                status_queue.put(f"Worker {worker_id}: Fetching tweets for: {display_keyword} ({start_date} to {end_date})")
                
                conn = http.client.HTTPSConnection(API_HOST)
                headers = {
                    'x-rapidapi-key': api_key,
                    'x-rapidapi-host': API_HOST
                }
                
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                api_query = format_keyword_for_api(keyword)
                
                # Enhanced API endpoint with sort_by parameter to ensure latest tweets
                endpoint = (
                    f"/search/search?query={api_query}"
                    f"&section={tweet_section}"
                    f"&min_retweets=1"
                    f"&min_likes=1"
                    f"&limit={TWEETS_PER_REQUEST}"
                    f"&start_date={start_date_str}"
                    f"&end_date={end_date_str}"
                    f"&language=en"
                    f"&sort_by=recency"  # Sort by most recent tweets first
                )
                
                conn.request("GET", endpoint, headers=headers)
                res = conn.getresponse()
                data_bytes = res.read()
                
                if not data_bytes:
                    error_msg = f"Empty response for {display_keyword} ({start_date} to {end_date})"
                    status_queue.put(error_msg)
                    continue
                
                data = json.loads(data_bytes.decode("utf-8"))
                tweet_count = len(data.get('results', []))
                status_queue.put(f"Worker {worker_id}: Found {tweet_count} tweets for {display_keyword} ({start_date} to {end_date})")
                
                company_results[keyword] = data
                success_count += 1
                
                # Add a small delay between requests to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error fetching tweets for {keyword.replace('+', ' ')} ({start_date} to {end_date}): {e}"
                status_queue.put(error_msg)
                continue
            finally:
                conn.close()
        
        # Report overall company success/failure
        if success_count > 0:
            status_queue.put(f"Worker {worker_id}: Successfully processed {success_count}/{len(all_keywords)} keywords for company {company} ({start_date} to {end_date})")
            result_queue.put((company, company_results, segment_id))
        else:
            error_msg = f"Failed to fetch any data for company {company} ({start_date} to {end_date})"
            status_queue.put(error_msg)
            error_queue.put((company, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            result_queue.put((company, None, segment_id))
            
    except Exception as e:
        error_msg = f"Fatal error processing company {company} ({start_date} to {end_date}): {e}"
        status_queue.put(error_msg)
        error_queue.put((company, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((company, None, segment_id))

def fetch_data_parallel(companies, start_date, end_date, max_workers=MAX_WORKERS, 
                       use_date_segmentation=True, segment_size_days=7, tweet_section="latest"):
    """Fetch data for companies and their combinations using parallel workers"""
    if not companies:
        st.warning("No companies selected to fetch")
        return
    
    if not st.session_state["api_keys"] and not st.session_state["api_key"].strip():
        st.error("API key is missing!")
        return
    
    # If no API keys in rotation but we have a single key, add it
    if not st.session_state["api_keys"] and st.session_state["api_key"].strip():
        st.session_state["api_keys"] = [st.session_state["api_key"]]
    
    # Clear the status table at the start of a new fetch
    st.session_state["status_table"] = []
    
    # Determine number of workers (limited by MAX_WORKERS and available keys)
    num_workers = min(max_workers, len(st.session_state["api_keys"]))
    
    # Split the date range into segments if enabled
    if use_date_segmentation:
        date_segments = split_date_range(start_date, end_date, segment_size_days)
        st.write(f"Date range split into {len(date_segments)} segments of {segment_size_days} days each")
        segment_progress = st.progress(0)
        segment_status = st.empty()
    else:
        date_segments = [(start_date, end_date)]
    
    # Process each date segment
    all_results = {}
    for segment_index, (segment_start, segment_end) in enumerate(date_segments):
        if use_date_segmentation:
            segment_status.text(f"Processing segment {segment_index + 1}/{len(date_segments)}: {segment_start} to {segment_end}")
        
        segment_id = f"{segment_start.strftime('%Y%m%d')}-{segment_end.strftime('%Y%m%d')}"
        
        st.write(f"Using {num_workers} parallel workers for fetching {tweet_section} tweets for period: {segment_start} to {segment_end}")
        
        # Create queues for thread communication
        status_queue = Queue()
        result_queue = Queue()
        error_queue = Queue()
        
        # Divide companies among workers
        company_batches = divide_into_chunks(companies, num_workers)
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_area = st.empty()
        eta_display = st.empty()
        
        # Use ThreadPoolExecutor for proper parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit tasks to the executor
            futures = []
            for i in range(min(num_workers, len(company_batches))):
                if i < len(company_batches) and company_batches[i]:  # Check if this batch has companies
                    api_key = st.session_state["api_keys"][i % len(st.session_state["api_keys"])]
                    for company in company_batches[i]:
                        # Get combined keywords for this company
                        combined_keywords = st.session_state["combined_keywords"].get(company, [])
                        
                        future = executor.submit(
                            fetch_company_data_worker,
                            i+1, company, combined_keywords, segment_start, segment_end, api_key,
                            status_queue, result_queue, error_queue, segment_id, tweet_section
                        )
                        futures.append((future, company))
                        # Add a small delay to prevent overwhelming the API
                        time.sleep(0.2)
            
            # Process results as they come in
            segment_results = {}
            processed_count = 0
            total_count = len(companies)
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
                    company, company_results, seg_id = result_queue.get()
                    processed_count += 1
                    
                    # Update API key rotation counter
                    st.session_state["companies_processed_with_current_key"] += 1
                    if st.session_state["companies_processed_with_current_key"] >= st.session_state["companies_per_key"]:
                        rotate_to_next_api_key()
                    
                    if company_results:
                        segment_results[company] = company_results
                        # Mark as processed
                        st.session_state["processed_companies"].add(company)
                        
                        # Save results to temporary files with segment ID in filename
                        for keyword, data in company_results.items():
                            try:
                                sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
                                output_file = os.path.join(JSON_TEMP_DIR, f"{sanitized_keyword}_{seg_id}.json")
                                with open(output_file, "w", encoding="utf-8") as outfile:
                                    json.dump(data, outfile)
                            except Exception as e:
                                st.error(f"Error saving tweets for {keyword.replace('+', ' ')}: {e}")
                    
                    # Update progress
                    progress_bar.progress(processed_count / total_count)
                    
                    # Calculate and display ETA
                    if processed_count > 0:
                        elapsed_time = time.time() - start_time
                        companies_per_second = processed_count / elapsed_time
                        remaining_companies = total_count - processed_count
                        eta_seconds = remaining_companies / companies_per_second if companies_per_second > 0 else 0
                        
                        # Format ETA nicely
                        if eta_seconds < 60:
                            eta_text = f"{eta_seconds:.0f} seconds"
                        elif eta_seconds < 3600:
                            eta_text = f"{eta_seconds/60:.1f} minutes"
                        else:
                            eta_text = f"{eta_seconds/3600:.1f} hours"
                        
                        eta_display.text(f"Progress: {processed_count}/{total_count} companies | ETA: {eta_text}")
                
                # Process errors
                while not error_queue.empty():
                    company, timestamp, reason = error_queue.get()
                    st.session_state["failed_companies"][company] = {
                        "timestamp": timestamp,
                        "reason": reason
                    }
                
                # Check if any futures are done
                for future, company in list(futures):
                    if future.done():
                        futures.remove((future, company))
                        try:
                            # This will raise an exception if the future raised one
                            future.result()
                        except Exception as e:
                            st.error(f"Error in worker thread for {company}: {e}")
                            # Make sure we count this as processed
                            if company not in segment_results:
                                processed_count += 1
                
                # If all futures are done but we haven't processed all companies, something went wrong
                if not futures and processed_count < total_count:
                    st.error(f"All workers finished but only processed {processed_count}/{total_count} companies")
                    break
                
                time.sleep(0.1)  # Prevent busy waiting
        
        # Save failed companies
        save_failed_companies()
        
        eta_display.empty()
        status_area.empty()
        
        # Merge this segment's results into the overall results
        for company, company_results in segment_results.items():
            if company not in all_results:
                all_results[company] = {}
            
            for keyword, data in company_results.items():
                if keyword not in all_results[company]:
                    all_results[company][keyword] = []
                
                # Add the tweets from this segment
                all_results[company][keyword].extend(data.get('results', []))
        
        # Update segment progress
        if use_date_segmentation:
            segment_progress.progress((segment_index + 1) / len(date_segments))
    
    # After all segments are processed, combine the results
    segment_status_text = "All segments processed. Combining results..."
    if use_date_segmentation:
        segment_status.text(segment_status_text)
    else:
        st.write(segment_status_text)
    
    combine_segmented_results(all_results, tweet_section, start_date, end_date)
    
    # Clean up temporary JSON files
    cleanup_status = "Cleaning up temporary files..."
    if use_date_segmentation:
        segment_status.text(cleanup_status)
    else:
        st.write(cleanup_status)
    
    cleanup_temp_json_files()
    
    completion_text = "Data fetching completed! Combined results are ready."
    if use_date_segmentation:
        segment_status.text(completion_text)
    else:
        st.write(completion_text)
    
    return all_results

def cleanup_temp_json_files():
    """Clean up temporary JSON files after combining"""
    try:
        if os.path.exists(JSON_TEMP_DIR):
            # Count files before deletion for reporting
            json_files = [f for f in os.listdir(JSON_TEMP_DIR) if f.endswith(".json")]
            file_count = len(json_files)
            
            # Delete all JSON files in the temp directory
            for file in json_files:
                os.remove(os.path.join(JSON_TEMP_DIR, file))
            
            st.session_state["process_status"].append(f"Cleaned up {file_count} temporary JSON files")
    except Exception as e:
        st.error(f"Error cleaning up temporary JSON files: {e}")

def combine_segmented_results(all_results, tweet_section="latest", start_date=None, end_date=None):
    """Combine results from different segments into unified files and initialize status table"""
    try:
        # Clear the status table before adding new entries
        st.session_state["status_table"] = []
        
        # Process each company
        for company, company_results in all_results.items():
            # Process each keyword
            for keyword, tweets in company_results.items():
                try:
                    # Remove duplicate tweets based on tweet_id
                    seen_ids = set()
                    unique_tweets = []
                    for tweet in tweets:
                        tweet_id = tweet.get('tweet_id')
                        if tweet_id and tweet_id not in seen_ids:
                            seen_ids.add(tweet_id)
                            unique_tweets.append(tweet)
                    
                    # Create a combined data structure
                    combined_data = {
                        "results": unique_tweets,
                        "meta": {
                            "combined_from_segments": True,
                            "total_tweets": len(unique_tweets),
                            "combination_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "section": tweet_section,
                            "original_tweets_count": len(tweets),
                            "duplicate_tweets_removed": len(tweets) - len(unique_tweets),
                            "date_range": f"{start_date.strftime('%Y-%m-%d') if start_date else 'unknown'} to {end_date.strftime('%Y-%m-%d') if end_date else 'unknown'}"
                        }
                    
                    # Save the combined data
                    sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
                    output_file = os.path.join(COMBINED_OUTPUT_DIR, f"{sanitized_keyword}_{tweet_section}_combined.json")
                    with open(output_file, "w", encoding="utf-8") as outfile:
                        json.dump(combined_data, outfile)
                    
                    # Add entry to status table
                    display_keyword = keyword.replace("+", " ")
                    keyword_type = "Base" if keyword == company else "Combined"
                    
                    st.session_state["status_table"].append({
                        "Company": company,
                        "Keyword": display_keyword,
                        "Type": keyword_type,
                        "JSON Data": "✅",
                        "CSV Output": "❌",
                        "Date Range": f"{start_date.strftime('%Y-%m-%d') if start_date else 'unknown'} to {end_date.strftime('%Y-%m-%d') if end_date else 'unknown'}",
                        "Tweets": len(unique_tweets),
                        "Section": tweet_section
                    })
                    
                    # Update status
                    st.session_state["process_status"].append(
                        f"Combined {len(unique_tweets)} unique tweets for {keyword.replace('+', ' ')} "
                        f"(removed {len(tweets) - len(unique_tweets)} duplicates)"
                    )
                
                except Exception as e:
                    st.error(f"Error combining results for {keyword.replace('+', ' ')}: {e}")
        
        st.success(f"Combined results saved to {COMBINED_OUTPUT_DIR}")
    except Exception as e:
        st.error(f"Error combining segmented results: {e}")

def convert_json_to_csv():
    """Convert all combined JSON files to CSV"""
    if not os.path.exists(COMBINED_OUTPUT_DIR):
        st.warning("No combined JSON files found. Please fetch tweets first.")
        return
    
    json_files = [f for f in os.listdir(COMBINED_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No combined JSON files found in the output directory.")
        return
    
    progress_bar = st.progress(0)
    status_area = st.empty()
    
    for i, json_file in enumerate(json_files):
        try:
            status_area.text(f"Converting {json_file} to CSV...")
            
            json_file_path = os.path.join(COMBINED_OUTPUT_DIR, json_file)
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
            
            # Extract the base keyword from the filename
            keyword_parts = os.path.splitext(json_file)[0].split('_')
            # Remove section and combined markers
            sections = ["latest", "top", "user", "image", "video", "combined"]
            keyword_parts = [part for part in keyword_parts if part not in sections]
            keyword = ' '.join(keyword_parts)
            
            # Update status table
            with status_lock:
                for entry in st.session_state["status_table"]:
                    if entry["Keyword"].lower() == keyword.lower() or entry["Keyword"].lower() == keyword.replace("_", " ").lower():
                        entry["CSV Output"] = "✅"
                        st.session_state["process_status"].append(f"Updated CSV status for {entry['Keyword']}")
                        break
            
            # Update progress
            progress_bar.progress((i + 1) / len(json_files))
            
        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")
    
    status_area.empty()
    st.success(f"Converted {len(json_files)} combined JSON files to CSV")

def combine_company_csvs(company_name):
    """Merge all CSV files for a company's combined keywords into one DataFrame"""
    dataframes = []
    
    if not os.path.exists(CSV_OUTPUT_DIR):
        return None
    
    company_prefix = company_name.replace(" ", "_")
    csv_files = [
        f for f in os.listdir(CSV_OUTPUT_DIR) 
        if f.startswith(company_prefix) and f.endswith(".csv")
    ]
    
    if not csv_files:
        return None
    
    for csv_file in csv_files:
        try:
            file_path = os.path.join(CSV_OUTPUT_DIR, csv_file)
            # Check if file is not empty
            if os.path.getsize(file_path) > 0:
                df = pd.read_csv(file_path)
                if not df.empty:
                    dataframes.append(df)
            else:
                st.warning(f"Skipping empty file: {csv_file}")
        except pd.errors.EmptyDataError:
            st.warning(f"No data in file: {csv_file}")
        except Exception as e:
            st.warning(f"Error reading {csv_file}: {str(e)}")
    
    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    else:
        return None

def clear_temp():
    """Clear temporary files"""
    try:
        if os.path.exists(JSON_TEMP_DIR):
            shutil.rmtree(JSON_TEMP_DIR)
            os.makedirs(JSON_TEMP_DIR, exist_ok=True)

        if os.path.exists(CSV_OUTPUT_DIR):
            shutil.rmtree(CSV_OUTPUT_DIR)
            os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
            
        if os.path.exists(COMBINED_OUTPUT_DIR):
            shutil.rmtree(COMBINED_OUTPUT_DIR)
            os.makedirs(COMBINED_OUTPUT_DIR, exist_ok=True)

        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        st.session_state["failed_companies"] = {}
        st.session_state["processed_companies"] = set()
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

# API Key Input
api_keys_input = st.text_area(
    "Twitter API Keys (one per line)",
    help="Enter your RapidAPI keys, one per line. The app will rotate through these keys."
)

# Parse the keys
if api_keys_input:
    st.session_state["api_keys"] = [key.strip() for key in api_keys_input.split('\n') if key.strip()]
    total_capacity = len(st.session_state["api_keys"]) * st.session_state["companies_per_key"]
    st.write(f"Found {len(st.session_state['api_keys'])} API keys.")
    st.write(f"Can process approximately {total_capacity} companies.")
elif not st.session_state["api_keys"]:
    st.session_state["api_keys"] = [DEFAULT_API_KEY]
    st.warning("No API keys provided. Using default key which is rate-limited.")

# API rotation settings
st.session_state["companies_per_key"] = st.number_input(
    "Companies per API key",
    min_value=1,
    value=st.session_state["companies_per_key"],
    help="Number of companies to process with each key before rotating. Each company includes its base keyword and all combinations."
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
    
    # Tweet section selection
    tweet_section_options = {
        "latest": "Latest Tweets (most recent)",
        "top": "Top Tweets (most popular)",
        "user": "User Tweets (from specific users)",
        "image": "Image Tweets (tweets with images)",
        "video": "Video Tweets (tweets with videos)"
    }
    
    st.session_state["tweet_section"] = st.selectbox(
        "Tweet Section",
        options=list(tweet_section_options.keys()),
        format_func=lambda x: tweet_section_options[x],
        index=list(tweet_section_options.keys()).index(st.session_state["tweet_section"]),
        help="Type of tweets to fetch. 'Latest' gets the most recent tweets."
    )
    
    # Date segmentation settings
    st.session_state["use_date_segmentation"] = st.checkbox(
        "Use Date Segmentation", 
        value=st.session_state["use_date_segmentation"],
        help="Split the date range into smaller segments to get more tweets"
    )
    
    if st.session_state["use_date_segmentation"]:
        st.session_state["segment_size_days"] = st.slider(
            "Segment Size (Days)",
            min_value=1,
            max_value=30,
            value=st.session_state["segment_size_days"],
            help="Size of each date segment in days. Smaller segments may yield more tweets but require more API calls."
        )

# Date input section - Using previous month as default
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=prev_month_start)
with col2:
    end_date = st.date_input("End Date", value=prev_month_end)

# Show date segmentation preview if enabled
if st.session_state["use_date_segmentation"]:
    segments = split_date_range(start_date, end_date, st.session_state["segment_size_days"])
    st.write(f"Date range will be split into {len(segments)} segments:")
    for i, (seg_start, seg_end) in enumerate(segments[:5]):  # Show first 5 segments
        st.write(f"  {i+1}. {seg_start} to {seg_end}")
    if len(segments) > 5:
        st.write(f"  ... and {len(segments) - 5} more segments")
    
    # Calculate potential tweet yield - updated for 20 tweets per request
    tweets_per_segment = 5 * TWEETS_PER_REQUEST  # 5 keywords × 20 tweets
    potential_tweets = len(segments) * tweets_per_segment
    st.write(f"Potential maximum tweets per company: {potential_tweets} ({tweets_per_segment} per segment × {len(segments)} segments)")

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
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Data"):
        if start_date <= end_date and base_keywords:
            fetch_data_parallel(
                base_keywords, 
                start_date, 
                end_date, 
                max_workers,
                st.session_state["use_date_segmentation"],
                st.session_state["segment_size_days"],
                st.session_state["tweet_section"]
            )
        else:
            st.warning("Invalid date range or no companies found!")

with col2:
    if st.button("Convert JSON to CSV"):
        convert_json_to_csv()

with col3:
    if st.button("Clear Temp"):
        clear_temp()

# Display failed companies
if st.session_state["failed_companies"]:
    with st.expander("Failed Companies", expanded=True):
        st.write(f"There are {len(st.session_state['failed_companies'])} companies that failed processing:")
        
        # Create a DataFrame for better display
        failed_data = []
        for company, details in st.session_state["failed_companies"].items():
            failed_data.append({
                "Company": company,
                "Timestamp": details["timestamp"],
                "Reason": details["reason"]
            })
        
        failed_df = pd.DataFrame(failed_data)
        st.dataframe(failed_df)
        
        # Option to clear failed companies
        if st.button("Clear Failed Companies List"):
            st.session_state["failed_companies"] = {}
            save_failed_companies()
            st.success("Failed companies list cleared.")

# Display API key usage
with st.expander("API Key Usage"):
    st.write(f"Current key index: {st.session_state['current_key_index'] + 1} of {len(st.session_state['api_keys'])}")
    st.write(f"Companies processed with current key: {st.session_state['companies_processed_with_current_key']} of {st.session_state['companies_per_key']}")
    st.write(f"Total companies processed: {len(st.session_state['processed_companies'])}")

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
    st.write("No actions performed yet. Fetch data to see the status.")

# Display storage information
with st.expander("Storage Information"):
    try:
        # Calculate storage usage
        total_size = 0
        file_count = 0
        
        # Check each directory
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files if os.path.isfile(os.path.join(dir_path, f)))
                total_size += dir_size
                dir_file_count = len([f for f in files if os.path.isfile(os.path.join(dir_path, f))])
                file_count += dir_file_count
                
                # Format size nicely
                if dir_size < 1024:
                    dir_size_str = f"{dir_size} bytes"
                elif dir_size < 1024 * 1024:
                    dir_size_str = f"{dir_size/1024:.2f} KB"
                else:
                    dir_size_str = f"{dir_size/(1024*1024):.2f} MB"
                
                # Display directory information with Twitter-specific context
                if dir_name == "json":
                    dir_display_name = "Twitter JSON Temp"
                elif dir_name == "csv":
                    dir_display_name = "Twitter CSV Output"
                elif dir_name == "logs":
                    dir_display_name = "Twitter Logs"
                elif dir_name == "combined":
                    dir_display_name = "Twitter Combined Output"
                else:
                    dir_display_name = f"Twitter {dir_name.capitalize()}"
                
                st.write(f"### {dir_display_name}: {dir_path}")
                st.write(f"- Contains {dir_file_count} files")
                st.write(f"- Size: {dir_size_str}")
                
                # Show some files as examples if there are any
                if files:
                    st.write("- Example files:")
                    for f in files[:5]:  # Show up to 5 files
                        st.write(f"  - {f}")
                    if len(files) > 5:
                        st.write(f"  - ... and {len(files) - 5} more")
            else:
                # Display empty directory with Twitter-specific context
                if dir_name == "json":
                    dir_display_name = "Twitter JSON Temp"
                elif dir_name == "csv":
                    dir_display_name = "Twitter CSV Output"
                elif dir_name == "logs":
                    dir_display_name = "Twitter Logs"
                elif dir_name == "combined":
                    dir_display_name = "Twitter Combined Output"
                else:
                    dir_display_name = f"Twitter {dir_name.capitalize()}"
                
                st.write(f"### {dir_display_name}: {dir_path}")
                st.write("- Directory does not exist")
        
        # Format total size nicely
        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size/1024:.2f} KB"
        else:
            size_str = f"{total_size/(1024*1024):.2f} MB"
        
        st.write(f"### Total Twitter Storage Used: {size_str}")
        st.write(f"### Total Twitter Files: {file_count}")
        
        # Add Twitter-specific information about accessing these files
        st.write("### Accessing Twitter Data Files")
        st.write("These files are stored in directories on your system. To access them:")
        st.write("1. Use the download buttons provided in the app")
        st.write("2. Navigate to the output directory on your system")
        st.write("3. The combined results are in the 'combined_output' directory")
        st.write("4. CSV files are in the 'csv_output' directory")
        
    except Exception as e:
        st.error(f"Error displaying storage information: {e}")

# CSV Download Section
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download CSV Files"):
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    # Extract the base keyword from the filename for better display
                    keyword_parts = os.path.splitext(csv_file)[0].split('_')
                    # Remove section markers
                    sections = ["latest", "top", "user", "image", "video", "combined"]
                    keyword_parts = [part for part in keyword_parts if part not in sections]
                    display_name = ' '.join(keyword_parts)
                    
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {display_name}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found. Convert JSON to CSV first.")
else:
    st.warning("CSV output directory does not exist")

# Combined JSON Download Section
if os.path.exists(COMBINED_OUTPUT_DIR):
    json_files = [f for f in os.listdir(COMBINED_OUTPUT_DIR) if f.endswith(".json")]
    if json_files:
        with st.expander("Download JSON Files"):
            st.write("These files contain the combined tweet data:")
            cols = st.columns(3)
            for i, json_file in enumerate(json_files):
                with cols[i % 3]:
                    # Extract the base keyword from the filename for better display
                    keyword_parts = os.path.splitext(json_file)[0].split('_')
                    # Remove section and combined markers
                    sections = ["latest", "top", "user", "image", "video", "combined"]
                    keyword_parts = [part for part in keyword_parts if part not in sections]
                    display_name = ' '.join(keyword_parts)
                    
                    with open(os.path.join(COMBINED_OUTPUT_DIR, json_file), "r") as f:
                        st.download_button(
                            label=f"Download {display_name} JSON",
                            data=f.read(),
                            file_name=json_file,
                            mime="application/json"
                        )
    else:
        st.warning("No JSON files found. Fetch data first.")
else:
    st.warning("Combined output directory does not exist")
