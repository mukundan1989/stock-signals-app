import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Custom CSS for dark theme
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #0B0F19;
        color: #E6E6E6;
    }
    
    /* Title styling */
    h1 {
        color: #E6E6E6;
        font-weight: 700;
    }
    
    /* Input box styling */
    .stTextInput > div > div {
        background-color: #1A1F2F;
        border-radius: 8px;
        border: 1px solid #2D3347;
    }
    
    /* Button alignment fix */
    .stButton {
        height: 100%;
        padding-top: 0;
    }
    .stButton > button {
        margin-top: 0;
        height: 42px;  /* Match input box height */
    }
    
    /* Metric container styling */
    .metric-container {
        background-color: #1A1F2F;
        border: 1px solid #2D3347;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1F2F;
        border-radius: 8px;
        padding: 12px 24px;
        color: #E6E6E6;
    }
    
    /* Table styling */
    .stDataFrame {
        background-color: #1A1F2F;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.write("")  # Add a small space to align with input label
    st.button("Go", type="primary")

[Rest of the code remains exactly the same...]
