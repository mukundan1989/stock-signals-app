import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

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
    /* Style for toggle switches */
    .st-cb {
        margin-bottom: 10px;
    }
    /* Table styling */
    .dataframe {
        width: 100%;
    }
    /* Signal weightage boxes */
    .weight-box {
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Backtesting Page
st.title("Twitter Sentiment Backtester")
st.write("Backtest trading strategies based on Twitter sentiment criteria")

# Input Parameters
st.header("Strategy Parameters")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entry Conditions")
    stock_symbol = st.text_input("Select Stock", value="TTD")
    
    # Date range selection
    months_options = ["All", "1 month", "3 months", "6 months", "1 year"]
    tweet_months = st.selectbox("Tweet Selection Criteria", months_options)
    
    follower_count = st.number_input("Minimum Follower Count", min_value=0, value=200)
    likes_count = st.number_input("Minimum Likes Count", min_value=0, value=20)
    fin_influencer = st.toggle("Financial Influencer Only", value=True)
    blue_verified = st.toggle("Blue Verified Only", value=True)
    
    # User creation date
    user_age_options = [">1 month", ">6 months", ">1 year", ">3 years"]
    user_age = st.selectbox("Minimum User Age", user_age_options)
    
    # Signal Weightage section
    st.subheader("Signal Weightage")
    st.write("(Sum must be ≤ 1)")
    
    finbert = st.number_input("FinBERT Text", min_value=0.0, max_value=1.0, value=0.3, step=0.05, key="finbert")
    ai_text = st.number_input("AI Text Analysis", min_value=0.0, max_value=1.0, value=0.3, step=0.05, key="ai_text")
    verified = st.number_input("Verified", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="verified")
    likes = st.number_input("Likes", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="likes")
    
    # Validate sum of weights
    total_weight = finbert + ai_text + verified + likes
    if total_weight > 1.0:
        st.error(f"Total weight exceeds 1.0 (Current: {total_weight:.2f})")
        st.stop()

with col2:
    st.subheader("Exit Conditions")
    holding_days = st.number_input("Time Wise Exit (Days)", min_value=1, max_value=30, value=5)
    stop_loss = st.number_input("Max Loss Stop Loss (%)", min_value=0.1, max_value=50.0, value=10.0, step=0.5)

# Backtest button
if st.button("Run Backtest", key="backtest_button"):
    st.write("Running backtest...")
    
    # Generate dummy data
    num_trades = 50
    dates = pd.date_range(end=datetime.today(), periods=num_trades).date
    trade_types = np.random.choice(["Long", "Short"], num_trades, p=[0.6, 0.4])
    holding_periods = np.random.randint(1, holding_days+1, num_trades)
    
    # Apply signal weights to generate more realistic P/L
    weighted_pl = np.random.uniform(-stop_loss, 20, num_trades) * (finbert + ai_text + verified + likes)
    pct_changes = np.clip(weighted_pl, -stop_loss, 20)
    
    # Create trades dataframe
    trades = pd.DataFrame({
        "Date": dates,
        "Trade Type": trade_types,
        "Holding Period": holding_periods,
        "P/L %": pct_changes
    })
    
    # Display trades
    st.subheader("Trade History")
    st.dataframe(trades.style.format({"P/L %": "{:.2f}%"}), hide_index=True)
    
    # Calculate summary statistics
    total_trades = len(trades)
    winning_trades = trades[trades["P/L %"] > 0]
    losing_trades = trades[trades["P/L %"] <= 0]
    win_rate = len(winning_trades) / total_trades * 100
    
    long_trades = trades[trades["Trade Type"] == "Long"]
    short_trades = trades[trades["Trade Type"] == "Short"]
    
    # Prepare summary data
    summary_data = {
        "Metric": [
            "Total Trades", "Win Rate (%)", "Lose Rate (%)",
            "Total Long Trades", "Long Win Rate (%)", "Long Lose Rate (%)",
            "Total Short Trades", "Short Win Rate (%)", "Short Lose Rate (%)",
            "Max Drawdown ($)", "Profit Factor",
            "Signal Weights (FinBERT/AI/Verified/Likes)",
            "Applied Weight Total"
        ],
        "Value": [
            total_trades,
            f"{win_rate:.1f}",
            f"{100 - win_rate:.1f}",
            len(long_trades),
            f"{len(long_trades[long_trades['P/L %'] > 0]) / len(long_trades) * 100:.1f}" if len(long_trades) > 0 else "0.0",
            f"{len(long_trades[long_trades['P/L %'] <= 0]) / len(long_trades) * 100:.1f}" if len(long_trades) > 0 else "0.0",
            len(short_trades),
            f"{len(short_trades[short_trades['P/L %'] > 0]) / len(short_trades) * 100:.1f}" if len(short_trades) > 0 else "0.0",
            f"{len(short_trades[short_trades['P/L %'] <= 0]) / len(short_trades) * 100:.1f}" if len(short_trades) > 0 else "0.0",
            f"${np.random.randint(500, 2000)}",
            f"{np.random.uniform(0.8, 2.5):.2f}",
            f"{finbert:.2f}/{ai_text:.2f}/{verified:.2f}/{likes:.2f}",
            f"{total_weight:.2f}"
        ]
    }
    
    # Display summary
    st.subheader("Backtest Summary")
    st.table(pd.DataFrame(summary_data))
    
    st.success("Backtest completed!")
