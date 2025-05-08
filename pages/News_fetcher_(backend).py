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
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Default placeholder
API_HOST_SEEKING_ALPHA = "seeking-alpha.p.rapidapi.com"
API_HOST_PERPLEXITY = "perplexity-api.p.rapidapi.com"  # Corrected API host
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdire"
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

# Streamlit UI
st.title("Seeking Alpha News Fetcher")
st.write("Fetch news articles for symbols listed in 'symbollist.txt' and process them.")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "RapidAPI Key",
    value=st.session_state["api_key"],
    type="password",
    help="Default key is rate-limited. Replace with your own RapidAPI key. This key will be used for both Seeking Alpha and Perplexity APIs."
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
            time.sleep(1)

        except Exception as e:
            st.session_state["process_status"].append(f"Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

# New function to fetch content summary from Perplexity API
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
    
    # Format the query to ask about the news article
    query = f"Do you know about '{title}' news published on {publish_date}? Provide a brief summary in 2-3 sentences."
    
    # Corrected payload structure based on the sample
    payload = json.dumps({
        "content": query
    })
    
    try:
        # Corrected endpoint to "/"
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        # Parse the response
        try:
            json_data = json.loads(data)
            # Extract the summary from the response
            if isinstance(json_data, dict) and 'answer' in json_data:
                return json_data['answer']
            else:
                return data[:500]  # Return first 500 chars if structure is unexpected
        except json.JSONDecodeError:
            # If response is not JSON, return the raw text (truncated)
            return data[:500]
            
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
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []
            st.session_state["articles_fetched"] = False
            st.session_state["content_fetched"] = False
            
            with open(SYMBOL_FILE, "r") as f:
                symbols = [line.strip() for line in f.readlines()]

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
                progress_bar.progress(processed_articles / total_articles)
                
                # Add a delay to avoid rate limiting
                time.sleep(1.5)
            
            # Save the updated DataFrame back to CSV
            df.to_csv(file_path, index=False)
            st.session_state["process_status"].append(f"Saved {len(df)} summaries for {symbol}")
        
        st.session_state["content_fetched"] = True
        st.success(f"Content summaries fetched successfully! Added {total_summaries} summaries.")

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
