import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set page config for dark theme
st.set_page_config(layout="wide", page_title="Stock Analysis Dashboard")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .css-1d391kg {
        background-color: #1B2838;
    }
    </style>
""", unsafe_allow_html=True)

# Generate dummy stock data
def generate_stock_data(days=180):
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    dates.reverse()
    
    # Generate synthetic stock prices with trend and volatility
    initial_price = 100
    prices = [initial_price]
    for i in range(1, days):
        change = np.random.normal(0.0001, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    return pd.DataFrame({
        'Date': dates,
        'Price': prices
    })

# Create dummy sentiment scores
social_media_sentiment = 75  # 0-100 scale
financial_sentiment = 62     # 0-100 scale

# Title
st.title("📈 Stock Analysis Dashboard")
st.markdown("---")

# Layout in columns
col1, col2 = st.columns([2, 1])

with col1:
    # Stock Price Chart
    stock_data = generate_stock_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stock_data['Date'],
        y=stock_data['Price'],
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)',
        line=dict(color='#00ff00', width=1),
        name='Stock Price'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title={
            'text': 'Stock Price Evolution',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=400,
        margin=dict(t=50, b=50, l=50, r=50),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Social Media Sentiment Gauge
    fig_social = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = social_media_sentiment,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Social Media Sentiment", 'font': {'size': 24, 'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#00ff00"},
            'bgcolor': "gray",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 33], 'color': '#ff0000'},
                {'range': [33, 66], 'color': '#ffff00'},
                {'range': [66, 100], 'color': '#00ff00'}
            ],
        }
    ))
    
    fig_social.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=50, b=0, l=30, r=30)
    )
    
    st.plotly_chart(fig_social, use_container_width=True)
    
    # Financial Analysis Sentiment Gauge
    fig_financial = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = financial_sentiment,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Financial Analysis Sentiment", 'font': {'size': 24, 'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#00ff00"},
            'bgcolor': "gray",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 33], 'color': '#ff0000'},
                {'range': [33, 66], 'color': '#ffff00'},
                {'range': [66, 100], 'color': '#00ff00'}
            ],
        }
    ))
    
    fig_financial.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=50, b=0, l=30, r=30)
    )
    
    st.plotly_chart(fig_financial, use_container_width=True)
