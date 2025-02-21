import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import uuid  # For unique chart identifiers

# Page config
st.set_page_config(page_title="Stock Signal Page", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .box-container {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border: 1px solid #333333;
        text-align: center;
    }
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        color: #bb86fc;
    }
    .metric-label {
        font-size: 16px;
        text-align: center;
        color: #ffffff;
        margin-top: 5px;
    }
    .box-title {
        color: #bb86fc;
        font-size: 24px;
        margin-bottom: 10px;
    }
    .sentiment-icon {
        font-size: 64px; /* Increased size */
        text-align: center;
        color: #00bfa5; /* Bluish Green */
    }
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Function to create realistic stock price trend chart
def create_stock_price_chart():
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    prices = [175]
    for _ in range(29):
        prices.append(prices[-1] * (1 + np.random.uniform(-0.02, 0.02)))  # Simulating real-life price fluctuations
    df_stock = pd.DataFrame({'Date': dates, 'Stock Price': prices})
    
    fig = px.line(df_stock, x='Date', y='Stock Price', title="Stock Price Trend")
    fig.update_traces(line=dict(color='#00ff9f', width=2))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_size=16,
        showlegend=False,
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)'),
        height=300
    )
    return fig

# Title (Now in White)
st.markdown("""
    <h1 style="text-align: center; color: white;">Stock Signal Page</h1>
""", unsafe_allow_html=True)

# News Insight Block
st.markdown("<div class='box-container'><h2 class='box-title'>News Insight</h2></div>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<div class='metric-value'>145</div><div class='metric-label'>Keywords</div>", unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_stock_price_chart(), use_container_width=True, key=str(uuid.uuid4()))

with col3:
    st.markdown("<div class='sentiment-icon'>&#9650;</div>", unsafe_allow_html=True)  # Large Bluish Green Triangle Up Arrow

# Twitter Trends Block
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Twitter Trend Insight</h2>
    </div>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<div class='metric-value'>145</div><div class='metric-label'>Keywords</div>", unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_stock_price_chart(), use_container_width=True, key=str(uuid.uuid4()))

with col3:
    st.markdown("<div class='sentiment-icon'>&#9650;</div>", unsafe_allow_html=True)  # Large Bluish Green Triangle Up Arrow
