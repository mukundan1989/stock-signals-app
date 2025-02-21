import streamlit as st
import plotly.express as px
import pandas as pd

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
    }
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        color: #bb86fc;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 16px;
        text-align: center;
        color: #ffffff;
        margin-top: 5px;
    }
    .box-title {
        color: #bb86fc;
        text-align: center;
        font-size: 24px;
        margin-bottom: 20px;
    }
    .company-info {
        text-align: center;
        color: #ffffff;
    }
    .company-symbol {
        font-size: 32px;
        font-weight: bold;
        color: #bb86fc;
    }
    .company-price {
        font-size: 28px;
        color: #bb86fc;
        font-weight: bold;
    }
    .sentiment-icon {
        font-size: 48px;
        text-align: center;
        line-height: 200px;  /* Matches chart height */
    }
    .metric-container {
        height: 200px;  /* Fixed height to match chart */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# Function for sentiment data
def create_sentiment_data():
    return pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })

# Function to create donut chart with dark theme
def create_donut_chart():
    data = create_sentiment_data()
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
        margin=dict(t=0, b=0, l=0, r=0),
        height=200,  # Fixed height
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        legend=dict(
            font=dict(color='#ffffff'),
            bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig

# Main title
st.title("Stock Signal Page")

# Box 1: Company Information
st.markdown("""
    <div class="box-container">
        <div class="company-info">
            <h2 class="box-title">Company Information</h2>
            <div class="company-symbol">AAPL</div>
            <div style="margin: 10px 0;">Apple Inc.</div>
            <div class="company-price">$175.34</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Box 2: Twitter Trends
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Twitter Trend Insight</h2>
    </div>
""", unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-value">145</div>
                <div class="metric-label">Keywords</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.plotly_chart(create_donut_chart(), use_container_width=True)

    with col3:
        st.markdown('<div class="sentiment-icon">🐂</div>', unsafe_allow_html=True)

# Box 3: Google Trends (same structure as Box 2)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">Google Trend Insight</h2>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">15</div>
            <div class="metric-label">Keywords</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=True)

with col3:
    st.markdown('<div class="sentiment-icon">🐻</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Box 4: News Analysis (same structure as Box 2)
st.markdown("""
    <div class="box-container">
        <h2 class="box-title">News Analysis</h2>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("""
        <div class="metric-container">
            <div class="metric-value">30</div>
            <div class="metric-label">Articles</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.plotly_chart(create_donut_chart(), use_container_width=True)

with col3:
    st.markdown('<div class="sentiment-icon">🐻</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
