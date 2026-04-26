import streamlit as st
import base64
import copy
import io
from PIL import Image

def apply_premium_theme(is_home=False):
    """
    Applies the global premium dark glassmorphic theme to the Streamlit app.
    If is_home=True, it also hides the sidebar and forces centering.
    """
    
    import textwrap
    
    # Base CSS applicable to all pages
    base_css = textwrap.dedent("""
    <style>
        /* Import Modern Font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        /* Global Background and Typography */
        .stApp {
            background: radial-gradient(circle at 50% 0%, #1a1b26 0%, #0d0e15 100%) !important;
            font-family: 'Outfit', sans-serif !important;
            color: #ffffff !important;
        }
        
        /* Typography overrides */
        h1, h2, h3, h4, h5, h6, p, label {
            font-family: 'Outfit', sans-serif !important;
        }
 
        /* Glassmorphic Containers */
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 20px !important;
            padding: 1.5rem !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        }
 
        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stSelectbox > div[data-baseweb="select"] {
            background: rgba(0, 0, 0, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 10px !important;
        }
        .stTextInput input:focus, .stSelectbox > div[data-baseweb="select"]:focus-within {
            border-color: #4facfe !important;
            box-shadow: 0 0 0 1px #4facfe !important;
        }
 
        /* Buttons */
        .stButton button {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
        }
        .stButton button:hover {
            background: rgba(255, 255, 255, 0.1) !important;
            border-color: #4facfe !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 16px rgba(79, 172, 254, 0.2) !important;
        }
        
        /* Primary Button Override */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
        }
        .stButton button[kind="primary"]:hover {
            opacity: 0.9 !important;
            box-shadow: 0 8px 24px rgba(79, 172, 254, 0.4) !important;
        }
        
        /* Remove default Streamlit header bar */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
    </style>
    """)
    
    if is_home:
        # Extra CSS specifically to center the home page and hide navigation
        home_css = textwrap.dedent("""
        <style>
            /* Hide the sidebar completely on home */
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
            
            /* Center the main block container */
            .block-container {
                padding-top: 2rem !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                min-height: 90vh !important;
                text-align: center !important;
            }
        </style>
        """)
        st.markdown(base_css + home_css, unsafe_allow_html=True)
    else:
        # Standard padding for tool pages
        tool_css = textwrap.dedent("""
        <style>
            .block-container {
                padding-top: 3rem !important;
                padding-bottom: 3rem !important;
                max-width: 95% !important;
            }
        </style>
        """)
        st.markdown(base_css + tool_css, unsafe_allow_html=True)

def toolbox_scripts(trigger_js: str):
    """
    Injects the JavaScript logic for the annotator page, including keyboard shortcuts
    and the hidden file uploader nuclear cleanup strategy.
    """
    st.components.v1.html(
        f"""
        <script>
        const trigger = {trigger_js};
        
        const nukeSecret = () => {{
            const parentDoc = window.parent.document;
            parentDoc.querySelectorAll('[data-testid="stFileUploader"]').forEach(el => {{
                if (el.innerText.includes('HIDDEN_STAMP')) {{
                    el.style.display = 'none';
                    el.style.height = '0';
                    el.style.overflow = 'hidden';
                }}
            }});
        }};
        setInterval(nukeSecret, 100);

        if (trigger) {{
            setTimeout(() => {{
                const parentDoc = window.parent.document;
                let targetButton = null;
                parentDoc.querySelectorAll('[data-testid="stFileUploader"]').forEach(el => {{
                    if (el.innerText.includes('HIDDEN_STAMP')) {{
                        targetButton = el.querySelector('button');
                    }}
                }});
                if (targetButton) targetButton.click();
            }}, 100);
        }}

        window.parent.document.addEventListener('keydown', (e) => {{
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            const key = e.key.toLowerCase();
            const buttons = window.parent.document.querySelectorAll('button');
            if (key === 'f') buttons.forEach(b => {{ if (b.innerText === '✏️') b.click(); }});
            if (key === 'l') buttons.forEach(b => {{ if (b.innerText === '📏') b.click(); }});
            if (key === 'r') buttons.forEach(b => {{ if (b.innerText === '⬛') b.click(); }});
            if (key === 'c') buttons.forEach(b => {{ if (b.innerText === '⭕') b.click(); }});
            if (key === 'i') buttons.forEach(b => {{ if (b.innerText === '🖼️') b.click(); }});
        }});
        </script>
        """,
        height=0
    )

def render_toolbox(page_num):
    """
    Renders the interactive drawing toolbox and handles state updates for tools and image uploads.
    """
    st.subheader("🛠️ Toolbox")
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] {
        justify-content: center !important;
        gap: 0.5rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 0 1 auto !important;
        min-width: 50px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        cols = st.columns(5)
        with cols[0]:
            if st.button("✏️", help="Freedraw", use_container_width=True):
                st.session_state[f"active_tool_{page_num}"] = "freedraw"
                st.rerun()
        with cols[1]:
            if st.button("📏", help="Line", use_container_width=True):
                st.session_state[f"active_tool_{page_num}"] = "line"
                st.rerun()
        with cols[2]:
            if st.button("⬛", help="Rectangle", use_container_width=True):
                st.session_state[f"active_tool_{page_num}"] = "rect"
                st.rerun()
        with cols[3]:
            if st.button("⭕", help="Circle", use_container_width=True):
                st.session_state[f"active_tool_{page_num}"] = "circle"
                st.rerun()
        with cols[4]:
            if st.button("🖼️", help="Direct Image Upload", use_container_width=True):
                st.session_state[f"trigger_upload_{page_num}"] = True
                st.rerun()
        
        active_tool = st.session_state[f"active_tool_{page_num}"]
        st.write(f"Active Tool: **{active_tool.capitalize()}**")
        
        st.write("---")
        
        uploader_key = f"stamp_uploader_{page_num}_{st.session_state[f'stamp_uploader_key_{page_num}']}"
        uploaded_stamp = st.file_uploader("HIDDEN_STAMP", type=["png", "jpg", "jpeg"], key=uploader_key)
        
        if uploaded_stamp:
            try:
                img_bytes = uploaded_stamp.read()
                pil_img = Image.open(io.BytesIO(img_bytes))
                img_width, img_height = pil_img.size
                
                max_dim = 400
                scale = 1.0
                if img_width > max_dim or img_height > max_dim:
                    scale = min(max_dim / img_width, max_dim / img_height)
                
                img_b64 = base64.b64encode(img_bytes).decode()
                data_url = f"data:image/{uploaded_stamp.type.split('/')[-1]};base64,{img_b64}"
                new_img_obj = {
                    "type": "image", "version": "4.4.0", "originX": "left", "originY": "top",
                    "left": 100, "top": 100, "width": img_width, "height": img_height, "fill": "rgb(0,0,0)",
                    "stroke": None, "strokeWidth": 0, "strokeDashArray": None, "strokeLineCap": "butt",
                    "strokeDashOffset": 0, "strokeLineJoin": "miter", "strokeUniform": False,
                    "strokeMiterLimit": 4, "scaleX": scale, "scaleY": scale, "angle": 0, "flipX": False,
                    "flipY": False, "opacity": 1, "shadow": None, "visible": True, "backgroundColor": "",
                    "fillRule": "nonzero", "paintFirst": "fill", "globalCompositeOperation": "source-over",
                    "skewX": 0, "skewY": 0, "cropX": 0, "cropY": 0, "src": data_url,
                    "crossOrigin": "anonymous", "filters": []
                }
                idx = st.session_state[f"history_idx_{page_num}"]
                current_json = st.session_state[f"history_{page_num}"][idx] if idx >= 0 else {"objects": [], "background": ""}
                current_json = copy.deepcopy(current_json)
                if "objects" not in current_json: current_json["objects"] = []
                current_json["objects"].append(new_img_obj)
                st.session_state[f"history_{page_num}"].append(current_json)
                st.session_state[f"history_idx_{page_num}"] += 1
                st.session_state[f"initial_drawing_{page_num}"] = current_json
                st.session_state[f"canvas_key_{page_num}"] += 1
                st.session_state[f"active_tool_{page_num}"] = "transform"
                st.session_state[f"stamp_uploader_key_{page_num}"] += 1
                st.rerun()
            except Exception:
                pass
        return active_tool
