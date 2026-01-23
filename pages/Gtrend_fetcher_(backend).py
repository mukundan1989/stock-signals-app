import requests
import csv
import os
import pandas as pd
import streamlit as st
import re  # For cleaning keywords
import time  # For adding delays
import json  # For handling JSON payloads
from serpapi import GoogleSearch  # For fetching Google Trends data

# --- CONFIGURATION ---
# ⚠️ SECURITY WARNING: You should not hardcode keys in production. 
# Consider using st.secrets or environment variables.
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
SERPAPI_KEY = "00d04ad3fedf5a39974184171ae64492e3198cc07ed608cad0af9a780ee6f4c0"  # Your SerpAPI key

# NEW: ChatGPT API Host
API_HOST = "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com"
COMPANY_NAMES_FILE = "data/comp_names.txt"
KEYWORDS_OUTPUT_DIR = "/tmp/datagdata/outputs"
TRENDS_OUTPUT_DIR = "/tmp/datagtrendoutputz/json/outputs"

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TRENDS_OUTPUT_DIR, exist_ok=True)

# Streamlit App Title
st.title("Google Trends Keyword Extractor (GPT-4o Edition)")
st.write("Fetching keywords for companies using GPT-4o and Google Trends data.")

# Read the company names
try:
    with open(COMPANY_NAMES_FILE, "r") as file:
        companies_list = [line.strip() for line in file if line.strip()]
    st.success(f"Successfully read {len(companies_list)} companies from '{COMPANY_NAMES_FILE}'.")
except FileNotFoundError:
    st.error(f"File '{COMPANY_NAMES_FILE}' not found. Please ensure the file exists.")
    st.stop()

# Function to fetch Google Trends data (Unchanged)
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

# Function to split keywords (Unchanged)
def split_keywords(keywords, chunk_size=5):
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]

# Function to fetch Trends for all files (Unchanged)
def fetch_trends_for_all_files():
    st.write("Fetching Google Trends data...")
    data_type = "TIMESERIES"
    date_ranges = ["2020-01-01 2024-11-30"]
    language = "en"
    location = "us"

    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_gpt_keywords.csv" # Renamed suffix to _gpt_keywords
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
                st.success(f"Google Trends data for '{company}' (Part {i + 1}) saved.")
                
        if all_data:
            combined_file_name = csv_filename.replace('.csv', '_trends_combined.json')
            combined_file_path = os.path.join(TRENDS_OUTPUT_DIR, combined_file_name)
            with open(combined_file_path, 'w') as combined_file:
                json.dump(all_data, combined_file, indent=2)
            st.success(f"Combined data saved: {combined_file_path}")

# --- KEYWORD FETCHING LOGIC (UPDATED FOR GPT-4o) ---
if st.button("Fetch Keywords"):
    st.write("Fetching keywords using GPT-4o...")

    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_gpt_keywords.csv"

        # NEW: Payload structure for the ChatGPT API
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Provide a list of top fifteen important keywords associated with the company \"{company}\", focusing on its most popular products, services, or core offerings. The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. Ensure the keywords are specific, and highly representative of the company's primary focus. Give the output as a bulletted list with no other extra characters or text."
                    )
                }
            ],
            "model": "gpt-4o",  # Updated model
            "max_tokens": 300,    # Increased tokens to ensure list isn't cut off
            "temperature": 0.9
        }

        # NEW: Headers with correct host
        headers = {
            'x-rapidapi-key': API_KEY,
            'x-rapidapi-host': API_HOST,
            'Content-Type': 'application/json'
        }

        # NEW: URL endpoint
        url = f"https://{API_HOST}/v1/chat/completions"

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Making request to new URL
                response = requests.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    response_data = response.json()

                    # Extract content (Structure is usually compatible with OpenAI format)
                    keywords_str = response_data['choices'][0]['message']['content']
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
                        writer.writerow(['gpt-4o']) # Updated header
                        for keyword in cleaned_keywords:
                            writer.writerow([keyword])

                    st.success(f"Keywords for '{company}' saved to {csv_path}")
                    break

                elif response.status_code == 429:
                    st.warning(f"Rate limit exceeded for '{company}'. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    st.error(f"Failed for '{company}'. Status: {response.status_code}")
                    st.error(response.text) # Print error details for debugging
                    break

            except Exception as e:
                st.error(f"Error fetching data for '{company}': {e}")
                break
        else:
            st.error(f"Max retries reached for '{company}'.")

        time.sleep(1)

    st.write("Keyword fetching completed!")

# --- DISPLAY & DOWNLOAD (Unchanged logic, updated file references) ---
st.write("### Keyword Files Table")
table_data = []
for company in companies_list:
    csv_filename = f"{company.lower().replace(' ', '_')}_gpt_keywords.csv"
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
    if os.path.exists(csv_path):
        table_data.append({"Company Name": company, "Keyword File Name": csv_filename})
    else:
        table_data.append({"Company Name": company, "Keyword File Name": "File not found"})

st.table(table_data)

st.write("### View Keywords")
selected_file = st.selectbox("Select a keyword file to view:", [row["Keyword File Name"] for row in table_data if row["Keyword File Name"] != "File not found"])

if selected_file:
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, selected_file)
    if os.path.exists(csv_path):
        with open(csv_path, "r") as file:
            reader = csv.reader(file)
            keywords = [row[0] for row in reader if row]
        st.write(f"Keywords in '{selected_file}':")
        st.write(keywords)

st.write("### Get Google Trend Values")
if st.button("Get Google Trend Values"):
    fetch_trends_for_all_files()

if os.path.exists(TRENDS_OUTPUT_DIR):
    st.write("### Combined Google Trends Files")
    combined_files = [f for f in os.listdir(TRENDS_OUTPUT_DIR) if f.endswith('_trends_combined.json')]
    if combined_files:
        for file_name in combined_files:
            file_path = os.path.join(TRENDS_OUTPUT_DIR, file_name)
            with open(file_path, "r") as file:
                st.download_button(
                    label=f"Download {file_name}",
                    data=file.read(),
                    file_name=file_name,
                    mime="application/json"
                )
