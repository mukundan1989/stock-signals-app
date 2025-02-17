import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf

# Set page title and layout
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Title
st.title("Stock Analysis Dashboard")
st.markdown("""
This dashboard provides a visual analysis of stock data using dummy datasets.
""")

# Sidebar for user inputs
st.sidebar.header("User Input Features")

# Create dummy stock data
@st.cache_data
def load_data():
    dates = pd.date_range("2023-01-01", "2023-10-01")
    stocks = {
        "AAPL": np.random.normal(150, 10, len(dates)),
        "GOOGL": np.random.normal(2800, 100, len(dates)),
        "MSFT": np.random.normal(300, 15, len(dates)),
        "AMZN": np.random.normal(120, 5, len(dates)),
    }
    df = pd.DataFrame(stocks, index=dates)
    df = df.reset_index().rename(columns={"index": "Date"})
    return df

df = load_data()

# Display raw data
if st.sidebar.checkbox("Show Raw Data"):
    st.subheader("Raw Data")
    st.write(df)

# Select stocks to analyze
selected_stocks = st.sidebar.multiselect("Select Stocks", df.columns[1:], default=["AAPL"])

# Filter data based on selected stocks
filtered_df = df[["Date"] + selected_stocks]

# Plot stock prices over time
st.subheader("Stock Price Over Time")
fig = px.line(filtered_df, x="Date", y=selected_stocks, title="Stock Price Trends")
st.plotly_chart(fig, use_container_width=True)

# Calculate and display daily returns
st.subheader("Daily Returns")
returns_df = filtered_df.set_index("Date").pct_change().dropna()
fig2 = px.line(returns_df, x=returns_df.index, y=selected_stocks, title="Daily Returns")
st.plotly_chart(fig2, use_container_width=True)

# Display summary statistics
st.subheader("Summary Statistics")
st.write(returns_df.describe())

# Correlation heatmap
st.subheader("Correlation Heatmap")
corr = filtered_df.set_index("Date").corr()
fig3 = px.imshow(corr, text_auto=True, title="Stock Correlation Heatmap")
st.plotly_chart(fig3, use_container_width=True)

# Add a footer
st.markdown("""
---
**Note:** This dashboard uses dummy data for demonstration purposes.
""")
