import streamlit as st
import plotly.express as px
import pandas as pd
import uuid  # For unique chart IDs

# Page config
st.set_page_config(page_title="Stock Signal Page", layout="wide")

# Custom CSS for dark theme styling
st.markdown("""
    <style>
    .box-container {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border: 1px solid #333333;
        text-align: center;
    }
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        color: #bb86fc;
    }
    .metric-label {
        font-size: 16px;
        text-align: center;
        color: #ffffff;
        margin-top: 5px;
    }
    .box-title {
        color: #bb86fc;
        font-size: 24px;
        margin-bottom: 10px;
    }
    .sentiment-icon {
        font-size: 48px;
        text-align: center;
    }
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Function to create a unique donut chart without displaying the unique ID
def create_donut_chart():
    _ = str(uuid.uuid4())  # Generate a unique ID but don't display it
    data = pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })
    fig = px.pie(data, 
                 values='Percentage', 
                 names='Sentiment',
                 hole=0.6,
                 color_discrete_map={
                     'Positive': '#00ff00',
                     'Negative': '#ff0000',
                     'Neutral': '#808080'
                 })
    fig.update_layout(
        showlegend=True,
        margin=dict(t=30, b=10, l=10, r=10),  # Adjust margins
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        legend=dict(
            font=dict(color='#ffffff'),
            bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig  # Ensure every call returns a fresh figure instance

# Main title
st.title("Stock Signal Page")

# Box 1: Company Information (Title Only)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Company Information</h2>
    </div>
""", unsafe_allow_html=True)

# Company Info Content (Outside the Box)
st.markdown("""
    <div style="text-align: center; color: white;">
        <div class="company-symbol" style="font-size: 32px; font-weight: bold; color: #bb86fc;">AAPL</div>
        <div style="margin: 10px 0;">Apple Inc.</div>
        <div class="company-price" style="font-size: 28px; color: #bb86fc; font-weight: bold;">$175.34</div>
    </div>
""", unsafe_allow_html=True)

# Box 2: Twitter Trends (Title Only)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Twitter Trend Insight</h2>
    </div>
""", unsafe_allow_html=True)

# Twitter Trend Content (Outside the Box)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">145</div>
            <div class="metric-label">Keywords</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=False)  # Unique instance

with col3:
    st.markdown('<div class="sentiment-icon">🐂</div>', unsafe_allow_html=True)

# Box 3: News Analysis (Title Only)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">News Analysis</h2>
    </div>
""", unsafe_allow_html=True)

# News Analysis Content (Outside the Box)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">30</div>
            <div class="metric-label">Articles</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=False)  # Unique instance

with col3:
    st.markdown('<div class="sentiment-icon">🐻</div>', unsafe_allow_html=True)

# Box 4: News Insight (Title Only)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">News Insight</h2>
    </div>
""", unsafe_allow_html=True)

# News Insight Content (Outside the Box)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">145</div>
            <div class="metric-label">Keywords</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=False)  # Unique instance

with col3:
    st.markdown('<div class="sentiment-icon">🐂</div>', unsafe_allow_html=True)
