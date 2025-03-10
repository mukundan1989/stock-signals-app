import streamlit as st
import os
import json
import http.client

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "twitter154.p.rapidapi.com"  # API host
KEYWORDS_FILE = "twitterdir/keywords.txt"  # Path to the keywords file
OUTPUT_DIR = "/tmp/twitterdir/output"  # Save files to Streamlit's persistent storage

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            output_file = os.path.join(OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)

            st.success(f"Saved tweets for '{keyword}' to: {output_file}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

def list_saved_files():
    """
    List all saved JSON files in the output directory.
    """
    if os.path.exists(OUTPUT_DIR):
        files = os.listdir(OUTPUT_DIR)
        if files:
            st.write("### Saved JSON Files")
            for file in files:
                st.write(f"- {file}")
                # Add a download button for each file
                with open(os.path.join(OUTPUT_DIR, file), "r") as f:
                    st.download_button(
                        label=f"Download {file}",
                        data=f.read(),
                        file_name=file,
                        mime="application/json"
                    )
        else:
            st.warning("No JSON files found in the output directory.")
    else:
        st.warning("Output directory does not exist.")

# Streamlit UI
st.title("Twitter Data Fetcher")
st.write("Fetch tweets for keywords listed in 'keywords.txt' and save them as JSON files.")

if st.button("Go"):
    st.write("Fetching tweets...")
    fetch_tweets()
    st.write("Process completed!")

# Display saved files
list_saved_files()
