import streamlit as st
import pandas as pd
import mysql.connector
import config  # Import your configuration file

# Apply custom styling from config
st.markdown(config.STYLES, unsafe_allow_html=True)

# Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# Database credentials from config
DB_HOST = config.DB_HOST
DB_NAME = config.DB_NAME
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD

# Available tables
TABLES = config.TABLES

# Initialize session state for selected table
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False

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

        df = df.rename(columns={
            "date": "Date",
            "comp_name": "Company Name",
            "comp_symbol": "Stock Symbol",
            "trade_signal": "Trade Signal",
            "entry_price": "Entry Price ($)"
        })
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Display table
st.write("### Portfolio")
if st.session_state["data"] is not None:
    st.dataframe(st.session_state["data"])  # Using Streamlit's built-in table rendering

# Add Stock button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

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
                new_row = new_row.rename(columns={
                    "date": "Date",
                    "comp_name": "Company Name",
                    "comp_symbol": "Stock Symbol",
                    "trade_signal": "Trade Signal",
                    "entry_price": "Entry Price ($)"
                })
                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
