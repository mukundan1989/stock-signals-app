import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for elegant table design using theme-based colors
st.markdown(
    """
    <style>
    /* Use theme-based background color for the main container */
    .st-emotion-cache-bm2z3a {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 10px; /* Adjust spacing between rows */
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: var(--text-color);
    }

    /* Black background with curved edges for each row */
    .pretty-table tbody tr {
        background-color: black; /* Set background color to black */
        border-radius: 20px; /* Adjust the border-radius for rounded edges */
        margin-bottom: 10px;
    }

    .pretty-table th {
        background-color: #1c1c1c; /* Set background color to black */
        color: #aeaeae !important; /* Set text color to light grey */
    }

    .pretty-table th:first-child {
        border-top-left-radius: 30px; /* Adjust the border-radius for the first cell */
        border-bottom-left-radius: 30px;
    }

    .pretty-table th:last-child {
        border-top-right-radius: 30px; /* Adjust the border-radius for the last cell */
        border-bottom-right-radius: 30px;
    }

    /* Padding for table cells */
    .pretty-table th, .pretty-table td {
        padding: 6px 9px;
        text-align: center;
        border: none;
        border-top: 5px solid #282828 !important;
    }

    /* Add curved edges to the first and last cells in each row */
    .pretty-table tbody tr td:first-child {
        border-top-left-radius: 20px; /* Adjust the border-radius for the first cell */
        border-bottom-left-radius: 20px;
    }

    .pretty-table tbody tr td:last-child {
        border-top-right-radius: 20px; /* Adjust the border-radius for the last cell */
        border-bottom-right-radius: 20px;
    }

    /* Hover effect for rows */
    .pretty-table tbody tr:hover {
        background-color: #333; /* Darker shade for hover effect */
    }

    /* Ensure the text above the table is white */
    h1, p {
        color: var(--text-color) !important;
    }

    /* Custom CSS for the Sentiment cell */
    .sentiment-positive {
        background-color: #2e7d32; /* Green background for positive sentiment */
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    .sentiment-negative {
        background-color: #c62828; /* Red background for negative sentiment */
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    /* Custom CSS for the title with logo */
    .title-with-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px; /* Space between logo and title */
    }

    .title-with-logo img {
        width: 70px; /* Adjust the size of the logo */
        height: 70px;
        background: #000;
        padding: 3px;
        border-radius: 5px;
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

# Function to fetch the latest News signals
def fetch_news_signals():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT date, comp_symbol, analyzed_articles, sentiment_score, sentiment, entry_price
        FROM news_signals_full
        WHERE (comp_symbol, date) IN (
            SELECT comp_symbol, MAX(date)
            FROM news_signals_full
            GROUP BY comp_symbol
        );
        """
        cursor.execute(query)
        result = cursor.fetchall()

        columns = ["Date", "Company Symbol", "Analyzed Articles", "Sentiment Score", "Sentiment", "Entry Price"]
        df = pd.DataFrame(result, columns=columns)

        # Apply custom CSS to the Sentiment column
        df["Sentiment"] = df["Sentiment"].apply(
            lambda x: (
                '<div class="sentiment-positive">' + x + '</div>'
            ) if x.lower() == "positive" else (
                '<div class="sentiment-negative">' + x + '</div>'
            ) if x.lower() == "negative" else x
        )

        cursor.close()
        conn.close()

        return df
    except Exception as e:
        st.error(f"Error fetching News signals: {e}")
        return None

# Page title with News logo
st.markdown(
    """
    <div class="title-with-logo">
        <img src="https://raw.githubusercontent.com/mukundan1989/stock-signals-app/refs/heads/main/images/news-logo.png" alt="News Logo">
        <h1 style='text-align: center;'>News Signals</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Page description
st.write("<p style='text-align: center;'>View the latest News sentiment signals for each stock.</p>", unsafe_allow_html=True)

# Fetch and display News signals
news_signals_df = fetch_news_signals()

if news_signals_df is not None:
    if not news_signals_df.empty:
        table_html = news_signals_df.to_html(index=False, classes="pretty-table", escape=False)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.warning("No News signals found in the database.")
else:
    st.error("Failed to fetch News signals. Please check the database connection.")
