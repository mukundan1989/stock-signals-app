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
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
API_HOST = "seeking-alpha.p.rapidapi.com"
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

def fetch_articles(symbol, since_timestamp, until_timestamp):
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': API_HOST
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

def fetch_content_from_perplexity(title, publish_date):
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection("perplexity2.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': "perplexity2.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    prompt = {
        "content": f"Give full details about the news article titled '{title}' published on {publish_date}."
    }

    try:
        conn.request("POST", "/", json.dumps(prompt), headers)
        res = conn.getresponse()
        result = res.read().decode("utf-8")
        data = json.loads(result)

        # Safely extract final answer
        if (
            "choices" in data and
            "content" in data["choices"] and
            "parts" in data["choices"]["content"]
        ):
            parts = data["choices"]["content"]["parts"]
            if isinstance(parts, list) and parts:
                return parts[-1].get("text", "").strip()

        # fallback if structure fails
        return None

    except Exception as e:
        st.session_state["process_status"].append(f"Error fetching content from Perplexity for '{title}': {e}")
        return None

def clean_html(raw_html):
    clean_regex = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(clean_regex, '', raw_html)

def extract_content(full_data):
    try:
        if not full_data or pd.isna(full_data):
            return None

        cleaned_content = clean_html(full_data)
        cleaned_content = ' '.join(cleaned_content.split())

        ending_markers = [
            r"\bMore on\b", r"\bRead more\b", r"\bSee also\b",
            r"\bLearn more\b", r"\bRelated articles\b",
            r"\bThis article was\b", r"\bOriginal post\b"
        ]

        earliest_pos = len(cleaned_content)
        for marker in ending_markers:
            match = re.search(marker, cleaned_content, re.IGNORECASE)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()

        if earliest_pos < len(cleaned_content):
            cleaned_content = cleaned_content[:earliest_pos]

        cleaned_content = re.sub(r"Editor's Note:.*$", '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r"SA Transcripts.*$", '', cleaned_content, flags=re.DOTALL)

        return cleaned_content.strip()
    except Exception as e:
        st.session_state["process_status"].append(f"Content extraction error: {e}")
        return None

def clear_temp_storage():
    try:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        return True
    except Exception as e:
        st.error(f"Error clearing temp storage: {e}")
        return False

# Streamlit UI
st.title("Seeking Alpha News Fetcher (with Perplexity Content)")

st.session_state["api_key"] = st.text_input(
    "RapidAPI Key",
    value=st.session_state["api_key"],
    type="password",
    help="Required for both Seeking Alpha and Perplexity APIs."
)

col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

status_placeholder = st.empty()
proc_col, util_col = st.columns([3, 1])

with proc_col:
    if st.button("Start Full Processing"):
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []

            with open(SYMBOL_FILE, "r") as f:
                symbols = [line.strip() for line in f.readlines()]

            status_placeholder.write("\U0001F680 Starting article fetching process...")

            for symbol in symbols:
                status_placeholder.write(f"⏳ Fetching articles for: {symbol}")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)

                if articles:
                    file_name = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_news_data.csv")
                    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['ID', 'Publish Date', 'Title', 'Author ID', 'Comment Count',
                                      'Primary Tickers', 'Secondary Tickers', 'Image URL']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in articles:
                            writer.writerow({
                                'ID': item['id'],
                                'Publish Date': item['attributes']['publishOn'],
                                'Title': item['attributes']['title'],
                                'Author ID': item['relationships']['author']['data']['id'],
                                'Comment Count': item['attributes']['commentCount'],
                                'Primary Tickers': ', '.join([t['type'] for t in item['relationships']['primaryTickers']['data']]),
                                'Secondary Tickers': ', '.join([t['type'] for t in item['relationships']['secondaryTickers']['data']]),
                                'Image URL': item['attributes'].get('gettyImageUrl', 'N/A')
                            })
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": len(articles)
                    })
                    st.session_state["process_status"].append(f"✅ Saved {len(articles)} articles for {symbol}")
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": "API Error"
                    })
                    st.session_state["process_status"].append(f"❌ Failed to fetch articles for {symbol}")

            status_placeholder.write("✔️ Article fetching complete! Starting content fetching...")

            csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
            for csv_file in csv_files:
                symbol = csv_file.replace("_news_data.csv", "")
                status_placeholder.write(f"⏳ Fetching content for: {symbol}")
                df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))

                if 'Content' not in df.columns:
                    df['Content'] = None

                for index, row in df.iterrows():
                    if pd.isna(row['Content']):
                        content = fetch_content_from_perplexity(row['Title'], row['Publish Date'])
                        df.at[index, 'Content'] = content
                        time.sleep(1)

                df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
                st.session_state["process_status"].append(f"✔️ Updated content for {symbol}")

            status_placeholder.write("✔️ Content fetching complete! Starting content cleaning...")

            for csv_file in csv_files:
                symbol = csv_file.replace("_news_data.csv", "")
                status_placeholder.write(f"⏳ Cleaning content for: {symbol}")
                df = pd.read_csv(os.path.join(OUTPUT_DIR, csv_file))

                if 'Content' in df.columns:
                    df['Extracted'] = df['Content'].apply(extract_content)
                    df.to_csv(os.path.join(OUTPUT_DIR, csv_file), index=False)
                    st.session_state["process_status"].append(f"✔️ Cleaned content for {symbol}")

            status_placeholder.write("🎉 All operations completed successfully!")
            st.balloons()
            st.rerun()

with util_col:
    if st.button("Clear Temporary Storage", help="Delete all downloaded files and reset status"):
        if clear_temp_storage():
            st.success("Temporary files and status cleared!")
            st.balloons()
            st.rerun()

if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.table(status_df)

if st.session_state["process_status"]:
    st.write("### Process Log")
    for status in st.session_state["process_status"]:
        st.write(status)

if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### Download Processed Files")
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
