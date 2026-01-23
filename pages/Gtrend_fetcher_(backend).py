import requests
import csv
import os
import pandas as pd  # Required for CSV conversion
import streamlit as st
import re
import time
import json
from serpapi import GoogleSearch

# --- APP LAYOUT & INPUTS ---
st.set_page_config(page_title="Trend Fetcher", layout="wide")

st.title("Google Trends Keyword Extractor")

# 1. API Configuration
col1, col2 = st.columns(2)
with col1:
    API_KEY = st.text_input("RapidAPI Key (Free ChatGPT)", type="password", help="Paste your RapidAPI key here")
with col2:
    SERPAPI_KEY = st.text_input("SerpAPI Key (Google Trends)", type="password", help="Paste your SerpAPI key here")

# Configuration Constants
API_HOST = "free-chatgpt-api.p.rapidapi.com"
COMPANY_NAMES_FILE = "data/comp_names.txt"
KEYWORDS_OUTPUT_DIR = "/tmp/datagdata/outputs"
TRENDS_OUTPUT_DIR = "/tmp/datagtrendoutputz/json/outputs"

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TRENDS_OUTPUT_DIR, exist_ok=True)

# 2. Prompt Configuration
default_prompt = (
    'Provide a list of top five important keywords associated with the company "{company}", '
    'focusing on its most popular products, services, or core offerings. '
    'The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. '
    'Ensure the keywords are specific, and highly representative of the company\'s primary focus. '
    'Give the output as a bulletted list with no other extra characters or text.'
)

st.write("### AI Prompt Configuration")
user_prompt_template = st.text_area(
    "Customize Prompt", 
    value=default_prompt, 
    height=150,
    help="Keep '{company}' in the prompt."
)

# Read company names
companies_list = []
try:
    with open(COMPANY_NAMES_FILE, "r") as file:
        companies_list = [line.strip() for line in file if line.strip()]
    st.success(f"Loaded {len(companies_list)} companies from '{COMPANY_NAMES_FILE}'.")
except FileNotFoundError:
    st.error(f"File '{COMPANY_NAMES_FILE}' not found. Please ensure the file exists.")
    st.stop()

# --- HELPER FUNCTIONS ---

def fetch_google_trends_data(keywords, data_type, date_range, api_key, language="en", location="us"):
    params = {
        "engine": "google_trends",
        "q": keywords,
        "data_type": data_type,
        "date": date_range,
        "api_key": api_key,
        "hl": language,
        "gl": location
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        st.error(f"Error fetching data for range {date_range}: {e}")
        return None

def split_keywords(keywords, chunk_size=5):
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]

def fetch_trends_for_all_files():
    if not SERPAPI_KEY:
        st.error("Please enter your SerpAPI Key first!")
        return

    st.write("Fetching Google Trends data...")
    data_type = "TIMESERIES"
    date_ranges = ["2020-01-01 2024-11-30"]
    language = "en"
    location = "us"

    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_freegpt_keywords.csv"
        csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)

        if not os.path.exists(csv_path):
            st.warning(f"No keyword file found for '{company}'. Skipping.")
            continue

        with open(csv_path, "r") as file:
            keywords = [row[0] for row in csv.reader(file) if row][1:]

        keyword_chunks = split_keywords(keywords)
        all_data = {}

        for i, chunk in enumerate(keyword_chunks):
            keywords_str = ",".join(chunk)
            trends_data = fetch_google_trends_data(
                keywords_str, data_type, date_ranges[0], SERPAPI_KEY, language, location
            )
            if trends_data:
                all_data[f"part_{i + 1}"] = trends_data
                output_file_name = csv_filename.replace('.csv', f'_part{i + 1}.json')
                output_file_path = os.path.join(TRENDS_OUTPUT_DIR, output_file_name)
                with open(output_file_path, 'w') as output_file:
                    json.dump(trends_data, output_file, indent=2)
                st.info(f"Saved Part {i + 1} for '{company}'")
                
        if all_data:
            combined_file_name = csv_filename.replace('.csv', '_trends_combined.json')
            combined_file_path = os.path.join(TRENDS_OUTPUT_DIR, combined_file_name)
            with open(combined_file_path, 'w') as combined_file:
                json.dump(all_data, combined_file, indent=2)
            st.success(f"✅ Finished: {company}")

# Helper to convert JSON structure to CSV
def convert_json_to_csv(json_path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        all_frames = []
        
        # Iterate through parts (Part 1, Part 2...)
        for part_name, content in data.items():
            if 'interest_over_time' in content and 'timeline_data' in content['interest_over_time']:
                timeline = content['interest_over_time']['timeline_data']
                
                rows = []
                for point in timeline:
                    # Create a row with the date
                    row_data = {'date': point.get('date')}
                    # Extract values for each keyword in this chunk
                    for value_item in point.get('values', []):
                        row_data[value_item['query']] = value_item.get('extracted_value')
                    rows.append(row_data)
                
                if rows:
                    df = pd.DataFrame(rows)
                    # Convert date to datetime objects for proper sorting/merging
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    all_frames.append(df)

        if all_frames:
            # Merge all parts horizontally (aligning by date)
            final_df = pd.concat(all_frames, axis=1)
            # Remove duplicate columns (if any)
            final_df = final_df.loc[:, ~final_df.columns.duplicated()]
            return final_df.to_csv()
        else:
            return None
    except Exception as e:
        return f"Error: {e}"

# --- KEYWORD FETCHING LOGIC ---
if st.button("Fetch Keywords"):
    if not API_KEY:
        st.error("❌ Please enter your RapidAPI Key above.")
    elif "{company}" not in user_prompt_template:
        st.error("❌ Your prompt must contain '{company}'.")
    else:
        st.write("Generating keywords...")
        progress_bar = st.progress(0)
        
        for idx, company in enumerate(companies_list):
            csv_filename = f"{company.lower().replace(' ', '_')}_freegpt_keywords.csv"
            formatted_prompt = user_prompt_template.replace("{company}", company)

            querystring = {"prompt": formatted_prompt}
            headers = {
                'x-rapidapi-key': API_KEY,
                'x-rapidapi-host': API_HOST
            }
            url = f"https://{API_HOST}/chat-completion-one"
            
            for attempt in range(3):
                try:
                    response = requests.get(url, headers=headers, params=querystring)
                    if response.status_code == 200:
                        response_data = response.json()
                        keywords_str = ""
                        
                        if isinstance(response_data, str): keywords_str = response_data
                        elif 'response' in response_data: keywords_str = response_data['response']
                        else: keywords_str = str(response_data)

                        keywords_list = keywords_str.split("\n")
                        cleaned_keywords = []
                        for kw in keywords_list:
                            kw = kw.replace("-", "").replace("*", "").replace('"', '')
                            kw = re.sub(r"[^a-zA-Z\s]", "", kw)
                            kw = kw.strip()
                            if kw: cleaned_keywords.append(kw)

                        csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
                        with open(csv_path, mode='w', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(['freegpt']) 
                            for keyword in cleaned_keywords:
                                writer.writerow([keyword])

                        st.toast(f"Generated for {company}")
                        break
                    elif response.status_code == 429:
                        time.sleep(2)
                        continue
                    else:
                        st.error(f"Error {response.status_code}")
                        break
                except Exception as e:
                    st.error(f"Error: {e}")
                    break
            
            progress_bar.progress((idx + 1) / len(companies_list))
            time.sleep(1)
        st.success("Keyword fetching completed!")

# --- DISPLAY & DOWNLOAD ---
st.markdown("---")
st.write("### Keyword Review & Trends")

table_data = []
for company in companies_list:
    csv_filename = f"{company.lower().replace(' ', '_')}_freegpt_keywords.csv"
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
    if os.path.exists(csv_path):
        table_data.append({"Company": company, "Status": "✅ Ready", "File": csv_filename})
    else:
        table_data.append({"Company": company, "Status": "⚠️ Missing", "File": "N/A"})

st.table(table_data)

col_view, col_action = st.columns([1, 1])
with col_view:
    st.write("#### Inspect Keywords")
    available_files = [row["File"] for row in table_data if row["File"] != "N/A"]
    if available_files:
        selected_file = st.selectbox("Select file:", available_files)
        if selected_file:
            csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, selected_file)
            with open(csv_path, "r") as file:
                reader = csv.reader(file)
                keywords = [row[0] for row in reader if row]
            st.caption(f"Found {len(keywords)} keywords")
            st.dataframe(keywords, height=200)

with col_action:
    st.write("#### Fetch Volume Data")
    if st.button("Get Google Trend Values", type="primary"):
        fetch_trends_for_all_files()

# --- DOWNLOAD SECTION ---
if os.path.exists(TRENDS_OUTPUT_DIR):
    combined_files = [f for f in os.listdir(TRENDS_OUTPUT_DIR) if f.endswith('_trends_combined.json')]
    
    if combined_files:
        col_json, col_csv = st.columns(2)
        
        # JSON Downloads
        with col_json:
            st.markdown("### Download Results (JSON)")
            for file_name in combined_files:
                file_path = os.path.join(TRENDS_OUTPUT_DIR, file_name)
                with open(file_path, "r") as file:
                    st.download_button(
                        label=f"📥 JSON: {file_name}",
                        data=file.read(),
                        file_name=file_name,
                        mime="application/json",
                        key=f"json_{file_name}"
                    )
        
        # CSV Downloads
        with col_csv:
            st.markdown("### Download Results (CSV)")
            for file_name in combined_files:
                file_path = os.path.join(TRENDS_OUTPUT_DIR, file_name)
                
                # Convert on the fly
                csv_data = convert_json_to_csv(file_path)
                
                if csv_data and not csv_data.startswith("Error"):
                    csv_filename = file_name.replace('.json', '.csv')
                    st.download_button(
                        label=f"📊 CSV: {csv_filename}",
                        data=csv_data,
                        file_name=csv_filename,
                        mime="text/csv",
                        key=f"csv_{file_name}"
                    )
                else:
                    st.error(f"Could not convert {file_name}")
