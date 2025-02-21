import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Glassmorphism CSS Styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #0A0F1C, #1A1F2C, #162037, #1E2A4A);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        transition: transform 0.3s ease;
        text-align: center;
    }

    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        font-weight: 600;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }

    .metric-trend {
        font-size: 0.85rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
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
            value = result[0] if result and result[0] is not None else "N/A"

            # Round off profit factor
            if key == "profit_factor" and isinstance(value, (int, float)):
                value = round(value, 2)

            results[key] = value

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
    st.write("")
    go_clicked = st.button("Go", type="primary")

# Performance Metrics Section
if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        cols = st.columns(3)

        metric_data = [
            {"label": "Win %", "value": f"{metrics['win_percentage']}%", "trend": None},
            {"label": "No. of Trades", "value": f"{metrics['total_trades']}", "trend": None},
            {"label": "Profit Factor", "value": f"{metrics['profit_factor']}", "trend": "positive" if metrics['profit_factor'] > 1 else "negative"}
        ]

        for col, metric in zip(cols, metric_data):
            trend_color = "#00ff9f" if metric['trend'] == "positive" else "#ff4b4b"
            trend_arrow = "↑" if metric['trend'] == "positive" else "↓"
            show_trend = metric['trend'] is not None
            
            col.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{metric['label']}</div>
                    <div class="metric-value">{metric['value']}</div>
                    {"<div class='metric-trend' style='color: "+trend_color+"'>"+trend_arrow+"</div>" if show_trend else ""}
                </div>
            """, unsafe_allow_html=True)

# Keep existing graphs and tables
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

cumulative_pl_df = fetch_cumulative_pl(symbol)
if cumulative_pl_df is not None and not cumulative_pl_df.empty:
    st.subheader("Equity Curve")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cumulative_pl_df["Date"], y=cumulative_pl_df["Cumulative P/L"], mode='lines+markers'))
    st.plotly_chart(fig, use_container_width=True)
