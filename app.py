import streamlit as st
import pandas as pd
import mysql.connector

# Apply modern glassmorphism CSS from test-page-7.py
st.markdown("""
    <style>
    /* Glassmorphism Table */
    .glass-table {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        width: 100%;
        color: white;
    }
    .glass-table th {
        background: rgba(255, 255, 255, 0.1);
        padding: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    .glass-table td {
        padding: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .glass-table tr:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Available tables
TABLES = {
    "Google Trends": "gtrend_latest_signal",
    "News": "news_latest_signal",
    "Twitter": "twitter_latest_signal",
    "Overall": "overall_latest_signal"
}

# Initialize session state for selected table
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"
if "data" not in st.session_state:
    st.session_state["data"] = None

# Function to fetch and format data
def fetch_data(table, limit=5):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"SELECT date, comp_name, comp_symbol, trade_signal, entry_price FROM `{DB_NAME}`.`{table}` LIMIT {limit}"
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=["Date", "Company Name", "Stock Symbol", "Trade Signal", "Entry Price ($)"])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Display formatted table with glassmorphism style
st.write("### Portfolio")
if st.session_state["data"] is not None:
    table_html = st.session_state["data"].to_html(index=False, classes="glass-table", escape=False)
    st.markdown(table_html, unsafe_allow_html=True)
