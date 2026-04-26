import streamlit as st
from src.auth import get_access_token
from src.converter import convert_document, SUPPORTED_FLOWS
from src.ui import apply_premium_theme

apply_premium_theme()

st.title("File Monk 📁")


with st.expander("ℹ️ View Supported Conversion Flows", expanded=True):
    st.markdown("""
    - **PDF** → DOCX, TIFF
    - **DOCX** → PDF
    - **PPTX** → PDF
    - **Images** (PNG, JPG, JPEG, TIF, TIFF, BMP, GIF, WEBP) → PDF
    """)

st.write("Upload documents and convert them to your desired format.")

uploaded_files = st.file_uploader("Upload files for conversion", accept_multiple_files=True, key="converter_uploader")

valid_target_exts = set()
if uploaded_files:
    for i, file in enumerate(uploaded_files):
        source_ext = file.name.rsplit(".", 1)[-1].lower()
        possible_targets = set(SUPPORTED_FLOWS.get(source_ext, []))
        if i == 0:
            valid_target_exts = possible_targets
        else:
            valid_target_exts = valid_target_exts.intersection(possible_targets)

if uploaded_files and not valid_target_exts:
    st.error(
        "The uploaded files do not share a common supported conversion format. "
        "**Supported flows are:**\n"
        "- PDF → DOCX, TIFF\n"
        "- DOCX → PDF\n"
        "- PPTX → PDF\n"
        "- Images (PNG, JPG, JPEG, TIF, TIFF, BMP, GIF, WEBP) → PDF"
    )
    target_ext = None
elif uploaded_files:
    target_ext = st.selectbox("Convert to", sorted(list(valid_target_exts)))
else:
    target_ext = None
    st.info("Upload files to see available conversion formats.")

if st.button("Convert", disabled=not uploaded_files or not valid_target_exts):
    try:
        token = get_access_token()
        
        for file in uploaded_files:
            source_ext = file.name.rsplit(".", 1)[-1].lower()
            
            if target_ext not in SUPPORTED_FLOWS.get(source_ext, []):
                st.error(f"Unsupported flow for {file.name}: {source_ext} → {target_ext}. Supported flows: pdf→docx, docx→pdf, pptx→pdf, image→pdf, pdf→tiff.")
                continue

            st.write(f"Converting {file.name}...")
            
            with st.spinner(f"Processing {file.name}..."):
                res = convert_document(file, target_ext, token)
            
            if res.status_code == 200:
                st.success(f"{file.name} converted successfully!")
                out_filename = file.name.rsplit(".", 1)[0] + "." + target_ext
                st.download_button(
                    label=f"Download {out_filename}",
                    data=res.content,
                    file_name=out_filename,
                    mime=res.headers.get("Content-Type", "application/octet-stream"),
                    key=f"dl_{file.name}"
                )
            else:
                st.error(f"Failed to convert {file.name}: {res.text}")
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
