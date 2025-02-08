import streamlit as st
import pandas as pd
import mysql.connector

# Set page title
st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")

# Title and Portfolio Summary
st.title("📈 Stock Signal Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions.")

# Portfolio Stats
col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Prediction Accuracy", "87%")
col2.metric("📈 Value Gain on Buy", "$13,813")
col3.metric("💡 Sentiment Score", "+0.75")
col4.metric("🔍 Above Baseline", "43%")

# Load Data (CSV or MySQL)
def load_data_from_csv(file_path):
    return pd.read_csv(file_path)

def load_data_from_mysql(host, user, password, database, table):
    conn = mysql.connector.connect(
        host=host, user=user, password=password, database=database
    )
    query = f"SELECT * FROM {table}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Sidebar: Choose Data Source
data_source = st.sidebar.radio("Select Data Source:", ["CSV", "MySQL"])
df = None

if data_source == "CSV":
    file_path = st.sidebar.text_input("Enter CSV File Path:")
    if st.sidebar.button("Load Data") and file_path:
        df = load_data_from_csv(file_path)

elif data_source == "MySQL":
    db_host = st.sidebar.text_input("DB Host", "localhost")
    db_user = st.sidebar.text_input("DB User", "root")
    db_password = st.sidebar.text_input("DB Password", type="password")
    db_name = st.sidebar.text_input("Database Name")
    table_name = st.sidebar.text_input("Table Name")
    if st.sidebar.button("Load Data") and db_name and table_name:
        df = load_data_from_mysql(db_host, db_user, db_password, db_name, table_name)

# Sample Data (if no database available)
if df is None:
    df = pd.DataFrame({
        "Stock": ["AAPL", "AMZN", "GOOG", "MA", "QQQQ", "WMT"],
        "Action": ["Buy", "Buy", "Sell", "Sell", "Buy", "Buy"],
        "Price": [99.99, 99.99, 99.99, 99.99, 99.99, 99.99],
        "Sentiment": ["Positive", "Positive", "Negative", "Negative", "Positive", "Positive"],
        "% Change": [0.7562, 0.6762, -0.2562, -0.6562, 0.4562, 0.3562]
    })

# Display Stock Data
st.write("### Stock Predictions")
st.dataframe(df)

# Sentiment Input
st.write("### Sentiment Input")
include_sentiment = st.checkbox("Include Market Sentiment in Prediction")

# Add Stock Button
if st.button("➕ Add Stock"):
    st.write("(Feature Coming Soon!)")

st.success("App Loaded Successfully!")
