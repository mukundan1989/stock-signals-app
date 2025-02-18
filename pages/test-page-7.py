import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Custom CSS for enhanced dark theme
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #0B0F19;
        color: #E6E6E6;
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Input box styling */
    .stTextInput > div > div {
        background-color: #1A1F2F;
        border-radius: 8px;
        border: 1px solid #2D3347;
        padding: 2px 12px;
    }
    .stTextInput > div > div:hover {
        border-color: #00FF94;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);
        color: #0B0F19;
        font-weight: 600;
        border: none;
        padding: 10px 25px;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #00B8FF 0%, #00FF94 100%);
    }
    
    /* Metric container styling */
    .metric-container {
        background-color: #1A1F2F;
        border: 1px solid #2D3347;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
        border-color: #00FF94;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1F2F;
        border-radius: 8px;
        padding: 12px 24px;
        color: #E6E6E6;
        border: 1px solid #2D3347;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);
        color: #0B0F19;
        font-weight: 600;
        border: none;
    }
    
    /* Table styling */
    .stDataFrame {
        background-color: #1A1F2F;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #2D3347;
    }
    .dataframe {
        border: none !important;
    }
    .dataframe th {
        background-color: #2D3347 !important;
        color: #E6E6E6 !important;
        padding: 12px !important;
    }
    .dataframe td {
        background-color: #1A1F2F !important;
        color: #E6E6E6 !important;
        padding: 10px !important;
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
tabs = st.tabs(["GTrends", "News", "Twitter", "Overall"])

def create_price_chart():
    # Sample data
    dates = pd.date_range(start='2024-01-01', end='2024-02-18', freq='D')
    prices = [100 + i + (i**1.5)*0.1 for i in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        fill='tozeroy',
        fillcolor='rgba(0, 255, 148, 0.1)',
        line=dict(
            color='#00FF94',
            width=2
        ),
        name='Price'
    ))
    
    fig.update_layout(
        plot_bgcolor='#1A1F2F',
        paper_bgcolor='#1A1F2F',
        font=dict(color='#E6E6E6'),
        margin=dict(l=0, r=0, t=20, b=0),
        height=350,
        xaxis=dict(
            showgrid=True,
            gridcolor='#2D3347',
            gridwidth=0.5,
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#2D3347',
            gridwidth=0.5,
            title=None
        ),
        hovermode='x unified'
    )
    return fig

def create_metrics_grid():
    col1, col2 = st.columns(2)
    with col1:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown('''
                <div class="metric-container">
                    <h3 style="margin:0;font-size:0.9em;color:#8B8FA3">Win %</h3>
                    <h2 style="margin:10px 0;font-size:1.8em;background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;">75.5%</h2>
                    <p style="margin:0;font-size:0.8em;color:#8B8FA3">↑ 5.2% vs last month</p>
                </div>
            ''', unsafe_allow_html=True)
        with m2:
            st.markdown('''
                <div class="metric-container">
                    <h3 style="margin:0;font-size:0.9em;color:#8B8FA3">No. of Trades</h3>
                    <h2 style="margin:10px 0;font-size:1.8em;background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;">142</h2>
                    <p style="margin:0;font-size:0.8em;color:#8B8FA3">↓ 3.4% vs last month</p>
                </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        m3, m4 = st.columns(2)
        with m3:
            st.markdown('''
                <div class="metric-container">
                    <h3 style="margin:0;font-size:0.9em;color:#8B8FA3">Profit Factor</h3>
                    <h2 style="margin:10px 0;font-size:1.8em;background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;">2.4</h2>
                    <p style="margin:0;font-size:0.8em;color:#8B8FA3">↑ 0.3 vs last month</p>
                </div>
            ''', unsafe_allow_html=True)
        with m4:
            st.markdown('''
                <div class="metric-container">
                    <h3 style="margin:0;font-size:0.9em;color:#8B8FA3">vs S&P</h3>
                    <h2 style="margin:10px 0;font-size:1.8em;background: linear-gradient(90deg, #00FF94 0%, #00B8FF 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;">+12.3%</h2>
                    <p style="margin:0;font-size:0.8em;color:#8B8FA3">↑ 2.1% vs last month</p>
                </div>
            ''', unsafe_allow_html=True)

def create_trade_table():
    data = {
        'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
        'Trade Type': ['Long', 'Short', 'Long', 'Short'],
        'Holding Period': ['2d', '3d', '1d', '4d'],
        '%P/L': ['+2.5%', '-1.2%', '+3.1%', '+0.8%']
    }
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, use_container_width=True)

# Populate each tab with the same components
for tab in tabs:
    with tab:
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Price performance chart
        st.plotly_chart(create_price_chart(), use_container_width=True)
        
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Metrics grid
        create_metrics_grid()
        
        # Add some spacing
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Trade table
        st.subheader("Trade History")
        create_trade_table()
