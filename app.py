import mysql.connector
import streamlit as st
import pandas as pd

# Connect to MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="your_remote_host",
        user="your_user",
        password="your_password",
        database="stock_signals"
    )

# Fetch data
def fetch_signals():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM signals ORDER BY created_at DESC", conn)
    conn.close()
    return df

# Streamlit UI
st.title("MySQL Database Viewer")
st.subheader("Stock Signals Table")

# Show MySQL data in a table
signals_df = fetch_signals()
st.dataframe(signals_df)
