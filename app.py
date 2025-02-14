import streamlit as st
import pandas as pd
import mysql.connector
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        }

    def connect(self):
        return mysql.connector.connect(**self.config)

class StockData:
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def fetch_stocks(self, table: str, limit: int = 5) -> Optional[pd.DataFrame]:
        try:
            with self.db.connect() as conn:
                query = """
                    SELECT date, comp_name, comp_symbol, trade_signal, entry_price 
                    FROM {table} 
                    LIMIT %s
                """.format(table=table)
                
                return pd.read_sql(query, conn, params=(limit,))
        except Exception as e:
            st.error(f"Database error: {e}")
            return None

    def search_stock(self, table: str, symbol: str) -> Optional[pd.DataFrame]:
        try:
            with self.db.connect() as conn:
                query = """
                    SELECT date, comp_name, comp_symbol, trade_signal, entry_price 
                    FROM {table} 
                    WHERE comp_symbol = %s
                """.format(table=table)
                
                return pd.read_sql(query, conn, params=(symbol,))
        except Exception as e:
            st.error(f"Search error: {e}")
            return None

class StockStreamUI:
    def __init__(self):
        self.stock_data = StockData(DatabaseConnection())
        self.initialize_session_state()

    @staticmethod
    def initialize_session_state():
        if "selected_table" not in st.session_state:
            st.session_state["selected_table"] = "overall_latest_signal"
        if "data" not in st.session_state:
            st.session_state["data"] = None
        if "show_search" not in st.session_state:
            st.session_state["show_search"] = False

    def render_header(self):
        st.markdown("<h1 style='text-align: center;'>Portfolio</h1>", unsafe_allow_html=True)
        st.write("Easily predict stock market trends and make smarter investment decisions with our intuitive portfolio tool.")

    def render_metric_card(self, value: str, label: str) -> str:
        return f"""
        <div style='background-color:#007BFF; padding:20px; border-radius:10px; text-align:center; color:white;'>
            <h2>{value}</h2>
            <p>{label}</p>
        </div>
        """

    def render_metrics(self):
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        metrics = [
            ("43%", "Above Baseline"),
            ("$13,813", "Value Gain on Buy"),
            ("+0.75", "Sentiment Score"),
            ("87%", "Prediction Accuracy")
        ]

        for col, (value, label) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(self.render_metric_card(value, label), unsafe_allow_html=True)

    def render_model_selection(self):
        st.write("### Select Sentiment Model")
        cols = st.columns(4)
        models = {
            "Google Trends": "gtrend_latest_signal",
            "News": "news_latest_signal",
            "Twitter": "twitter_latest_signal",
            "Overall": "overall_latest_signal"
        }

        for col, (label, table) in zip(cols, models.items()):
            with col:
                if st.toggle(label, value=(st.session_state["selected_table"] == table)):
                    self.toggle_selection(table)

    def toggle_selection(self, table_key: str):
        if st.session_state["selected_table"] != table_key:
            st.session_state["selected_table"] = table_key
            st.session_state["data"] = None
            st.rerun()

    def render_watchlist(self):
        st.write("### Watchlist")
        
        if st.session_state["data"] is None:
            st.session_state["data"] = self.stock_data.fetch_stocks(st.session_state["selected_table"])

        if st.session_state["data"] is not None:
            st.dataframe(st.session_state["data"].to_dict(orient="records"))

        if st.button("Add Stock"):
            st.session_state["show_search"] = True

        if st.session_state["show_search"]:
            self.render_stock_search()

    def render_stock_search(self):
        symbol = st.text_input("Enter Stock Symbol:")
        if symbol:
            result = self.stock_data.search_stock(st.session_state["selected_table"], symbol)
            if result is not None and not result.empty:
                st.session_state["data"] = pd.concat(
                    [st.session_state["data"], result], 
                    ignore_index=True
                )
                st.session_state["show_search"] = False
                st.rerun()
            else:
                st.warning("Stock not found!")

    def render(self):
        self.render_header()
        self.render_metrics()
        st.markdown("<br>", unsafe_allow_html=True)
        self.render_model_selection()
        st.markdown("<br>", unsafe_allow_html=True)
        self.render_watchlist()

if __name__ == "__main__":
    app = StockStreamUI()
    app.render()
