import streamlit as st
import mysql.connector

# Database credentials
DB_HOST = "13.234.116.170"
DB_USER = "stockapp_sentiment_v1"
DB_PASSWORD = "Speed#a12345"
DB_NAME = "stockapp_sentiment_v1"

# Function to test database connection
def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if conn.is_connected():
            return "✅ Database connection successful!"
        else:
            return "❌ Database connection failed!"
    except mysql.connector.Error as err:
        return f"❌ Error: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# Streamlit app
st.title("Database Connection Test")

# Check database connection
status_message = test_db_connection()
st.write(status_message)
