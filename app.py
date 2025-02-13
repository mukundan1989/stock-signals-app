import streamlit as st
import pandas as pd
import mysql.connector
import os

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="13.234.116.170",
        user="stockapp_sentiment_v1",
        password="Speed#a12345",
        database="stockapp_sentiment_v1"
    )

# Fetch data function
def fetch_data(offset, limit):
    conn = get_db_connection()
    query = f"""
        SELECT * FROM portfolio
        LIMIT {limit} OFFSET {offset}
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit app
st.title("Portfolio Stocks")

# Initialize session state for row count
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 10  # Default rows to show

# Fetch initial data
stocks_df = fetch_data(0, st.session_state.num_rows)
st.dataframe(stocks_df)

# Button to load more rows
if st.button("Add Stock"):
    st.session_state.num_rows += 10  # Increase row count by 10
    st.experimental_rerun()
