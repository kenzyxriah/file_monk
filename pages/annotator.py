import streamlit as st
import fitz
import io
import json
import hashlib
import base64
import copy
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from src.converter import convert_document
from src.auth import get_access_token
from src.ui import apply_premium_theme, toolbox_scripts, render_toolbox

apply_premium_theme()

st.title("File Monk 📁")

def process_file_to_pdf_bytes(file):
    ext = file.name.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return file.getvalue()
    elif ext == "docx":
        token = get_access_token()
        with st.spinner("Converting DOCX to PDF for annotation..."):
            res = convert_document(file, "pdf", token)
        if res.status_code == 200:
            return res.content
        else:
            st.error(f"Failed to convert DOCX: {res.text}")
            return None
    else:
        st.error("Unsupported file type for annotation.")
        return None

uploaded_file = st.file_uploader("Upload document for annotation", type=["pdf", "docx"], key="annotator_uploader")

if uploaded_file is not None:
    if "pdf_bytes" not in st.session_state or st.session_state.get("last_uploaded_filename") != uploaded_file.name:
        with st.spinner("Processing document..."):
            pdf_bytes = process_file_to_pdf_bytes(uploaded_file)
            if pdf_bytes:
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["last_uploaded_filename"] = uploaded_file.name
            else:
                st.stop()
    pdf_bytes = st.session_state.get("pdf_bytes")
else:
    if "pdf_bytes" not in st.session_state or st.session_state.get("last_uploaded_filename") != "blank":
        blank_doc = fitz.open()
        page = blank_doc.new_page(width=612, height=792)
        page.draw_rect(page.rect, color=(1, 1, 1), fill=(1, 1, 1))
        out_pdf = io.BytesIO()
        blank_doc.save(out_pdf)
        st.session_state["pdf_bytes"] = out_pdf.getvalue()
        st.session_state["last_uploaded_filename"] = "blank"
    pdf_bytes = st.session_state.get("pdf_bytes")

if not pdf_bytes:
    st.stop()

doc = fitz.open(stream=pdf_bytes, filetype="pdf")
total_pages = len(doc)
page_num = st.sidebar.number_input("📄 Page Number", min_value=1, max_value=total_pages, value=1) if total_pages > 1 else 1

if f"active_tool_{page_num}" not in st.session_state:
    st.session_state[f"active_tool_{page_num}"] = "transform"
if f"history_{page_num}" not in st.session_state:
    st.session_state[f"history_{page_num}"] = []
if f"history_idx_{page_num}" not in st.session_state:
    st.session_state[f"history_idx_{page_num}"] = -1
if f"initial_drawing_{page_num}" not in st.session_state:
    st.session_state[f"initial_drawing_{page_num}"] = None
if f"canvas_key_{page_num}" not in st.session_state:
    st.session_state[f"canvas_key_{page_num}"] = 0
if f"stamp_uploader_key_{page_num}" not in st.session_state:
    st.session_state[f"stamp_uploader_key_{page_num}"] = 0

col1, col2 = st.columns([1.2, 3.8])

with col1:
    active_tool = render_toolbox(page_num)
    
    with st.container(border=True):
        if st.button("🗑️ Clear Page", use_container_width=True):
            st.session_state[f"canvas_key_{page_num}"] = st.session_state.get(f"canvas_key_{page_num}", 0) + 1
            st.session_state[f"history_{page_num}"] = []
            st.session_state[f"history_idx_{page_num}"] = -1
            st.session_state[f"initial_drawing_{page_num}"] = None
            if "canvas_image" in st.session_state:
                del st.session_state["canvas_image"]
            st.rerun()
            
        st.write("---")
        if st.button("🚀 Apply & Export", type="primary", use_container_width=True):
            if "canvas_image" in st.session_state and st.session_state["canvas_image"] is not None:
                page = doc[page_num - 1]
                temp_pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                base_img = Image.frombytes("RGB", [temp_pix.width, temp_pix.height], temp_pix.samples)
                img_data = st.session_state["canvas_image"]
                canvas_drawn = Image.fromarray(img_data.astype('uint8'))
                canvas_drawn = canvas_drawn.crop((0, 0, temp_pix.width, temp_pix.height))
                base_img.paste(canvas_drawn, (0, 0), canvas_drawn)
                img_byte_arr = io.BytesIO()
                base_img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                page.insert_image(page.rect, stream=img_bytes)
                out_pdf = io.BytesIO()
                doc.save(out_pdf)
                st.session_state["pdf_bytes"] = out_pdf.getvalue()
                st.success(f"Applied enhancements to page {page_num}!")
                st.rerun()

        if st.session_state.get("pdf_bytes"):
            st.write("---")
            file_name_out = f"annotated_{uploaded_file.name.rsplit('.', 1)[0]}.pdf" if uploaded_file else "annotated_document.pdf"
            st.download_button(label="📥 Download Annotated PDF", data=st.session_state["pdf_bytes"], file_name=file_name_out, mime="application/pdf", use_container_width=True)

    with col2:
        c2_head, c2_undo, c2_redo = st.columns([6, 1, 1], vertical_alignment="bottom")
        with c2_head:
            st.subheader(f"📄 Page Preview ({page_num}/{total_pages})")
        with c2_undo:
            if st.button("↩️", use_container_width=True, help="Undo"):
                if st.session_state[f"history_idx_{page_num}"] > 0:
                    st.session_state[f"history_idx_{page_num}"] -= 1
                    idx = st.session_state[f"history_idx_{page_num}"]
                    st.session_state[f"initial_drawing_{page_num}"] = st.session_state[f"history_{page_num}"][idx]
                    st.session_state[f"canvas_key_{page_num}"] += 1
                    st.rerun()
                elif st.session_state[f"history_idx_{page_num}"] == 0:
                    st.session_state[f"history_idx_{page_num}"] = -1
                    st.session_state[f"initial_drawing_{page_num}"] = None
                    st.session_state[f"canvas_key_{page_num}"] += 1
                    st.rerun()
        with c2_redo:
            if st.button("↪️", use_container_width=True, help="Redo"):
                if st.session_state[f"history_idx_{page_num}"] < len(st.session_state[f"history_{page_num}"]) - 1:
                    st.session_state[f"history_idx_{page_num}"] += 1
                    idx = st.session_state[f"history_idx_{page_num}"]
                    st.session_state[f"initial_drawing_{page_num}"] = st.session_state[f"history_{page_num}"][idx]
                    st.session_state[f"canvas_key_{page_num}"] += 1
                    st.rerun()

        bg_img_key = f"bg_img_{page_num}_{st.session_state.get('last_uploaded_filename')}"
        if bg_img_key not in st.session_state:
            page = doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), alpha=False)
            bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            st.session_state[bg_img_key] = bg_img
        bg_img = st.session_state[bg_img_key]
        drawing_mode = st.session_state[f"active_tool_{page_num}"]
        stroke_width = 3
        stroke_color = "#3182CE"
        fill_color = "rgba(49, 130, 206, 0.15)"
        canvas_result = st_canvas(
            fill_color=fill_color,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=bg_img,
            initial_drawing=st.session_state[f"initial_drawing_{page_num}"],
            update_streamlit=True,
            height=bg_img.height,
            width=bg_img.width,
            drawing_mode=drawing_mode,
            key=f"canvas_{page_num}_{st.session_state[f'canvas_key_{page_num}']}",
        )
        
        if canvas_result.json_data is not None:
            curr_str = json.dumps(canvas_result.json_data)
            idx = st.session_state[f"history_idx_{page_num}"]
            hist_item = st.session_state[f"history_{page_num}"][idx] if idx >= 0 else None
            hist_str = json.dumps(hist_item) if hist_item else ""
            if curr_str != hist_str:
                st.session_state[f"history_{page_num}"] = st.session_state[f"history_{page_num}"][:idx+1]
                st.session_state[f"history_{page_num}"].append(canvas_result.json_data)
                st.session_state[f"history_idx_{page_num}"] += 1
                if st.session_state[f"active_tool_{page_num}"] != "transform":
                    st.session_state[f"active_tool_{page_num}"] = "transform"
                    st.rerun()
        if canvas_result.image_data is not None:
            st.session_state["canvas_image"] = canvas_result.image_data

trigger_js = "true" if st.session_state.get(f"trigger_upload_{page_num}") else "false"
if st.session_state.get(f"trigger_upload_{page_num}"):
    st.session_state[f"trigger_upload_{page_num}"] = False

toolbox_scripts(trigger_js)
