import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    .st-bq {
        color: #ffffff;
    }
    .st-cb {
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("📈 Stock Analysis Dashboard")
st.markdown("---")

# Dummy stock price data
def generate_stock_data():
    dates = pd.date_range(end=datetime.today(), periods=180, freq='D')
    prices = np.cumsum(np.random.randn(180)) + 100  # Random walk for stock prices
    return pd.DataFrame({"Date": dates, "Price": prices})

stock_data = generate_stock_data()

# Stock Price Area Chart
st.subheader("Stock Price (Last 6 Months)")
fig = px.area(
    stock_data,
    x="Date",
    y="Price",
    title="",
    labels={"Price": "Stock Price ($)", "Date": "Date"},
    template="plotly_dark",
    line_shape="spline"
)
fig.update_traces(fill='tozeroy', line=dict(color='#00FF00'), fillcolor='rgba(0,255,0,0.2)')
fig.update_layout(
    xaxis_title="",
    yaxis_title="",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white')
)
st.plotly_chart(fig, use_container_width=True)

# Sentiment Gauges
col1, col2 = st.columns(2)

# Social Media Sentiment Gauge
with col1:
    st.subheader("Social Media Sentiment")
    social_media_sentiment = np.random.randint(-100, 100)  # Dummy sentiment value
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=social_media_sentiment,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Bullish/Bearish", 'font': {'color': 'white'}},
        gauge={
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': 'white'},
            'bar': {'color': 'limegreen' if social_media_sentiment >= 0 else 'red'},
            'bgcolor': 'black',
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [-100, 0], 'color': 'red'},
                {'range': [0, 100], 'color': 'limegreen'}
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Annual Results Sentiment Gauge
with col2:
    st.subheader("Annual Results Sentiment")
    annual_sentiment = np.random.randint(0, 100)  # Dummy sentiment value
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=annual_sentiment,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Bullish/Bearish", 'font': {'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': 'white'},
            'bar': {'color': 'limegreen'},
            'bgcolor': 'black',
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [0, 50], 'color': 'red'},
                {'range': [50, 100], 'color': 'limegreen'}
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("© 2023 Stock Analysis Dashboard | Made with Streamlit")
