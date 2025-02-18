import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Page config
st.set_page_config(layout="wide", page_title="Next-Gen Analytics", page_icon="🌌")

# Custom CSS for ultra-modern dark theme
st.markdown("""
    <style>
    /* Radical dark theme with neon accents */
    .stApp {
        background: #0D1117;
        background-image: 
            radial-gradient(circle at 50% 0%, #1A1F29 0%, transparent 70%),
            radial-gradient(circle at 0% 100%, #1F1C36 0%, transparent 70%);
    }
    
    /* Neon card effect */
    .neon-card {
        background: rgba(13, 17, 23, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 
            0 0 10px rgba(99, 102, 241, 0.1),
            inset 0 0 20px rgba(99, 102, 241, 0.05);
        transition: all 0.3s ease;
    }
    
    .neon-card:hover {
        box-shadow: 
            0 0 15px rgba(99, 102, 241, 0.2),
            inset 0 0 30px rgba(99, 102, 241, 0.1);
    }
    
    /* Cyberpunk-inspired text */
    .cyber-text {
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
    }
    
    /* Title animation */
    @keyframes titleGlow {
        0% { text-shadow: 0 0 10px rgba(99, 102, 241, 0.5); }
        50% { text-shadow: 0 0 20px rgba(99, 102, 241, 0.8); }
        100% { text-shadow: 0 0 10px rgba(99, 102, 241, 0.5); }
    }
    
    .title {
        color: #E2E8F0;
        font-size: 2.5rem;
        text-align: center;
        animation: titleGlow 3s infinite;
        margin-bottom: 2rem;
    }
    
    /* Custom metric styles */
    .metric-container {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(13, 17, 23, 0.7));
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(99, 102, 241, 0.1);
    }
    
    /* Graph container */
    .graph-container {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 12px;
        background: rgba(13, 17, 23, 0.7);
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="title">🌌 Neural Command Center</h1>', unsafe_allow_html=True)

# Generate complex sample data
np.random.seed(42)

# Time series data
dates = pd.date_range(start='2024-01-01', periods=1000, freq='H')
base_trend = np.linspace(0, 100, 1000)
noise = np.random.normal(0, 10, 1000)
seasonal = 20 * np.sin(np.linspace(0, 10*np.pi, 1000))

data = pd.DataFrame({
    'timestamp': dates,
    'neural_load': (base_trend + noise + seasonal).clip(0, 100),
    'quantum_stability': np.random.normal(75, 15, 1000).clip(0, 100),
    'energy_flux': np.abs(np.random.normal(0, 1, 1000) * base_trend),
    'sync_rate': np.random.normal(95, 5, 1000).clip(0, 100),
    'dimensional_variance': np.random.exponential(5, 1000),
    'entropy_level': np.random.gamma(2, 2, 1000)
})

# Create unique cosmic-themed gauges
def create_cosmic_gauge(value, title, max_val=100):
    fig = go.Figure()
    
    # Add main gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': '#E2E8F0', 'size': 24}},
        gauge={
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#6366F1"},
            'bar': {'color': "#6366F1"},
            'bgcolor': "rgba(13, 17, 23, 0.7)",
            'borderwidth': 2,
            'bordercolor': "#6366F1",
            'steps': [
                {'range': [0, max_val/3], 'color': 'rgba(99, 102, 241, 0.1)'},
                {'range': [max_val/3, max_val*2/3], 'color': 'rgba(99, 102, 241, 0.2)'},
                {'range': [max_val*2/3, max_val], 'color': 'rgba(99, 102, 241, 0.3)'}
            ]
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#E2E8F0"},
        height=200,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    return fig

# Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(create_cosmic_gauge(
        data['neural_load'].iloc[-1],
        "Neural Load"
    ), use_container_width=True)

with col2:
    st.plotly_chart(create_cosmic_gauge(
        data['quantum_stability'].iloc[-1],
        "Quantum Stability"
    ), use_container_width=True)

with col3:
    st.plotly_chart(create_cosmic_gauge(
        data['sync_rate'].iloc[-1],
        "Sync Rate"
    ), use_container_width=True)

# Create unique 3D scatter plot
st.markdown('<div class="neon-card">', unsafe_allow_html=True)
fig_3d = go.Figure(data=[go.Scatter3d(
    x=data['neural_load'].values[-100:],
    y=data['quantum_stability'].values[-100:],
    z=data['energy_flux'].values[-100:],
    mode='markers',
    marker=dict(
        size=8,
        color=data['sync_rate'].values[-100:],
        colorscale='Plasma',
        opacity=0.8
    )
)])

fig_3d.update_layout(
    title="Quantum State Visualization",
    scene=dict(
        xaxis_title="Neural Load",
        yaxis_title="Quantum Stability",
        zaxis_title="Energy Flux",
        bgcolor='rgba(13, 17, 23, 0.7)'
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "#E2E8F0"},
    height=500
)
st.plotly_chart(fig_3d, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Create unique radar chart
st.markdown('<div class="neon-card">', unsafe_allow_html=True)
categories = ['Neural', 'Quantum', 'Energy', 'Sync', 'Entropy']
values = [
    data['neural_load'].iloc[-1],
    data['quantum_stability'].iloc[-1],
    data['energy_flux'].iloc[-1] / 100,
    data['sync_rate'].iloc[-1],
    data['entropy_level'].iloc[-1] * 10
]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=values,
    theta=categories,
    fill='toself',
    fillcolor='rgba(99, 102, 241, 0.2)',
    line=dict(color='#6366F1', width=2)
))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
            gridcolor='rgba(99, 102, 241, 0.1)'
        ),
        angularaxis=dict(
            gridcolor='rgba(99, 102, 241, 0.1)'
        ),
        bgcolor='rgba(13, 17, 23, 0.7)'
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "#E2E8F0"},
    height=400,
    title="System Harmony Analysis"
)
st.plotly_chart(fig_radar, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Create unique spiral chart
theta = np.linspace(0, 8*np.pi, 1000)
radius = np.exp(0.1 * theta)

fig_spiral = go.Figure()
fig_spiral.add_trace(go.Scatterpolar(
    r=radius,
    theta=theta,
    mode='lines',
    line=dict(
        color=data['quantum_stability'].values,
        colorscale='Plasma',
        width=2
    ),
    name='Quantum Spiral'
))

fig_spiral.update_layout(
    title="Quantum Stability Spiral",
    polar=dict(
        radialaxis=dict(
            visible=False,
            range=[0, max(radius)]
        ),
        bgcolor='rgba(13, 17, 23, 0.7)'
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "#E2E8F0"},
    showlegend=False,
    height=400
)
st.plotly_chart(fig_spiral, use_container_width=True)

# Create unique bubble chart
fig_bubble = px.scatter(
    data.iloc[-100:],
    x='neural_load',
    y='quantum_stability',
    size='energy_flux',
    color='sync_rate',
    color_continuous_scale='Plasma',
    title="Neural-Quantum Relationship"
)

fig_bubble.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(13, 17, 23, 0.7)',
    font={'color': "#E2E8F0"},
    height=400
)
st.plotly_chart(fig_bubble, use_container_width=True)

# Stats cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
        <div class="metric-container">
            <h3 style="color: #6366F1; font-size: 14px;">DIMENSIONAL VARIANCE</h3>
            <p style="color: #E2E8F0; font-size: 24px; margin: 0;">{:.2f}</p>
            <p style="color: #6366F1; font-size: 12px;">σ: {:.2f}</p>
        </div>
    """.format(data['dimensional_variance'].mean(), data['dimensional_variance'].std()), unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="metric-container">
            <h3 style="color: #6366F1; font-size: 14px;">ENTROPY LEVEL</h3>
            <p style="color: #E2E8F0; font-size: 24px; margin: 0;">{:.2f}</p>
            <p style="color: #6366F1; font-size: 12px;">Peak: {:.2f}</p>
        </div>
    """.format(data['entropy_level'].mean(), data['entropy_level'].max()), unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="metric-container">
            <h3 style="color: #6366F1; font-size: 14px;">QUANTUM COHERENCE</h3>
            <p style="color: #E2E8F0; font-size: 24px; margin: 0;">98.2%</p>
            <p style="color: #6366F1; font-size: 12px;">Optimal Range</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="metric-container">
            <h3 style="color: #6366F1; font-size: 14px;">SYSTEM INTEGRITY</h3>
            <p style="color: #E2E8F0; font-size: 24px; margin: 0;">99.9%</p>
            <p style="color: #6366F1; font-size: 12px;">All Systems Nominal</p>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
    <div style='text-align: center; color: #6366F1; padding: 20px; font-size: 12px;'>
        ⚡ System Online | Quantum Core Stable | Last Update: {}
    </div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
