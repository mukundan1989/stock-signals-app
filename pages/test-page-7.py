import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Custom CSS for dark theme
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #0B0F19;
        color: #E6E6E6;
    }
    
    /* Title styling */
    h1 {
        color: #E6E6E6;
        font-weight: 700;
    }
    
    /* Input box styling */
    .stTextInput > div > div {
        background-color: #1A1F2F;
        border-radius: 8px;
        border: 1px solid #2D3347;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007BFF;
        color: white;
        border-radius: 8px;
        height: 42px;
    }
    
    /* Metric container styling */
    .metric-container {
        background-color: #1A1F2F;
        border: 1px solid #2D3347;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        text-align: center;
    }
    
    /* Table styling */
    .stDataFrame {
        background-color: #1A1F2F;
        color: #E6E6E6;
    }
    </style>
    """, unsafe_allow_html=True)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch performance metrics
def fetch_performance_metrics(comp_symbol):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        queries = {
            "win_percentage": """
                SELECT (COUNT(CASE WHEN (`30d_pl` > 0 OR `60d_pl` > 0) AND sentiment != 'neutral' THEN 1 END) 
                / COUNT(CASE WHEN sentiment != 'neutral' THEN 1 END)) * 100 AS win_percentage
                FROM models_performance WHERE comp_symbol = %s;
            """,
            "total_trades": """
                SELECT COUNT(*) AS total_trades FROM models_performance
                WHERE comp_symbol = %s AND sentiment != 'neutral';
            """,
            "profit_factor": """
                SELECT COALESCE(SUM(CASE WHEN `30d_pl` > 0 AND sentiment != 'neutral' THEN `30d_pl` ELSE 0 END), 0) / 
                NULLIF(ABS(SUM(CASE WHEN `30d_pl` < 0 AND sentiment != 'neutral' THEN `30d_pl` ELSE 0 END)), 0) 
                AS profit_factor FROM models_performance WHERE comp_symbol = %s;
            """
        }
        
        results = {}
        for key, query in queries.items():
            cursor.execute(query, (comp_symbol,))
            result = cursor.fetchone()
            results[key] = result[0] if result and result[0] is not None else "N/A"
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.write("")  # Add a small space to align with input label
    go_clicked = st.button("Go", type="primary")

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-container"><h3>Win %</h3><h2 style="color:#00FF94">{metrics["win_percentage"]}%</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-container"><h3>No. of Trades</h3><h2 style="color:#00FF94">{metrics["total_trades"]}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-container"><h3>Profit Factor</h3><h2 style="color:#00FF94">{metrics["profit_factor"]}</h2></div>', unsafe_allow_html=True)
    
    st.subheader("Cumulative Profit/Loss Chart")
    st.plotly_chart(go.Figure(), use_container_width=True)  # Placeholder for chart
