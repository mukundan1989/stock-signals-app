import streamlit as st
import pandas as pd

# Set Page Config
st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")

# Custom CSS for Styling
st.markdown("""
    <style>
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .metric-header {
            font-size: 18px;
            font-weight: bold;
            color: #555;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin-top: 5px;
        }
        .positive {
            color: green;
            font-weight: bold;
        }
        .negative {
            color: red;
            font-weight: bold;
        }
        .stButton>button {
            background-color: #1f77b4;
            color: white;
            border-radius: 10px;
            padding: 10px 15px;
        }
        .stButton>button:hover {
            background-color: #144d7f;
        }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("<h1 style='text-align: center;'>📈 Stock Signal Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>Easily predict stock market trends and make smarter investment decisions.</p>", unsafe_allow_html=True)

# Portfolio Stats (Grid Layout)
st.write("### 📊 Portfolio Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<div class='metric-card'><div class='metric-header'>📊 Prediction Accuracy</div><div class='metric-value'>87%</div></div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-card'><div class='metric-header'>📈 Value Gain on Buy</div><div class='metric-value'>$13,813</div></div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-card'><div class='metric-header'>💡 Sentiment Score</div><div class='metric-value'>+0.75</div></div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='metric-card'><div class='metric-header'>🔍 Above Baseline</div><div class='metric-value'>43%</div></div>", unsafe_allow_html=True)

# Sidebar Toggle Switches
st.sidebar.header("🔧 Settings")
include_sentiment = st.sidebar.checkbox("Include Sentiment Analysis", value=False)
include_technical = st.sidebar.checkbox("Include Technical Indicators", value=False)
include_fundamental = st.sidebar.checkbox("Include Fundamental Data", value=False)

# Sample Stock Data
df = pd.DataFrame({
    "Symbol": ["AAPL", "AMZN", "GOOG", "MA", "QQQQ", "WMT"],
    "Name": ["Apple", "Amazon", "Google", "Mastercard", "Nasdaq", "Walmart"],
    "Action": ["Buy", "Buy", "Sell", "Sell", "Buy", "Buy"],
    "Price": ["$99.99", "$99.99", "$99.99", "$99.99", "$99.99", "$99.99"],
    "Sentiment": ["Positive", "Positive", "Negative", "Negative", "Positive", "Positive"],
    "% Change": ["+0.7562%", "+0.6762%", "-0.2562%", "-0.6562%", "+0.4562%", "+0.3562%"]
})

# Format Data Table with Conditional Colors
def highlight_action(val):
    color = 'green' if val == 'Buy' else 'red'
    return f'color: {color}; font-weight: bold;'

styled_df = df.style.applymap(highlight_action, subset=['Action'])

# Display Stock Data
st.write("### 📌 Stock Predictions")
st.dataframe(styled_df)

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.write("(Feature Coming Soon!)")

st.success("✅ App Loaded Successfully!")
