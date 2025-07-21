import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
import time
# threading removed - using only concurrent.futures
import concurrent.futures
from queue import Queue
from datetime import datetime, timedelta, date
import calendar
import platform
from typing import List, Dict, Any, Tuple, Set
import csv
from transformers import pipeline

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
KEYWORDS_FILE = "data/twitter_keyboards.csv"
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
if "failed_companies" not in st.session_state:
    st.session_state["failed_companies"] = set()
if "completed_companies" not in st.session_state:
    st.session_state["completed_companies"] = set()
if "segment_size_days" not in st.session_state:
    st.session_state["segment_size_days"] = 7
if "tweet_section" not in st.session_state:
    st.session_state["tweet_section"] = "latest"
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []

# No longer need locks since workers only use queues

# Streamlit UI
st.title("Twitter Data Fetcher - Company Based")

# Output directory configuration
st.session_state["output_dir"] = st.text_input(
    "Output Directory",
    value=st.session_state["output_dir"],
    help="Directory where all files will be saved"
)

def ensure_directories():
    """Create necessary directories"""
    try:
        os.makedirs(st.session_state["output_dir"], exist_ok=True)
        dirs = {
            "main": st.session_state["output_dir"],
            "company_json": os.path.join(st.session_state["output_dir"], "company_json"),
            "company_csv": os.path.join(st.session_state["output_dir"], "company_csv"),
            "final_output": os.path.join(st.session_state["output_dir"], "final_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs")
        }
        for dir_name, dir_path in dirs.items():
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                raise Exception(f"Failed to create directory: {dir_path}")
        return dirs
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        return {}

st.session_state["directories"] = ensure_directories()
dirs = st.session_state["directories"]

# 1. Add import for zero-shot classification
# 2. Update KEYWORDS_FILE to point to the new CSV
# 3. Helper to read companies from CSV
import csv

def read_companies_from_csv(csv_path):
    companies = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            companies.append({
                'symbol': row['symbol'].strip(),
                'compname': row['compname'].strip()
            })
    return companies

# 4. Update keyword generation

def generate_company_keywords(symbol, compname):
    return [
        f'"{symbol}"',
        f'"${symbol}"',
        f'"{compname}"',
        f'"{compname} stock"',
        f'"{compname} earnings"'
    ]

# 5. Zero-shot classifier setup (load once)
@st.cache_resource(show_spinner=False)
def get_zero_shot_classifier():
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

classifier = get_zero_shot_classifier()

# 6. Filtering function

def filter_tweets_zero_shot(tweets, compname):
    good, bad = [], []
    labels = [f"about {compname}", f"not about {compname}"]
    for tweet in tweets:
        text = tweet.get('text', '')
        result = classifier(text, labels)
        if result['labels'][0] == labels[0] and result['scores'][0] > 0.7:
            good.append(tweet)
        else:
            bad.append(tweet)
    return good, bad

def format_keyword_for_api(keyword):
    """Format keyword for API call"""
    return keyword.replace(" ", "+")

def split_date_range(start_date, end_date, segment_size_days=7):
    """Split date range into segments"""
    segments = []
    current_start = start_date
    
    while current_start <= end_date:
        segment_end = min(current_start + timedelta(days=segment_size_days - 1), end_date)
        segments.append((current_start, segment_end))
        current_start = segment_end + timedelta(days=1)
    
    return segments

def fetch_tweets_for_keyword(keyword, start_date, end_date, api_key, tweet_section="latest"):
    """Fetch tweets for a single keyword and date range"""
    try:
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
        conn.close()
        
        if not data_bytes:
            return {"results": [], "error": "Empty response"}
        
        data = json.loads(data_bytes.decode("utf-8"))
        
        # Add metadata to each tweet
        if "results" in data:
            for tweet in data["results"]:
                tweet["keyword_used"] = keyword
                tweet["fetch_date_range"] = f"{start_date_str}_to_{end_date_str}"
        
        return data
        
    except Exception as e:
        return {"results": [], "error": str(e)}

def process_company_worker(worker_id: int, companies: List[str], start_date, end_date, 
                          api_key: str, segment_size_days: int, status_queue: Queue, 
                          result_queue: Queue, output_dirs: dict, tweet_section: str = "latest"):
    """Process multiple companies with one API key"""
    try:
        for company in companies:
            company_success = True
            all_company_tweets = []
            keywords = generate_company_keywords(company['symbol'], company['compname'])
            
            status_queue.put(f"Worker {worker_id}: Processing company: {company['compname']}")
            
            # Get date segments
            date_segments = split_date_range(start_date, end_date, segment_size_days)
            
            # Process each keyword for this company
            for keyword_idx, keyword in enumerate(keywords):
                keyword_tweets = []
                keyword_success = True
                
                status_queue.put(f"Worker {worker_id}: {company['compname']} - Keyword {keyword_idx+1}/5: {keyword.replace('+', ' ')}")
                
                # Fetch tweets for each date segment
                for segment_start, segment_end in date_segments:
                    try:
                        result = fetch_tweets_for_keyword(keyword, segment_start, segment_end, api_key, tweet_section)
                        
                        if "error" in result:
                            status_queue.put(f"Worker {worker_id}: Error for {keyword}: {result['error']}")
                            keyword_success = False
                            break
                        
                        tweets = result.get("results", [])
                        keyword_tweets.extend(tweets)
                        
                        status_queue.put(f"Worker {worker_id}: {company['compname']} - {keyword.replace('+', ' ')} ({segment_start} to {segment_end}): {len(tweets)} tweets")
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        status_queue.put(f"Worker {worker_id}: Error fetching {keyword} for {segment_start}-{segment_end}: {e}")
                        keyword_success = False
                        break
                
                if not keyword_success:
                    company_success = False
                    status_queue.put(f"Worker {worker_id}: Company {company['compname']} FAILED due to keyword {keyword}")
                    break
                
                # Add all tweets from this keyword to company collection
                all_company_tweets.extend(keyword_tweets)
            
            # --- Wait and allow user to cancel filtering ---
            filter_key = f"cancel_filtering_{company['symbol']}_{company['compname']}"
            st.session_state[filter_key] = False
            with st.spinner(f"Waiting 10 seconds before filtering tweets for {company['compname']}... Click 'Cancel Filtering' to skip."):
                cancel_button = st.button("Cancel Filtering", key=filter_key)
                start_time = time.time()
                while time.time() - start_time < 10:
                    if st.session_state.get(filter_key):
                        break
                    time.sleep(0.1)
            if st.session_state.get(filter_key):
                status_queue.put(f"Worker {worker_id}: Filtering canceled for {company['compname']}")
                # Save all tweets as good (skip filtering)
                if company_success and all_company_tweets:
                    # Remove duplicates by tweet_id
                    unique_tweets = {}
                    for tweet in all_company_tweets:
                        tweet_id = tweet.get("tweet_id")
                        if tweet_id and tweet_id not in unique_tweets:
                            tweet["company_name"] = company['compname']
                            unique_tweets[tweet_id] = tweet
                    final_tweets = list(unique_tweets.values())
                    # Save as CSV
                    good_tweets_path = os.path.join(output_dirs["company_csv"], f"{company['compname'].replace(' ', '_')}_good_tweets.csv")
                    try:
                        df = pd.DataFrame(final_tweets)
                        df.to_csv(good_tweets_path, index=False)
                        status_queue.put(f"Worker {worker_id}: 💾 Saved {company['compname']}_good_tweets.csv with {len(final_tweets)} tweets")
                    except Exception as e:
                        status_queue.put(f"Worker {worker_id}: ❌ Error saving {company['compname']}_good_tweets.csv: {e}")
                        company_success = False
                    if company_success:
                        status_queue.put(f"Worker {worker_id}: ✅ Company {company['compname']} completed - {len(final_tweets)} unique tweets")
                        result_queue.put(("success", company['compname'], len(final_tweets)))
                    else:
                        status_queue.put(f"Worker {worker_id}: ❌ Company {company['compname']} failed during save")
                        result_queue.put(("failed", company['compname'], 0))
                else:
                    status_queue.put(f"Worker {worker_id}: ❌ Company {company['compname']} failed")
                    result_queue.put(("failed", company['compname'], 0))
            else:
                # Proceed with zero-shot filtering
                good, bad = filter_tweets_zero_shot(all_company_tweets, company['compname'])
                # Save good tweets as CSV
                good_tweets_path = os.path.join(output_dirs["company_csv"], f"{company['compname'].replace(' ', '_')}_good_tweets.csv")
                try:
                    df_good = pd.DataFrame(good)
                    df_good.to_csv(good_tweets_path, index=False)
                    status_queue.put(f"Worker {worker_id}: 💾 Saved {company['compname']}_good_tweets.csv with {len(good)} good tweets")
                except Exception as e:
                    status_queue.put(f"Worker {worker_id}: ❌ Error saving {company['compname']}_good_tweets.csv: {e}")
                    company_success = False
                # Save bad tweets as CSV
                bad_tweets_path = os.path.join(output_dirs["company_csv"], f"{company['compname'].replace(' ', '_')}_bad_tweets.csv")
                try:
                    df_bad = pd.DataFrame(bad)
                    df_bad.to_csv(bad_tweets_path, index=False)
                    status_queue.put(f"Worker {worker_id}: 💾 Saved {company['compname']}_bad_tweets.csv with {len(bad)} bad tweets")
                except Exception as e:
                    status_queue.put(f"Worker {worker_id}: ❌ Error saving {company['compname']}_bad_tweets.csv: {e}")
                    company_success = False
                if company_success:
                    status_queue.put(f"Worker {worker_id}: ✅ Company {company['compname']} completed - {len(good)} good tweets, {len(bad)} bad tweets")
                    result_queue.put(("success", company['compname'], len(good)))
                else:
                    status_queue.put(f"Worker {worker_id}: ❌ Company {company['compname']} failed during save")
                    result_queue.put(("failed", company['compname'], 0))
                
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Fatal error: {e}")
        for company in companies:
            result_queue.put(("failed", company['compname'], 0))

def fetch_data_parallel(companies, start_date, end_date, api_keys, segment_size_days=7, tweet_section="latest"):
    """Main parallel fetching function"""
    if not companies:
        st.warning("No companies to fetch")
        return
    
    if not api_keys:
        st.error("No API keys provided!")
        return
    
    # Clear previous data
    for dir_path in [dirs["company_json"], dirs["company_csv"], dirs["final_output"]]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    # Reset state
    st.session_state["status_table"] = []
    st.session_state["process_status"] = []
    st.session_state["failed_companies"] = set()
    st.session_state["completed_companies"] = set()
    
    # Distribute companies among API keys
    num_workers = min(len(api_keys), len(companies))
    companies_per_worker = len(companies) // num_workers
    company_assignments = []
    
    for i in range(num_workers):
        start_idx = i * companies_per_worker
        if i == num_workers - 1:  # Last worker gets remaining companies
            end_idx = len(companies)
        else:
            end_idx = (i + 1) * companies_per_worker
        company_assignments.append(companies[start_idx:end_idx])
    
    st.write(f"🔄 Starting parallel fetch with {num_workers} workers")
    st.write(f"📊 Distribution: {[len(assignment) for assignment in company_assignments]} companies per worker")
    
    # Progress tracking
    total_companies = len(companies)
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all worker tasks
        futures = []
        for worker_id, (company_list, api_key) in enumerate(zip(company_assignments, api_keys)):
            if company_list:  # Only submit if there are companies to process
                future = executor.submit(
                    process_company_worker,
                    worker_id + 1,
                    company_list,
                    start_date,
                    end_date,
                    api_key,
                    segment_size_days,
                    status_queue,
                    result_queue,
                    dirs,
                    tweet_section
                )
                futures.append(future)
        
        # Monitor progress
        completed_companies = 0
        
        while completed_companies < total_companies:
            # Update status
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            # Check results
            while not result_queue.empty():
                status, company, tweet_count = result_queue.get()
                if status == "success":
                    st.session_state["completed_companies"].add(company)
                    st.session_state["status_table"].append({
                        "Company": company,
                        "Status": "✅ Success",
                        "Tweets": tweet_count
                    })
                else:
                    st.session_state["failed_companies"].add(company)
                    st.session_state["status_table"].append({
                        "Company": company,
                        "Status": "❌ Failed",
                        "Tweets": 0
                    })
                
                completed_companies += 1
                progress_bar.progress(completed_companies / total_companies)
            
            # Update display
            status_container.write(f"Progress: {completed_companies}/{total_companies} companies completed")
            
            time.sleep(1)
        
        # Wait for all workers to complete
        concurrent.futures.wait(futures)
    
    st.success(f"✅ Fetching completed! {len(st.session_state['completed_companies'])} successful, {len(st.session_state['failed_companies'])} failed")
    
    # Show what was created
    if os.path.exists(dirs["company_json"]):
        json_files = [f for f in os.listdir(dirs["company_json"]) if f.endswith(".json")]
        st.info(f"📁 Created {len(json_files)} JSON files in: {dirs['company_json']}")
        if json_files:
            st.write("JSON files:", ", ".join(json_files[:5]) + ("..." if len(json_files) > 5 else ""))
    
    # Convert to CSV and create master file
    convert_json_to_csv()
    create_master_csv()
    save_failed_companies_list()

def convert_json_to_csv():
    """Convert company JSON files to CSV"""
    if not dirs or "company_json" not in dirs:
        st.error("Directory structure not initialized properly")
        return
        
    if not os.path.exists(dirs["company_json"]):
        st.warning("Company JSON directory does not exist")
        return
        
    json_files = [f for f in os.listdir(dirs["company_json"]) if f.endswith(".json")]
    
    if not json_files:
        st.warning("No JSON files to convert")
        st.info(f"Checked directory: {dirs['company_json']}")
        return
    
    progress_bar = st.progress(0)
    
    for i, json_file in enumerate(json_files):
        try:
            json_path = os.path.join(dirs["company_json"], json_file)
            csv_path = os.path.join(dirs["company_csv"], json_file.replace(".json", ".csv"))
            
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tweets = data.get("results", [])
            if tweets:
                # Flatten tweet data
                records = []
                for tweet in tweets:
                    record = {
                        "company_name": tweet.get("company_name", ""),
                        "keyword_used": tweet.get("keyword_used", ""),
                        "tweet_id": tweet.get("tweet_id", ""),
                        "creation_date": tweet.get("creation_date", ""),
                        "text": tweet.get("text", ""),
                        "language": tweet.get("language", ""),
                        "favorite_count": tweet.get("favorite_count", 0),
                        "retweet_count": tweet.get("retweet_count", 0),
                        "reply_count": tweet.get("reply_count", 0),
                        "views": tweet.get("views", 0),
                        "fetch_date_range": tweet.get("fetch_date_range", "")
                    }
                    
                    # Add user information
                    user_info = tweet.get("user", {})
                    for key, value in user_info.items():
                        record[f"user_{key}"] = value
                    
                    records.append(record)
                
                df = pd.DataFrame(records)
                df.to_csv(csv_path, index=False, encoding="utf-8")
            
            progress_bar.progress((i + 1) / len(json_files))
            
        except Exception as e:
            st.error(f"Error converting {json_file}: {e}")
    
    st.success(f"✅ Converted {len(json_files)} company files to CSV")

def create_master_csv():
    """Create master CSV with all companies"""
    csv_files = [f for f in os.listdir(dirs["company_csv"]) if f.endswith(".csv")]
    
    if not csv_files:
        st.warning("No CSV files to combine")
        return
    
    all_dataframes = []
    
    for csv_file in csv_files:
        try:
            csv_path = os.path.join(dirs["company_csv"], csv_file)
            df = pd.read_csv(csv_path, encoding="utf-8")
            if not df.empty:
                all_dataframes.append(df)
        except Exception as e:
            st.error(f"Error reading {csv_file}: {e}")
    
    if all_dataframes:
        master_df = pd.concat(all_dataframes, ignore_index=True)
        master_path = os.path.join(dirs["final_output"], "Master_All_Companies.csv")
        master_df.to_csv(master_path, index=False, encoding="utf-8")
        st.success(f"✅ Created master CSV with {len(master_df)} total tweets")
    else:
        st.warning("No data to combine into master CSV")

def save_failed_companies_list():
    """Save list of failed companies"""
    if st.session_state["failed_companies"]:
        failed_path = os.path.join(dirs["final_output"], "Failed_Companies.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            f.write("Failed Companies:\n")
            f.write("================\n\n")
            for company in sorted(st.session_state["failed_companies"]):
                f.write(f"- {company}\n")
        st.info(f"📝 Saved {len(st.session_state['failed_companies'])} failed companies to Failed_Companies.txt")

# UI Configuration
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date", value=get_previous_month_range()[0])
    st.session_state["segment_size_days"] = st.number_input(
        "Date Segment Size (days)", 
        min_value=1, 
        max_value=30, 
        value=st.session_state["segment_size_days"],
        help="Split date range into segments of this many days"
    )

with col2:
    end_date = st.date_input("End Date", value=get_previous_month_range()[1])
    st.session_state["tweet_section"] = st.selectbox(
        "Tweet Section",
        ["latest", "top", "people", "photos", "videos"],
        index=0
    )

# API Keys input
st.subheader("API Keys Configuration")
api_keys_text = st.text_area(
    "Enter API Keys (one per line)",
    help="Enter multiple RapidAPI Twitter keys, one per line. Companies will be distributed among these keys.",
    height=100
)

if api_keys_text.strip():
    st.session_state["api_keys"] = [key.strip() for key in api_keys_text.strip().split('\n') if key.strip()]
else:
    st.session_state["api_keys"] = [DEFAULT_API_KEY] if DEFAULT_API_KEY else []

st.write(f"📊 **{len(st.session_state['api_keys'])} API keys configured**")

# Load companies
companies = []
if os.path.exists(KEYWORDS_FILE):
    companies = read_companies_from_csv(KEYWORDS_FILE)
else:
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "compname"])
        writer.writeheader()
        writer.writerow({"symbol": "AAPL", "compname": "Apple"})
        writer.writerow({"symbol": "MSFT", "compname": "Microsoft"})
        writer.writerow({"symbol": "GOOG", "compname": "Google"})
        writer.writerow({"symbol": "AMZN", "compname": "Amazon"})
        writer.writerow({"symbol": "META", "compname": "Meta"})
    companies = read_companies_from_csv(KEYWORDS_FILE)
    st.info(f"Created sample companies file at {KEYWORDS_FILE}")

if companies:
    st.write(f"📋 **{len(companies)} companies loaded from {KEYWORDS_FILE}**")
    
    # Show distribution
    if st.session_state["api_keys"]:
        num_workers = min(len(st.session_state["api_keys"]), len(companies))
        companies_per_worker = len(companies) // num_workers
        remaining = len(companies) % num_workers
        
        st.write("**Work Distribution:**")
        for i in range(num_workers):
            companies_for_this_worker = companies_per_worker + (1 if i < remaining else 0)
            st.write(f"- API Key {i+1}: {companies_for_this_worker} companies")

# Date segmentation info
if start_date <= end_date:
    segments = split_date_range(start_date, end_date, st.session_state["segment_size_days"])
    st.write(f"📅 **Date range will be split into {len(segments)} segments**")
    potential_tweets_per_keyword = len(segments) * TWEETS_PER_REQUEST
    potential_tweets_per_company = potential_tweets_per_keyword * 5  # 5 keywords per company
    st.write(f"🎯 **Potential tweets per company: ~{potential_tweets_per_company}** ({potential_tweets_per_keyword} per keyword)")

# Main fetch button
st.subheader("Data Fetching")

if st.button("🚀 Start Fetching Data", type="primary"):
    if start_date <= end_date and companies and st.session_state["api_keys"]:
        fetch_data_parallel(
            companies,
            start_date,
            end_date,
            st.session_state["api_keys"],
            st.session_state["segment_size_days"],
            st.session_state["tweet_section"]
        )
    else:
        st.warning("⚠️ Please check: valid date range, companies loaded, and API keys provided!")

# Additional action buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 Convert JSON to CSV"):
        convert_json_to_csv()

with col2:
    if st.button("🔗 Create Master CSV"):
        create_master_csv()

with col3:
    if st.button("🔍 Debug Files"):
        st.write("**Directory Status:**")
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                st.write(f"✅ {dir_name}: {len(files)} files")
                if files and len(files) <= 10:
                    st.write(f"   Files: {', '.join(files)}")
                elif files:
                    st.write(f"   Sample files: {', '.join(files[:5])}...")
            else:
                st.write(f"❌ {dir_name}: Directory missing")

with col4:
    if st.button("🗑️ Clear All Data"):
        for dir_path in [dirs["company_json"], dirs["company_csv"], dirs["final_output"]]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            os.makedirs(dir_path, exist_ok=True)
        # Reset all session state keys that could affect outputs or company lists
        for key in list(st.session_state.keys()):
            if key not in ["output_dir", "directories"]:  # preserve output_dir and directories
                del st.session_state[key]
        st.success("🗑️ All data and session state cleared!")

# Show a collapsible table of all companies and their keywords before fetching
if os.path.exists(KEYWORDS_FILE):
    companies_preview = read_companies_from_csv(KEYWORDS_FILE)
    if companies_preview:
        import pandas as pd
        preview_rows = []
        for c in companies_preview:
            keywords = generate_company_keywords(c['symbol'], c['compname'])
            preview_rows.append({
                "Symbol": c['symbol'],
                "Company Name": c['compname'],
                "Keyword 1": keywords[0],
                "Keyword 2": keywords[1],
                "Keyword 3": keywords[2],
                "Keyword 4": keywords[3],
                "Keyword 5": keywords[4],
            })
        preview_df = pd.DataFrame(preview_rows)
        st.info("If you edit twitter_keyboards.csv, please reload the app to see the updated preview and ensure correct fetching.")
        with st.expander("🔍 Preview: Keywords to be Fetched (Company-wise)", expanded=False):
            st.dataframe(preview_df, hide_index=True)

# Display results
if st.session_state.get("status_table"):
    st.subheader("📊 Company Processing Status")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.dataframe(status_df, hide_index=True)
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful", len(st.session_state.get("completed_companies", set())))
    with col2:
        st.metric("❌ Failed", len(st.session_state.get("failed_companies", set())))
    with col3:
        total_tweets = sum([row["Tweets"] for row in st.session_state["status_table"] if row["Tweets"] > 0])
        st.metric("🐦 Total Tweets", total_tweets)

# Process status
if st.session_state.get("process_status"):
    with st.expander("📝 Process Log", expanded=False):
        for status in st.session_state["process_status"][-50:]:  # Show last 50 messages
            st.text(status)

# Download section
if os.path.exists(dirs["final_output"]):
    files = os.listdir(dirs["final_output"])
    if files:
        st.subheader("📥 Download Results")
        
        # Master CSV download
        master_file = "Master_All_Companies.csv"
        if master_file in files:
            with open(os.path.join(dirs["final_output"], master_file), "rb") as f:
                st.download_button(
                    label="📊 Download Master CSV (All Companies)",
                    data=f.read(),
                    file_name=master_file,
                    mime="text/csv",
                    type="primary"
                )
        
        # Individual company downloads
        csv_files = [f for f in os.listdir(dirs["company_csv"]) if f.endswith(".csv")]
        if csv_files:
            with st.expander("📁 Download Individual Company Files"):
                cols = st.columns(3)
                for i, csv_file in enumerate(csv_files):
                    with cols[i % 3]:
                        company_name = csv_file.replace("_", " ").replace(".csv", "")
                        with open(os.path.join(dirs["company_csv"], csv_file), "rb") as f:
                            st.download_button(
                                label=f"📄 {company_name}",
                                data=f.read(),
                                file_name=csv_file,
                                mime="text/csv",
                                key=f"download_{csv_file}"
                            )
        
        # Failed companies download
        failed_file = "Failed_Companies.txt"
        if failed_file in files:
            with open(os.path.join(dirs["final_output"], failed_file), "rb") as f:
                st.download_button(
                    label="📝 Download Failed Companies List",
                    data=f.read(),
                    file_name=failed_file,
                    mime="text/plain"
                )

# Storage information
with st.expander("💾 Storage Information"):
    try:
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                total_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
                
                if total_size < 1024 * 1024:
                    size_str = f"{total_size / 1024:.1f} KB"
                else:
                    size_str = f"{total_size / (1024 * 1024):.1f} MB"
                
                st.write(f"**{dir_name.replace('_', ' ').title()}**: {len(files)} files, {size_str}")
    except Exception as e:
        st.error(f"Error calculating storage: {e}")
