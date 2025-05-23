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
        return os.path.join(os.path.expanduser("~"), "Documents", "NewsData")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Documents", "NewsData")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "NewsData")

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
NEWS_API_HOST = "newsapi.org"
PERPLEXITY_API_HOST = "api.perplexity.ai"
DEFAULT_NEWS_API_KEY = "b8b8e1b8b8b8e1b8b8b8e1b8b8b8e1b8"
DEFAULT_PERPLEXITY_API_KEY = "pplx-b8b8e1b8b8b8e1b8b8b8e1b8b8b8e1b8"
KEYWORDS_FILE = "data/keywords.txt"
MAX_WORKERS = 4  # Maximum number of parallel workers

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
if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = None
if "news_api_key" not in st.session_state:
    st.session_state["news_api_key"] = DEFAULT_NEWS_API_KEY
if "perplexity_api_key" not in st.session_state:
    st.session_state["perplexity_api_key"] = DEFAULT_PERPLEXITY_API_KEY
if "failed_companies" not in st.session_state:
    st.session_state["failed_companies"] = {}
if "processed_companies" not in st.session_state:
    st.session_state["processed_companies"] = set()
if "processed_symbols_perplexity" not in st.session_state:
    st.session_state["processed_symbols_perplexity"] = set()

# API key rotation state for News API
if "news_api_keys" not in st.session_state:
    st.session_state["news_api_keys"] = []
if "current_news_key_index" not in st.session_state:
    st.session_state["current_news_key_index"] = 0
if "companies_processed_with_current_news_key" not in st.session_state:
    st.session_state["companies_processed_with_current_news_key"] = 0
if "companies_per_news_key" not in st.session_state:
    st.session_state["companies_per_news_key"] = 5

# API key rotation state for Perplexity API
if "perplexity_api_keys" not in st.session_state:
    st.session_state["perplexity_api_keys"] = []
if "current_perplexity_key_index" not in st.session_state:
    st.session_state["current_perplexity_key_index"] = 0
if "articles_processed_with_current_perplexity_key" not in st.session_state:
    st.session_state["articles_processed_with_current_perplexity_key"] = 0
if "articles_per_perplexity_key" not in st.session_state:
    st.session_state["articles_per_perplexity_key"] = 10

# Thread-safe locks for shared resources
status_lock = threading.Lock()
dataframe_lock = threading.Lock()  # New lock for DataFrame operations
file_locks = {}  # Dictionary to store file-specific locks

# Streamlit UI
st.title("News Data Fetcher")

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
        
        # CSV output directory
        csv_dir = os.path.join(st.session_state["output_dir"], "csv_output")
        os.makedirs(csv_dir, exist_ok=True)
        
        # Logs directory
        logs_dir = os.path.join(st.session_state["output_dir"], "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        return {
            "main": st.session_state["output_dir"],
            "csv": csv_dir,
            "logs": logs_dir
        }
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        return {
            "main": st.session_state["output_dir"],
            "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs")
        }

# Ensure directories exist and store in session state
try:
    st.session_state["directories"] = ensure_directories()
    dirs = st.session_state["directories"]
except Exception as e:
    st.error(f"Error initializing directories: {e}")
    dirs = {
        "main": st.session_state["output_dir"],
        "csv": os.path.join(st.session_state["output_dir"], "csv_output"),
        "logs": os.path.join(st.session_state["output_dir"], "logs")
    }
    st.session_state["directories"] = dirs

CSV_OUTPUT_DIR = dirs["csv"]

def get_file_lock(file_path):
    """Get or create a lock for a specific file"""
    if file_path not in file_locks:
        file_locks[file_path] = threading.Lock()
    return file_locks[file_path]

def safe_dataframe_update(file_path, article_id, summary, symbol):
    """Safely update a DataFrame with proper file locking"""
    file_lock = get_file_lock(file_path)
    
    with file_lock:
        try:
            # Read the current DataFrame from disk
            df = pd.read_csv(file_path)
            
            # Find the article and update it
            success, idx, article_id_converted = debug_summary_update(article_id, symbol, summary, df)
            
            if success:
                # Update the summary
                df.at[idx, 'Summary'] = summary
                
                # Immediately save back to disk
                df.to_csv(file_path, index=False)
                
                with status_lock:
                    st.session_state["process_status"].append(
                        f"✅ Updated and saved summary for article {article_id_converted} in {symbol}"
                    )
                return True
            else:
                with status_lock:
                    st.session_state["process_status"].append(
                        f"❌ Failed to find article {article_id} in {symbol}"
                    )
                return False
                
        except Exception as e:
            with status_lock:
                st.session_state["process_status"].append(
                    f"❌ Error updating {symbol}: {e}"
                )
            return False

def get_current_news_api_key():
    """Get the current News API key from the rotation"""
    if not st.session_state["news_api_keys"]:
        return DEFAULT_NEWS_API_KEY
    return st.session_state["news_api_keys"][st.session_state["current_news_key_index"]]

def rotate_to_next_news_api_key():
    """Rotate to the next News API key and reset the counter"""
    st.session_state["companies_processed_with_current_news_key"] = 0
    if len(st.session_state["news_api_keys"]) > 1:
        st.session_state["current_news_key_index"] = (st.session_state["current_news_key_index"] + 1) % len(st.session_state["news_api_keys"])
        with status_lock:
            st.session_state["process_status"].append(f"Switched to News API key {st.session_state['current_news_key_index'] + 1} of {len(st.session_state['news_api_keys'])}")
    return get_current_news_api_key()

def get_current_perplexity_api_key():
    """Get the current Perplexity API key from the rotation"""
    if not st.session_state["perplexity_api_keys"]:
        return DEFAULT_PERPLEXITY_API_KEY
    return st.session_state["perplexity_api_keys"][st.session_state["current_perplexity_key_index"]]

def rotate_to_next_perplexity_api_key():
    """Rotate to the next Perplexity API key and reset the counter"""
    st.session_state["articles_processed_with_current_perplexity_key"] = 0
    if len(st.session_state["perplexity_api_keys"]) > 1:
        st.session_state["current_perplexity_key_index"] = (st.session_state["current_perplexity_key_index"] + 1) % len(st.session_state["perplexity_api_keys"])
        with status_lock:
            st.session_state["process_status"].append(f"Switched to Perplexity API key {st.session_state['current_perplexity_key_index'] + 1} of {len(st.session_state['perplexity_api_keys'])}")
    return get_current_perplexity_api_key()

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

def fetch_company_news_worker(worker_id: int, company: str, start_date, end_date, api_key: str, 
                             status_queue: Queue, result_queue: Queue, error_queue: Queue):
    """Worker function to fetch news for a company"""
    try:
        status_queue.put(f"Worker {worker_id}: Processing company: {company} ({start_date} to {end_date})")
        
        conn = http.client.HTTPSConnection(NEWS_API_HOST)
        headers = {
            'X-API-Key': api_key
        }
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Enhanced API endpoint
        endpoint = (
            f"/v2/everything?q={company}"
            f"&from={start_date_str}"
            f"&to={end_date_str}"
            f"&language=en"
            f"&sortBy=publishedAt"
            f"&pageSize=100"
        )
        
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data_bytes = res.read()
        
        if not data_bytes:
            error_msg = f"Empty response for {company} ({start_date} to {end_date})"
            status_queue.put(error_msg)
            error_queue.put((company, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            result_queue.put((company, None))
            return
        
        data = json.loads(data_bytes.decode("utf-8"))
        
        if data.get('status') == 'error':
            error_msg = f"API Error for {company}: {data.get('message', 'Unknown error')}"
            status_queue.put(error_msg)
            error_queue.put((company, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            result_queue.put((company, None))
            return
        
        articles = data.get('articles', [])
        article_count = len(articles)
        status_queue.put(f"Worker {worker_id}: Found {article_count} articles for {company} ({start_date} to {end_date})")
        
        result_queue.put((company, articles))
        
    except Exception as e:
        error_msg = f"Fatal error processing company {company} ({start_date} to {end_date}): {e}"
        status_queue.put(error_msg)
        error_queue.put((company, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))
        result_queue.put((company, None))
    finally:
        conn.close()

def fetch_news_parallel(companies, start_date, end_date, max_workers=MAX_WORKERS):
    """Fetch news for companies using parallel workers"""
    if not companies:
        st.warning("No companies selected to fetch")
        return

    if not st.session_state["news_api_keys"] and not st.session_state["news_api_key"].strip():
        st.error("News API key is missing!")
        return

    # If no API keys in rotation but we have a single key, add it
    if not st.session_state["news_api_keys"] and st.session_state["news_api_key"].strip():
        st.session_state["news_api_keys"] = [st.session_state["news_api_key"]]

    # Clear the status table at the start of a new fetch
    st.session_state["status_table"] = []

    # Determine number of workers
    num_workers = min(max_workers, len(st.session_state["news_api_keys"]))
    
    st.write(f"Using {num_workers} parallel workers for fetching news articles for period: {start_date} to {end_date}")
    
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
            if i < len(company_batches) and company_batches[i]:
                api_key = st.session_state["news_api_keys"][i % len(st.session_state["news_api_keys"])]
                for company in company_batches[i]:
                    future = executor.submit(
                        fetch_company_news_worker,
                        i+1, company, start_date, end_date, api_key,
                        status_queue, result_queue, error_queue
                    )
                    futures.append((future, company))
                    time.sleep(0.1)  # Small delay to prevent overwhelming the API
        
        # Process results as they come in
        all_results = {}
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
                status_area.text("\n".join(status_messages[-5:]))
            
            # Process results
            while not result_queue.empty():
                company, articles = result_queue.get()
                processed_count += 1
                
                # Update API key rotation counter
                st.session_state["companies_processed_with_current_news_key"] += 1
                if st.session_state["companies_processed_with_current_news_key"] >= st.session_state["companies_per_news_key"]:
                    rotate_to_next_news_api_key()
                
                if articles:
                    all_results[company] = articles
                    st.session_state["processed_companies"].add(company)
                    
                    # Save results immediately
                    save_company_articles(company, articles, start_date, end_date)
                
                # Update progress
                progress_bar.progress(processed_count / total_count)
                
                # Calculate and display ETA
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
                        future.result()
                    except Exception as e:
                        st.error(f"Error in worker thread for {company}: {e}")
                        if company not in all_results:
                            processed_count += 1
            
            if not futures and processed_count < total_count:
                st.error(f"All workers finished but only processed {processed_count}/{total_count} companies")
                break
            
            time.sleep(0.1)
    
    # Save failed companies
    save_failed_companies()
    
    eta_display.empty()
    status_area.empty()
    
    st.success("News fetching completed!")
    return all_results

def save_company_articles(company, articles, start_date, end_date):
    """Save articles for a company to CSV"""
    try:
        # Prepare data for DataFrame
        records = []
        for i, article in enumerate(articles):
            record = {
                'ID': i + 1,
                'Company': company,
                'Title': article.get('title', ''),
                'Description': article.get('description', ''),
                'URL': article.get('url', ''),
                'Published': article.get('publishedAt', ''),
                'Source': article.get('source', {}).get('name', ''),
                'Author': article.get('author', ''),
                'Content': article.get('content', ''),
                'Summary': '',  # Empty initially
                'Date_Range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
            records.append(record)
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Save to CSV
        sanitized_company = company.replace(" ", "_").replace("/", "_")
        output_file = os.path.join(CSV_OUTPUT_DIR, f"{sanitized_company}_news.csv")
        df.to_csv(output_file, index=False)
        
        # Add entry to status table
        st.session_state["status_table"].append({
            "Company": company,
            "Articles": len(articles),
            "CSV File": "✅",
            "Summaries": "❌",
            "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        })
        
        st.session_state["process_status"].append(f"Saved {len(articles)} articles for {company}")
        
    except Exception as e:
        st.error(f"Error saving articles for {company}: {e}")

def get_summary_from_perplexity(article_title, article_description, article_content, api_key):
    """Get summary from Perplexity API"""
    try:
        conn = http.client.HTTPSConnection(PERPLEXITY_API_HOST)
        
        # Combine article information
        article_text = f"Title: {article_title}\n"
        if article_description:
            article_text += f"Description: {article_description}\n"
        if article_content:
            article_text += f"Content: {article_content}"
        
        # Create the prompt
        prompt = f"""Please provide a concise summary (2-3 sentences) of the following news article:

{article_text}

Summary:"""
        
        payload = json.dumps({
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.2,
            "top_p": 0.9,
            "return_citations": False,
            "search_domain_filter": ["perplexity.ai"],
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "month",
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1
        })
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status != 200:
            return f"Error: HTTP {res.status}"
        
        response_data = json.loads(data.decode("utf-8"))
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            summary = response_data['choices'][0]['message']['content'].strip()
            return summary
        else:
            return "Error: No summary generated"
            
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

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
            if isinstance(article_id, str) and article_id.isdigit():
                idx = df.index[df['ID'] == int(article_id)].tolist()
            elif isinstance(article_id, (int, float)):
                idx = df.index[df['ID'] == str(article_id)].tolist()
        
        if idx:
            return True, idx[0], article_id_converted
        else:
            return False, None, article_id_converted
    except Exception as e:
        st.error(f"Error in debug_summary_update: {e}")
        return False, None, article_id

def fetch_content_summaries_worker(worker_id: int, articles_batch: List[Tuple], api_key: str,
                                 status_queue: Queue, result_queue: Queue, error_queue: Queue):
    """Worker function to fetch content summaries for articles"""
    try:
        for article_id, symbol, title, description, content, file_path in articles_batch:
            try:
                status_queue.put(f"Worker {worker_id}: Fetching summary for article {article_id} in {symbol}")
                
                # Get summary from Perplexity
                summary = get_summary_from_perplexity(title, description, content, api_key)
                
                if summary and not summary.startswith("Error:"):
                    # Use the safe update function
                    success = safe_dataframe_update(file_path, article_id, summary, symbol)
                    
                    if success:
                        result_queue.put((article_id, symbol, summary, "success"))
                    else:
                        result_queue.put((article_id, symbol, summary, "update_failed"))
                else:
                    error_msg = f"Failed to get summary for article {article_id} in {symbol}: {summary}"
                    status_queue.put(error_msg)
                    result_queue.put((article_id, symbol, summary, "api_error"))
                
                # Add delay between requests to respect rate limits
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error processing article {article_id} in {symbol}: {e}"
                status_queue.put(error_msg)
                result_queue.put((article_id, symbol, str(e), "processing_error"))
                
    except Exception as e:
        error_msg = f"Fatal error in worker {worker_id}: {e}"
        status_queue.put(error_msg)
        error_queue.put((worker_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg))

def fetch_content_summaries_parallel(max_workers=2):
    """Fetch content summaries for articles that don't have them yet"""
    if not st.session_state["perplexity_api_keys"] and not st.session_state["perplexity_api_key"].strip():
        st.error("Perplexity API key is missing!")
        return

    # If no API keys in rotation but we have a single key, add it
    if not st.session_state["perplexity_api_keys"] and st.session_state["perplexity_api_key"].strip():
        st.session_state["perplexity_api_keys"] = [st.session_state["perplexity_api_key"]]

    # Find all CSV files
    if not os.path.exists(CSV_OUTPUT_DIR):
        st.warning("No CSV files found. Please fetch articles first.")
        return

    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if not csv_files:
        st.warning("No CSV files found in the output directory.")
        return

    # Collect articles that need summaries
    articles_needing_summaries = []
    symbol_to_file = {}
    
    for csv_file in csv_files:
        try:
            file_path = os.path.join(CSV_OUTPUT_DIR, csv_file)
            df = pd.read_csv(file_path)
            
            # Extract symbol from filename
            symbol = os.path.splitext(csv_file)[0].replace("_news", "")
            symbol_to_file[symbol] = file_path
            
            # Find articles without summaries or with error summaries
            if 'Summary' in df.columns:
                articles_without_summaries = df[
                    (df['Summary'].isna()) | 
                    (df['Summary'] == '') | 
                    (df['Summary'].str.startswith('Error:', na=False))
                ]
            else:
                # If no Summary column, add it and consider all articles need summaries
                df['Summary'] = ''
                df.to_csv(file_path, index=False)
                articles_without_summaries = df
            
            for _, row in articles_without_summaries.iterrows():
                articles_needing_summaries.append((
                    row['ID'], symbol, row.get('Title', ''), 
                    row.get('Description', ''), row.get('Content', ''),
                    file_path
                ))
                
        except Exception as e:
            st.error(f"Error reading {csv_file}: {e}")
            continue

    if not articles_needing_summaries:
        st.success("All articles already have summaries!")
        return

    total_articles = len(articles_needing_summaries)
    st.write(f"Found {total_articles} articles needing summaries")
    
    # Calculate optimal number of workers based on workload
    articles_per_key = st.session_state["articles_per_perplexity_key"]
    available_keys = len(st.session_state["perplexity_api_keys"])
    
    # Calculate how many keys we need based on article count and per-key limit
    keys_needed = (total_articles + articles_per_key - 1) // articles_per_key  # Ceiling division
    
    # Determine optimal number of workers (limited by available keys, needed keys, and max_workers)
    optimal_workers = min(max_workers, available_keys, keys_needed)
    
    # Display workload analysis
    st.write(f"**Workload Analysis:**")
    st.write(f"- Total articles to process: {total_articles}")
    st.write(f"- Articles per API key limit: {articles_per_key}")
    st.write(f"- Keys needed for workload: {keys_needed}")
    st.write(f"- Available API keys: {available_keys}")
    st.write(f"- Max workers setting: {max_workers}")
    st.write(f"- **Optimal workers to use: {optimal_workers}**")
    
    if optimal_workers < keys_needed:
        st.warning(f"Note: Using {optimal_workers} workers but ideally need {keys_needed} for optimal distribution")
    
    # Create queues for thread communication
    status_queue = Queue()
    result_queue = Queue()
    error_queue = Queue()
    
    # Divide articles among workers
    article_batches = divide_into_chunks(articles_needing_summaries, optimal_workers)
    
    # Display worker allocation details
    st.write(f"**Worker Allocation:**")
    for i in range(optimal_workers):
        batch_size = len(article_batches[i]) if i < len(article_batches) else 0
        key_index = i % available_keys
        masked_key = f"{st.session_state['perplexity_api_keys'][key_index][:4]}...{st.session_state['perplexity_api_keys'][key_index][-4:]}" if len(st.session_state['perplexity_api_keys'][key_index]) > 8 else "****"
        st.write(f"- Worker {i+1}: {batch_size} articles, using API key {key_index + 1} ({masked_key})")
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_area = st.empty()
    eta_display = st.empty()
    
    # Use ThreadPoolExecutor for proper parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_workers) as executor:
        # Submit tasks to the executor
        futures = []
        for i in range(optimal_workers):
            if i < len(article_batches) and article_batches[i]:
                # Explicitly assign a different API key to each worker
                key_index = i % available_keys
                api_key = st.session_state["perplexity_api_keys"][key_index]
                
                # Log which worker is using which key (masked for security)
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
                with status_lock:
                    st.session_state["process_status"].append(
                        f"🚀 Worker {i+1} started with {len(article_batches[i])} articles using API key {key_index + 1} ({masked_key})"
                    )
                
                future = executor.submit(
                    fetch_content_summaries_worker,
                    i+1, article_batches[i], api_key,
                    status_queue, result_queue, error_queue
                )
                futures.append(future)
        
        # Process results as they come in
        processed_count = 0
        success_count = 0
        total_count = len(articles_needing_summaries)
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
                status_area.text("\n".join(status_messages[-3:]))
            
            # Process results
            while not result_queue.empty():
                article_id, symbol, summary, status_type = result_queue.get()
                processed_count += 1
                
                if status_type == "success":
                    success_count += 1
                
                # Note: We don't rotate API keys here since each worker has its own assigned key
                
                # Update progress
                progress_bar.progress(processed_count / total_count)
                
                # Calculate and display ETA
                if processed_count > 0:
                    elapsed_time = time.time() - start_time
                    articles_per_second = processed_count / elapsed_time
                    remaining_articles = total_count - processed_count
                    eta_seconds = remaining_articles / articles_per_second if articles_per_second > 0 else 0
                    
                    if eta_seconds < 60:
                        eta_text = f"{eta_seconds:.0f} seconds"
                    elif eta_seconds < 3600:
                        eta_text = f"{eta_seconds/60:.1f} minutes"
                    else:
                        eta_text = f"{eta_seconds/3600:.1f} hours"
                    
                    eta_display.text(f"Progress: {processed_count}/{total_count} articles | Success: {success_count} | ETA: {eta_text}")
            
            # Process errors
            while not error_queue.empty():
                worker_id, timestamp, reason = error_queue.get()
                with status_lock:
                    st.session_state["process_status"].append(f"❌ Worker {worker_id} error: {reason}")
            
            # Check if any futures are done
            for future in list(futures):
                if future.done():
                    futures.remove(future)
                    try:
                        future.result()
                    except Exception as e:
                        st.error(f"Error in worker thread: {e}")
            
            if not futures and processed_count < total_count:
                st.warning(f"All workers finished but only processed {processed_count}/{total_count} articles")
                break
            
            time.sleep(0.1)
    
    eta_display.empty()
    status_area.empty()
    
    # Update status table
    for entry in st.session_state["status_table"]:
        if entry["Summaries"] == "❌":
            entry["Summaries"] = "✅"
    
    # Final summary
    with status_lock:
        st.session_state["process_status"].append(f"🎉 Content summary fetching completed! Successfully processed {success_count}/{total_count} articles using {optimal_workers} workers")
    
    st.success(f"Content summary fetching completed! Successfully processed {success_count}/{total_count} articles")

def clear_temp():
    """Clear temporary files"""
    try:
        if os.path.exists(CSV_OUTPUT_DIR):
            shutil.rmtree(CSV_OUTPUT_DIR)
            os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        st.session_state["failed_companies"] = {}
        st.session_state["processed_companies"] = set()
        st.session_state["processed_symbols_perplexity"] = set()
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

# API Key Input Section
st.subheader("API Configuration")

col1, col2 = st.columns(2)

with col1:
    st.write("**News API Keys**")
    news_api_keys_input = st.text_area(
        "News API Keys (one per line)",
        help="Enter your NewsAPI.org keys, one per line. The app will rotate through these keys."
    )
    
    # Parse the News API keys
    if news_api_keys_input:
        st.session_state["news_api_keys"] = [key.strip() for key in news_api_keys_input.split('\n') if key.strip()]
        total_news_capacity = len(st.session_state["news_api_keys"]) * st.session_state["companies_per_news_key"]
        st.write(f"Found {len(st.session_state['news_api_keys'])} News API keys.")
        st.write(f"Can process approximately {total_news_capacity} companies.")
    elif not st.session_state["news_api_keys"]:
        st.session_state["news_api_keys"] = [DEFAULT_NEWS_API_KEY]
        st.warning("No News API keys provided. Using default key which is rate-limited.")

with col2:
    st.write("**Perplexity API Keys**")
    perplexity_api_keys_input = st.text_area(
        "Perplexity API Keys (one per line)",
        help="Enter your Perplexity AI keys, one per line. The app will rotate through these keys."
    )
    
    # Parse the Perplexity API keys
    if perplexity_api_keys_input:
        st.session_state["perplexity_api_keys"] = [key.strip() for key in perplexity_api_keys_input.split('\n') if key.strip()]
        total_perplexity_capacity = len(st.session_state["perplexity_api_keys"]) * st.session_state["articles_per_perplexity_key"]
        st.write(f"Found {len(st.session_state['perplexity_api_keys'])} Perplexity API keys.")
        st.write(f"Can process approximately {total_perplexity_capacity} articles.")
    elif not st.session_state["perplexity_api_keys"]:
        st.session_state["perplexity_api_keys"] = [DEFAULT_PERPLEXITY_API_KEY]
        st.warning("No Perplexity API keys provided. Using default key which is rate-limited.")

# API rotation settings
col1, col2 = st.columns(2)
with col1:
    st.session_state["companies_per_news_key"] = st.number_input(
        "Companies per News API key",
        min_value=1,
        value=st.session_state["companies_per_news_key"],
        help="Number of companies to process with each News API key before rotating."
    )

with col2:
    st.session_state["articles_per_perplexity_key"] = st.number_input(
        "Articles per Perplexity API key",
        min_value=1,
        value=st.session_state["articles_per_perplexity_key"],
        help="Number of articles to process with each Perplexity API key before rotating."
    )

# Advanced settings in expander
with st.expander("Advanced Settings"):
    max_workers = st.slider(
        "Maximum Parallel Workers (News)", 
        min_value=1, 
        max_value=8, 
        value=MAX_WORKERS,
        step=1,
        help="Maximum number of parallel workers for news fetching."
    )
    
    max_summary_workers = st.slider(
        "Maximum Parallel Workers (Summaries)", 
        min_value=1, 
        max_value=4, 
        value=2,
        step=1,
        help="Maximum number of parallel workers for summary fetching. Keep this low to respect API rate limits."
    )

# Date input section
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=prev_month_start)
with col2:
    end_date = st.date_input("End Date", value=prev_month_end)

# Load base keywords
base_keywords = []
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        base_keywords = [line.strip() for line in file if line.strip()]
else:
    # Create the directory and file if it doesn't exist
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w") as file:
        file.write("AAPL\nMSFT\nGOOG\nAMZN\nTSLA")
    base_keywords = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
    st.info(f"Created sample keywords file at {KEYWORDS_FILE}")

# Company selection dropdown
if base_keywords:
    st.session_state["selected_company"] = st.selectbox(
        "Select Company for Individual Download",
        base_keywords,
        index=0
    )
    
    # Individual CSV download button
    if st.session_state["selected_company"]:
        sanitized_company = st.session_state["selected_company"].replace(" ", "_").replace("/", "_")
        csv_file_path = os.path.join(CSV_OUTPUT_DIR, f"{sanitized_company}_news.csv")
        
        if os.path.exists(csv_file_path):
            with open(csv_file_path, "r") as f:
                st.download_button(
                    label=f"Download {st.session_state['selected_company']} Data",
                    data=f.read(),
                    file_name=f"{sanitized_company}_news.csv",
                    mime="text/csv",
                    key=f"individual_{st.session_state['selected_company']}"
                )
        else:
            st.info(f"No data file found for {st.session_state['selected_company']}. Fetch articles first.")
else:
    st.warning("No companies found in keywords.txt")

# Main action buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        if start_date <= end_date and base_keywords:
            fetch_news_parallel(base_keywords, start_date, end_date, max_workers)
        else:
            st.warning("Invalid date range or no companies found!")

with col2:
    if st.button("Fetch Content"):
        fetch_content_summaries_parallel(max_summary_workers)

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
            save_failed_companies()
            st.success("Failed companies list cleared.")

# Display API key usage
with st.expander("API Key Usage"):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**News API Usage**")
        st.write(f"Current key index: {st.session_state['current_news_key_index'] + 1} of {len(st.session_state['news_api_keys'])}")
        st.write(f"Companies processed with current key: {st.session_state['companies_processed_with_current_news_key']} of {st.session_state['companies_per_news_key']}")
    
    with col2:
        st.write("**Perplexity API Usage**")
        st.write(f"Current key index: {st.session_state['current_perplexity_key_index'] + 1} of {len(st.session_state['perplexity_api_keys'])}")
        st.write(f"Articles processed with current key: {st.session_state['articles_processed_with_current_perplexity_key']} of {st.session_state['articles_per_perplexity_key']}")

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
    st.write("No actions performed yet. Fetch articles to see the status.")

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
                
                if dir_name == "csv":
                    dir_display_name = "News CSV Output"
                elif dir_name == "logs":
                    dir_display_name = "News Logs"
                else:
                    dir_display_name = f"News {dir_name.capitalize()}"
                
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
                if dir_name == "csv":
                    dir_display_name = "News CSV Output"
                elif dir_name == "logs":
                    dir_display_name = "News Logs"
                else:
                    dir_display_name = f"News {dir_name.capitalize()}"
                
                st.write(f"### {dir_display_name}: {dir_path}")
                st.write("- Directory does not exist")
        
        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size/1024:.2f} KB"
        else:
            size_str = f"{total_size/(1024*1024):.2f} MB"
        
        st.write(f"### Total News Storage Used: {size_str}")
        st.write(f"### Total News Files: {file_count}")
        
    except Exception as e:
        st.error(f"Error displaying storage information: {e}")

# CSV Download Section
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download All CSV Files"):
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:
                    company_name = os.path.splitext(csv_file)[0].replace("_news", "").replace("_", " ")
                    
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {company_name}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv",
                            key=f"download_{csv_file}"
                        )
    else:
        st.warning("No CSV files found. Fetch articles first.")
else:
    st.warning("CSV output directory does not exist")
