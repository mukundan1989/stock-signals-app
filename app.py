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

# Metrics Grid (2x2 Layout with Spacing)
col1, col2 = st.columns(2)

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

st.markdown("<br>", unsafe_allow_html=True)

col3, col4 = st.columns(2)

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

# Add spacing before "Select Data Source"
st.markdown("<br>", unsafe_allow_html=True)

# Toggle buttons (Only one can be active at a time)
st.write("### Select Sentiment Model")
col1, col2, col3, col4 = st.columns(4)

def toggle_selection(table_key):
    if st.session_state["selected_table"] != table_key:
        st.session_state["selected_table"] = table_key
        st.session_state["data"] = None  # Reset data
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

# Function to fetch and filter data
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
if st.session_state["data"] is not None:
    df = st.session_state["data"]
    st.dataframe(
        df.style.set_properties(**{
            'background-color': '#f9f9f9',
            'color': '#333',
            'border': '1px solid #ddd',
            'text-align': 'center',
        }).set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#007BFF'), ('color', 'white'), ('font-size', '16px')]}
        ])
    )

# Add spacing before "Watchlist"
st.markdown("<br>", unsafe_allow_html=True)

# Toggle buttons (Only one can be active at a time)
st.write("### Watchlist")
col1, col2, col3, col4 = st.columns(4)

# Display table with only required columns (No extra index)
if st.session_state["data"] is not None:
    st.dataframe(st.session_state["data"].to_dict(orient="records"))

# Add Stock button (always visible)
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
                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False  # Hide search box after adding stock
                st.rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
