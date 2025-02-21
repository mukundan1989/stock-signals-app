import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Apply modern glassmorphism CSS
st.markdown("""
    <style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        transition: transform 0.3s ease;
        text-align: center;
        margin: 10px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 2rem;
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

    .positive { color: #00ff9f; }
    .negative { color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

def fetch_performance_metrics(comp_symbol):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        cursor = conn.cursor()

        queries = {
            "win_percentage": """
                SELECT (COUNT(CASE WHEN (`30d_pl` > 0 OR `60d_pl` > 0) AND sentiment != 'neutral' THEN 1 END) 
                / COUNT(CASE WHEN sentiment != 'neutral' THEN 1 END)) * 100 AS win_percentage
                FROM models_performance WHERE comp_symbol = %s;
            """,
            "total_trades": """
                SELECT COUNT(*) FROM models_performance
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

            if key == "profit_factor" and isinstance(value, (int, float)):
                value = round(value, 2)

            results[key] = value

        cursor.close()
        conn.close()
        return results
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None

def fetch_model_data(comp_symbol, model_name):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
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

        win_class = "positive" if metrics['win_percentage'] >= 50 else "negative"
        profit_class = "positive" if metrics['profit_factor'] > 1 else "negative"

        cols = st.columns(3)
        metric_data = [
            {"label": "Win %", "value": f"{metrics['win_percentage']}%", "trend": "", "class": win_class},
            {"label": "No. of Trades", "value": f"{metrics['total_trades']}", "trend": "", "class": "positive"},
            {"label": "Profit Factor", "value": f"{metrics['profit_factor']}", "trend": "↑" if metrics['profit_factor'] > 1 else "↓", "class": profit_class}
        ]

        for col, metric in zip(cols, metric_data):
            with col:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{metric['label']}</div>
                        <div class="metric-value">{metric['value']}</div>
                        <div class="metric-trend {metric['class']}">
                            {metric['trend']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Restore data table for model performance
    st.subheader("Model Performance Data")
    tabs = st.tabs(["GTrends", "News", "Twitter", "Overall"])

    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")

