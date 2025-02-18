import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Enterprise Analytics", page_icon="💎")

# Modern Enterprise CSS
st.markdown("""
    <style>
    /* Animated Gradient Background */
    .stApp {
        background: linear-gradient(
            -45deg, 
            #0f1722,
            #162032,
            #1c2c44,
            #23374d
        );
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Frosted Glass Effect */
    .glass-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }
    
    /* Modern Metric Card */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    }
    
    /* Luxury Typography */
    .premium-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(45deg, #fff, #6E8EFB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        text-align: center;
        letter-spacing: -1px;
        margin-bottom: 2rem;
    }
    
    .section-title {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        letter-spacing: 0.5px;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 10px 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Modern Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }
    
    /* Chart Container */
    .chart-container {
        padding: 15px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Dashboard Title
st.markdown('<h1 class="premium-title">💎 Enterprise Command Center</h1>', unsafe_allow_html=True)

# Generate sample data
def generate_sample_data():
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='H')
    df = pd.DataFrame({
        'timestamp': dates,
        'revenue': np.random.normal(5000, 1000, len(dates)) * (1 + np.sin(np.arange(len(dates)) * 0.1) * 0.2),
        'users': np.random.normal(1000, 100, len(dates)) * (1 + np.cos(np.arange(len(dates)) * 0.1) * 0.3),
        'system_load': np.random.normal(65, 15, len(dates)),
        'temperature': np.random.normal(72, 5, len(dates)),
        'network_speed': np.random.normal(95, 10, len(dates)),
        'error_rate': np.random.normal(2, 1, len(dates)).clip(0, 100),
        'satisfaction': np.random.normal(85, 5, len(dates)).clip(0, 100),
        'uptime': np.random.normal(99.9, 0.1, len(dates)).clip(0, 100)
    })
    return df

df = generate_sample_data()

# Key Performance Metrics Row
col1, col2, col3, col4 = st.columns(4)

# Function to create a modern gauge
def create_gauge(value, title, min_val=0, max_val=100, color_scheme=['#FF6B6B', '#4ECDC4', '#45B7D1']):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={'reference': value-5},
        title={'text': title, 'font': {'size': 24, 'color': 'white'}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color_scheme[2]},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'borderwidth': 2,
            'bordercolor': "rgba(255, 255, 255, 0.2)",
            'steps': [
                {'range': [min_val, max_val*0.5], 'color': color_scheme[0]},
                {'range': [max_val*0.5, max_val*0.8], 'color': color_scheme[1]},
                {'range': [max_val*0.8, max_val], 'color': color_scheme[2]}
            ]
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white", 'family': "Arial"},
        height=200,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig

with col1:
    st.plotly_chart(create_gauge(df['system_load'].iloc[-1], "System Load"), use_container_width=True)

with col2:
    st.plotly_chart(create_gauge(df['temperature'].iloc[-1], "Temperature", 0, 100, 
                                ['#45B7D1', '#4ECDC4', '#FF6B6B']), use_container_width=True)

with col3:
    st.plotly_chart(create_gauge(df['network_speed'].iloc[-1], "Network Speed"), use_container_width=True)

with col4:
    st.plotly_chart(create_gauge(df['satisfaction'].iloc[-1], "User Satisfaction"), use_container_width=True)

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["📊 Performance", "🌡️ System Health", "📈 Analytics"])

with tab1:
    # Performance Metrics
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # Revenue Area Chart
    fig_revenue = px.area(df.resample('D', on='timestamp').mean(), 
                         y='revenue', 
                         title='Daily Revenue Trend')
    fig_revenue.update_traces(
        fill='tozeroy',
        fillcolor='rgba(78, 205, 196, 0.2)',
        line=dict(color='#4ECDC4', width=2)
    )
    fig_revenue.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # User Activity Heatmap
    user_activity = df.pivot_table(
        index=df.timestamp.dt.hour,
        columns=df.timestamp.dt.day_name(),
        values='users',
        aggfunc='mean'
    )
    
    fig_heatmap = px.imshow(
        user_activity,
        color_continuous_scale=[[0, '#1A2332'],
                              [0.5, '#4ECDC4'],
                              [1, '#45B7D1']],
        title='User Activity Heatmap'
    )
    fig_heatmap.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # System Health Metrics
    col5, col6 = st.columns(2)
    
    with col5:
        # Error Rate Trend
        fig_errors = go.Figure()
        fig_errors.add_trace(go.Scatter(
            y=df['error_rate'].rolling(24).mean(),
            line=dict(color='#FF6B6B', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.1)',
            name='Error Rate'
        ))
        fig_errors.update_layout(
            title='Error Rate Trend (24h Rolling Average)',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_errors, use_container_width=True)
    
    with col6:
        # System Temperature Distribution
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Histogram(
            x=df['temperature'],
            nbinsx=30,
            marker_color='#45B7D1'
        ))
        fig_temp.update_layout(
            title='Temperature Distribution',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    # Uptime Timeline
    fig_uptime = go.Figure()
    fig_uptime.add_trace(go.Scatter(
        y=df['uptime'].rolling(12).mean(),
        line=dict(color='#4ECDC4', width=2),
        name='Uptime %'
    ))
    fig_uptime.update_layout(
        title='System Uptime Timeline (12h Rolling Average)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_uptime, use_container_width=True)

with tab3:
    # Analytics Dashboard
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # Metrics Summary
    cols = st.columns(3)
    metrics = [
        {"label": "Average Response Time", "value": "235ms", "delta": "-12ms"},
        {"label": "Active Sessions", "value": "1,234", "delta": "+5.2%"},
        {"label": "Error Rate", "value": "0.12%", "delta": "-0.05%"}
    ]
    
    for col, metric in zip(cols, metrics):
        col.markdown(f"""
            <div class="metric-card">
                <h3 style="color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-bottom: 8px;">
                    {metric['label']}
                </h3>
                <p style="color: white; font-size: 1.8rem; margin: 0;">
                    {metric['value']}
                </p>
                <p style="color: {'#4ECDC4' if '-' in metric['delta'] else '#FF6B6B'}; font-size: 0.9rem;">
                    {metric['delta']}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Create a candlestick chart for system metrics
    fig_candlestick = go.Figure(data=[go.Candlestick(
        x=df['timestamp'][::24],
        open=df['system_load'][::24],
        high=df['system_load'][::24].rolling(24).max(),
        low=df['system_load'][::24].rolling(24).min(),
        close=df['system_load'][::24].shift(-23)
    )])
    fig_candlestick.update_layout(
        title='System Load Analysis (Daily)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_candlestick, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with system status
st.markdown(f"""
    <div style='text-align: center; color: rgba(255,255,255,0.5); padding: 20px; font-size: 0.8rem;'>
        🟢 All Systems Operational | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
