import pandas as pd
import mysql.connector

def load_data_from_csv(file_path):
    """Load stock signal data from a CSV file."""
    return pd.read_csv(file_path)

def load_data_from_mysql(host, user, password, database, table):
    """Load stock signal data from a MySQL database."""
    conn = mysql.connector.connect(
        host=host, user=user, password=password, database=database
    )
    query = f"SELECT * FROM {table}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
