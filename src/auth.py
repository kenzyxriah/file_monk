import streamlit as st
import requests

@st.cache_data(ttl=2700, show_spinner=False)
def get_initial_access_token():
    payload = {"name": st.secrets["AUTH_NAME"], "browser": st.secrets["AUTH_BROWSER"]}
    try:
        response = requests.post(st.secrets["AUTH_API"], json=payload)
        response.raise_for_status()
    except Exception as e:
        status_code = getattr(e.response, 'status_code', 'Unknown') if hasattr(e, 'response') and e.response is not None else '???'
        if status_code == 503:
            raise Exception("Authentication Service: System busy or temporarily unavailable. Please try again later.")
        raise Exception(f"Authentication System: Initial handshake failed (Status {status_code}).")
        
    data = response.json()
    if data.get("isSuccess") and "token" in data:
        return data["token"]["accessToken"]
    raise ValueError("Authentication System: Initial token response invalid.")

@st.cache_data(ttl=2700, show_spinner=False)
def get_subsequent_access_token(_dev_token):
    payload = {
        "deviceId": st.secrets["LOGIN_DEVICE_ID"],
        "ipAddress": st.secrets["LOGIN_IP_ADDRESS"],
        "deviceName": "",
        "browser": st.secrets["AUTH_BROWSER"],
        "location": st.secrets["LOGIN_LOCATION"],
        "email": st.secrets["LOGIN_EMAIL"],
        "password": st.secrets["LOGIN_PASSWORD"],
    }
    headers = {"Authorization": f"Bearer {_dev_token}"}
    try:
        response = requests.post(st.secrets["AUTH_USER_API"], json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        status_code = getattr(e.response, 'status_code', 'Unknown') if hasattr(e, 'response') and e.response is not None else '???'
        if status_code == 503:
            raise Exception("Authentication Service: Login server is temporarily unavailable. Please try again later.")
        raise Exception(f"Authentication System: User login failed (Status {status_code}).")
        
    data = response.json()
    if data.get("isSuccess") and "token" in data:
        return data["token"]["accessToken"]
    raise ValueError("Authentication System: Login token response invalid.")

def get_access_token():
    dev_token = get_initial_access_token()
    user_token = get_subsequent_access_token(dev_token)
    return user_token
