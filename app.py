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

# Streamlit UI - Metrics Section
st.markdown("<h1 style='text-align: center;'>Portfolio</h1>", unsafe_allow_html=True)
st.write("Easily predict stock market trends and make smarter investment decisions with our intuitive portfolio tool.")

# Metrics Grid (2x2 Layout)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.markdown(
        "<div style='background-color:#007BFF; padding:20px; border-radius:10px; text-align:center; color:white;'>"
        "<h2>43%</h2><p>Above Baseline</p></div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        "<div style='background-color:#007BFF; padding:20px; border-radius:10px; text-align:center; color:white;'>"
        "<h2>$13,813</h2><p>Value Gain on Buy</p></div>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        "<div style='background-color:#007BFF; padding:20px; border-radius:10px; text-align:center; color:white;'>"
        "<h2>+0.75</h2><p>Sentiment Score</p></div>",
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        "<div style='background-color:#007BFF; padding:20px; border-radius:10px; text-align:center; color:white;'>"
        "<h2>87%</h2><p>Prediction Accuracy</p></div>",
        unsafe_allow_html=True
    )

# Initialize session state for selected table
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"  # Default table
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False
if "added_symbols" not in st.session_state:
    st.session_state["added_symbols"] = set()

# Toggle buttons for table selection
selected_table = None
cols = st.columns(len(TABLES))
for i, (label, table) in enumerate(TABLES.items()):
    if cols[i].toggle(label, table == st.session_state["selected_table"]):
        selected_table = table

# Update session state if a new table is selected
if selected_table and selected_table != st.session_state["selected_table"]:
    st.session_state["selected_table"] = selected_table
    st.session_state["data"] = None  # Reset data
    st.rerun()

# Function to fetch data
def fetch_data(table, limit=5):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM `{DB_NAME}`.`{table}` LIMIT {limit}"
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Add Stock button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

# Search functionality
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
            query = f"SELECT * FROM `{DB_NAME}`.`{st.session_state['selected_table']}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()

            if result:
                if symbol not in st.session_state["added_symbols"]:
                    new_row = pd.DataFrame(result, columns=st.session_state["data"].columns)
                    st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                    st.session_state["added_symbols"].add(symbol)
                    st.session_state["show_search"] = False
                    st.rerun()
                else:
                    st.warning("Stock already added!")
            else:
                st.error("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")

# Display table data
st.dataframe(st.session_state["data"])
