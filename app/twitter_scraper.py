import streamlit as st
import requests
import pandas as pd
import os
import time

# API credentials (stored in Streamlit secrets)
API_KEY = st.secrets["RAPIDAPI_KEY"]
API_HOST = "twitter154.p.rapidapi.com"

# GitHub folder path where keywords are stored
GITHUB_FOLDER = "twitterdir"
KEYWORDS_FILE = os.path.join(GITHUB_FOLDER, "keywords.txt")

# Function to fetch tweets for a given keyword
def fetch_tweets_for_keyword(keyword):
    """
    Fetch tweets from the Twitter API for a given keyword.
    Implements basic rate-limit handling with retries.
    """
    url = f"https://{API_HOST}/search/search?query={keyword}&section=latest&min_retweets=1&min_likes=1&limit=50"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }

    for attempt in range(5):  # Retry up to 5 times
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit hit
            wait_time = 2 ** attempt
            st.warning(f"Rate limit hit. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            return None
    return None

# Function to process JSON and convert to DataFrame
def process_json_data(data):
    """
    Extracts relevant fields from JSON and converts to DataFrame.
    """
    records = []
    for item in data.get("results", []):
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

    return pd.DataFrame(records)

# Streamlit UI
st.title("🔍 Twitter Sentiment Extractor")

# Check if the keywords file exists in GitHub folder
if os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "r") as file:
        company_names = file.read().strip()
    st.success(f"✅ Found `{KEYWORDS_FILE}` in GitHub folder")
else:
    company_names = ""

# Display existing keywords & allow user to edit
company_names = st.text_area("Modify keywords (one per line):", company_names)

# Button to start fetching tweets
if st.button("Fetch Tweets"):
    if not company_names.strip():
        st.warning("Please enter at least one company name.")
    else:
        company_list = [c.strip() for c in company_names.split("\n") if c.strip()]
        all_dfs = []
        
        for company in company_list:
            st.write(f"Fetching tweets for: **{company}**")
            data = fetch_tweets_for_keyword(company)
            
            if data:
                df = process_json_data(data)
                all_dfs.append((company, df))
                st.write(f"✅ **Fetched {len(df)} tweets for {company}**")
        
        # Save results in GitHub folder
        if all_dfs:
            for company, df in all_dfs:
                # Convert DataFrame to CSV
                csv_filename = f"{GITHUB_FOLDER}/{company.replace(' ', '_')}.csv"
                df.to_csv(csv_filename, index=False)

                # Display data & provide download link
                st.subheader(f"📊 {company} Tweets")
                st.dataframe(df)
                st.download_button(
                    label=f"📥 Download {company}.csv",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name=f"{company.replace(' ', '_')}.csv",
                    mime="text/csv"
                )

st.info("Built with Streamlit & Twitter API 🚀")
