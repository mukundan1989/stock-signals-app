import streamlit as st
import http.client
import os
import json

# Configuration
KEYWORDS_FILE = "twitterdir/keywords.txt"  # Path to keywords file
OUTPUT_DIR = "output/"  # Change this to your output directory
API_KEY = "your_rapidapi_key"  # Replace with actual API key
API_HOST = "twitter154.p.rapidapi.com"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_tweets_for_keyword(keyword):
    """Fetch tweets for a specific keyword from the API."""
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

def process_keywords():
    """Reads keywords from the file and fetches tweets."""
    if not os.path.exists(KEYWORDS_FILE):
        st.error(f"Keywords file '{KEYWORDS_FILE}' not found.")
        return
    
    with open(KEYWORDS_FILE, "r") as file:
        keywords = [line.strip() for line in file if line.strip()]
    
    results = {}
    for keyword in keywords:
        try:
            st.write(f"Fetching tweets for: {keyword}")
            result = fetch_tweets_for_keyword(keyword)
            sanitized_keyword = keyword.replace(" ", "_").replace("/", "_")
            output_file = os.path.join(OUTPUT_DIR, f"{sanitized_keyword}.json")
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(result)
            results[keyword] = output_file
            st.success(f"Saved tweets for '{keyword}' to {output_file}")
        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

def run_twitter_scraper():
    """Streamlit UI for Twitter Scraper."""
    st.title("Twitter Keyword Extractor")
    st.write("Fetch tweets for keywords listed in `twitterdir/keywords.txt`")

    if st.button("Go"):
        process_keywords()
