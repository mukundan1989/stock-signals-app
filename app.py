import streamlit as st
import pandas as pd
import mysql.connector
import app.twitter_scraper as twitter_scraper  # Import the Twitter scraper

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Main App", "Twitter Scraper"])

# Show the selected page
if page == "Main App":
    st.title("Stock Sentimeter")
    st.write("Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.")
    
    # Existing Portfolio UI and Functionality
    
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
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None
    
    # Load initial data if not set
    if st.session_state["data"] is None:
        st.session_state["data"] = fetch_data(st.session_state["selected_table"])
    
    if st.session_state["data"] is not None:
        st.dataframe(st.session_state["data"])
    
    if st.button("Add Stock"):
        st.session_state["show_search"] = True
    
    if st.session_state["show_search"]:
        symbol = st.text_input("Enter Stock Symbol:")
        if symbol:
            st.session_state["show_search"] = False
            st.rerun()

elif page == "Twitter Scraper":
    twitter_scraper.run_twitter_scraper()  # Call the function from twitter_scraper.py
