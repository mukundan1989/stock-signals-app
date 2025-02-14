import streamlit as st
import pandas as pd
import mysql.connector
import plotly.graph_objects as go
from datetime import datetime
from streamlit_option_menu import option_menu
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="StockStream Portfolio",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
    }
    .trend-up {
        color: #28a745;
    }
    .trend-down {
        color: #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Available tables
TABLES = {
    "Google Trends": {"table": "gtrend_latest_signal", "icon": "📊"},
    "News": {"table": "news_latest_signal", "icon": "📰"},
    "Twitter": {"table": "twitter_latest_signal", "icon": "🐦"},
    "Overall": {"table": "overall_latest_signal", "icon": "📈"}
}

# Helper function to create sparkline
def create_sparkline(values):
    fig = go.Figure(go.Scatter(
        y=values,
        mode='lines',
        line=dict(width=2, color='#007BFF'),
        showlegend=False
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False)
    )
    return fig

# Header with Navigation
selected = option_menu(
    menu_title=None,
    options=["Portfolio", "Analysis", "Settings"],
    icons=["house", "graph-up", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

if selected == "Portfolio":
    # Main header
    st.markdown("<h1 style='text-align: center;'>Portfolio Dashboard</h1>", unsafe_allow_html=True)
    st.write("Make smarter investment decisions with our AI-powered portfolio insights.")

    # Metrics Grid with enhanced visuals
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <h3>Performance</h3>
                <h2 class="trend-up">↗ 43%</h2>
                <p>Above Baseline</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <h3>Value Gain</h3>
                <h2 class="trend-up">↗ $13,813</h2>
                <p>Total Returns</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <h3>Sentiment</h3>
                <h2>+0.75</h2>
                <p>Market Sentiment Score</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <h3>Accuracy</h3>
                <h2>87%</h2>
                <p>Prediction Success Rate</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Initialize session state
    if "selected_table" not in st.session_state:
        st.session_state["selected_table"] = "overall_latest_signal"
    if "data" not in st.session_state:
        st.session_state["data"] = None
    if "show_search" not in st.session_state:
        st.session_state["show_search"] = False

    # Sentiment Model Selection
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("### Select Sentiment Model")
    
    cols = st.columns(4)
    for i, (name, info) in enumerate(TABLES.items()):
        with cols[i]:
            if st.button(
                f"{info['icon']} {name}",
                key=f"btn_{name}",
                help=f"View {name} sentiment data",
                use_container_width=True,
            ):
                st.session_state["selected_table"] = info['table']
                st.session_state["data"] = None
                st.rerun()

    # Function to fetch and filter data
    def fetch_data(table, limit=5):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            query = f"""
                SELECT 
                    date, 
                    comp_name, 
                    comp_symbol, 
                    trade_signal, 
                    entry_price 
                FROM `{DB_NAME}`.`{table}` 
                ORDER BY date DESC 
                LIMIT {limit}
            """
            cursor.execute(query)
            df = pd.DataFrame(
                cursor.fetchall(),
                columns=["Date", "Company", "Symbol", "Signal", "Entry Price"]
            )
            cursor.close()
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None

    # Load initial data if not set
    if st.session_state["data"] is None:
        st.session_state["data"] = fetch_data(st.session_state["selected_table"])

    # Watchlist section
    st.markdown("<br>", unsafe_allow_html=True)
    
    watchlist_col1, watchlist_col2 = st.columns([3, 1])
    with watchlist_col1:
        st.write("### Watchlist")
    with watchlist_col2:
        if st.button("➕ Add Stock", use_container_width=True):
            st.session_state["show_search"] = True

    # Display enhanced watchlist table
    if st.session_state["data"] is not None:
        df = st.session_state["data"].copy()
        
        # Add styling
        def color_signal(val):
            color = '#28a745' if val > 0 else '#dc3545'
            return f'color: {color}'
        
        st.dataframe(
            df.style
            .format({
                'Entry Price': '${:.2f}',
                'Signal': '{:.2f}'
            })
            .applymap(color_signal, subset=['Signal']),
            use_container_width=True,
            height=300
        )

    # Show search box when "Add Stock" is clicked
    if st.session_state["show_search"]:
        with st.container():
            st.markdown(
                """
                <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px;'>
                    <h4>Add New Stock</h4>
                """,
                unsafe_allow_html=True
            )
            symbol = st.text_input("Enter Stock Symbol:", key="stock_search")
            
            if symbol:
                try:
                    conn = mysql.connector.connect(
                        host=DB_HOST,
                        database=DB_NAME,
                        user=DB_USER,
                        password=DB_PASSWORD
                    )
                    cursor = conn.cursor()
                    query = f"""
                        SELECT 
                            date, 
                            comp_name, 
                            comp_symbol, 
                            trade_signal, 
                            entry_price 
                        FROM `{DB_NAME}`.`{st.session_state['selected_table']}` 
                        WHERE comp_symbol = %s
                    """
                    cursor.execute(query, (symbol,))
                    result = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    if result:
                        new_row = pd.DataFrame(
                            result,
                            columns=["Date", "Company", "Symbol", "Signal", "Entry Price"]
                        )
                        st.session_state["data"] = pd.concat(
                            [st.session_state["data"], new_row],
                            ignore_index=True
                        )
                        st.session_state["show_search"] = False
                        st.success(f"Added {symbol} to watchlist!")
                        st.rerun()
                    else:
                        st.warning("Stock not found! Please check the symbol and try again.")
                except Exception as e:
                    st.error(f"Error searching stock: {e}")

elif selected == "Analysis":
    st.write("### Market Analysis")
    st.info("Analysis features coming soon!")

else:  # Settings
    st.write("### Settings")
    st.info("Settings panel coming soon!")

# Footer
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Last updated: {}
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)
