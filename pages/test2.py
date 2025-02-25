import streamlit as st
import pandas as pd
import mysql.connector

# Apply glassmorphism CSS styling & table formatting
st.markdown("""
    <style>
    /* Metric Card Styling */
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
    .metric-card:hover { transform: translateY(-5px); }
    .metric-label { font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); }
    .metric-value { font-size: 2rem; font-weight: 700; color: #ffffff; margin: 8px 0; }
    
    /* Remove Table Borders */
    .dataframe { border-collapse: collapse; width: 100%; }
    .dataframe th, .dataframe td { border: none !important; padding: 8px; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI Header
st.markdown("<h1 style='text-align: center; color: #ffffff;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center; color: #ffffff;'>Know stock market trends and make smarter investment decisions.</p>", unsafe_allow_html=True)

# Database Configuration
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Available Sentiment Tables
TABLES = {
    "Google Trends": "gtrend_latest_signal",
    "News": "news_latest_signal",
    "Twitter": "twitter_latest_signal",
    "Overall": "overall_latest_signal"
}

# Initialize session state
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False

# Toggle Buttons for Sentiment Models (Working Version)
st.write("### Select Sentiment Model")
selected_model = st.radio("Choose Model", list(TABLES.keys()), horizontal=True)

# Update session state when selection changes
if TABLES[selected_model] != st.session_state["selected_table"]:
    st.session_state["selected_table"] = TABLES[selected_model]
    st.session_state["data"] = None  # Force data refresh

# Function to Fetch Data
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

# Load data if not already fetched
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Format Data: Stock Symbol Below Company Name
def format_dataframe(df):
    if df is not None:
        df["Company Info"] = df.apply(lambda row: f"<b>{row['Company Name']}</b><br><span style='color:gray;'>{row['Stock Symbol']}</span>", axis=1)
        return df[["Date", "Company Info", "Trade Signal", "Entry Price ($)"]]
    return df

# Display Portfolio Table
st.write("### Portfolio")
if st.session_state["data"] is not None:
    formatted_data = format_dataframe(st.session_state["data"])
    st.markdown(formatted_data.to_html(escape=False, index=False), unsafe_allow_html=True)

# Add Stock Button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

# Search Stock Symbol Input
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
                new_row = pd.DataFrame(result, columns=["Date", "Company Name", "Stock Symbol", "Trade Signal", "Entry Price ($)"])
                new_row["Company Info"] = new_row.apply(lambda row: f"<b>{row['Company Name']}</b><br><span style='color:gray;'>{row['Stock Symbol']}</span>", axis=1)
                new_row = new_row[["Date", "Company Info", "Trade Signal", "Entry Price ($)"]]

                st.session_state["data"] = pd.concat([format_dataframe(st.session_state["data"]), new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.experimental_rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
