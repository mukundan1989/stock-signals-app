import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import uuid  # For unique chart identifiers

# Page config
st.set_page_config(page_title="Stock Signal Page", layout="wide")

# Apply modern glassmorphism CSS
st.markdown("""
    <style>
    /* Glassmorphism Metric Card */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        transition: transform 0.3s ease;
        text-align: center;
        margin: 10px;
    }

    .stHorizontalBlock {
        background-color: black; /* Set background color to black */
        border-radius: 20px; /* Adjust the border-radius for rounded edges */
        padding: 10px 20px 20px 20px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }
    
    .metric-trend {
        font-size: 0.85rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
    }

    /* Trend Colors */
    .positive { color: #00ff9f; }  /* Green */
    .negative { color: #ff4b4b; }  /* Red */

    /* Grid container for metric boxes */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        justify-content: center;
        align-items: center;
    }

    @media (max-width: 600px) {
        .grid-container { grid-template-columns: repeat(2, 1fr); gap: 5px; }
    }

    /* Styling for the metric boxes */
    .metric-box {
        background: linear-gradient(10deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box h2 {
        margin-top: 30px;
        margin-left: 5px;
        margin-bottom: 1px;
    }

    .metric-box p {
        margin-left: 5px;
        margin-bottom: 0;
    }

    /* Second grid box with pile of cash icon */
    .metric-box-gain {
        background: linear-gradient(15deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-gain::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4zM3 6h18m-5 4a4 4 0 0 1-8 0"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-gain h2 {
        margin-top: 30px;
        margin-left: 5px;
        margin-bottom: 1px;
    }

    .metric-box-gain p {
        margin-left: 5px;
        margin-bottom: 0;
    }

    /* Third grid box with speedometer gauge icon */
    .metric-box-speedometer {
        background: linear-gradient(15deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-speedometer::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 1 0 0 7h5a3.5 3.5 0 1 1 0 7H6"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-speedometer h2 {
        margin-top: 30px;
        margin-left: 5px;
        margin-bottom: 1px;
    }

    .metric-box-speedometer p {
        margin-left: 5px;
        margin-bottom: 0;
    }

    /* Custom CSS for Twitter and News blocks */
    .block-title {
        font-size: 24px;
        font-weight: bold;
        color: white;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .sentiment-icon {
        font-size: 48px;
        text-align: center;
        color: #00ff00;
    }

    /* Center align text vertically */
    .vertical-center {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }

    /* Larger arrow icon */
    .large-arrow {
        font-size: 100px;
        color: #00ff9f;
    }

    /* Custom CSS for the title with logo */
    .title-with-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px; /* Space between logo and title */
    }

    .title-with-logo img {
        width: 70px; /* Adjust the size of the logo */
        height: 70px;
        /*background: #000;*/
        padding: 3px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Function to create a realistic stock price trend chart
def create_stock_price_chart():
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    # Simulate realistic stock price fluctuations
    stock_prices = [175 + (i * 0.5) + np.random.normal(0, 1) for i in range(30)]
    df_stock = pd.DataFrame({'Date': dates, 'Stock Price': stock_prices})
    
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

# Function to create a donut chart
def create_donut_chart():
    data = pd.DataFrame({'Sentiment': ['Positive', 'Negative', 'Neutral'], 'Percentage': [45, 30, 25]})
    fig = px.pie(data, values='Percentage', names='Sentiment', hole=0.6, color_discrete_map={
        'Positive': '#00ff00', 'Negative': '#ff0000', 'Neutral': '#808080'
    })
    fig.update_layout(
        showlegend=True, margin=dict(t=20, b=20, l=20, r=20), height=200, width=200,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'), legend=dict(font=dict(color='#ffffff'), bgcolor='rgba(0,0,0,0)')
    )
    fig.for_each_trace(lambda trace: trace.update(name=str(uuid.uuid4())))
    return fig

# Function to create a speedometer
def create_speedometer():
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=70,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]}, 'bar': {'color': "#006400"},
            'steps': [
                {'range': [0, 50], 'color': "#cddc39"},
                {'range': [50, 75], 'color': "#8bc34a"},
                {'range': [75, 100], 'color': "#006400"}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 85}
        }
    ))
    fig.update_layout(height=200, width=200, margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
    return fig

# Title with Twitter logo
st.markdown(
    """
    <div class="title-with-logo">
        <img src="https://raw.githubusercontent.com/mukundan1989/stock-signals-app/refs/heads/main/images/stocksignal-icon.png" alt="Twitter Logo" class="logo">
        <h1 style='text-align: center;'>Stock Signal Page</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Page description
st.write("<p style='text-align: center;'>Insights and Analysis from various models.</p>", unsafe_allow_html=True)

# Company Information Block
st.markdown("""
    <div class="grid-container">
        <div class="metric-box">
            <h2>AAPL</h2>
            <p>Apple Inc.</p>
        </div>
        <div class="metric-box-gain">
            <h2>$175.34</h2>
            <p>Current Price</p>
        </div>
        <div class="metric-box-speedometer">
            <h2>70%</h2>
            <p>Sentiment Score</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Stock Price Trend Chart
st.plotly_chart(create_stock_price_chart(), use_container_width=True, key=str(uuid.uuid4()))

# Twitter Sentiment Block
st.markdown("""
    <div class="block-title">Twitter Sentiment</div>
""", unsafe_allow_html=True)

# Create three columns for the layout
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    # First column: Keyword analyzed and count
    st.markdown("""
        <div class="vertical-center">
            <div>
                <h2 style="text-align: center; color: white;">Keywords Analyzed</h2>
                <p style="font-size: 24px; font-weight: bold; text-align: center; color: white;">145</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    # Second column: Donut chart (only chart, no legend)
    donut_fig = create_donut_chart()
    donut_fig.update_layout(showlegend=False)  # Hide the legend
    st.plotly_chart(donut_fig, use_container_width=True, key=str(uuid.uuid4()))

with col3:
    # Third column: Green arrow icon
    st.markdown("""
        <div class="vertical-center">
            <span class="large-arrow">&#9650;</span>
        </div>
    """, unsafe_allow_html=True)

# News Sentiment Block
st.markdown("""
    <div class="block-title">News Sentiment</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="vertical-center">
            <div>
                <h2 style="text-align: center; color: white;">Positive Sentiment</h2>
                <p style="font-size: 24px; font-weight: bold; text-align: center; color: white;">70%</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_speedometer(), use_container_width=True, key=str(uuid.uuid4()))

with col3:
    st.markdown("""
        <div class="vertical-center">
            <span class="large-arrow">&#9650;</span>
        </div>
    """, unsafe_allow_html=True)
