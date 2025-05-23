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

# Configuration
DEFAULT_API_KEY = "4eab47a1bfmsh51c8a20cf14a71fp13947bjsnbff888983296"  # Default placeholder
API_HOST_SEEKING_ALPHA = "seeking-alpha.p.rapidapi.com"
API_HOST_PERPLEXITY = "perplexity2.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdirect"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

# Streamlit UI
st.title("News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and process them.")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "RapidAPI Key",
    value=st.session_state["api_key"],
    type="password",
    help="Default key is rate-limited. Replace with your own RapidAPI key. This key will be used for both Seeking Alpha and Perplexity APIs."
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

# Fetch articles function
def fetch_articles(symbol, since_timestamp, until_timestamp):
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
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
            st.session_state["process_status"].append(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

# New function to fetch content summary from Perplexity API - simplified with no retries
def fetch_content_summary(title, publish_date):
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return "API key missing"

    conn = http.client.HTTPSConnection(API_HOST_PERPLEXITY)
    
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
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
    from_date = st.date_input("From Date", value=datetime(2025, 4, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2025, 4, 30))

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Fetch Articles"):
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            st.session_state["articles_fetched"] = False
            st.session_state["content_fetched"] = False
            
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

            for symbol in symbols:
                st.session_state["process_status"].append(f"Fetching articles for: {symbol}")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)
                if articles:
                    file_name = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_news_data.csv")
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
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": "API Error"
                    })
                    st.session_state["process_status"].append(f"Failed to fetch articles for {symbol}")
            
            st.session_state["articles_fetched"] = True
            st.success("Articles fetched successfully! You can now fetch content summaries.")

with col2:
    # New button to fetch content summaries
    if st.button("Fetch Content", disabled=not st.session_state["articles_fetched"]):
        st.session_state["process_status"].append("Starting to fetch content summaries...")
        
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        total_summaries = 0
        
        progress_bar = st.progress(0)
        total_articles = sum([len(pd.read_csv(os.path.join(OUTPUT_DIR, f))) for f in csv_files])
        processed_articles = 0
        
        start_time = time.time()
        eta_display = st.empty()
        
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            st.session_state["process_status"].append(f"Fetching summaries for {symbol}")
            
            # Read the CSV file
            file_path = os.path.join(OUTPUT_DIR, csv_file)
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
                summary = fetch_content_summary(title, formatted_date)
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
        
        elapsed_time = time.time() - start_time
        st.session_state["content_fetched"] = True
        st.success(f"Content summaries fetched successfully! Added {total_summaries} summaries in {elapsed_time:.1f} seconds.")

with col3:
    if st.button("Clean Up"):
        st.session_state["process_status"] = []
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            st.session_state["process_status"].append(f"Cleaning content for {symbol}")
            df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))
            # No 'Content' column to clean now — placeholder logic removed
            st.session_state["process_status"].append(f"Cleanup skipped: no content to clean for {symbol}")

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
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    
    # Create tabs for each symbol
    if csv_files:
        tabs = st.tabs([f.replace("_news_data.csv", "").upper() for f in csv_files])
        
        for i, tab in enumerate(tabs):
            with tab:
                file_path = os.path.join(OUTPUT_DIR, csv_files[i])
                df = pd.read_csv(file_path)
                
                # Display a preview of the summaries
                if 'Summary' in df.columns and not df['Summary'].isna().all():
                    for _, row in df.iterrows():
                        with st.expander(f"{row['Title']} ({row['Publish Date']})"):
                            st.write(row['Summary'])
                else:
                    st.write("No summaries available for this symbol.")

# Download Section
if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### Download Extracted Files")
        cols = st.columns(3)
        for i, csv_file in enumerate(csv_files):
            with cols[i % 3]:
                with open(os.path.join(OUTPUT_DIR, csv_file), "r") as f:
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
