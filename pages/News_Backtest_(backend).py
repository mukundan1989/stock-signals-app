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

# News Articles Backtesting Page
st.title("News Articles Backtester")
st.write("Backtest trading strategies based on news and analyst articles")

# Input Parameters
st.header("Strategy Parameters")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entry Conditions")
    stock_symbol = st.text_input("Select Stock", value="AAPL")
    
    # News article parameters
    news_months = st.number_input("News Article Lookback (months)", 
                                min_value=1, max_value=12, value=3)
    
    analyst_months = st.number_input("Analyst Article Lookback (months)", 
                                   min_value=1, max_value=12, value=3)
    
    text_model = st.radio("Text Analysis Model", 
                         ("FinBERT", "AI Model"), 
                         horizontal=True)
    
    # Signal Weightage
    st.subheader("Signal Weightage")
    st.write("(Sum must be ≤ 1)")
    news_weight = st.number_input("News Weight", 
                                min_value=0.0, max_value=1.0, 
                                value=0.6, step=0.05)
    analyst_weight = st.number_input("Analyst Weight", 
                                   min_value=0.0, max_value=1.0, 
                                   value=0.4, step=0.05)
    
    # Validate weights
    total_weight = news_weight + analyst_weight
    if total_weight > 1.0:
        st.error(f"Total weight exceeds 1.0 (Current: {total_weight:.2f})")
        st.stop()
    
    article_percentage = st.number_input("Percentage of Articles to Determine Direction (%)", 
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
    
    # Generate dummy data based on parameters
    num_trades = max(10, min(50, news_months * 5))  # Scale with lookback period
    
    dates = pd.date_range(end=datetime.today(), periods=num_trades).date
    
    # Generate trades with success probability based on article percentage
    success_prob = (article_percentage / 100) * 0.9  # Scale probability
    trade_types = np.random.choice(["Long", "Short"], num_trades, 
                                 p=[success_prob, 1-success_prob])
    
    holding_periods = np.random.randint(1, holding_days+1, num_trades)
    pct_changes = np.random.uniform(-stop_loss, 20, num_trades)
    
    # Create trades dataframe
    trades = pd.DataFrame({
        "Date": dates,
        "Trade Type": trade_types,
        "Holding Period": holding_periods,
        "P/L %": pct_changes,
        "Model Used": text_model
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
    
    # Prepare summary data (removed the requested metrics)
    summary_data = {
        "Metric": [
            "Total Trades", "Win Rate (%)", "Lose Rate (%)",
            "Total Long Trades", "Long Win Rate (%)", "Long Lose Rate (%)",
            "Total Short Trades", "Short Win Rate (%)", "Short Lose Rate (%)",
            "Max Drawdown ($)", "Profit Factor",
            "Text Analysis Model",
            "Weights (News/Analyst)"
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
            text_model,
            f"{news_weight:.1f}/{analyst_weight:.1f}"
        ]
    }
    
    # Display summary
    st.subheader("Backtest Summary")
    st.table(pd.DataFrame(summary_data))
    
    st.success("Backtest completed!")
