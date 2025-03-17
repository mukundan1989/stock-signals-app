import requests
import csv
import os
import pandas as pd
import streamlit as st
import re  # For cleaning keywords
import time  # For adding delays
import json  # For handling JSON payloads
from serpapi import GoogleSearch  # For fetching Google Trends data

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4fc681388b27"  # Your RapidAPI key for Llama API
SERPAPI_KEY = "85f1efaedeed8b213c459d6973f27ba731ec82ab6612bad27a6e37ebd1164df1"  # Your SerpAPI key
API_HOST = "meta-llama-3-8b.p.rapidapi.com"  # API host for Llama API
COMPANY_NAMES_FILE = "data/comp_names.txt"  # Path to the company names file
KEYWORDS_OUTPUT_DIR = "/tmp/datagdata/output"  # Directory to save keyword CSV files
TRENDS_OUTPUT_DIR = "/tmp/datagtrendoutputz/json/output"  # Directory to save Google Trends JSON files

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TRENDS_OUTPUT_DIR, exist_ok=True)

# Streamlit App Title
st.title("Google Trends Keyword Extractor")
st.write("Fetching keywords for companies listed in 'comp_names.txt' and Google Trends data.")

# Read the company names from the text file
try:
    with open(COMPANY_NAMES_FILE, "r") as file:
        companies_list = [line.strip() for line in file if line.strip()]  # Read and clean the company names
    st.success(f"Successfully read {len(companies_list)} companies from '{COMPANY_NAMES_FILE}'.")
except FileNotFoundError:
    st.error(f"File '{COMPANY_NAMES_FILE}' not found. Please ensure the file exists in the 'repo' folder.")
    st.stop()

# Function to fetch Google Trends data
def fetch_google_trends_data(keywords, data_type, date_range, api_key, language="en", location="us"):
    """
    Fetch Google Trends data using the provided parameters.

    :param keywords: Comma-separated string of keywords.
    :param data_type: Data type for the trends (e.g., TIMESERIES).
    :param date_range: Date range for the query (e.g., "2023-01-01 2023-12-31").
    :param api_key: API key for the Google Trends API.
    :param language: Language for the trends data (e.g., "en").
    :param location: Location for the trends data (e.g., "us").
    :return: Results as a dictionary, or None in case of an error.
    """
    params = {
        "engine": "google_trends",
        "q": keywords,
        "data_type": data_type,
        "date": date_range,
        "api_key": api_key,
        "hl": language,  # Language parameter
        "gl": location   # Location parameter
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        st.error(f"Error fetching data for range {date_range}: {e}")
        return None

# Function to split keywords into chunks of 5
def split_keywords(keywords, chunk_size=5):
    """
    Split a list of keywords into chunks of a specified size.

    :param keywords: List of keywords.
    :param chunk_size: Size of each chunk (default is 5).
    :return: List of keyword chunks.
    """
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]

# Function to fetch Google Trends data for all keyword files
def fetch_trends_for_all_files():
    """
    Fetch Google Trends data for all keyword files in the output directory.
    """
    st.write("Fetching Google Trends data...")

    data_type = "TIMESERIES"
    date_ranges = ["2020-01-01 2024-11-30"]  # Specify the date range
    language = "en"  # Language for the trends data
    location = "us"  # Location for the trends data

    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_llama_keywords.csv"
        csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)

        if not os.path.exists(csv_path):
            st.warning(f"No keyword file found for '{company}'. Skipping.")
            continue

        # Read keywords from the CSV file
        with open(csv_path, "r") as file:
            keywords = [row[0] for row in csv.reader(file) if row][1:]  # Skip the header

        # Split keywords into chunks of 5
        keyword_chunks = split_keywords(keywords)

        all_data = {}
        for i, chunk in enumerate(keyword_chunks):
            keywords_str = ",".join(chunk)

            # Fetch Google Trends data for the current chunk
            trends_data = fetch_google_trends_data(
                keywords_str, data_type, date_ranges[0], SERPAPI_KEY, language, location
            )

            if trends_data:
                all_data[f"part_{i + 1}"] = trends_data

                # Save the trends data for the current chunk (not displayed for download)
                output_file_name = csv_filename.replace('.csv', f'_part{i + 1}.json')
                output_file_path = os.path.join(TRENDS_OUTPUT_DIR, output_file_name)
                with open(output_file_path, 'w') as output_file:
                    json.dump(trends_data, output_file, indent=2)

                st.success(f"Google Trends data for '{company}' (Part {i + 1}) saved to {output_file_path}")

        # Save the combined data for the company
        if all_data:
            combined_file_name = csv_filename.replace('.csv', '_trends_combined.json')
            combined_file_path = os.path.join(TRENDS_OUTPUT_DIR, combined_file_name)
            with open(combined_file_path, 'w') as combined_file:
                json.dump(all_data, combined_file, indent=2)

            st.success(f"Combined Google Trends data for '{company}' saved to {combined_file_path}")

# Button to start fetching keywords
if st.button("Fetch Keywords"):
    st.write("Fetching keywords...")

    # Loop through each company to get the keywords
    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_llama_keywords.csv"

        # Prepare the payload for the API request
        payload = {
            "model": "llama-3.1-8B-Instruct",  # Specify the model
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Provide a list of top fifteen important keywords associated with the company \"{company}\", focusing on its most popular products, services, or core offerings. The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. Ensure the keywords are specific, and highly representative of the company's primary focus. Give the output as a bulletted list with no other extra characters or text."
                    )
                }
            ]
        }

        # Retry logic for rate limiting
        max_retries = 3  # Maximum number of retries
        retry_delay = 2  # Delay between retries in seconds

        for attempt in range(max_retries):
            try:
                # Make the API request with SSL verification disabled
                response = requests.post(
                    f"https://{API_HOST}/",
                    json=payload,
                    headers={
                        'x-rapidapi-key': API_KEY,
                        'x-rapidapi-host': API_HOST,
                        'Content-Type': 'application/json'
                    },
                    verify=False  # Disable SSL verification
                )

                # Check if the response is successful
                if response.status_code == 200:
                    response_data = response.json()

                    # Extract and clean the list of keywords
                    keywords_str = response_data['choices'][0]['message']['content']  # Extract the response content
                    keywords_list = keywords_str.split("\n")[1:]  # Skip the first line (header)

                    # Clean each keyword
                    cleaned_keywords = []
                    for kw in keywords_list:
                        # Remove hyphens, quotes, and non-alphabetic characters (except spaces)
                        kw = kw.replace("-", "").replace('"', '')  # Remove hyphens and quotes
                        kw = re.sub(r"[^a-zA-Z\s]", "", kw)  # Remove non-alphabetic characters (except spaces)
                        kw = kw.strip()  # Remove leading/trailing spaces
                        if kw:  # Add only non-empty keywords
                            cleaned_keywords.append(kw)

                    # Write the cleaned keywords to a CSV file
                    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
                    with open(csv_path, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['llama'])  # Write the header
                        for keyword in cleaned_keywords:
                            writer.writerow([keyword])

                    st.success(f"Keywords for '{company}' saved to {csv_path}")
                    break  # Exit the retry loop if successful

                elif response.status_code == 429:
                    st.warning(f"Rate limit exceeded for '{company}'. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)  # Wait before retrying
                    continue  # Retry the request

                else:
                    st.error(f"Failed to retrieve data for '{company}'. Status code: {response.status_code}")
                    break  # Exit the retry loop if the error is not rate-limiting

            except Exception as e:
                st.error(f"Error fetching data for '{company}': {e}")
                break  # Exit the retry loop if an unexpected error occurs

        else:
            st.error(f"Max retries ({max_retries}) reached for '{company}'. Skipping.")

        # Add a delay between requests to avoid rate limiting
        time.sleep(1)  # Wait 1 second before the next request

    st.write("Keyword fetching completed!")

# Create a table with Company Name and Keyword File Name
st.write("### Keyword Files Table")

# Initialize a list to store table data
table_data = []

# Loop through companies and check if their keyword files exist
for company in companies_list:
    csv_filename = f"{company.lower().replace(' ', '_')}_llama_keywords.csv"
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)

    # Check if the file exists
    if os.path.exists(csv_path):
        table_data.append({"Company Name": company, "Keyword File Name": csv_filename})
    else:
        table_data.append({"Company Name": company, "Keyword File Name": "File not found"})

# Display the table
st.table(table_data)

# Add functionality to display keywords when a file name is clicked
st.write("### View Keywords")
selected_file = st.selectbox("Select a keyword file to view:", [row["Keyword File Name"] for row in table_data if row["Keyword File Name"] != "File not found"])

if selected_file:
    csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, selected_file)
    if os.path.exists(csv_path):
        with open(csv_path, "r") as file:
            reader = csv.reader(file)
            keywords = [row[0] for row in reader if row]  # Read keywords from the CSV file

        st.write(f"Keywords in '{selected_file}':")
        st.write(keywords)
    else:
        st.error(f"File '{selected_file}' not found.")

# Button to fetch Google Trends data
st.write("### Get Google Trend Values")
if st.button("Get Google Trend Values"):
    fetch_trends_for_all_files()

# Display combined Google Trends files for download
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
    else:
        st.warning("No combined Google Trends files found in the output directory.")
else:
    st.warning("Google Trends output directory does not exist.")
