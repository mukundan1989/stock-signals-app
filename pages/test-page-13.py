import streamlit as st
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(
    page_title="Stock Signal Page",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .insight-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .big-number {
        font-size: 48px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
    }
    .centered-text {
        text-align: center;
    }
    .sentiment-icon {
        font-size: 48px;
        text-align: center;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

# Create dummy data for donut charts
def create_sentiment_data():
    return pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })

# Box 1: Company Information
with st.container():
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**Company Information**")
    st.markdown("**AAPL**")
    st.markdown("Apple Inc.")
    st.markdown("**$175.34**")
    st.markdown('</div>', unsafe_allow_html=True)

# Box 2: Twitter Trends
with st.container():
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**Twitter Trend Insight**")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown('<p class="big-number">145</p>', unsafe_allow_html=True)
        st.markdown('<p class="centered-text">Keywords</p>', unsafe_allow_html=True)
    
    with col2:
        fig = px.pie(create_sentiment_data(), 
                    values='Percentage', 
                    names='Sentiment',
                    hole=0.6,  # This creates the donut effect
                    color_discrete_map={
                        'Positive': '#00ff00',
                        'Negative': '#ff0000',
                        'Neutral': '#808080'
                    })
        fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p class="sentiment-icon" style="color: green;">🐂</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Box 3: Google Trends
with st.container():
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**Google Trend Insight**")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown('<p class="big-number">15</p>', unsafe_allow_html=True)
        st.markdown('<p class="centered-text">Keywords</p>', unsafe_allow_html=True)
    
    with col2:
        fig = px.pie(create_sentiment_data(), 
                    values='Percentage', 
                    names='Sentiment',
                    hole=0.6,
                    color_discrete_map={
                        'Positive': '#00ff00',
                        'Negative': '#ff0000',
                        'Neutral': '#808080'
                    })
        fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p class="sentiment-icon" style="color: red;">🐻</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Box 4: News Analysis
with st.container():
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**News Analysis**")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown('<p class="big-number">30</p>', unsafe_allow_html=True)
        st.markdown('<p class="centered-text">Articles</p>', unsafe_allow_html=True)
    
    with col2:
        fig = px.pie(create_sentiment_data(), 
                    values='Percentage', 
                    names='Sentiment',
                    hole=0.6,
                    color_discrete_map={
                        'Positive': '#00ff00',
                        'Negative': '#ff0000',
                        'Neutral': '#808080'
                    })
        fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown('<p class="sentiment-icon" style="color: red;">🐻</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
