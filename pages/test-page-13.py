import streamlit as st
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(page_title="Stock Signal Page", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] > div:first-of-type {
        white-space: pre;
    }
    .box-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 16px;
        text-align: center;
        color: #666;
    }
    .center-align {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Function for sentiment data
def create_sentiment_data():
    return pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Percentage': [45, 30, 25]
    })

# Function to create donut chart
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
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# Main title
st.title("Stock Signal Page")

# Box 1: Company Information
with st.container():
    st.markdown("""
        <div class="box-container">
            <div style="text-align: center;">
                <h2>Company Information</h2>
                <h3>AAPL</h3>
                <p>Apple Inc.</p>
                <h3>$175.34</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Box 2: Twitter Trends
with st.container():
    st.markdown('<div class="box-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Twitter Trend Insight</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    
    with cols[0]:
        st.markdown('<div class="metric-value">145</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Keywords</div>', unsafe_allow_html=True)
    
    with cols[1]:
        st.plotly_chart(create_donut_chart(), use_container_width=True)
    
    with cols[2]:
        st.markdown('<div class="center-align" style="font-size: 48px; color: green;">🐂</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Box 3: Google Trends
with st.container():
    st.markdown('<div class="box-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Google Trend Insight</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    
    with cols[0]:
        st.markdown('<div class="metric-value">15</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Keywords</div>', unsafe_allow_html=True)
    
    with cols[1]:
        st.plotly_chart(create_donut_chart(), use_container_width=True)
    
    with cols[2]:
        st.markdown('<div class="center-align" style="font-size: 48px; color: red;">🐻</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Box 4: News Analysis
with st.container():
    st.markdown('<div class="box-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>News Analysis</h2>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    
    with cols[0]:
        st.markdown('<div class="metric-value">30</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Articles</div>', unsafe_allow_html=True)
    
    with cols[1]:
        st.plotly_chart(create_donut_chart(), use_container_width=True)
    
    with cols[2]:
        st.markdown('<div class="center-align" style="font-size: 48px; color: red;">🐻</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
