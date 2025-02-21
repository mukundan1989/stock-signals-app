import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for dark-themed elegant table design
st.markdown(
    """
    <style>
    /* Target the main container (st-emotion-cache-bm2z3a) and set a dark grey background */
    .st-emotion-cache-bm2z3a {
        background-color: #2a2a2a; /* Dark grey background */
        color: #ffffff; /* White text for the entire page */
    }

    /* Ensure the text above the table is white */
    h1, p {
        color: #ffffff !important; /* White text for titles and paragraphs */
    }

    /* Updated styling for metric boxes with gradient background */
    .metric-box {
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a); /* Dark grey gradient */
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: #ffffff; /* White text */
        font-size: 18px;
        font-weight: bold;
        border: 1px solid #4a4a4a; /* Subtle border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow */
    }

    /* Grid container for metric boxes */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        justify-content: center;
        align-items: center;
    }

    @media (max-width: 600px) {
        .grid-container { grid-template-columns: repeat(2, 1fr); gap: 5px; }
    }

    /* Styling for the "Add Stock" button */
    .stButton button {
        background-color: #000000; /* Black background */
        color: #ffffff; /* White text */
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }

    .stButton button:hover {
        background-color: #333333; /* Slightly lighter black on hover */
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
        <div class="metric-box"><h2>43%</h2><p>Above Baseline</p></div>
        <div class="metric-box"><h2>$13,813</h2><p>Gain on Buy</p></div>
        <div class="metric-box"><h2>+0.75</h2><p>Sentiment Score</p></div>
        <div class="metric-box"><h2>87%</h2><p>Accuracy</p></div>
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

        # **Rename columns to user-friendly names**
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

# Add spacing before "Portfolio"
st.markdown("<br>", unsafe_allow_html=True)

# Display formatted table with pretty headers
st.write("### Portfolio")
if st.session_state["data"] is not None:
    table_html = st.session_state["data"].to_html(index=False, escape=False)
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
                
                # Rename new row to match the table headers
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
