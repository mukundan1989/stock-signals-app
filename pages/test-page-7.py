import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Custom CSS for dark-themed elegant table design
st.markdown(
    """
    <style>
    /* Target the main container (st-emotion-cache-bm2z3a) and set a dark grey background */
    .st-emotion-cache-bm2z3a {
        background-color: #2a2a2a; /* Dark grey background */
        color: #ffffff; /* White text for the entire page */
    }

    /* Custom CSS for elegant table design */
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
        color: #ffffff; /* White text for the table */
    }

    /* Black header with white text */
    .pretty-table thead tr {
        background-color: #000000; /* Black header */
        color: #ffffff; /* White text */
        text-align: center;
        border: none;
    }

    /* Padding for table cells */
    .pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
        border: none;
    }

    /* Alternating row colors: light grey and dark grey */
    .pretty-table tbody tr:nth-of-type(odd) {
        background-color: #3a3a3a; /* Dark grey */
    }

    .pretty-table tbody tr:nth-of-type(even) {
        background-color: #4a4a4a; /* Light grey */
    }

    /* Hover effect for rows */
    .pretty-table tbody tr:hover {
        background-color: #5a5a5a; /* Slightly lighter grey on hover */
    }

    /* Ensure the text above the table is white */
    h1, h2, h3, h4, h5, h6, p {
        color: #ffffff !important; /* White text for titles and paragraphs */
    }

    /* Ensure Streamlit widgets (like text input and buttons) are styled appropriately */
    .stTextInput input, .stButton button {
        color: #ffffff;
        background-color: #4a4a4a;
        border: 1px solid #5a5a5a;
    }

    /* Ensure Plotly charts have a dark background */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly div {
        background-color: #2a2a2a !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
        line=dict(color='green' if df["Cumulative P/L"].iloc[-1] > 0 else 'red', width=2),
        marker=dict(size=5),
        name='Cumulative P/L'
    ))
    fig.update_layout(
        title="Cumulative Profit/Loss Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative P/L",
        plot_bgcolor='#2a2a2a',  # Dark background for the chart
        paper_bgcolor='#2a2a2a',  # Dark background for the chart area
        font=dict(color='white'),  # White text for the chart
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
    go_clicked = st.button("Go", type="primary")

# Create tabs
tab_names = ["GTrends", "News", "Twitter", "Overall"]
tabs = st.tabs(tab_names)

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Win %", f"{metrics['win_percentage']}%")
        col2.metric("No. of Trades", f"{metrics['total_trades']}")
        col3.metric("Profit Factor", f"{metrics['profit_factor']}")
    
    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)
    
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                table_html = df.to_html(index=False, classes="pretty-table")
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
