import requests
import csv
import os
import pandas as pd
import streamlit as st

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "meta-llama-3-8b.p.rapidapi.co"  # API host
COMPANY_NAMES_FILE = "twitterdir/comp_names.txt"  # Path to the company names file
KEYWORDS_OUTPUT_DIR = "/tmp/gtrendsdisssr/output"  # Directory to save keyword CSV files

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

# Define the API endpoint and headers
url = f"https://{API_HOST}/chatgpt"
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
    "Content-Type": "application/json"
}

# Button to start fetching keywords
if st.button("Fetch Keywords"):
    st.write("Fetching keywords...")

    # Loop through each company to get the keywords
    for company in companies_list:
        csv_filename = f"{company.lower().replace(' ', '_')}_chatgpt_keywords.csv"

        # Prepare the payload for the API request
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Provide a list of top fifteen important keywords associated with the company \"{company}\", focusing on its most popular products, services, or core offerings. The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. Ensure the keywords are specific, and highly representative of the company's primary focus. Give the output as a bulletted list with no other extra characters or text."
                    )
                }
            ],
            "web_access": False
        }

        # Make the API request
        response = requests.post(url, json=payload, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            response_data = response.json()

            try:
                # Extract and clean the list of keywords
                keywords_str = response_data['result']
                keywords_list = keywords_str.split("\n")[3:13]  # Extract only the keywords
                keywords_list = [kw.strip().split('. ')[-1] for kw in keywords_list]

                # Write the keywords to a CSV file in the output folder
                csv_path = os.path.join(KEYWORDS_OUTPUT_DIR, csv_filename)
                with open(csv_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['chatgpt'])  # Write the header
                    for keyword in keywords_list:
                        writer.writerow([keyword])

                st.success(f"Keywords for '{company}' saved to {csv_path}")

            except KeyError as e:
                st.error(f"KeyError for '{company}': {e}. Please check the response structure.")

        else:
            st.error(f"Failed to retrieve data for '{company}'. Status code: {response.status_code}")

    st.write("Keyword fetching completed!")

# Display the list of companies
st.write("### List of Companies")
st.write(companies_list)

# Display the output directory contents
if os.path.exists(KEYWORDS_OUTPUT_DIR):
    st.write("### Output Directory Contents")
    output_files = os.listdir(KEYWORDS_OUTPUT_DIR)
    if output_files:
        st.write(output_files)
    else:
        st.warning("No output files found in the directory.")
else:
    st.warning("Output directory does not exist.")
