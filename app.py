import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

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
        .stock-table th, .stock-table td {
            padding: 10px;
            text-align: left;
        }
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

# Stock Table Data
stocks = pd.DataFrame([
    ["AAPL", "Apple", "$99.99", "Positive", "+0.7562%", "Buy"],
    ["AMZN", "Amazon", "$99.99", "Positive", "+0.6762%", "Buy"],
    ["GOOG", "Google", "$99.99", "Negative", "-0.2562%", "Sell"],
    ["MA", "Mastercard", "$99.99", "Negative", "-0.6562%", "Sell"],
    ["QQQQ", "Nasdaq", "$99.99", "Positive", "+0.4562%", "Buy"],
    ["WMT", "Walmart", "$99.99", "Positive", "+0.3562%", "Buy"]
], columns=["Symbol", "Name", "Current Price", "Sentiment", "% Change", "Action"])

# Display Stock Table
st.subheader("📜 Stock Portfolio")
st.markdown("""
    <table class='stock-table' style='width:100%; border-collapse: collapse;'>
        <tr style='background-color: #f4f4f4;'>
            <th>Symbol</th>
            <th>Name</th>
            <th>Action</th>
            <th>Current $</th>
            <th>% Change</th>
            <th>Sentiment</th>
        </tr>
""", unsafe_allow_html=True)

for _, row in stocks.iterrows():
    color = "#10B981" if row["Action"] == "Buy" else "#EF4444"
    st.markdown(f"""
        <tr>
            <td>{row['Symbol']}</td>
            <td>{row['Name']}</td>
            <td style='color: {color}; font-weight: bold;'>{row['Action']}</td>
            <td>{row['Current Price']}</td>
            <td>{row['% Change']}</td>
            <td>{row['Sentiment']}</td>
        </tr>
    """, unsafe_allow_html=True)

st.markdown("</table>", unsafe_allow_html=True)

# Add Stock Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Add Stock"):
    st.success("Feature to add stocks coming soon!")
