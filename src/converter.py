import streamlit as st
import requests

SUPPORTED_FLOWS = {
    "docx": ["pdf"],
    "pdf": ["docx", "tiff"],
    "pptx": ["pdf"],
    "png": ["pdf"],
    "jpg": ["pdf"],
    "jpeg": ["pdf"],
    "tif": ["pdf"],
    "tiff": ["pdf"],
    "bmp": ["pdf"],
    "gif": ["pdf"],
    "webp": ["pdf"],
}

def convert_document(file, target_ext, token):
    api_base_url = st.secrets["API_BASE_URL"].rstrip("/")
    convert_url = f"{api_base_url}/utilities/convert-file"
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"convert_to_ext": target_ext}
    
    response = requests.post(convert_url, headers=headers, files=files, data=data)
    return response
