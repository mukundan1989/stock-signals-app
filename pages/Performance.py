import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide", page_title="Performance Summary", initial_sidebar_state="collapsed")

# Apply modern glassmorphism CSS
st.markdown("""
    <style>
    /* Glassmorphism Metric Card */
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
        letter-spacing: 0.1em;
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

    /* Trend Colors */
    .positive { color: #00ff9f; }  /* Green */
    .negative { color: #ff4b4b; }  /* Red */

    /* Custom CSS for elegant table design using theme-based colors */
    .pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 10px; /* Adjust spacing between rows */
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: var(--text-color);
    }

    /* Black background with curved edges for each row */
    .pretty-table tbody tr {
        background-color: black; /* Set background color to black */
        border-radius: 20px; /* Adjust the border-radius for rounded edges */
        margin-bottom: 10px;
    }
 
    .pretty-table th {
        background-color: #1c1c1c; /* Set background color to black */
        color: #aeaeae !important; /* Set background color to black */
    } 

    .pretty-table th:first-child {
        border-top-left-radius: 30px; /* Adjust the border-radius for the first cell */
        border-bottom-left-radius: 30px;
    }

    .pretty-table th:last-child {
        border-top-right-radius: 30px; /* Adjust the border-radius for the first cell */
        border-bottom-right-radius: 30px;
    }

    /* Padding for table cells */
    .pretty-table th, .pretty-table td {
        padding: 6px 9px;
        text-align: center;
        border: none;
        border-top: 5px solid #282828 !important;
    }

    /* Add curved edges to the first and last cells in each row */
    .pretty-table tbody tr td:first-child {
        border-top-left-radius: 20px; /* Adjust the border-radius for the first cell */
        border-bottom-left-radius: 20px;
    }

    .pretty-table tbody tr td:last-child {
        border-top-right-radius: 20px; /* Adjust the border-radius for the last cell */
        border-bottom-right-radius: 20px;
    }

    /* Hover effect for rows */
    .pretty-table tbody tr:hover {
        background-color: #333; /* Darker shade for hover effect */
    }

    /* Ensure the text above the table is white */
    h1, p {
        color: var(--text-color) !important;
    }

    /* Grid container for metric boxes */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        justify-content: center;
        align-items: center;
    }

    @media (max-width: 600px) {
        .grid-container { grid-template-columns: repeat(2, 1fr); gap: 5px; }
    }

    /* Styling for the metric boxes */
    .metric-box {
        background: linear-gradient(10deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box p {
        margin-left: 20px;
        margin-bottom: 0;
    }

    /* Second grid box with pile of cash icon */
    .metric-box-gain {
        background: linear-gradient(15deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-gain::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 1 0 0 7h5a3.5 3.5 0 1 1 0 7H6"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-gain h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box-gain p {
        margin-left: 20px;
        margin-bottom: 0;
    }

    /* Third grid box with speedometer gauge icon */
    .metric-box-speedometer {
        background: linear-gradient(15deg, #000000, #232323);
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-speedometer::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-speedometer h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box-speedometer p {
        margin-left: 20px;
        margin-bottom: 0;
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

            # Round off win_percentage to whole number and profit_factor to 2 decimal places
            if key == "win_percentage" and isinstance(value, (int, float)):
                value = round(value, 0)  # Round to whole number
            elif key == "profit_factor" and isinstance(value, (int, float)):
                value = round(value, 2)

            results[key] = value

        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None

# Function to fetch and display model performance data
def fetch_model_data(comp_symbol):
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
        WHERE comp_symbol = %s AND sentiment != 'neutral'
        """
        
        cursor.execute(query, (comp_symbol,))
        result = cursor.fetchall()
        columns = ["Date", "Sentiment", "Entry Price", "30D P/L", "60D P/L"]
        df = pd.DataFrame(result, columns=columns)
        
        cursor.close()
        conn.close()
        
        return df
    except Exception as e:
        st.error(f"Error fetching model data: {e}")
        return None

# Function to fetch cumulative P/L data
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

# Function to create cumulative P/L graph
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

    fig.update_layout(
        title="Cumulative Profit/Loss Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative P/L",
        height=400,
        plot_bgcolor="#121212",
        paper_bgcolor="#121212",
        font=dict(color="white")
    )

    return fig

# UI Elements
st.title("Performance Summary")
symbol = st.text_input("Enter Stock Symbol", value="APRN")
go_clicked = st.button("Go", type="primary")

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")
        win_class = "positive" if metrics['win_percentage'] >= 50 else "negative"
        profit_class = "positive" if metrics['profit_factor'] > 1 else "negative"

        st.markdown("""
            <div class="grid-container">
                <div class="metric-box"><h2>{}%</h2><p>Win %</p></div>
                <div class="metric-box-gain"><h2>{}</h2><p>No. of Trades</p></div>
                <div class="metric-box-speedometer"><h2>{}</h2><p>Profit Factor</p></div>
            </div>
        """.format(int(metrics['win_percentage']), metrics['total_trades'], metrics['profit_factor']), unsafe_allow_html=True)

    # Add spacing before "Equity Curve"
    st.markdown("<br>", unsafe_allow_html=True)

    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.subheader("Equity Curve")
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)

    # Add spacing before "Performance Data Table"
    st.markdown("<br>", unsafe_allow_html=True)
    
    df = fetch_model_data(symbol)
    if df is not None and not df.empty:
        st.subheader("Performance Data Table")
        table_html = df.to_html(index=False, classes="pretty-table", escape=False)
        st.markdown(table_html, unsafe_allow_html=True)
