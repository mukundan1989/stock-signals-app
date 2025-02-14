import streamlit as st
import pandas as pd
import mysql.connector
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards
from st_aggrid import AgGrid
from streamlit_lottie import st_lottie
import requests

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

# Load Lottie Animation
@st.cache_data
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        return None

lottie_stock = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_k6hrgs9k.json")

# Sidebar Navigation
with st.sidebar:
    selected = option_menu("Main Menu", ["Portfolio", "Sentiment Model", "Watchlist"], 
                           icons=["graph-up", "search", "list"], menu_icon="cast", default_index=0)

# Main Page Title
st.markdown("<h1 style='text-align: center;'>Portfolio Dashboard</h1>", unsafe_allow_html=True)
st.write("Easily predict stock market trends and make smarter investment decisions with our intuitive tool.")

# Display Lottie Animation
st_lottie(lottie_stock, height=200)

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

style_metric_cards()  # Enhance metric card styles

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
    AgGrid(data)  # Enhanced interactive table

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
