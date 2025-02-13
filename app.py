import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Custom CSS
st.markdown("""
<style>
    .metric-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    .metric-label {
        color: #666;
        font-size: 14px;
        margin: 0;
    }
    .stock-table {
        font-size: 14px;
    }
    .sentiment-positive {
        color: #22c55e;
    }
    .sentiment-negative {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# Title and Description
st.title("Portfolio")
st.markdown("""
Easily predict stock market trends and make smarter investment decisions
with our intuitive portfolio tool.
""")

# Metrics
metrics = [
    {"label": "Above Baseline", "value": "43%", "description": "Compared to market average"},
    {"label": "Value Gain on Buy", "value": "$13,813", "description": "Total profit from buy signals"},
    {"label": "Sentiment Score", "value": "+0.75", "description": "Overall market sentiment"},
    {"label": "Prediction Accuracy", "value": "87%", "description": "Success rate of predictions"}
]

# Display metrics in a grid
cols = st.columns(4)
for col, metric in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{metric['value']}</p>
            <p class="metric-label">{metric['label']}</p>
        </div>
        """, unsafe_allow_html=True)

# Sentiment Input Section
st.markdown("""
### Sentiment Input
Include market sentiment and see how public opinion shapes stock predictions.
""")

# Initialize session state
if "stocks_data" not in st.session_state:
    # Initial stock data
    st.session_state.stocks_data = pd.DataFrame({
        'symbol': ['AAPL', 'AMZN', 'GOOG', 'MA', 'QQQQ', 'WMT'],
        'name': ['Apple', 'Amazon', 'Google', 'Mastercard', 'Nasdaq', 'Walmart'],
        'signal': ['Buy', 'Buy', 'Sell', 'Sell', 'Buy', 'Buy'],
        'price': [99.99, 99.99, 99.99, 99.99, 99.99, 99.99],
        'sentiment': ['Positive', 'Positive', 'Negative', 'Negative', 'Positive', 'Positive'],
        'change': [0.7562, 0.6762, -0.2562, -0.6562, 0.4562, 0.3562]
    })

# Function to format the stock table
def create_stock_table(df):
    baseline_date = "2 Jan 2025"
    
    # Create the table with custom formatting
    table_html = f"""
    <div class="stock-table">
        <table style="width: 100%;">
            <tr style="background-color: #f3f4f6;">
                <th>Symbol</th>
                <th>Name</th>
                <th>Signal</th>
                <th>Baseline: {baseline_date}</th>
                <th>Current $</th>
                <th>% Chg</th>
                <th>Sentiment</th>
            </tr>
    """
    
    for _, row in df.iterrows():
        sentiment_color = "sentiment-positive" if row['sentiment'] == 'Positive' else "sentiment-negative"
        signal_color = "#22c55e" if row['signal'] == 'Buy' else "#ef4444"
        change_color = "#22c55e" if row['change'] > 0 else "#ef4444"
        
        table_html += f"""
        <tr>
            <td><strong>{row['symbol']}</strong></td>
            <td>{row['name']}</td>
            <td style="color: {signal_color}">{row['signal']}</td>
            <td>${row['price']}</td>
            <td>${row['price']}</td>
            <td style="color: {change_color}">{row['change']:+.4f}%</td>
            <td class="{sentiment_color}">{row['sentiment']}</td>
        </tr>
        """
    
    table_html += "</table></div>"
    return table_html

# Display the stock table
st.markdown(create_stock_table(st.session_state.stocks_data), unsafe_allow_html=True)

# Add Stock Button
if st.button("➕ Add Stock"):
    st.text_input("Enter Stock Symbol:")
