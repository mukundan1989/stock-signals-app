import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Custom CSS for elegant table design
st.markdown(
    """
    <style>
    .pretty-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: #ffffff;
    }
    .pretty-table thead tr {
        background-color: #000000;
        color: #ffffff;
        text-align: center;
        border: none;
    }
    .pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
        border: none;
    }
    .pretty-table tbody tr:nth-of-type(odd) {
        background-color: #3a3a3a;
    }
    .pretty-table tbody tr:nth-of-type(even) {
        background-color: #4a4a4a;
    }
    .pretty-table tbody tr:hover {
        background-color: #5a5a5a;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
        SELECT COUNT(*) AS total_trades, 
               (COUNT(CASE WHEN `30d_pl` > 0 OR `60d_pl` > 0 THEN 1 END) / COUNT(*)) * 100 AS win_percentage,
               COALESCE(SUM(CASE WHEN `30d_pl` > 0 THEN `30d_pl` ELSE 0 END) / 
               NULLIF(ABS(SUM(CASE WHEN `30d_pl` < 0 THEN `30d_pl` ELSE 0 END)), 0), 0) AS profit_factor
        FROM models_performance WHERE comp_symbol = %s;
        """
        
        cursor.execute(query, (comp_symbol,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_trades": result[0] if result else "N/A",
            "win_percentage": f"{result[1]:.2f}%" if result else "N/A",
            "profit_factor": f"{result[2]:.2f}" if result else "N/A"
        }
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

# Create tabs
tab_names = ["GTrends", "News", "Twitter", "Overall"]
tabs = st.tabs(tab_names)

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Win %", metrics['win_percentage'])
        col2.metric("No. of Trades", metrics['total_trades'])
        col3.metric("Profit Factor", metrics['profit_factor'])
    
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                table_html = df.to_html(index=False, classes="pretty-table")
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
