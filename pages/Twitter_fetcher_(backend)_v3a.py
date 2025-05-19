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
    if today.month == 1:
        prev_month = 12
        year = today.year - 1
    else:
        prev_month = today.month - 1
        year = today.year
    
    first_day = date(year, prev_month, 1)
    _, last_day_num = calendar.monthrange(year, prev_month)
    last_day = date(year, prev_month, last_day_num)
    
    return first_day, last_day

# Configuration
API_HOST = "twitter154.p.rapidapi.com"
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
KEYWORDS_FILE = "data/keywords.txt"
MAX_WORKERS = 4
TWEETS_PER_REQUEST = 20

# Initialize session state
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "directories" not in st.session_state:
    st.session_state["directories"] = {}
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
    st.session_state["failed_companies"] = {}
if "processed_companies" not in st.session_state:
    st.session_state["processed_companies"] = set()
if "use_date_segmentation" not in st.session_state:
    st.session_state["use_date_segmentation"] = True
if "segment_size_days" not in st.session_state:
    st.session_state["segment_size_days"] = 7
if "tweet_section" not in st.session_state:
    st.session_state["tweet_section"] = "latest"
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []
if "current_key_index" not in st.session_state:
    st.session_state["current_key_index"] = 0
if "companies_processed_with_current_key" not in st.session_state:
    st.session_state["companies_processed_with_current_key"] = 0
if "companies_per_key" not in st.session_state:
    st.session_state["companies_per_key"] = 5

# Thread-safe locks
status_lock = threading.Lock()

# Streamlit UI
st.title("Twitter Data Fetcher")

# Output directory configuration
st.session_state["output_dir"] = st.text_input(
    "Output Directory",
    value=st.session_state["output_dir"],
    help="Directory where all files will be saved"
)

def ensure_directories():
    try:
        os.makedirs(st.session_state["output_dir"], exist_ok=True)
        dirs = {
            "main": st.session_state["output_dir"],
            "json": os.path.join(st.session_state["output_dir"], "json_output"),
            "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs"),
            "combined": os.path.join(st.session_state["output_dir"], "combined_output")
        }
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        return dirs
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        return {
            "main": st.session_state["output_dir"],
            "json": os.path.join(st.session_state["output_dir"], "json_output"),
            "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs"),
            "combined": os.path.join(st.session_state["output_dir"], "combined_output")
        }

st.session_state["directories"] = ensure_directories()
dirs = st.session_state["directories"]
JSON_OUTPUT_DIR = dirs["json"]
CSV_OUTPUT_DIR = dirs["csv"]
COMBINED_OUTPUT_DIR = dirs["combined"]

def generate_combined_keywords(base_keywords):
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
    return keyword.replace(" ", "+")

def get_current_api_key():
    if not st.session_state["api_keys"]:
        return DEFAULT_API_KEY
    return st.session_state["api_keys"][st.session_state["current_key_index"]]

def rotate_to_next_api_key():
    st.session_state["companies_processed_with_current_key"] = 0
    if len(st.session_state["api_keys"]) > 1:
        st.session_state["current_key_index"] = (st.session_state["current_key_index"] + 1) % len(st.session_state["api_keys"])
        with status_lock:
            st.session_state["process_status"].append(f"Switched to API key {st.session_state['current_key_index'] + 1} of {len(st.session_state['api_keys'])}")
    return get_current_api_key()

def split_date_range(start_date, end_date, segment_size_days=7):
    segments = []
    current_start = start_date
    
    while current_start <= end_date:
        segment_end = min(current_start + timedelta(days=segment_size_days - 1), end_date)
        segments.append((current_start, segment_end))
        current_start = segment_end + timedelta(days=1)
    
    return segments

def fetch_company_data_worker(worker_id: int, company: str, combined_keywords: List[str], 
                             start_date, end_date, api_key: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue,
                             segment_id: str = "", tweet_section: str = "latest"):
    try:
        status_queue.put(f"Worker {worker_id}: Processing company: {company} ({start_date} to {end_date})")
        
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
                
                endpoint = (
                    f"/search/search?query={api_query}"
                    f"&section={tweet_section}"
                    f"&min_retweets=1"
                    f"&min_likes=1"
                    f"&limit={TWEETS_PER_REQUEST}"
                    f"&start_date={start_date_str}"
                    f"&end_date={end_date_str}"
                    f"&language=en"
                    f"&sort_by=recency"
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
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error fetching tweets for {keyword.replace('+', ' ')} ({start_date} to {end_date}): {e}"
                status_queue.put(error_msg)
                continue
            finally:
                conn.close()
        
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
    if not companies:
        st.warning("No companies selected to fetch")
        return
    
    if not st.session_state["api_keys"] and not st.session_state["api_key"].strip():
        st.error("API key is missing!")
        return
    
    # Clear previous data
    if os.path.exists(JSON_OUTPUT_DIR):
        shutil.rmtree(JSON_OUTPUT_DIR)
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    
    if os.path.exists(COMBINED_OUTPUT_DIR):
        shutil.rmtree(COMBINED_OUTPUT_DIR)
    os.makedirs(COMBINED_OUTPUT_DIR, exist_ok=True)
    
    # Reset status table
    st.session_state["status_table"] = []
    st.session_state["process_status"] = []
    st.session_state["failed_companies"] = {}
    st.session_state["processed_companies"] = set()
    
    if not st.session_state["api_keys"] and st.session_state["api_key"].strip():
        st.session_state["api_keys"] = [st.session_state["api_key"]]
    
    num_workers = min(max_workers, len(st.session_state["api_keys"]))
    
    if use_date_segmentation:
        date_segments = split_date_range(start_date, end_date, segment_size_days)
        st.write(f"Date range split into {len(date_segments)} segments of {segment_size_days} days each")
        segment_progress = st.progress(0)
        segment_status = st.empty()
    else:
        date_segments = [(start_date, end_date)]
    
    all_results = {}
    for segment_index, (segment_start, segment_end) in enumerate(date_segments):
        if use_date_segmentation:
            segment_status.text(f"Processing segment {segment_index + 1}/{len(date_segments)}: {segment_start} to {segment_end}")
        
        segment_id = f"{segment_start.strftime('%Y%m%d')}-{segment_end.strftime('%Y%m%d')}"
        
        st.write(f"Using {num_workers} parallel workers for fetching {tweet_section} tweets for period: {segment_start} to {segment_end}")
        
        status_queue = Queue()
        result_queue = Queue()
        error_queue = Queue()
        
        company_batches = divide_into_chunks(companies, num_workers)
        
        progress_bar = st.progress(0)
        status_area = st.empty()
        eta_display = st.empty()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for i in range(min(num_workers, len(company_batches))):
                if i < len(company_batches) and company_batches[i]:
                    api_key = st.session_state["api_keys"][i % len(st.session_state["api_keys"])]
                    for company in company_batches[i]:
                        combined_keywords = st.session_state["combined_keywords"].get(company, [])
                        future = executor.submit(
                            fetch_company_data_worker,
                            i+1, company, combined_keywords, segment_start, segment_end, api_key,
                            status_queue, result_queue, error_queue, segment_id, tweet_section
                        )
                        futures.append((future, company))
                        time.sleep(0.2)
            
            segment_results = {}
            processed_count = 0
            total_count = len(companies)
            start_time = time.time()
            
            while processed_count < total_count:
                status_messages = []
                while not status_queue.empty():
                    status = status_queue.get()
                    with status_lock:
                        st.session_state["process_status"].append(status)
                    status_messages.append(status)
                
                if status_messages:
                    status_area.text("\n".join(status_messages[-5:]))
                
                while not result_queue.empty():
                    company, company_results, seg_id = result_queue.get()
                    processed_count += 1
                    
                    st.session_state["companies_processed_with_current_key"] += 1
                    if st.session_state["companies_processed_with_current_key"] >= st.session_state["companies_per_key"]:
                        rotate_to_next_api_key()
                    
                    if company_results:
                        segment_results[company] = company_results
                        st.session_state["processed_companies"].add(company)
                        
                        for keyword, data in company_results.items():
                            try:
                                sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
                                output_file = os.path.join(JSON_OUTPUT_DIR, f"{sanitized_keyword}_{seg_id}.json")
                                with open(output_file, "w", encoding="utf-8") as outfile:
                                    json.dump(data, outfile)
                                
                                display_keyword = keyword.replace("+", " ")
                                keyword_type = "Base" if keyword == company else "Combined"
                                
                                st.session_state["status_table"].append({
                                    "Company": company,
                                    "Keyword": display_keyword,
                                    "Type": keyword_type,
                                    "Tweet Extract JSON": "✅",
                                    "CSV Output": "❌",
                                    "Date Range": f"{segment_start.strftime('%Y-%m-%d')} to {segment_end.strftime('%Y-%m-%d')}",
                                    "Segment": seg_id,
                                    "Section": tweet_section
                                })
                            except Exception as e:
                                st.error(f"Error saving tweets for {keyword.replace('+', ' ')}: {e}")
                    
                    progress_bar.progress(processed_count / total_count)
                    
                    if processed_count > 0:
                        elapsed_time = time.time() - start_time
                        companies_per_second = processed_count / elapsed_time
                        remaining_companies = total_count - processed_count
                        eta_seconds = remaining_companies / companies_per_second if companies_per_second > 0 else 0
                        
                        if eta_seconds < 60:
                            eta_text = f"{eta_seconds:.0f} seconds"
                        elif eta_seconds < 3600:
                            eta_text = f"{eta_seconds/60:.1f} minutes"
                        else:
                            eta_text = f"{eta_seconds/3600:.1f} hours"
                        
                        eta_display.text(f"Progress: {processed_count}/{total_count} companies | ETA: {eta_text}")
                
                while not error_queue.empty():
                    company, timestamp, reason = error_queue.get()
                    st.session_state["failed_companies"][company] = {
                        "timestamp": timestamp,
                        "reason": reason
                    }
                
                for future, company in list(futures):
                    if future.done():
                        futures.remove((future, company))
                        try:
                            future.result()
                        except Exception as e:
                            st.error(f"Error in worker thread for {company}: {e}")
                            if company not in segment_results:
                                processed_count += 1
                
                if not futures and processed_count < total_count:
                    st.error(f"All workers finished but only processed {processed_count}/{total_count} companies")
                    break
                
                time.sleep(0.1)
        
        eta_display.empty()
        status_area.empty()
        
        for company, company_results in segment_results.items():
            if company not in all_results:
                all_results[company] = {}
            
            for keyword, data in company_results.items():
                if keyword not in all_results[company]:
                    all_results[company][keyword] = []
                
                all_results[company][keyword].extend(data.get('results', []))
        
        if use_date_segmentation:
            segment_progress.progress((segment_index + 1) / len(date_segments))
    
    if use_date_segmentation:
        segment_status.text("All segments processed. Combining results...")
        combine_segmented_results(all_results, tweet_section)
        segment_status.text("Results combined successfully!")
    
    # Clean up individual JSON files after combining
    if os.path.exists(JSON_OUTPUT_DIR):
        shutil.rmtree(JSON_OUTPUT_DIR)
        os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    
    return all_results

def combine_segmented_results(all_results, tweet_section="latest"):
    try:
        for company, company_results in all_results.items():
            for keyword, tweets in company_results.items():
                try:
                    seen_ids = set()
                    unique_tweets = []
                    for tweet in tweets:
                        tweet_id = tweet.get('tweet_id')
                        if tweet_id and tweet_id not in seen_ids:
                            seen_ids.add(tweet_id)
                            unique_tweets.append(tweet)
                    
                    combined_data = {
                        "results": unique_tweets,
                        "meta": {
                            "combined_from_segments": True,
                            "total_tweets": len(unique_tweets),
                            "combination_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "section": tweet_section,
                            "original_tweets_count": len(tweets),
                            "duplicate_tweets_removed": len(tweets) - len(unique_tweets)
                        }
                    }
                    
                    sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
                    output_file = os.path.join(COMBINED_OUTPUT_DIR, f"{sanitized_keyword}_combined.json")
                    with open(output_file, "w", encoding="utf-8") as outfile:
                        json.dump(combined_data, outfile)
                    
                    display_keyword = keyword.replace("+", " ")
                    keyword_type = "Base" if keyword == company else "Combined"
                    
                    # Update status table entry
                    for entry in st.session_state["status_table"]:
                        if entry["Company"] == company and entry["Keyword"] == display_keyword:
                            entry["Segment"] = "Combined"
                            break
                    
                    st.session_state["process_status"].append(
                        f"Combined {len(unique_tweets)} unique tweets for {display_keyword} "
                        f"(removed {len(tweets) - len(unique_tweets)} duplicates)"
                    )
                    
                except Exception as e:
                    st.error(f"Error combining results for {keyword.replace('+', ' ')}: {e}")
        
        st.success(f"Combined results saved to {COMBINED_OUTPUT_DIR}")
    except Exception as e:
        st.error(f"Error combining segmented results: {e}")

def convert_json_to_csv():
    """Convert all combined JSON files to CSV and update status"""
    if not os.path.exists(COMBINED_OUTPUT_DIR):
        st.warning("No combined JSON files found. Please fetch tweets first.")
        return
    
    json_files = [f for f in os.listdir(COMBINED_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No JSON files found in the combined output directory.")
        return
    
    progress_bar = st.progress(0)
    status_area = st.empty()
    
    for i, json_file in enumerate(json_files):
        try:
            status_area.text(f"Converting {json_file} to CSV...")
            
            json_file_path = os.path.join(COMBINED_OUTPUT_DIR, json_file)
            csv_file_name = f"{os.path.splitext(json_file)[0]}.csv"
            csv_file_path = os.path.join(COMBINED_OUTPUT_DIR, csv_file_name)
            
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
            
            # Extract keyword from filename
            keyword = os.path.splitext(json_file)[0].replace("_combined", "").replace("_", " ")
            
            # Update status table
            with status_lock:
                for entry in st.session_state["status_table"]:
                    if entry["Keyword"] == keyword:
                        entry["CSV Output"] = "✅"
                        break
            
            progress_bar.progress((i + 1) / len(json_files))
            
        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")
    
    status_area.empty()
    st.success(f"Converted {len(json_files)} combined JSON files to CSV")

def combine_company_csvs(company_name, use_combined=True):
    dataframes = []
    
    if use_combined and os.path.exists(COMBINED_OUTPUT_DIR):
        company_prefix = company_name.replace(" ", "_")
        csv_files = [
            f for f in os.listdir(COMBINED_OUTPUT_DIR) 
            if f.startswith(company_prefix) and f.endswith(".csv")
        ]
        
        if csv_files:
            for csv_file in csv_files:
                try:
                    file_path = os.path.join(COMBINED_OUTPUT_DIR, csv_file)
                    if os.path.getsize(file_path) > 0:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            dataframes.append(df)
                except Exception as e:
                    st.warning(f"Error reading {csv_file}: {str(e)}")
            
            if dataframes:
                return pd.concat(dataframes, ignore_index=True)
    
    return None

def clear_temp():
    try:
        if os.path.exists(JSON_OUTPUT_DIR):
            shutil.rmtree(JSON_OUTPUT_DIR)
            os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

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

# Advanced settings
with st.expander("Advanced Settings"):
    max_workers = st.slider(
        "Maximum Parallel Workers", 
        min_value=1, 
        max_value=8, 
        value=MAX_WORKERS,
        step=1,
        help="Maximum number of parallel workers. Each worker uses one API key."
    )
    
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

# Date input section
prev_month_start, prev_month_end = get_previous_month_range()
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=prev_month_start)
with col2:
    end_date = st.date_input("End Date", value=prev_month_end)

if st.session_state["use_date_segmentation"]:
    segments = split_date_range(start_date, end_date, st.session_state["segment_size_days"])
    st.write(f"Date range will be split into {len(segments)} segments:")
    for i, (seg_start, seg_end) in enumerate(segments[:5]):
        st.write(f"  {i+1}. {seg_start} to {seg_end}")
    if len(segments) > 5:
        st.write(f"  ... and {len(segments) - 5} more segments")
    
    tweets_per_segment = 5 * TWEETS_PER_REQUEST
    potential_tweets = len(segments) * tweets_per_segment
    st.write(f"Potential maximum tweets per company: {potential_tweets} ({tweets_per_segment} per segment × {len(segments)} segments)")

# Load base keywords
base_keywords = []
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]
else:
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w") as file:
        file.write("AAPL\nMSFT\nGOOG\nAMZN\nFB")
    base_keywords = ["AAPL", "MSFT", "GOOG", "AMZN", "FB"]
    st.info(f"Created sample keywords file at {KEYWORDS_FILE}")

if not st.session_state["combined_keywords"] and base_keywords:
    st.session_state["combined_keywords"] = generate_combined_keywords(base_keywords)

# Company selection dropdown
if base_keywords:
    st.session_state["selected_company"] = st.selectbox(
        "Select Company to Manage Combinations",
        base_keywords,
        index=0
    )
    
    combined_csv = combine_company_csvs(st.session_state["selected_company"], use_combined=True)
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
        
        failed_data = []
        for company, details in st.session_state["failed_companies"].items():
            failed_data.append({
                "Company": company,
                "Timestamp": details["timestamp"],
                "Reason": details["reason"]
            })
        
        failed_df = pd.DataFrame(failed_data)
        st.dataframe(failed_df)
        
        if st.button("Clear Failed Companies List"):
            st.session_state["failed_companies"] = {}
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
            for status in st.session_state["process_status"][-20:]:
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
        total_size = 0
        file_count = 0
        
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files if os.path.isfile(os.path.join(dir_path, f)))
                total_size += dir_size
                dir_file_count = len([f for f in files if os.path.isfile(os.path.join(dir_path, f))])
                file_count += dir_file_count
                
                if dir_size < 1024:
                    dir_size_str = f"{dir_size} bytes"
                elif dir_size < 1024 * 1024:
                    dir_size_str = f"{dir_size/1024:.2f} KB"
                else:
                    dir_size_str = f"{dir_size/(1024*1024):.2f} MB"
                
                if dir_name == "json":
                    dir_display_name = "Twitter JSON Output"
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
                
                if files:
                    st.write("- Example files:")
                    for f in files[:5]:
                        st.write(f"  - {f}")
                    if len(files) > 5:
                        st.write(f"  - ... and {len(files) - 5} more")
            else:
                if dir_name == "json":
                    dir_display_name = "Twitter JSON Output"
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
        
        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size/1024:.2f} KB"
        else:
            size_str = f"{total_size/(1024*1024):.2f} MB"
        
        st.write(f"### Total Twitter Storage Used: {size_str}")
        st.write(f"### Total Twitter Files: {file_count}")
        
        st.write("### Accessing Twitter Data Files")
        st.write("These files are stored in directories on your system. To access them:")
        st.write("1. Use the download buttons provided in the app")
        st.write("2. Navigate to the output directory on your system")
        st.write("3. The combined results are in the 'combined_output' directory")
        
    except Exception as e:
        st.error(f"Error displaying storage information: {e}")

# CSV Download Section
if os.path.exists(COMBINED_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(COMBINED_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download Combined CSV Files"):
            st.write("These files contain all tweets combined:")
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    with open(os.path.join(COMBINED_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {csv_file.replace('_', ' ').replace('.csv', '').replace('combined', 'All')}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found in combined output directory")
else:
    st.warning("Combined output directory does not exist")
