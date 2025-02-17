import streamlit as st

# Custom CSS for dark-themed elegant design
st.markdown(
    """
    <style>
    /* Target the main container and set a dark grey background */
    .st-emotion-cache-bm2z3a {
        background-color: #111827; /* Dark grey background */
        color: white; /* White text for the entire page */
        font-family: system-ui, -apple-system, sans-serif;
    }

    /* Container styling */
    .container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Stock symbol styling */
    .stock-symbol {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin: 0;
    }

    /* Company name styling */
    .company-name {
        color: #9CA3AF;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 30px;
    }

    /* Chart and sentiment container styling */
    .chart-container, .sentiment-container, .overall-sentiment-container, .google-trends-container {
        background: #1F2937;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Sentiment title styling */
    .sentiment-title {
        text-align: center;
        margin-bottom: 20px;
        font-size: 1.2rem;
    }

    /* Gauge and thermometer styling */
    .gauge, .thermometer {
        width: 100%;
        height: 160px;
        position: relative;
    }

    /* Tweets and articles analyzed styling */
    .tweets-analyzed, .articles-analyzed {
        text-align: center;
        margin-top: 20px;
        font-size: 1rem;
        color: #9CA3AF;
    }

    .tweets-analyzed span, .articles-analyzed span {
        font-weight: bold;
        color: #4ADE80;
    }

    /* Dual gauge container styling */
    .dual-gauge-container {
        display: flex;
        gap: 20px;
    }

    .gauge-section {
        flex: 1;
    }

    .gauge-subtitle {
        text-align: center;
        color: #9CA3AF;
        margin-bottom: 10px;
        font-size: 1rem;
    }

    /* Trends flex container styling */
    .trends-flex-container {
        display: flex;
        gap: 20px;
        margin-top: 20px;
        align-items: center;
        min-height: 200px;
    }

    /* Thermometer section styling */
    .thermometer-section {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 200px;
        position: relative;
    }

    .thermometer {
        width: 40px;
        height: 160px;
        background: #1a2234;
        border-radius: 20px;
        position: relative;
        margin: 0 auto;
        overflow: hidden;
        border: 2px solid #2D3748;
    }

    .thermometer-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        height: 70%;
        background: linear-gradient(to top, #4ADE80, #ffffff);
        border-radius: 20px;
        transition: height 0.5s ease;
    }

    /* Keyword cloud section styling */
    .keyword-cloud-section {
        flex: 2;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 10px;
        padding: 10px;
    }

    .keyword-row {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .keyword-tag {
        background: #374151;
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 16px;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }

    .keyword-tag:hover {
        transform: scale(1.1);
        background: #404b5f;
        z-index: 2;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page title and description
st.markdown("<h1 class='stock-symbol'>AAPL</h1>", unsafe_allow_html=True)
st.markdown("<div class='company-name'>Apple Inc.</div>", unsafe_allow_html=True)

# Chart container
with st.container():
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<div class='price-chart'><svg viewBox='0 0 400 200'></svg></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Sentiment container
with st.container():
    st.markdown("<div class='sentiment-container'>", unsafe_allow_html=True)
    st.markdown("<div class='sentiment-title'>Twitter Sentiment</div>", unsafe_allow_html=True)
    st.markdown("<div class='gauge'><svg viewBox='0 0 200 160'></svg></div>", unsafe_allow_html=True)
    st.markdown("<div class='tweets-analyzed'>Tweets Analyzed: <span>1,234</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Overall sentiment container
with st.container():
    st.markdown("<div class='overall-sentiment-container'>", unsafe_allow_html=True)
    st.markdown("<div class='sentiment-title'>Overall Sentiment</div>", unsafe_allow_html=True)
    st.markdown("<div class='dual-gauge-container'>", unsafe_allow_html=True)
    
    # News Sentiment Gauge
    st.markdown("<div class='gauge-section'>", unsafe_allow_html=True)
    st.markdown("<div class='gauge-subtitle'>News Sentiment</div>", unsafe_allow_html=True)
    st.markdown("<div class='gauge'><svg viewBox='0 0 200 160'></svg></div>", unsafe_allow_html=True)
    st.markdown("<div class='articles-analyzed'>News Articles Analyzed: <span>740</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Sector Sentiment Gauge
    st.markdown("<div class='gauge-section'>", unsafe_allow_html=True)
    st.markdown("<div class='gauge-subtitle'>Sector Sentiment</div>", unsafe_allow_html=True)
    st.markdown("<div class='gauge'><svg viewBox='0 0 200 160'></svg></div>", unsafe_allow_html=True)
    st.markdown("<div class='articles-analyzed'>Sector Articles Analyzed: <span>44</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Google Trends container
with st.container():
    st.markdown("<div class='google-trends-container'>", unsafe_allow_html=True)
    st.markdown("<div class='sentiment-title'>Google Trend Bullishness Indicator</div>", unsafe_allow_html=True)
    st.markdown("<div class='trends-flex-container'>", unsafe_allow_html=True)
    
    # Thermometer section
    st.markdown("<div class='thermometer-section'>", unsafe_allow_html=True)
    st.markdown("<div class='thermometer'><div class='thermometer-fill'></div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Keyword cloud section
    st.markdown("<div class='keyword-cloud-section'>", unsafe_allow_html=True)
    st.markdown("<div class='keyword-row'><div class='keyword-tag'>AAPL earnings</div><div class='keyword-tag'>iPhone sales</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='keyword-row'><div class='keyword-tag'>Apple Vision</div><div class='keyword-tag'>iOS update</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='keyword-row'><div class='keyword-tag'>Apple stock</div><div class='keyword-tag'>MacBook Pro</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='keyword-row'><div class='keyword-tag'>Apple services</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
