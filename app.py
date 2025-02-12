import streamlit as st

# Set page title
st.set_page_config(page_title="Stock Portfolio", layout="wide")

# Read HTML content
with open("design.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# Display the HTML in Streamlit
st.components.v1.html(html_content, height=800, scrolling=True)
