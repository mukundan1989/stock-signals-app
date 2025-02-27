import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for dark-themed elegant table design
st.markdown(
    """
    <style>
    /* Target the main container (st-emotion-cache-bm2z3a) and set a dark grey background */
    .st-emotion-cache-bm2z3a {
        background-color: #2a2a2a; /* Dark grey background */
        color: #ffffff; /* White text for the entire page */
    }

	/* Custom CSS for elegant table design with curved edges */
	.pretty-table {
        width: 100%;
        border-collapse: separate; /* Use separate to allow rounded corners */
        border-spacing: 0 30px; /* Add spacing between rows */
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px; /* Rounded edges for the table */
        overflow: hidden;
        text-align: center;
        border: none;
        color: #ffffff; /* White text for the table */
	}

	/* Grey background with curved edges for each row */
	.pretty-table tbody tr {
        background-color: #3a3a3a; /* Dark grey background */
        border-radius: 10px; /* Rounded edges for each row */
        margin-bottom: 10px; /* Add spacing between rows */
	}

	/* Padding for table cells */
	.pretty-table th, .pretty-table td {
        padding: 12px 15px;
        text-align: center;
        border: none;
	}

	/* Add curved edges to the first and last cells in each row */
	.pretty-table tbody tr td:first-child {
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
	}

	.pretty-table tbody tr td:last-child {
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
	}

	/* Hover effect for rows */
	.pretty-table tbody tr:hover {
        background-color: #4a4a4a; /* Slightly lighter grey on hover */
	}

    /* Ensure the text above the table is white */
    h1, p {
        color: #ffffff !important; /* White text for titles and paragraphs */
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
        background-color: #000000; /* Black background */
        color: #ffffff; /* White text */
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }

    .stButton button:hover {
        background-color: #333333; /* Slightly lighter black on hover */
    }

    /* Custom CSS for the Company Name cell */
    .company-name-cell {
        background-color: #3a3a3a; /* Dark grey background */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
    }

    /* Custom CSS for the Trade Signal cell */
    .trade-signal-buy {
        background-color: #2e7d32; /* Green background for Buy */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
    }

    .trade-signal-sell {
        background-color: #c62828; /* Red background for Sell */
        border-radius: 10px; /* Rounded edges */
        padding: 10px; /* Padding for better spacing */
        color: #ffffff; /* White text */
    }

    /* First grid box with line chart icon */
    .metric-box {
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a); /* Dark grey gradient */
        padding: 20px; /* Padding for the box */
        border-radius: 10px;
        text-align: left; /* Left-align text */
        color: #ffffff; /* White text */
        font-size: 18px;
        font-weight: bold;
        border: 1px solid #4a4a4a; /* Subtle border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow */
        position: relative; /* Required for positioning the icon */
        overflow: hidden; /* Ensure the icon doesn't overflow */
    }

    .metric-box::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>'); /* Line chart SVG */
        background-size: 40px 40px; /* Adjust size of the icon */
        background-position: left top; /* Position the icon at the top-left */
        background-repeat: no-repeat;
        opacity: 0.3; /* Blend the icon with the background */
        position: absolute;
        top: 20px; /* Adjust top position */
        left: 20px; /* Adjust left position */
        width: 40px;
        height: 40px;
        z-index: 1; /* Ensure the icon is behind the text */
    }

    .metric-box h2 {
        margin-top: 60px; /* Push text down to avoid overlapping with the icon */
        margin-left: 20px; /* Left-align text */
        margin-bottom: 10px; /* Space between h2 and p */
    }

    .metric-box p {
        margin-left: 20px; /* Left-align text */
        margin-bottom: 0; /* Remove extra margin */
    }

    /* Second grid box with pile of cash icon */
    .metric-box-gain {
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a); /* Dark grey gradient */
        padding: 20px; /* Padding for the box */
        border-radius: 10px;
        text-align: left; /* Left-align text */
        color: #ffffff; /* White text */
        font-size: 18px;
        font-weight: bold;
        border: 1px solid #4a4a4a; /* Subtle border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow */
        position: relative; /* Required for positioning the icon */
        overflow: hidden; /* Ensure the icon doesn't overflow */
    }

    .metric-box-gain::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 1 0 0 7h5a3.5 3.5 0 1 1 0 7H6"/></svg>'); /* Pile of cash SVG */
        background-size: 40px 40px; /* Adjust size of the icon */
        background-position: left top; /* Position the icon at the top-left */
        background-repeat: no-repeat;
        opacity: 0.3; /* Blend the icon with the background */
        position: absolute;
        top: 20px; /* Adjust top position */
        left: 20px; /* Adjust left position */
        width: 40px;
        height: 40px;
        z-index: 1; /* Ensure the icon is behind the text */
    }

    .metric-box-gain h2 {
        margin-top: 60px; /* Push text down to avoid overlapping with the icon */
        margin-left: 20px; /* Left-align text */
        margin-bottom: 10px; /* Space between h2 and p */
    }

    .metric-box-gain p {
        margin-left: 20px; /* Left-align text */
        margin-bottom: 0; /* Remove extra margin */
    }

    /* Third grid box with speedometer gauge icon */
    .metric-box-speedometer {
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a); /* Dark grey gradient */
        padding: 20px; /* Padding for the box */
        border-radius: 10px;
        text-align: left; /* Left-align text */
        color: #ffffff; /* White text */
        font-size: 18px;
        font-weight: bold;
        border: 1px solid #4a4a4a; /* Subtle border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow */
        position: relative; /* Required for positioning the icon */
        overflow: hidden; /* Ensure the icon doesn't overflow */
    }

    .metric-box-speedometer::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2"/></svg>'); /* Speedometer gauge SVG */
        background-size: 40px 40px; /* Adjust size of the icon */
        background-position: left top; /* Position the icon at the top-left */
        background-repeat: no-repeat;
        opacity: 0.3; /* Blend the icon with the background */
        position: absolute;
        top: 20px; /* Adjust top position */
        left: 20px; /* Adjust left position */
        width: 40px;
        height: 40px;
        z-index: 1; /* Ensure the icon is behind the text */
    }

    .metric-box-speedometer h2 {
        margin-top: 60px; /* Push text down to avoid overlapping with the icon */
        margin-left: 20px; /* Left-align text */
        margin-bottom: 10px; /* Space between h2 and p */
    }

    .metric-box-speedometer p {
        margin-left: 20px; /* Left-align text */
        margin-bottom: 0; /* Remove extra margin */
    }

    /* Fourth grid box with dartboard and arrow icon */
    .metric-box-accuracy {
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a); /* Dark grey gradient */
        padding: 20px; /* Padding for the box */
        border-radius: 10px;
        text-align: left; /* Left-align text */
        color: #ffffff; /* White text */
        font-size: 18px;
        font-weight: bold;
        border: 1px solid #4a4a4a; /* Subtle border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow */
        position: relative; /* Required for positioning the icon */
        overflow: hidden; /* Ensure the icon doesn't overflow */
    }

    .metric-box-accuracy::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8l-4 4-4-4"/></svg>'); /* Dartboard with arrow SVG */
        background-size: 40px 40px; /* Adjust size of the icon */
        background-position: left top; /* Position the icon at the top-left */
        background-repeat: no-repeat;
        opacity: 0.3; /* Blend the icon with the background */
        position: absolute;
        top: 20px; /* Adjust top position */
        left: 20px; /* Adjust left position */
        width: 40px;
        height: 40px;
        z-index: 1; /* Ensure the icon is behind the text */
    }

    .metric-box-accuracy h2 {
        margin-top: 60px; /* Push text down to avoid overlapping with the icon */
        margin-left: 20px; /* Left-align text */
        margin-bottom: 10px; /* Space between h2 and p */
    }

    .metric-box-accuracy p {
        margin-left: 20px; /* Left-align text */
        margin-bottom: 0; /* Remove extra margin */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit UI - Portfolio Section
st.markdown("<h1 style='text-align: center;'>Stock Sentimeter</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Know stock market trends and make smarter investment decisions with our intuitive portfolio tool.</p>", unsafe_allow_html=True)

# **2×2 Grid Layout Using HTML**
st.markdown(
    """
    <div class="grid-container">
        <div class="metric-box"><h2>43%</h2><p>Above Baseline</p></div>
        <div class="metric-box-gain"><h2>$13,813</h2><p>Gain on Buy</p></div>
        <div class="metric-box-speedometer"><h2>+0.75</h2><p>Sentiment Score</p></div>
        <div class="metric-box-accuracy"><h2>87%</h2><p>Accuracy</p></div>
    </div>
    """,
    unsafe_allow_html=True
)

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

# Initialize session state for selected table
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = "overall_latest_signal"
if "data" not in st.session_state:
    st.session_state["data"] = None
if "show_search" not in st.session_state:
    st.session_state["show_search"] = False

# Add spacing before "Select Sentiment Model"
st.markdown("<br>", unsafe_allow_html=True)

# Toggle buttons for selecting models
st.write("### Select Sentiment Model")
col1, col2, col3, col4 = st.columns(4)

def toggle_selection(table_key):
    if st.session_state["selected_table"] != table_key:
        st.session_state["selected_table"] = table_key
        st.session_state["data"] = None
        st.rerun()

with col1:
    if st.toggle("Google Trends", value=(st.session_state["selected_table"] == "gtrend_latest_signal")):
        toggle_selection("gtrend_latest_signal")

with col2:
    if st.toggle("News", value=(st.session_state["selected_table"] == "news_latest_signal")):
        toggle_selection("news_latest_signal")

with col3:
    if st.toggle("Twitter", value=(st.session_state["selected_table"] == "twitter_latest_signal")):
        toggle_selection("twitter_latest_signal")

with col4:
    if st.toggle("Overall", value=(st.session_state["selected_table"] == "overall_latest_signal")):
        toggle_selection("overall_latest_signal")

# Function to fetch and format data
def fetch_data(table, limit=5):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"SELECT date, comp_name, comp_symbol, trade_signal, entry_price FROM `{DB_NAME}`.`{table}` LIMIT {limit}"
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=["date", "comp_name", "comp_symbol", "trade_signal", "entry_price"])
        cursor.close()
        conn.close()

        # Combine company name and symbol into a single column with custom CSS
        df["Company Name"] = df.apply(
            lambda row: f'<div class="company-name-cell">{row["comp_name"]}<br><small>{row["comp_symbol"]}</small></div>',
            axis=1
        )
        
        # Drop the original comp_name and comp_symbol columns
        df = df.drop(columns=["comp_name", "comp_symbol"])

        # Add trending graph icons and background to the Trade Signal column
        df["Trade Signal"] = df["trade_signal"].apply(
            lambda x: (
                '<div class="trade-signal-buy">'
                '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M2 20 L8 15 L14 18 L20 12 L26 16 L32 10 L38 14 L44 8 L50 2" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                '</svg> ' + x + '</div>'
            ) if x.lower() == "buy" else (
                '<div class="trade-signal-sell">'
                '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M2 10 L8 15 L14 12 L20 18 L26 14 L32 20 L38 16 L44 22 L50 28" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                '</svg> ' + x + '</div>'
            ) if x.lower() == "sell" else x
        )

        # Rename columns to user-friendly names
        df = df.rename(columns={
            "date": "Date",
            "entry_price": "Entry Price ($)"
        })

        # Drop the original trade_signal column to avoid duplication
        df = df.drop(columns=["trade_signal"])

        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load initial data if not set
if st.session_state["data"] is None:
    st.session_state["data"] = fetch_data(st.session_state["selected_table"])

# Add spacing before "Portfolio"
st.markdown("<br>", unsafe_allow_html=True)

# Display formatted table with pretty headers
st.write("### Portfolio")
if st.session_state["data"] is not None:
    table_html = st.session_state["data"].to_html(index=False, classes="pretty-table", escape=False)
    st.markdown(table_html, unsafe_allow_html=True)

# Add Stock button
if st.button("Add Stock"):
    st.session_state["show_search"] = True

# Show search box when "Add Stock" is clicked
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
            query = f"SELECT date, comp_name, comp_symbol, trade_signal, entry_price FROM `{DB_NAME}`.`{st.session_state['selected_table']}` WHERE comp_symbol = %s"
            cursor.execute(query, (symbol,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()

            if result:
                new_row = pd.DataFrame(result, columns=["date", "comp_name", "comp_symbol", "trade_signal", "entry_price"])
                
                # Combine company name and symbol into a single column with custom CSS
                new_row["Company Name"] = new_row.apply(
                    lambda row: f'<div class="company-name-cell">{row["comp_name"]}<br><small>{row["comp_symbol"]}</small></div>',
                    axis=1
                )
                
                # Drop the original comp_name and comp_symbol columns
                new_row = new_row.drop(columns=["comp_name", "comp_symbol"])

                # Add trending graph icons and background to the Trade Signal column
                new_row["Trade Signal"] = new_row["trade_signal"].apply(
                    lambda x: (
                        '<div class="trade-signal-buy">'
                        '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                        '<path d="M2 20 L8 15 L14 18 L20 12 L26 16 L32 10 L38 14 L44 8 L50 2" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        '</svg> ' + x + '</div>'
                    ) if x.lower() == "buy" else (
                        '<div class="trade-signal-sell">'
                        '<svg width="50" height="30" viewBox="0 0 50 30" fill="none" xmlns="http://www.w3.org/2000/svg">'
                        '<path d="M2 10 L8 15 L14 12 L20 18 L26 14 L32 20 L38 16 L44 22 L50 28" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        '</svg> ' + x + '</div>'
                    ) if x.lower() == "sell" else x
                )

                # Rename new row to match the table headers
                new_row = new_row.rename(columns={
                    "date": "Date",
                    "entry_price": "Entry Price ($)"
                })

                # Drop the original trade_signal column to avoid duplication
                new_row = new_row.drop(columns=["trade_signal"])

                st.session_state["data"] = pd.concat([st.session_state["data"], new_row], ignore_index=True)
                st.session_state["show_search"] = False
                st.rerun()
            else:
                st.warning("Stock not found!")
        except Exception as e:
            st.error(f"Error searching stock: {e}")
