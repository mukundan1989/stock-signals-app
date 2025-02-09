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

        .stock-container {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }
        .stock-card {
            width: calc(33.333% - 16px);
            background: white;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .stock-action {
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .buy { background-color: #D1FAE5; color: #065F46; }
        .sell { background-color: #FEE2E2; color: #991B1B; }
        .stock-info {
            font-size: 14px;
            color: #4B5563;
        }
        .stock-change {
            font-size: 16px;
            font-weight: bold;
        }
        .positive { color: #10B981; }
        .negative { color: #EF4444; }
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

# Stock Data
stocks = [
    {"symbol": "AAPL", "name": "Apple", "price": "$99.99", "sentiment": "Positive", "change": "+0.75%", "action": "Buy"},
    {"symbol": "AMZN", "name": "Amazon", "price": "$99.99", "sentiment": "Positive", "change": "+0.67%", "action": "Buy"},
    {"symbol": "GOOG", "name": "Google", "price": "$99.99", "sentiment": "Negative", "change": "-0.25%", "action": "Sell"},
    {"symbol": "MA", "name": "Mastercard", "price": "$99.99", "sentiment": "Negative", "change": "-0.65%", "action": "Sell"},
    {"symbol": "QQQQ", "name": "Nasdaq", "price": "$99.99", "sentiment": "Positive", "change": "+0.45%", "action": "Buy"},
    {"symbol": "WMT", "name": "Walmart", "price": "$99.99", "sentiment": "Positive", "change": "+0.35%", "action": "Buy"}
]

# Display Stock Portfolio in Card Layout
st.subheader("📜 Stock Portfolio")
st.markdown("<div class='stock-container'>", unsafe_allow_html=True)
for stock in stocks:
    action_class = "buy" if stock["action"] == "Buy" else "sell"
    change_class = "positive" if float(stock["change"].replace('%', '')) > 0 else "negative"
    sentiment_class = "positive" if stock["sentiment"] == "Positive" else "negative"

    st.markdown(f"""
        <div class='stock-card'>
            <div class='stock-header'>
                <span>{stock['symbol']} - {stock['name']}</span>
                <span class='stock-action {action_class}'>{stock['action']}</span>
            </div>
            <div class='stock-info'>
                <b>Current Price:</b> {stock['price']} <br>
                <b>Sentiment:</b> <span class='{sentiment_class}'>{stock['sentiment']}</span>
            </div>
            <div class='stock-change {change_class}'>
                {"📈" if 'positive' in change_class else "📉"} {stock['change']}
            </div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
