import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import seaborn as sns

# Set page config
st.set_page_config(layout="wide", page_title="Dark Dashboard")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .css-1d391kg {
        background-color: #1E2329;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #0E1117;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2329;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Dark Analytics Dashboard")

# Create sample data
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
data = {
    'Date': dates,
    'Sales': np.random.normal(1000, 100, len(dates)),
    'Traffic': np.random.normal(5000, 500, len(dates)),
    'Conversion': np.random.uniform(1, 5, len(dates))
}
df = pd.DataFrame(data)

# Layout with columns
col1, col2 = st.columns(2)

# 1. Gauge Chart
with col1:
    st.subheader("Performance Gauge")
    current_value = 75
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#00FF00"},
            'bgcolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#FF0000'},
                {'range': [50, 75], 'color': '#FFFF00'},
                {'range': [75, 100], 'color': '#00FF00'}
            ]
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=250
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# 2. Speedometer
with col2:
    st.subheader("Speed Indicator")
    speed_value = 65
    fig_speed = go.Figure(go.Indicator(
        mode="gauge+number",
        value=speed_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#00FFFF"},
            'bgcolor': "gray",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 30], 'color': '#00FFFF'},
                {'range': [30, 70], 'color': '#00CCCC'},
                {'range': [70, 100], 'color': '#009999'}
            ]
        }
    ))
    fig_speed.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=250
    )
    st.plotly_chart(fig_speed, use_container_width=True)

# 3. Heatmap
st.subheader("Activity Heatmap")
# Generate sample heatmap data
heatmap_data = np.random.rand(10, 10)
fig_heatmap = px.imshow(
    heatmap_data,
    color_continuous_scale='Viridis'
)
fig_heatmap.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': 'white'}
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# 4. Area Graph
st.subheader("Sales Trend")
fig_area = px.area(
    df, 
    x='Date', 
    y='Sales',
    line_shape="spline"
)
fig_area.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': 'white'},
    xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
    yaxis={'gridcolor': 'rgba(255,255,255,0.1)'}
)
st.plotly_chart(fig_area, use_container_width=True)

# 5. Multiple Graphs
col3, col4 = st.columns(2)

with col3:
    st.subheader("Traffic Analysis")
    fig_line = px.line(
        df, 
        x='Date', 
        y='Traffic',
        line_shape="spline"
    )
    fig_line.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
        yaxis={'gridcolor': 'rgba(255,255,255,0.1)'}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with col4:
    st.subheader("Conversion Rate")
    fig_bar = px.bar(
        df.resample('M', on='Date').mean(),
        y='Conversion'
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
        yaxis={'gridcolor': 'rgba(255,255,255,0.1)'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 6. Table
st.subheader("Monthly Summary")
monthly_summary = df.resample('M', on='Date').agg({
    'Sales': ['mean', 'min', 'max'],
    'Traffic': ['mean', 'min', 'max'],
    'Conversion': 'mean'
}).round(2)
monthly_summary.columns = ['Avg Sales', 'Min Sales', 'Max Sales', 
                         'Avg Traffic', 'Min Traffic', 'Max Traffic', 
                         'Avg Conversion']
st.dataframe(monthly_summary, use_container_width=True)
