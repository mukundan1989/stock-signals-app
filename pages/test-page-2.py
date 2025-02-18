import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(layout="wide", page_title="Premium Analytics Dashboard", page_icon="✨")

# Enhanced Custom CSS for a more premium look
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #0A0F1C 0%, #1A1F2C 100%);
        color: #E0E0E0;
    }
    .css-1d391kg {
        background-color: #1E2329;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #0A0F1C;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2329;
        color: #FFFFFF;
        border-radius: 5px;
    }
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E2329;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2E3339;
    }
    .custom-metric-text {
        font-size: 12px;
        color: #B0B0B0;
    }
    .custom-metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #FFFFFF;
    }
    .stDataFrame {
        background-color: #1E2329;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title with emoji and gradient text
st.markdown("""
    <h1 style='text-align: center; 
               background: linear-gradient(45deg, #00FFFF, #FF69B4); 
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;
               padding: 20px;'>
        ✨ Executive Analytics Dashboard
    </h1>
""", unsafe_allow_html=True)

# Create sample data
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
data = {
    'Date': dates,
    'Sales': np.random.normal(1000, 100, len(dates)),
    'Traffic': np.random.normal(5000, 500, len(dates)),
    'Conversion': np.random.uniform(1, 5, len(dates)),
    'Revenue': np.random.normal(50000, 5000, len(dates))
}
df = pd.DataFrame(data)

# KPI Metrics Row
st.markdown("### 📊 Key Performance Metrics")
col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)

with col_metric1:
    st.markdown("""
        <div class="metric-card">
            <p class="custom-metric-text">Total Revenue</p>
            <p class="custom-metric-value">$1.2M</p>
            <p style="color: #00FF00; font-size: 12px;">↑ 12.3%</p>
        </div>
    """, unsafe_allow_html=True)

with col_metric2:
    st.markdown("""
        <div class="metric-card">
            <p class="custom-metric-text">Active Users</p>
            <p class="custom-metric-value">8.5K</p>
            <p style="color: #00FF00; font-size: 12px;">↑ 8.7%</p>
        </div>
    """, unsafe_allow_html=True)

with col_metric3:
    st.markdown("""
        <div class="metric-card">
            <p class="custom-metric-text">Conversion Rate</p>
            <p class="custom-metric-value">4.2%</p>
            <p style="color: #FF0000; font-size: 12px;">↓ 2.1%</p>
        </div>
    """, unsafe_allow_html=True)

with col_metric4:
    st.markdown("""
        <div class="metric-card">
            <p class="custom-metric-text">Avg Order Value</p>
            <p class="custom-metric-value">$142</p>
            <p style="color: #00FF00; font-size: 12px;">↑ 5.3%</p>
        </div>
    """, unsafe_allow_html=True)

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📈 Performance", "🔥 Engagement", "📊 Analysis"])

with tab1:
    col1, col2 = st.columns(2)
    
    # Enhanced Gauge
    with col1:
        st.markdown("### Performance Score")
        current_value = 75
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_value,
            delta={'reference': 60, 'position': "bottom"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': "#00FFFF"},
                'bgcolor': "#1E2329",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 50], 'color': '#FF69B4'},
                    {'range': [50, 75], 'color': '#9370DB'},
                    {'range': [75, 100], 'color': '#00FFFF'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'family': 'Arial'},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Enhanced Speedometer
    with col2:
        st.markdown("### System Load")
        speed_value = 65
        fig_speed = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=speed_value,
            delta={'reference': 50},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': "#FF69B4"},
                'bgcolor': "#1E2329",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 30], 'color': '#00FFFF'},
                    {'range': [30, 70], 'color': '#9370DB'},
                    {'range': [70, 100], 'color': '#FF69B4'}
                ]
            }
        ))
        fig_speed.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'family': 'Arial'},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_speed, use_container_width=True)

    # Enhanced Heatmap
    st.markdown("### Activity Distribution")
    hours = list(range(24))
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    heatmap_data = np.random.rand(7, 24)
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=hours,
        y=days,
        colorscale=[
            [0, '#1E2329'],
            [0.5, '#9370DB'],
            [1, '#00FFFF']
        ]
    ))
    fig_heatmap.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white', 'family': 'Arial'},
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

with tab2:
    # Enhanced Area Graph
    st.markdown("### Revenue Trends")
    fig_area = px.area(
        df, 
        x='Date', 
        y='Revenue',
        line_shape="spline"
    )
    fig_area.update_traces(
        fill='tozeroy',
        fillcolor='rgba(147, 112, 219, 0.2)',
        line_color='#00FFFF'
    )
    fig_area.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white', 'family': 'Arial'},
        xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
        yaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_area, use_container_width=True)

with tab3:
    col3, col4 = st.columns(2)

    # Enhanced Line Chart
    with col3:
        st.markdown("### Traffic Analysis")
        fig_line = px.line(
            df, 
            x='Date', 
            y='Traffic',
            line_shape="spline"
        )
        fig_line.update_traces(line_color='#FF69B4')
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'family': 'Arial'},
            xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            yaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # Enhanced Bar Chart
    with col4:
        st.markdown("### Conversion Trends")
        fig_bar = px.bar(
            df.resample('M', on='Date').mean(),
            y='Conversion'
        )
        fig_bar.update_traces(marker_color='#9370DB')
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'family': 'Arial'},
            xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            yaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Enhanced Table
st.markdown("### 📋 Performance Summary")
monthly_summary = df.resample('M', on='Date').agg({
    'Sales': ['mean', 'min', 'max'],
    'Traffic': ['mean', 'min', 'max'],
    'Conversion': 'mean',
    'Revenue': ['sum', 'mean']
}).round(2)
monthly_summary.columns = ['Avg Sales', 'Min Sales', 'Max Sales', 
                         'Avg Traffic', 'Min Traffic', 'Max Traffic', 
                         'Avg Conversion', 'Total Revenue', 'Avg Revenue']

# Format the table
st.dataframe(
    monthly_summary.style.background_gradient(
        cmap='viridis', 
        subset=['Avg Sales', 'Avg Traffic', 'Avg Conversion']
    ),
    use_container_width=True
)

# Add a footer
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        Last updated: {}
    </div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
