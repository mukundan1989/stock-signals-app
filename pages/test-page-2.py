import streamlit as st
import plotly.graph_objects as go

# Function to create a stylish gauge chart with a black background
def create_gauge(value, title, min_value=0, max_value=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': 'white', 'size': 20}},
        number={'font': {'color': 'white', 'size': 40}},
        gauge={
            'axis': {'range': [min_value, max_value], 'tickcolor': 'white', 'tickfont': {'color': 'white'}},
            'bar': {'color': 'cyan'},  # Bright color for the bar
            'bgcolor': 'black',  # Background color of the gauge
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [min_value, max_value * 0.5], 'color': 'darkgray'},
                {'range': [max_value * 0.5, max_value * 0.75], 'color': 'gray'},
                {'range': [max_value * 0.75, max_value], 'color': 'lightgray'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='black',  # Background color of the chart
        plot_bgcolor='black',   # Background color of the plot area
        margin=dict(l=50, r=50, t=50, b=50),
        height=300,
        font={'color': 'white'}  # Global font color
    )
    return fig

# Streamlit app
st.set_page_config(page_title="Elegant Gauge Dashboard", layout="wide")

# Custom CSS to set the background color of the entire app to black
st.markdown(
    """
    <style>
    .stApp {
        background-color: black;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("Elegant Gauge Dashboard")
st.markdown("---")

# Example values
value = st.slider("Select a value", 0, 100, 50, key="gauge_value")
title = "Speedometer"

# Create and display the gauge chart
gauge_chart = create_gauge(value, title)
st.plotly_chart(gauge_chart, use_container_width=True)
