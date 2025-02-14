import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS to make the app full-width and responsive
st.markdown(
    """
    <style>
    .main > div {
        max-width: 100%;
        padding-left: 5%;
        padding-right: 5%;
    }
    .stDataFrame {
        width: 100% !important;
    }
    .stDataFrame > div {
        width: 100% !important;
    }
    .stDataFrame table {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .stDataFrame th, .stDataFrame td {
        padding: 8px !important;
    }
    .stButton > button {
        width: 100%;
    }
    .stMarkdown {
        width: 100%;
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
        # Connect to the database
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # SQL query to fetch the latest entry for each comp_symbol
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

        # Convert the result to a DataFrame
        columns = ["date", "comp_symbol", "analyzed_keywords", "sentiment_score", "sentiment", "entry_price"]
        df = pd.DataFrame(result, columns=columns)

        # Close the database connection
        cursor.close()
        conn.close()

        return df

    except Exception as e:
        st.error(f"Error fetching Google Trends signals: {e}")
        return None

# Streamlit UI - Google Trends Signals Page
st.markdown("<h1 style='text-align: center;'>Google Trends Signals</h1>", unsafe_allow_html=True)
st.write("View the latest Google Trends sentiment signals for each stock.")

# Fetch and display the Google Trends signals
gtrend_signals_df = fetch_gtrend_signals()

if gtrend_signals_df is not None:
    if not gtrend_signals_df.empty:
        # Display the DataFrame without the index column
        st.dataframe(gtrend_signals_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No Google Trends signals found in the database.")
else:
    st.error("Failed to fetch Google Trends signals. Please check the database connection.")
