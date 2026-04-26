import streamlit as st
import io
import logging
from docx import Document
from streamlit_quill import st_quill
from markdownify import markdownify as md
from src.file_utils import build_pdf_report, build_docx_report
from streamlit_shortcuts import add_shortcuts
from src.agent import generate_smart_title, generate_content
from src.ui import apply_premium_theme

apply_premium_theme()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if "quill_html" not in st.session_state:
    st.session_state["quill_html"] = ""
if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = 0

st.markdown("""
<style>
    iframe {
        height: 75vh !important;
        min-height: 700px !important;
        width: 100% !important;
    }
    [data-testid="stElementContainer"]:has(iframe) {
        height: 75vh !important;
        min-height: 700px !important;
    }
</style>
""", unsafe_allow_html=True)

@st.dialog("💾 Export Document")
def show_export_dialog():
    st.write("Configure your export settings:")
    if "export_filename" not in st.session_state:
        st.session_state["export_filename"] = "Report"
    filename = st.text_input("File Name", key="export_filename")
    export_format = st.radio("Export Format", ["PDF", "DOCX"], horizontal=True)
    st.write("---")
    content_html = st.session_state.get("quill_html", "")
    content_md = md(content_html) if content_html else ""
    if not content_md.strip():
        st.warning("The document is empty. Add some content before exporting.")
        return
    if export_format == "PDF":
        out_pdf = io.BytesIO()
        try:
            build_pdf_report(out_pdf, content_md, filename)
            st.success("PDF ready for download!")
            if st.download_button(
                label=f"Download {filename}.pdf",
                data=out_pdf.getvalue(),
                file_name=f"{filename}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            ):
                st.rerun()
        except Exception as e:
            st.error(f"Failed to build PDF: {e}")
    else:
        out_docx = io.BytesIO()
        try:
            doc = Document()
            build_docx_report(doc, content_md, filename)
            doc.save(out_docx)
            st.success("DOCX ready for download!")
            if st.download_button(
                label=f"Download {filename}.docx",
                data=out_docx.getvalue(),
                file_name=f"{filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                type="primary"
            ):
                st.rerun()
        except Exception as e:
            st.error(f"Failed to build DOCX: {e}")

col_title, col_save = st.columns([10, 1.5], vertical_alignment="bottom")
with col_title:
    st.title("File Monk 📁")
with col_save:
    if st.button("💾 Save", use_container_width=True, type="primary", key="save_export_btn"):
        st.session_state["export_filename"] = generate_smart_title(st.session_state.get("quill_html", ""))
        show_export_dialog()

with st.container():
    c1, c2, c3 = st.columns([7, 2, 1])
    with c1:
        ai_prompt = st.text_input("Ask AI to write...", placeholder="e.g. Draft a project plan for a new website...", label_visibility="collapsed")
    with c2:
        ai_mode = st.selectbox("Action", ["Append to document", "Rewrite entirely"], label_visibility="collapsed")
    with c3:
        if st.button("✨", use_container_width=True):
            if ai_prompt:
                is_rewrite = ai_mode == "Rewrite entirely"
                current_doc = st.session_state.get("quill_html", "")
                
                with st.spinner("Thinking..."):
                    full_response = generate_content(ai_prompt, current_doc, is_rewrite)
                
                if full_response:
                    if is_rewrite:
                        st.session_state["quill_html"] = full_response
                    else:
                        st.session_state["quill_html"] = current_doc + f"<div>{full_response}</div>"
                    st.session_state["editor_key"] += 1
                    st.rerun()

html_content = st_quill(
    value=st.session_state["quill_html"],
    placeholder="Start typing your report here...",
    key=f"quill_editor_{st.session_state['editor_key']}",
    html=True,
)

if html_content != st.session_state["quill_html"]:
    st.session_state["quill_html"] = html_content

add_shortcuts(save_export_btn=["ctrl+s", "meta+s"])

st.components.v1.html(
    """
    <script>
    const disableSave = function(e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            e.stopPropagation();
        }
    };
    document.addEventListener('keydown', disableSave, true);
    window.parent.document.addEventListener('keydown', disableSave, true);

    setInterval(() => {
        const iframes = window.parent.document.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            try {
                if (iframe.title.includes("quill")) {
                    if (!iframe.contentDocument.getElementById("custom-quill-style")) {
                        const style = iframe.contentDocument.createElement('style');
                        style.id = "custom-quill-style";
                        style.textContent = `
                            .ql-container { border: none !important; }
                            #editor, .ql-editor { min-height: 600px !important; height: 100% !important; }
                        `;
                        iframe.contentDocument.head.appendChild(style);
                    }
                }
            } catch (e) {}
        });
    }, 1000);
    </script>
    """,
    height=0
)
