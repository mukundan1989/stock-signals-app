import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Apply dark theme using custom CSS
st.markdown(
    """
    <style>
        body {
            background-color: #121212 !important;
            color: #e0e0e0 !important;
        }
        .stTextInput>div>div>input, .stButton>button {
            background-color: #333333 !important;
            color: white !important;
        }
        .stDataFrame {
            background-color: #222222 !important;
        }
        .stMetric {
            color: white !important;
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
            value = result[0] if result and result[0] is not None else "N/A"

            # Round profit factor to 2 decimal places
            if key == "profit_factor" and isinstance(value, (int, float)):
                value = round(value, 2)

            results[key] = value

        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None

# Function to fetch and compute cumulative P/L data
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

# Function to create the cumulative P/L graph
def create_cumulative_pl_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], 
        y=df["Cumulative P/L"],
        mode='lines+markers',
        line=dict(color='cyan' if df["Cumulative P/L"].iloc[-1] > 0 else 'red', width=2),
        marker=dict(size=5),
        name='Cumulative P/L'
    ))
    
    # Apply dark mode styling
    fig.update_layout(
        title="Cumulative Profit/Loss Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative P/L",
        plot_bgcolor="#121212",  # Dark background for plot area
        paper_bgcolor="#121212",  # Dark background for outer area
        font=dict(color="white"),  # White text for visibility
        xaxis=dict(showgrid=True, gridcolor="#333333", zerolinecolor="#444444"),
        yaxis=dict(showgrid=True, gridcolor="#333333", zerolinecolor="#444444"),
        height=400
    )
    
    return fig

# Title and search section
st.title("Performance Summary")

col1, col2 = st.columns([4, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
with col2:
    st.write("")  # Add a small space to align with input label
    go_clicked = st.button("Go")

# Create tabs
tab_names = ["GTrends", "News", "Twitter", "Overall"]
tabs = st.tabs(tab_names)

if go_clicked:
    # 1️⃣ Show Performance Metrics first
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Win %", f"{metrics['win_percentage']}%")
        col2.metric("No. of Trades", f"{metrics['total_trades']}")
        col3.metric("Profit Factor", f"{metrics['profit_factor']}")

    # 2️⃣ Show Equity Curve next
    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.subheader("Equity Curve")
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)

    # 3️⃣ Show the model data table last
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
