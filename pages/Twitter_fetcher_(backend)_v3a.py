import streamlit as st
import os
import json
import http.client
import pandas as pd
import shutil
import time
import threading
import concurrent.futures
from queue import Queue
from datetime import datetime, timedelta, date
import calendar
import platform
from typing import List, Dict, Any, Tuple, Set

# Custom CSS
st.markdown(
    """
    <style>
    .stButton > button:hover {
        background-color: #000000;
        color: white;
    }
    .stButton > button {
        background-color: #282828;
        color: white;
    }
    .stButton > button:active {
        background-color: #282828;
        color: white;
    }    
    </style>
    """,
    unsafe_allow_html=True
)

# Default paths based on OS
def get_default_output_dir():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Documents", "TwitterData")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Documents", "TwitterData")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "TwitterData")

# Get previous month's date range
def get_previous_month_range():
    today = date.today()
    
    # If we're in the first month of the year
    if today.month == 1:
        prev_month = 12
        year = today.year - 1
    else:
        prev_month = today.month - 1
        year = today.year
    
    # Get the first day of the previous month
    first_day = date(year, prev_month, 1)
    
    # Get the last day of the previous month
    _, last_day_num = calendar.monthrange(year, prev_month)
    last_day = date(year, prev_month, last_day_num)
    
    return first_day, last_day

# Configuration
API_HOST = "twitter154.p.rapidapi.com"
DEFAULT_API_KEY = "3cf0736f79mshe60115701a871c4p19c558jsncccfd9521243"
KEYWORDS_FILE = "data/keywords.txt"
MAX_WORKERS = 4  # Maximum number of parallel workers
TWEETS_PER_REQUEST = 20  # Maximum tweets per API request

# Get previous month's date range
prev_month_start, prev_month_end = get_previous_month_range()

# Initialize session state for output directories
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "directories" not in st.session_state:
    st.session_state["directories"] = {}

# Initialize session state
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
