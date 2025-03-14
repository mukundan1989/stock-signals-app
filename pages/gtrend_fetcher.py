import requests
import csv
import os
import pandas as pd
import streamlit as st
import re  # For cleaning keywords
import time  # For adding delays
import json  # For handling JSON payloads

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "meta-llama-3-8b.p.rapidapi.com"  # API host
COMPANY_NAMES_FILE = "twitterdir/comp_names.txt"  # Path to the company names file
KEYWORDS_OUTPUT_DIR = "/tmp/gtrenssdsdir/output"  # Directory to save keyword CSV files

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)

# Streamlit App Title
st.title("Google Trends Keyword Extractor")
st.write("Fetching keywords for companies listed in 'comp_names.txt'.")

# Read the company names from the text file
try:
    with open(COMPANY_NAMES_FILE, "r") as file:
        companies_list = [line.strip() for line in file if line.strip()]  # Read and clean the company names
    st.success(f"Successfully read {len(companies_list)} companies from '{COMPANY_NAMES_FILE}'.")
except FileNotFoundError:
    st.error(f"File '{COMPANY_NAMES_FILE}' not found. Please ensure the file exists in the 'repo' folder.")
    st.stop()

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
