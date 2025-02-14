import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for elegant table design
st.markdown(
    """
    <style>
    .pretty-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        overflow: hidden;
        text-align: center;
    }
    .pretty-table thead tr {
        background-color: #007BFF;
        color: #ffffff;
        text-align: center;
    }
    .pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
    }
    .pretty-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    .pretty-table tbody tr:hover {
        background-color: #f1f1f1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch the latest Google Trends signals
def fetch_gtrend_signals():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT date, comp_symbol, analyzed_keywords, sentiment_score, sentiment, entry_price
        FROM gtrend_signals_full
        WHERE (comp_symbol, date) IN (
            SELECT comp_symbol, MAX(date)
            FROM gtrend_signals_full
            GROUP BY comp_symbol
        );
        """
        cursor.execute(query)
        result = cursor.fetchall()

        columns = ["Date", "Company Symbol", "Analyzed Keywords", "Sentiment Score", "Sentiment", "Entry Price"]
        df = pd.DataFrame(result, columns=columns)

        cursor.close()
        conn.close()

        return df
    except Exception as e:
        st.error(f"Error fetching Google Trends signals: {e}")
        return None

st.markdown("<h1 style='text-align: center; color: #007BFF;'>Google Trends Signals</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>View the latest Google Trends sentiment signals for each stock.</p>", unsafe_allow_html=True)

gtrend_signals_df = fetch_gtrend_signals()

if gtrend_signals_df is not None:
    if not gtrend_signals_df.empty:
        table_html = gtrend_signals_df.to_html(index=False, classes="pretty-table", border=0)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.warning("No Google Trends signals found in the database.")
else:
    st.error("Failed to fetch Google Trends signals. Please check the database connection.")
