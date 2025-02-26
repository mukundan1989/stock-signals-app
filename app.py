import streamlit as st
import pandas as pd
import mysql.connector

# Set page config
st.set_page_config(layout="wide", page_title="Stock Sentimeter", initial_sidebar_state="collapsed")

# Apply modern glassmorphism CSS
st.markdown(
    """
    <style>
    /* Glassmorphism Metric Card */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        transition: transform 0.3s ease;
        text-align: center;
        margin: 10px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }
    
    .metric-trend {
        font-size: 0.85rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
    }

    /* Trend Colors */
    .positive { color: #00ff9f; }  /* Green */
    .negative { color: #ff4b4b; }  /* Red */

    /* Glassmorphism Table Styling */
    .pretty-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: #ffffff; /* White text for the table */
        background: rgba(255, 255, 255, 0.05); /* Glassmorphism background */
        backdrop-filter: blur(10px); /* Blur effect */
    }

    .pretty-table thead tr {
        background-color: rgba(0, 0, 0, 0.3); /* Semi-transparent black header */
        color: #ffffff; /* White text */
        text-align: center;
        border: none;
    }

    .pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
        border: none;
    }

    .pretty-table tbody tr:nth-of-type(odd) {
        background-color: rgba(255, 255, 255, 0.05); /* Light glassmorphism for odd rows */
    }

    .pretty-table tbody tr:nth-of-type(even) {
        background-color: rgba(255, 255, 255, 0.1); /* Slightly darker glassmorphism for even rows */
    }

    .pretty-table tbody tr:hover {
        background-color: rgba(255, 255, 255, 0.2); /* Hover effect */
    }

    /* Glassmorphism Button Styling */
    .stButton button {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 10px 20px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        transition: background 0.3s ease !important;
    }

    .stButton button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
    }

    /* Glassmorphism Text Input Styling */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 10px !important;
    }

    /* Glassmorphism Title and Subheader Styling */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }

    p {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# **2×2 Grid Layout Using HTML**
st.markdown(
    """
    <div class="grid-container">
        <div class="metric-card"><h2>43%</h2><p>Above Baseline</p></div>
        <div class="metric-card"><h2>$13,813</h2><p>Gain on Buy</p></div>
        <div class="metric-card"><h2>+0.75</h2><p>Sentiment Score</p></div>
        <div class="metric-card"><h2>87%</h2><p>Accuracy</p></div>
    </div>
    """,
    unsafe_allow_html=True
)

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
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False

# Add spacing before "Select Sentiment Model"
st.markdown("<br>", unsafe_allow_html=True)

# Toggle buttons for selecting models
st.write("### Select Sentiment Model")
col1, col2, col3, col4 = st.columns(4)

def toggle_selection(table_key):
    if st.session_state["selected_table"] != table_key:
        st.session_state["selected_table"] = table_key
        st.session_state["data"] = None
        st.rerun()

with col1:
    if st.toggle("Google Trends", value=(st.session_state["selected_table"] == "gtrend_latest_signal")):
        toggle_selection("gtrend_latest_signal")

with col2:
    if st.toggle("News", value=(st.session_state["selected_table"] == "news_latest_signal")):
        toggle_selection("news_latest_signal")

with col3:
    if st.toggle("Twitter", value=(st.session_state["selected_table"] == "twitter_latest_signal")):
        toggle_selection("twitter_latest_signal")

with col4:
    if st.toggle("Overall", value=(st.session_state["selected_table"] == "overall_latest_signal")):
        toggle_selection("overall_latest_signal")

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
        df = pd.DataFrame(cursor.fetchall(), columns=["date", "comp_name", "comp_symbol", "trade_signal", "entry_price"])
        cursor.close()
        conn.close()

        # Combine company name and symbol into a single column
        df["Company Name"] = df["comp_name"] + "<br><small>" + df["comp_symbol"] + "</small>"
        
        # Drop the original comp_name and comp_symbol columns
        df = df.drop(columns=["comp_name", "comp_symbol"])

        # Add trending graph icons to the Trade Signal column
        df["Trade Signal"] = df["trade_signal"].apply(
            lambda x: (
                '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M2 20 L8 15 L14 18 L20 12 L26 16 L32 10 L38 14 L44 8 L50 2" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                '</svg> ' + x
            ) if x.lower() == "buy" else (
                '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M2 10 L8 15 L14 12 L20 18 L26 14 L32 20 L38 16 L44 22 L50 28" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                '</svg> ' + x
            ) if x.lower() == "sell" else x
        )

        # Rename columns to user-friendly names
        df = df.rename(columns={
            "date": "Date",
            "entry_price": "Entry Price ($)"
        })

        # Drop the original trade_signal column to avoid duplication
        df = df.drop(columns=["trade_signal"])

        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Add spacing before "Portfolio"
st.markdown("<br>", unsafe_allow_html=True)

# Display formatted table with glassmorphism styling
st.write("### Portfolio")
if st.session_state["data"] is not None:
    table_html = st.session_state["data"].to_html(index=False, escape=False, classes="pretty-table")
    st.markdown(table_html, unsafe_allow_html=True)

# Add Stock button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

# Show search box when "Add Stock" is clicked
if st.session_state["show_search"]:
    symbol = st.text_input("Enter Stock Symbol:")
    if symbol:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            query = f"SELECT date, comp_name, comp_symbol, trade_signal, entry_price FROM `{DB_NAME}`.`{st.session_state['selected_table']}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()

            if result:
                new_row = pd.DataFrame(result, columns=["date", "comp_name", "comp_symbol", "trade_signal", "entry_price"])
                
                # Combine company name and symbol into a single column
                new_row["Company Name"] = new_row["comp_name"] + "<br><small>" + new_row["comp_symbol"] + "</small>"
                
                # Drop the original comp_name and comp_symbol columns
                new_row = new_row.drop(columns=["comp_name", "comp_symbol"])

                # Add trending graph icons to the Trade Signal column
                new_row["Trade Signal"] = new_row["trade_signal"].apply(
                    lambda x: (
                        '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                        '<path d="M2 20 L8 15 L14 18 L20 12 L26 16 L32 10 L38 14 L44 8 L50 2" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        '</svg> ' + x
                    ) if x.lower() == "buy" else (
                        '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                        '<path d="M2 10 L8 15 L14 12 L20 18 L26 14 L32 20 L38 16 L44 22 L50 28" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        '</svg> ' + x
                    ) if x.lower() == "sell" else x
                )

                # Rename new row to match the table headers
                new_row = new_row.rename(columns={
                    "date": "Date",
                    "entry_price": "Entry Price ($)"
                })

                # Drop the original trade_signal column to avoid duplication
                new_row = new_row.drop(columns=["trade_signal"])

                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
