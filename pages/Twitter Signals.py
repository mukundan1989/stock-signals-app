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
    /* Remove table borders */
    .custom-table {
        border-collapse: separate;
        border-spacing: 0 10px; /* Add space between rows */
        border: none; /* Remove table borders */
        width: 100%;
    }

    /* Dark grey background for each row with curved borders */
    .custom-table tbody tr {
        background-color: #2a2a2a; /* Dark grey background */
        border-radius: 10px; /* Curved borders */
        border: none; /* Remove row borders */
    }

    /* Add space between rows */
    .custom-table tbody tr:not(:last-child) {
        margin-bottom: 10px; /* Space between rows */
    }

    /* Ensure the table cells have padding and text alignment */
    .custom-table th, .custom-table td {
        padding: 12px 15px;
        text-align: center;
        border: none; /* Remove cell borders */
    }

    /* Header styling */
    .custom-table thead tr {
        background-color: #000000; /* Black header */
        color: #ffffff; /* White text */
        border-radius: 10px; /* Curved borders for header */
        border: none; /* Remove header borders */
    }

    /* Hover effect for rows */
    .custom-table tbody tr:hover {
        background-color: #3a3a3a; /* Slightly lighter grey on hover */
    }

    /* Custom styling for Company Symbol column */
    .symbol-positive {
        background-color: #4CAF50; /* Elegant green for positive sentiment */
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        display: inline-block;
    }

    .symbol-negative {
        background-color: #F44336; /* Elegant red for negative sentiment */
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to apply custom styling to the Company Symbol column
def style_symbol(symbol, sentiment):
    if sentiment == "Positive":
        return f'<span class="symbol-positive">{symbol}</span>'
    elif sentiment == "Negative":
        return f'<span class="symbol-negative">{symbol}</span>'
    else:
        return symbol

# Page title and description
st.markdown("<h1 style='text-align: center;'>Twitter Signals</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>View the latest Twitter sentiment signals for each stock.</p>", unsafe_allow_html=True)

# Fetch and display Twitter signals
twitter_signals_df = fetch_twitter_signals()

if twitter_signals_df is not None:
    if not twitter_signals_df.empty:
        # Apply custom styling to the Company Symbol column
        twitter_signals_df["Company Symbol"] = twitter_signals_df.apply(
            lambda row: style_symbol(row["Company Symbol"], row["Sentiment"]), axis=1
        )

        # Convert DataFrame to HTML
        table_html = twitter_signals_df.to_html(escape=False, index=False, classes="custom-table")

        # Display the table using st.markdown
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.warning("No Twitter signals found in the database.")
else:
    st.error("Failed to fetch Twitter signals. Please check the database connection.")
