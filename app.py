import streamlit as st
import pandas as pd

# Set page title
st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")

# Inject custom CSS
st.markdown("""
    <style>
        .big-metric {
            font-size: 32px !important;
            font-weight: bold;
            color: #333;
        }
        .positive {
            color: green;
            font-weight: bold;
        }
        .negative {
            color: red;
            font-weight: bold;
        }
        .stButton>button {
            background-color: #1f77b4;
            color: white;
            border-radius: 10px;
            padding: 10px 15px;
        }
        .stButton>button:hover {
            background-color: #144d7f;
        }
    </style>
""", unsafe_allow_html=True)

# Title and Portfolio Summary
st.markdown("<h1 style='text-align: center;'>📈 Stock Signal Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>Easily predict stock market trends and make smarter investment decisions.</p>", unsafe_allow_html=True)

# Portfolio Stats
col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Prediction Accuracy", "87%")
col2.metric("📈 Value Gain on Buy", "$13,813")
col3.metric("💡 Sentiment Score", "+0.75")
col4.metric("🔍 Above Baseline", "43%")

# Sidebar Toggle Switches
st.sidebar.header("Settings")
include_sentiment = st.sidebar.checkbox("Include Sentiment Analysis", value=False)
include_technical = st.sidebar.checkbox("Include Technical Indicators", value=False)
include_fundamental = st.sidebar.checkbox("Include Fundamental Data", value=False)

# Sample Stock Data
df = pd.DataFrame({
    "Symbol": ["AAPL", "AMZN", "GOOG", "MA", "QQQQ", "WMT"],
    "Name": ["Apple", "Amazon", "Google", "Mastercard", "Nasdaq", "Walmart"],
    "Action": ["Buy", "Buy", "Sell", "Sell", "Buy", "Buy"],
    "Price": [99.99, 99.99, 99.99, 99.99, 99.99, 99.99],
    "Sentiment": ["Positive", "Positive", "Negative", "Negative", "Positive", "Positive"],
    "% Change": [0.7562, 0.6762, -0.2562, -0.6562, 0.4562, 0.3562]
})

# Apply colors based on sentiment
df["Sentiment"] = df["Sentiment"].apply(lambda x: f"<span class='positive'>{x}</span>" if x == "Positive" else f"<span class='negative'>{x}</span>",)

# Display Stock Data
st.write("### Stock Predictions")
st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

# Add Stock Button
if st.button("➕ Add Stock"):
    st.write("(Feature Coming Soon!)")

st.success("App Loaded Successfully!")
