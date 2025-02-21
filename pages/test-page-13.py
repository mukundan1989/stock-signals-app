import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
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
        font-size: 48px;
        text-align: center;
    }
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Function to create stock price trend chart
def create_stock_price_chart():
    # Generate fake stock price data
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    stock_prices = [175 + (i * 0.5) for i in range(30)]  # Simulated increasing stock price

    df_stock = pd.DataFrame({'Date': dates, 'Stock Price': stock_prices})

    fig = px.line(df_stock, x='Date', y='Stock Price', title="Stock Price Trend")

    fig.update_traces(
        line=dict(color='#00ff9f', width=2)
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_size=16,
        showlegend=False,
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)'),
        height=200
    )

    return fig

# Function to create a unique donut chart
def create_donut_chart():
    data = pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })
    fig = px.pie(data, 
                 values='Percentage', 
                 names='Sentiment',
                 hole=0.6,
                 color_discrete_map={
                     'Positive': '#00ff00',
                     'Negative': '#ff0000',
                     'Neutral': '#808080'
                 })
    fig.update_layout(
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        height=180,
        width=180,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        legend=dict(
            font=dict(color='#ffffff'),
            bgcolor='rgba(0,0,0,0)'
        )
    )
    fig.for_each_trace(lambda trace: trace.update(name=str(uuid.uuid4())))
    return fig

# Function to create a speedometer with yellowish green to elegant green transition
def create_speedometer():
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=70,  # Example Value
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#006400"},  # Elegant Green (Dark Green)
            'steps': [
                {'range': [0, 50], 'color': "#cddc39"},  # Yellowish Green
                {'range': [50, 75], 'color': "#8bc34a"},  # Fresh Green
                {'range': [75, 100], 'color': "#006400"}  # Elegant Green (Dark Green)
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 85}
        }
    ))

    fig.update_layout(
        height=180,
        width=180,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )

    return fig

# Centered title using Markdown and CSS
st.markdown("""
    <h1 style="text-align: center; color: #bb86fc;">Stock Signal Page</h1>
""", unsafe_allow_html=True)

# **Company Information Block** with Stock Chart on the Right
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Company Information</h2>
    </div>
""", unsafe_allow_html=True)

# Create 2 columns (Left: Company Info, Right: Stock Price Chart)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
        <div style="text-align: left; color: white;">
            <div class="company-symbol" style="font-size: 32px; font-weight: bold; color: #bb86fc;">AAPL</div>
            <div style="margin: 10px 0; font-size: 20px;">Apple Inc.</div>
            <div class="company-price" style="font-size: 28px; color: #00ff9f; font-weight: bold;">$175.34</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_stock_price_chart(), use_container_width=True, key=str(uuid.uuid4()))

# **Twitter Trends Block**
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Twitter Trend Insight</h2>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">145</div>
            <div class="metric-label">Keywords</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=True, key=str(uuid.uuid4()))

with col3:
    st.markdown('<div class="sentiment-icon">🐂</div>', unsafe_allow_html=True)

# **News Insight Block**
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">News Insight</h2>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">145</div>
            <div class="metric-label">Keywords</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_speedometer(), use_container_width=True, key=str(uuid.uuid4()))  # Speedometer

with col3:
    st.markdown('<div class="sentiment-icon" style="color: #00ff00;">⬆️</div>', unsafe_allow_html=True)  # Green Up Arrow
