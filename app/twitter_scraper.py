import streamlit as st
import json
import os

def load_keywords(file_path):
    """Reads keywords from a text file."""
    try:
        with open(file_path, "r") as file:
            keywords = [line.strip() for line in file.readlines() if line.strip()]
        return keywords
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return []

def save_json(data, output_dir, filename="output.json"):
    """Saves data to a JSON file in the specified output directory."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
    return file_path

# Streamlit UI
st.title("Keyword Processing App")

# Define file paths
keyword_file = "twitterdir/keywords.txt"
output_dir = "outputdir"  # Change this if needed

if st.button("Go"):
    keywords = load_keywords(keyword_file)
    if keywords:
        output_data = {"keywords": keywords}
        output_file = save_json(output_data, output_dir)
        st.success(f"Output saved to {output_file}")
        st.json(output_data)
