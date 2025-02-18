import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch data from the database
def fetch_model_data(comp_symbol, model_name):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        query = """
        SELECT date, sentiment, entry_price, `30d_pl`, `60d_pl`
        FROM models_performance
        WHERE comp_symbol = %s AND model = %s
        """
        
        cursor.execute(query, (comp_symbol, model_name))
        result = cursor.fetchall()
        columns = ["Date", "Sentiment", "Entry Price", "30D P/L", "60D P/L"]
        df = pd.DataFrame(result, columns=columns)
        
        cursor.close()
        conn.close()
        
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to create dummy price chart
def create_price_chart():
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    prices = [100 + i * 0.5 for i in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, fill='tozeroy', line=dict(color='#00FF94', width=2), name='Price'))
    fig.update_layout(plot_bgcolor='#1A1F2F', paper_bgcolor='#1A1F2F', font=dict(color='#E6E6E6'), height=350)
    return fig

# Function to create dummy metric boxes
def create_metrics_grid():
    col1, col2 = st.columns(2)
    with col1:
        m1, m2 = st.columns(2)
        with m1:
            st.metric(label="Win %", value="75.5%")
        with m2:
            st.metric(label="No. of Trades", value="142")
    with col2:
        m3, m4 = st.columns(2)
        with m3:
            st.metric(label="Profit Factor", value="2.4")
        with m4:
            st.metric(label="vs S&P", value="+12.3%")

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.write("")  # Add a small space to align with input label
    go_clicked = st.button("Go", type="primary")

# Create tabs
tab_names = ["GTrends", "News", "Twitter", "Overall"]
tabs = st.tabs(tab_names)

if go_clicked:
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            st.plotly_chart(create_price_chart(), use_container_width=True)
            create_metrics_grid()
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
