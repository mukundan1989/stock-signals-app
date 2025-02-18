import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# [Previous styling code remains exactly the same until the functions]

def create_price_chart(tab_index):
    dates = pd.date_range(start='2024-01-01', end='2024-02-18', freq='D')
    
    # Different price patterns for each tab
    if tab_index == 0:  # GTrends - Upward trend
        prices = [100 + i + (i**1.5)*0.1 for i in range(len(dates))]
    elif tab_index == 1:  # News - Volatile pattern
        prices = [100 + i + 20*np.sin(i/5) for i in range(len(dates))]
    elif tab_index == 2:  # Twitter - Downward trend
        prices = [150 - i + (i**1.5)*0.05 for i in range(len(dates))]
    else:  # Overall - Sideways pattern
        prices = [120 + 15*np.sin(i/10) for i in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        fill='tozeroy',
        fillcolor='rgba(0, 255, 148, 0.1)',
        line=dict(color='#00FF94', width=2),
        name='Price'
    ))
    
    fig.update_layout(
        plot_bgcolor='#1A1F2F',
        paper_bgcolor='#1A1F2F',
        font=dict(color='#E6E6E6'),
        margin=dict(l=0, r=0, t=20, b=0),
        height=350,
        xaxis=dict(
            showgrid=True,
            gridcolor='#2D3347',
            gridwidth=0.5,
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#2D3347',
            gridwidth=0.5,
            title=None
        ),
        hovermode='x unified'
    )
    return fig

def create_metrics_grid(tab_index):
    # Different metrics for each tab
    metrics = {
        0: {'win': 75.5, 'trades': 142, 'profit': 2.4, 'sp': 12.3},  # GTrends
        1: {'win': 68.2, 'trades': 95, 'profit': 1.8, 'sp': 8.7},    # News
        2: {'win': 81.3, 'trades': 167, 'profit': 3.1, 'sp': 15.2},  # Twitter
        3: {'win': 72.8, 'trades': 128, 'profit': 2.2, 'sp': 10.5}   # Overall
    }
    
    current_metrics = metrics[tab_index]
    
    col1, col2 = st.columns(2)
    with col1:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f'''
                <div class="metric-container">
                    <h3 style="margin:0">Win %</h3>
                    <h2 style="color:#00FF94;margin:10px 0">{current_metrics['win']}%</h2>
                </div>
            ''', unsafe_allow_html=True)
        with m2:
            st.markdown(f'''
                <div class="metric-container">
                    <h3 style="margin:0">No. of Trades</h3>
                    <h2 style="color:#00FF94;margin:10px 0">{current_metrics['trades']}</h2>
                </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        m3, m4 = st.columns(2)
        with m3:
            st.markdown(f'''
                <div class="metric-container">
                    <h3 style="margin:0">Profit Factor</h3>
                    <h2 style="color:#00FF94;margin:10px 0">{current_metrics['profit']}</h2>
                </div>
            ''', unsafe_allow_html=True)
        with m4:
            st.markdown(f'''
                <div class="metric-container">
                    <h3 style="margin:0">vs S&P</h3>
                    <h2 style="color:#00FF94;margin:10px 0">+{current_metrics['sp']}%</h2>
                </div>
            ''', unsafe_allow_html=True)

def create_trade_table(tab_index):
    # Different trade data for each tab
    trade_data = {
        0: {  # GTrends
            'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
            'Trade Type': ['Long', 'Short', 'Long', 'Short'],
            'Holding Period': ['2d', '3d', '1d', '4d'],
            '%P/L': ['+2.5%', '-1.2%', '+3.1%', '+0.8%']
        },
        1: {  # News
            'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
            'Trade Type': ['Short', 'Long', 'Short', 'Long'],
            'Holding Period': ['1d', '2d', '3d', '1d'],
            '%P/L': ['+1.8%', '-2.1%', '+2.7%', '-1.5%']
        },
        2: {  # Twitter
            'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
            'Trade Type': ['Long', 'Long', 'Short', 'Long'],
            'Holding Period': ['3d', '1d', '2d', '3d'],
            '%P/L': ['+3.2%', '+2.8%', '-1.7%', '+2.2%']
        },
        3: {  # Overall
            'Date': ['2024-02-18', '2024-02-17', '2024-02-16', '2024-02-15'],
            'Trade Type': ['Short', 'Short', 'Long', 'Short'],
            'Holding Period': ['2d', '4d', '1d', '2d'],
            '%P/L': ['+2.1%', '+1.9%', '-1.4%', '+1.6%']
        }
    }
    
    df = pd.DataFrame(trade_data[tab_index])
    st.dataframe(df, hide_index=True, use_container_width=True)

# Populate each tab with different data
for i, tab in enumerate(tabs):
    with tab:
        # Price performance chart with unique key and different data
        st.plotly_chart(create_price_chart(i), use_container_width=True, key=f"chart_{i}")
        
        # Metrics grid with different values
        create_metrics_grid(i)
        
        # Trade table with different data
        st.subheader("Trade History")
        create_trade_table(i)
