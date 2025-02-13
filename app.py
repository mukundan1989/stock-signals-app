import mysql.connector

# Database credentials
HOST = "13.203.191.72"
USER = "stockstream_two"
PASSWORD = "stockstream_two"
DATABASE = "stockstream_two"

try:
    # Attempt connection
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    
    if conn.is_connected():
        print("✅ Successfully connected to the database!")
    else:
        print("❌ Connection failed.")

    # Close connection
    conn.close()

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
