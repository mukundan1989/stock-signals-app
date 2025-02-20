import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(layout="wide", page_title="Advanced Charts Dashboard")

# Generate sample data
@st.cache_data
def generate_data():
    # Time series data
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    np.random.seed(42)
    
    df = pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(100, 15, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1)),
        'revenue': np.random.normal(1000, 150, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1)),
        'customers': np.random.normal(500, 50, len(dates)) * (1 + np.cos(np.arange(len(dates)) * 0.1)),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Sports'], len(dates)),
        'region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
        'satisfaction': np.random.normal(4.2, 0.3, len(dates))
    })
    
    # Add some trends
    df['sales'] = df['sales'] * (1 + np.arange(len(df)) * 0.001)
    df['revenue'] = df['revenue'] * (1 + np.arange(len(df)) * 0.002)
    
    return df

df = generate_data()

# Title and description
st.title("📊 Advanced Analytics Dashboard")
st.markdown("### Interactive Visualization Gallery")

# 1. Advanced Area Chart
st.subheader("1. Revenue Trends by Region")
fig_area = px.area(df, x='date', y='revenue', color='region',
                   line_shape='spline',  # Smooth lines
                   template='plotly_dark',
                   color_discrete_sequence=px.colors.qualitative.Set3)
fig_area.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend_title_text='Region'
)
st.plotly_chart(fig_area, use_container_width=True)

# 2. Animated Bubble Chart
st.subheader("2. Sales, Revenue, and Customer Satisfaction by Category")
fig_bubble = px.scatter(df, x='sales', y='revenue',
                       size='customers', color='category',
                       animation_frame=df['date'].dt.strftime('%Y-%m'),
                       size_max=60,
                       template='plotly_white',
                       color_discrete_sequence=px.colors.qualitative.Bold)
fig_bubble.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
st.plotly_chart(fig_bubble, use_container_width=True)

# 3. Custom Styled Bar Chart
st.subheader("3. Monthly Category Performance")
monthly_data = df.groupby([df['date'].dt.strftime('%B'), 'category'])['revenue'].mean().reset_index()
fig_bar = px.bar(monthly_data, x='date', y='revenue', color='category',
                 barmode='group',
                 template='plotly_white',
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_bar.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    bargap=0.2,
    bargroupgap=0.1
)
st.plotly_chart(fig_bar, use_container_width=True)

# 4. Radar Chart
st.subheader("4. Regional Performance Metrics")
regional_metrics = df.groupby('region').agg({
    'sales': 'mean',
    'revenue': 'mean',
    'customers': 'mean',
    'satisfaction': 'mean'
}).reset_index()

fig_radar = go.Figure()
for region in regional_metrics['region']:
    metrics = regional_metrics[regional_metrics['region'] == region]
    fig_radar.add_trace(go.Scatterpolar(
        r=[metrics['sales'].iloc[0]/100, metrics['revenue'].iloc[0]/1000,
           metrics['customers'].iloc[0]/500, metrics['satisfaction'].iloc[0]],
        theta=['Sales', 'Revenue', 'Customers', 'Satisfaction'],
        name=region,
        fill='toself'
    ))
fig_radar.update_layout(polar=dict(radialaxis=dict(showticklabels=False, ticks='')))
st.plotly_chart(fig_radar, use_container_width=True)

# 5. Custom Candlestick Chart
st.subheader("5. Weekly Sales Volatility")
weekly_stats = df.groupby(pd.Grouper(key='date', freq='W')).agg({
    'sales': ['first', 'max', 'min', 'last']
}).reset_index()
weekly_stats.columns = ['date', 'open', 'high', 'low', 'close']

fig_candle = go.Figure(data=[go.Candlestick(
    x=weekly_stats['date'],
    open=weekly_stats['open'],
    high=weekly_stats['high'],
    low=weekly_stats['low'],
    close=weekly_stats['close']
)])
fig_candle.update_layout(
    template='plotly_dark',
    xaxis_rangeslider_visible=False
)
st.plotly_chart(fig_candle, use_container_width=True)

# 6. Sunburst Chart
st.subheader("6. Hierarchical Revenue Distribution")
fig_sunburst = px.sunburst(df, path=['region', 'category'], values='revenue',
                          color='satisfaction',
                          color_continuous_scale='RdYlBu',
                          template='plotly_white')
st.plotly_chart(fig_sunburst, use_container_width=True)

# 7. Advanced Line Chart with Range Selector
st.subheader("7. Interactive Revenue Timeline")
fig_line = px.line(df, x='date', y=['revenue', 'sales'],
                   template='plotly_white',
                   line_shape='spline')
fig_line.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
)
st.plotly_chart(fig_line, use_container_width=True)

# 8. Violin Plot
st.subheader("8. Revenue Distribution by Category")
fig_violin = px.violin(df, y='revenue', x='category', color='category',
                      box=True, points="all",
                      template='plotly_white',
                      color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig_violin, use_container_width=True)

# 9. Scatter Matrix
st.subheader("9. Multi-variable Analysis")
fig_scatter_matrix = px.scatter_matrix(df, 
    dimensions=['sales', 'revenue', 'customers', 'satisfaction'],
    color='category',
    template='plotly_white')
fig_scatter_matrix.update_traces(diagonal_visible=False)
st.plotly_chart(fig_scatter_matrix, use_container_width=True)

# 10. Tree Map
st.subheader("10. Revenue Tree Map")
fig_treemap = px.treemap(df, path=[px.Constant("Total"), 'region', 'category'],
                        values='revenue',
                        color='satisfaction',
                        color_continuous_scale='RdYlBu',
                        template='plotly_white')
st.plotly_chart(fig_treemap, use_container_width=True)
