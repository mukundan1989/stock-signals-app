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
    </style>
    """, unsafe_allow_html=True)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch model data
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
        WHERE comp_symbol = %s AND model = %s AND sentiment != 'neutral'
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

# Function to fetch and compute cumulative P/L
def fetch_cumulative_pl(comp_symbol):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = """
        SELECT date, SUM(`30d_pl`) AS daily_pl
        FROM models_performance
        WHERE comp_symbol = %s AND sentiment != 'neutral'
        GROUP BY date ORDER BY date;
        """
        cursor.execute(query, (comp_symbol,))
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=["Date", "Daily P/L"])
        df["Cumulative P/L"] = df["Daily P/L"].cumsum()
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching cumulative P/L data: {e}")
        return None

# Function to create cumulative P/L chart
def create_cumulative_pl_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], 
        y=df["Cumulative P/L"],
        mode='lines+markers',
        line=dict(color='green' if df["Cumulative P/L"].iloc[-1] > 0 else 'red', width=2),
        marker=dict(size=5),
        name='Cumulative P/L'
    ))
    fig.update_layout(
        title="Cumulative Profit/Loss Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative P/L",
        plot_bgcolor='#1A1F2F',
        paper_bgcolor='#1A1F2F',
        font=dict(color='#E6E6E6'),
        height=400
    )
    return fig

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
    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.subheader("Cumulative Profit/Loss Chart")
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)
    
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
