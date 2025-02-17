import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Custom CSS for dark theme and styling
st.markdown(
    """
    <style>
    body {
        background: #111827;
        color: white;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .container {
        max-width: 400px;
        margin: 0 auto;
    }
    .pretty-box {
        background: #1F2937;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .stock-symbol {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin: 0;
    }
    .company-name {
        color: #9CA3AF;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page layout
st.markdown("<h1 class='stock-symbol'>AAPL</h1>", unsafe_allow_html=True)
st.markdown("<div class='company-name'>Apple Inc.</div>", unsafe_allow_html=True)

# Sample Price Chart
def plot_price_chart():
    fig, ax = plt.subplots()
    x = np.arange(5)
    y = np.random.randint(140, 170, size=5)
    ax.plot(x, y, marker='o', linestyle='-', color='#4ADE80')
    ax.set_xticks(x)
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
    ax.set_ylabel("Price ($)")
    st.pyplot(fig)

st.markdown("<div class='pretty-box'>Price Chart</div>", unsafe_allow_html=True)
plot_price_chart()

# Placeholder for Twitter Sentiment
st.markdown("<div class='pretty-box'>Twitter Sentiment Gauge (Coming Soon)</div>", unsafe_allow_html=True)

# Placeholder for Overall Sentiment (News & Sector)
st.markdown("<div class='pretty-box'>Overall Sentiment Gauges (Coming Soon)</div>", unsafe_allow_html=True)

# Placeholder for Google Trends Sentiment
st.markdown("<div class='pretty-box'>Google Trend Bullishness Indicator (Coming Soon)</div>", unsafe_allow_html=True)

# Placeholder for Keyword Cloud
st.markdown("<div class='pretty-box'>Keyword Cloud (Coming Soon)</div>", unsafe_allow_html=True)
