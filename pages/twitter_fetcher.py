import streamlit as st
import os
import json
import http.client
from github import Github  # PyGithub library

# Configuration
API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"  # Your RapidAPI key
API_HOST = "twitter154.p.rapidapi.com"  # API host
KEYWORDS_FILE = "twitterdir/keywords.txt"  # Path to the keywords file
OUTPUT_DIR = "twitterdir/output"  # Directory to save JSON files
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # Securely access GitHub token from Streamlit Secrets
GITHUB_REPO = "mukundan1989/stock-signals-app"  # Replace with your GitHub repo

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

def push_to_github(file_path, content):
    """
    Push a file to GitHub using the GitHub API.
    """
    try:
        github = Github(GITHUB_TOKEN)
        repo = github.get_repo(GITHUB_REPO)
        with open(file_path, "r") as file:
            content = file.read()
        repo.create_file(
            path=file_path,  # Path in the repository
            message=f"Add {os.path.basename(file_path)}",  # Commit message
            content=content,  # File content
            branch="main"  # Branch to push to
        )
        st.success(f"Pushed {file_path} to GitHub.")
    except Exception as e:
        st.error(f"Error pushing to GitHub: {e}")

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

            # Push the file to GitHub
            push_to_github(output_file, result)

        except Exception as e:
            st.error(f"Error fetching tweets for '{keyword}': {e}")

# Streamlit UI
st.title("Twitter Data Fetcher")
st.write("Fetch tweets for keywords listed in 'keywords.txt' and save them as JSON files.")

if st.button("Go"):
    st.write("Fetching tweets...")
    fetch_tweets()
    st.write("Process completed!")
