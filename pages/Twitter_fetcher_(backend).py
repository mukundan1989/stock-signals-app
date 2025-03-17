import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil  # For clearing directories

# Custom CSS to change button hover color
st.markdown(
    """
    <style>
    /* Target the Fetch Tweets button */
    .stButton > button:hover {
        background-color: #4CAF50; /* Green color on hover */
        color: white; /* Text color on hover */
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    endpoint = f"/search/search?query={keyword}&section=latest&min_retweets=1&min_likes=1&limit=50&start_date=2025-01-01&language=en&end_date=2025-03-10"
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

    # Create a placeholder for the dynamic status line
    status_placeholder = st.empty()

    for keyword in keywords:
        try:
            # Update the dynamic status line for fetching
            status_placeholder.write(f"Fetching tweets for: {keyword}")

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

            # Update the dynamic status line for saving
            status_placeholder.write(f"Saved tweets for: {keyword}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

    # Clear the dynamic status line after all keywords are processed
    status_placeholder.empty()

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

    # Create a placeholder for the dynamic status line
    status_placeholder = st.empty()

    for json_file in json_files:
        try:
            # Update the dynamic status line for conversion
            status_placeholder.write(f"Converting {json_file} → {os.path.splitext(json_file)[0]}.csv")

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

        except Exception as e:
            st.error(f"Error converting {json_file} to CSV: {e}")

    # Clear the dynamic status line after all files are processed
    status_placeholder.empty()

def clear_temp():
    """
    Clear the /tmp/twitterdir/output and /tmp/twitterdir/csv_output folders.
    """
    try:
        # Remove JSON output directory
        if os.path.exists(JSON_OUTPUT_DIR):
            shutil.rmtree(JSON_OUTPUT_DIR)
            os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

        # Remove CSV output directory
        if os.path.exists(CSV_OUTPUT_DIR):
            shutil.rmtree(CSV_OUTPUT_DIR)
            os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

        # Clear the status table
        st.session_state["status_table"] = []

        st.success("Temporary files cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing temporary files: {e}")

# Streamlit UI
st.title("Twitter Data Fetcher")
st.write("Fetch tweets for keywords listed in 'keywords.txt' and save them as JSON files.")

# Buttons side by side
col1, col2, col3 = st.columns(3)
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

with col3:
    if st.button("Clear Temp"):
        st.write("Clearing temporary files...")
        clear_temp()
        st.write("Process completed!")

# Status Table
if st.session_state["status_table"]:
    st.write("### Status Table")
    # Create DataFrame
    status_df = pd.DataFrame(st.session_state["status_table"])
    # Display the table without the index column
    st.dataframe(status_df, hide_index=True)
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
