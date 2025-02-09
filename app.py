import streamlit as st
import pandas as pd

# Load FontAwesome for Icons
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        /* Make toggle section responsive */
        .toggle-wrapper {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;  /* Allows wrapping on smaller screens */
            gap: 15px;
        }
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .toggle-icon {
            font-size: 20px;
            color: black;
        }
        /* Ensure stock table is scrollable on mobile */
        .stock-table-container {
            overflow-x: auto;
        }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("📈 Portfolio Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions.")

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
            <div style='padding:20px; border-radius:10px; text-align:center; background:{metric['color']}; color:white;'>
                <h2>{metric['value']}</h2>
                <p>{metric['label']}</p>
                <small>{metric['description']}</small>
            </div>
        """, unsafe_allow_html=True)

# Add spacing above Toggle Features
st.markdown("<br>", unsafe_allow_html=True)

# Toggle Buttons Section (Now Mobile-Friendly)
st.subheader("🔧 Toggle Features")
st.markdown("<div class='toggle-wrapper'>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='toggle-container'><i class='fa-brands fa-twitter toggle-icon'></i>", unsafe_allow_html=True)
    st.toggle("", False, key="sentiment")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='toggle-container'><i class='fa-solid fa-newspaper toggle-icon'></i>", unsafe_allow_html=True)
    st.toggle("", False, key="technical")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='toggle-container'><i class='fa-brands fa-google toggle-icon'></i>", unsafe_allow_html=True)
    st.toggle("", False, key="fundamental")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # Close wrapper div

# Add spacing above Stock Portfolio
st.markdown("<br>", unsafe_allow_html=True)

# Stock Table Data
stocks = [
    {"symbol": "AAPL", "name": "Apple", "price": "$99.99", "sentiment": "Positive", "change": "+0.7562%", "action": "Buy"},
    {"symbol": "AMZN", "name": "Amazon", "price": "$99.99", "sentiment": "Positive", "change": "+0.6762%", "action": "Buy"},
    {"symbol": "GOOG", "name": "Google", "price": "$99.99", "sentiment": "Negative", "change": "-0.2562%", "action": "Sell"},
    {"symbol": "MA", "name": "Mastercard", "price": "$99.99", "sentiment": "Negative", "change": "-0.6562%", "action": "Sell"},
    {"symbol": "QQQQ", "name": "Nasdaq", "price": "$99.99", "sentiment": "Positive", "change": "+0.4562%", "action": "Buy"},
    {"symbol": "WMT", "name": "Walmart", "price": "$99.99", "sentiment": "Positive", "change": "+0.3562%", "action": "Buy"}
]

# Display Stock Portfolio (Mobile-Friendly)
st.subheader("📜 Stock Portfolio")
st.markdown("<div class='stock-table-container'>", unsafe_allow_html=True)

# Display Stocks with Responsive Layout
for stock in stocks:
    action_class = "buy" if stock["action"] == "Buy" else "sell"
    change_class = "positive" if float(stock["change"].replace('%', '')) > 0 else "negative"
    sentiment_class = "positive" if stock["sentiment"] == "Positive" else "negative"

    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])

    col1.markdown(f"""
        <div style='background:#f3f4f6; padding:10px; border-radius:8px; text-align:center;'>
            <strong>{stock['symbol']}</strong><br>
            <small style='color:gray'>{stock['name']}</small>
        </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"<span class='{action_class}'>{stock['action']}</span>", unsafe_allow_html=True)
    col3.markdown(f"<span class='{change_class}'>📈 {stock['change']}</span>" if "positive" in change_class else f"<span class='{change_class}'>📉 {stock['change']}</span>", unsafe_allow_html=True)
    col4.markdown(f"<span class='{sentiment_class}'>{stock['sentiment']}</span>", unsafe_allow_html=True)

    st.divider()

st.markdown("</div>", unsafe_allow_html=True)  # Close stock table div

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
