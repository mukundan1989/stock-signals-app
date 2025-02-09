import streamlit as st
import pandas as pd

# Custom CSS for Styling
st.markdown("""
    <style>
        .metric-card {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            color: white;
            margin: 10px;
        }
        .blue { background-color: #3B82F6; }
        .green { background-color: #10B981; }
        .purple { background-color: #8B5CF6; }
        .orange { background-color: #F59E0B; }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("📈 Portfolio Dashboard")
st.markdown("Easily predict stock market trends and make smarter investment decisions.")

# Sidebar Toggles
st.sidebar.header("Options")
sentiment_toggle = st.sidebar.checkbox("Include Sentiment Analysis", False)
technical_toggle = st.sidebar.checkbox("Include Technical Indicators", False)
fundamental_toggle = st.sidebar.checkbox("Include Fundamental Data", False)

# Metrics Data
metrics = [
    {"label": "Above baseline", "value": "43%", "color": "blue", "description": "Compared to market average"},
    {"label": "Value gain on buy", "value": "$13,813", "color": "green", "description": "Total profit from buy signals"},
    {"label": "Sentiment Score", "value": "+0.75", "color": "purple", "description": "Overall market sentiment"},
    {"label": "Prediction Accuracy", "value": "87%", "color": "orange", "description": "Success rate of predictions"}
]

# Display Metrics
st.subheader("📊 Key Metrics")
cols = st.columns(2)
for i, metric in enumerate(metrics):
    with cols[i % 2]:
        st.markdown(f"""
            <div class='metric-card {metric['color']}'>
                <h2>{metric['value']}</h2>
                <p>{metric['label']}</p>
                <small>{metric['description']}</small>
            </div>
        """, unsafe_allow_html=True)

# Toggle Buttons Section (Below Key Metrics)
st.subheader("🔧 Toggle Features")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Sentiment Analysis")
    sentiment_toggle = st.toggle("Enable Sentiment", sentiment_toggle)
with col2:
    st.write("Technical Indicators")
    technical_toggle = st.toggle("Enable Technical", technical_toggle)
with col3:
    st.write("Fundamental Data")
    fundamental_toggle = st.toggle("Enable Fundamental", fundamental_toggle)

# Stock Table Data
stocks = pd.DataFrame([
    ["AAPL", "Apple", "$99.99", "Positive", "+0.7562%", "Buy"],
    ["AMZN", "Amazon", "$99.99", "Positive", "+0.6762%", "Buy"],
    ["GOOG", "Google", "$99.99", "Negative", "-0.2562%", "Sell"],
    ["MA", "Mastercard", "$99.99", "Negative", "-0.6562%", "Sell"],
    ["QQQQ", "Nasdaq", "$99.99", "Positive", "+0.4562%", "Buy"],
    ["WMT", "Walmart", "$99.99", "Positive", "+0.3562%", "Buy"]
], columns=["Symbol", "Name", "Current Price", "Sentiment", "% Change", "Action"])

# Display Stock Table with Improved Styling
st.subheader("📜 Stock Portfolio")

# Apply Styling to Data
def style_row(action):
    return "background-color: #d1fae5; color: #065f46;" if action == "Buy" else "background-color: #fee2e2; color: #b91c1c;"

styled_table = """
    <table style="width:100%; border-collapse: collapse; text-align: left; font-size: 16px;">
        <tr style="background-color: #f4f4f4; font-weight: bold;">
            <th style="padding: 10px;">Symbol</th>
            <th style="padding: 10px;">Name</th>
            <th style="padding: 10px;">Action</th>
            <th style="padding: 10px;">Current $</th>
            <th style="padding: 10px;">% Change</th>
            <th style="padding: 10px;">Sentiment</th>
        </tr>
"""

for _, row in stocks.iterrows():
    color_style = style_row(row["Action"])
    change_icon = "⬆️" if "+" in row["% Change"] else "⬇️"
    
    styled_table += f"""
        <tr style="{color_style}; font-weight: bold;">
            <td style="padding: 10px; color: #2563eb;">{row['Symbol']}</td>
            <td style="padding: 10px;">{row['Name']}</td>
            <td style="padding: 10px;">{row['Action']}</td>
            <td style="padding: 10px;">{row['Current Price']}</td>
            <td style="padding: 10px;">{change_icon} {row['% Change']}</td>
            <td style="padding: 10px;">{row['Sentiment']}</td>
        </tr>
    """

styled_table += "</table>"

st.markdown(styled_table, unsafe_allow_html=True)

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
