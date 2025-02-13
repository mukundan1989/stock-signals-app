import mysql.connector

# Database credentials
HOST = "13.203.191.72"
USER = "stockstream_two"
PASSWORD = "stockstream_two"
DATABASE = "stockstream_two"

try:
    print("🔄 Attempting to connect to the database...")

    # Attempt connection
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        connect_timeout=10  # 10-second timeout to prevent hanging
    )
    
    if conn.is_connected():
        print("✅ Successfully connected to the database!")
    else:
        print("❌ Connection failed.")

    # Close connection
    conn.close()

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
except Exception as e:
    print(f"⚠️ Unexpected error: {e}")
