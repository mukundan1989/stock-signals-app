import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Dashboard Template", layout="wide")
st.title("Dashboard Visualization Template")

# Generate sample data
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
data = {
    'date': dates,
    'value1': np.random.uniform(0, 100, len(dates)),
    'value2': np.random.uniform(30, 80, len(dates)),
    'value3': np.random.uniform(20, 90, len(dates)),
    'category': np.random.choice(['A', 'B', 'C', 'D'], len(dates))
}
df = pd.DataFrame(data)

# Create layout
st.header("1. Speedometers")
col1, col2, col3 = st.columns(3)

# Speedometer 1 - Basic
with col1:
    st.subheader("Basic Speedometer")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': "Speed"},
        gauge={'axis': {'range': [None, 100]}}
    ))
    st.plotly_chart(fig, use_container_width=True)

# Speedometer 2 - With color ranges
with col2:
    st.subheader("Color Range Speedometer")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': "Performance"},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Speedometer 3 - Custom design
with col3:
    st.subheader("Custom Speedometer")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={'reference': 50},
        title={'text': "Progress"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Gauges
st.header("2. Gauges")
col1, col2, col3 = st.columns(3)

# Gauge 1 - Simple
with col1:
    st.subheader("Simple Gauge")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={'axis': {'range': [None, 100]}}
    ))
    st.plotly_chart(fig, use_container_width=True)

# Gauge 2 - Bullet
with col2:
    st.subheader("Bullet Gauge")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="number+gauge+delta",
        gauge={'shape': "bullet",
               'axis': {'range': [None, 100]},
               'threshold': {
                   'line': {'color': "red", 'width': 2},
                   'thickness': 0.75,
                   'value': 80}},
        value=value,
        delta={'reference': 50}
    ))
    st.plotly_chart(fig, use_container_width=True)

# Gauge 3 - Angular
with col3:
    st.subheader("Angular Gauge")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100]},
            'shape': "angular",
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Meters
st.header("3. Meter Measurements")
col1, col2, col3 = st.columns(3)

# Meter 1 - Vertical bar
with col1:
    st.subheader("Vertical Bar Meter")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'shape': "bullet",
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Meter 2 - Progress bar
with col2:
    st.subheader("Progress Meter")
    value = np.random.randint(0, 100)
    st.progress(value/100)
    st.write(f"Progress: {value}%")

# Meter 3 - Custom meter
with col3:
    st.subheader("Custom Meter")
    value = np.random.randint(0, 100)
    fig = go.Figure(go.Indicator(
        mode="number+delta+gauge",
        value=value,
        delta={'reference': 50},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'shape': "bullet",
            'axis': {'range': [None, 100]},
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Heat Maps
st.header("4. Heat Maps")
col1, col2 = st.columns(2)

# Heatmap 1 - Basic
with col1:
    st.subheader("Basic Heatmap")
    data_2d = np.random.rand(10, 10)
    fig = px.imshow(data_2d, color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

# Heatmap 2 - Annotated
with col2:
    st.subheader("Annotated Heatmap")
    data_2d = np.random.randint(0, 100, size=(8, 8))
    fig = px.imshow(data_2d,
                    labels=dict(x="X Axis", y="Y Axis", color="Value"),
                    text=data_2d,
                    aspect="auto")
    st.plotly_chart(fig, use_container_width=True)

# Heatmap 3 - Correlation
st.subheader("Correlation Heatmap")
correlation = df[['value1', 'value2', 'value3']].corr()
fig = px.imshow(correlation,
                labels=dict(x="Features", y="Features", color="Correlation"),
                color_continuous_scale='RdBu_r')
st.plotly_chart(fig, use_container_width=True)

# Charts
st.header("5. Various Charts")

# Chart 1 - Line
st.subheader("Line Chart")
fig = px.line(df, x='date', y=['value1', 'value2', 'value3'],
              title='Multi-line Chart')
st.plotly_chart(fig, use_container_width=True)

# Chart 2 - Bar
st.subheader("Bar Chart")
monthly_avg = df.groupby(df['date'].dt.month)[['value1', 'value2']].mean()
fig = px.bar(monthly_avg, barmode='group',
             title='Monthly Average Values')
st.plotly_chart(fig, use_container_width=True)

# Chart 3 - Scatter
st.subheader("Scatter Plot")
fig = px.scatter(df, x='value1', y='value2', color='category',
                 title='Scatter Plot with Categories')
st.plotly_chart(fig, use_container_width=True)

# Chart 4 - Area
st.subheader("Area Chart")
fig = px.area(df, x='date', y=['value1', 'value2'],
              title='Stacked Area Chart')
st.plotly_chart(fig, use_container_width=True)

# Chart 5 - Pie
st.subheader("Pie Chart")
category_counts = df['category'].value_counts()
fig = px.pie(values=category_counts.values,
             names=category_counts.index,
             title='Distribution by Category')
st.plotly_chart(fig, use_container_width=True)
