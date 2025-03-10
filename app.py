import streamlit as st
import requests

st.title("GitHub Token Connection Test (via Streamlit Secrets)")

# Read token from secrets
github_token = st.secrets["GITHUB_TOKEN"]

if st.button("Check GitHub Connection"):
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get("https://api.github.com/user", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        st.success(f"✅ Connected as: {user_data['login']}")
        st.json(user_data)
    else:
        st.error(f"❌ Failed. Status Code: {response.status_code}")
        st.write(response.json())
