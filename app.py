import streamlit as st
import pandas as pd

# Custom CSS for Styling
st.markdown("""
    <style>
        .metric-card {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            color: white;
            margin: 10px;
        }
        .blue { background-color: #3B82F6; }
        .green { background-color: #10B981; }
        .purple { background-color: #8B5CF6; }
        .orange { background-color: #F59E0B; }
        .buy { background-color: #D1FAE5; color: #065F46; padding: 6px 12px; border-radius: 5px; font-weight: bold; }
        .sell { background-color: #FEE2E2; color: #991B1B; padding: 6px 12px; border-radius: 5px; font-weight: bold; }
        .positive { color: #10B981; font-weight: bold; }
        .negative { color: #EF4444; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("📈 Portfolio Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions.")

# Sidebar Toggles
st.sidebar.header("Options")
sentiment_toggle = st.sidebar.checkbox("Include Sentiment Analysis", False)
technical_toggle = st.sidebar.checkbox("Include Technical Indicators", False)
fundamental_toggle = st.sidebar.checkbox("Include Fundamental Data", False)

# Metrics Data
metrics = [
    {"label": "Above baseline", "value": "43%", "color": "blue", "description": "Compared to market average"},
    {"label": "Value gain on buy", "value": "$13,813", "color": "green", "description": "Total profit from buy signals"},
    {"label": "Sentiment Score", "value": "+0.75", "color": "purple", "description": "Overall market sentiment"},
    {"label": "Prediction Accuracy", "value": "87%", "color": "orange", "description": "Success rate of predictions"}
]

# Display Metrics
st.subheader("📊 Key Metrics")
cols = st.columns(2)
for i, metric in enumerate(metrics):
    with cols[i % 2]:
        st.markdown(f"""
            <div class='metric-card {metric['color']}'>
                <h2>{metric['value']}</h2>
                <p>{metric['label']}</p>
                <small>{metric['description']}</small>
            </div>
        """, unsafe_allow_html=True)

# Toggle Buttons Section (Now Below Key Metrics)
st.subheader("🔧 Toggle Features")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Sentiment Analysis")
    sentiment_toggle = st.toggle("Enable Sentiment", sentiment_toggle)
with col2:
    st.write("Technical Indicators")
    technical_toggle = st.toggle("Enable Technical", technical_toggle)
with col3:
    st.write("Fundamental Data")
    fundamental_toggle = st.toggle("Enable Fundamental", fundamental_toggle)

# Stock Table Data
stocks = [
    {"symbol": "AAPL", "name": "Apple", "price": "$99.99", "sentiment": "Positive", "change": "+0.7562%", "action": "Buy"},
    {"symbol": "AMZN", "name": "Amazon", "price": "$99.99", "sentiment": "Positive", "change": "+0.6762%", "action": "Buy"},
    {"symbol": "GOOG", "name": "Google", "price": "$99.99", "sentiment": "Negative", "change": "-0.2562%", "action": "Sell"},
    {"symbol": "MA", "name": "Mastercard", "price": "$99.99", "sentiment": "Negative", "change": "-0.6562%", "action": "Sell"},
    {"symbol": "QQQQ", "name": "Nasdaq", "price": "$99.99", "sentiment": "Positive", "change": "+0.4562%", "action": "Buy"},
    {"symbol": "WMT", "name": "Walmart", "price": "$99.99", "sentiment": "Positive", "change": "+0.3562%", "action": "Buy"}
]

# Display Styled Stock Portfolio
st.subheader("📜 Stock Portfolio")

# Table Header
st.markdown("**Stock Details**")
st.divider()

# Iterate through stocks and display rows with columns
for stock in stocks:
    action_class = "buy" if stock["action"] == "Buy" else "sell"
    change_class = "positive" if float(stock["change"].replace('%', '')) > 0 else "negative"
    sentiment_class = "positive" if stock["sentiment"] == "Positive" else "negative"

    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 1])
    
    col1.write(f"**{stock['symbol']}**")
    col2.write(stock["name"])
    col3.markdown(f"<span class='{action_class}'>{stock['action']}</span>", unsafe_allow_html=True)
    col4.write(stock["price"])
    col5.markdown(f"<span class='{change_class}'>📈 {stock['change']}</span>" if "positive" in change_class else f"<span class='{change_class}'>📉 {stock['change']}</span>", unsafe_allow_html=True)
    col6.markdown(f"<span class='{sentiment_class}'>{stock['sentiment']}</span>", unsafe_allow_html=True)

    st.divider()

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
