import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for table styling (from app (24).py)
st.markdown(
    """
    <style>
    /* Custom CSS for elegant table design with curved edges */
    .pretty-table {
        width: 100%;
        border-collapse: separate; /* Use separate to allow rounded corners */
        border-spacing: 0 30px; /* Add spacing between rows */
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 30px; /* Rounded edges for the table */
        overflow: hidden;
        text-align: center;
        border: none;
        color: #ffffff; /* White text for the table */
    }

    /* Grey background with curved edges for each row */
    .pretty-table tbody tr {
        background-color: #3a3a3a; /* Dark grey background */
        border-radius: 50px; /* Rounded edges for each row */
        margin-bottom: 10px; /* Add spacing between rows */
    }

    /* Padding for table cells */
    .pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
        border: none;
    }

    /* Add curved edges to the first and last cells in each row */
    .pretty-table tbody tr td:first-child {
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
    }

    .pretty-table tbody tr td:last-child {
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
    }

    /* Hover effect for rows */
    .pretty-table tbody tr:hover {
        background-color: #4a4a4a; /* Slightly lighter grey on hover */
    }

    /* Custom CSS for the Company Name cell */
    .company-name-cell {
        background-color: #3a3a3a; /* Dark grey background */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
    }

    /* Custom CSS for the Trade Signal cell */
    .trade-signal-buy {
        background-color: #2e7d32; /* Green background for Buy */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
    }

    .trade-signal-sell {
        background-color: #c62828; /* Red background for Sell */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
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

# Page title and description
st.markdown("<h1 style='text-align: center;'>Twitter Signals</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>View the latest Twitter sentiment signals for each stock.</p>", unsafe_allow_html=True)

# Fetch and display Twitter signals
twitter_signals_df = fetch_twitter_signals()

if twitter_signals_df is not None:
    if not twitter_signals_df.empty:
        # Apply custom styling to the Company Symbol column based on sentiment
        twitter_signals_df["Company Symbol"] = twitter_signals_df.apply(
            lambda row: f'<div class="company-name-cell">{row["Company Symbol"]}</div>', axis=1
        )

        # Apply custom styling to the Sentiment column
        twitter_signals_df["Sentiment"] = twitter_signals_df.apply(
            lambda row: (
                f'<div class="trade-signal-buy">{row["Sentiment"]}</div>'
                if row["Sentiment"] == "Positive"
                else f'<div class="trade-signal-sell">{row["Sentiment"]}</div>'
            ),
            axis=1,
        )

        # Convert DataFrame to HTML and render it
        table_html = twitter_signals_df.to_html(index=False, classes="pretty-table", escape=False)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.warning("No Twitter signals found in the database.")
else:
    st.error("Failed to fetch Twitter signals. Please check the database connection.")
