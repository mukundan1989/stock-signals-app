import streamlit as st
import pandas as pd
import mysql.connector

# 🔹 Apply Custom CSS
st.markdown("""
    <style>
        /* Grid Layout for Metric Boxes */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }

        /* Styling for Each Metric Box */
        .metric-box {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            font-weight: bold;
            color: white;
            font-family: Arial, sans-serif;
        }

        /* Remove Borders from Data Table */
        .stDataFrame div[data-testid="stVerticalBlockBorderWrapper"], 
        .stDataFrame div[data-testid="StyledDataFrameCell"], 
        .stDataFrame div[data-testid="StyledDataFrameHeaderCell"] {
            border: none !important;
        }

        .stDataFrame table {
            border-collapse: collapse !important;
        }

        /* Prevent Layout Issues */
        .stApp {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

# 🔹 Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# 🔹 Display the 4 Metric Boxes Properly
st.markdown("""
    <div class="grid-container">
        <div class="metric-box"><h2>43%</h2><p>Above Baseline</p></div>
        <div class="metric-box"><h2>$13,813</h2><p>Gain on Buy</p></div>
        <div class="metric-box"><h2>+0.75</h2><p>Sentiment Score</p></div>
        <div class="metric-box"><h2>87%</h2><p>Accuracy</p></div>
    </div>
""", unsafe_allow_html=True)

# 🔹 Database Credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# 🔹 Available Tables
TABLES = {
    "Google Trends": "gtrend_latest_signal",
    "News": "news_latest_signal",
    "Twitter": "twitter_latest_signal",
    "Overall": "overall_latest_signal"
}

# 🔹 Initialize Session State
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False

# 🔹 Function to Check Toggle States
def toggle_selection(table_key):
    st.session_state["selected_table"] = table_key
    st.session_state["data"] = None
    st.rerun()

# 🔹 Toggle Buttons for Selecting Models
st.write("### Select Sentiment Model")
col1, col2, col3, col4 = st.columns(4)

with col1:
    google_trends_toggle = st.toggle("Google Trends", value=(st.session_state["selected_table"] == "gtrend_latest_signal"))

with col2:
    news_toggle = st.toggle("News", value=(st.session_state["selected_table"] == "news_latest_signal"))

with col3:
    twitter_toggle = st.toggle("Twitter", value=(st.session_state["selected_table"] == "twitter_latest_signal"))

with col4:
    overall_toggle = st.toggle("Overall", value=(st.session_state["selected_table"] == "overall_latest_signal"))

# 🔹 Logic to Keep "Overall" On If Others Are Off
if not (google_trends_toggle or news_toggle or twitter_toggle):
    overall_toggle = True
else:
    overall_toggle = False

# 🔹 Update Selected Table Based on Toggle
if google_trends_toggle:
    toggle_selection("gtrend_latest_signal")
elif news_toggle:
    toggle_selection("news_latest_signal")
elif twitter_toggle:
    toggle_selection("twitter_latest_signal")
elif overall_toggle:
    toggle_selection("overall_latest_signal")

# 🔹 Function to Fetch Data
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

# 🔹 Load Initial Data
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# 🔹 Format Stock Symbol Below Company Name & Display Table
if st.session_state["data"] is not None:
    st.session_state["data"]["Company Name"] = st.session_state["data"].apply(
        lambda row: f"<b>{row['Company Name']}</b><br><span style='color:gray;'>{row['Stock Symbol']}</span>", axis=1
    )

    st.session_state["data"] = st.session_state["data"].drop(columns=["Stock Symbol"])

    st.markdown(
        st.session_state["data"].to_html(escape=False, index=False), 
        unsafe_allow_html=True
    )

# 🔹 "Add Stock" Button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

# 🔹 Show Search Box When "Add Stock" is Clicked
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
                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
