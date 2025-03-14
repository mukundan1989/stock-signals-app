import requests
import csv
import os
import pandas as pd
import streamlit as st
import re  # For cleaning keywords

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "open-ai21.p.rapidapi.com"  # API host
COMPANY_NAMES_FILE = "twitterdir/comp_names.txt"  # Path to the company names file
KEYWORDS_OUTPUT_DIR = "/tmp/gtrendsdir/output"  # Directory to save keyword CSV files

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
                    writer.writerow(['chatgpt'])  # Write the header
                    for keyword in cleaned_keywords:
                        writer.writerow([keyword])

                st.success(f"Keywords for '{company}' saved to {csv_path}")

            except KeyError as e:
                st.error(f"KeyError for '{company}': {e}. Please check the response structure.")

        else:
            st.error(f"Failed to retrieve data for '{company}'. Status code: {response.status_code}")

    st.write("Keyword fetching completed!")

# Create a table with Company Name and Keyword File Name
st.write("### Keyword Files Table")

# Initialize a list to store table data
table_data = []

# Loop through companies and check if their keyword files exist
for company in companies_list:
    csv_filename = f"{company.lower().replace(' ', '_')}_chatgpt_keywords.csv"
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
