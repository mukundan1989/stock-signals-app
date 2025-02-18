import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-container {
        background-color: #1E2227;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .css-1d391kg {
        background-color: #1E2227;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
        background-color: #0E1117;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2227;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        color: #FAFAFA;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E3137;
    }
    .stDataFrame {
        background-color: #1E2227;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.button("Go", type="primary")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["GTrends", "News", "Twitter", "Overall"])

# Function to create sample price chart
def create_price_chart():
    # Sample data
    dates = pd.date_range(start='2024-01-01', end='2024-02-18', freq='D')
    prices = [100 + i + (i**1.5)*0.1 for i in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)',
        line=dict(color='#00FF00', width=2),
        name='Price'
    ))
    
    fig.update_layout(
        plot_bgcolor='#1E2227',
        paper_bgcolor='#1E2227',
        font=dict(color='#FAFAFA'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        xaxis=dict(
            showgrid=True,
            gridcolor='#2E3137',
            gridwidth=0.5,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#2E3137',
            gridwidth=0.5,
        )
    )
    return fig

# Function to create metrics grid
def create_metrics_grid():
    col1, col2 = st.columns(2)
    with col1:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown('<div class="metric-container">'
                       '<h3 style="margin:0">Win %</h3>'
                       '<h2 style="color:#00FF00;margin:10px 0">75.5%</h2>'
                       '</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="metric-container">'
                       '<h3 style="margin:0">No. of Trades</h3>'
                       '<h2 style="color:#00FF00;margin:10px 0">142</h2>'
                       '</div>', unsafe_allow_html=True)
    
    with col2:
        m3, m4 = st.columns(2)
        with m3:
            st.markdown('<div class="metric-container">'
                       '<h3 style="margin:0">Profit Factor</h3>'
                       '<h2 style="color:#00FF00;margin:10px 0">2.4</h2>'
                       '</div>', unsafe_allow_html=True)
        with m4:
            st.markdown('<div class="metric-container">'
                       '<h3 style="margin:0">vs S&P</h3>'
                       '<h2 style="color:#00FF00;margin:10px 0">+12.3%</h2>'
                       '</div>', unsafe_allow_html=True)

# Function to create trade table
def create_trade_table():
    data = {
        'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
        'Trade Type': ['Long', 'Short', 'Long', 'Short'],
        'Holding Period': ['2d', '3d', '1d', '4d'],
        '%P/L': ['+2.5%', '-1.2%', '+3.1%', '+0.8%']
    }
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, use_container_width=True)

# Content for each tab
for tab in [tab1, tab2, tab3, tab4]:
    with tab:
        # Price performance chart
        st.plotly_chart(create_price_chart(), use_container_width=True)
        
        # Metrics grid
        create_metrics_grid()
        
        # Trade table
        st.subheader("Trade History")
        create_trade_table()
