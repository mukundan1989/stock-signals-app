import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Custom CSS to match original styling
st.markdown(
    """
    <style>
    /* Match button styling from original code */
    .stButton > button:hover {
        background-color: #000000;
        color: white;
    }
    .stButton > button {
        background-color: #282828;
        color: white;
    }
    .stButton > button:active {
        background-color: #282828;
        color: white;
    }
    /* Table styling */
    .dataframe {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Google Trends Backtesting Page
st.title("Google Trends Backtester")
st.write("Backtest trading strategies based on Google Trends data")

# Input Parameters
st.header("Strategy Parameters")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entry Conditions")
    stock_symbol = st.text_input("Select Stock", value="GOOGL")
    
    # Google Trends parameters
    num_keywords = st.number_input("Number of Keywords to Monitor", 
                                 min_value=1, max_value=20, value=5)
    
    weeks_rising = st.number_input("Keywords Rising for Minimum (weeks)", 
                                 min_value=1, max_value=12, value=2)
    
    rising_percentage = st.number_input("Percentage of Keywords Indicating Rising Trend (%)", 
                                      min_value=1, max_value=100, value=60)

with col2:
    st.subheader("Exit Conditions")
    holding_days = st.number_input("Time Wise Exit (Days)", 
                                 min_value=1, max_value=30, value=5)
    stop_loss = st.number_input("Max Loss Stop Loss (%)", 
                              min_value=0.1, max_value=50.0, value=10.0, step=0.5)

# Backtest button
if st.button("Run Backtest", key="backtest_button"):
    st.write("Running backtest...")
    
    # Generate dummy data based on parameters (only long trades)
    num_trades = min(30, num_keywords * 3)  # Scale with number of keywords
    dates = pd.date_range(end=datetime.today(), periods=num_trades).date
    
    holding_periods = np.random.randint(1, holding_days+1, num_trades)
    pct_changes = np.random.uniform(-stop_loss, 20, num_trades)
    
    # Create trades dataframe (only long trades)
    trades = pd.DataFrame({
        "Date": dates,
        "Holding Period": holding_periods,
        "P/L %": pct_changes,
        "Trigger Keywords": np.random.randint(1, num_keywords+1, num_trades)
    })
    
    # Display trades
    st.subheader("Trade History")
    st.dataframe(trades.style.format({"P/L %": "{:.2f}%"}), hide_index=True)
    
    # Calculate summary statistics (only for long trades)
    total_trades = len(trades)
    winning_trades = trades[trades["P/L %"] > 0]
    losing_trades = trades[trades["P/L %"] <= 0]
    win_rate = len(winning_trades) / total_trades * 100
    
    # Prepare summary data (removed short trade metrics)
    summary_data = {
        "Metric": [
            "Total Trades", 
            "Win Rate (%)", 
            "Lose Rate (%)",
            "Max Drawdown ($)", 
            "Profit Factor",
            "Parameters (Keywords/Weeks/Rising %)"
        ],
        "Value": [
            total_trades,
            f"{win_rate:.1f}",
            f"{100 - win_rate:.1f}",
            f"${np.random.randint(500, 2000)}",
            f"{np.random.uniform(0.8, 2.5):.2f}",
            f"{num_keywords}/{weeks_rising}w/{rising_percentage}%"
        ]
    }
    
    # Display summary
    st.subheader("Backtest Summary")
    st.table(pd.DataFrame(summary_data))
    
    st.success("Backtest completed!")
