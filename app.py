import streamlit as st
import requests

# Streamlit page title
st.title("GitHub Token Connection Test")

# Input field to enter GitHub Token securely
github_token = st.text_input("Enter your GitHub Personal Access Token (PAT)", type="password")

# Button to trigger the check
if st.button("Check GitHub Connection"):
    if not github_token:
        st.error("Please enter your GitHub token!")
    else:
        # Prepare API request to GitHub
        headers = {
            "Authorization": f"token {github_token}"
        }
        response = requests.get("https://api.github.com/user", headers=headers)

        # Check response status
        if response.status_code == 200:
            user_data = response.json()
            st.success(f"✅ Connection successful! Logged in as: {user_data['login']}")
            st.json(user_data)  # Optionally display the user data
        else:
            st.error(f"❌ Connection failed! Status Code: {response.status_code}")
            st.write(response.json())
