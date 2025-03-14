import requests
import csv
import os
import pandas as pd

# Configuration
API_KEY = "fa106911d1msh3c9f067ace5be00p1071cfjsn4fc681388b27"  # Your RapidAPI key
API_HOST = "open-ai21.p.rapidapi.com"  # API host
COMPANY_SYMBOLS_FILE = "twitterdir/comp_names.csv"  # Path to the company symbols file
KEYWORDS_OUTPUT_DIR = "/tmp/gtrendsdir/output"  # Directory to save keyword CSV files

# Ensure output directories exist
os.makedirs(KEYWORDS_OUTPUT_DIR, exist_ok=True)

# Read the symbols from the CSV file
symbols_df = pd.read_csv(COMPANY_SYMBOLS_FILE)  # Read the CSV file
symbols_list = symbols_df['symbols'].tolist()  # Extract the list of company symbols

# Define the API endpoint and headers
url = f"https://{API_HOST}/chatgpt"
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
    "Content-Type": "application/json"
}

# Loop through each symbol to get the keywords
for symbol in symbols_list:
    csv_filename = f"{symbol.lower().replace(' ', '_')}_chatgpt_keywords.csv"

    # Prepare the payload for the API request
    payload = {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Provide a list of top fifteen important keywords associated with the company \"{symbol}\", focusing on its most popular products, services, or core offerings. The keywords should reflect areas where demand or interest can be analyzed using Google Trends data. Ensure the keywords are specific, and highly representative of the company's primary focus. Give the output as a bulletted list with no other extra characters or text."
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

            print(f"Keywords for {symbol} saved to {csv_path}")

        except KeyError as e:
            print(f"KeyError for {symbol}: {e}. Please check the response structure.")

    else:
        print(f"Failed to retrieve data for {symbol}. Status code: {response.status_code}")
