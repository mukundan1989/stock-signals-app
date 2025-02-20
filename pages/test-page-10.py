import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Page config
st.set_page_config(layout="wide", page_title="Pie Charts Dashboard")

# Generate sample data
@st.cache_data
def generate_data():
    # Sales data
    categories = ['Electronics', 'Clothing', 'Food', 'Books', 'Sports', 'Home', 'Beauty']
    regions = ['North', 'South', 'East', 'West']
    channels = ['Online', 'Retail', 'Wholesale', 'Mobile App']
    payment_methods = ['Credit Card', 'Cash', 'Digital Wallet', 'Bank Transfer']
    
    df = pd.DataFrame({
        'category': categories,
        'sales': np.random.randint(1000, 5000, len(categories)),
        'growth': np.random.uniform(0.05, 0.25, len(categories)),
        'profit_margin': np.random.uniform(0.15, 0.35, len(categories))
    })
    
    regional_data = pd.DataFrame({
        'region': regions,
        'revenue': np.random.randint(10000, 50000, len(regions)),
        'customers': np.random.randint(1000, 5000, len(regions))
    })
    
    channel_data = pd.DataFrame({
        'channel': channels,
        'sales': np.random.randint(5000, 20000, len(channels)),
        'conversion_rate': np.random.uniform(0.02, 0.15, len(channels))
    })
    
    payment_data = pd.DataFrame({
        'method': payment_methods,
        'transactions': np.random.randint(1000, 8000, len(payment_methods)),
        'average_value': np.random.uniform(50, 200, len(payment_methods))
    })
    
    return df, regional_data, channel_data, payment_data

df, regional_data, channel_data, payment_data = generate_data()

# Title
st.title("🥧 Advanced Pie Charts Gallery")
st.markdown("### Interactive Pie Chart Visualizations")

# Layout
col1, col2 = st.columns(2)

# 1. Basic Pie Chart with Custom Colors
with col1:
    st.subheader("Sales Distribution by Category")
    fig1 = px.pie(df, values='sales', names='category',
                  color_discrete_sequence=px.colors.qualitative.Set3)
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig1, use_container_width=True)

# 2. Donut Chart
with col2:
    st.subheader("Revenue by Region")
    fig2 = go.Figure(data=[go.Pie(
        labels=regional_data['region'],
        values=regional_data['revenue'],
        hole=.6,
        marker_colors=px.colors.qualitative.Pastel
    )])
    fig2.update_traces(textposition='outside', textinfo='percent+label')
    fig2.update_layout(annotations=[dict(text='Revenue', x=0.5, y=0.5, font_size=20, showarrow=False)])
    st.plotly_chart(fig2, use_container_width=True)

# 3. Sunburst Chart (Hierarchical Pie)
st.subheader("Hierarchical Sales Distribution")
df_sunburst = df.copy()
df_sunburst['total'] = 'Total Sales'
fig3 = px.sunburst(df_sunburst, 
                   path=['total', 'category'],
                   values='sales',
                   color='profit_margin',
                   color_continuous_scale='RdYlBu',
                   hover_data=['growth'])
st.plotly_chart(fig3, use_container_width=True)

# 4. Interactive Pie Charts Side by Side
col3, col4 = st.columns(2)

with col3:
    st.subheader("Sales Channels")
    fig4 = px.pie(channel_data, values='sales', names='channel',
                  color_discrete_sequence=px.colors.qualitative.Bold,
                  hover_data=['conversion_rate'])
    fig4.update_traces(textposition='inside', 
                      textinfo='percent+label',
                      hovertemplate="Channel: %{label}<br>Sales: $%{value:,.0f}<br>Conversion Rate: %{customdata:.1%}<extra></extra>")
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("Payment Methods")
    fig5 = px.pie(payment_data, values='transactions', names='method',
                  color_discrete_sequence=px.colors.qualitative.Safe,
                  hover_data=['average_value'])
    fig5.update_traces(textposition='inside',
                      textinfo='percent+label',
                      hovertemplate="Method: %{label}<br>Transactions: %{value:,.0f}<br>Avg Value: $%{customdata:.2f}<extra></extra>")
    st.plotly_chart(fig5, use_container_width=True)

# 5. Animated Pie Chart
st.subheader("Quarterly Sales Distribution (Animated)")
quarters = ['Q1', 'Q2', 'Q3', 'Q4']
quarterly_data = pd.DataFrame({
    'quarter': np.repeat(quarters, len(df)),
    'category': df['category'].tolist() * len(quarters),
    'sales': np.random.randint(1000, 5000, len(df) * len(quarters))
})

fig6 = px.pie(quarterly_data, values='sales', names='category',
              animation_frame='quarter',
              color_discrete_sequence=px.colors.qualitative.Vivid)
fig6.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig6, use_container_width=True)

# 6. Half Pie Chart
st.subheader("Customer Distribution by Region")
fig7 = go.Figure(data=[go.Pie(
    labels=regional_data['region'],
    values=regional_data['customers'],
    marker_colors=px.colors.qualitative.Light24,
    rotation=90,
    direction='clockwise',
    hole=0.3,
    textposition='inside',
    textinfo='percent+label'
)])
fig7.update_layout(
    annotations=[dict(text='Customers', x=0.5, y=0.5, font_size=20, showarrow=False)],
    # Make it a half pie
    showlegend=False,
    width=800,
    height=400,
)
# Update traces for half pie
fig7.update_traces(
    startangle=90,
    direction='clockwise',
    textposition='inside',
    textinfo='percent+label'
)
st.plotly_chart(fig7, use_container_width=True)

# 7. Nested Pie Chart
st.subheader("Nested Sales Analysis")
# Inner circle data
inner_labels = df['category']
inner_values = df['sales']
# Outer circle data (subdividing each category)
outer_labels = []
outer_values = []
outer_colors = []
for i, cat in enumerate(df['category']):
    subdivisions = ['Online', 'Offline']
    for sub in subdivisions:
        outer_labels.append(f"{cat}-{sub}")
        outer_values.append(inner_values[i] * np.random.uniform(0.3, 0.7))
        
fig8 = go.Figure()
# Inner pie
fig8.add_trace(go.Pie(
    labels=inner_labels,
    values=inner_values,
    hole=0.6,
    textinfo='label',
    textposition='inside',
    name='Categories'
))
# Outer pie
fig8.add_trace(go.Pie(
    labels=outer_labels,
    values=outer_values,
    textinfo='percent',
    textposition='outside',
    hole=0.4,
    name='Channels'
))
fig8.update_layout(
    annotations=[dict(text='Sales<br>Channels', x=0.5, y=0.5, font_size=20, showarrow=False)],
    showlegend=True
)
st.plotly_chart(fig8, use_container_width=True)

# Add interactivity note
st.info("💡 All charts are interactive! Try hovering, clicking, or dragging to explore the data.")
