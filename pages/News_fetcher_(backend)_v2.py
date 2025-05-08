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
API_HOST_PERPLEXITY = "perplexity-api.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"

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
    
# API key rotation state - separate for each API
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []

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

# Ensure directories exist
dirs = ensure_directories()

# Function to save failed symbols to file
def save_failed_symbols():
    failed_file = os.path.join(dirs["logs"], "failed_symbols.txt")
    with open(failed_file, "w", encoding="utf-8") as f:
        for symbol, details in st.session_state["failed_symbols"].items():
            f.write(f"{symbol},{details['timestamp']},{details['reason']}\n")
    return failed_file

# Function to load failed symbols from file
def load_failed_symbols():
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

# Load failed symbols on startup
load_failed_symbols()

# API Key Input
api_keys_input = st.text_area(
    "API Keys (one per line)",
    help="Enter your RapidAPI keys, one per line. The app will rotate through these keys."
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

# Parse the keys
if api_keys_input:
    st.session_state["api_keys"] = [key.strip() for key in api_keys_input.split('\n') if key.strip()]
    total_capacity_seeking_alpha = len(st.session_state["api_keys"]) * st.session_state["stocks_per_key_seeking_alpha"]
    total_capacity_perplexity = len(st.session_state["api_keys"]) * st.session_state["stocks_per_key_perplexity"]
    st.write(f"Found {len(st.session_state['api_keys'])} API keys.")
    st.write(f"Can process approximately {total_capacity_seeking_alpha} stocks with Seeking Alpha API.")
    st.write(f"Can process approximately {total_capacity_perplexity} stocks with Perplexity API.")
elif not st.session_state["api_keys"]:
    st.session_state["api_keys"] = [DEFAULT_API_KEY]
    st.warning("No API keys provided. Using default key which is rate-limited.")

# Function to get the current Seeking Alpha API key
def get_current_seeking_alpha_key():
    if not st.session_state["api_keys"]:
        return DEFAULT_API_KEY
    return st.session_state["api_keys"][st.session_state["current_key_index_seeking_alpha"]]

# Function to get the current Perplexity API key
def get_current_perplexity_key():
    if not st.session_state["api_keys"]:
        return DEFAULT_API_KEY
    return st.session_state["api_keys"][st.session_state["current_key_index_perplexity"]]

# Function to rotate to the next Seeking Alpha key
def rotate_to_next_seeking_alpha_key():
    st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
    if len(st.session_state["api_keys"]) > 1:
        st.session_state["current_key_index_seeking_alpha"] = (st.session_state["current_key_index_seeking_alpha"] + 1) % len(st.session_state["api_keys"])
        st.session_state["process_status"].append(f"Switched to API key {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['api_keys'])} for Seeking Alpha")
    return get_current_seeking_alpha_key()

# Function to rotate to the next Perplexity key
def rotate_to_next_perplexity_key():
    st.session_state["stocks_processed_with_current_key_perplexity"] = 0
    if len(st.session_state["api_keys"]) > 1:
        st.session_state["current_key_index_perplexity"] = (st.session_state["current_key_index_perplexity"] + 1) % len(st.session_state["api_keys"])
        st.session_state["process_status"].append(f"Switched to API key {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['api_keys'])} for Perplexity")
    return get_current_perplexity_key()

# Advanced settings in expander
with st.expander("Advanced Settings"):
    summary_prompt_template = st.text_area(
        "Summary Prompt Template",
        value="Do you know about '{title}' news published on {date}? Please provide a detailed summary of this news, including key details, implications, and context.",
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

# Fetch articles function - now using Seeking Alpha specific key rotation
def fetch_articles(symbol, since_timestamp, until_timestamp):
    # Check if we need to rotate the Seeking Alpha key
    if symbol not in st.session_state["processed_symbols_seeking_alpha"] and st.session_state["stocks_processed_with_current_key_seeking_alpha"] >= st.session_state["stocks_per_key_seeking_alpha"]:
        rotate_to_next_seeking_alpha_key()
    
    api_key = get_current_seeking_alpha_key()
    
    if not api_key.strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA)
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': API_HOST_SEEKING_ALPHA
    }
    size = 20
    page = 1
    all_news_data = []
    seen_ids = set()

    try:
        while True:
            try:
                conn.request(
                    "GET",
                    f"/news/v2/list-by-symbol?size={size}&number={page}&id={symbol}&since={since_timestamp}&until={until_timestamp}",
                    headers=headers
                )
                res = conn.getresponse()
                data = json.loads(res.read().decode("utf-8"))

                if not data['data']:
                    break

                for item in data['data']:
                    if item['id'] not in seen_ids:
                        seen_ids.add(item['id'])
                        all_news_data.append(item)

                page += 1
                time.sleep(0.5)  # Reduced delay for Seeking Alpha API

            except Exception as e:
                error_msg = f"Error fetching articles for {symbol} on page {page}: {e}"
                st.session_state["process_status"].append(error_msg)
                # Record the failure
                st.session_state["failed_symbols"][symbol] = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": f"API error on page {page}: {str(e)}"
                }
                save_failed_symbols()
                return None
    except Exception as e:
        error_msg = f"Fatal error fetching articles for {symbol}: {e}"
        st.session_state["process_status"].append(error_msg)
        # Record the failure
        st.session_state["failed_symbols"][symbol] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reason": f"Fatal error: {str(e)}"
        }
        save_failed_symbols()
        return None

    # Mark this symbol as processed for Seeking Alpha
    if symbol not in st.session_state["processed_symbols_seeking_alpha"]:
        st.session_state["processed_symbols_seeking_alpha"].add(symbol)
        st.session_state["stocks_processed_with_current_key_seeking_alpha"] += 1
        
    return all_news_data

# New function to fetch content summary from Perplexity API - now using Perplexity specific key rotation
def fetch_content_summary(symbol, title, publish_date):
    # Check if we need to rotate the Perplexity key
    if symbol not in st.session_state["processed_symbols_perplexity"] and st.session_state["stocks_processed_with_current_key_perplexity"] >= st.session_state["stocks_per_key_perplexity"]:
        rotate_to_next_perplexity_key()
    
    api_key = get_current_perplexity_key()
    
    if not api_key.strip():
        st.error("API key is missing! Please enter a valid key.")
        return "API key missing"

    conn = http.client.HTTPSConnection(API_HOST_PERPLEXITY)
    
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': API_HOST_PERPLEXITY,
        'Content-Type': "application/json"
    }
    
    # Format the query to ask about the news article using the template
    query = summary_prompt_template.replace("{title}", title).replace("{date}", str(publish_date))
    
    # Payload with just the content parameter
    payload = json.dumps({
        "content": query
    })
    
    try:
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        # Parse the response
        try:
            json_data = json.loads(data)
            
            # Extract the summary from the nested JSON structure
            if "choices" in json_data and "content" in json_data["choices"] and "parts" in json_data["choices"]["content"]:
                parts = json_data["choices"]["content"]["parts"]
                if parts and len(parts) > 0 and "text" in parts[0]:
                    return parts[0]["text"]
            
            # Fallback to other possible response formats
            if "answer" in json_data:
                return json_data["answer"]
                
            # If we can't find the expected structure, return a diagnostic message
            return f"API response structure unexpected. Raw response (truncated): {str(json_data)[:500]}"
            
        except json.JSONDecodeError:
            # If response is not JSON, return the raw text (truncated)
            return f"Non-JSON response: {data[:500]}"
            
    except Exception as e:
        st.session_state["process_status"].append(f"Error fetching summary for '{title}': {e}")
        return f"Error: {str(e)}"

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        if not get_current_seeking_alpha_key().strip():
            st.error("Please enter at least one valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            st.session_state["articles_fetched"] = False
            st.session_state["content_fetched"] = False
            st.session_state["processed_symbols_seeking_alpha"] = set()
            st.session_state["current_key_index_seeking_alpha"] = 0
            st.session_state["stocks_processed_with_current_key_seeking_alpha"] = 0
            
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

            # Display key status
            key_status = st.empty()
            key_status.text(f"Using API key {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['api_keys'])} for Seeking Alpha | " +
                           f"Processed {st.session_state['stocks_processed_with_current_key_seeking_alpha']} of {st.session_state['stocks_per_key_seeking_alpha']} stocks with current key")

            for symbol in symbols:
                st.session_state["process_status"].append(f"Fetching articles for: {symbol} (Using API key {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['api_keys'])} for Seeking Alpha)")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)
                
                # Update key status after each symbol
                key_status.text(f"Using API key {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['api_keys'])} for Seeking Alpha | " +
                               f"Processed {st.session_state['stocks_processed_with_current_key_seeking_alpha']} of {st.session_state['stocks_per_key_seeking_alpha']} stocks with current key")
                
                if articles:
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
                        save_failed_symbols()
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": "API Error"
                    })
                    st.session_state["process_status"].append(f"Failed to fetch articles for {symbol}")
                    
                    # Already recorded in fetch_articles function
            
            st.session_state["articles_fetched"] = True
            st.success("Articles fetched successfully! You can now fetch content summaries.")

with col2:
    # New button to fetch content summaries
    if st.button("Fetch Content", disabled=not st.session_state["articles_fetched"]):
        st.session_state["process_status"].append("Starting to fetch content summaries...")
        st.session_state["current_key_index_perplexity"] = 0
        st.session_state["stocks_processed_with_current_key_perplexity"] = 0
        st.session_state["processed_symbols_perplexity"] = set()
        
        csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
        total_summaries = 0
        
        progress_bar = st.progress(0)
        total_articles = sum([len(pd.read_csv(os.path.join(dirs["articles"], f))) for f in csv_files])
        processed_articles = 0
        
        start_time = time.time()
        eta_display = st.empty()
        key_status = st.empty()
        
        # Update key status display
        key_status.text(f"Using API key {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['api_keys'])} for Perplexity | " +
                        f"Processed {st.session_state['stocks_processed_with_current_key_perplexity']} of {st.session_state['stocks_per_key_perplexity']} stocks with current key")
        
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            
            st.session_state["process_status"].append(f"Fetching summaries for {symbol} (Using API key {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['api_keys'])} for Perplexity)")
            
            # Read the CSV file
            file_path = os.path.join(dirs["articles"], csv_file)
            df = pd.read_csv(file_path)
            
            # Add summaries for each article
            for index, row in df.iterrows():
                title = row['Title']
                publish_date = row['Publish Date']
                
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
                
                st.session_state["process_status"].append(f"Fetching summary for: {title}")
                summary = fetch_content_summary(symbol, title, formatted_date)
                df.at[index, 'Summary'] = summary
                total_summaries += 1
                
                # Update progress
                processed_articles += 1
                progress_percentage = processed_articles / total_articles
                progress_bar.progress(progress_percentage)
                
                # Calculate and display ETA
                if processed_articles > 0:
                    elapsed_time = time.time() - start_time
                    articles_per_second = processed_articles / elapsed_time
                    remaining_articles = total_articles - processed_articles
                    eta_seconds = remaining_articles / articles_per_second if articles_per_second > 0 else 0
                    
                    # Format ETA nicely
                    if eta_seconds < 60:
                        eta_text = f"{eta_seconds:.0f} seconds"
                    elif eta_seconds < 3600:
                        eta_text = f"{eta_seconds/60:.1f} minutes"
                    else:
                        eta_text = f"{eta_seconds/3600:.1f} hours"
                    
                    eta_display.text(f"Progress: {processed_articles}/{total_articles} articles | ETA: {eta_text}")
                
                # Add a delay to avoid rate limiting - using the user-configurable delay
                time.sleep(st.session_state["delay_between_calls"])
            
            # Save the updated DataFrame back to CSV
            df.to_csv(file_path, index=False)
            st.session_state["process_status"].append(f"Saved {len(df)} summaries for {symbol}")
            
            # Mark this symbol as processed for Perplexity
            if symbol not in st.session_state["processed_symbols_perplexity"]:
                st.session_state["processed_symbols_perplexity"].add(symbol)
                st.session_state["stocks_processed_with_current_key_perplexity"] += 1
                # Update key status display
                key_status.text(f"Using API key {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['api_keys'])} for Perplexity | " +
                               f"Processed {st.session_state['stocks_processed_with_current_key_perplexity']} of {st.session_state['stocks_per_key_perplexity']} stocks with current key")
        
        elapsed_time = time.time() - start_time
        st.session_state["content_fetched"] = True
        st.success(f"Content summaries fetched successfully! Added {total_summaries} summaries in {elapsed_time:.1f} seconds.")

with col3:
    if st.button("Clean Up"):
        # Ask for confirmation
        if st.checkbox("I understand this will delete all downloaded files. Proceed?", value=False):
            st.session_state["process_status"] = []
            st.session_state["process_status"].append("Starting cleanup...")
            
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
            st.warning("Cleanup cancelled. Please check the confirmation box to proceed.")

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

# Display API key usage
with st.expander("API Key Usage"):
    st.write("### Seeking Alpha API")
    st.write(f"Current key index: {st.session_state['current_key_index_seeking_alpha'] + 1} of {len(st.session_state['api_keys'])}")
    st.write(f"Stocks processed with current key: {st.session_state['stocks_processed_with_current_key_seeking_alpha']} of {st.session_state['stocks_per_key_seeking_alpha']}")
    st.write(f"Total stocks processed: {len(st.session_state['processed_symbols_seeking_alpha'])}")
    
    st.write("### Perplexity API")
    st.write(f"Current key index: {st.session_state['current_key_index_perplexity'] + 1} of {len(st.session_state['api_keys'])}")
    st.write(f"Stocks processe  + 1} of {len(st.session_state['api_keys'])}")
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

# Download Section
if os.path.exists(dirs["articles"]):
    csv_files = [f for f in os.listdir(dirs["articles"]) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### Download Extracted Files")
        cols = st.columns(3)
        for i, csv_file in enumerate(csv_files):
            with cols[i % 3]:
                with open(os.path.join(dirs["articles"], csv_file), "r") as f:
                    st.download_button(
                        label=f"Download {csv_file}",
                        data=f.read(),
                        file_name=csv_file,
                        mime="text/csv"
                    )
    else:
        st.warning("No CSV files found in the output directory.")
else:
    st.warning("Output directory does not exist.")

# Display storage information
with st.expander("Storage Information"):
    # Calculate storage usage
    total_size = 0
    file_count = 0
    
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
    
    # Show directory structure
    st.write("### Directory Structure:")
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
