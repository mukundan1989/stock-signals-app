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

# Display initial data
data = fetch_data()
if data is not None:
    st.dataframe(data)

# Add stock search functionality
if st.button("Add Stock"):
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
            query = f"SELECT * FROM `{DB_NAME}`.`{DB_TABLE}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            if result:
                new_row = pd.DataFrame(result, columns=data.columns)
                data = pd.concat([data, new_row], ignore_index=True)
                st.dataframe(data)
            else:
                st.warning("No matching stock found.")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
