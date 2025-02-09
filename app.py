import streamlit as st

# Custom CSS for styling
st.markdown("""
    <style>
    .stock-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
    }
    .stock-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        width: 30%;
        min-width: 200px;
        text-align: center;
        margin-bottom: 15px;
    }
    .stock-name {
        font-size: 18px;
        font-weight: bold;
    }
    .stock-price {
        font-size: 16px;
        color: #333;
    }
    .buy {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .sell {
        background-color: #FF4C4C;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .percentage {
        font-size: 14px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Sample stock data
stocks = [
    {"name": "AAPL - Apple", "price": "$99.99", "change": "+0.75%", "action": "BUY"},
    {"name": "AMZN - Amazon", "price": "$99.99", "change": "-0.67%", "action": "BUY"},
    {"name": "GOOG - Google", "price": "$99.99", "change": "-0.25%", "action": "SELL"},
    {"name": "MA - Mastercard", "price": "$99.99", "change": "-0.65%", "action": "SELL"},
    {"name": "QQQQ - Nasdaq", "price": "$99.99", "change": "+0.45%", "action": "BUY"},
    {"name": "WMT - Walmart", "price": "$99.99", "change": "+0.35%", "action": "BUY"},
]

st.subheader("📜 Stock Portfolio")

# Creating a row-based layout
st.markdown('<div class="stock-container">', unsafe_allow_html=True)
for stock in stocks:
    action_class = "buy" if stock["action"] == "BUY" else "sell"
    st.markdown(
        f"""
        <div class="stock-card">
            <div class="stock-name">{stock["name"]}</div>
            <div class="stock-price">{stock["price"]}</div>
            <div class="{action_class}">{stock["action"]}</div>
            <div class="percentage">{stock["change"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)
