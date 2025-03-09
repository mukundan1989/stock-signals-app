import streamlit as st
import os
import json
import http.client

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "twitter154.p.rapidapi.com"  # API host
KEYWORDS_FILE = os.path.join(os.getcwd(), "twitterdir", "keywords.txt")  # Path to the keywords file
OUTPUT_DIR = os.path.join(os.getcwd(), "twitterdir", "output")  # Directory to save JSON files

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

            # Sanitize the keyword for filename
            sanitized_keyword = "".join(c for c in keyword if c.isalnum() or c in ("_", "-"))
            output_file = os.path.join(OUTPUT_DIR, f"{sanitized_keyword}.json")

            # Save the result to a JSON file
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)

            st.success(f"Saved tweets for '{keyword}' to: {output_file}")

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

# Streamlit UI
st.title("Twitter Data Fetcher")
st.write("Fetch tweets for keywords listed in 'keywords.txt' and save them as JSON files.")

# Debug: Print current working directory
st.write(f"Current working directory: {os.getcwd()}")

if st.button("Go"):
    st.write("Fetching tweets...")
    fetch_tweets()
    st.write("Process completed!")
