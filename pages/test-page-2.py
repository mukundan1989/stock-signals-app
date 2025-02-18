import streamlit as st
import plotly.graph_objects as go

# Function to create a gauge chart
def create_gauge(value, title, min_value=0, max_value=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_value, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.75], 'color': "gray"},
                {'range': [max_value * 0.75, max_value], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(
        margin=dict(l=50, r=50, t=50, b=50),
        height=300
    )
    return fig

# Streamlit app
st.title("Stunning Gauge Chart Dashboard")

# Example values
value = st.slider("Select a value", 0, 100, 50)
title = "Speedometer"

# Create and display the gauge chart
gauge_chart = create_gauge(value, title)
st.plotly_chart(gauge_chart, use_container_width=True)
