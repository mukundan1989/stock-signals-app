import streamlit as st
import pandas as pd
import mysql.connector

# Apply glassmorphism CSS styling (from Performance Summary)
st.markdown("""
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

    /* Remove all borders from the table */
    .dataframe-container table {
        border-collapse: collapse;
        border: none;
    }
    .dataframe-container th, .dataframe-container td {
        border: none !important;
        padding: 10px;
    }

    </style>
""", unsafe_allow_html=True)

# Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center; color: #ffffff;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center; color: #ffffff;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# 2x2 Grid Layout Using Glassmorphism Metric Cards
st.markdown(
    """
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; justify-content: center; align-items: center;">
        <div class="metric-card">
            <div class="metric-label">Above Baseline</div>
            <div class="metric-value">43%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Gain on Buy</div>
            <div class="metric-value">$13,813</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Sentiment Score</div>
            <div class="metric-value">+0.75</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Accuracy</div>
            <div class="metric-value">87%</div>
        </div>
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
        st.experimental_rerun()

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
        df = pd.DataFrame(cursor.fetchall(), columns=["Date", "Company Name", "Stock Symbol", "Trade Signal", "Entry Price ($)"])
        cursor.close()
        conn.close()

        # Format Company Name & Stock Symbol into a single column
        df["Company Info"] = df.apply(lambda row: f"{row['Company Name']}<br><small>{row['Stock Symbol']}</small>", axis=1)

        # Drop the old Company Name and Stock Symbol columns
        df = df.drop(columns=["Company Name", "Stock Symbol"])

        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Add spacing before "Portfolio"
st.markdown("<br>", unsafe_allow_html=True)

# Display formatted table using Streamlit's dataframe
st.write("### Portfolio")
if st.session_state["data"] is not None:
    st.markdown(
        st.session_state["data"].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

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
                new_row = pd.DataFrame(result, columns=["Date", "Company Name", "Stock Symbol", "Trade Signal", "Entry Price ($)"])
                
                # Format Company Info
                new_row["Company Info"] = new_row.apply(lambda row: f"{row['Company Name']}<br><small>{row['Stock Symbol']}</small>", axis=1)
                new_row = new_row.drop(columns=["Company Name", "Stock Symbol"])

                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.experimental_rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
