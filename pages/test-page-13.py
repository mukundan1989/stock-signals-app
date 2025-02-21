import streamlit as st
import plotly.express as px
import pandas as pd
from PIL import Image

# Page config
st.set_page_config(
    page_title="Stock Signal Page",
    layout="wide"
)

# Title
st.title("Stock Signal Page")

# Custom CSS
st.markdown("""
    <style>
    .big-number {
        font-size: 48px;
        font-weight: bold;
        color: #1E88E5;
    }
    .icon {
        font-size: 48px;
        margin-left: 20px;
    }
    .box-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .insight-box {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Box 1: Company Information
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
with st.container():
    st.markdown("## Company Information")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.markdown("### AAPL")
        st.markdown("Apple Inc.")
        st.markdown("### $175.34")
st.markdown('</div>', unsafe_allow_html=True)

# Create dummy data for pie charts
def create_sentiment_data():
    return pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })

# Box 2: Twitter Trends
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
with st.container():
    st.markdown('<p class="box-title">Twitter Trend Insight</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col1:
        st.markdown('<p class="big-number">145</p>', unsafe_allow_html=True)
        st.markdown("Keywords")
    
    with col2:
        fig = px.pie(create_sentiment_data(), values='Percentage', names='Sentiment',
                    color_discrete_map={'Positive':'#00ff00',
                                      'Negative':'#ff0000',
                                      'Neutral':'#808080'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p style="color: green; font-size: 48px;">🐂</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Box 3: Google Trends
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
with st.container():
    st.markdown('<p class="box-title">Google Trend Insight</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col1:
        st.markdown('<p class="big-number">15</p>', unsafe_allow_html=True)
        st.markdown("Keywords")
    
    with col2:
        fig = px.pie(create_sentiment_data(), values='Percentage', names='Sentiment',
                    color_discrete_map={'Positive':'#00ff00',
                                      'Negative':'#ff0000',
                                      'Neutral':'#808080'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p style="color: red; font-size: 48px;">🐻</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Box 4: News Analysis
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
with st.container():
    st.markdown('<p class="box-title">News Analysis</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col1:
        st.markdown('<p class="big-number">30</p>', unsafe_allow_html=True)
        st.markdown("Articles")
    
    with col2:
        fig = px.pie(create_sentiment_data(), values='Percentage', names='Sentiment',
                    color_discrete_map={'Positive':'#00ff00',
                                      'Negative':'#ff0000',
                                      'Neutral':'#808080'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p style="color: red; font-size: 48px;">🐻</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
