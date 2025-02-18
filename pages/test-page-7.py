import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0B0F19;
        color: #E6E6E6;
    }
    h1 {
        color: #E6E6E6;
        font-weight: 700;
    }
    .stTextInput > div > div {
        background-color: #1A1F2F;
        border-radius: 8px;
        border: 1px solid #2D3347;
    }
    .stButton > button {
        background-color: #007BFF;
        color: white;
        border-radius: 8px;
        height: 42px;
    }
    .metric-container {
        background-color: #1A1F2F;
        border: 1px solid #2D3347;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        text-align: center;
    }
    .stDataFrame {
        background-color: #1A1F2F;
        color: #E6E6E6;
    }
    .stDataFrame th {
        background-color: #2D3347 !important;
        color: #E6E6E6 !important;
    }
    .stDataFrame td {
        background-color: #1A1F2F !important;
        color: #E6E6E6 !important;
    }
    .stDataFrame tr:hover {
        background-color: #2D3347 !important;
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
        
        query = """
        SELECT (COUNT(CASE WHEN (`30d_pl` > 0 OR `60d_pl` > 0) AND sentiment != 'neutral' THEN 1 END) 
                / COUNT(CASE WHEN sentiment != 'neutral' THEN 1 END)) * 100 AS win_percentage,
               COUNT(*) AS total_trades,
               COALESCE(SUM(CASE WHEN `30d_pl` > 0 THEN `30d_pl` ELSE 0 END), 0) / 
               NULLIF(ABS(SUM(CASE WHEN `30d_pl` < 0 THEN `30d_pl` ELSE 0 END)), 0) AS profit_factor
        FROM models_performance WHERE comp_symbol = %s;
        """
        
        cursor.execute(query, (comp_symbol,))
        result = cursor.fetchone()
        
        metrics = {
            "win_percentage": result[0] if result and result[0] is not None else "N/A",
            "total_trades": result[1] if result and result[1] is not None else "N/A",
            "profit_factor": result[2] if result and result[2] is not None else "N/A"
        }
        
        cursor.close()
        conn.close()
        
        return metrics
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.write("")
    go_clicked = st.button("Go", type="primary")

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Win %", f"{metrics['win_percentage']}%")
        col2.metric("No. of Trades", f"{metrics['total_trades']}")
        col3.metric("Profit Factor", f"{metrics['profit_factor']}")
    
    st.subheader("Cumulative Profit/Loss Chart")
    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)
    
    tabs = st.tabs(["GTrends", "News", "Twitter", "Overall"])
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
