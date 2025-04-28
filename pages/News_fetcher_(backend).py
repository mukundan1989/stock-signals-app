import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime
import shutil
import re

# Configuration
DEFAULT_API_KEY = "1ce12aafcdmshdb6eea1ac608501p1ab501jsn4a47cc5027ce"
API_HOST = "seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
OUTPUT_DIR = "/tmp/newsdire"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "process_status" not in st.session_state:
    st.session_state["process_status"] = []
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY

# [Keep all the existing functions (fetch_articles, fetch_content, etc.) exactly the same...]

# Streamlit UI
st.title("Seeking Alpha News Fetcher")

# API Key Input
st.session_state["api_key"] = st.text_input(
    "Seeking Alpha API Key",
    value=st.session_state["api_key"],
    type="password",
    help="Default key is rate-limited. Replace with your own RapidAPI key."
)

# Date input boxes
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", value=datetime(2023, 10, 1))
with col2:
    to_date = st.date_input("To Date", value=datetime(2023, 10, 31))

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# Status placeholder
status_placeholder = st.empty()

# ===== NEW CLEAR TEMP FUNCTION =====
def clear_temp_storage():
    try:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        status_placeholder.write("♻️ Temporary storage cleared successfully!")
        return True
    except Exception as e:
        status_placeholder.write(f"❌ Error clearing temp storage: {e}")
        return False

# Button layout - Now with 2 columns (processing and utility buttons)
proc_col, util_col = st.columns([3, 1])

with proc_col:
    if st.button("Start Full Processing"):
        if not st.session_state["api_key"].strip():
            st.error("Please enter a valid API key!")
        else:
            # [Keep all the existing processing code exactly the same...]

with util_col:
    if st.button("Clear Temporary Storage", help="Delete all downloaded files and reset status"):
        if clear_temp_storage():
            st.success("Temporary files and status cleared!")
            st.balloons()
            st.experimental_rerun()

# [Keep all the existing display code (status table, process log, download section) the same...]
