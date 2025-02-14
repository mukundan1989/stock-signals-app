import streamlit as st
import pandas as pd
import mysql.connector

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

# Sidebar Navigation
st.sidebar.title("Navigation")
selected = st.sidebar.radio("Select Page", ["Portfolio", "Sentiment Model", "Watchlist"])

# Main Page Title
st.title("Portfolio Dashboard")
st.write("Easily predict stock market trends and make smarter investment decisions.")

# Metrics Section
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Above Baseline", value="43%")
with col2:
    st.metric(label="Value Gain on Buy", value="$13,813")

col3, col4 = st.columns(2)
with col3:
    st.metric(label="Sentiment Score", value="+0.75")
with col4:
    st.metric(label="Prediction Accuracy", value="87%")

# Fetch Data Function
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
        df = pd.DataFrame(cursor.fetchall(), columns=["Date", "Company Name", "Symbol", "Trade Signal", "Entry Price"])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Display Watchlist Table
st.write("### Watchlist")
data = fetch_data("overall_latest_signal")
if data is not None:
    st.dataframe(data)  # Simplified table display

# Add Stock Search Feature
if st.button("Add Stock"):
    symbol = st.text_input("Enter Stock Symbol:")
    if symbol:
        new_data = fetch_data("overall_latest_signal", limit=1)  # Simulating search
        if new_data is not None:
            data = pd.concat([data, new_data], ignore_index=True)
            st.rerun()
        else:
            st.warning("Stock not found!")
