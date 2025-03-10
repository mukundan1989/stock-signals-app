import streamlit as st

github_token = st.secrets["GITHUB_TOKEN"]

# For testing only - show part of token to confirm it's being read correctly
if github_token:
    st.success(f"Token detected: {github_token[:6]}...{github_token[-4:]}")
else:
    st.error("❌ Token not found!")
