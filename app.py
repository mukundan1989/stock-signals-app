import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

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
        .stock-table th, .stock-table td {
            padding: 10px;
            text-align: left;
        }
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

# Toggle Buttons in Main Section
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

# Stock Table Data
stocks = pd.DataFrame([
    ["AAPL", "Apple", "$99.99", "Positive", "+0.7562%", "Buy"],
    ["AMZN", "Amazon", "$99.99", "Positive", "+0.6762%", "Buy"],
    ["GOOG", "Google", "$99.99", "Negative", "-0.2562%", "Sell"],
    ["MA", "Mastercard", "$99.99", "Negative", "-0.6562%", "Sell"],
    ["QQQQ", "Nasdaq", "$99.99", "Positive", "+0.4562%", "Buy"],
    ["WMT", "Walmart", "$99.99", "Positive", "+0.3562%", "Buy"]
], columns=["Symbol", "Name", "Current Price", "Sentiment", "% Change", "Action"])

# Display Stock Table
st.subheader("📜 Stock Portfolio")
st.dataframe(stocks)

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
