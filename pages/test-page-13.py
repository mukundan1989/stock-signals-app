import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import uuid  # For unique chart identifiers

# Page config
st.set_page_config(page_title="Stock Signal Page", layout="wide")

# Function to generate dummy stock price data
def generate_stock_price_data():
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    prices = np.cumsum(np.random.randn(30) * 2) + 150  # Simulated price trend
    return pd.DataFrame({"Date": dates, "Price": prices})

# Function to create the stock price line chart
def create_stock_price_chart():
    df = generate_stock_price_data()
    fig = px.line(df, x="Date", y="Price", title="Stock Price Trends")

    fig.update_traces(line=dict(color="#00ff9f", width=2))  # Green Line
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ffffff",
        title_font_size=18,
        showlegend=False,
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(255,255,255,0.1)"),
        height=250  # Reduced height for alignment
    )
    return fig

# Main title
st.title("Stock Signal Page")

# Box: Company Information with Stock Price Chart
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Company Overview</h2>
    </div>
""", unsafe_allow_html=True)

# Two-column layout: Left (Company Info) | Right (Stock Price Chart)
col1, col2 = st.columns([1, 2])

# Left: Company Info
with col1:
    st.markdown("""
        <div style="text-align: left; color: white;">
            <div class="company-symbol" style="font-size: 32px; font-weight: bold; color: #bb86fc;">AAPL</div>
            <div style="margin: 10px 0;">Apple Inc.</div>
            <div class="company-price" style="font-size: 28px; color: #00ff9f; font-weight: bold;">$175.34</div>
        </div>
    """, unsafe_allow_html=True)

# Right: Stock Price Chart
with col2:
    st.plotly_chart(create_stock_price_chart(), use_container_width=True, key=str(uuid.uuid4()))
