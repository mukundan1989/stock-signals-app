import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for elegant table design using theme-based colors
st.markdown(
    """
    <style>
    /* Use theme-based background color for the main container */
    .st-emotion-cache-bm2z3a {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .logo {
        width: 46px; /* Default size for desktop */
        height: 46px;
        margin-bottom: 2px; /* Spacing between logo and title */
    }

    /* Adjust logo size for smaller screens */
    @media (max-width: 768px) {
        .logo {
            width: 32px; /* Smaller size for tablets */
            height: 32px;
        }
    }

    /* Adjust logo size for mobile devices */
    @media (max-width: 480px) {
        .logo {
            width: 26px; /* Smallest size for mobile */
            height: 26px;
        }
    }

    .stHorizontalBlock {
        background-color: black; /* Set background color to black */
        border-radius: 20px; /* Adjust the border-radius for rounded edges */
        padding: 10px 20px 20px 20px;
    }

    .pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 10px; /* Adjust spacing between rows */
        font-size: 0.9em;
        font-family: "Source Sans Pro", sans-serif;
        min-width: 400px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: var(--text-color);
    }

    /* Black background with curved edges for each row */
    .pretty-table tbody tr {
        background-color: #161616; /* Set background color to black */
        border-radius: 20px; /* Adjust the border-radius for rounded edges */
        margin-bottom: 10px;
    }

    .pretty-table th:first-child {
        border-top-left-radius: 30px; /* Adjust the border-radius for the first cell */
        border-bottom-left-radius: 30px;
    }

    .pretty-table th:last-child {
        border-top-right-radius: 30px; /* Adjust the border-radius for the first cell */
        border-bottom-right-radius: 30px;
    }

    .pretty-table th{
        background-color: #000; /* Set background color to black */
        color: #fff !important; /* Set background color to black */
        padding: 6px 9px;
        text-align: center;
        border: 2px solid #282828 !important; 
    } 

    /* Padding for table cells */
    .pretty-table td {
        padding: 5px 8px;
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
        background-color: #000000; /* Darker shade for hover effect */
    }

    /* Ensure the text above the table is white */
    h1, p {
        color: var(--text-color) !important;
    }

    /* Grid container for metric boxes */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        justify-content: center;
        align-items: center;
    }

    @media (max-width: 600px) {
        .grid-container { grid-template-columns: repeat(2, 1fr); gap: 5px; }
    }

    /* Styling for the "Add Stock" button */
    .stButton button {
        background-color: var(--primary-color);
        color: var(--text-color);
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }

    .stButton button:hover {
        background-color: var(--primary-hover-color);
    }

    /* Custom CSS for the Company Name cell */
    .company-name-cell {
        text-align: center;
    }

    .company-name-cell small {
        background-color: #313131;
        border-radius: 4px;
        padding: 2px 6px;
        color: var(--text-color);
        display: inline-block;
        margin-top: 4px;
    }

    /* Custom CSS for the Sentiment cell */
    .sentiment-positive {
        background-color: #6eb330; /* Green background for positive sentiment */
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    .sentiment-negative {
        background-color: #db503a; /* Red background for negative sentiment */
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    /* Custom CSS for aligning titles to the left */
    .left-align {
        text-align: left;
        display: flex;
        align-items: center;
    }

    .left-align svg {
        margin-right: 10px;
    }
    
    .st-b1 {
        background-color: #000;
    }

    .st-bt {
        background-color: #fff;
    }
    
    /* Custom CSS for the title with logo */
    .title-with-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px; /* Space between logo and title */
    }

    .title-with-logo img {
        width: 70px; /* Adjust the size of the logo */
        height: 70px;
        background: #000;
        padding: 3px;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database credentials
DB_HOST = "13.203.191.72"
DB_NAME = "stockstream_two"
DB_USER = "stockstream_two"
DB_PASSWORD = "stockstream_two"

# Function to fetch the latest Google Trends signals
def fetch_gtrend_signals():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT date, comp_symbol, analyzed_keywords, sentiment_score, sentiment, entry_price
        FROM gtrend_signals_full
        WHERE (comp_symbol, date) IN (
            SELECT comp_symbol, MAX(date)
            FROM gtrend_signals_full
            GROUP BY comp_symbol
        );
        """
        cursor.execute(query)
        result = cursor.fetchall()

        columns = ["Date", "Company Symbol", "Analyzed Keywords", "Sentiment Score", "Sentiment", "Entry Price"]
        df = pd.DataFrame(result, columns=columns)

        # Apply custom CSS to the Sentiment column
        df["Sentiment"] = df["Sentiment"].apply(
            lambda x: (
                '<div class="sentiment-positive">' + x + '</div>'
            ) if x.lower() == "positive" else (
                '<div class="sentiment-negative">' + x + '</div>'
            ) if x.lower() == "negative" else x
        )

        cursor.close()
        conn.close()

        return df
    except Exception as e:
        st.error(f"Error fetching Google Trends signals: {e}")
        return None

# Page title with Google Trends logo
st.markdown(
    """
    <div class="title-with-logo">
        <img src="https://raw.githubusercontent.com/mukundan1989/stock-signals-app/refs/heads/main/images/gtrend-logo.png" alt="Google Trends Logo" class="logo">
        <h1 style='text-align: center;'>Google Trends Signals</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Page description
st.write("<p style='text-align: center;'>View the latest Google Trends sentiment signals for each stock.</p>", unsafe_allow_html=True)

# Fetch and display Google Trends signals
gtrend_signals_df = fetch_gtrend_signals()

if gtrend_signals_df is not None:
    if not gtrend_signals_df.empty:
        table_html = gtrend_signals_df.to_html(index=False, classes="pretty-table", escape=False)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.warning("No Google Trends signals found in the database.")
else:
    st.error("Failed to fetch Google Trends signals. Please check the database connection.")
