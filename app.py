import streamlit as st
import pandas as pd
import mysql.connector

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="13.234.116.170",
            user="stockapp_sentiment_v1",
            password="Speed#a12345",
            database="stockapp_sentiment_v1"
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

# Fetch data function
def fetch_data(offset, limit):
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()  # Return empty DataFrame if no connection

    try:
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM portfolio LIMIT {limit} OFFSET {offset};"
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not records:
            st.warning("No more data available.")
            return pd.DataFrame()

        return pd.DataFrame(records)  # Convert MySQL rows to DataFrame
    except mysql.connector.Error as err:
        st.error(f"Error fetching data: {err}")
        return pd.DataFrame()

# Streamlit app
st.title("Portfolio Stocks")

# Initialize session state for row count
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 10  # Default rows to show

# Fetch initial data
stocks_df = fetch_data(0, st.session_state.num_rows)

if stocks_df.empty:
    st.warning("No data found in the portfolio table.")
else:
    st.dataframe(stocks_df)

# Button to load more rows
if st.button("Add Stock"):
    st.session_state.num_rows += 10  # Increase row count by 10
    st.experimental_rerun()
