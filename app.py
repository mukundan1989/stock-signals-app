import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

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
    </style>
""", unsafe_allow_html=True)

# Header Section
st.title("Portfolio Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions with our intuitive portfolio tool.")

# Create metrics data
metrics = {
    "Above baseline": {"value": "43%", "description": "Compared to market average", "color": "blue"},
    "Value gain on buy": {"value": "$13,813", "description": "Total profit from buy signals", "color": "green"},
    "Sentiment Score": {"value": "+0.75", "description": "Overall market sentiment", "color": "purple"},
    "Prediction Accuracy": {"value": "87%", "description": "Success rate of predictions", "color": "orange"}
}

# Display metrics in a grid
col1, col2 = st.columns(2)
metric_cols = [col1, col2, col1, col2]

for (metric_name, metric_data), col in zip(metrics.items(), metric_cols):
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <div style="height: 4px; width: 64px; background-color: {metric_data['color']}; margin-bottom: 16px;"></div>
                <h2 style="font-size: 2.5rem; font-weight: bold; margin-bottom: 16px;">{metric_data['value']}</h2>
                <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 8px;">{metric_name}</h3>
                <p style="color: #6B7280; font-size: 0.875rem;">{metric_data['description']}</p>
            </div>
        """, unsafe_allow_html=True)

# Toggle switches for analysis types
st.markdown("### Analysis Settings")
col1, col2, col3 = st.columns(3)

with col1:
    sentiment_toggle = st.toggle("Include Sentiment Analysis", value=False)
with col2:
    technical_toggle = st.toggle("Include Technical Indicators", value=False)
with col3:
    fundamental_toggle = st.toggle("Include Fundamental Data", value=False)

# Sentiment Section
st.markdown("### Sentiment Input")
st.markdown("Include market sentiment and see how public opinion shapes stock predictions.")
st.markdown("Baseline: 2 Jan 2025", help="Reference date for sentiment analysis")

# Create sample stock data
stocks_data = {
    "Symbol": ["AAPL", "AMZN", "GOOG", "MA", "QQQQ", "WMT"],
    "Name": ["Apple", "Amazon", "Google", "Mastercard", "Nasdaq", "Walmart"],
    "Price": ["$99.99", "$99.99", "$99.99", "$99.99", "$99.99", "$99.99"],
    "Change": ["+0.7562%", "+0.6762%", "-0.2562%", "-0.6562%", "+0.4562%", "+0.3562%"],
    "Sentiment": ["Positive", "Positive", "Negative", "Negative", "Positive", "Positive"],
    "Action": ["Buy", "Buy", "Sell", "Sell", "Buy", "Buy"]
}

df = pd.DataFrame(stocks_data)

# Style the dataframe
def color_sentiment(val):
    color = 'green' if val == 'Positive' else 'red'
    return f'color: {color}'

def color_change(val):
    color = 'green' if '+' in val else 'red'
    return f'color: {color}'

# Display styled dataframe
st.markdown("### Stock Analysis")
styled_df = df.style\
    .applymap(color_sentiment, subset=['Sentiment'])\
    .applymap(color_change, subset=['Change'])

st.dataframe(styled_df, use_container_width=True)

# Add Stock Button
if st.button("➕ Add Stock"):
    st.info("Stock addition functionality would go here")

# Optional: Add a simple line chart for visualization
st.markdown("### Market Trend")
chart_data = pd.DataFrame({
    'Date': pd.date_range(start='2025-01-01', periods=30),
    'Value': [100 + i + (i**2)*0.1 for i in range(30)]
})

fig = go.Figure()
fig.add_trace(go.Scatter(x=chart_data['Date'], y=chart_data['Value'], mode='lines'))
fig.update_layout(
    title="Portfolio Performance",
    xaxis_title="Date",
    yaxis_title="Value",
    height=400,
    margin=dict(l=0, r=0, t=40, b=0)
)

st.plotly_chart(fig, use_container_width=True)
