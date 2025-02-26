import streamlit as st
import pandas as pd
import mysql.connector

# Custom CSS for modern table styling
st.markdown(
    """
    <style>
    /* Table styling */
    .stDataFrame {
        background-color: #121212; /* Dark background */
        color: #ffffff; /* White text */
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Table header styling */
    .stDataFrame thead th {
        background-color: #1f1f1f; /* Slightly lighter dark background for header */
        color: #ffffff; /* White text */
        font-weight: bold;
        padding: 12px 15px;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Table row styling */
    .stDataFrame tbody tr {
        background-color: #1f1f1f; /* Slightly lighter dark background for rows */
        color: #ffffff; /* White text */
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Alternating row colors */
    .stDataFrame tbody tr:nth-of-type(odd) {
        background-color: #2a2a2a; /* Darker background for odd rows */
    }

    /* Hover effect for rows */
    .stDataFrame tbody tr:hover {
        background-color: #3a3a3a; /* Lighter background on hover */
    }

    /* Table cell styling */
    .stDataFrame tbody td {
        padding: 12px 15px;
        text-align: center;
        color: #ffffff; /* White text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Your existing code for fetching and displaying the table
# Example:
st.write("### Portfolio")
if st.session_state["data"] is not None:
    st.dataframe(st.session_state["data"], use_container_width=True, hide_index=True)
