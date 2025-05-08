import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime

# Configuration
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"
API_HOST_SA = "seeking-alpha.p.rapidapi.com"
API_HOST_PERPLEXITY = "perplexity-api.p.rapidapi.com"
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

# Streamlit UI
st.title("📰 Seeking Alpha News Fetcher + Perplexity Summary")
st.write("Fetch financial news for stock symbols and generate smart summaries.")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "RapidAPI Key (used for both Seeking Alpha & Perplexity)",
    value=st.session_state["api_key"],
    type="password",
    help="Used for both APIs. Replace the default key with your own if needed."
)

# Date range inputs
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Function to fetch articles from Seeking Alpha
def fetch_articles(symbol, since_timestamp, until_timestamp):
    conn = http.client.HTTPSConnection(API_HOST_SA)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': API_HOST_SA
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
            st.session_state["process_status"].append(f"❌ Error fetching articles for {symbol}: {e}")
            return None

    return all_news_data

# Function to get a summary from Perplexity
def get_news_summary_from_perplexity(title, publish_date):
    conn = http.client.HTTPSConnection(API_HOST_PERPLEXITY)
    prompt = {
        "content": f"Do you know about the news titled '{title}' published on {publish_date}? Please summarize what this news is about."
    }
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': API_HOST_PERPLEXITY,
        'Content-Type': "application/json"
    }

    try:
        conn.request("POST", "/", json.dumps(prompt), headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        return data.get("text", "Summary not available")
    except Exception as e:
        return f"Error fetching summary: {e}"

# Fetch articles button
col1, col2 = st.columns(2)
with col1:
    if st.button("📥 Fetch Articles"):
        if not st.session_state["api_key"].strip():
            st.error("❗ Please enter a valid RapidAPI key!")
        else:
            st.session_state["status_table"] = []
            st.session_state["process_status"] = []

            with open(SYMBOL_FILE, "r") as f:
                symbols = [line.strip() for line in f.readlines()]

            for symbol in symbols:
                st.session_state["process_status"].append(f"🔍 Fetching articles for: {symbol}")
                articles = fetch_articles(symbol, since_timestamp, until_timestamp)

                if articles:
                    file_name = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_news_data.csv")
                    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['ID', 'Publish Date', 'Title', 'Author ID', 'Comment Count', 'Summary']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()

                        for item in articles:
                            title = item['attributes']['title']
                            publish_date = item['attributes']['publishOn']
                            summary = get_news_summary_from_perplexity(title, publish_date)
                            time.sleep(1.5)  # avoid Perplexity rate limit

                            writer.writerow({
                                'ID': item['id'],
                                'Publish Date': publish_date,
                                'Title': title,
                                'Author ID': item['relationships']['author']['data']['id'],
                                'Comment Count': item['attributes']['commentCount'],
                                'Summary': summary
                            })

                            st.session_state["process_status"].append(f"✅ {symbol} → {title[:60]}... → Summary added.")
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": len(articles)
                    })
                else:
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Number of Articles Extracted": "API Error"
                    })

with col2:
    if st.button("🧹 Clean Up"):
        st.session_state["process_status"] = []
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_data.csv", "")
            st.session_state["process_status"].append(f"🧽 Skipped cleanup for {symbol} (no content column).")

# Show process log
if st.session_state["process_status"]:
    st.write("### 🪵 Process Log")
    for status in st.session_state["process_status"]:
        st.write(status)

# Show summary table
if st.session_state["status_table"]:
    st.write("### ✅ Fetch Summary")
    st.table(pd.DataFrame(st.session_state["status_table"]))

# Download buttons
if os.path.exists(OUTPUT_DIR):
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_news_data.csv")]
    if csv_files:
        st.write("### ⬇️ Download News Files")
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
        st.warning("⚠️ No CSV files found.")
else:
    st.warning("⚠️ Output directory does not exist.")
