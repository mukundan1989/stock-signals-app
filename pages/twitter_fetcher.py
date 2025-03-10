import streamlit as st
import os
import json
import http.client
import pandas as pd

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "twitter154.p.rapidapi.com"  # API host
KEYWORDS_FILE = "twitterdir/keywords.txt"  # Path to the keywords file
JSON_OUTPUT_DIR = "/tmp/twitterdir/output"  # Directory to save JSON files
CSV_OUTPUT_DIR = "/tmp/twitterdir/csv_output"  # Directory to save CSV files

# Ensure output directories exist
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Initialize session state for status table
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []

def fetch_tweets_for_keyword(keyword):
    """
    Fetch tweets for a specific keyword from the API.
    """
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    endpoint = f"/search/search?query={keyword}&section=latest&min_retweets=1&min_likes=1&limit=50&start_date=2024-07-01&language=en&end_date=2024-07-31"
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return data.decode("utf-8")

def fetch_tweets():
    """
    Fetch tweets for all keywords in the keywords file.
    """
    if not os.path.exists(KEYWORDS_FILE):
        st.error(f"Keywords file '{KEYWORDS_FILE}' does not exist. Please create it.")
        return

    with open(KEYWORDS_FILE, "r") as file:
        keywords = [line.strip() for line in file if line.strip()]

    if not keywords:
        st.warning("No keywords found in the file. Please add keywords to 'keywords.txt'.")
        return

    for keyword in keywords:
        try:
            st.write(f"Fetching tweets for: {keyword}")
            result = fetch_tweets_for_keyword(keyword)

            # Save the result to a JSON file
            sanitized_keyword = keyword.replace(" ", "_").replace("/", "_")  # Sanitize filename
            output_file = os.path.join(JSON_OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)

            # Update status table
            st.session_state["status_table"].append({
                "Keyword": keyword,
                "Tweet Extract JSON": "✅",
                "CSV Output": "❌"
            })

            st.success(f"Saved tweets for '{keyword}' to: {output_file}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

def convert_json_to_csv():
    """
    Convert all JSON files in the JSON output directory to CSV files.
    """
    if not os.path.exists(JSON_OUTPUT_DIR):
        st.warning("No JSON files found. Please fetch tweets first.")
        return

    json_files = [f for f in os.listdir(JSON_OUTPUT_DIR) if f.endswith(".json")]
    if not json_files:
        st.warning("No JSON files found in the output directory.")
        return

    for json_file in json_files:
        try:
            json_file_path = os.path.join(JSON_OUTPUT_DIR, json_file)
            csv_file_name = f"{os.path.splitext(json_file)[0]}.csv"
            csv_file_path = os.path.join(CSV_OUTPUT_DIR, csv_file_name)

            # Read JSON file
            with open(json_file_path, "r") as file:
                data = json.load(file)

            # Flatten the nested JSON structure
            records = []
            for item in data.get("results", []):  # Adjust key if structure changes
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

            # Convert to a pandas DataFrame
            df = pd.DataFrame(records)

            # Save to CSV
            df.to_csv(csv_file_path, index=False)

            # Update status table
            keyword = json_file.replace(".json", "").replace("_", " ")
            for entry in st.session_state["status_table"]:
                if entry["Keyword"] == keyword:
                    entry["CSV Output"] = "✅"
                    break

            st.success(f"Converted {json_file} -> {csv_file_name}")

        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")

# Streamlit UI
st.title("Twitter Data Fetcher")
st.write("Fetch tweets for keywords listed in 'keywords.txt' and save them as JSON files.")

# Buttons side by side
col1, col2 = st.columns(2)
with col1:
    if st.button("Fetch Tweets"):
        st.write("Fetching tweets...")
        fetch_tweets()
        st.write("Process completed!")

with col2:
    if st.button("Convert JSON to CSV"):
        st.write("Converting JSON files to CSV...")
        convert_json_to_csv()
        st.write("Conversion completed!")

# Status Table
if st.session_state["status_table"]:
    st.write("### Status Table")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.table(status_df)
else:
    st.write("No actions performed yet. Fetch tweets to see the status.")

# Display CSV files in a collapsible multi-column layout
if os.path.exists(CSV_OUTPUT_DIR):
    csv_files = [f for f in os.listdir(CSV_OUTPUT_DIR) if f.endswith(".csv")]
    if csv_files:
        with st.expander("Download Converted CSV Files"):
            # Create 3 columns for the download buttons
            cols = st.columns(3)
            for i, csv_file in enumerate(csv_files):
                with cols[i % 3]:  # Distribute buttons across columns
                    with open(os.path.join(CSV_OUTPUT_DIR, csv_file), "r") as f:
                        st.download_button(
                            label=f"Download {csv_file}",
                            data=f.read(),
                            file_name=csv_file,
                            mime="text/csv"
                        )
    else:
        st.warning("No CSV files found in the output directory.")
else:
    st.warning("CSV output directory does not exist.")
