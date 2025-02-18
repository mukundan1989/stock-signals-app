import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

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

# Apply dark style to tables
def style_dataframe(df):
    return df.style.set_properties(
        **{
            'background-color': '#2e2e2e',
            'color': 'white',
            'border-color': 'gray'
        }
    )

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
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(style_dataframe(df), use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
