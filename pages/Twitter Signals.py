import streamlit as st
import pandas as pd
import mysql.connector

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch the latest Twitter signals
def fetch_twitter_signals():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT date, comp_symbol, analyzed_tweets, sentiment_score, sentiment, entry_price
        FROM twitter_signals_full
        WHERE (comp_symbol, date) IN (
            SELECT comp_symbol, MAX(date)
            FROM twitter_signals_full
            GROUP BY comp_symbol
        );
        """
        cursor.execute(query)
        result = cursor.fetchall()

        columns = ["Date", "Company Symbol", "Analyzed Tweets", "Sentiment Score", "Sentiment", "Entry Price"]
        df = pd.DataFrame(result, columns=columns)

        cursor.close()
        conn.close()

        return df
    except Exception as e:
        st.error(f"Error fetching Twitter signals: {e}")
        return None

# Custom CSS for table styling
st.markdown(
    """
    <style>
    /* Dark grey background for each row with curved borders */
    .stDataFrame tbody tr {
        background-color: #2a2a2a; /* Dark grey background */
        border-radius: 10px; /* Curved borders */
        margin-bottom: 10px; /* Space between rows */
    }

    /* Add space between rows */
    .stDataFrame tbody tr:not(:last-child) {
        margin-bottom: 10px; /* Space between rows */
    }

    /* Ensure the table cells have padding and text alignment */
    .stDataFrame th, .stDataFrame td {
        padding: 12px 15px;
        text-align: center;
    }

    /* Header styling */
    .stDataFrame thead tr {
        background-color: #000000; /* Black header */
        color: #ffffff; /* White text */
    }

    /* Hover effect for rows */
    .stDataFrame tbody tr:hover {
        background-color: #3a3a3a; /* Slightly lighter grey on hover */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page title and description
st.markdown("<h1 style='text-align: center;'>Twitter Signals</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>View the latest Twitter sentiment signals for each stock.</p>", unsafe_allow_html=True)

# Fetch and display Twitter signals
twitter_signals_df = fetch_twitter_signals()

if twitter_signals_df is not None:
    if not twitter_signals_df.empty:
        st.dataframe(twitter_signals_df, use_container_width=True)  # Use st.dataframe for better styling control
    else:
        st.warning("No Twitter signals found in the database.")
else:
    st.error("Failed to fetch Twitter signals. Please check the database connection.")
