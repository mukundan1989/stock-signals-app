import streamlit as st
import pandas as pd

# App title
st.title("Portfolio Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions.")

# Toggle switches
st.sidebar.header("Options")
sentiment_toggle = st.sidebar.checkbox("Include Sentiment Analysis", False)
technical_toggle = st.sidebar.checkbox("Include Technical Indicators", False)
fundamental_toggle = st.sidebar.checkbox("Include Fundamental Data", False)

# Metrics data
metrics = [
    {"label": "Above baseline", "value": "43%", "color": "blue", "description": "Compared to market average"},
    {"label": "Value gain on buy", "value": "$13,813", "color": "green", "description": "Total profit from buy signals"},
    {"label": "Sentiment Score", "value": "+0.75", "color": "purple", "description": "Overall market sentiment"},
    {"label": "Prediction Accuracy", "value": "87%", "color": "orange", "description": "Success rate of predictions"}
]

# Display Metrics
st.subheader("Key Metrics")
cols = st.columns(2)
for i, metric in enumerate(metrics):
    with cols[i % 2]:
        st.markdown(f"""
            <div style='padding: 10px; background-color: {metric['color']}; border-radius: 5px; color: white;'>
                <h3>{metric['value']}</h3>
                <p><b>{metric['label']}</b></p>
                <small>{metric['description']}</small>
            </div>
        """, unsafe_allow_html=True)

# Stock table data
stocks = pd.DataFrame([
    ["AAPL", "Apple", "$99.99", "Positive", "+0.7562%", "Buy"],
    ["AMZN", "Amazon", "$99.99", "Positive", "+0.6762%", "Buy"],
    ["GOOG", "Google", "$99.99", "Negative", "-0.2562%", "Sell"],
    ["MA", "Mastercard", "$99.99", "Negative", "-0.6562%", "Sell"],
    ["QQQQ", "Nasdaq", "$99.99", "Positive", "+0.4562%", "Buy"],
    ["WMT", "Walmart", "$99.99", "Positive", "+0.3562%", "Buy"]
], columns=["Symbol", "Name", "Current Price", "Sentiment", "% Change", "Action"])

# Display Stock Table
st.subheader("Stock Portfolio")
st.dataframe(stocks)

# Add Stock Button
if st.button("Add Stock"):
    st.success("Feature to add stocks coming soon!")
