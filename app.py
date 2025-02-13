import streamlit as st
import pandas as pd
import mysql.connector

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"
DB_TABLE = "overall_latest_signal"

# Streamlit UI
st.title("Database Table Viewer")

# Initialize session state for data if not already set
if "data" not in st.session_state:
    st.session_state["data"] = None

# Function to fetch data
def fetch_data(limit=5):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM `{DB_NAME}`.`{DB_TABLE}` LIMIT {limit}"
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data()

st.dataframe(st.session_state["data"])

# Add stock search functionality
if "show_search" not in st.session_state:
    st.session_state["added_symbols"] = set()  # Track added stock symbols
    st.session_state["show_search"] = False

if st.button("Add Stock"):
    st.session_state["show_search"] = True

if st.session_state["show_search"]:
    symbol = st.text_input("Enter Stock Symbol:")
    if symbol and symbol not in st.session_state["added_symbols"]:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            query = f"SELECT * FROM `{DB_NAME}`.`{DB_TABLE}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            if result:
                # Check if the stock symbol already exists in the table
                existing_symbols = st.session_state["data"]["comp_symbol"].tolist()
                new_symbol = result[0][st.session_state["data"].columns.get_loc("comp_symbol")]
                if new_symbol in existing_symbols:
                    st.warning("Stock symbol already added.")
                else:
                new_row = pd.DataFrame(result, columns=st.session_state["data"].columns)
                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)new_row = pd.DataFrame(result, columns=st.session_state["data"].columns)
                                    st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.session_state["added_symbols"].add(symbol)
                st.rerun()
            else:
                st.warning("No matching stock found.")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
