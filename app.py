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

    /* Custom CSS for elegant table design with curved edges */
    .pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 30px;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 30px;
        overflow: hidden;
        text-align: center;
        border: none;
        color: var(--text-color);
    }

    /* Grey background with curved edges for each row */
    .pretty-table tbody tr {
        background-color: var(--secondary-background-color);
        border-radius: 50px;
        margin-bottom: 10px;
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
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
    }

    /* Hover effect for rows */
    .pretty-table tbody tr:hover {
        background-color: var(--hover-background-color);
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
        background-color: var(--secondary-background-color);
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    /* Custom CSS for the Trade Signal cell */
    .trade-signal-buy {
        background-color: #2e7d32;
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    .trade-signal-sell {
        background-color: #c62828;
        border-radius: 10px;
        padding: 10px;
        color: var(--text-color);
    }

    /* First grid box with line chart icon */
    .metric-box {
        background: linear-gradient(135deg, var(--secondary-background-color), var(--background-color));
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box p {
        margin-left: 20px;
        margin-bottom: 0;
    }

    /* Second grid box with pile of cash icon */
    .metric-box-gain {
        background: linear-gradient(135deg, var(--secondary-background-color), var(--background-color));
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-gain::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 1 0 0 7h5a3.5 3.5 0 1 1 0 7H6"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-gain h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box-gain p {
        margin-left: 20px;
        margin-bottom: 0;
    }

    /* Third grid box with speedometer gauge icon */
    .metric-box-speedometer {
        background: linear-gradient(135deg, var(--secondary-background-color), var(--background-color));
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-speedometer::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-speedometer h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box-speedometer p {
        margin-left: 20px;
        margin-bottom: 0;
    }

    /* Fourth grid box with dartboard and arrow icon */
    .metric-box-accuracy {
        background: linear-gradient(135deg, var(--secondary-background-color), var(--background-color));
        padding: 20px;
        border-radius: 10px;
        text-align: left;
        color: var(--text-color);
        font-size: 18px;
        font-weight: bold;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .metric-box-accuracy::before {
        content: "";
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8l-4 4-4-4"/></svg>');
        background-size: 40px 40px;
        background-position: left top;
        background-repeat: no-repeat;
        opacity: 0.3;
        position: absolute;
        top: 20px;
        left: 20px;
        width: 40px;
        height: 40px;
        z-index: 1;
    }

    .metric-box-accuracy h2 {
        margin-top: 60px;
        margin-left: 20px;
        margin-bottom: 10px;
    }

    .metric-box-accuracy p {
        margin-left: 20px;
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Rest of the code remains unchanged...
