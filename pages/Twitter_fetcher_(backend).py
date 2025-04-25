import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
from datetime import datetime

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

# Ensure output directories exist
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "combined_keywords" not in st.session_state:
    st.session_state["combined_keywords"] = {}
if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = None
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY

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

def fetch_tweets_for_keyword(keyword, start_date, end_date):
    """Fetch tweets for a specific keyword from the API"""
    if not st.session_state["api_key"].strip():
        st.error("API key is missing! Please enter a valid key.")
        return None

    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': st.session_state["api_key"],
        'x-rapidapi-host': API_HOST
    }
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    api_query = format_keyword_for_api(keyword)
    endpoint = f"/search/search?query={api_query}&section=latest&min_retweets=1&min_likes=1&limit=50&start_date={start_date_str}&language=en&end_date={end_date_str}"
    
    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None
    finally:
        conn.close()

def fetch_tweets(start_date, end_date, keywords_to_fetch):
    """Fetch tweets for specified keywords"""
    if not keywords_to_fetch:
        st.warning("No keywords selected to fetch")
        return
    if not st.session_state["api_key"].strip():
        st.error("API key is missing!")
        return

    status_placeholder = st.empty()

    for keyword in keywords_to_fetch:
        try:
            display_keyword = keyword.replace("+", " ")
            status_placeholder.write(f"Fetching tweets for: {display_keyword}")
            result = fetch_tweets_for_keyword(keyword, start_date, end_date)

            if not result:
                continue

            sanitized_keyword = keyword.replace(" ", "_").replace("/", "_").replace("+", "_")
            output_file = os.path.join(JSON_OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)

            keyword_type = "Combined" if any(keyword in combos for combos in st.session_state["combined_keywords"].values()) else "Base"
            
            st.session_state["status_table"].append({
                "Keyword": display_keyword,
                "Type": keyword_type,
                "Tweet Extract JSON": "✅",
                "CSV Output": "❌",
                "Date Range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            })

            status_placeholder.write(f"Saved tweets for: {display_keyword}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword.replace('+', ' ')}': {e}")

    status_placeholder.empty()

def convert_json_to_csv():
    """Convert all JSON files to CSV"""
    if not os.path.exists(JSON_OUTPUT_DIR):
        st.warning("No JSON files found. Please fetch tweets first.")
        return

    json_files = [f for f in os.listdir(JSON_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No JSON files found in the output directory.")
        return

    status_placeholder = st.empty()

    for json_file in json_files:
        try:
            status_placeholder.write(f"Converting {json_file} to CSV...")

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
            for entry in st.session_state["status_table"]:
                if entry["Keyword"] == keyword:
                    entry["CSV Output"] = "✅"
                    break

        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")

    status_placeholder.empty()

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
        st.success("Temporary files cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing temporary files: {e}")

# Streamlit UI
st.title("Twitter Data Fetcher")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "Twitter API Key",
    value=st.session_state["api_key"],
    type="password",
    help="Default key is rate-limited. Replace with your own RapidAPI key."
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
            fetch_tweets(start_date, end_date, base_keywords)
        else:
            st.warning("Invalid date range or no base keywords!")

with col2:
    if st.button("Fetch All Combined Keywords"):
        if start_date <= end_date and st.session_state["combined_keywords"]:
            all_combined = []
            for combos in st.session_state["combined_keywords"].values():
                all_combined.extend(combos)
            fetch_tweets(start_date, end_date, all_combined)
        else:
            st.warning("Invalid date range or no combined keywords!")

with col3:
    if st.button("Convert JSON to CSV"):
        convert_json_to_csv()

with col4:
    if st.button("Clear Temp"):
        clear_temp()

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
