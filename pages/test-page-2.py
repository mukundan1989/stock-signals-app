import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Custom CSS for dark-themed elegant design
st.markdown(
    """
    <style>
    /* Dark background for the entire page */
    .st-emotion-cache-bm2z3a {
        background-color: #2a2a2a; /* Dark grey background */
        color: #ffffff; /* White text for the entire page */
    }

    /* Custom CSS for elegant box design */
    .custom-box {
        background-color: #3a3a3a; /* Dark grey box background */
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        color: #ffffff; /* White text inside the box */
    }

    /* Large text for tweet count */
    .tweet-count {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
    }

    /* Meter design for sentiment */
    .meter {
        width: 100%;
        height: 20px;
        background: linear-gradient(90deg, #ff4b4b 0%, #4bff4b 100%);
        border-radius: 10px;
        position: relative;
        margin: 20px 0;
    }

    .meter-indicator {
        width: 5px;
        height: 30px;
        background-color: #ffffff;
        position: absolute;
        top: -5px;
        transform: translateX(-50%);
    }

    /* Ensure the text above the boxes is white */
    h1, p {
        color: #ffffff !important; /* White text for titles and paragraphs */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page title and description
st.markdown("<h1 style='text-align: center;'>AAPL Stock & Twitter Sentiment</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>View the latest stock price and Twitter sentiment for AAPL.</p>", unsafe_allow_html=True)

# Fetch AAPL stock data for the last 50 days
@st.cache_data
def fetch_stock_data():
    ticker = "AAPL"
    data = yf.download(ticker, period="50d")
    return data

stock_data = fetch_stock_data()

# Calculate percentage change over the last 50 days
initial_price = stock_data['Close'].iloc[0]
current_price = stock_data['Close'].iloc[-1]
percentage_change = ((current_price - initial_price) / initial_price) * 100

# Display stock price chart in a box
with st.container():
    st.markdown("<div class='custom-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AAPL Stock Price (Last 50 Days)</h2>", unsafe_allow_html=True)
    st.line_chart(stock_data['Close'])
    st.markdown(f"<p style='text-align: center;'>Percentage Change: <b>{percentage_change:.2f}%</b></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Dummy Twitter sentiment data
sentiment_score = 0.65  # Dummy sentiment score (range: -1 to 1, where -1 is negative, 1 is positive)
tweet_count = 1234  # Dummy number of tweets

# Display Twitter sentiment box
with st.container():
    st.markdown("<div class='custom-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Twitter Sentiment</h2>", unsafe_allow_html=True)

    # Meter-like design for sentiment
    st.markdown("<div class='meter'>", unsafe_allow_html=True)
    st.markdown(f"<div class='meter-indicator' style='left: {((sentiment_score + 1) / 2 * 100)}%;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Labels for the meter
    st.markdown("<div style='display: flex; justify-content: space-between; margin: 10px 0;'>", unsafe_allow_html=True)
    st.markdown("<span>Negative</span>", unsafe_allow_html=True)
    st.markdown("<span>Positive</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Display number of tweets in large font
    st.markdown(f"<div class='tweet-count'>{tweet_count}</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Number of Tweets Analyzed</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
