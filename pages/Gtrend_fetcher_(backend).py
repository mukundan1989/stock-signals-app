import requests
import csv
import os
import streamlit as st
import re  # For cleaning keywords
import time  # For adding delays
import json  # For handling JSON payloads
from serpapi import GoogleSearch  # For fetching Google Trends data

# --- APP LAYOUT & INPUTS ---
st.set_page_config(page_title="Trend Fetcher", layout="wide")

st.sidebar.header("API Configuration")
st.sidebar.info("Enter your API keys here so you don't need to edit the code.")

# 1. Frontend Inputs for Keys
API_KEY = st.sidebar.text_input("RapidAPI Key (Open-AI21)", type="password", help="Paste your RapidAPI key here")
SERPAPI_KEY = st.sidebar.text_input("SerpAPI Key (Google Trends)", type="password", help="Paste your SerpAPI key here")

# API Configuration
API_HOST = "open-ai21.p.rapidapi.com"
COMPANY_NAMES_FILE = "data/comp_names.txt"
KEYWORDS_OUTPUT_DIR = "/tmp/datagdata/outputs"
TRENDS_OUTPUT_DIR = "/tmp/datagtrendoutputz/json/outputs"

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TRENDS_OUTPUT_DIR, exist_ok=True)

# Streamlit App Title
st.title("Google Trends Keyword Extractor")
st.markdown("### Step 1: Generate Keywords")

# 2. Frontend Input for Prompt
default_prompt = (
    'Provide a list of top fifteen important keywords associated with the company "{company}", '
    'focusing on its most popular products, services, or core offerings. '
    'The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. '
    'Ensure the keywords are specific, and highly representative of the company\'s primary focus. '
    'Give the output as a bulletted list with no other extra characters or text.'
)

user_prompt_template = st.text_area(
    "Customize AI Prompt", 
    value=default_prompt, 
    height=150,
    help="Keep the text '{company}' in the prompt. The script will replace it with the actual company names from your file."
)

# Read the company names
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
        st.error("Please enter your SerpAPI Key in the sidebar first!")
        return

    st.write("Fetching Google Trends data...")
    data_type = "TIMESERIES"
    date_ranges = ["2020-01-01 2024-11-30"]
    language = "en"
    location = "us"

    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_ai21_keywords.csv"
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

# --- KEYWORD FETCHING LOGIC ---

if st.button("Fetch Keywords"):
    if not API_KEY:
        st.error("❌ Please enter your RapidAPI Key in the sidebar.")
    elif "{company}" not in user_prompt_template:
        st.error("❌ Your prompt must contain the placeholder '{company}' so the script knows where to insert the name.")
    else:
        st.write("Using Open-AI21 to generate keywords...")
        progress_bar = st.progress(0)
        
        for idx, company in enumerate(companies_list):
            csv_filename = f"{company.lower().replace(' ', '_')}_ai21_keywords.csv"
            
            # 3. Dynamic Prompt formatting
            formatted_prompt = user_prompt_template.replace("{company}", company)

            payload = {
                "messages": [{"role": "user", "content": formatted_prompt}],
                "web_access": False
            }

            headers = {
                'x-rapidapi-key': API_KEY,
                'x-rapidapi-host': API_HOST,
                'Content-Type': 'application/json'
            }

            url = f"https://{API_HOST}/chatgpt"
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        # Parsing Logic
                        keywords_str = ""
                        if 'result' in response_data:
                            keywords_str = response_data['result']
                        elif 'choices' in response_data:
                            keywords_str = response_data['choices'][0]['message']['content']
                        else:
                            keywords_str = str(response_data)

                        # Clean keywords
                        keywords_list = keywords_str.split("\n")
                        cleaned_keywords = []
                        for kw in keywords_list:
                            kw = kw.replace("-", "").replace('"', '')
                            kw = re.sub(r"[^a-zA-Z\s]", "", kw)
                            kw = kw.strip()
                            if kw:
                                cleaned_keywords.append(kw)

                        csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
                        with open(csv_path, mode='w', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(['ai21']) 
                            for keyword in cleaned_keywords:
                                writer.writerow([keyword])

                        st.toast(f"Generated for {company}")
                        break
                    elif response.status_code == 429:
                        time.sleep(2)
                        continue
                    else:
                        st.error(f"Error {response.status_code} for {company}")
                        break
                except Exception as e:
                    st.error(f"Error: {e}")
                    break
            
            # Update progress
            progress_bar.progress((idx + 1) / len(companies_list))
            time.sleep(1)

        st.success("Keyword fetching completed!")

# --- DISPLAY & DOWNLOAD ---
st.markdown("---")
st.markdown("### Step 2: Review & Trends")

# Table Logic
table_data = []
for company in companies_list:
    csv_filename = f"{company.lower().replace(' ', '_')}_ai21_keywords.csv"
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
    if os.path.exists(csv_path):
        table_data.append({"Company": company, "Status": "✅ Ready", "File": csv_filename})
    else:
        table_data.append({"Company": company, "Status": "⚠️ Missing", "File": "N/A"})

st.table(table_data)

# View Keywords
col1, col2 = st.columns([1, 1])
with col1:
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

# Get Trends
with col2:
    st.write("#### Fetch Volume Data")
    if st.button("Get Google Trend Values", type="primary"):
        fetch_trends_for_all_files()

# Download Section
if os.path.exists(TRENDS_OUTPUT_DIR):
    st.markdown("### Step 3: Download Results")
    combined_files = [f for f in os.listdir(TRENDS_OUTPUT_DIR) if f.endswith('_trends_combined.json')]
    if combined_files:
        for file_name in combined_files:
            file_path = os.path.join(TRENDS_OUTPUT_DIR, file_name)
            with open(file_path, "r") as file:
                st.download_button(
                    label=f"📥 Download {file_name}",
                    data=file.read(),
                    file_name=file_name,
                    mime="application/json"
                )
