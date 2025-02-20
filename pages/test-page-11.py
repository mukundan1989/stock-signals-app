import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(layout="wide", page_title="Stock Market Analysis Charts")

# Generate sample stock data
@st.cache_data
def generate_stock_data():
    np.random.seed(42)
    
    # Generate dates for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate OHLCV data
    base_price = 100
    volatility = 0.02
    prices = []
    current_price = base_price
    
    for _ in range(len(dates)):
        open_price = current_price
        high_price = open_price * (1 + np.random.uniform(0, volatility))
        low_price = open_price * (1 - np.random.uniform(0, volatility))
        close_price = np.random.uniform(low_price, high_price)
        volume = np.random.normal(1000000, 200000)
        
        prices.append([open_price, high_price, low_price, close_price, volume])
        current_price = close_price * (1 + np.random.normal(0.0001, volatility/2))
    
    df = pd.DataFrame(prices, columns=['Open', 'High', 'Low', 'Close', 'Volume'], index=dates)
    
    # Calculate technical indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Upper_Band'] = df['Close'].rolling(window=20).mean() + (df['Close'].rolling(window=20).std() * 2)
    df['Lower_Band'] = df['Close'].rolling(window=20).mean() - (df['Close'].rolling(window=20).std() * 2)
    df['RSI'] = calculate_rsi(df['Close'])
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    
    return df

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Generate data
df = generate_stock_data()

# Title
st.title("📈 Stock Market Technical Analysis Charts")
st.markdown("### Comprehensive Technical Analysis Visualization Suite")

# 1. Candlestick Chart with Moving Averages
st.subheader("1. Candlestick Chart with Moving Averages")
fig_candle = go.Figure()

# Add candlesticks
fig_candle.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='OHLC'
))

# Add moving averages
fig_candle.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange')))
fig_candle.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='blue')))

fig_candle.update_layout(
    yaxis_title='Price',
    xaxis_title='Date',
    template='plotly_white'
)
st.plotly_chart(fig_candle, use_container_width=True)

# 2. Bollinger Bands
st.subheader("2. Bollinger Bands")
fig_bb = go.Figure()

fig_bb.add_trace(go.Scatter(x=df.index, y=df['Upper_Band'], name='Upper Band', line=dict(dash='dash')))
fig_bb.add_trace(go.Scatter(x=df.index, y=df['Lower_Band'], name='Lower Band', line=dict(dash='dash')))
fig_bb.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'))
fig_bb.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='20-day MA'))

fig_bb.update_layout(
    yaxis_title='Price',
    xaxis_title='Date',
    template='plotly_white'
)
st.plotly_chart(fig_bb, use_container_width=True)

# 3. Volume Profile
st.subheader("3. Volume Profile")
fig_volume = go.Figure()

fig_volume.add_trace(go.Bar(
    x=df.index,
    y=df['Volume'],
    name='Volume',
    marker_color='rgba(0, 128, 0, 0.5)'
))

fig_volume.add_trace(go.Scatter(
    x=df.index,
    y=df['Close'],
    name='Close Price',
    yaxis='y2'
))

fig_volume.update_layout(
    yaxis2=dict(
        title='Price',
        overlaying='y',
        side='right'
    ),
    yaxis=dict(title='Volume'),
    template='plotly_white'
)
st.plotly_chart(fig_volume, use_container_width=True)

# 4. RSI Indicator
st.subheader("4. Relative Strength Index (RSI)")
fig_rsi = go.Figure()

fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'))
fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")

fig_rsi.update_layout(
    yaxis_title='RSI',
    xaxis_title='Date',
    yaxis=dict(range=[0, 100]),
    template='plotly_white'
)
st.plotly_chart(fig_rsi, use_container_width=True)

# 5. MACD
st.subheader("5. MACD (Moving Average Convergence Divergence)")
fig_macd = go.Figure()

fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'))
fig_macd.add_trace(go.Bar(
    x=df.index,
    y=df['MACD'] - df['Signal'],
    name='MACD Histogram',
    marker_color=np.where(df['MACD'] >= df['Signal'], 'green', 'red')
))

fig_macd.update_layout(
    yaxis_title='MACD',
    xaxis_title='Date',
    template='plotly_white'
)
st.plotly_chart(fig_macd, use_container_width=True)

# 6. Price Channel
st.subheader("6. Price Channel")
fig_channel = go.Figure()

df['Upper_Channel'] = df['High'].rolling(20).max()
df['Lower_Channel'] = df['Low'].rolling(20).min()

fig_channel.add_trace(go.Scatter(x=df.index, y=df['Upper_Channel'], name='Upper Channel', line=dict(dash='dash')))
fig_channel.add_trace(go.Scatter(x=df.index, y=df['Lower_Channel'], name='Lower Channel', line=dict(dash='dash')))
fig_channel.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'))

fig_channel.update_layout(
    yaxis_title='Price',
    xaxis_title='Date',
    template='plotly_white'
)
st.plotly_chart(fig_channel, use_container_width=True)

# 7. Advanced Candlestick Patterns
st.subheader("7. Candlestick with Volume and MA")
fig_advanced = go.Figure()

# Candlesticks
fig_advanced.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='OHLC'
))

# Volume bars
colors = ['green' if close >= open else 'red' 
          for close, open in zip(df['Close'], df['Open'])]

fig_advanced.add_trace(go.Bar(
    x=df.index,
    y=df['Volume'],
    name='Volume',
    marker_color=colors,
    opacity=0.3,
    yaxis='y2'
))

fig_advanced.update_layout(
    yaxis2=dict(
        title='Volume',
        overlaying='y',
        side='right'
    ),
    yaxis=dict(title='Price'),
    template='plotly_white'
)
st.plotly_chart(fig_advanced, use_container_width=True)

# 8. Heikin-Ashi Chart
st.subheader("8. Heikin-Ashi Chart")
df_ha = pd.DataFrame(index=df.index)
df_ha['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close'])/4
df_ha['Open'] = df['Open'].copy()
for i in range(1, len(df)):
    df_ha.iloc[i, df_ha.columns.get_loc('Open')] = (df_ha.iloc[i-1, df_ha.columns.get_loc('Open')] + 
                                                   df_ha.iloc[i-1, df_ha.columns.get_loc('Close')])/2
df_ha['High'] = df[['High', 'Open', 'Close']].max(axis=1)
df_ha['Low'] = df[['Low', 'Open', 'Close']].min(axis=1)

fig_ha = go.Figure(data=[go.Candlestick(
    x=df_ha.index,
    open=df_ha['Open'],
    high=df_ha['High'],
    low=df_ha['Low'],
    close=df_ha['Close'],
    name='Heikin-Ashi'
)])

fig_ha.update_layout(
    yaxis_title='Price',
    xaxis_title='Date',
    template='plotly_white'
)
st.plotly_chart(fig_ha, use_container_width=True)

# Add interactivity note
st.info("💡 All charts are interactive! You can zoom, pan, and hover over data points for more information.")
