import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Portfolio Dashboard", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #2563eb;
        color: white;
        width: 100%;
    }
    /* Custom table styling */
    [data-testid="stDataFrame"] div[class*="data-table"] {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    [data-testid="stDataFrame"] th {
        background-color: #f8f9fa;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        color: #374151 !important;
        border-bottom: 1px solid #e5e7eb;
    }
    [data-testid="stDataFrame"] td {
        padding: 16px 24px !important;
        font-size: 14px;
    }
    .badge {
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 500;
        font-size: 12px;
        display: inline-block;
    }
    .badge-buy {
        background-color: #dcfce7;
        color: #166534;
    }
    .badge-sell {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .badge-positive {
        background-color: #dcfce7;
        color: #166534;
    }
    .badge-negative {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .symbol {
        color: #2563eb;
        font-weight: 600;
    }
    .trend-up {
        color: #16a34a;
    }
    .trend-down {
        color: #dc2626;
    }
    </style>
""", unsafe_allow_html=True)

# [Previous header and metrics code remains the same until the table section]

# Create sample stock data with HTML formatting
stocks_data = {
    "Symbol": [
        f'<span class="symbol">{symbol}</span>'
        for symbol in ["AAPL", "AMZN", "GOOG", "MA", "QQQQ", "WMT"]
    ],
    "Name": ["Apple", "Amazon", "Google", "Mastercard", "Nasdaq", "Walmart"],
    "Action": [
        '<span class="badge badge-buy">Buy</span>',
        '<span class="badge badge-buy">Buy</span>',
        '<span class="badge badge-sell">Sell</span>',
        '<span class="badge badge-sell">Sell</span>',
        '<span class="badge badge-buy">Buy</span>',
        '<span class="badge badge-buy">Buy</span>'
    ],
    "Price": ["$99.99", "$99.99", "$99.99", "$99.99", "$99.99", "$99.99"],
    "Change": [
        '<span class="trend-up">↑ +0.7562%</span>',
        '<span class="trend-up">↑ +0.6762%</span>',
        '<span class="trend-down">↓ -0.2562%</span>',
        '<span class="trend-down">↓ -0.6562%</span>',
        '<span class="trend-up">↑ +0.4562%</span>',
        '<span class="trend-up">↑ +0.3562%</span>'
    ],
    "Sentiment": [
        '<span class="badge badge-positive">Positive</span>',
        '<span class="badge badge-positive">Positive</span>',
        '<span class="badge badge-negative">Negative</span>',
        '<span class="badge badge-negative">Negative</span>',
        '<span class="badge badge-positive">Positive</span>',
        '<span class="badge badge-positive">Positive</span>'
    ]
}

df = pd.DataFrame(stocks_data)

# Display the styled table
st.markdown("### Stock Analysis")
st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# [Rest of the code remains the same]
