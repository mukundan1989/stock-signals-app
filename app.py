import streamlit as st
import random

# Dummy data
stocks = [
    {"symbol": "AAPL", "name": "Apple", "price": 99.99, "sentiment": "Positive", "change": "+0.7562%", "action": "Buy"},
    {"symbol": "AMZN", "name": "Amazon", "price": 99.99, "sentiment": "Positive", "change": "+0.6762%", "action": "Buy"},
    {"symbol": "GOOG", "name": "Google", "price": 99.99, "sentiment": "Negative", "change": "-0.2562%", "action": "Sell"},
    {"symbol": "MA", "name": "Mastercard", "price": 99.99, "sentiment": "Negative", "change": "-0.6562%", "action": "Sell"},
    {"symbol": "QQQQ", "name": "Nasdaq", "price": 99.99, "sentiment": "Positive", "change": "+0.4562%", "action": "Buy"},
    {"symbol": "WMT", "name": "Walmart", "price": 99.99, "sentiment": "Positive", "change": "+0.3562%", "action": "Buy"},
]

def render_dashboard():
    st.title("📈 Portfolio Dashboard")
    st.write("Easily predict stock market trends and make smarter investment decisions.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Above Baseline", "43%")
    col2.metric("Value Gain on Buy", "$13,813")
    col3.metric("Sentiment Score", "+0.75")
    col4.metric("Prediction Accuracy", "87%")

    st.subheader("Sentiment Input")
    st.write("Include market sentiment and see how public opinion shapes stock predictions.")
    
    st.write("Baseline: 2 Jan 2025")
    
    st.subheader("Portfolio")
    st.write("Current Portfolio Holdings:")
    
    for stock in stocks:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2])
        col1.write(f"**{stock['symbol']}**")
        col2.write(stock["name"])
        col3.write(f"{stock['action']} ${stock['price']}")
        col4.write(f"{stock['sentiment']}")
        col5.write(stock["change"])
    
    if st.button("➕ Add Stock"):
        new_stock = {
            "symbol": f"STK{random.randint(100,999)}",
            "name": "New Stock",
            "price": 99.99,
            "sentiment": random.choice(["Positive", "Negative"]),
            "change": f"{random.uniform(-1,1):.4f}%",
            "action": random.choice(["Buy", "Sell"])
        }
        stocks.append(new_stock)
        st.experimental_rerun()

# Run the app
if __name__ == "__main__":
    render_dashboard()
