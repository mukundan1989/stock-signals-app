import streamlit as st
import pandas as pd
import mysql.connector

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Available tables
TABLES = {
    "Google Trends": "gtrend_latest_signal",
    "News": "news_latest_signal",
    "Twitter": "twitter_latest_signal",
    "Overall": "overall_latest_signal"
}

# Custom CSS for metrics
st.markdown("""
<style>
.metric-box {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin: 10px 0;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 5px;
}
.metric-label {
    font-size: 16px;
    color: #333;
    margin-bottom: 5px;
}
.metric-description {
    font-size: 12px;
    color: #666;
}
</style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("📊 Portfolio Dashboard")

# Header & Description
st.markdown("""
### Portfolio
Easily predict stock market trends and make smarter investment decisions
with our intuitive portfolio tool.
""")

# Metrics Data
metrics = [
    {"label": "Above Baseline", "value": "43%", "color": "#3b82f6", "description": "Compared to market average"},
    {"label": "Value Gain on Buy", "value": "$13,813", "color": "#22c55e", "description": "Total profit from buy signals"},
    {"label": "Sentiment Score", "value": "+0.75", "color": "#8b5cf6", "description": "Overall market sentiment"},
    {"label": "Prediction Accuracy", "value": "87%", "color": "#f97316", "description": "Success rate of predictions"}
]

# Display Metrics in a 2x2 Grid
col1, col2 = st.columns(2)
with col1:
    for metric in metrics[0:2]:
        st.markdown(f"""
        <div class="metric-box" style="border-left: 4px solid {metric['color']};">
            <div class="metric-value" style="color: {metric['color']}">{metric['value']}</div>
            <div class="metric-label">{metric['label']}</div>
            <div class="metric-description">{metric['description']}</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    for metric in metrics[2:4]:
        st.markdown(f"""
        <div class="metric-box" style="border-left: 4px solid {metric['color']};">
            <div class="metric-value" style="color: {metric['color']}">{metric['value']}</div>
            <div class="metric-label">{metric['label']}</div>
            <div class="metric-description">{metric['description']}</div>
        </div>
        """, unsafe_allow_html=True)

# Initialize session state for selected table
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"  # Default table
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False
if "added_symbols" not in st.session_state:
    st.session_state["added_symbols"] = set()

# Toggle buttons for table selection
selected_table = None
cols = st.columns(len(TABLES))
for i, (label, table) in enumerate(TABLES.items()):
    if cols[i].toggle(label, table == st.session_state["selected_table"]):
        selected_table = table

# Update session state if a new table is selected
if selected_table and selected_table != st.session_state["selected_table"]:
    st.session_state["selected_table"] = selected_table
    st.session_state["data"] = None  # Reset data
    st.rerun()

# Function to fetch data
def fetch_data(table, limit=5):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM `{DB_NAME}`.`{table}` LIMIT {limit}"
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Add Stock button
if st.button("➕ Add Stock"):
    st.session_state["show_search"] = True

# Search functionality
if st.session_state["show_search"]:
    symbol = st.text_input("Enter Stock Symbol:")
    if symbol:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            query = f"SELECT * FROM `{DB_NAME}`.`{st.session_state['selected_table']}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()

            if result:
                if symbol not in st.session_state["added_symbols"]:
                    new_row = pd.DataFrame(result, columns=st.session_state["data"].columns)
                    st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                    st.session_state["added_symbols"].add(symbol)
                    st.session_state["show_search"] = False
                    st.rerun()
                else:
                    st.warning("Stock already added!")
            else:
                st.error("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")

# Display table data
st.dataframe(st.session_state["data"])
