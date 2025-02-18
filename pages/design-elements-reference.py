import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(layout="wide", page_title="Elegant Analytics", page_icon="⚡")

# Modern Glassmorphism CSS
st.markdown("""
    <style>
    /* Main Background with animated gradient */
    .stApp {
        background: linear-gradient(-45deg, #0A0F1C, #1A1F2C, #162037, #1E2A4A);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Glassmorphism Card Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* Modern Metric Card */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Typography */
    .elegant-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(45deg, #fff, #a5a5a5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }
    
    .metric-trend {
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    /* Custom Tab Design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        padding: 0.5rem;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 8px 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    /* Dataframe Styling */
    .dataframe {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 15px;
        border: none;
    }
    
    .dataframe th {
        background: rgba(255, 255, 255, 0.05);
        color: white;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="elegant-title">⚡ Elegant Analytics</h1>', unsafe_allow_html=True)

# Generate sample data
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
data = {
    'Date': dates,
    'Revenue': np.random.normal(50000, 5000, len(dates)),
    'Users': np.random.normal(1000, 100, len(dates)),
    'Engagement': np.random.normal(75, 15, len(dates)),
    'Conversion': np.random.uniform(1, 5, len(dates))
}
df = pd.DataFrame(data)

# KPI Row
cols = st.columns(4)
metrics = [
    {
        "label": "Total Revenue",
        "value": "$1.25M",
        "change": "+12.3%",
        "trend": "positive"
    },
    {
        "label": "Active Users",
        "value": "8.5K",
        "change": "+8.7%",
        "trend": "positive"
    },
    {
        "label": "Engagement Score",
        "value": "78.2",
        "change": "-2.1%",
        "trend": "negative"
    },
    {
        "label": "Conversion Rate",
        "value": "4.2%",
        "change": "+5.3%",
        "trend": "positive"
    }
]

for col, metric in zip(cols, metrics):
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-trend" style="color: {'#00ff9f' if metric['trend'] == 'positive' else '#ff4b4b'}">
                    {metric['change']}
                    {'↑' if metric['trend'] == 'positive' else '↓'}
                </div>
            </div>
        """, unsafe_allow_html=True)

# Create tabs with modern styling
tabs = st.tabs(["📊 Overview", "📈 Performance", "🎯 Insights"])

with tabs[0]:
    # Modern Area Chart
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    fig_area = px.area(df, x='Date', y='Revenue', 
                      title='Revenue Trends')
    fig_area.update_traces(
        fill='tozeroy',
        fillcolor='rgba(0, 255, 159, 0.1)',
        line=dict(color='#00ff9f', width=2)
    )
    fig_area.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_size=20,
        showlegend=False,
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)')
    )
    st.plotly_chart(fig_area, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    col1, col2 = st.columns(2)
    
    with col1:
        # Modern Gauge
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=78,
            delta={'reference': 70},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#00ff9f"},
                'bgcolor': "rgba(255, 255, 255, 0.1)",
                'borderwidth': 2,
                'bordercolor': "rgba(255, 255, 255, 0.2)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255, 75, 75, 0.15)'},
                    {'range': [50, 80], 'color': 'rgba(0, 255, 159, 0.15)'},
                    {'range': [80, 100], 'color': 'rgba(0, 255, 159, 0.3)'}
                ]
            }
        ))
        fig_gauge.update_layout(
            title_text="Performance Score",
            font_color="white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Modern Heatmap
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        hours = list(range(24))
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        z = np.random.rand(7, 24)
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=z,
            x=hours,
            y=days,
            colorscale=[
                [0, 'rgba(0,0,0,0)'],
                [0.5, 'rgba(0,255,159,0.3)'],
                [1, 'rgba(0,255,159,0.8)']
            ]
        ))
        fig_heatmap.update_layout(
            title_text="Activity Distribution",
            font_color="white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    # Modern Table with glassmorphism
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    monthly_stats = df.resample('M', on='Date').agg({
        'Revenue': ['sum', 'mean'],
        'Users': 'mean',
        'Engagement': 'mean',
        'Conversion': 'mean'
    }).round(2)
    monthly_stats.columns = ['Total Revenue', 'Avg Revenue', 'Avg Users', 'Avg Engagement', 'Avg Conversion']
    st.dataframe(monthly_stats.style.background_gradient(
        cmap='viridis',
        subset=['Avg Revenue', 'Avg Users', 'Avg Engagement']
    ), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with last update time
st.markdown(f"""
    <div style='text-align: center; color: rgba(255,255,255,0.5); padding: 20px; font-size: 0.8rem;'>
        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
