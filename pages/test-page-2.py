import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Custom CSS for dark theme and styling
st.markdown(
    """
    <style>
    body {
        background: #111827;
        color: white;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .container {
        max-width: 400px;
        margin: 0 auto;
    }
    .pretty-box {
        background: #1F2937;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .gauge-container {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .gauge-svg {
        width: 200px;
        height: 160px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page layout
st.markdown("<h1 class='stock-symbol'>AAPL</h1>", unsafe_allow_html=True)
st.markdown("<div class='company-name'>Apple Inc.</div>", unsafe_allow_html=True)

# Sample Price Chart
def plot_price_chart():
    fig, ax = plt.subplots()
    x = np.arange(5)
    y = np.random.randint(140, 170, size=5)
    ax.plot(x, y, marker='o', linestyle='-', color='#4ADE80')
    ax.set_xticks(x)
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
    ax.set_ylabel("Price ($)")
    st.pyplot(fig)

st.markdown("<div class='pretty-box'>Price Chart</div>", unsafe_allow_html=True)
plot_price_chart()

# Speedometer Gauge SVG
def render_gauge(rotation=0):
    svg = f"""
    <svg viewBox="0 0 200 160" class='gauge-svg'>
        <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y1="0%">
                <stop offset="0%" stop-color="#ef4444" />
                <stop offset="50%" stop-color="#ffffff" />
                <stop offset="100%" stop-color="#4ade80" />
            </linearGradient>
        </defs>
        <path d="M20 140 A80 80 0 0 1 180 140" fill="none" stroke="#1a2234" stroke-width="12" stroke-linecap="round"/>
        <path d="M20 140 A80 80 0 0 1 180 140" fill="none" stroke="url(#gradient)" stroke-width="10" stroke-linecap="round"/>
        <g transform="translate(100, 140)">
            <line x1="0" y1="0" x2="0" y2="-70" stroke="white" stroke-width="3" transform="rotate({rotation})"/>
            <circle cx="0" cy="0" r="6" fill="white"/>
        </g>
    </svg>
    """
    return svg

st.markdown("<div class='pretty-box'>Twitter Sentiment Gauge</div>", unsafe_allow_html=True)
st.markdown(render_gauge(40), unsafe_allow_html=True)

st.markdown("<div class='pretty-box'>News Sentiment Gauge</div>", unsafe_allow_html=True)
st.markdown(render_gauge(60), unsafe_allow_html=True)

st.markdown("<div class='pretty-box'>Sector Sentiment Gauge</div>", unsafe_allow_html=True)
st.markdown(render_gauge(20), unsafe_allow_html=True)

# Google Trends Thermometer
def render_thermometer(fill_percentage=70):
    height = fill_percentage * 1.6
    svg = f"""
    <div style='display: flex; justify-content: center;'>
        <div style='width: 40px; height: 160px; background: #1a2234; border-radius: 20px; overflow: hidden; border: 2px solid #2D3748;'>
            <div style='position: absolute; bottom: 0; width: 100%; height: {height}px; background: linear-gradient(to top, #4ADE80, #ffffff); border-radius: 20px;'></div>
        </div>
    </div>
    """
    return svg

st.markdown("<div class='pretty-box'>Google Trend Bullishness Indicator</div>", unsafe_allow_html=True)
st.markdown(render_thermometer(70), unsafe_allow_html=True)

# Keyword Cloud
keywords = ["AAPL earnings", "iPhone sales", "Apple Vision", "iOS update", "Apple stock", "MacBook Pro", "Apple services"]
keyword_html = "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;'>"
for keyword in keywords:
    keyword_html += f"<div style='background: #374151; color: #ffffff; padding: 8px 16px; border-radius: 16px; font-size: 14px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); transition: all 0.2s ease;'>{keyword}</div>"
keyword_html += "</div>"

st.markdown("<div class='pretty-box'>Keyword Cloud</div>", unsafe_allow_html=True)
st.markdown(keyword_html, unsafe_allow_html=True)
