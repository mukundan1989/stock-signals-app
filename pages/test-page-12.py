import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(layout="wide", page_title="Area Charts Gallery")

# Generate sample data
@st.cache_data
def generate_data():
    # Date range
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Basic data
    df = pd.DataFrame({
        'date': dates,
        'revenue': np.random.normal(1000, 100, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1)),
        'profit': np.random.normal(300, 50, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1)),
        'costs': np.random.normal(700, 80, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1)),
        'category': np.random.choice(['A', 'B', 'C', 'D'], len(dates))
    })
    
    # Add some trends and seasonality
    df['revenue'] = df['revenue'] * (1 + np.arange(len(df)) * 0.001)
    df['visitors'] = np.random.normal(5000, 1000, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1))
    
    # Create regional data
    regions = ['North', 'South', 'East', 'West']
    regional_data = pd.DataFrame()
    for region in regions:
        temp_df = pd.DataFrame({
            'date': dates,
            'region': region,
            'sales': np.random.normal(1000, 100, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1))
        })
        regional_data = pd.concat([regional_data, temp_df])
    
    return df, regional_data

df, regional_data = generate_data()

# Title
st.title("📊 Advanced Area Charts Gallery")
st.markdown("### Interactive Area Chart Visualizations")

# 1. Basic Area Chart
st.subheader("1. Basic Area Chart")
fig1 = px.area(df, x='date', y='revenue',
               title='Revenue Over Time',
               template='plotly_white')
fig1.update_traces(fillcolor='rgba(64, 224, 208, 0.5)')
st.plotly_chart(fig1, use_container_width=True)

# 2. Stacked Area Chart
st.subheader("2. Stacked Area Chart by Region")
fig2 = px.area(regional_data, x='date', y='sales', color='region',
               title='Regional Sales Distribution',
               template='plotly_white')
st.plotly_chart(fig2, use_container_width=True)

# 3. Normalized Stacked Area (100%)
st.subheader("3. Normalized Stacked Area")
fig3 = px.area(regional_data, x='date', y='sales', color='region',
               title='Regional Sales Distribution (%)',
               template='plotly_white',
               groupnorm='percent')
st.plotly_chart(fig3, use_container_width=True)

# 4. Gradient Area Chart
st.subheader("4. Gradient Area Chart")
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=df['date'],
    y=df['revenue'],
    fill='tonexty',
    fillcolor='rgba(0, 100, 255, 0.2)',
    line=dict(color='rgb(0, 100, 255)'),
    name='Revenue',
    mode='lines',
    gradient=dict(
        type="vertical",
        color="white"
    )
))
fig4.update_layout(title='Revenue with Gradient Fill')
st.plotly_chart(fig4, use_container_width=True)

# 5. Multiple Area Charts
st.subheader("5. Multiple Area Charts")
fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=df['date'], y=df['revenue'],
    fill='tonexty',
    name='Revenue',
    fillcolor='rgba(0, 255, 0, 0.2)'
))
fig5.add_trace(go.Scatter(
    x=df['date'], y=df['costs'],
    fill='tonexty',
    name='Costs',
    fillcolor='rgba(255, 0, 0, 0.2)'
))
fig5.update_layout(title='Revenue vs Costs')
st.plotly_chart(fig5, use_container_width=True)

# 6. Range Area Chart
st.subheader("6. Range Area Chart")
df['revenue_high'] = df['revenue'] * 1.1
df['revenue_low'] = df['revenue'] * 0.9
fig6 = go.Figure()
fig6.add_trace(go.Scatter(
    x=df['date'], y=df['revenue_high'],
    fill=None,
    mode='lines',
    line_color='rgba(0, 100, 255, 0.5)',
    name='High Range'
))
fig6.add_trace(go.Scatter(
    x=df['date'], y=df['revenue_low'],
    fill='tonexty',
    mode='lines',
    line_color='rgba(0, 100, 255, 0.5)',
    name='Low Range'
))
fig6.update_layout(title='Revenue Range')
st.plotly_chart(fig6, use_container_width=True)

# 7. Area Chart with Moving Average
st.subheader("7. Area Chart with Moving Average")
df['MA_7'] = df['revenue'].rolling(window=7).mean()
df['MA_30'] = df['revenue'].rolling(window=30).mean()

fig7 = go.Figure()
fig7.add_trace(go.Scatter(
    x=df['date'], y=df['revenue'],
    fill='tonexty',
    name='Revenue',
    fillcolor='rgba(0, 255, 0, 0.1)'
))
fig7.add_trace(go.Scatter(
    x=df['date'], y=df['MA_7'],
    name='7-day MA',
    line=dict(color='red')
))
fig7.add_trace(go.Scatter(
    x=df['date'], y=df['MA_30'],
    name='30-day MA',
    line=dict(color='blue')
))
fig7.update_layout(title='Revenue with Moving Averages')
st.plotly_chart(fig7, use_container_width=True)

# 8. Streamgraph
st.subheader("8. Streamgraph")
fig8 = px.area(regional_data, x='date', y='sales', color='region',
               title='Regional Sales Distribution (Streamgraph)',
               template='plotly_white')
fig8.update_layout(
    showlegend=True,
    stackgroup='one',
    groupnorm='',
)
st.plotly_chart(fig8, use_container_width=True)

# 9. Area Chart with Patterns
st.subheader("9. Area Chart with Patterns")
fig9 = go.Figure()
regions = regional_data['region'].unique()
patterns = ['/', '\\', 'x', '-', '|', '+', '.']
for i, region in enumerate(regions):
    data = regional_data[regional_data['region'] == region]
    fig9.add_trace(go.Scatter(
        x=data['date'],
        y=data['sales'],
        name=region,
        mode='lines',
        stackgroup='one',
        fillpattern=dict(
            shape=patterns[i % len(patterns)],
            size=10,
            fgopacity=0.5,
            solidity=0.5
        )
    ))
fig9.update_layout(title='Regional Sales with Patterns')
st.plotly_chart(fig9, use_container_width=True)

# 10. Dual-Axis Area Chart
st.subheader("10. Dual-Axis Area Chart")
fig10 = go.Figure()
fig10.add_trace(go.Scatter(
    x=df['date'],
    y=df['revenue'],
    name='Revenue',
    fill='tonexty',
    fillcolor='rgba(0, 255, 0, 0.2)',
    yaxis='y'
))
fig10.add_trace(go.Scatter(
    x=df['date'],
    y=df['visitors'],
    name='Visitors',
    fill='tonexty',
    fillcolor='rgba(255, 0, 0, 0.2)',
    yaxis='y2'
))
fig10.update_layout(
    title='Revenue vs Visitors',
    yaxis=dict(title='Revenue'),
    yaxis2=dict(title='Visitors', overlaying='y', side='right')
)
st.plotly_chart(fig10, use_container_width=True)

# Add interactivity note
st.info("💡 All charts are interactive! Try hovering, zooming, or clicking on legend items to show/hide series.")
