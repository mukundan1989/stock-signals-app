import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go
from datetime import datetime
import plotly.express as px
from functools import lru_cache

# Set page config with modern styling
st.set_page_config(layout="wide", page_title="Stock Performance", page_icon="📈")

# Modern UI Styling
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
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    .elegant-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(45deg, #fff, #a5a5a5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

class DatabaseConnection:
    def __init__(self):
        self.config = {
            "host": "13.203.191.72",
            "database": "stockstream_two",
            "user": "stockstream_two",
            "password": "stockstream_two"
        }

    def __enter__(self):
        self.conn = mysql.connector.connect(**self.config)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

@lru_cache(maxsize=32)
def fetch_model_data(comp_symbol, model_name):
    try:
        with DatabaseConnection() as conn:
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
            return df
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return None

def create_performance_chart(df):
    fig = go.Figure()
    
    # Add Cumulative P/L line
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Cumulative P/L"],
        mode='lines',
        line=dict(
            color='rgba(0, 255, 159, 0.8)',
            width=2
        ),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 159, 0.1)',
        name='Cumulative P/L'
    ))
    
    # Modern styling
    fig.update_layout(
        title="Performance Over Time",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_size=20,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255, 255, 255, 0.05)',
            bordercolor='rgba(255, 255, 255, 0.1)'
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=0.5,
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=0.5,
            gridcolor='rgba(255,255,255,0.1)'
        )
    )
    
    return fig

def main():
    # Title
    st.markdown('<h1 class="elegant-title">📈 Stock Performance Analytics</h1>', unsafe_allow_html=True)
    
    # Search Section
    col1, col2 = st.columns([4, 1])
    with col1:
        symbol = st.text_input("Enter Stock Symbol", value="AAPL")
    with col2:
        st.write("")
        go_clicked = st.button("Analyze", type="primary")
    
    if go_clicked:
        # Fetch and display metrics
        metrics = fetch_performance_metrics(symbol)
        if metrics:
            cols = st.columns(3)
            
            metric_data = [
                {"label": "Win Rate", "value": f"{metrics['win_percentage']:.1f}%"},
                {"label": "Total Trades", "value": str(metrics['total_trades'])},
                {"label": "Profit Factor", "value": f"{metrics['profit_factor']:.2f}"}
            ]
            
            for col, metric in zip(cols, metric_data):
                with col:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{metric['label']}</div>
                            <div class="metric-value">{metric['value']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Create tabs with modern styling
        tab_names = ["Overview", "GTrends", "News", "Twitter"]
        tabs = st.tabs(tab_names)
        
        # Overview Tab
        with tabs[0]:
            cumulative_pl_df = fetch_cumulative_pl(symbol)
            if cumulative_pl_df is not None and not cumulative_pl_df.empty:
                st.plotly_chart(create_performance_chart(cumulative_pl_df), use_container_width=True)
        
        # Model-specific tabs
        for tab, model_name in zip(tabs[1:], ["gtrends", "news", "twitter"]):
            with tab:
                df = fetch_model_data(symbol, model_name)
                if df is not None and not df.empty:
                    st.dataframe(
                        df.style.background_gradient(
                            cmap='viridis',
                            subset=['30D P/L', '60D P/L']
                        ),
                        use_container_width=True
                    )
        
        # Footer
        st.markdown(f"""
            <div style='text-align: center; color: rgba(255,255,255,0.5); padding: 20px; font-size: 0.8rem;'>
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
